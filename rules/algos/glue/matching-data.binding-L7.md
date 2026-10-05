## Layer 7: Matching and data binding

### G53. Unification (pattern matching with variables)

**Definition:** Finding variable bindings that make two structured patterns identical, the core matching step inside planners and rule engines.

**How it works:**
1. Two terms are compared, for example `requires(sorted(List[X]))` and `provides(sorted(List[Path]))`.
2. Matching constants must be equal. A variable binds to whatever is in the same position (X = Path).
3. A variable bound earlier must match consistently everywhere it appears.
4. The occurs check prevents a variable binding to a term containing itself (an infinite structure).
5. The output is the most general set of bindings, or failure.

**Glue use:** The planner (G18–G22) uses unification to decide whether one step's guaranteed effects satisfy another step's preconditions, including generic types (G55).

**Guardrails:** Always enable the occurs check in planning and rule engines, so malformed contracts can't cause infinite loops.

### G54. Subtyping and structural compatibility

**Definition:** Rules deciding when a value of one type can be used where another type is expected.

**How it works:**
1. **Nominal subtyping:** a type is compatible if it's declared as a subtype ("RankedMatchList" is declared a subtype of "MatchList").
2. **Structural subtyping:** a type is compatible if it has every required field with a compatible type, even without a declaration.
3. **Variance rules:** a function or algorithm can accept more general input and produce more specific output than required, but not the other way around.
4. Optional versus required fields follow schema evolution rules (G3).

**Glue use:** The type-directed composer (G23) accepts connections without needing an adapter for every small type difference, and still rejects truly incompatible ones.

**Guardrails:** Structural matches must also check meaning-carrying metadata (units, coordinate systems, byte versus character offsets). Same shape doesn't mean same meaning.

### G55. Generic (parametric) types for algorithms

**Definition:** Declaring algorithms over type parameters, so one algorithm works for many element types.

**How it works:**
1. A contract like `dedupe: List[T] → List[T]`, or `topK: List[Scored[T]], k → List[Scored[T]]`.
2. When used, T binds to a concrete type (T = Match, T = Chunk) through unification (G53).
3. Constraints on T (for example "T must have an ID field" or "T must be hashable") are checked when the type is bound.
4. One registry entry then serves many flows.

**Glue use:** Generic utilities (sort, dedupe, merge, filter, top-k, batch) work everywhere, which cuts the registry size and the adapter count.

**Guardrails:** Constraint checking at binding time is mandatory, so a generic algorithm is never applied to a type it can't handle.

### G56. Expression language for guards and scopes (CEL)

**Definition:** A small, safe, non-Turing-complete language for writing conditions, filters and scope rules. Google's Common Expression Language (CEL) is a widely used open specification.

**How it works:**
1. Expressions like `result.count > 0 && result.recall >= 0.95`, or `file.path.startsWith("src/") && file.lang == "ts"`.
2. Expressions are parsed and type-checked against declared variable types before running.
3. Evaluation is guaranteed to terminate, with no loops or side effects, and with a cost limit.
4. The same expression gives the same result for the same input (deterministic).

**Glue use:** Every guard (G31), scope (G45), stop condition (G33) and rule condition (G26) uses one consistent language, instead of scattered custom code.

**Guardrails:** Set evaluation cost limits. Expressions are type-checked when flows are saved, not only when they run.

### G57. Data selection paths (JSONPath, RFC 9535)

**Definition:** A standard syntax for selecting parts of structured data, standardized by the IETF as JSONPath in RFC 9535.

**How it works:**
1. Path expressions navigate nested data: `$.matches[*].range.start` selects every match's start offset.
2. Filters select by condition: `$.matches[?@.score > 0.8]`.
3. The result is a list of selected values, with their locations.
4. Used to bind specific fields of one step's output to another step's input parameters.

**Glue use:** Wires steps together without adapter code ("pass `$.files[*].path` from step 3 into step 5 as `paths`"), so flows can be defined entirely in configuration.

**Guardrails:** Validate the selected values against the target input schema (G6). A path selecting nothing is an error, unless it's explicitly declared optional.

