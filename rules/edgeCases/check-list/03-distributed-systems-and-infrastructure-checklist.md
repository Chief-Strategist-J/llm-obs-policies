# Checklist 03: Distributed Systems & Infrastructure Scale

**Source Reference**: [Distributed Systems Edge Cases (Parts 18–28)](file:///home/btpl-lap-22/live/llm-obs-infra/policies/rules/edgeCases/distributed-systems-edge-cases.md)  
**Objective**: Guarantee distributed safety across network partitions, clock skews, process freezes, lock expiries, and cascading traffic storms.

---

## 1. Distributed Concurrency & Locking Safety

- [ ] **Distributed Locks Must Use Fencing Tokens**:
  - [ ] Are all distributed locks (Redis Redlock, Postgres advisory locks, Consul, Zookeeper) paired with monotonically increasing fencing tokens?
  - [ ] Does the storage/resource layer check that incoming writes provide a fencing token strictly greater than the previously accepted token:
    ```sql
    UPDATE target_resource 
    SET data = :payload, last_fencing_token = :current_token 
    WHERE id = :resource_id AND last_fencing_token < :current_token;
    ```
  - [ ] If 0 rows are updated, is the write rejected as an expired/stale lease (preventing split-brain data corruption during long GC pauses)?
- [ ] **Lock Lease Heartbeats & Safe Expiration**:
  - [ ] Are lock TTLs sufficiently longer than expected task duration, with asynchronous renewal background threads?
  - [ ] If lease renewal fails, does the task immediately abort execution and release resources?
- [ ] **Lock Ordering for Deadlock Avoidance**:
  - [ ] When acquiring multiple locks/resources, are they always acquired in a deterministic global order (e.g., sorted alphabetically by resource ID)?

---

## 2. Clocks, Time & Ordering Assumptions

- [ ] **Monotonic Clocks for Duration & Latency**:
  - [ ] Are duration calculations, timeouts, and benchmark metrics measured using monotonic clocks (`clock_gettime(CLOCK_MONOTONIC)`, `process.hrtime()`, `time.Now().Sub()`), never system wall clocks?
- [ ] **Wall Clock Skew & Leap Seconds**:
  - [ ] Is wall-clock synchronization monitored via NTP/PTP with maximum skew alerts ($\Delta > 100\text{ms}$)?
  - [ ] Are business orderings dependent on monotonic sequence numbers, Raft log indices, or Lamport timestamps rather than distributed wall clocks?

---

## 3. Network Partitions & Partial Failures

- [ ] **Split-Brain Mitigation**:
  - [ ] Do cluster consensus decisions (Raft, Paxos, etcd) require a strict majority quorum ($Q = \lfloor N/2 \rfloor + 1$)?
  - [ ] Are cluster nodes configured with odd counts ($N=3, 5, 7$) to avoid tied split-brain votes?
- [ ] **Handling Half-Open Connections & TCP Keepalives**:
  - [ ] Are TCP keepalives enabled (`SO_KEEPALIVE`, `TCP_KEEPIDLE`, `TCP_KEEPINTVL`) to detect silent connection drops through firewalls and NAT gateways?
  - [ ] Are client-side and server-side idle connection timeouts configured symmetrically?

---

## 4. Cascading Failures & Backpressure Defenses

- [ ] **Exponential Backoff with Full Jitter**:
  - [ ] Are all retries implemented using exponential backoff with full jitter to eliminate resonant synchronization waves:
    $$\text{Sleep} = \text{random}(0, \min(M, B \times 2^{\text{attempt}}))$$
- [ ] **Retry Budgets & Circuit Breakers**:
  - [ ] Are client retries constrained by a finite retry budget (e.g. retries can consume at most 10% of total outbound requests)?
  - [ ] Do downstream calls route through a circuit breaker that fails fast when error rate exceeds threshold (e.g. 50% over 10s)?
- [ ] **Deadline Propagation / Context Budgets**:
  - [ ] Is an end-to-end request deadline passed through HTTP (`X-Request-Deadline` / `grpc-timeout`) across all service hops?
  - [ ] If the remaining deadline is $\le 0$, is execution aborted immediately before performing expensive downstream work?
- [ ] **Load Shedding & Queue Dropping**:
  - [ ] Do saturated services drop or reject traffic early (`HTTP 429 / 503`) using CoDel or queue-depth limits rather than buffering requests until memory exhaustion?

---

## 5. Caching, Thundering Herds & Secondary Storage

- [ ] **Cache Stampede Prevention**:
  - [ ] Are cache keys populated with probabilistic early expiration (XFetch algorithm) or single-flight mutexes (Go `singleflight`, Redis mutex)?
  - [ ] Do cache TTLs include random jitter (e.g. TTL $\pm 10\%$) to prevent synchronized bulk expirations?
- [ ] **Cache Invalidation Consistency**:
  - [ ] Does cache eviction occur *after* the database transaction commits, or rely on CDC-driven cache updates?
  - [ ] Is fallback behavior defined for when cache servers are completely unreachable?

---

## 6. Code Smells & Architectural Anti-Pattern Audit

- [ ] **No Naked `sleep()` in Production or Concurrency Control**:
  - [ ] Verify that code never uses `sleep(100ms)` as a synchronization or retry mechanism.
- [ ] **No Unbounded Fan-Out**:
  - [ ] Are concurrent asynchronous tasks (goroutines, Promises, threads) managed via bounded worker pools (`semaphore`, `errgroup` with limit), never unrestricted `Promise.all(unboundedList.map(...))`?
- [ ] **No Silent Fallbacks**:
  - [ ] Does fall-back logic emit structured warnings and metrics so degraded mode operation is immediately visible to operators?
