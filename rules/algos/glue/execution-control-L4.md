
## Layer 4: Execution control

### G29. Work queue and scheduler

**Definition:** The runtime that dispatches ready steps to workers, respecting dependencies, priorities and resource limits.

**How it works:**
1. Ready steps (those with all dependencies done, G9) enter a queue.
2. Workers take steps by priority (Code ref #173).
3. Resource limits (CPU, memory, API quotas) decide how many run at once.
4. Completed steps release the steps that depend on them.

**Glue use:** Runs any composed plan at full parallelism automatically.

**Guardrails:** Per-resource concurrency limits. Never let one flow starve all others.

### G30. List scheduling and critical path

**Definition:** Ordering parallel steps to minimize total completion time, prioritizing steps on the longest dependency chain.

**How it works:**
1. Estimate each step's duration.
2. Compute the critical path: the longest chain from start to end.
3. Give steps on the critical path the highest priority.
4. Greedy list scheduling assigns the highest-priority ready step to the next free worker.

**Glue use:** Big flows finish sooner, because bottleneck steps start first.

**Guardrails:** Update the duration estimates from real runs.

### G31. Conditional branching with guards

**Definition:** Choosing the next step based on data or results at runtime.

**How it works:**
1. A guard is a boolean condition on available data ("match count > 0", "recall < target").
2. Exclusive branch: take the first branch whose guard is true. Inclusive: take all branches whose guards are true.
3. Always define a default branch.
4. Guards must be side-effect free and deterministic.

**Glue use:** "If exact search found nothing, try fuzzy. If more than 1,000 results, narrow the scope. Else continue."

**Guardrails:** Every decision point has a default branch, so there are no undefined paths.

### G32. Scatter-gather (fan-out / fan-in, multi-instance)

**Definition:** Running the same step on many items in parallel, then combining their results.

**How it works:**
1. **Scatter:** split the input (files, repos, shards, queries) into items.
2. Run one instance per item, in parallel, up to a concurrency limit.
3. **Gather:** combine results with a merge function (concatenate, k-way merge, sum, union).
4. A completion policy: wait for all, wait for N, or continue after a timeout with partial results flagged.

**Glue use:** "Apply this whole sub-flow to each of 400 repos" becomes one node in the plan.

**Guardrails:** Partial results are always marked as partial, and failures are listed per item.

### G33. Iteration until a fixpoint

**Definition:** Repeating a sub-flow until its output stops changing, or a condition is met.

**How it works:**
1. Run the sub-flow.
2. Compare the new result with the previous one (by hash or by a delta measure).
3. If unchanged, or if the stop condition is true ("zero remaining matches", "recall ≥ target"), stop.
4. Otherwise, feed the result back in and repeat.
5. Semi-naive iteration processes only what changed since the last round (KG ref #89).

**Glue use:** This is your "repeated flow". For example: search → edit → verify → search again until zero old matches remain. Or retrieve → expand → retrieve again until no new relevant entities appear.

**Guardrails:** Always set a maximum iteration count and a time budget (G34). Detect oscillation (results alternating between two states).

### G34. Budgets and bounded execution

**Definition:** Hard limits on iterations, time, cost and resources for every flow and sub-flow.

**How it works:**
1. Each flow gets budgets: maximum steps, maximum wall-clock time, maximum money or API calls, maximum items touched.
2. Every step deducts its usage from the budget.
3. When a budget runs out, stop cleanly: save state, report partial results, explain which budget ran out.
4. Child flows get portions of their parent's budget.

**Glue use:** Guarantees any combination, however complex or repeated, terminates within known limits.

**Guardrails:** No flow runs without budgets. Defaults apply when none are set.

### G35. Retry with exponential backoff and jitter

**Definition:** Repeating failed steps with growing, randomized delays.

**How it works:**
1. Classify errors as retryable (timeout, rate limit) or not (validation error, permission denied).
2. Delay = base × 2^attempt, plus random jitter, capped at a maximum.
3. Stop after N attempts and escalate.

**Glue use:** Makes long combined flows resilient to temporary failures in any single step.

**Guardrails:** Retry only idempotent steps (G40). Never retry non-retryable errors.

### G36. Circuit breaker

**Definition:** Temporarily stopping calls to a failing component, to protect the rest of the flow.

**How it works:**
1. **Closed:** normal operation, counting failures.
2. **Open:** after too many failures, reject calls immediately for a cool-down period.
3. **Half-open:** allow a few trial calls. Close on success, re-open on failure.

**Glue use:** One failing algorithm or service can't stall or overload every flow that depends on it. Flows reroute through fallbacks (G13) instead.

**Guardrails:** Log every state change, and alert when breakers stay open.

### G37. Durable execution (checkpointing, event-sourced replay)

**Definition:** Recording each completed step durably, so a flow resumes exactly where it stopped after a crash.

**How it works:**
1. Each step's start, result and end are appended to an event log.
2. After a crash, the engine replays the log to rebuild the flow's state, without re-executing completed steps (their results come from the log).
3. Execution continues from the first unfinished step.
4. Flow code must be deterministic, so that replay reproduces the same decisions.

**Glue use:** Long, multi-hour combined flows (bulk migrations, re-embeddings, KG backfills) survive restarts and deployments. This is the model Temporal-style engines use.

**Guardrails:** Non-deterministic operations (time, random values, external calls) must be recorded as events, never recomputed during replay.

### G38. Saga with compensation

**Definition:** Undoing completed steps in reverse order when a later step fails, for flows that can't use a single transaction.

**How it works:**
1. Each step with side effects has a compensating step (create ↔ delete, apply edit ↔ revert edit, publish ↔ deprecate).
2. Run the steps forward, recording each completion.
3. On failure, run the compensations of the completed steps in reverse order.
4. Compensations must be idempotent (G40).

**Glue use:** Any combination that writes in several places stays recoverable.

**Guardrails:** Steps that can't be undone are marked irreversible, placed as late as possible in the flow, and require approval.

### G39. Memoization and content-addressed caching

**Definition:** Reusing a step's result when it's called again with exactly the same inputs.

**How it works:**
1. Key = hash(algorithm ID + version + parameters + input content hashes).
2. Before running a step, look up the key. On a hit, reuse the result.
3. On a miss, run the step and store the result under the key.
4. Any change in algorithm version, parameters or input changes the key, so results can't go stale.

**Glue use:** Repeated and overlapping flows become cheap. The 30 steps shared between two tasks run once. This is how build systems like Bazel avoid redundant work.

**Guardrails:** Only cache deterministic steps. Exclude secrets and access-restricted data from shared caches.

### G40. Idempotency keys

**Definition:** Unique keys that make repeated execution of a step have no extra effect.

**How it works:**
1. Each side-effecting step gets a key: (flow ID, step ID, input hash).
2. Before acting, check whether that key was already applied. If so, return the stored result.
3. Otherwise act, and record the key with its result atomically.

**Glue use:** Retries, replays and resumed flows never double-apply anything.

**Guardrails:** Every write step must have an idempotency key.

### G41. Incremental recomputation (dirty propagation)

**Definition:** When an input changes, recomputing only the steps that depend on it, not the whole flow.

**How it works:**
1. Keep the dependency graph of steps and data (from the DAG and lineage, G46).
2. When an input changes, mark it dirty, and propagate "dirty" to everything downstream.
3. Re-run only the dirty steps, in topological order (G9).
4. Early cutoff: if a re-run step produces the same output as before (same hash), stop propagating past it.

**Glue use:** When one file changes, a long combined flow updates in seconds instead of re-running everything. This is the model used by Bazel, the Salsa framework and spreadsheet engines.

**Guardrails:** The dependency tracking must be complete. A missed dependency produces stale results.

### G42. Event-driven triggering (publish/subscribe, CloudEvents)

**Definition:** Starting flows or steps automatically when events occur.

**How it works:**
1. Producers publish events ("file changed", "index rebuilt", "verification failed") in a standard envelope (CloudEvents, a CNCF specification).
2. Subscriptions match events by type and attributes.
3. Matching events start flows or resume waiting steps.
4. Events are durable and replayable.

**Glue use:** Connects flows together without hard-wiring. "When the code index updates, re-run the affected search flows" is just one subscription.

**Guardrails:** Detect trigger loops (A triggers B, which triggers A) with event lineage and loop limits.

---
