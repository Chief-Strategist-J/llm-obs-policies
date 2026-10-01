# Checklist 06: Domain-Specific Systems

**Source Reference**: [Domain-Specific Edge Cases (Parts 59–68)](file:///home/btpl-lap-22/live/llm-obs-infra/policies/rules/edgeCases/domain-specific-edge-cases.md)  
**Objective**: Eliminate edge-case bugs across Payments/Ledgers, Multi-Tenant SaaS/Billing, Offline-First Sync/CRDTs, ML/Data Pipelines, and Messaging.

---

## 1. Payments & Double-Entry Financial Ledgers

- [ ] **Immutable Double-Entry Accounting**:
  - [ ] Are all financial mutations recorded as append-only ledger entries, never mutating an existing balance row in place?
  - [ ] Does every transaction enforce zero-sum balance: $\sum \text{Debits} - \sum \text{Credits} = 0$?
  - [ ] Are account balances calculated as derived materialized views or validated periodically against the underlying ledger log?
- [ ] **Currency Representation & Rounding Precision**:
  - [ ] Are amounts stored as integers in lowest minor units (cents, satoshis) or exact-precision numeric types (`NUMERIC(28, 8)`), never IEEE floating-point numbers?
  - [ ] Is rounding calculated using Half-Even (Banker's Rounding) to prevent directional accumulation bias over large transaction sets?
- [ ] **Payment Gateway Webhooks & Idempotency**:
  - [ ] Are gateway webhooks verified against cryptographic signatures before processing?
  - [ ] Does webhook ingestion record an idempotency key in the ledger transaction table before executing fulfillment?
  - [ ] Are duplicate webhook retries handled as idempotent no-ops?
- [ ] **Refund, Chargeback & Cancellation Races**:
  - [ ] Is partial and full refund tracking locked against concurrent duplicate requests?
  - [ ] Are refunds capped: $\sum \text{Refunds} \le \text{Original Captured Amount}$ via database constraints?

---

## 2. Multi-Tenant SaaS, Metering & Subscriptions

- [ ] **Hard Tenant Isolation**:
  - [ ] Are tenant identifiers verified at the gateway and injected into the execution context?
  - [ ] Are shared resources (queues, caches, DB connection pools) partitioned or rate-limited per tenant to prevent "noisy neighbor" starvation?
- [ ] **Usage Metering & Overages**:
  - [ ] Are usage events ingested idempotently with unique event IDs?
  - [ ] Does usage aggregation use streaming windowing (e.g. tumbling/sliding windows) that accounts for late-arriving usage logs?
- [ ] **Proration & Billing Cycle Boundaries**:
  - [ ] Are subscription upgrades/downgrades calculated based on UTC timestamps?
  - [ ] Are grace periods and payment retry schedules (dunning) modeled with explicit state machine transitions?

---

## 3. Mobile, Offline-First & Sync

- [ ] **Conflict Resolution & CRDTs**:
  - [ ] Are offline concurrent edits resolved via CRDTs (Conflict-free Replicated Data Types) or explicit deterministic merge rules rather than naive client-timestamp Last-Write-Wins (LWW)?
- [ ] **Tombstone Garbage Collection**:
  - [ ] When records are deleted offline, are they preserved as soft-deleted tombstones until all authorized client devices have acknowledged sync?
  - [ ] Is there an upper-bound TTL on tombstones with full re-sync fallbacks for dormant devices?
- [ ] **Schema Migration across Multi-Version Clients**:
  - [ ] Does backend sync support clients running older app versions ($V - 3$)?

---

## 4. Data Pipelines, Analytics & ML Systems

- [ ] **Late-Arriving Data & Watermarking**:
  - [ ] Do streaming pipelines (Flink, Spark Streaming) implement bounded watermarks to handle out-of-order and delayed event ingestion?
- [ ] **Idempotent Backfills**:
  - [ ] Are backfill and replay jobs idempotent (e.g. partition overwrite instead of append) to avoid duplicating historical analytics?
- [ ] **ML Training-Serving Feature Skew**:
  - [ ] Are features logged at inference time identically formatted to training feature store extracts?
  - [ ] Are automated monitors tracking feature drift (Kolmogorov-Smirnov test, PSI) and prediction drift?

---

## 5. Notifications & Messaging Delivery

- [ ] **Deduplication & Anti-Spam Throttling**:
  - [ ] Are outbound notifications deduplicated across channels (email, SMS, push) to prevent user flooding during retry loops?
- [ ] **Timezone-Aware Quiet Hours**:
  - [ ] Are non-urgent marketing/informational messages deferred during the recipient's local night hours?
- [ ] **Unsubscribe & Opt-Out Invariants**:
  - [ ] Is user unsubscribe / opt-out status checked at the final delivery hop immediately before sending?
  - [ ] Are bounce and complaint webhooks ingested to suppress dead email addresses automatically?
