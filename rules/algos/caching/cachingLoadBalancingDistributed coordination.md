# Part 2: Caching, load balancing and distributed coordination (#51–100)

Same format and the same contract (roles; rules T1–T8; guardrails TX1–TX5). Already covered elsewhere and not repeated: consistent hashing basics (G79), Raft (G76, V#136), leader leases and fencing (G74–G75), vector and Lamport clocks (G80), token bucket (G66), circuit breakers (G36), hedged requests (G75 in code ref), gossip (graph #309), two-phase commit (G86), quorums (V#137).

## B1. Cache eviction and admission

### 51. LRU (least recently used)

**Definition:** An eviction policy that removes the item that hasn't been accessed for the longest time.

**How it works:**
1. Keep a hash map from key to node, and a doubly linked list ordered by recency.
2. **Get:** look up the node, move it to the head of the list (most recent).
3. **Put:** insert at the head. If the cache is full, remove the tail (least recent) from both the list and the map.
4. All operations are O(1).
5. **Concurrent versions:** lock striping, or buffer access events and apply them to the list in batches (as Caffeine does), because a global list lock is a bottleneck.

**Cost:** O(1) per operation. Two pointers per entry.

**Agent use:**
- **Role:** Coordinator.
- **How:** A safe default for workloads where recent items are likely to be reused (session data, recent queries).
- **Rules:** Measure the hit ratio under real traffic before tuning anything else.
- **Guardrails:** A single large scan (a batch job reading many keys once) flushes the whole LRU cache. Use scan-resistant policies (#54–57) for mixed workloads.

### 52. LFU (least frequently used) in O(1)

**Definition:** An eviction policy that removes the item with the fewest accesses, implemented with constant-time operations.

**How it works:**
1. Keep a map from key to node, and a list of frequency buckets, each holding the items with that access count (in LRU order within the bucket, for tie-breaking).
2. **Access:** move the item from bucket f to bucket f+1 (creating it if needed).
3. **Evict:** take the least recent item from the lowest-frequency bucket.
4. Track the current minimum frequency.
5. **Aging:** periodically halve all counts (or use decaying counters), so items that were popular long ago don't stay forever.

**Cost:** O(1) per operation.

**Agent use:**
- **Role:** Coordinator.
- **How:** Workloads with stable popularity (reference data, popular product pages).
- **Rules:** Always use aging. Plain LFU never adapts to changing popularity.
- **Guardrails:** New items start with low counts and get evicted before they can prove themselves. Admission policies (#56) handle this better.

### 53. CLOCK and CLOCK-Pro

**Definition:** Approximations of LRU that avoid moving items on every access, by using a reference bit and a circular "clock hand".

**How it works:**
1. Items sit in a circular buffer, each with a reference bit.
2. **On access:** set the item's reference bit to 1 (no list manipulation, so it's cheap and concurrency-friendly).
3. **On eviction:** advance the clock hand. If the item's bit is 1, clear it and move on (a "second chance"). If it's 0, evict it.
4. **CLOCK-Pro:** separates hot and cold items, and tracks recently evicted items ("non-resident" entries) to adapt how much space hot items get, which approximates the much better LIRS policy.

**Cost:** O(1) access. Amortized O(1) eviction.

**Agent use:**
- **Role:** Coordinator.
- **How:** Page caches and buffer pools (operating systems, databases), and highly concurrent caches where list updates are too costly.
- **Rules:** Use CLOCK-Pro or similar adaptive variants for mixed workloads.
- **Guardrails:** None specific.

### 54. ARC (adaptive replacement cache)

**Definition:** An eviction policy that balances recency and frequency automatically, adapting to the workload by learning from recently evicted keys.

**How it works:**
1. Two lists of cached items: **T1** (seen once recently, recency) and **T2** (seen at least twice, frequency).
2. Two "ghost" lists **B1** and **B2** hold the keys (not values) recently evicted from T1 and T2.
3. A target size p for T1 adapts: a hit in B1 means T1 was too small, so increase p; a hit in B2 means T2 was too small, so decrease p.
4. Evict from T1 or T2 according to p.
5. Scan-resistant: a scan fills T1 only, without flushing the frequent items in T2.

**Cost:** O(1) per operation. Ghost lists cost memory for keys.

**Agent use:**
- **Role:** Coordinator.
- **How:** Workloads that shift between recency-heavy and frequency-heavy patterns, such as storage and database caches.
- **Rules:** Compare against W-TinyLFU (#56) on recorded traces.
- **Guardrails:** Check licensing for the exact algorithm in your context (it was historically patented).

### 55. 2Q and segmented LRU (SLRU)

**Definition:** Scan-resistant policies that require items to prove their value in a probationary area before entering the main (protected) area.

**How it works:**
1. **SLRU:** two LRU segments, probationary and protected. New items enter probationary. A hit in probationary promotes the item to protected. When protected is full, its least recent items demote back to probationary.
2. **2Q:** new items enter a FIFO queue (A1in). If they're accessed again after being evicted from it (tracked by a ghost list A1out), they enter the main LRU (Am).
3. One-time accesses (scans) never reach the protected or main area.

**Cost:** O(1).

**Agent use:**
- **Role:** Coordinator.
- **How:** Simple, effective scan resistance. SLRU is the main region inside W-TinyLFU (#56).
- **Rules:** Size the protected segment to about 80% of the cache as a starting point, then tune on traces.
- **Guardrails:** None specific.

### 56. W-TinyLFU (windowed TinyLFU admission)

**Definition:** A high-hit-ratio cache design combining a small LRU window for new items with a frequency-based admission filter that decides whether a newcomer deserves to replace an existing item.

**How it works:**
1. **Window cache:** a small LRU (about 1% of capacity) admits every new item, absorbing bursts of recent items.
2. **Main cache:** a segmented LRU (#55).
3. **Admission:** when the window evicts an item (the candidate), compare its estimated frequency against the main cache's eviction victim. The candidate enters the main cache only if it's more frequent.
4. **Frequency estimates:** a count-min-style sketch with small 4-bit counters ("TinyLFU"). Periodically halve all counters ("reset"), for aging.
5. **A doorkeeper Bloom filter** absorbs one-time items before they reach the sketch.
6. **Adaptive variants** resize the window by hill climbing on the hit rate.

**Cost:** O(1). The sketch uses about 1 byte per cached entry.

**Agent use:**
- **Role:** Coordinator.
- **How:** A strong general-purpose default (used by Caffeine and many systems) with near-optimal hit rates across diverse workloads.
- **Rules:** Measure the hit ratio against recorded traces when choosing between policies.
- **Guardrails:** None specific.

### 57. S3-FIFO

**Definition:** A simple, scalable eviction policy using three FIFO queues, which removes most one-hit items quickly and matches or beats LRU-based policies on many real workloads.

**How it works:**
1. **Small queue S** (about 10% of capacity), **main queue M** (90%) and a **ghost queue G** (recently evicted keys only).
2. New items enter S, unless their key is in G (then they go straight to M).
3. **Evicting from S:** if the item was accessed while in S, move it to M; otherwise evict it and record its key in G.
4. **Evicting from M:** like CLOCK, an item with a nonzero access counter gets reinserted (with the counter decremented); otherwise it's evicted.
5. Only FIFO operations (no list reordering on hits), so it's lock-friendly and fast.

**Cost:** O(1), with very low per-access overhead.

**Agent use:**
- **Role:** Coordinator.
- **How:** High-throughput caches (CDNs, key-value stores) where per-access overhead and lock contention matter.
- **Rules:** Validate on your own traces against W-TinyLFU.
- **Guardrails:** None specific.

### 58. Hierarchical timing wheels (TTL expiry and timers)

**Definition:** A data structure for managing very large numbers of timers (TTLs, timeouts) with O(1) insertion and expiry.

**How it works:**
1. **Simple timing wheel:** a circular array of buckets, one per time tick. A timer due in d ticks goes into bucket (current + d) mod size. Each tick, expire everything in the current bucket.
2. **Hierarchical:** several wheels with coarser ticks (seconds, minutes, hours), like a clock's hands. Long timers go into a coarse wheel, and cascade down into finer wheels as their time approaches.
3. Insert and cancel are O(1). Each tick processes only one bucket.

**Cost:** O(1) per timer operation.

**Agent use:**
- **Role:** Coordinator.
- **How:** Cache TTL expiry, connection and request timeouts, delayed retries, and session expiry, at very high timer counts (used in Kafka, Netty and Linux).
- **Rules:** Choose the tick resolution by the precision needed (coarser ticks are cheaper).
- **Guardrails:** Expiry precision is limited to one tick. Don't use it where exact timing matters.

## B2. Cache patterns and consistency

### 59. Write policies (write-through, write-back, write-around)

**Definition:** Rules for how writes are applied to the cache and the backing store.

**How it works:**
1. **Write-through:** write to the cache and the store synchronously. The cache is always consistent; writes are slower.
2. **Write-back (write-behind):** write to the cache, and asynchronously flush to the store later, often batched. Fast writes, but data is lost if the cache fails before flushing.
3. **Write-around:** write only to the store, and invalidate the cache entry. Avoids filling the cache with data that might not be read.
4. Combine with a read policy (#60).

**Cost:** Trades write latency against durability and consistency.

**Agent use:**
- **Role:** Coordinator.
- **How:** Write-through for data that must be consistent, write-back for high-volume counters and metrics where small losses are acceptable, write-around for write-once data.
- **Rules:** Document the policy and its failure behavior per cache.
- **Guardrails:** Never use write-back for data that can't be lost (payments, user data) without a durable write-ahead log.

### 60. Cache-aside, read-through and refresh-ahead

**Definition:** Patterns for how data gets into a cache on reads, and how it's kept fresh.

**How it works:**
1. **Cache-aside:** the application checks the cache. On a miss, it reads from the store and writes the result to the cache. Simple and common.
2. **Read-through:** the cache itself loads missing data from the store (with a loader function). The application only talks to the cache.
3. **Refresh-ahead:** the cache reloads popular items asynchronously before they expire (for example when 80% of the TTL has passed and the item is accessed), so readers rarely see a miss.
4. **Stale-while-revalidate:** serve the stale value immediately, and refresh it in the background.

**Cost:** Refresh-ahead costs extra background loads.

**Agent use:**
- **Role:** Coordinator.
- **How:** Refresh-ahead and stale-while-revalidate keep latency low for hot keys, which matters for agent tools making many repeated lookups.
- **Rules:** Set a maximum staleness for serving stale values.
- **Guardrails:** Cache-aside has a race: a stale value written after a newer invalidation. Use versioned values or leases (#62).

### 61. Cache stampede prevention (request coalescing, probabilistic early expiration)

**Definition:** Preventing many simultaneous misses on the same key (when a popular item expires) from overwhelming the backing store.

**How it works:**
1. **Locking / single-flight:** the first request to miss takes a lock (or registers in-flight) and recomputes. Others wait for its result, or serve the stale value.
2. **Probabilistic early expiration (XFetch):** each reader recomputes early with a probability that grows as expiry approaches: recompute if (now − Δ × β × log(random)) ≥ expiry, where Δ is the recomputation time. One request usually refreshes before expiry, and spikes never form.
3. **TTL jitter:** randomize TTLs (±10%), so many keys don't expire at the same moment.
4. **Stale-while-revalidate** (#60).

**Cost:** Small.

**Agent use:**
- **Role:** Coordinator.
- **How:** Protects databases and services from synchronized miss storms, a common cause of outages.
- **Rules:** Use jitter on all TTLs by default.
- **Guardrails:** Locks need timeouts, or a crashed recomputation blocks everyone.

### 62. Cache invalidation (versioned keys, event-driven invalidation, leases)

**Definition:** Keeping cached data consistent with the source when the source changes.

**How it works:**
1. **TTL only:** simplest, with bounded staleness.
2. **Event-driven invalidation:** on a source change (from CDC or an outbox, V#125–126), delete or update the cache entry.
3. **Versioned keys:** include a version in the cache key (`user:42:v17`). Updates bump the version, and old entries simply stop being read and expire.
4. **Leases (memcache-style):** on a miss, the cache gives the client a lease token. Only the holder of a valid token can fill the key. An invalidation in the meantime cancels the token, so a stale value fetched before the update can't be written afterward. Leases also throttle stampedes (#61).
5. **Delete, don't update:** on change, delete the cache entry rather than writing the new value, which avoids races between concurrent writers.

**Cost:** Event pipelines or version tracking.

**Agent use:**
- **Role:** Coordinator.
- **How:** Correct caching of mutable data: permissions, account status, configuration.
- **Rules:** Permission and access-control caches need short TTLs plus event-driven invalidation (TX3).
- **Guardrails:** Never cache authorization decisions longer than the acceptable revocation delay.

### 63. Negative caching

**Definition:** Caching "not found" results, so repeated lookups for missing keys don't hit the backing store every time.

**How it works:**
1. On a lookup that finds nothing, store a special "absent" marker with a short TTL.
2. Later lookups for that key return "not found" from the cache.
3. When the key is created, invalidate the marker (#62).
4. **Bloom filters** in front of the store can also reject keys that definitely don't exist.

**Cost:** Small.

**Agent use:**
- **Role:** Coordinator.
- **How:** Protects stores from repeated misses: probing for nonexistent IDs, typos, enumeration attacks.
- **Rules:** Use shorter TTLs for negative entries than for positive ones.
- **Guardrails:** Long negative TTLs hide newly created items. Make sure creation invalidates them.

### 64. Consistent hashing with bounded loads

**Definition:** Consistent hashing extended so no server receives more than (1 + ε) times the average load, by overflowing to the next server on the ring.

**How it works:**
1. Place servers on a hash ring (G79).
2. Each server has a capacity ⌈(1 + ε) × (total load / number of servers)⌉.
3. A key goes to its usual server on the ring. If that server is at capacity, it goes to the next server clockwise with spare capacity.
4. Keys still mostly stay in place when servers change, and no server gets overloaded by hot key clusters.

**Cost:** Small extra lookups when servers are full.

**Agent use:**
- **Role:** Coordinator.
- **How:** Cache cluster routing and request affinity (for example routing a tenant's requests to the same cache node), without hotspots.
- **Rules:** Tune ε: smaller gives better balance and more key movement.
- **Guardrails:** None specific.

### 65. Multi-tier caching and hot-key replication

**Definition:** Layering caches (in-process near caches in front of a distributed cache in front of the store), and replicating extremely hot keys to many nodes.

**How it works:**
1. **L1:** a small in-process cache per application instance (microseconds, no network).
2. **L2:** a shared distributed cache (milliseconds).
3. **L3:** the backing store.
4. Reads check L1 → L2 → L3, filling each layer on the way back.
5. **Invalidation** must reach every L1 copy: broadcast invalidation messages, or short L1 TTLs.
6. **Hot-key replication:** detect keys with extreme read rates (heavy-hitter sketches), and replicate them to several cache nodes (or into L1), with reads spread across replicas.

**Cost:** Memory for duplicate copies. Invalidation traffic.

**Agent use:**
- **Role:** Coordinator.
- **How:** Very low latency for hot reference data, and protection against single-node hotspots (one celebrity key overloading one cache shard).
- **Rules:** Keep L1 TTLs short for mutable data.
- **Guardrails:** Multi-tier caching multiplies places where stale or deleted data lives. Invalidation must cover all tiers (TX3).

## B3. Load balancing and overload control

### 66. Smooth weighted round-robin

**Definition:** Distributing requests across servers in proportion to their weights, while spreading each server's turns evenly rather than in bursts.

**How it works:**
1. Each server has a weight w_i and a running value c_i (initially 0).
2. For each request, add w_i to every c_i.
3. Pick the server with the largest c_i, then subtract the total weight from its c_i.
4. Over a cycle, each server gets exactly w_i picks, interleaved smoothly (weights 5, 1, 1 give a, a, b, a, c, a, a, not five a's in a row).

**Cost:** O(n) per pick (fine for small server counts).

**Agent use:**
- **Role:** Coordinator.
- **How:** Proportional distribution across servers of different capacity, or for gradual traffic shifting (canary weights).
- **Rules:** Use it for stable, similar requests. Load-aware methods (#67, #68, #72) adapt better to varying request costs.
- **Guardrails:** None specific.

### 67. Least connections and least outstanding requests

**Definition:** Sending each request to the server with the fewest active connections or in-flight requests.

**How it works:**
1. The load balancer tracks the number of in-flight requests per server.
2. Pick the server with the fewest, optionally divided by its weight.
3. Slow servers accumulate in-flight requests, so they automatically get fewer new ones.
4. Requires accurate, shared tracking. With many independent load balancers, each sees only its own requests.

**Cost:** O(n), or O(log n) with heaps.

**Agent use:**
- **Role:** Coordinator.
- **How:** Workloads with very variable request durations (some requests 10 ms, others 10 s).
- **Rules:** With many load balancer instances, combine with #68 to avoid herding.
- **Guardrails:** A failing server that responds fast with errors looks "least loaded" and attracts all traffic. Combine with outlier ejection (#75).

### 68. Power of two choices

**Definition:** Picking two servers at random and sending the request to the less loaded one, which gives nearly optimal balance with very little coordination.

**How it works:**
1. For each request, sample two servers uniformly at random.
2. Compare their load (in-flight requests, or latency scores).
3. Send to the less loaded.
4. **Theory:** the maximum load drops dramatically compared with one random choice (from about log n / log log n to about log log n above average, in the classic balls-into-bins analysis).
5. Avoids herding: many independent load balancers don't all pick the same "best" server at once.

**Cost:** O(1) per request.

**Agent use:**
- **Role:** Coordinator.
- **How:** A robust default for distributed client-side or proxy load balancing.
- **Rules:** Use with a load signal like in-flight requests or peak EWMA latency (#72).
- **Guardrails:** None specific.

### 69. Maglev hashing

**Definition:** A consistent hashing scheme that builds a lookup table for very fast, evenly balanced, minimally disruptive mapping of flows to backends.

**How it works:**
1. Choose a table size M, a prime much larger than the number of backends.
2. Each backend generates a permutation of table positions from two hashes of its name (offset and skip): positions offset, offset + skip, offset + 2 × skip, … mod M.
3. **Fill the table:** backends take turns claiming their next preferred empty slot, until the table is full. Each backend gets an almost equal share of slots.
4. **Lookup:** table[hash(flow) mod M]: one array access.
5. When a backend is added or removed, only a small fraction of slots change owners.

**Cost:** O(1) lookups. O(M × number of backends) table rebuilds.

**Agent use:**
- **Role:** Coordinator.
- **How:** High-speed network load balancers, and any affinity routing that needs even balance with minimal reshuffling.
- **Rules:** Pair with connection tracking, so existing flows survive table changes.
- **Guardrails:** None specific.

### 70. Rendezvous hashing (highest random weight)

**Definition:** Assigning each key to the server with the highest hash score for that (key, server) pair, which gives consistent assignment without a ring.

**How it works:**
1. For key k, compute score(k, s) = hash(k, s) for every server s.
2. Assign k to the server with the highest score. For replication, take the top r servers.
3. **Removing a server:** only its keys move, each to its own next-highest server, which spreads them evenly.
4. **Weighted variant:** score = −w_s / ln(hash(k, s) normalized to (0, 1)).

**Cost:** O(n) per lookup (fine for small n). Hierarchical variants for large n.

**Agent use:**
- **Role:** Coordinator.
- **How:** Simple, balanced key-to-node assignment and replica placement, with no virtual nodes to tune.
- **Rules:** Use hierarchical rendezvous (racks → servers) for large clusters.
- **Guardrails:** None specific.

### 71. Jump consistent hash

**Definition:** A tiny, memory-free consistent hash that maps a key to one of n numbered buckets, moving only about 1/n of keys when n grows.

**How it works:**
1. Seed a pseudo-random generator with the key.
2. Starting from bucket b = 0, repeatedly "jump" forward to j = floor((b + 1) / random), while j < n.
3. The last b is the bucket.
4. Growing from n to n + 1 buckets moves exactly the expected 1/(n + 1) of keys, all into the new bucket.
5. Buckets must be numbered 0…n−1, and can only be added or removed at the end.

**Cost:** O(log n) time, no memory.

**Agent use:**
- **Role:** Coordinator.
- **How:** Sharding data across numbered shards (storage shards, partitions) that grow over time.
- **Rules:** Use only where shards are added at the end. Arbitrary server removal needs rendezvous or ring hashing.
- **Guardrails:** None specific.

### 72. Peak-EWMA latency-aware load balancing

**Definition:** Choosing servers by a latency estimate that reacts instantly to spikes and decays slowly, combined with in-flight load.

**How it works:**
1. Each server has a latency estimate.
2. On a new measurement: if it's higher than the estimate, jump to it immediately ("peak"). If lower, move toward it with exponential decay over a time window.
3. Cost score = estimated latency × (in-flight requests + 1).
4. Pick between servers with power-of-two-choices (#68) using the cost score.
5. A server that suddenly slows down is avoided within one request, and recovers gradually.

**Cost:** O(1) per request.

**Agent use:**
- **Role:** Coordinator.
- **How:** Latency-sensitive services with uneven backends (noisy neighbors, garbage collection pauses), as used in service meshes and RPC frameworks.
- **Rules:** Tune the decay window to the service's typical latency changes.
- **Guardrails:** Fast failures look like low latency. Exclude error responses from latency measurements, and combine with #75.

### 73. CoDel (controlled delay queue management)

**Definition:** An active queue management algorithm that controls queueing delay (not queue length), dropping or rejecting requests when delay stays above a target too long.

**How it works:**
1. Track each request's time spent waiting in the queue ("sojourn time").
2. If the minimum sojourn time over an interval (for example 100 ms) stays above a target (for example 5 ms), the queue is persistently overloaded (not just a short burst).
3. Enter a dropping state: drop (or reject) a request, then the next ones at increasing frequency (interval / √count), until the delay falls below the target.
4. Short bursts pass without drops.
5. **Server-side adaptation:** when overloaded, switch the queue to LIFO with short timeouts, so fresh requests (whose clients are still waiting) are served first.

**Cost:** Timestamps per request.

**Agent use:**
- **Role:** Coordinator.
- **How:** Keeps services responsive under overload, instead of building huge queues where every request times out anyway.
- **Rules:** Set targets from the service's latency SLO.
- **Guardrails:** Rejected requests must return clear "retry later" signals to clients (G35, G109-style).

### 74. Adaptive concurrency limits (AIMD, Vegas, gradient)

**Definition:** Discovering a service's safe number of concurrent requests automatically from measured latency, like TCP congestion control applied to request concurrency.

**How it works:**
1. Maintain a concurrency limit L. Requests beyond L are rejected or queued.
2. **AIMD:** increase L by 1 after each successful window, and halve it on errors, timeouts or latency above a threshold.
3. **Vegas-style:** compare the minimum latency (no queueing) with the current latency. Estimated queue = L × (1 − minRTT / currentRTT). Increase L when the queue is small, decrease when it grows.
4. **Gradient:** L_new = L × (minRTT / currentRTT) + queue allowance, with smoothing.
5. Limits are applied per client and per server, adapting continuously as capacity changes.

**Cost:** O(1) per request.

**Agent use:**
- **Role:** Coordinator.
- **How:** Protects services from overload without hand-tuned static limits, which go stale as code and hardware change.
- **Rules:** Combine with priority-aware rejection, so critical traffic is rejected last.
- **Guardrails:** Latency changes not caused by load (a slow dependency) can shrink limits unnecessarily. Monitor limit changes.

### 75. Outlier detection and ejection

**Definition:** Automatically removing misbehaving backends from load-balancing rotation, based on their recent errors or latency compared with their peers.

**How it works:**
1. Track per-backend statistics over a window: consecutive errors, error rate, latency percentiles.
2. **Eject** a backend when it exceeds thresholds (for example 5 consecutive 5xx errors), or is a statistical outlier versus the others (error rate more than k standard deviations above the mean).
3. Ejection lasts for a base time, increasing with repeated ejections.
4. **Maximum ejection percentage:** never eject more than a set fraction of backends (to avoid ejecting everyone during a widespread incident).
5. Return ejected backends to rotation after the time expires, and re-check.

**Cost:** Small.

**Agent use:**
- **Role:** Coordinator.
- **How:** Removes bad hosts (bad deploys, failing disks, noisy neighbors) faster than health checks alone.
- **Rules:** Always set a maximum ejection percentage.
- **Guardrails:** If many backends are being ejected, the problem is systemic. Alert rather than eject further.

## B4. Consensus and replication

### 76. Paxos (single-decree)

**Definition:** The classic algorithm for a group of processes to agree on a single value, tolerating crashes of a minority, with safety even under message delays and losses.

**How it works:**
1. **Roles:** proposers, acceptors (a majority forms a quorum) and learners.
2. **Phase 1 (prepare):** a proposer picks a unique, increasing proposal number n, and sends prepare(n) to the acceptors.
3. An acceptor promises not to accept proposals numbered below n, and replies with the highest-numbered proposal it has already accepted (if any).
4. **Phase 2 (accept):** if a majority promised, the proposer sends accept(n, v), where v is the value of the highest-numbered accepted proposal among the replies, or its own value if none.
5. Acceptors accept unless they've promised a higher number.
6. A value is chosen once a majority accepts the same proposal. Safety holds always; progress requires a stable leader (competing proposers can livelock).

**Cost:** Two round trips to a majority.

**Agent use:**
- **Role:** Verifier.
- **How:** The theoretical basis for consensus in replicated systems. Understanding it helps evaluate the correctness claims of infrastructure.
- **Rules:** Use proven implementations (etcd, ZooKeeper, consensus libraries). Never write a custom consensus protocol for production.
- **Guardrails:** None specific.

### 77. Multi-Paxos

**Definition:** Paxos extended to agree on a sequence of values (a replicated log) efficiently, with a stable leader skipping phase 1 for most entries.

**How it works:**
1. Elect a distinguished leader, which runs phase 1 once for all future log slots.
2. For each new command, the leader runs only phase 2 (accept) for the next slot: one round trip to a majority.
3. Committed entries are applied to every replica's state machine in log order.
4. On leader failure, a new leader runs phase 1, learns any accepted but uncommitted entries, and fills gaps (with no-ops if needed).
5. Raft (G76) is a closely related design with a more prescribed structure.

**Cost:** One round trip per command in steady state.

**Agent use:**
- **Role:** Verifier.
- **How:** Understanding replicated-log databases (Spanner and many others use Multi-Paxos variants).
- **Rules:** Same as #76.
- **Guardrails:** None specific.

### 78. ZAB and viewstamped replication

**Definition:** Leader-based replication protocols with primary-backup structure: ZAB (ZooKeeper Atomic Broadcast) and viewstamped replication.

**How it works:**
1. **Views or epochs:** each leadership period has a number. The leader orders all updates.
2. **Broadcast:** the leader proposes updates with (epoch, counter) identifiers. Followers acknowledge; once a majority acknowledges, the leader commits.
3. **Recovery / view change:** on leader failure, elect a new leader with the most complete history. It synchronizes followers (sending missing entries, or truncating divergent ones) before starting a new epoch.
4. **Primary order:** ZAB guarantees that a leader's updates are delivered in the order it sent them, and that every update from earlier epochs is delivered before new ones.

**Cost:** One round trip to a majority per update.

**Agent use:**
- **Role:** Verifier.
- **How:** Understanding the coordination services underlying many platforms (ZooKeeper powers configuration, leader election and locking in many systems).
- **Rules:** Same as #76.
- **Guardrails:** None specific.

### 79. Chain replication (and CRAQ)

**Definition:** Replicating data along a chain of servers: writes go to the head and propagate down, reads go to the tail. This gives strong consistency with high throughput.

**How it works:**
1. Servers form a chain: head → … → tail.
2. **Writes** enter at the head, are applied at each server in turn, and are acknowledged when they reach the tail.
3. **Reads** go to the tail, which has only committed data, so reads are strongly consistent.
4. **Failures:** a separate configuration service (often Paxos-based) removes failed servers and repairs the chain.
5. **CRAQ:** any server can serve reads. A server holding an uncommitted (dirty) version asks the tail for the committed version, spreading read load across the whole chain.

**Cost:** Write latency grows with chain length. Read throughput is high with CRAQ.

**Agent use:**
- **Role:** Coordinator.
- **How:** Understanding storage systems built on chain replication, which suit read-heavy, strongly consistent workloads.
- **Rules:** Pair with a consensus-based configuration manager.
- **Guardrails:** None specific.

### 80. Linearizable reads in consensus systems (ReadIndex, lease reads)

**Definition:** Ways to serve reads that reflect every committed write, without writing each read through the log.

**How it works:**
1. **Log reads:** append the read to the log like a write. Correct but slow.
2. **ReadIndex:** the leader records its current commit index, confirms it's still leader with a heartbeat round to a majority, waits until that index is applied, then serves the read locally.
3. **Lease reads:** the leader holds a time-based lease (followers promise not to elect another leader before it expires). During the lease, it serves reads locally with no round trip. This depends on bounded clock drift.
4. **Follower reads:** a follower asks the leader for its commit index (ReadIndex) and serves the read once it has caught up, spreading read load.

**Cost:** ReadIndex: one heartbeat round. Lease reads: none (with clock assumptions).

**Agent use:**
- **Role:** Coordinator.
- **How:** Understanding read consistency options in the agent's coordination stores (configuration, locks, leases), and choosing correctly per use case.
- **Rules:** Use ReadIndex or log reads for correctness-critical reads (lock checks), unless clock bounds are trusted.
- **Guardrails:** Lease reads with badly drifting clocks can return stale data. Monitor clock health (#100).

### 81. Cluster membership changes (joint consensus, single-server changes)

**Definition:** Safely adding or removing members of a consensus group without a moment where two separate majorities could both act.

**How it works:**
1. **The danger:** switching directly from an old member set to a new one could let the old majority and the new majority each elect a leader at the same time.
2. **Joint consensus:** first commit a combined configuration (old + new) where decisions need majorities of both sets, then commit the new configuration alone.
3. **Single-server changes:** add or remove one member at a time. Any majority of the old set and any majority of the new set always overlap, so no joint phase is needed.
4. **Learners / non-voting members:** new members first catch up on the log without voting, then become voters.

**Cost:** Extra configuration entries.

**Agent use:**
- **Role:** Coordinator.
- **How:** Executes cluster resizing and node replacement in consensus systems safely.
- **Rules:** Add replacements before removing failed members. Change one member at a time.
- **Guardrails:** TX4: membership changes need approval, and a check that a majority stays available throughout.

### 82. Practical Byzantine fault tolerance (PBFT)

**Definition:** Consensus that tolerates nodes that behave arbitrarily or maliciously (not just crashing), using 3f + 1 replicas to tolerate f faulty ones.

**How it works:**
1. A primary assigns sequence numbers to client requests.
2. **Pre-prepare:** the primary broadcasts the request with its sequence number.
3. **Prepare:** replicas broadcast prepare messages. A replica is "prepared" once it has 2f matching prepares plus the pre-prepare.
4. **Commit:** replicas broadcast commit messages, and execute after 2f + 1 matching commits.
5. Clients accept a result after f + 1 matching replies.
6. **View change:** if the primary appears faulty, replicas switch to a new primary.

**Cost:** O(n²) messages per request. 3f + 1 replicas.

**Agent use:**
- **Role:** Verifier.
- **How:** Relevant when participants don't fully trust each other (multi-organization ledgers, adversarial environments). Within one trusted organization, crash-fault protocols (#77, G76) suffice.
- **Rules:** Use only when Byzantine faults are a real threat. The cost is much higher.
- **Guardrails:** None specific.

## B5. Clocks and distributed transactions

### 83. Hybrid logical clocks (HLC)

**Definition:** Timestamps that combine physical time with a logical counter, so they stay close to wall-clock time while still respecting causality.

**How it works:**
1. Each timestamp is (l, c): l is the largest physical time seen; c is a counter for ordering within the same l.
2. **On a local or send event:** l′ = max(l, physical now). If l′ = l, increment c; otherwise c = 0.
3. **On receiving a message with (l_m, c_m):** l′ = max(l, l_m, physical now), and set c to order after both the local and the message timestamps.
4. If A causally precedes B, then HLC(A) < HLC(B), and l always stays within the clock skew of real time.

**Cost:** 64 bits per timestamp. O(1) updates.

**Agent use:**
- **Role:** Coordinator.
- **How:** Ordering events across services in a way that's both causally correct and human-readable, for event logs, MVCC timestamps and snapshot reads (used in CockroachDB and others).
- **Rules:** Monitor clock skew. HLC tolerates skew but stays close to it.
- **Guardrails:** None specific.

### 84. TrueTime and commit wait (Spanner)

**Definition:** Using clocks with explicit uncertainty bounds to give externally consistent (linearizable) transactions across a global database.

**How it works:**
1. **TrueTime API:** now() returns an interval [earliest, latest] guaranteed to contain the true time. The uncertainty ε is kept small with GPS and atomic clock references.
2. **Commit timestamp:** at commit, choose s = TT.now().latest.
3. **Commit wait:** wait until TT.now().earliest > s before making the commit visible, so the timestamp is definitely in the past for everyone.
4. Consequently, any transaction starting after this one commits gets a larger timestamp: commit order matches real time.
5. **Reads** at a timestamp can be served by any sufficiently up-to-date replica, without locks.

**Cost:** A commit wait of about 2ε per write transaction.

**Agent use:**
- **Role:** Verifier.
- **How:** Understanding globally consistent databases, and the trade-off between clock quality and write latency.
- **Rules:** Systems without bounded-uncertainty clocks use other methods (HLC with uncertainty intervals, #83).
- **Guardrails:** None specific.

### 85. Percolator (snapshot isolation over a key-value store)

**Definition:** A protocol for distributed transactions with snapshot isolation on top of a key-value store with single-row atomicity, using a timestamp oracle and locks stored in the data itself.

**How it works:**
1. A central timestamp oracle hands out monotonically increasing timestamps.
2. A transaction reads at its start timestamp (a snapshot).
3. **Prewrite:** for each written cell, check there's no newer committed write and no lock. Write the data at the start timestamp, plus a lock. One lock is the "primary"; the others point to it.
4. **Commit:** get a commit timestamp. Replace the primary lock with a commit record (an atomic single-row operation, which is the commit point). Then clean up the secondary locks.
5. **Crash recovery:** a reader that finds a lock checks the primary. If the primary committed, roll the secondary forward; if it's abandoned, roll back.

**Cost:** Several round trips per transaction. The timestamp oracle can be a bottleneck (batching helps).

**Agent use:**
- **Role:** Verifier.
- **How:** Understanding transactional key-value databases built on this model (TiDB/TiKV and others), and their contention behavior.
- **Rules:** Expect write conflicts on hot rows. Design to spread writes.
- **Guardrails:** None specific.

### 86. Calvin (deterministic transaction ordering)

**Definition:** Distributed transactions that are first ordered globally by a sequencing layer, then executed deterministically by every replica in that order, avoiding two-phase commit.

**How it works:**
1. **Sequencing:** transactions are collected in short epochs (for example 10 ms) and ordered globally (replicated with Paxos).
2. **Scheduling:** each partition acquires locks in the global order, deterministically.
3. **Execution:** every replica executes the same transactions in the same order, so they reach identical states without coordination.
4. Transactions must declare their read and write sets in advance (dependent transactions use a reconnaissance read first).
5. A failure on one node doesn't abort a transaction: replicas replay deterministically.

**Cost:** Epoch batching adds latency. High throughput under contention.

**Agent use:**
- **Role:** Verifier.
- **How:** Understanding deterministic databases, and the deterministic-replay idea that also underlies event sourcing (G82) and the glue engine's durable execution (G37).
- **Rules:** None specific.
- **Guardrails:** None specific.

## B6. CRDTs and causal consistency

### 87. G-Counter and PN-Counter

**Definition:** Conflict-free counters that can be incremented (and decremented) on any replica independently, and always converge when replicas sync.

**How it works:**
1. **G-Counter (grow-only):** a vector with one count per replica. Each replica increments only its own entry. Value = the sum of all entries.
2. **Merge:** take the entry-wise maximum of two vectors. Merges are commutative, associative and idempotent, so replicas converge regardless of order or duplicate syncs.
3. **PN-Counter:** two G-Counters, one for increments (P) and one for decrements (N). Value = sum(P) − sum(N).

**Cost:** O(number of replicas) per counter.

**Agent use:**
- **Role:** Coordinator.
- **How:** Counters updated in many regions or devices without coordination: view counts, likes, approximate usage meters.
- **Rules:** Use for counts where eventual convergence is acceptable.
- **Guardrails:** Not suitable for enforcing limits ("never below zero"), since replicas can't prevent concurrent decrements. Use coordination for limits.

### 88. LWW-Register and MV-Register

**Definition:** CRDT registers that hold a single value: last-writer-wins by timestamp, or keeping all concurrent values (multi-value) for later resolution.

**How it works:**
1. **LWW-Register:** each write carries a timestamp (HLC, #83) and a replica ID for tie-breaking. Merge keeps the value with the highest (timestamp, replica ID).
2. **MV-Register:** each value carries a version vector (G80). Merge keeps every value not dominated by another, so concurrent writes are all kept as siblings.
3. Readers (or the application) resolve siblings: pick one, merge them semantically, or ask a user.

**Cost:** LWW: O(1). MV: grows with concurrent writes.

**Agent use:**
- **Role:** Coordinator.
- **How:** LWW for fields where losing a concurrent update is acceptable (profile settings, status), MV where concurrent edits must not be lost silently (shopping carts, documents).
- **Rules:** LWW needs well-synchronized clocks (#100). Skewed clocks make "last" wrong.
- **Guardrails:** LWW silently discards concurrent writes. Never use it for data where both writes matter.

### 89. OR-Set (observed-remove set)

**Definition:** A CRDT set where adds and removes can happen concurrently on any replica, and an add concurrent with a remove wins.

**How it works:**
1. Each add creates a unique tag (replica ID + counter) for the element.
2. The set holds (element, tag) pairs.
3. A remove deletes only the tags the removing replica has observed for that element.
4. A concurrent add (with a new, unobserved tag) survives the remove: "add wins".
5. **Merge:** the union of adds, minus the removed tags. Optimized versions use version vectors and dots to avoid keeping removed tags (tombstones) forever.

**Cost:** Metadata grows with tags. Optimized versions bound it.

**Agent use:**
- **Role:** Coordinator.
- **How:** Collaborative or multi-region sets: tags, memberships, feature flags per user, offline-first collections.
- **Rules:** Use the optimized (dot-based) variant to bound metadata.
- **Guardrails:** "Add wins" semantics may not match business rules for some cases (revoked permissions). Check before using it for access control.

### 90. Sequence CRDTs (RGA, YATA)

**Definition:** CRDTs for ordered lists and text, allowing concurrent inserts and deletes at any position, with every replica converging to the same order.

**How it works:**
1. Each inserted element gets a unique ID (replica ID + counter) and a reference to the element it was inserted after.
2. **RGA (replicated growable array):** concurrent inserts after the same element are ordered by their IDs (newer first), deterministically on every replica.
3. Deletes mark elements as tombstones (hidden but kept, so later inserts that reference them still resolve).
4. **YATA (used in Yjs):** each insert references both its left and right neighbors at the time of insertion, with rules that preserve user intent better in interleaving cases.
5. Garbage collection of tombstones when all replicas have seen the deletes.

**Cost:** Metadata per element. Efficient implementations compress runs of characters.

**Agent use:**
- **Role:** Coordinator.
- **How:** Real-time collaborative editing (documents, code, shared notes, including agents editing alongside humans).
- **Rules:** Use mature libraries (Yjs, Automerge).
- **Guardrails:** Concurrent edits converge, but may not make sense semantically. Show conflicts or merges to people for important documents.

### 91. Delta-state CRDTs

**Definition:** CRDTs that sync only the recent changes (deltas) instead of the full state, which combines state-based robustness with small messages.

**How it works:**
1. Each update produces a small delta: a state fragment representing just that change (for example the one counter entry that changed).
2. Deltas are merged into the local state with the normal CRDT merge.
3. Replicas send accumulated deltas to peers, instead of their full state.
4. Deltas can be merged with each other before sending (delta groups).
5. **Anti-entropy fallback:** if deltas are lost, a full state sync repairs any divergence.

**Cost:** Messages proportional to the changes.

**Agent use:**
- **Role:** Coordinator.
- **How:** Efficient multi-region or edge replication of CRDT state over limited bandwidth.
- **Rules:** Keep periodic full-state anti-entropy for recovery (#93).
- **Guardrails:** None specific.

### 92. Causal broadcast and causal consistency

**Definition:** Delivering messages so that every message is delivered only after everything that causally preceded it, at every replica.

**How it works:**
1. Each message carries the sender's vector clock (G80).
2. A receiver delivers a message from sender j only when: the message is the next one from j (its entry for j is one more than the receiver's), and the receiver has already delivered everything the message depends on from others (all other entries are ≤ the receiver's).
3. Otherwise, buffer the message until its dependencies arrive.
4. **Causal consistency** for storage: reads never see an effect without its cause (a reply without its original question).

**Cost:** Vector-clock metadata per message. Buffering.

**Agent use:**
- **Role:** Coordinator.
- **How:** Replication for messaging, comments and collaborative state, where cause-before-effect matters but full global ordering is too expensive.
- **Rules:** Use dependency tracking with compact metadata for large systems.
- **Guardrails:** Vector clocks grow with participants. Use per-datacenter clocks or dependency pruning.

## B7. Replication repair, rate limiting and system utilities

### 93. Dynamo-style anti-entropy (hinted handoff, read repair, sloppy quorums, Merkle sync)

**Definition:** Techniques that keep eventually consistent replicas available during failures and repair their divergence afterward.

**How it works:**
1. **Sloppy quorum:** if a key's preferred replicas are unavailable, write to the next healthy nodes on the ring instead.
2. **Hinted handoff:** those substitute nodes store the write with a "hint" naming the intended replica, and deliver it when that replica recovers.
3. **Read repair:** on a read, compare the versions returned by several replicas, return the newest, and write it back to the stale replicas.
4. **Anti-entropy with Merkle trees:** replicas periodically compare Merkle trees of their key ranges (V#127), and sync only the differing ranges.
5. **Version vectors** (G80) detect concurrent writes, which are resolved by CRDTs (#87–91), last-writer-wins (#88), or the application.

**Cost:** Background repair traffic.

**Agent use:**
- **Role:** Coordinator.
- **How:** Understanding and operating highly available stores (Cassandra, Riak-style systems), including why deleted data can reappear.
- **Rules:** Run full anti-entropy repairs on a schedule shorter than the tombstone retention period.
- **Guardrails:** Without timely repair, deletes can be "resurrected" by stale replicas after tombstones expire (TX3).

### 94. GCRA and sliding-window rate limiting

**Definition:** Precise rate limiting algorithms: the generic cell rate algorithm (equivalent to a leaky bucket, with one stored timestamp) and sliding-window counters.

**How it works:**
1. **GCRA:** store one value per key, the theoretical arrival time (TAT). Each request: if now < TAT − burst tolerance, reject. Otherwise TAT = max(TAT, now) + emission interval (1 / rate). Allows bursts up to the tolerance, smoothly.
2. **Fixed window counter:** count requests per clock window. Simple, but allows double bursts at window boundaries.
3. **Sliding window log:** store each request's timestamp, and count those within the last window. Exact, but memory grows with the rate.
4. **Sliding window counter:** estimate = current window count + previous window count × (fraction of the previous window still inside the sliding window). Nearly exact with two counters.

**Cost:** GCRA: one timestamp per key. Sliding counter: two counters per key.

**Agent use:**
- **Role:** Coordinator.
- **How:** Per-user, per-tenant and per-agent API rate limits with smooth behavior and minimal storage (GCRA fits well in Redis-like stores).
- **Rules:** Return the retry-after time to clients.
- **Guardrails:** None specific.

### 95. Distributed rate limiting (global quotas with local leases)

**Definition:** Enforcing a global rate or quota across many servers without a central check on every request.

**How it works:**
1. A central quota service holds the global budget per key (tenant, API key).
2. Each server requests a lease: a share of the budget for a short period (for example 100 requests for the next second), sized by its recent demand.
3. Servers enforce their local shares independently, with no network call per request.
4. Unused shares are returned or expire. Servers with more demand get bigger shares next time.
5. **Fallback** when the quota service is unavailable: a conservative local limit (fail-safe), or the last known share.

**Cost:** One quota call per lease period per server.

**Agent use:**
- **Role:** Coordinator.
- **How:** Global limits on expensive resources (LLM tokens, external APIs, per-tenant usage), enforced across a whole fleet of agent workers.
- **Rules:** Choose the lease duration by acceptable overshoot (longer leases mean less accuracy).
- **Guardrails:** Define fail-open versus fail-closed behavior explicitly per limit. Billing and security limits fail closed.

### 96. Deadline propagation

**Definition:** Passing an absolute deadline along with a request through every service it calls, so all work stops when the original caller no longer needs the answer.

**How it works:**
1. The original client sets a deadline (for example now + 2 seconds).
2. Every downstream call carries the remaining time (in request metadata), minus a small margin for network and processing.
3. Each service checks the remaining time before starting work, and gives up (cancels) when it's exhausted.
4. Retries and hedged requests stay within the remaining deadline.
5. Cancellation also propagates: when a caller gives up, it cancels downstream calls.

**Cost:** Negligible.

**Agent use:**
- **Role:** Coordinator.
- **How:** Prevents wasted work and cascading overload in multi-service and multi-step agent call chains (G34 budgets made concrete).
- **Rules:** Every outbound call must pass the remaining deadline. No call without a timeout.
- **Guardrails:** Deadlines must not be extended by downstream services.

### 97. Bulkheads (resource isolation)

**Definition:** Partitioning resources (thread pools, connection pools, queues, instances) per dependency, tenant or priority, so a failure or overload in one part can't consume everything.

**How it works:**
1. Allocate separate, bounded pools: for example one connection pool per downstream service, or separate worker pools per tenant tier.
2. When one pool is exhausted (its dependency is slow), only calls using that pool fail or queue. Others continue normally.
3. Size the pools by expected concurrency (Little's law, graph #186) with headroom.
4. Combine with timeouts (#96), circuit breakers (G36) and load shedding (#73).

**Cost:** Some idle capacity in reserved pools.

**Agent use:**
- **Role:** Coordinator.
- **How:** Isolating noisy tenants, slow dependencies and batch workloads (such as bulk migrations) from interactive traffic.
- **Rules:** Separate interactive and batch agent workloads into different bulkheads.
- **Guardrails:** None specific.

### 98. Distributed unique ID generation (Snowflake, ULID, UUIDv7)

**Definition:** Generating unique, roughly time-ordered identifiers across many machines without coordination.

**How it works:**
1. **Snowflake-style:** a 64-bit ID = timestamp in milliseconds + worker ID + per-millisecond sequence number. Unique if worker IDs are unique and clocks don't go backward.
2. **ULID:** a 128-bit ID = 48-bit timestamp + 80 random bits, encoded in a sortable text form.
3. **UUIDv7 (IETF RFC 9562):** the standardized time-ordered UUID: Unix timestamp in milliseconds plus random bits, sortable and compatible with UUID columns.
4. Time ordering keeps database index inserts mostly sequential (better B-tree locality than random UUIDv4).
5. **Clock going backward:** wait, or refuse IDs until the clock catches up.

**Cost:** Negligible.

**Agent use:**
- **Role:** Coordinator.
- **How:** IDs for events, records and traces that sort by creation time and don't collide across workers.
- **Rules:** Prefer UUIDv7 as the standard format.
- **Guardrails:** Time-ordered IDs reveal creation times. Don't expose them where that leaks sensitive information.

### 99. Sharded counters

**Definition:** Splitting a heavily updated counter into many sub-counters, so concurrent increments don't contend on one record.

**How it works:**
1. Create N shards for the counter.
2. Each increment picks a shard at random (or by worker), and increments it.
3. Read = the sum of all shards (cache it, or maintain it asynchronously, for frequent reads).
4. Increase N when contention appears.

**Cost:** Reads cost N lookups (or a cached total).

**Agent use:**
- **Role:** Coordinator.
- **How:** High-rate counters in transactional stores: likes, usage meters, quota consumption.
- **Rules:** Size N from the peak write rate per record that the store can handle.
- **Guardrails:** Totals are only eventually consistent if cached. Don't use cached totals for hard limits.

### 100. Clock synchronization (NTP, PTP)

**Definition:** Keeping machines' clocks close to true time and to each other: NTP over networks, PTP for much higher precision.

**How it works:**
1. **NTP (IETF RFC 5905):** a client exchanges timestamped packets with servers. From four timestamps (client send, server receive, server send, client receive), it estimates the offset ((t2 − t1) + (t3 − t4)) / 2 and the round-trip delay.
2. Filtering and selection algorithms reject bad samples and bad servers. A control loop slews the clock gradually (avoiding jumps).
3. Typical accuracy: milliseconds over the internet, much better within a datacenter.
4. **PTP (IEEE 1588):** hardware timestamping in network cards and switches, which gives sub-microsecond accuracy within a network.
5. Monitor offsets, and alert when they exceed the bound that applications assume.

**Cost:** Negligible network overhead.

**Agent use:**
- **Role:** Coordinator.
- **How:** Correct timestamps underpin event time (#1), lease safety (#80), last-writer-wins (#88), ID ordering (#98) and log correlation.
- **Rules:** Treat clock offset as a monitored SLO, with alerting.
- **Guardrails:** Applications relying on clock bounds (lease reads, LWW) must fail safe when clock monitoring reports drift beyond the bound.

---

Part 3 (#101–150) covers classical machine learning: linear and generalized linear models (OLS, ridge/lasso/elastic net, logistic regression, GLMs, GAMs), decision trees, random forests, extra trees, gradient boosting (Friedman's method, histogram-based LightGBM, XGBoost, CatBoost), monotonic and interaction constraints, feature importance, SVMs, kernel methods and random features, k-NN, naive Bayes, DBSCAN, HDBSCAN, Gaussian mixtures, mean shift, k-medoids, the EM algorithm, HMM training, LDA topic models, Gaussian processes, ALS matrix factorization, factorization machines, isolation forest, one-class SVM, robust covariance, seasonal anomaly tests, ARIMA, exponential smoothing, decomposable forecasting, intermittent demand, hierarchical reconciliation, time-series cross-validation, model selection, encoding, imputation, feature selection, SMOTE, stacking, bagging, AdaBoost, partial dependence, online learning (FTRL), and concept drift detection.