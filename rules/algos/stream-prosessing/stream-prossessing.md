This is a new reference covering every Tier 1 area: **200 algorithms**, with no repeats from the earlier references (where something was touched before, only the parts not yet covered are added, with a cross-reference). Same format as before (definition, how it works, cost, agent use), no code, in 4 parts of 50.

**Map:**
- **Part 1 (#1–50): Stream processing.** Time semantics and watermarks, windowing, sliding-window aggregation, joins, complex event processing, state and fault tolerance, exactly-once, partitioning and consumption.
- **Part 2 (#51–100): Caching, load balancing and distributed coordination.** Eviction and admission, cache consistency, load balancing and overload control, consensus and replication, clocks and distributed transactions, CRDTs, rate limiting and IDs.
- **Part 3 (#101–150): Classical machine learning.** Linear models, trees and boosting, kernel and instance methods, clustering and mixtures, probabilistic models, anomaly detection, time series, model selection, online learning and drift.
- **Part 4 (#151–200): Experimentation and statistics.** Testing foundations, randomization and validity checks, variance reduction, sequential and Bayesian testing, multiple testing, complex designs, heterogeneous effects and uplift, observational causal inference, and robust statistics.

Standard definitions here are [Certain]. Where details differ between systems (Flink, Kafka Streams, Spark, specific caches), entries say so.

---

# Tier 1 contract (referenced in every entry)

| Role | Job | Can write? |
|---|---|---|
| **Pipeline Builder** | Designs stream topologies: sources, operators, state, sinks | Configs only |
| **Processor** | Runs and operates streaming jobs | Job state, sinks, through approved deployments |
| **Coordinator** | Operates caches, load balancers, consensus and storage infrastructure | Infra changes, through approved plans |
| **Modeler** | Builds and evaluates classical ML models | Models, in staging |
| **Experimenter** | Designs and analyzes experiments and causal studies | Analysis results (decisions belong to owners) |
| **Verifier** | Checks correctness, delivery guarantees and statistical validity | No (can block) |

**Rules:**
- **T1. Time semantics declared:** every stream computation states event time or processing time, its watermark strategy and its allowed lateness.
- **T2. Delivery semantics declared end to end:** at-most-once, at-least-once or exactly-once, from source to sink, and verified by test.
- **T3. Bounded state:** every stateful operator has a retention rule (window, TTL, compaction) and a size estimate.
- **T4. Partitioning documented:** keys, partition counts and co-partitioning requirements for joins are explicit.
- **T5. Plan before data:** every model and experiment has a pre-declared metric, baseline and analysis plan.
- **T6. Uncertainty attached:** results carry confidence intervals or error bounds.
- **T7. Reproducible:** seeds, versions, offsets and data snapshots are recorded.
- **T8. Outputs are proposals:** decisions affecting people, money or production systems go through owners or approved policies.

**Guardrails:**
- **TX1. Resource caps:** state size, memory, CPU, compute cost and query limits.
- **TX2. Replay safety:** any reprocessing must not repeat external side effects. Sinks and actions are idempotent or transactional.
- **TX3. Data governance:** personal data in streams, caches and models follows retention, minimization and access rules.
- **TX4. Change approval:** consensus membership changes, partition and rebalance changes, and cache-cluster topology changes need approval and staged rollout.
- **TX5. No p-hacking:** no changing metrics, segments or stopping rules after seeing the data, unless declared as exploratory.

---

# PART 1: STREAM PROCESSING

## A1. Time, ordering and lateness

### 1. Event time, ingestion time and processing time semantics

**Definition:** The three clocks a stream system can use to assign a time to each record, which determine whether results reflect when things happened or when they were processed.

**How it works:**
1. **Event time:** the timestamp when the event occurred, embedded in the record by the producer.
2. **Ingestion time:** when the record entered the streaming system (broker or source operator).
3. **Processing time:** the wall clock of the machine processing the record at that moment.
4. Event-time processing gives the same results regardless of delays, replays or reprocessing. Processing-time results change with load and outages.
5. Event time needs watermarks (#2) to know when a time period is complete, because records arrive out of order.

**Cost:** Event time adds buffering state and latency (waiting for late data). Processing time is cheapest but not reproducible.

**Agent use:**
- **Role:** Pipeline Builder.
- **How:** Uses event time for anything analytical, billing-related or replayed (correct, repeatable results), and processing time only for operational signals where "now" matters (alerting on current lag).
- **Rules:** T1: declare the time semantics per operator, and validate producer timestamps (clock skew, defaults like 1970-01-01).
- **Guardrails:** Never mix event-time and processing-time results in one metric without labeling.

### 2. Watermark generation strategies

**Definition:** Rules that produce watermarks, assertions that "no more events with timestamps earlier than T are expected", which let event-time operators finalize results.

**How it works:**
1. **Bounded out-of-orderness:** watermark = maximum event time seen − a fixed delay (for example 5 seconds). Simple and common.
2. **Punctuated:** special marker records (or fields) in the stream carry explicit watermarks from the producer.
3. **Per-partition watermarks:** compute a watermark for each source partition separately, and use the minimum across partitions as the source's watermark (a partition that's behind holds everyone back, correctly).
4. **Idle sources:** a partition with no data would block the minimum forever. Mark it idle after a timeout, so it's excluded until data returns.
5. **Heuristic / percentile-based:** set the delay from observed lateness distributions (for example, the 99th percentile delay).

**Cost:** The delay trades completeness (fewer late events) against latency (results come later).

**Agent use:**
- **Role:** Pipeline Builder.
- **How:** Chooses the delay from measured event delay distributions, per source, rather than guessing.
- **Rules:** Monitor the fraction of late events dropped (#4). Rising late rates mean the delay is too small or producers are lagging.
- **Guardrails:** Idle-source timeouts that are too short cause early watermarks and silently drop data from slow partitions. Test with a stalled partition.

### 3. Watermark propagation and alignment

**Definition:** How watermarks flow through an operator graph, and how to keep fast sources from running far ahead of slow ones.

**How it works:**
1. An operator with several inputs (a union or join) sets its output watermark to the **minimum** of its input watermarks.
2. Operators forward the watermark after processing everything before it, and fire timers (window ends) whose time is ≤ the watermark.
3. **Watermark skew:** if one source is far ahead of another, operators buffer huge amounts of the fast source's data while waiting for the slow one.
4. **Watermark alignment:** pause reading from sources (or splits) whose watermark is more than a set amount ahead of the slowest, until the others catch up.
5. Monitor the watermark lag (current time − watermark) per operator.

**Cost:** Alignment bounds buffered state at the cost of throttling fast sources.

**Agent use:**
- **Role:** Processor.
- **How:** Enables alignment when joining sources with different lag (for example, a backfilled source with a live one), to keep state bounded (T3).
- **Rules:** Alert on watermark lag per operator. A frozen watermark means stalled results.
- **Guardrails:** None specific.

### 4. Allowed lateness and late-data side outputs

**Definition:** Policies for events that arrive after the watermark has passed their window: update results, route them elsewhere, or drop them.

**How it works:**
1. **Allowed lateness L:** keep window state for L after the watermark passes the window's end. Late events within L update the window and trigger a corrected result.
2. Events arriving after (window end + L) are "too late".
3. **Side output:** send too-late events to a separate stream (for audit, reconciliation or batch correction) instead of silently dropping them.
4. Downstream consumers must handle updated results: an upsert by window key, or a retraction followed by a new value.

**Cost:** Allowed lateness keeps window state longer (memory, T3).

**Agent use:**
- **Role:** Pipeline Builder.
- **How:** Sets lateness from the business need: billing and compliance need completeness (long lateness plus side outputs and reconciliation); dashboards prefer timeliness.
- **Rules:** Always capture too-late events in a side output with counts. Silent drops are never acceptable for financial data.
- **Guardrails:** Downstream sinks must handle result updates idempotently (TX2).

### 5. Out-of-order buffering (K-slack reordering)

**Definition:** Restoring time order within a bounded delay, for operators that need strictly ordered input.

**How it works:**
1. Keep incoming events in a priority queue (min-heap) keyed by event time.
2. Track the maximum event time seen, t_max.
3. Release events with timestamps ≤ t_max − K, in order (K is the slack, the maximum expected disorder).
4. **Adaptive K:** increase K when an event arrives later than the current K allows; shrink it slowly when disorder decreases.
5. Events arriving later than the slack are handled like late events (#4).

**Cost:** O(log n) per event. Memory for the buffered window of K time units.

**Agent use:**
- **Role:** Processor.
- **How:** Needed before sequence-sensitive logic: CEP (#27), sessionization (#11) or state machines that require order.
- **Rules:** Size K from the measured delay distribution, and report how many events exceeded it.
- **Guardrails:** Buffer memory grows with event rate × K. Cap it (TX1).

### 6. Triggers and accumulation modes

**Definition:** Rules for when a window emits results (possibly several times) and how successive results relate to each other.

**How it works:**
1. **Event-time trigger:** fire when the watermark passes the window end (the "on-time" result).
2. **Early firings:** fire periodically in processing time (for example every 10 seconds) before the window closes, giving speculative partial results.
3. **Late firings:** fire again for each late event within allowed lateness (#4).
4. **Count triggers:** fire every N elements.
5. **Accumulation modes:**
   - **Discarding:** each firing contains only new data since the last firing.
   - **Accumulating:** each firing contains the full result so far.
   - **Accumulating and retracting:** each firing retracts the previous result and emits the new one, so downstream sums stay correct.

**Cost:** Each firing costs an emission and downstream processing.

**Agent use:**
- **Role:** Pipeline Builder.
- **How:** Early firings give low-latency dashboards; on-time and late firings give correctness. Picks the accumulation mode to match how downstream consumers combine results.
- **Rules:** Document the trigger and accumulation mode for each output topic (T1).
- **Guardrails:** Accumulating results summed downstream (without retractions) double-count. Verify downstream logic.

### 7. Bounded-state stream deduplication

**Definition:** Removing duplicate events (from retries, at-least-once delivery or replays) using limited memory.

**How it works:**
1. Choose a deduplication key: an event ID, or a hash of the business fields.
2. **Keyed state with TTL:** remember seen keys for a time horizon H (longer than the maximum duplicate delay). Drop events whose key is already present.
3. **Time-bucketed sets:** keep one set (or Bloom filter) per time bucket. Expire whole buckets as the watermark advances, which is cheaper than per-key TTLs.
4. **Bloom filter variant:** much less memory, with a small chance of wrongly dropping a unique event (false positive).
5. Order-sensitive variant: keep the first occurrence or the latest version (by sequence number, #8).

**Cost:** Memory proportional to keys seen within H.

**Agent use:**
- **Role:** Processor.
- **How:** Makes at-least-once pipelines effectively exactly-once for downstream counting and billing.
- **Rules:** Choose H from measured duplicate delays (retries, replays). Duplicates arriving after H aren't caught.
- **Guardrails:** Don't use Bloom-based deduplication where dropping a unique event is unacceptable (payments).

### 8. Sequence numbers and gap detection

**Definition:** Using per-producer or per-key sequence numbers to detect missing, duplicated or reordered events.

**How it works:**
1. Each producer (or each entity key) attaches a monotonically increasing sequence number to its events.
2. The consumer tracks the last sequence number seen per producer or key.
3. **Duplicate:** sequence ≤ last seen. **In order:** sequence = last + 1. **Gap:** sequence > last + 1.
4. On a gap: buffer briefly (waiting for the missing event), then alert, request a resend, or mark the data incomplete.
5. Producer restarts need epochs (producer ID + epoch + sequence), so a restarted producer isn't mistaken for a duplicate source.

**Cost:** One counter per producer or key.

**Agent use:**
- **Role:** Verifier.
- **How:** Proves completeness of critical streams (financial events, audit logs), and detects lost data immediately instead of at month-end reconciliation.
- **Rules:** Alert on any unresolved gap after the buffering timeout.
- **Guardrails:** None specific.

## A2. Windowing and window aggregation

### 9. Tumbling windows

**Definition:** Fixed-size, non-overlapping, contiguous time windows. Each event belongs to exactly one window.

**How it works:**
1. Window size S (for example 1 minute). Optionally an offset (for example to align daily windows with a time zone).
2. Window start = floor((timestamp − offset) / S) × S + offset.
3. Aggregate events into their window's state (count, sum, sketch).
4. When the watermark passes the window end, emit the result and clear the state (after allowed lateness, #4).

**Cost:** O(1) per event. State: one aggregate per key per open window.

**Agent use:**
- **Role:** Pipeline Builder.
- **How:** Standard for periodic metrics (per-minute counts, hourly totals, daily billing).
- **Rules:** Align daily windows to the business time zone explicitly (T1).
- **Guardrails:** Daylight-saving transitions make "daily" windows 23 or 25 hours long in local time. Decide and document how they're handled.

### 10. Hopping (sliding) windows

**Definition:** Fixed-size windows that start at regular intervals smaller than their size, so they overlap and each event belongs to several windows.

**How it works:**
1. Size S, slide (hop) H < S. For example, 10-minute windows every 1 minute.
2. Each event belongs to S/H windows.
3. **Naive implementation:** update every window an event belongs to, so cost grows with S/H.
4. **Efficient implementations:** pane-based slicing (#14) or sliding-window aggregation structures (#15–17).
5. Emit each window when the watermark passes its end.

**Cost:** Naive: O(S/H) per event. Efficient methods are much lower.

**Agent use:**
- **Role:** Pipeline Builder.
- **How:** Smoothed rolling metrics: "requests in the last 5 minutes, updated every 10 seconds", moving averages for alerting.
- **Rules:** Use pane-based or incremental methods when S/H is large (more than about 10).
- **Guardrails:** Large S/H with naive updates multiplies state and CPU (TX1).

### 11. Session windows (gap-based)

**Definition:** Variable-length windows that group a key's events separated by less than a gap, ending after a period of inactivity.

**How it works:**
1. Each event initially forms its own window [t, t + gap).
2. **Merge** overlapping windows for the same key: a new event extends or joins sessions within the gap.
3. A late event can bridge two existing sessions, merging them into one (#13).
4. A session closes when the watermark passes (last event time + gap).
5. Optional maximum session length (to split never-ending sessions).

**Cost:** State per active session. Merging cost is small.

**Agent use:**
- **Role:** Pipeline Builder.
- **How:** User sessions, device activity bursts, conversation threads, incident clusters (alerts close together).
- **Rules:** Choose the gap from the distribution of inactivity periods (look for the natural break).
- **Guardrails:** Bots and stuck devices create endless sessions. Use a maximum length.

### 12. Global and count windows with custom triggers

**Definition:** Windows not tied to fixed time boundaries: one window per key for all time (global), or windows of N events (count windows), emitting according to custom triggers.

**How it works:**
1. **Global window:** all events for a key go into a single window that never ends naturally.
2. A custom trigger decides when to emit: every N events, on a special event, on processing-time intervals, or when a condition holds.
3. An evictor (or explicit state logic) removes old elements, to keep state bounded.
4. **Count windows:** tumbling (every N events) or sliding (last N events, every M).

**Cost:** Depends on the trigger and eviction logic.

**Agent use:**
- **Role:** Pipeline Builder.
- **How:** "Last 100 transactions per account", "emit when the batch reaches N items", or per-key running state machines.
- **Rules:** Always pair global windows with eviction or TTL (T3).
- **Guardrails:** Count windows depend on arrival order. They aren't reproducible on replays with different ordering. Document it.

### 13. Window assignment and merging

**Definition:** The algorithm that assigns each event to its windows, and merges windows when needed (for sessions), while keeping their state consistent.

**How it works:**
1. **Assign:** for each event, compute its window set (one for tumbling, S/H for hopping, a provisional window for sessions).
2. **Merging window sets:** for merging windows (sessions), keep a per-key set of current windows. When a new window overlaps existing ones, compute their union.
3. **State merge:** combine the aggregate states of the merged windows (requires aggregates that can be merged: sums, counts, mergeable sketches).
4. Move timers: cancel the old windows' end timers, and register the merged window's end timer.
5. Keep a mapping from merged windows to their state locations, to avoid copying state.

**Cost:** Small per event. Merges cost proportional to the state merged.

**Agent use:**
- **Role:** Pipeline Builder.
- **How:** Explains why session aggregations need mergeable aggregates (#18), and how late events can change earlier session results.
- **Rules:** Use only mergeable aggregate functions with session windows.
- **Guardrails:** None specific.

### 14. Pane-based window slicing (Pairs, Cutty)

**Definition:** Computing overlapping windows by splitting the timeline into non-overlapping slices, aggregating each slice once, and combining slices into windows.

**How it works:**
1. Split time into slices at every window boundary (for hopping windows: slice size = gcd(S, H), or the pairs technique with two alternating slice sizes).
2. Each event updates exactly one slice aggregate.
3. When a window closes, combine the aggregates of its slices.
4. **Cutty / general slicing:** handles different window types, several window definitions at once, and session-like windows by cutting slices at every boundary of every window definition.
5. Slices are shared between overlapping windows and across different queries over the same stream.

**Cost:** O(1) per event, plus combining (S/slice size) partial aggregates per window.

**Agent use:**
- **Role:** Processor.
- **How:** Efficient computation of many overlapping windows, or many dashboards with different window sizes on the same stream.
- **Rules:** Requires aggregates that can be combined (associative).
- **Guardrails:** None specific.

### 15. Two-stacks sliding window aggregation (non-invertible aggregates)

**Definition:** An amortized O(1) method to maintain aggregates like max, min or any associative operation over a sliding window, without needing to "subtract" elements.

**How it works:**
1. Keep a "front" stack and a "back" stack. Each entry stores a value plus the aggregate of everything below it in its stack.
2. **Insert:** push onto the back stack, updating its running aggregate.
3. **Evict (oldest):** pop from the front stack. If it's empty, move every element from the back stack to the front stack, recomputing running aggregates in reverse order (this flip makes the front stack's top the oldest element).
4. **Query:** combine the aggregates at the tops of the two stacks.
5. Every element is moved at most once, so operations are amortized O(1).

**Cost:** Amortized O(1). Occasional O(n) flips.

**Agent use:**
- **Role:** Processor.
- **How:** Rolling max and min latency, rolling "worst" values for alerting, any associative but non-invertible metric over count-based or time-based sliding windows.
- **Rules:** For strict per-event latency guarantees, use the de-amortized version (#16).
- **Guardrails:** None specific.

### 16. FlatFAT and DABA (worst-case efficient sliding aggregation)

**Definition:** Sliding-window aggregation structures with worst-case (not just amortized) bounds, suited to low-latency systems.

**How it works:**
1. **FlatFAT:** a complete binary tree over a circular buffer of window slots, stored as a flat array. Each internal node holds the aggregate of its subtree. An update touches O(log n) nodes up to the root. The query reads the root (with handling for wrap-around).
2. **DABA (de-amortized banker's aggregator):** a de-amortized version of two-stacks (#15) that performs a constant amount of the "flip" work on every operation, giving worst-case O(1) per insert and evict.
3. Both work with any associative aggregation operation.

**Cost:** FlatFAT O(log n) per update. DABA worst-case O(1).

**Agent use:**
- **Role:** Processor.
- **How:** Low-latency streaming with strict per-event time budgets (trading, real-time control).
- **Rules:** Choose by the window size and latency requirements.
- **Guardrails:** None specific.

### 17. Subtract-on-evict (invertible incremental aggregation)

**Definition:** Maintaining aggregates over a sliding window by adding new elements and subtracting expired ones, for aggregates that have an inverse.

**How it works:**
1. Invertible aggregates: sum, count, sum of squares (so mean and variance), product (with care for zeros).
2. On insert: aggregate += value.
3. On evict: aggregate −= value (this requires keeping the window's elements, or their per-slice partial sums).
4. Query: O(1).
5. For floating-point sums, periodically recompute from scratch (or use compensated, Kahan summation) to remove accumulated rounding error.

**Cost:** O(1) per event.

**Agent use:**
- **Role:** Processor.
- **How:** The cheapest way to maintain rolling sums, counts and means.
- **Rules:** Use for invertible aggregates only. Max and min need #15 or #16.
- **Guardrails:** Floating-point drift over long runs. Re-baseline periodically.

### 18. Mergeable sketches for windowed approximate aggregates

**Definition:** Using sketches that can be combined (HyperLogLog, Count-Min, t-digest, KLL) as window and slice aggregates, so approximate distinct counts and quantiles can be computed over any window combination.

**How it works:**
1. Maintain one sketch per slice (#14) or per window per key.
2. Sketches merge: HyperLogLog by register-wise max, Count-Min by elementwise sum, t-digest by merging centroids.
3. Window result = merge of its slices' sketches.
4. Results carry the sketch's error bounds.
5. Sketches can also be emitted downstream and merged further (rolling up from per-minute to per-hour, or across partitions).

**Cost:** Fixed size per sketch, cheap merges.

**Agent use:**
- **Role:** Processor.
- **How:** Real-time distinct users, latency percentiles (p95, p99) and top items per window, at high cardinality, with bounded state (T3).
- **Rules:** Store sketches (not only final numbers), so they can be re-aggregated later (T6).
- **Guardrails:** Never average percentiles across windows or partitions. Merge the sketches.

## A3. Stream joins and enrichment

### 19. Windowed stream-stream join (symmetric hash join)

**Definition:** Joining two event streams on a key, for events that fall in the same time window.

**How it works:**
1. For each stream, keep a hash table of buffered events per (key, window).
2. When an event arrives on stream A: store it in A's table, and probe B's table for matching (key, window) entries. Emit a joined result for each match.
3. Symmetric for stream B.
4. When the watermark passes a window's end (+ lateness), drop both sides' buffered events for that window.
5. Outer joins: at window close, emit unmatched events with nulls for the other side.

**Cost:** State = events per window on both sides. O(matches) per event.

**Agent use:**
- **Role:** Pipeline Builder.
- **How:** Correlating related events: impressions with clicks, requests with responses, orders with payments.
- **Rules:** Both streams must be co-partitioned on the join key (#50, T4).
- **Guardrails:** State grows with window length × event rate. Estimate it before deploying (T3).

### 20. Interval join

**Definition:** Joining two streams where events match if their timestamps are within a relative time range of each other, such as a payment between 0 and 30 minutes after an order.

**How it works:**
1. Condition: B.time ∈ [A.time + lower, A.time + upper].
2. Buffer events from each side as long as they can still match: an A event is kept until the watermark passes A.time + upper.
3. On arrival, probe the other side's buffer for timestamps in the matching range (sorted per key for range lookups).
4. Emit matches. Clean up the expired events as watermarks advance.
5. More precise than a windowed join: no artificial window boundaries splitting related events.

**Cost:** State depends on the interval width and event rates.

**Agent use:**
- **Role:** Pipeline Builder.
- **How:** Time-bounded correlations: "fraud check event within 2 seconds of transaction", "login followed by password change within 10 minutes".
- **Rules:** Choose the interval from the real causal delay distribution.
- **Guardrails:** Wide intervals hold large state. Check TX1.

### 21. Stream-table join (changelog materialization)

**Definition:** Enriching each stream event with the current value from a table that is itself maintained from a changelog stream.

**How it works:**
1. The table is built by consuming a changelog (compacted topic or CDC stream): each record upserts or deletes a key in a local state store.
2. Each stream event looks up its key in the local table, and joins with the current value.
3. Table updates don't trigger outputs; only stream events do.
4. Both inputs must be co-partitioned (#50), unless the table is replicated to every instance (a global table).
5. Table state is restored from its changelog after failures (#42).

**Cost:** One local lookup per event. Table state size.

**Agent use:**
- **Role:** Pipeline Builder.
- **How:** Enrichment with reference data: user profiles, product catalogs, account status.
- **Rules:** For historical correctness on replays, use a temporal (as-of) join (#22) instead of the current table value.
- **Guardrails:** The join result depends on the order in which the table update and the stream event are processed. Document the expected behavior.

### 22. Temporal (as-of) join with versioned tables

**Definition:** Joining each event with the version of a table row that was valid at the event's time, not the current version.

**How it works:**
1. Keep a versioned table: for each key, a time-ordered list of (valid-from time, value).
2. For an event at time t with key k, find the latest version with valid-from ≤ t (binary search per key).
3. Emit the joined result.
4. Keep old versions only as long as events might still need them (until the watermark passes, plus lateness).
5. Equivalent to SQL `FOR SYSTEM_TIME AS OF` joins.

**Cost:** O(log versions) per lookup. Version history state.

**Agent use:**
- **Role:** Pipeline Builder.
- **How:** Correct historical enrichment: the exchange rate when the transaction happened, the price at order time, the user's plan at event time. Results stay the same on replay.
- **Rules:** Use for anything financial or audit-related.
- **Guardrails:** Version retention must cover replay horizons. Otherwise replays silently use the wrong versions.

### 23. Foreign-key table-table join

**Definition:** Joining two continuously updated tables on a foreign key (for example orders → customers) as a streaming computation that stays correct as either table changes.

**How it works:**
1. The left table's rows reference the right table by a foreign key, so the two tables are partitioned differently.
2. **Subscription:** each left row sends a subscription message (left key, foreign key, a hash of its value) to the partition owning the foreign key.
3. The right side stores subscriptions per foreign key. When a right row changes, it sends responses to every subscribed left key.
4. The left side joins the response with the current left row, using the value hash to ignore stale responses (from an older version of the left row).
5. Deletions on either side produce retractions.

**Cost:** Subscription state on the right side. Extra network messages.

**Agent use:**
- **Role:** Pipeline Builder.
- **How:** Materializing denormalized views that stay current (order with current customer details), without re-joining everything.
- **Rules:** Expect updates when either side changes (T1).
- **Guardrails:** A popular foreign key (one customer with many orders) creates fan-out storms on updates. Check skew (#25).

### 24. Lookup and async enrichment with caching

**Definition:** Enriching events by querying an external system (database, service), asynchronously with bounded concurrency and a local cache.

**How it works:**
1. For each event, issue an asynchronous request to the external system, without blocking the operator.
2. Keep up to N requests in flight. Results return out of order.
3. **Ordered mode:** emit results in the original order (buffering). **Unordered mode:** emit as soon as results arrive (lower latency, order lost).
4. A local cache with TTL (Part 2, #51–65) avoids repeated lookups for hot keys.
5. Timeouts and retries per request. On failure: a default value, a dead-letter queue (#49) or failing the job, by policy.

**Cost:** Bounded by the external service's capacity.

**Agent use:**
- **Role:** Pipeline Builder.
- **How:** Enrichment from systems that can't be streamed as changelogs.
- **Rules:** Prefer changelog-based tables (#21, #22) when the data is available as a stream: they're faster and reproducible.
- **Guardrails:** External lookups aren't reproducible on replay (values change). Rate-limit them to protect the external service (TX1).

### 25. Join skew handling (hot-key splitting, salting)

**Definition:** Dealing with keys that have far more events than others, which overload one partition in joins and aggregations.

**How it works:**
1. Detect hot keys: per-key event counts (or heavy-hitter sketches) per partition.
2. **Salting for aggregations:** append a random suffix (0…n−1) to hot keys, aggregate per salted key in parallel, then combine the partial results per original key.
3. **Joins:** split the hot key's events from the large side across n salted keys, and replicate the other side's matching rows to all n salted keys.
4. **Two-phase aggregation:** local pre-aggregation per instance before the shuffle (combiners).
5. Apply salting only to detected hot keys, to avoid overhead elsewhere.

**Cost:** Extra stage and replication for hot keys.

**Agent use:**
- **Role:** Processor.
- **How:** Fixes the most common streaming performance problem: one partition lagging because of a few huge keys.
- **Rules:** Monitor per-partition lag and throughput, so skew is visible.
- **Guardrails:** Salting changes ordering within a key. Don't apply it to order-sensitive logic.

### 26. Join state cleanup (TTL and watermark-driven eviction)

**Definition:** Removing join state that can no longer produce matches, so state doesn't grow forever.

**How it works:**
1. **Watermark-driven:** for windowed and interval joins, drop entries once the watermark proves no future match is possible.
2. **TTL:** for unbounded joins (regular table joins), expire entries not accessed or updated for a configured time.
3. Expiry is often lazy (checked on access) plus background cleanup during compaction (RocksDB compaction filters).
4. Outer joins: emitting unmatched results requires timers at expiry.

**Cost:** Small. Background cleanup cost.

**Agent use:**
- **Role:** Processor.
- **How:** Keeps unbounded SQL-style streaming joins from accumulating unlimited state (T3).
- **Rules:** Choose TTLs from business semantics (how long a match can arrive), and document them.
- **Guardrails:** TTL expiry silently changes results: an event arriving after the TTL gets no match. Monitor expired-entry counts.

## A4. Complex event processing and pattern analytics

### 27. Complex event processing with NFAs

**Definition:** Detecting patterns of events (sequences, with conditions and time limits) by running a nondeterministic finite automaton over the stream.

**How it works:**
1. A pattern (for example "A, then one or more B where B.amount > 100, then C, within 10 minutes") compiles into an NFA: states for each pattern element, with transitions guarded by conditions.
2. For each incoming event (per key), try to advance every active partial match ("run"), and start new runs where the first element matches.
3. A run that reaches the final state emits a complete match.
4. Runs whose time limit expires are removed (or emitted as timeouts, for "A not followed by B" patterns).
5. **Shared buffer:** partial matches share their common event prefixes in a versioned structure, so memory isn't duplicated for every run.

**Cost:** Proportional to active runs, which can explode with permissive patterns.

**Agent use:**
- **Role:** Pipeline Builder.
- **How:** Real-time detection of multi-step behaviors: fraud sequences, attack chains, process violations, SLA breaches.
- **Rules:** Always add time limits (WITHIN) and order input first (#5).
- **Guardrails:** Patterns with loops and lax contiguity create combinatorial explosions of runs. Cap the runs per key (TX1).

### 28. Contiguity modes and after-match skip strategies

**Definition:** Rules that control which events may appear between pattern elements, and how matching resumes after a match is found.

**How it works:**
1. **Strict contiguity:** matching events must be directly consecutive.
2. **Relaxed contiguity:** non-matching events in between are ignored, and only the first matching event is taken.
3. **Non-deterministic relaxed:** every combination of matching events is considered (all possible matches, potentially very many).
4. **Skip strategies after a match:** no skip (every overlapping match), skip to the next event, skip past the last event of the match (no overlapping matches), skip to the first or last occurrence of a named element.
5. These choices determine both correctness and the number of runs.

**Cost:** Non-deterministic relaxed contiguity can be exponential. Strict is cheapest.

**Agent use:**
- **Role:** Pipeline Builder.
- **How:** Choosing the semantics that match the business meaning (alert once per incident versus every combination).
- **Rules:** Default to relaxed contiguity with "skip past last event" unless all combinations are genuinely needed.
- **Guardrails:** Test patterns on recorded streams, and count matches before deploying alerts on them.

### 29. Row pattern recognition (SQL MATCH_RECOGNIZE)

**Definition:** The SQL standard syntax (ISO/IEC 9075, introduced in SQL:2016) for pattern matching over ordered rows, supported by several streaming SQL engines.

**How it works:**
1. `PARTITION BY` (key) and `ORDER BY` (time) define ordered sequences.
2. `PATTERN` uses regular-expression-like syntax over named variables: `(A B+ C)`.
3. `DEFINE` gives each variable's condition: `B AS B.price > PREV(B.price)`.
4. `MEASURES` computes output values per match (first or last values, counts, aggregates). `ONE ROW PER MATCH` or `ALL ROWS PER MATCH`.
5. `AFTER MATCH SKIP` options (#28). Engines compile this to an NFA (#27).

**Cost:** Like CEP.

**Agent use:**
- **Role:** Pipeline Builder.
- **How:** Expressing patterns declaratively in SQL, which is easier to review and maintain than procedural CEP code. Common patterns: V-shapes in metrics, price trends, step sequences.
- **Rules:** Use the standard syntax where the engine supports it, for portability.
- **Guardrails:** Same run-explosion caution as #27.

### 30. Funnel and path analysis over streams

**Definition:** Computing how many users (or entities) complete an ordered sequence of steps within a time limit, and where they drop off.

**How it works:**
1. Define the steps (for example visit → signup → verify → first action) and a maximum time for completing the funnel.
2. Per entity, keep the furthest step reached and its timestamp (a small state machine).
3. On each event, advance the entity's state if the event is the next step, within the time limit (strict order, or allowing other events in between).
4. Aggregate the counts per step reached, giving conversion rates and drop-off points.
5. **Path analysis:** count the most common sequences of events between steps (with heavy-hitter sketches for high cardinality).

**Cost:** One small state per active entity.

**Agent use:**
- **Role:** Pipeline Builder and Experimenter.
- **How:** Real-time conversion monitoring and metrics for experiments (Part 4).
- **Rules:** Use event time and ordering (#1, #5). Define what counts as completion precisely.
- **Guardrails:** Funnel metrics on personal behavior follow governance rules (TX3).

### 31. Autoscaling stream jobs (DS2)

**Definition:** Choosing the parallelism of each operator in a streaming job from measured processing rates, so the job keeps up with input without overprovisioning.

**How it works:**
1. Instrument each operator: records processed per second of actual useful work (excluding time spent waiting or blocked by backpressure). That's its "true processing rate" per instance.
2. Compute the "true output rate" that the operator would have if it weren't throttled.
3. Starting from the sources' target input rates, propagate the rates through the job graph: each operator's required rate = the sum of its inputs' true output rates.
4. Required parallelism = required rate / true processing rate per instance.
5. Rescale all operators at once (few steps instead of trial and error), then re-measure.

**Cost:** Light instrumentation. Rescaling costs a state redistribution (#41).

**Agent use:**
- **Role:** Processor.
- **How:** Right-sizing streaming jobs as traffic grows, without guessing or repeated oscillating adjustments.
- **Rules:** Add a headroom factor for peaks, and apply cooldown periods between rescalings.
- **Guardrails:** Rescaling stateful jobs takes a pause or checkpoint-restore cycle. Schedule it, and follow TX4 for production changes.

## A5. State and fault tolerance

### 32. Keyed state and key groups

**Definition:** Partitioning operator state by key, and grouping keys into a fixed number of key groups, so state can be redistributed when the parallelism changes.

**How it works:**
1. Each record's key determines which state it can read and write (the "current key").
2. Keys are hashed into K key groups (K = the maximum parallelism, fixed at job creation).
3. Each parallel instance owns a contiguous range of key groups.
4. **Rescaling:** reassign key-group ranges to the new number of instances. State moves in whole key groups, so no per-key re-hashing is needed.
5. K limits the maximum parallelism ever possible for the job.

**Cost:** None at runtime. Rescaling moves whole key-group ranges.

**Agent use:**
- **Role:** Pipeline Builder.
- **How:** Sets the maximum parallelism high enough for future growth at job creation, because it can't easily be changed later.
- **Rules:** Choose K as a multiple of expected parallelism levels, with headroom.
- **Guardrails:** Changing K later usually requires state migration or a new job. Plan it.

### 33. State backends and incremental checkpoints

**Definition:** Where operator state lives (in-memory heap or an embedded LSM store like RocksDB) and how checkpoints copy only what changed.

**How it works:**
1. **Heap backend:** state as objects in memory. Fast, but limited by memory, and checkpoints copy everything.
2. **Embedded LSM backend (RocksDB):** state on local disk, in sorted immutable files plus a memory buffer (the LSM tree structure). Supports state far larger than memory, with slower access (serialization on every read and write).
3. **Incremental checkpoints:** because LSM files are immutable, a checkpoint uploads only the files created since the last checkpoint, and references the unchanged ones.
4. **Changelog-based state (generalized incremental):** continuously log state changes to durable storage, so checkpoints are fast and small.
5. Tune compaction, block cache and memory budgets for the workload.

**Cost:** Heap: fast access, expensive full checkpoints. LSM: slower access, cheap incremental checkpoints.

**Agent use:**
- **Role:** Processor.
- **How:** Picks the backend by state size: heap for small state, LSM for large state (multi-GB per instance).
- **Rules:** Monitor checkpoint size and duration trends. Growth means state retention problems (T3).
- **Guardrails:** Shared incremental checkpoint files must not be deleted manually. Use the system's retention.

### 34. Chandy-Lamport distributed snapshots

**Definition:** An algorithm for capturing a consistent global snapshot of a distributed system (every process's state plus the messages in flight) without stopping it.

**How it works:**
1. An initiator records its own state and sends a marker on every outgoing channel.
2. When a process receives its first marker: it records its own state, and sends markers on all its outgoing channels.
3. For each incoming channel, the process records all messages that arrive after it recorded its state and before that channel's marker arrives. Those are the channel's in-flight messages.
4. The snapshot is complete when every process has received a marker on every incoming channel.
5. The recorded states and channel messages form a consistent cut: a state the system could actually have been in.

**Cost:** Marker messages and recorded channel contents.

**Agent use:**
- **Role:** Verifier.
- **How:** The theoretical foundation of stream checkpointing (#35, #36). Explains why checkpoints are consistent without pausing the job.
- **Rules:** None beyond the implementations.
- **Guardrails:** None specific.

### 35. Asynchronous barrier snapshotting (aligned checkpoints)

**Definition:** The stream-processing version of Chandy-Lamport used by Flink-like systems: barriers flow through the data stream, and operators snapshot their state when barriers pass.

**How it works:**
1. The coordinator injects a numbered checkpoint barrier into every source partition, and sources record their read positions (offsets).
2. Barriers flow downstream with the data, never overtaking records.
3. **Alignment:** an operator with several inputs waits until it has received the barrier on every input. It buffers (or blocks) inputs that have already delivered their barrier, so no post-barrier data mixes into the snapshot.
4. Once aligned, the operator snapshots its state (asynchronously, copy-on-write), and forwards the barrier.
5. When every sink has acknowledged the barrier, the checkpoint is complete. Recovery restores every state and rewinds the sources to the recorded offsets.
6. Because the data streams themselves are replayable, no in-flight messages need to be stored.

**Cost:** Alignment delays under backpressure. Asynchronous state upload.

**Agent use:**
- **Role:** Processor.
- **How:** The foundation of exactly-once state in streaming jobs (with transactional sinks, #37).
- **Rules:** Monitor checkpoint duration and alignment time (NR4-style). Long alignment means backpressure.
- **Guardrails:** Checkpoint intervals bound how much is reprocessed after failures. Choose them by recovery time targets.

### 36. Unaligned checkpoints

**Definition:** A checkpointing variant where barriers overtake buffered records, and the in-flight data is stored as part of the checkpoint, so checkpoints complete quickly even under heavy backpressure.

**How it works:**
1. When an operator receives a barrier on any input, it immediately forwards the barrier to its outputs, jumping ahead of queued data.
2. It snapshots its state, plus all the records in its input and output buffers that the barrier overtook (the in-flight data, as in Chandy-Lamport's channel recording).
3. No waiting for alignment.
4. Recovery restores the state plus the in-flight records.
5. Checkpoints become larger (in-flight data) but faster under backpressure.

**Cost:** Larger checkpoints. Fast completion.

**Agent use:**
- **Role:** Processor.
- **How:** Keeps checkpoints completing (and recovery times bounded) when jobs are backpressured, such as during catch-up after outages.
- **Rules:** Enable when aligned checkpoints time out under load. Some systems switch automatically after an alignment timeout.
- **Guardrails:** Rescaling from unaligned checkpoints has constraints in some systems. Check before relying on it.

### 37. Exactly-once sinks with two-phase commit

**Definition:** Making external outputs exactly-once by committing them transactionally only when the checkpoint that covers them completes.

**How it works:**
1. For each checkpoint interval, the sink opens a transaction in the external system (a transactional producer, a database transaction, staged files).
2. Records are written inside the open transaction (invisible to readers).
3. **Pre-commit:** when the checkpoint barrier reaches the sink, it flushes and prepares the transaction, and records the transaction ID in its checkpoint state.
4. **Commit:** when the coordinator confirms the checkpoint completed everywhere, the sink commits the transaction.
5. **Recovery:** pending transactions from the last completed checkpoint are committed; later ones are aborted. The external system must support resuming a transaction by ID.

**Cost:** Output visible only at checkpoint completion (latency = checkpoint interval).

**Agent use:**
- **Role:** Pipeline Builder.
- **How:** End-to-end exactly-once (T2) for financial counts, billing and audit outputs.
- **Rules:** Consumers of the output must read only committed data (#38's read_committed).
- **Guardrails:** Transaction timeouts in the external system must exceed the maximum checkpoint plus recovery time, or committed checkpoints lose their data.

### 38. Kafka transactions (consume-transform-produce)

**Definition:** Kafka's protocol for atomically writing output records to several partitions together with the consumer's input offsets, making read-process-write loops exactly-once within Kafka.

**How it works:**
1. A producer registers a `transactional.id`. The coordinator assigns a producer ID and epoch, fencing off older instances with the same ID (zombie fencing).
2. `beginTransaction`, then send output records to any partitions.
3. `sendOffsetsToTransaction`: the consumed input offsets are written as part of the same transaction.
4. `commitTransaction`: the coordinator writes commit markers to every involved partition (a two-phase protocol through a transaction log).
5. Consumers with `isolation.level=read_committed` see only committed records, and skip aborted ones.

**Cost:** Commit latency per transaction, and some throughput cost (batch transactions to amortize it).

**Agent use:**
- **Role:** Pipeline Builder.
- **How:** Exactly-once processing in Kafka-native pipelines (Kafka Streams "exactly_once_v2").
- **Rules:** Keep transactional IDs stable per instance and partition assignment.
- **Guardrails:** Exactly-once applies only within Kafka. External side effects (emails, API calls) are still at-least-once (TX2): make them idempotent.

### 39. Idempotent producers

**Definition:** A broker-side mechanism that discards duplicate writes caused by producer retries, using producer IDs and per-partition sequence numbers.

**How it works:**
1. The producer gets a producer ID and attaches a sequence number per partition to each batch.
2. The broker remembers the last sequence numbers per (producer ID, partition).
3. A retried batch with an already-seen sequence is acknowledged but not written again.
4. Out-of-order sequences (gaps) are rejected, preserving order.
5. Combined with transactions (#38), it gives exactly-once writes.

**Cost:** Negligible.

**Agent use:**
- **Role:** Pipeline Builder.
- **How:** Always enabled for producers: prevents duplicates from network retries.
- **Rules:** Pair with `acks=all` and bounded in-flight requests per the system's requirements.
- **Guardrails:** Doesn't deduplicate across producer restarts without transactions, or application-level resends. Use #7 for those.

### 40. State TTL and retention

**Definition:** Automatic expiry of state entries after a time limit, to keep long-running stateful jobs from growing without bound.

**How it works:**
1. Each state entry gets a timestamp: last write, or last access (configurable).
2. On read, expired entries are treated as absent (and optionally returned anyway if not yet cleaned up, configurable).
3. **Cleanup:** incremental cleanup during access, full-snapshot cleanup at checkpoints, or compaction filters in LSM backends.
4. TTL is based on processing time in many systems. Event-time semantics need explicit timers instead.

**Cost:** Timestamp per entry. Background cleanup.

**Agent use:**
- **Role:** Processor.
- **How:** Bounding state for deduplication (#7), unbounded joins (#26), and per-user aggregates (T3).
- **Rules:** Document the TTL and its effect on results.
- **Guardrails:** Processing-time TTL behaves differently during replays (everything might expire immediately or never). Test replay scenarios.

### 41. Rescaling stateful jobs

**Definition:** Changing the parallelism of a running stateful job while keeping state and exactly-once guarantees.

**How it works:**
1. Take a savepoint (a portable checkpoint).
2. Stop the job.
3. Restart with the new parallelism. Each new instance loads the key-group ranges (#32) it now owns from the savepoint.
4. Operator state that isn't keyed (source offsets, broadcast state) is redistributed by its declared method (split, union, broadcast).
5. **Reactive or in-place rescaling:** some systems rescale from the last checkpoint automatically when resources change.

**Cost:** Downtime of a stop-restore cycle (shorter with local recovery).

**Agent use:**
- **Role:** Processor.
- **How:** Executes scaling decisions (#31) safely.
- **Rules:** Take and verify a savepoint before every rescale.
- **Guardrails:** TX4: production rescales follow change approval and are done in maintenance windows where possible.

### 42. Changelog topics, standby replicas and state restoration

**Definition:** Making local state durable by mirroring every state change to a compacted log, and keeping warm copies on other instances for fast failover (Kafka Streams model).

**How it works:**
1. Every write to a local state store is also sent to a changelog topic (compacted, #47).
2. On failure or rebalance, the new owner rebuilds the store by replaying the changelog.
3. **Standby replicas:** other instances continuously consume the changelog into a copy of the store, so failover takes seconds instead of a full replay.
4. **Warm-up replicas:** during rebalancing, state is pre-copied to the new owner before the task moves (probing rebalances).
5. Restoration progress is tracked by changelog offsets.

**Cost:** Changelog write amplification. Standby replicas double state storage.

**Agent use:**
- **Role:** Processor.
- **How:** Fast, safe recovery for large stateful stream applications.
- **Rules:** Configure at least one standby for latency-critical applications. Monitor restoration lag.
- **Guardrails:** Changelogs contain all state values: apply the same data governance (TX3).

## A6. Partitioning, consumption and log management

### 43. Producer partitioning strategies

**Definition:** How producers choose a partition for each record, which determines ordering, load balance and co-partitioning.

**How it works:**
1. **Key hashing:** partition = hash(key) mod number of partitions (murmur2 in Kafka's default). All records with the same key go to the same partition, preserving their order.
2. **Round-robin:** spreads keyless records evenly.
3. **Sticky partitioning:** for keyless records, fill one partition's batch before switching, giving larger batches and better throughput.
4. **Custom partitioners:** by tenant, region or priority.
5. Changing the number of partitions changes the key-to-partition mapping for hashed keys.

**Cost:** Negligible.

**Agent use:**
- **Role:** Pipeline Builder.
- **How:** Chooses keys that give both the needed ordering (per account, per device) and even distribution.
- **Rules:** T4: document the partition key and count. Keys must match across topics that are joined (#50).
- **Guardrails:** Adding partitions to a keyed topic breaks per-key ordering for in-flight data and existing co-partitioning. Plan it as a migration (TX4).

### 44. Consumer group partition assignment (range, round-robin, sticky, cooperative)

**Definition:** The protocols and strategies by which a group of consumers divides a topic's partitions among themselves, and rebalances when members join or leave.

**How it works:**
1. Members join a group coordinated by a broker. A leader computes the assignment (or the broker does, in newer protocols).
2. **Range:** consecutive partitions per consumer per topic (keeps co-partitioned topics aligned).
3. **Round-robin:** spreads partitions evenly across consumers.
4. **Sticky:** keeps existing assignments as much as possible when membership changes, so less state moves.
5. **Cooperative (incremental) rebalancing:** instead of every consumer releasing all partitions ("stop the world"), only the partitions that must move are revoked, over two rounds. Others keep processing.
6. Newer broker-side protocols compute assignments incrementally on the coordinator.

**Cost:** Rebalances pause affected partitions.

**Agent use:**
- **Role:** Processor.
- **How:** Uses cooperative sticky assignment for stateful consumers, to minimize pauses and state movement.
- **Rules:** Monitor rebalance frequency and duration.
- **Guardrails:** Rebalance storms (consumers repeatedly timing out because processing is slow) stall whole groups. Tune poll intervals and processing batches.

### 45. Static membership (rebalance avoidance)

**Definition:** Giving each consumer a persistent identity, so short restarts don't trigger rebalances.

**How it works:**
1. Each consumer instance has a fixed `group.instance.id`.
2. When it disconnects, the coordinator keeps its partitions assigned until a session timeout expires.
3. If it returns within the timeout (a rolling restart, a brief failure), it gets the same partitions back, with no rebalance.
4. Only a real departure (timeout exceeded) triggers reassignment.

**Cost:** Slower detection of real failures (bounded by the timeout).

**Agent use:**
- **Role:** Processor.
- **How:** Avoids rebalances during deployments and restarts of stateful consumers.
- **Rules:** Set the session timeout longer than a normal restart, and shorter than the acceptable outage time.
- **Guardrails:** Duplicate instance IDs cause fencing errors. Make IDs unique per instance.

### 46. Offset management and commit strategies

**Definition:** How and when consumers record their progress (offsets), which determines delivery semantics.

**How it works:**
1. **Commit after processing** (at-least-once): process records, then commit offsets. A crash between them causes reprocessing (duplicates).
2. **Commit before processing** (at-most-once): commit, then process. A crash loses records.
3. **Transactional commit** (exactly-once within Kafka): offsets committed in the same transaction as outputs (#38).
4. **External offsets:** store offsets in the same database transaction as the results (exactly-once with that database).
5. Automatic periodic commits are convenient but give fuzzy semantics. Explicit commits are clearer.

**Cost:** Commit frequency trades overhead against replay amount.

**Agent use:**
- **Role:** Pipeline Builder.
- **How:** Chooses and documents the semantics per consumer (T2).
- **Rules:** At-least-once consumers need idempotent processing and sinks (#7, TX2).
- **Guardrails:** Auto-commit with asynchronous processing can commit offsets for unprocessed records: data loss. Avoid it.

### 47. Log compaction (key-based retention and tombstones)

**Definition:** Retention that keeps at least the latest record for each key in a topic, deleting older versions, so the topic becomes a durable table.

**How it works:**
1. The log is split into segments. The active (newest) segment isn't compacted.
2. A cleaner builds a map from key to the latest offset in the "dirty" (not yet cleaned) part.
3. It rewrites older segments, keeping only records that are the latest for their key.
4. **Tombstones:** a record with a null value deletes its key. Tombstones are kept for a configured time (so consumers can see the deletion), then removed.
5. Order of the remaining records is preserved, and offsets don't change.

**Cost:** Background cleaner I/O.

**Agent use:**
- **Role:** Pipeline Builder.
- **How:** Changelogs (#42), CDC-backed tables (#21) and configuration topics, with rebuildable state.
- **Rules:** Set tombstone retention longer than the slowest consumer's catch-up time.
- **Guardrails:** Compaction keeps only the latest value. For erasure requests, a tombstone must be written, and the data persists until compaction runs (TX3).

### 48. Time and size retention, segment rolling and tiered storage

**Definition:** How logs expire old data by age or size, and how tiered storage moves older segments to cheap object storage while keeping them readable.

**How it works:**
1. The log is divided into segments, rolled by size or time.
2. **Retention:** delete whole segments older than the retention time, or when the total size exceeds the limit.
3. **Tiered storage:** closed segments are uploaded to object storage. Brokers keep only recent segments on local disk. Reads of old data are fetched remotely.
4. Indexes (offset and time indexes per segment) allow fast lookup of a position or a timestamp.

**Cost:** Tiered storage cuts disk costs. Remote reads are slower.

**Agent use:**
- **Role:** Coordinator.
- **How:** Long retention for replay and backfills (#41, reprocessing), at low cost.
- **Rules:** Retention must cover the longest replay or recovery need.
- **Guardrails:** Retention also determines how long personal data persists (TX3). Align it with data policies.

### 49. Dead-letter queues and retry topics

**Definition:** Routing records that fail processing to separate topics, with delayed retries, instead of blocking the partition or losing data.

**How it works:**
1. On a processing failure, classify the error: retryable (timeout, temporary unavailability) or permanent (bad format, validation failure).
2. **Retryable:** publish the record to a retry topic with a delay tier (for example 1 minute, 10 minutes, 1 hour). A consumer reads each tier after its delay.
3. After the maximum number of retries, or for permanent errors: publish to a dead-letter queue with the error details, the original topic, partition and offset.
4. The main consumer continues with the next record, so one bad record doesn't block the partition.
5. Dead-letter records are inspected, fixed and replayed through a controlled process.

**Cost:** Extra topics and consumers.

**Agent use:**
- **Role:** Processor.
- **How:** Keeps pipelines flowing with "poison" records, while preserving everything for repair.
- **Rules:** Alert on dead-letter volume. Every dead-letter record needs an owner and a resolution.
- **Guardrails:** Retry topics break per-key ordering. Don't use them where order matters, without per-key blocking logic.

### 50. Repartitioning and co-partitioning for joins

**Definition:** Making sure records with the same join key are in the same partition number of each joined topic, and reshuffling (repartitioning) data when they aren't.

**How it works:**
1. **Co-partitioning requirements:** the same number of partitions, the same partitioning function, and the same key (in the same format) in both inputs.
2. If not, insert a repartition step: re-key the records, and write them to an internal topic partitioned by the join key.
3. Downstream join tasks read matching partitions from each input.
4. Global or broadcast tables (#21) avoid repartitioning for small reference data.
5. Repartitioning adds latency, network traffic and storage.

**Cost:** One extra write and read through the broker.

**Agent use:**
- **Role:** Pipeline Builder.
- **How:** Validates co-partitioning before deploying any join (T4), and minimizes repartition steps by choosing keys early.
- **Rules:** Use broadcast tables for small, slowly changing reference data.
- **Guardrails:** Key serialization differences (string versus integer encoding of the "same" key) silently break joins. Verify by test.

---