### G58. Structured data patching (JSON Patch RFC 6902, JSON Merge Patch RFC 7386)

**Definition:** IETF standard formats describing changes to structured data documents.

**How it works:**
1. **JSON Patch:** a list of operations (add, remove, replace, move, copy, test) with paths. The `test` operation makes a patch fail unless a value matches what's expected.
2. **JSON Merge Patch:** a partial document. Fields present replace the original values, and `null` removes them.
3. Patches are applied atomically: all operations or none.

**Glue use:** Steps update shared context (G43) or configuration with precise, reviewable, revertible changes, instead of overwriting whole documents.

**Guardrails:** Use JSON Patch with `test` operations for concurrent updates. That gives an optimistic check, similar to G87.

### G59. Canonical serialization and hashing (JSON Canonicalization Scheme, RFC 8785)

**Definition:** A standard way to serialize data so identical content always produces identical bytes, and therefore identical hashes.

**How it works:**
1. Sort object keys in a defined order.
2. Use a canonical number format and canonical string escaping.
3. No insignificant whitespace.
4. Hash the canonical bytes (for example with SHA-256).

**Glue use:** Cache keys (G39), idempotency keys (G40), plan IDs and change detection (G41) all depend on stable hashes. Without canonicalization, the same parameters in a different key order miss the cache, or get processed twice.

**Guardrails:** Use canonical hashing for every key derived from structured data.

## Layer 8: Dependency and plugin management

### G60. Dependency resolution (SAT-based, PubGrub)

**Definition:** Choosing compatible versions of every algorithm and library a flow needs, or explaining why none exist.

**How it works:**
1. Each component version declares which versions of other components it needs.
2. Finding a set of versions satisfying every requirement is a Boolean satisfiability (SAT) problem.
3. **PubGrub** (used by the Dart and Swift package managers, and others) does conflict-driven search: when it hits a conflict, it learns why and skips similar dead ends.
4. On failure, it produces a readable explanation of the conflicting requirements.

**Glue use:** When a plan combines 40 algorithms with different library requirements, the resolver picks consistent versions automatically, or explains exactly which pair conflicts.

**Guardrails:** Lock the resolved versions for each saved plan, so reruns are reproducible.

### G61. Capability negotiation

**Definition:** At runtime, checking which features each component actually supports, and adapting the plan to match.

