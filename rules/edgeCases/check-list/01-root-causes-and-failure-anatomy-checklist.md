# Checklist 01: Root Causes & Failure Anatomy

**Source Reference**: [The Anatomy of a Failure (Parts 1–8)](file:///home/btpl-lap-22/live/llm-obs-infra/policies/rules/edgeCases/the-anatomy-of-a-failure.md)  
**Objective**: Eliminate systemic failure classes by transforming implicit assumptions into hard invariants, enforcing boundaries, and building resilient feedback control.

---

## 1. Failure Layer & Root Cause Decomposition Gate

When investigating an incident or reviewing a new architectural design, verify that the solution targets the structural root cause rather than merely the trigger.

- [ ] **Incident Layering Analysis Completed**:
  - **Symptom**: Observed behavior clearly documented.
  - **Trigger**: The specific event that sparked the issue (e.g. network timeout, deploy restart, retry burst).
  - **Proximate Cause**: Direct technical mechanism that executed the failure (e.g. double request processing).
  - **Contributing Conditions**: Environmental factors amplifying the blast radius (e.g. aggressive default retries, missing jitter).
  - **Root Cause**: The systemic structural flaw allowing the failure class (e.g. lack of idempotency keys at storage layer).
  - **Latent Conditions**: Dormant vulnerabilities waiting for a trigger (e.g. lack of drift reconciliation job).
- [ ] **Whole-Class Elimination Test**: If this fix is deployed, does the *entire class* of failures vanish across all possible triggers (double clicks, queue redeliveries, retries, race conditions)?
- [ ] **Avoid the "Human Error" Anti-Pattern**: If an investigation lands on "an engineer forgot," ask: *Why was it possible, easy, and undetectable by automated gates?*

---

## 2. Invariants & Domain Modeling Invariants Gate (Families A, B & C)

Rules must live where the authoritative state resides. Illegal states must be unrepresentable.

- [ ] **Cardinality & Nullability Explicitly Defined**:
  - [ ] Are empty arrays (`[]`), `NULL`, and `undefined` differentiated with distinct, explicit semantics?
  - [ ] Does every collection query handle `0`, `1`, and `N > 100,000` items safely?
  - [ ] Are `NOT IN (subquery)` SQL operations checked for potential `NULL` values that cause whole-query suppression?
- [ ] **Domain Value Objects & Types**:
  - [ ] Are currency amounts represented as integers in the lowest denominator (e.g. cents) or arbitrary-precision decimals, never IEEE-754 floats?
  - [ ] Are timestamps stored with explicit timezone offsets or strictly normalized to UTC (`TIMESTAMPTZ`)?
  - [ ] Are strings normalized (e.g. Unicode NFC normalization, trimmed whitespace, case-folded emails) before comparison or hashing?
- [ ] **Snapshot vs. Reference Explicitly Decided**:
  - [ ] Does historical transaction data (orders, invoices, receipts) snapshot prices, discounts, tax rates, and customer addresses rather than referencing live mutable entities?
- [ ] **Authoritative Storage Layer Invariants**:
  - [ ] Is every invariant backed by a database-level constraint (`CHECK (balance >= 0)`, `UNIQUE`, `FOREIGN KEY`, `EXCLUSION`) rather than relying solely on UI or application checks?
  - [ ] Can raw SQL run by a migration script or admin tool violate the invariant? If yes, tighten the storage constraint.
  - [ ] Are soft-delete filters (`WHERE deleted_at IS NULL`) or multi-tenant filters (`WHERE tenant_id = ?`) enforced systematically (e.g. via Row-Level Security or ORM hooks), preventing query-level omissions?

---

## 3. Boundary & Contract Integrity Gate (Family D)

Boundaries between microservices, external APIs, and internal modules must be strictly validated.

- [ ] **Strict Runtime Anti-Corruption Layer**:
  - [ ] Is incoming data strictly parsed at the edge via Zod, Protobuf, or JSON Schema before entering domain logic?
  - [ ] Does the parser reject unknown/unexpected fields where security-sensitive, or ignore safely without state corruption?
- [ ] **Semantic Unit Clarity**:
  - [ ] Are variable, column, and metric names explicit about their units (`timeout_ms`, `price_cents`, `retry_count`, `duration_seconds`)?
- [ ] **Contract Versioning & Backward Compatibility**:
  - [ ] Do API contract changes maintain backward compatibility with in-flight requests and previous client versions?
  - [ ] Is field deprecation handled via phased deprecation rather than breaking field removals?

---

## 4. Temporal & Concurrency Gate (Family E)

Assume concurrent execution, delays, out-of-order delivery, and mid-flight crashes.

- [ ] **Atomic Conditional Writes over TOCTOU**:
  - [ ] Are read-then-write operations converted to atomic conditional updates (`UPDATE ... WHERE version = X` or `INSERT ... ON CONFLICT`)?
- [ ] **Crash-Safe Multi-Step Workflows**:
  - [ ] If an operation crashes after step $K$ of $N$, can the system cleanly resume or roll back via compensation?
  - [ ] Are all state transition steps persisted in a state machine table before external network calls?
- [ ] **Logical Clocks over System Clocks**:
  - [ ] Are ordering and concurrency decisions made using monotonic version counters / sequence IDs rather than trusting machine wall clocks (`Date.now()`)?
- [ ] **At-Least-Once Delivery Defenses**:
  - [ ] Does every message consumer and webhook handler implement idempotency deduplication with unique request tokens?

---

## 5. Unbounded Resources & Feedback Loops Gate (Family F)

Bound every resource and ensure failure sheds load instead of amplifying it.

- [ ] **Explicit Finite Upper Bounds**:
  - [ ] Is there an explicit limit on payload sizes, pagination `limit`, string lengths, array item counts, and concurrent workers?
  - [ ] Is `OFFSET` pagination replaced with keyset/cursor-based pagination (`WHERE id > last_seen_id LIMIT N`) for large tables?
- [ ] **Negative Feedback Loop Implementation**:
  - [ ] Do downstream network failures trigger exponential backoff with full jitter and circuit breakers?
  - [ ] Does autoscaling protect the shared database from connection saturation (e.g. via connection pooling like PgBouncer)?
- [ ] **Resource Headroom Monitoring**:
  - [ ] Are alerts configured at 70% utilization for integer primary keys, table storage, connection pools, and queue depths?

---

## 6. Coupling & Shared Fate Isolation Gate (Family G)

Independent services must not share unmonitored failure domains.

- [ ] **Bulkheading & Blast Radius Limits**:
  - [ ] Are high-volume or adversarial tenants isolated via dedicated worker pools or strict per-tenant rate limit quotas?
- [ ] **Degraded Mode Fallbacks**:
  - [ ] If an auxiliary service (recommendations, analytics, search) goes down, does the core transaction flow continue seamlessly in degraded mode?
- [ ] **Independent Recovery Tooling**:
  - [ ] Can runbooks, admin portals, and deployment pipelines operate when the primary application database or main cluster is down?

---

## 7. Observability & Blindness Prevention (Family H)

Detect failures by observing business outcomes, not just server uptime.

- [ ] **Business Invariant Alerts**:
  - [ ] Are alerts triggered directly on business invariant anomalies (e.g., zero successful checkouts in 10 minutes, discrepancy in ledger totals)?
- [ ] **Error Visibility & Context**:
  - [ ] Are all exceptions logged with structured metadata, request context, and distributed trace IDs?
  - [ ] Are catch blocks checked to ensure no errors are swallowed or converted into empty arrays without alerts?
- [ ] **Tail Latency Tracking**:
  - [ ] Are dashboards focused on p99/p99.9 latency and error rates rather than misleading averages?

---

## 8. Change Management & Evolution Safety (Family I)

Software and infrastructure must evolve through reversible, backward-compatible transitions.

- [ ] **Expand-Migrate-Contract Pattern**:
  - [ ] **Expand**: Add new database column/field as optional/nullable while keeping the old field populated.
  - [ ] **Migrate**: Update all writers to write to both fields; backfill historical data.
  - [ ] **Contract**: Switch readers to the new field, stop writing to the old field, and deprecate/drop the old column in a subsequent release.
- [ ] **Configuration as Code**:
  - [ ] Are feature flags and configuration changes validated with schema checking and rolled out gradually via canary rings?

---

## 9. Verification & Testing Integrity (Family J & K)

Tests must evaluate adversarial, concurrent, and high-scale conditions.

- [ ] **Scale & Chaos Testing**:
  - [ ] Are database queries benchmarked against production-scale datasets with realistic index cardinality and distribution?
  - [ ] Are tests conducted under simulated network latency, packet loss, and worker crashes?
- [ ] **Negative & Boundary Test Coverage**:
  - [ ] Does the test suite assert failure handling for empty payloads, negative numbers, maximum bounds, and malformed inputs?
