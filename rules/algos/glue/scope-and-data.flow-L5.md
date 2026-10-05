
## Layer 5: Scope and data flow

### G43. Blackboard pattern (shared context)

**Definition:** A shared, structured workspace where steps read inputs and write results, coordinated by a controller.

**How it works:**
1. The blackboard holds the current facts: scope, intermediate results, status, budgets.
2. Each step declares which keys it reads and which it writes.
3. The controller picks the next step whose required keys are available (similar to planning preconditions, G18).
4. Writes are versioned, so changes can be traced.

**Glue use:** Lets very different algorithms (search, graph, vector, edit) cooperate on one task without knowing about each other.

**Guardrails:** Steps can write only to their declared keys. Unexpected writes are rejected.

### G44. Lexical scoping (nested environments)

**Definition:** Each flow and sub-flow gets its own environment of variables, which inherits from its parent but can't change the parent's values.

**How it works:**
1. An environment maps names to values (scope, parameters, intermediate results).
2. A child flow gets a new environment linked to its parent's.
3. Lookups search the child first, then the parent.
4. Writes go to the child only. Results return to the parent explicitly, through declared outputs.

**Glue use:** Sub-flows reused in many places (G17) can't accidentally interfere with each other's data, even when they run in parallel or repeatedly.

**Guardrails:** No global mutable state. Everything flows through declared inputs and outputs.

### G45. Scope expressions and predicate narrowing

**Definition:** A formal description of what a flow may touch (which repos, paths, tenants, entity types, time range), which can only stay the same or get narrower as it passes down.

**How it works:**
1. Scope is a predicate, such as repo ∈ {A, B} AND path matches src/** AND tenant = X.
2. Each step receives the scope and must stay within it.
3. A child's scope = the parent's scope AND the child's own restriction (intersection). It can never widen.
4. Steps check targets against the scope before acting (G1 guardrails from the earlier references).
5. Represented efficiently as bitmaps or glob sets (Code ref #4, #64).

**Glue use:** Guarantees "specific scope" across any combination, however deep: no step anywhere can touch something outside the original scope.

**Guardrails:** Scope checks are enforced by the executor, not left to each algorithm. Out-of-scope access fails the step.

### G46. Data lineage tracking

**Definition:** Recording which steps, inputs and versions produced every piece of data.

**How it works:**
1. Each output records: the step ID and version, parameters, input IDs and hashes, and the time.
2. Following the links backward shows how a result was produced. Following them forward shows everything a given input affected.
3. Standard models: W3C PROV for provenance, OpenLineage for data pipelines.

**Glue use:** Explains any result of a complex combined flow, and powers incremental recomputation (G41) and targeted rollback.

**Guardrails:** Lineage is recorded automatically by the executor, not by each algorithm.

### G47. Partitioning work by scope

**Definition:** Splitting the scope into independent partitions that can be processed separately and safely in parallel.

**How it works:**
1. Choose a partition key: repo, directory, owner, shard, tenant.
2. Partitions must not overlap, so that no two workers touch the same item.
3. Each partition runs the same sub-flow (G32).
4. Results are combined, and per-partition status is tracked.

**Glue use:** Scales any flow to large scopes with no conflicts between workers.

**Guardrails:** Verify partitions are disjoint and complete: their union equals the full scope, and no item is in two partitions.

---