**How it works:**
1. Components advertise capabilities: supported versions, optional features, limits ("supports filtered search", "maximum batch 1,000").
2. The engine compares the required capabilities with the advertised ones (as LSP's initialize handshake does).
3. Missing features trigger a fallback (G94), or a re-plan that avoids that component.
4. Results are cached for each component instance.

**Glue use:** The same flow works across environments with different engines or versions, choosing compatible paths automatically.

**Guardrails:** Never assume a capability without a positive answer from the component.

### G62. Plugin isolation (process and WebAssembly sandboxes)

**Definition:** Running each algorithm in an isolated environment with limited permissions and resources.

**How it works:**
1. Each algorithm runs in its own process, container or WebAssembly module.
2. Permissions are granted explicitly: which files, which network hosts, how much memory and CPU (WASI capability-based permissions for WebAssembly, for example).
3. Communication goes only through the declared inputs and outputs.
4. A crash or hang in one plugin can't take down the engine.

**Glue use:** You can combine many algorithms of varying quality safely. A buggy one fails alone, inside its sandbox.

**Guardrails:** Least privilege by default. Each plugin gets only the scope (G45) of its current step.

### G63. Parameterized flow templates (macros)

**Definition:** Reusable flow definitions with parameters that are expanded into concrete plans.

**How it works:**
1. A template defines a flow with placeholders: `safe_rename(symbol_from, symbol_to, scope)`.
2. Instantiating it substitutes and type-checks the parameters (G56).
3. The expanded plan is validated (G28) like any other plan.
4. Templates can call other templates, with a depth limit.

**Glue use:** Proven combinations are captured once and reused with different inputs, which gives a library of tested recipes alongside HTN methods (G21).

**Guardrails:** Templates are versioned (G3) and tested (G95–G98). Instantiation can't widen the scope passed in.

### G64. Plan diffing and versioning

**Definition:** Comparing two plans, or two versions of a plan, structurally, to see exactly what changed.

**How it works:**
1. Represent plans as graphs (G8).
2. Match nodes between versions by stable step IDs, or by similarity.
3. Report added, removed and changed steps, changed edges, and parameter changes.
4. Store every plan version with its hash (G59).

**Glue use:** When automatic planning (Layer 3) produces a different plan than last time, you can see why, and review only the differences.

**Guardrails:** Changes to write steps between plan versions require review before execution.

## Layer 9: Scheduling and resources

### G65. Weighted fair queuing and dominant resource fairness (DRF)

**Definition:** Sharing workers and resources fairly across many concurrent flows or tenants.

**How it works:**
1. **Weighted fair queuing:** each flow gets a share of capacity proportional to its weight. Idle shares are redistributed to busy flows.
2. **DRF:** with several resource types (CPU, memory, API quota), each flow's "dominant share" is its largest fractional use of any one resource. Each new allocation goes to the flow with the smallest dominant share.
3. This prevents one heavy flow from starving others.

**Glue use:** Many flows built from different combinations can run at once without one large migration blocking everything else.

**Guardrails:** Every flow has at least a minimum guaranteed share, and a maximum cap.

### G66. Token bucket rate limiting

**Definition:** Limiting how fast operations happen, while allowing short bursts.

**How it works:**
1. A bucket holds up to B tokens and refills at R tokens per second.
2. Each operation takes one token (or more, weighted by cost).
3. If the bucket is empty, the operation waits or is rejected.
4. Buckets can be set per flow, per tenant, per algorithm and per external API.

**Glue use:** Protects external services and shared indexes from bursts created by fan-out (G32) inside combined flows.

**Guardrails:** Set limits from the downstream service's real capacity, not guesses.

### G67. Admission control and load shedding

**Definition:** Deciding whether to accept new work, based on current load, and dropping or deferring low-priority work under overload.

**How it works:**
1. Measure the load: queue depth, latency, resource use.
2. When it's above a threshold, reject or defer new low-priority flows.
3. Degrade gracefully: run cheaper plan variants (G94) instead of failing.
4. Return clear "retry later" signals.

**Glue use:** The engine stays stable even when many complex combinations are requested at once.

**Guardrails:** Never shed critical work, such as deletions, rollbacks or safety checks.

### G68. Bin packing for worker placement

**Definition:** Assigning steps to workers so that resources are used efficiently, without overloading any worker.

**How it works:**
1. Each step has resource needs (CPU, memory, GPU). Each worker has capacity.
2. Heuristics: first-fit decreasing (place the largest steps first, each into the first worker where it fits), or best-fit.
3. Multi-dimensional versions balance several resources at once.
4. Re-pack when workers are added or removed.

**Glue use:** Heavy steps (index builds, embedding batches) and light steps (filters, adapters) share hardware efficiently.

**Guardrails:** Leave headroom on every worker for bursts and system processes.

### G69. Work stealing

**Definition:** Letting idle workers take queued tasks from busy workers.

**How it works:**
1. Each worker has its own task queue (a deque).
2. A worker takes tasks from one end of its own deque.
3. An idle worker steals from the other end of a busy worker's deque.
4. Load balances automatically, with little coordination.

**Glue use:** Uneven sub-tasks (some repos huge, some tiny) finish without idle workers waiting.

**Guardrails:** Stealing must respect scope partition ownership (G47). Never steal a task assigned exclusively to one partition owner.

### G70. Priority aging

**Definition:** Gradually raising the priority of waiting tasks, so low-priority work eventually runs.

**How it works:**
1. Each task has a base priority.
2. Its effective priority increases with its waiting time.
3. Eventually, every waiting task outranks newly arriving work.

**Glue use:** Background flows (reindexing, quality checks) still complete while interactive flows get preference.

**Guardrails:** Cap the maximum aged priority below critical tasks.

### G71. Deadline scheduling (earliest deadline first)

**Definition:** Running the task with the nearest deadline first.

**How it works:**
1. Each task or flow has a deadline.
2. The scheduler always picks the ready task with the earliest deadline.
3. A deadline that can't be met triggers degradation (G94) or a cancellation decision.
4. On a single resource, if any schedule can meet every deadline, EDF meets them too.

**Glue use:** Interactive requests with tight latency budgets get done in time, even when they're built from many steps.

**Guardrails:** Admission control (G67) rejects work that can't possibly meet its deadline, instead of accepting and failing.

### G72. Request coalescing (batching and deduplication of in-flight work)

**Definition:** Combining identical or similar requests that arrive close together, so the work is done once.

**How it works:**
1. **Deduplication ("single-flight"):** if an identical request is already running (same canonical key, G59), later callers wait for its result instead of running it again.
2. **Batching:** collect similar requests for a short window and process them together (embedding batches, multi-get lookups).
3. Distribute the results to all callers.

**Glue use:** When many flows need the same intermediate result at the same time, it's computed once.

**Guardrails:** Coalesce only read-only, deterministic steps. Keep permission scopes separate: different users' requests coalesce only if their access is identical.

### G73. Backpressure (Reactive Streams specification)

**Definition:** Consumers signal how much data they can accept, so producers never overwhelm them.

**How it works:**
1. A consumer requests N items.
2. The producer sends at most N items, then waits for more requests.
3. Demand propagates upstream through the whole pipeline.
4. The Reactive Streams specification standardizes this protocol on the JVM, and it's the model in many streaming systems.

**Glue use:** In streaming flows (G14), a slow step automatically slows everything upstream, with no unbounded queues and no memory blowups.

**Guardrails:** Combine with timeouts. A consumer that stops requesting entirely must be detected.

## Layer 10: Distributed coordination (running the engine on many machines)

### G74. Leader election with leases

**Definition:** Choosing exactly one coordinator among several engine instances, with automatic takeover when it fails.

**How it works:**
1. Instances compete to acquire a lease (a lock with an expiry) in a consistent store (etcd, ZooKeeper, or a database).
2. The holder is the leader, and must renew the lease before it expires.
3. If the leader stops renewing, the lease expires, and another instance takes over.

**Glue use:** One scheduler or planner is in charge at a time, so plans don't get executed twice by competing coordinators.

**Guardrails:** Always combine leases with fencing tokens (G75). A paused old leader may wake up still believing it leads.

### G75. Distributed locks with fencing tokens

**Definition:** Locks that come with an increasing number, so that stale lock holders are rejected by the resources they try to write.

**How it works:**
1. Each lock grant includes a token that increases with every grant.
2. The holder sends its token with every write to the protected resource.
3. The resource rejects any write with a token lower than the highest it has already seen.
4. A holder whose lock expired (because of a long pause) can no longer corrupt data.

**Glue use:** Safe exclusive access to shared targets (a repo branch, an index, a graph partition) across distributed workers.

**Guardrails:** Locks without fencing aren't safe for correctness. Use them only for efficiency.

### G76. Raft consensus for engine state

**Definition:** Keeping the engine's critical state (flow registry, plan states, locks) consistent across machines, tolerating failures.

**How it works:**
1. A replicated log of state changes. An entry is committed when a majority of nodes have stored it.
2. An elected leader orders all writes, and followers replicate them.
3. Committed entries survive any minority of node failures.
4. Usually used through an existing system (etcd, Consul) rather than implemented from scratch.

**Glue use:** Flow states, budgets and locks never diverge between engine instances.

**Guardrails:** Run 3 or 5 nodes across failure zones, and keep large data out of the consensus log.

### G77. Transactional outbox for step results

**Definition:** Writing a step's result and its "completed" event in one local transaction, then publishing the event reliably.

**How it works:**
1. In one transaction, store the result and an outbox record.
2. A relay publishes the outbox records to the event bus (G42).
3. Mark them as published after acknowledgment. Consumers deduplicate repeats (G40).

**Glue use:** A step never finishes "silently". Its successors are always notified, even after crashes.

**Guardrails:** Alert on outbox backlog age.

### G78. Lease-based task claiming (visibility timeout)

**Definition:** Workers claim tasks for a limited time. Unfinished tasks return to the queue automatically.

**How it works:**
1. A claimed task becomes invisible to other workers for a lease period.
2. The worker finishes and acknowledges it, or extends the lease.
3. If the lease expires (the worker died), the task becomes visible again.
4. Idempotency (G40) handles the case where a task actually finished but wasn't acknowledged.

**Glue use:** No task is lost when workers crash, across any number of combined flows.

**Guardrails:** Lease length must exceed typical task time. Long tasks must send heartbeats.

### G79. Consistent hashing for flow affinity

**Definition:** Routing related work to the same worker consistently, while moving as little as possible when workers change.

**How it works:**
1. Workers and keys (repo, tenant, flow ID) are placed on a hash ring.
2. Each key goes to the next worker clockwise.
3. Virtual nodes even out the load.
4. Adding or removing a worker moves only the keys next to it on the ring.

**Glue use:** The same repo's flows go to the same worker, which keeps its caches warm (G39) and avoids conflicting writes.

**Guardrails:** When ownership moves, hand off cleanly with fencing (G75).

### G80. Logical clocks (Lamport and vector clocks)

**Definition:** Ordering events across machines without relying on synchronized wall clocks.

**How it works:**
1. **Lamport clock:** each process keeps a counter. It increments the counter on every event, and on receiving a message sets it to max(own, received) + 1. If one event caused another, the first has the smaller timestamp.
2. **Vector clock:** one counter per process. It shows whether two events are causally ordered or truly concurrent.
3. Used to order step results and detect conflicting concurrent updates.

**Glue use:** Correct ordering of results from distributed steps, and conflict detection for concurrent writes to shared context (G43).

**Guardrails:** Never order critical events by wall-clock time across machines.

### G81. Failure detection (heartbeats, phi accrual)

**Definition:** Deciding when a worker or component should be considered failed.

**How it works:**
1. Components send regular heartbeats.
2. **Simple:** missing heartbeats for a timeout means failed.
3. **Phi accrual:** compute a suspicion level from the observed heartbeat timing distribution, and act at a threshold. It adapts to network variability (used in Cassandra and Akka).
4. Suspected failures trigger lease expiry (G78) and re-assignment.

**Glue use:** Stuck or dead steps are detected and recovered automatically, inside any flow.

**Guardrails:** Tune thresholds to avoid flapping (marking healthy components as failed during short network hiccups).

## Layer 11: State management

### G82. Event sourcing

**Definition:** Storing every state change as an immutable event, and deriving the current state by replaying them.

**How it works:**
1. Each change is an event ("StepStarted", "StepCompleted", "BudgetConsumed") appended to a log.
2. Current state = all events replayed in order.
3. Past states can be reconstructed at any point in time.
4. Events are never modified. Corrections are new events.

**Glue use:** A complete, auditable history of every flow. It's the foundation of durable execution (G37) and deterministic replay (G51).

**Guardrails:** Events carry schema versions (G3). Replay code must handle old event versions.

### G83. CQRS (separate write model and read views)

**Definition:** Separating the model that records changes from the models that answer queries.

**How it works:**
1. The write side appends events (G82).
2. Projections consume the events and build read-optimized views: flow status dashboards, per-repo progress, cost summaries.
3. Views can be rebuilt from the events at any time.
4. Views are eventually consistent with the write side.

**Glue use:** Fast monitoring and progress queries over thousands of running flows, without slowing down execution.

**Guardrails:** Show view freshness. Decisions needing exact state read the write side.

### G84. Snapshots and log compaction

**Definition:** Periodically saving the full state, so replay starts from the snapshot instead of from the very first event.

**How it works:**
1. Every N events, or every T minutes, save the full flow state with its event position.
2. Recovery loads the latest snapshot and replays only the events after it.
3. Older events can be archived or compacted, if policy allows.

**Glue use:** Long-running and repeated flows (G33) recover quickly, even after millions of events.

**Guardrails:** Verify snapshots by comparing them against a full replay periodically.

### G85. Copy-on-write branching of flow state

**Definition:** Creating cheap copies of the state to try alternatives in parallel, using persistent data structures.

**How it works:**
1. State is stored in persistent structures (Code ref #143): an update creates a new version sharing unchanged parts.
2. A branch is just a new root pointing to shared data.
3. Run alternative plans on separate branches.
4. Keep the winning branch and discard the others.

**Glue use:** Speculative execution: try two combinations side by side, then keep the one that passes verification. No full copies needed.

**Guardrails:** Side effects (writes outside the engine) are never allowed on speculative branches.

### G86. Two-phase commit (when atomic multi-resource commits are available)

**Definition:** A protocol for committing changes to several resources all at once, or not at all.

**How it works:**
1. **Prepare phase:** the coordinator asks every participant to prepare (make changes durable but invisible) and vote yes or no.
2. **Commit phase:** if all voted yes, the coordinator tells all to commit. Otherwise, all abort.
3. Participants that voted yes must wait for the decision. A failed coordinator can block them.

**Glue use:** For steps writing to several transactional stores that support it, 2PC gives true atomicity. Otherwise use sagas (G38).

**Guardrails:** Use only within one trusted, reliable infrastructure. Across services, prefer sagas, because 2PC blocking hurts availability.

### G87. Optimistic concurrency (compare-and-swap)

**Definition:** Updating shared state only if it hasn't changed since you read it.

**How it works:**
1. Read the state with its version number.
2. Compute the update.
3. Write with the condition "version is still N". If the condition fails, re-read and retry.
4. No locks are held while computing.

**Glue use:** Many parallel steps safely update the shared context (G43) and the registry (G2).

**Guardrails:** Cap the retries. Persistent conflicts mean the work should be partitioned (G47).

### G88. Lifecycle and garbage collection of intermediate artifacts

**Definition:** Cleaning up temporary results that are no longer needed by any flow.

**How it works:**
1. Each artifact (intermediate results, caches, temporary indexes, worktrees) has an owner flow, a reference count and a time-to-live (TTL).
2. When no flow references an artifact and its TTL has passed, it's deleted.
3. Mark-and-sweep: periodically mark everything reachable from active flows, and delete the rest.
4. Pinned artifacts (needed for audit or replay) are kept.

**Glue use:** Combined flows produce many intermediate results. Without collection, storage grows without limit.

**Guardrails:** Never delete artifacts needed for running flows, rollbacks or required audits. Deletion of sensitive data follows the erasure rules.

## Layer 12: Adaptivity without AI (statistical learning, zero tokens)

### G89. Multi-armed bandits (UCB, Thompson sampling)

**Definition:** Learning which option works best by trying options and favoring the ones that perform well, while still occasionally testing the others.

**How it works:**
1. Each "arm" is an alternative: a different algorithm combination or parameter set for the same goal.
2. After each run, record the reward: success, speed, quality score, cost.
3. **UCB (upper confidence bound):** pick the arm with the highest average reward plus an uncertainty bonus, so rarely tried arms get explored.
4. **Thompson sampling:** keep a probability distribution of each arm's reward, sample once from each, and pick the highest sample.
5. Over time, most runs use the best option.
6. **Contextual bandits** learn the best option for each context (data size, language, repo type).

**Glue use:** The engine learns from its own history which of several valid plans works best for each kind of task. It's cheap, statistical and needs no LLM.

**Guardrails:** Only choose among plans that already passed validation (G28). Bandits pick between safe options, never unsafe ones.

### G90. Online cost-model calibration

**Definition:** Continuously correcting the cost estimates used for planning, using real measurements.

**How it works:**
1. After each step, compare the estimated cost (time, memory, money) with the actual cost.
2. Update the cost model with exponential smoothing (new estimate = α × observed + (1 − α) × old) or regression on input sizes.
3. Track the error per algorithm and context.
4. The planner (G19, G24) uses the updated models.

**Glue use:** Plan selection improves automatically as the engine learns how each algorithm really behaves on your data and hardware.

**Guardrails:** Ignore outliers caused by incidents, and alert when estimates drift significantly.

### G91. Adaptive timeouts from latency percentiles

**Definition:** Setting each step's timeout from its observed latency distribution, instead of fixed guesses.

**How it works:**
1. Track each step's latency percentiles with streaming sketches (t-digest).
2. Timeout = a high percentile (for example p99.9) times a safety factor, within absolute minimum and maximum bounds.
3. Update it periodically.
4. Use different timeouts for different input-size buckets.

**Glue use:** Combined flows fail fast on truly stuck steps, without killing steps that are just slow on big inputs.

**Guardrails:** Absolute maximum timeouts always apply (G34).

### G92. Offline parameter search (grid, random, Bayesian optimization)

**Definition:** Finding good parameter settings by testing many configurations against a benchmark, before deployment.

**How it works:**
1. Define the search space (parameters and ranges) and an objective (quality, latency, cost, or a weighted mix).
2. **Grid search:** test every combination. **Random search:** sample combinations, which is often more efficient.
3. **Bayesian optimization:** fit a model of the objective (a Gaussian process or tree-based model) and choose the next configuration where improvement is most likely.
4. Pick the best configuration that meets all constraints (G25).

**Glue use:** Tunes the default parameters of reusable flow templates (G63) once, offline, with no runtime cost.

**Guardrails:** Tune on representative benchmarks, and validate on held-out data.

### G93. Decision trees learned from execution logs (CART)

**Definition:** Learning simple, readable "if-then" selection rules from past flow results.

**How it works:**
1. Collect past runs: context features (input size, language, scope size) and outcomes (which plan was used, success, cost).
2. A decision tree repeatedly splits the data on the feature that best separates good from bad outcomes (Gini impurity or variance reduction).
3. The tree becomes readable rules: "IF repo size > X AND language = Go THEN plan B".
4. Review the rules and promote them into the rule engine (G26) or decision tables (G27).

**Glue use:** Converts experience into explicit, reviewable selection rules. A tiny, cheap model, nothing like an LLM.

**Guardrails:** Rules learned from logs are reviewed before activation. Retrain periodically as conditions change.

### G94. Fallback ladders and graceful degradation

**Definition:** An ordered list of alternatives for each capability, from best to most basic, used automatically when better options fail or are too slow.

**How it works:**
1. For each capability, define ranked options: for example, filtered HNSW → brute force on the filtered set → keyword search → "no answer, with an explanation".
2. Each level declares its quality and cost.
3. On failure, timeout, open circuit breaker (G36) or budget pressure, move down a level.
4. Responses report which level was used.

**Glue use:** Combined flows keep working, at reduced quality, when parts fail, instead of failing entirely.

**Guardrails:** Degradation is always visible in results and metrics. Correctness-critical steps (verification, permission checks) never degrade.

## Layer 13: Testing the glue

### G95. Property-based testing of flows

**Definition:** Testing flows with many automatically generated inputs, checking that general properties always hold.

**How it works:**
1. Define properties: "running the flow twice gives no extra diff" (idempotency), "output stays within scope", "result count ≤ input count", "applying then reverting restores the original".
2. A generator creates many random valid inputs, including edge cases.
3. Run the flow on each, and check the properties.
4. On failure, shrinking finds the smallest input that still fails.

**Glue use:** Finds bugs in combinations that hand-written tests miss, especially at the boundaries between algorithms.

**Guardrails:** Run property tests in CI for every reusable template (G63).

### G96. Contract testing between steps

**Definition:** Verifying that each producer's actual output matches what its consumers expect, independently of full end-to-end runs.

**How it works:**
1. Consumers record their expectations of a producer's output (fields, types, conditions).
2. Producers are tested against all their consumers' recorded expectations.
3. A producer change that breaks a consumer's expectation fails before deployment.
4. This is the consumer-driven contract testing practice.

**Glue use:** With hundreds of algorithms and many combinations, contract tests catch incompatible changes early, without testing every combination end to end.

**Guardrails:** Every registry entry (G2) has contract tests for its declared outputs.

### G97. Fault injection (chaos testing)

**Definition:** Deliberately introducing failures to verify that flows recover correctly.

**How it works:**
1. Inject faults: kill workers, delay responses, return errors, corrupt messages, exhaust budgets, partition networks.
2. Run representative flows during the faults.
3. Check that recovery works: retries (G35), compensation (G38), resume (G37), no duplicate effects (G40).
4. Start in test environments, then carefully in production, with limits.

**Glue use:** Proves the reliability machinery actually works for real combinations, not just in theory.

**Guardrails:** Production fault injection needs approval, a limited blast radius and an instant stop switch.

### G98. Golden-flow regression testing

**Definition:** Running a fixed set of representative flows with known inputs, and comparing their results to approved outputs.

**How it works:**
1. Pick representative tasks covering the main combinations.
2. Record approved outputs (results, step sequences, key metrics).
3. After any change to algorithms, the planner, rules or the engine, re-run them and compare.
4. Review the differences, then approve new outputs or fix regressions.

**Glue use:** Ensures that improving one algorithm doesn't silently change how other combinations behave.

**Guardrails:** Unexplained differences block deployment.

### G99. Static plan linting

**Definition:** Automatically checking flow definitions and plans against best-practice rules before running them.

**How it works:**
1. Lint rules check things like: every loop has a maximum iteration count, every write step has an idempotency key, every fan-out has a concurrency limit, no lossy adapter feeds an exhaustive scope, and every branch point has a default.
2. Rules run on plans and templates (G63) at save time.
3. Violations are reported with the location and a suggested fix.

**Glue use:** Catches dangerous combinations immediately, whether they were written by hand or generated by the planner.

**Guardrails:** Errors (as opposed to warnings) block execution.

### G100. Termination proofs with ranking functions

**Definition:** Proving that a loop or repeated flow must finish, by showing that some measure strictly decreases each round and can't go below zero.

**How it works:**
1. Pick a ranking function: a value that's always ≥ 0, such as remaining matches, remaining budget or unprocessed items.
2. Show that each iteration strictly decreases it.
3. Since it can't decrease forever, the loop must end.
4. If no such measure exists, the loop relies on its budget (G34) to terminate.

**Glue use:** For repeated flows (G33), proves termination by design. For example, "each round fixes at least one remaining match, or stops".

**Guardrails:** Loops without a ranking function must have strict budgets, and are flagged by the linter (G99).

---

## Minimal core: what to build first

You don't need all 100 on day one. This core of 20 gives you composition of any combination, in any order, with repetition and scoped execution, without AI:

1. **Contracts and registry:** G1, G2, G5, G6.
2. **Plumbing:** G4 (adapters), G56 (CEL expressions), G57 (JSONPath bindings), G59 (canonical hashing).
3. **Composition:** G8 and G9 (DAG plus topological sort), G13 (behavior trees for fallbacks), G17 (composite flows).
4. **Automatic composition:** G21 (HTN methods encoding your recipes), G23 (type-directed plumbing), G28 (plan validation).
5. **Execution:** G33 (fixpoint loops), G34 (budgets), G37 (durable execution), G40 (idempotency).
6. **Scope:** G45 (scope narrowing).

Then add the rest in this order: safety (G48–G52, G99, G100), reliability (G35, G36, G38, G78), scale (G29–G32, G65–G73), distribution (G74–G81), state (G82–G88), and adaptivity (G89–G94).

Existing industry engines already implement large parts of this, so you can adopt them instead of building from scratch: Temporal for durable execution, Camunda for BPMN and DMN, Bazel's model for content-addressed incremental computation, and CEL for expressions. Your own work then becomes the registry, the contracts, the HTN methods and the scope rules: the parts specific to your 606 algorithms.