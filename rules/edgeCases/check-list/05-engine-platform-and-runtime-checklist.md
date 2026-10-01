# Checklist 05: Engine, Platform & Runtime Deep Internals

**Source Reference**: [Engine, Platform, and Runtime-Specific Edge Cases (Parts 44–58)](file:///home/btpl-lap-22/live/llm-obs-infra/policies/rules/edgeCases/engine-platform-runtime-specific-edge-cases.md)  
**Objective**: Prevent engine-specific traps across PostgreSQL, MySQL, Redis, Kafka, Elasticsearch, Kubernetes, Cloud IAM/S3, and runtime languages (Go, Node, Python, JVM).

---

## 1. PostgreSQL Deep Internals

- [ ] **Transaction ID (XID) Wraparound Prevention**:
  - [ ] Are monitors tracking `datfrozenxid` age with alarms firing at $> 1.2 \text{ billion}$ transactions to prevent emergency database read-only freeze?
  - [ ] Is `autovacuum` tuned aggressively on high-write tables (`autovacuum_vacuum_scale_factor = 0.05`, `autovacuum_cost_limit = 2000`)?
- [ ] **DDL Lock Queues & Lock Timeouts**:
  - [ ] Do all migration scripts set `SET lock_timeout = '2s';` to prevent DDL statements waiting on locks from blocking all incoming reads/writes?
  - [ ] Are indexes created using `CREATE INDEX CONCURRENTLY` outside transaction blocks?
- [ ] **Prepared Statement Cache Invalidation**:
  - [ ] When schema alterations occur, are connection pools configured to reset prepared statements to avoid plan invalidation crashes?

---

## 2. MySQL (InnoDB) Specifics

- [ ] **Gap Locks & Next-Key Lock Deadlocks**:
  - [ ] Are `SELECT ... FOR UPDATE` or `UPDATE` statements on non-indexed columns audited to avoid full-table gap locks in Repeatable Read isolation?
- [ ] **Metadata Lock (MDL) Queue Cascades**:
  - [ ] Are long-running `SELECT` queries monitored and terminated before attempting `ALTER TABLE` operations?

---

## 3. Redis & In-Memory Storage

- [ ] **Blocking Command Elimination**:
  - [ ] Are dangerous $O(N)$ commands (`KEYS *`, `HGETALL` on large maps, `SMEMBERS`, `FLUSHALL`) banned in production and replaced with `SCAN`, `HSCAN`, or `SSCAN`?
- [ ] **Memory Eviction Policy & Fragmentation**:
  - [ ] Is `maxmemory-policy` explicitly configured (`volatile-lru` or `noeviction` depending on caching vs persistence role)?
  - [ ] Is memory fragmentation ratio monitored ($\text{Ratio} > 1.5$ requires active defragmentation)?
- [ ] **AOF Fsync vs. Latency Spikes**:
  - [ ] Is `appendfsync` set to `everysec` with `no-appendfsync-on-rewrite yes` to prevent disk I/O flushes from blocking Redis single-threaded event loop?

---

## 4. Kafka & Message Brokers

- [ ] **Consumer Rebalance Minimization**:
  - [ ] Is `max.poll.interval.ms` configured with sufficient headroom above max message processing duration to prevent rebalance storms?
  - [ ] Are consumer group partitions assigned using cooperative sticky partition assignors?
- [ ] **Poison Pill Elimination & DLQ**:
  - [ ] Do Kafka consumers catch un-parseable or malformed payloads and route them to a Dead-Letter Queue (DLQ) rather than failing the consumer in an infinite loop?
- [ ] **Partition Key Skew**:
  - [ ] Are partition keys checked for uniform cardinality to prevent a single hot tenant/user overloading a single partition?

---

## 5. Elasticsearch & Secondary Search Indexes

- [ ] **Mapping Explosions**:
  - [ ] Is dynamic field mapping disabled or restricted (`index.mapping.total_fields.limit`) to prevent JSON payloads with arbitrary keys exhausting cluster metadata memory?
- [ ] **Refresh vs. Flush Lag Awareness**:
  - [ ] Do applications understand that documents are searchable only after `refresh_interval` (default 1s), and not immediately upon HTTP 201 response?

---

## 6. Kubernetes & Container Orchestration

- [ ] **Graceful Termination & PreStop Hooks**:
  - [ ] Do Pod specifications include `preStop: exec: sleep 5` to allow ingress routers to remove the endpoint before the container receives `SIGTERM`?
  - [ ] Does the application handle `SIGTERM`, stop accepting new traffic, finish in-flight requests, and exit within `terminationGracePeriodSeconds`?
- [ ] **Readiness vs. Liveness Probe Disconnection**:
  - [ ] **Liveness Probe**: Only checks if process is alive / un-deadlocked (does NOT ping downstream DB/Kafka).
  - [ ] **Readiness Probe**: Checks if the instance is ready to receive network traffic.
- [ ] **CPU Throttling vs. OOMKill**:
  - [ ] Are memory limits set with headroom to avoid hard OOMKill termination?

---

## 7. Cloud Provider Traps (AWS / GCP / Azure)

- [ ] **S3 / Blob Storage Lifecycle & Metadata**:
  - [ ] Are S3 upload workflows protected against partial multipart uploads eating storage costs via S3 Lifecycle abort rules?
- [ ] **IAM Permission Eventual Consistency**:
  - [ ] Do automation scripts account for 10–30s replication delay after creating IAM roles/policies before assuming them?
- [ ] **API Rate Limit Handling**:
  - [ ] Do cloud API calls (AWS STS, EC2, CloudWatch) implement exponential backoff to handle `ThrottlingException` / `RateExceeded`?

---

## 8. Language & Runtime Traps

### Go
- [ ] **Goroutine & Channel Leak Audit**:
  - [ ] Does every goroutine have an exit condition bound to a `context.Context` or done channel?
  - [ ] Are unbuffered channels evaluated to ensure writers do not block indefinitely if readers terminate?
- [ ] **Nil Interface Trap**:
  - [ ] Verify that concrete nil pointers are not returned as non-nil `error` or `interface{}` types.

### Node.js / TypeScript
- [ ] **Event Loop Non-Blocking**:
  - [ ] Are heavy CPU tasks (crypto, JSON parsing of massive files, compression) offloaded to worker threads?
- [ ] **Unhandled Rejections**:
  - [ ] Is `process.on('unhandledRejection')` configured with proper logging and alert dispatch?

### Python
- [ ] **GIL Bottlenecks & Asyncio Safety**:
  - [ ] Are CPU-bound routines executed in `multiprocessing` or native extensions rather than blocking the asyncio event loop?
  - [ ] Are mutable default arguments (`def func(items=[])`) eliminated.

### Java / JVM
- [ ] **GC Pause & Metaspace Leak Monitoring**:
  - [ ] Are garbage collector pauses monitored (e.g. ZGC/G1GC) to ensure STW (Stop-The-World) pauses do not cause distributed lease expirations?
