# Checklist 02: Architecture, Database & Concurrency Mechanisms

**Source Reference**: [Why Failures Take Their Shape (Parts 9–17)](file:///home/btpl-lap-22/live/llm-obs-infra/policies/rules/edgeCases/why-failures-take-their-shape.md)  
**Objective**: Prevent concurrency anomalies, transaction boundary bugs, state corruption, and silent drift across databases, message buses, and state engines.

---

## 1. Database Concurrency & Isolation Pitfalls

- [ ] **Isolation Level Verification**:
  - [ ] Are transactions aware of their engine's default isolation level (Postgres/MySQL default is Read Committed or Repeatable Read, neither of which prevents Write Skew)?
  - [ ] If relying on `SERIALIZABLE` isolation, does the application implement automated retry loops to catch serialization failures (`40001 / could not serialize access`)?
- [ ] **Pessimistic vs. Optimistic Locking**:
  - [ ] **Optimistic Concurrency**: Checked against `UPDATE items SET stock = stock - 1, version = version + 1 WHERE id = ? AND version = ?`.
  - [ ] **Pessimistic Concurrency**: High-contention rows use `SELECT ... FOR UPDATE` within a short, bounded transaction.
  - [ ] **Lock Queues / Hot Rows**: High-throughput increments (counters, analytics, balance tallies) use append-only event logs or sharded counters instead of single-row update hotspots.
- [ ] **Queue Worker Concurrency**:
  - [ ] Queue-processing queries use `SELECT ... FOR UPDATE SKIP LOCKED LIMIT N` to prevent lock contention, blocking cascades, and duplicate processing across concurrent workers.
- [ ] **Read-Your-Own-Writes Consistency**:
  - [ ] Do read-heavy systems with primary-replica replication route immediate post-write queries to the primary database, or enforce replication lag bounds, to prevent users seeing stale state right after an edit?

---

## 2. Cursor Pagination & Keyset Query Safety

- [ ] **Elimination of Deep `OFFSET`**:
  - [ ] Is `OFFSET N` completely replaced with keyset pagination for large tables ($N > 10,000$)?
    ```sql
    -- Compliant Keyset Pagination
    SELECT id, created_at, title
    FROM events
    WHERE (created_at, id) < (:last_created_at, :last_id)
    ORDER BY created_at DESC, id DESC
    LIMIT 50;
    ```
- [ ] **Composite Sorting Uniqueness**:
  - [ ] Does every keyset pagination query have a strictly unique tie-breaker (e.g., `id`) in the `ORDER BY` clause to avoid skipping or repeating rows with identical timestamps?

---

## 3. Transactional Boundaries & Dual Writes

- [ ] **Elimination of Split Dual Writes**:
  - [ ] Verify that application code **never** performs a database commit and a message publish / external HTTP call as separate independent steps.
- [ ] **Transactional Outbox Pattern Implementation**:
  - [ ] Are events written to an `outbox_table` inside the *same* database transaction that updates business state?
  - [ ] Is an outbox processor (or CDC engine such as Debezium) used to reliably publish outbox events to Kafka/RabbitMQ with at-least-once delivery?
- [ ] **Polling over Serial ID Traps**:
  - [ ] When polling an outbox or event table via auto-increment IDs (`WHERE id > :last_seen_id`), are transaction commit order delays accounted for (Transaction A gets ID 100 but commits after Transaction B gets ID 101, leading to ID 100 being skipped)?
  - [ ] Is outbox polling performed with continuous sequence tracking, CDC logs, or timestamp buffer windows?

---

## 4. State Machine & Lifecycle Integrity

- [ ] **Explicit Transitions as Data**:
  - [ ] Are allowed state transitions codified in an explicit transition matrix rather than scattered across arbitrary controller endpoints?
- [ ] **Rejection of Out-of-Order or Illegal Transitions**:
  - [ ] Does the state updater enforce transition constraints atomically?
    ```sql
    UPDATE orders 
    SET status = 'SHIPPED', updated_at = NOW() 
    WHERE id = :id AND status = 'PROCESSING';
    ```
  - [ ] If 0 rows are updated, is an explicit conflict error raised rather than assuming success?
- [ ] **Terminal State Immutability**:
  - [ ] Are terminal states (`CANCELLED`, `REFUNDED`, `COMPLETED`, `ARCHIVED`) strictly immutable against further modifications?

---

## 5. Reconciliation & Invariant Monitoring Engine

- [ ] **Continuous Out-of-Band Audit Jobs**:
  - [ ] Is an asynchronous reconciliation job running on a fixed cron schedule to verify cross-system and cross-row invariants?
    ```sql
    -- Example Ledger Invariant: Sum of debits must equal sum of credits per transaction
    SELECT transaction_id, SUM(amount) AS net_sum
    FROM ledger_entries
    GROUP BY transaction_id
    HAVING SUM(amount) != 0;
    ```
- [ ] **Stuck State Detectors**:
  - [ ] Are there automated monitors alerting on records remaining in intermediate states (`PENDING`, `IN_FLIGHT`, `PROCESSING`) longer than their timeout threshold ($T > 15 \text{ mins}$)?
- [ ] **Automated Self-Healing / Repair Jobs**:
  - [ ] Do reconciliation jobs flag discrepancies in a review table and trigger safe, idempotent compensation flows?

---

## 6. Infrastructure & Connection Pool Boundaries

- [ ] **Connection Pool Size Math**:
  - [ ] Is pool size calculated according to CPU core capacity:
    $$\text{Max Connections} \approx (\text{Core Count} \times 2) + \text{Spindle Count}$$
  - [ ] Are application instances capped so $\sum (\text{App Instances} \times \text{Pool Size}) \le \text{DB Max Connections} \times 0.8$?
- [ ] **Query Timeout Guardrails**:
  - [ ] Does every database query have an explicit `statement_timeout` (e.g. 5000ms) configured to prevent runaway full-table locks?
- [ ] **DNS Caching & TTL Compliance**:
  - [ ] Is JVM/Node/Go DNS lookup caching set to a finite TTL (e.g. 10–30s) instead of caching DNS resolutions indefinitely (which breaks IP failovers)?
