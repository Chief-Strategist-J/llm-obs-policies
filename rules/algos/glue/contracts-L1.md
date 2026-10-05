## How the glue fits together

| Layer | Question it answers | Entries |
|---|---|---|
| **1. Contracts** | What does each algorithm take in, produce, require and guarantee? | G1–G6 |
| **2. Composition models** | In what shapes can algorithms be connected (sequence, parallel, loop, branch)? | G7–G17 |
| **3. Automatic composition** | Which algorithms, in which order, reach this goal? | G18–G28 |
| **4. Execution control** | How does the plan actually run: scheduling, loops, retries, recovery? | G29–G42 |
| **5. Scope and data flow** | What data does each step see and pass on, and how far can it reach? | G43–G47 |
| **6. Safety and verification** | How do we prove the combined flow is correct, bounded and safe? | G48–G52 |

The key idea: **if every algorithm declares a precise contract (Layer 1), then Layer 3 can combine them automatically, like puzzle pieces whose shapes must fit.** That's what makes "any combination, any order" possible without you designing each flow by hand.

The format below matches the earlier references, with "Glue use" in place of "Agent use".

---

## Layer 1: Contracts (making algorithms pluggable)

### G1. Typed interface contract

**Definition:** A formal description of each algorithm's inputs, outputs, parameters and behavior, so that a machine can decide what can connect to what.

**How it works:**
1. Each algorithm declares its input types (for example "list of file paths", "vector set", "graph snapshot") and output types ("ranked matches with byte ranges").
2. It declares its parameters, with types, ranges and defaults (k, ef, depth, threshold).
3. It declares its properties: deterministic or not, idempotent or not, side effects (read-only, writes), and cost estimate (time and memory as a function of input size).
4. Contracts are written in a schema language (JSON Schema, Protocol Buffers or Avro), so they can be checked automatically.
5. Two algorithms can connect when the first one's output type is compatible with the second one's input type.

**Glue use:** This is the foundation of everything. Code ref #24 (Aho-Corasick) outputs "matches with offsets"; Code ref #121 (overlap detection) inputs "edits with ranges". With contracts, the engine knows an adapter (G4) is needed between them.

**Guardrails:** No algorithm enters the registry without a complete contract. Contracts are versioned (G3).

### G2. Capability registry (service catalog)

**Definition:** A searchable catalog of every available algorithm, indexed by what it consumes, produces and can do.

**How it works:**
1. Each entry stores: ID, version, contract (G1), capability tags ("search.substring", "graph.traverse", "edit.apply"), cost model and scope constraints.
2. Indexes: by output type (what produces X?), by input type (what consumes X?), by capability tag.
3. Queries like "all algorithms producing ranked candidates from a text query, read-only, under 100 ms" return the matching entries.
4. The planner (Layer 3) reads from this registry instead of a hard-coded list.

**Glue use:** All 606 algorithms from the three references become registry entries. Adding a new algorithm makes it instantly available to every future plan, with no rewiring.

**Guardrails:** Registry entries are reviewed before activation. Disabled or deprecated entries are kept but never planned.

### G3. Semantic versioning and compatibility checking

**Definition:** Versioning each algorithm's contract so that changes are classified as compatible or breaking (Semantic Versioning 2.0.0 specification).

**How it works:**
1. Version = MAJOR.MINOR.PATCH.
2. PATCH: internal fix, same contract. MINOR: added optional input or output fields (backward compatible). MAJOR: a breaking contract change.
3. Schema compatibility rules check this automatically: a new optional field is compatible, a removed field or changed type is breaking (Avro and Protobuf schema registries do exactly this).
4. Saved plans pin the major versions they were built with.

**Glue use:** You can upgrade one algorithm without silently breaking every flow that uses it. Plans using a changed major version are flagged for re-planning.

**Guardrails:** A MAJOR change never auto-applies to existing plans.

### G4. Adapter (type conversion) pattern

**Definition:** Small converters that turn one algorithm's output into another algorithm's input format.

**How it works:**
1. Register adapters as algorithms too, with contracts: "line numbers → byte offsets", "match list → edit list", "graph nodes → text chunks", "ranked list → set".
2. When two algorithms don't connect directly, the planner looks for an adapter (or a chain of adapters) between their types.
3. Adapters are pure functions: deterministic, with no side effects.
4. Lossy adapters (ranked list → top-k set) declare what they lose.

**Glue use:** This is what makes "any combination" practical. Code ref #14 (line numbers) to Code ref #117 (text edits) needs a line-index adapter (Code ref #142).

**Guardrails:** Lossy adapters are allowed only where the plan's goal accepts the loss. For example, never truncate a list that feeds an exhaustive edit scope.

### G5. Pre- and postconditions (design by contract)

**Definition:** Declared conditions that must hold before an algorithm runs and conditions it guarantees after.

**How it works:**
1. **Precondition:** what must be true of the input ("input is sorted", "file hash matches", "graph has no cycles").
2. **Postcondition:** what is guaranteed about the output ("results are deduplicated", "no overlapping edits", "count equals expected").
3. **Invariants:** what stays true throughout ("scope never grows").
4. The executor checks preconditions before each step and postconditions after it. A failure stops or reroutes the flow.
5. The planner also uses them: postconditions of step A can satisfy preconditions of step B (G18).

**Glue use:** Galloping intersection (Code ref #66) requires sorted input; a sort step guarantees "sorted". The planner automatically inserts the sort when the previous output isn't declared sorted.

**Guardrails:** Conditions are checked at runtime, not just assumed. Expensive checks can be sampled, but checks on write steps are always full.

### G6. Data schemas and validation

**Definition:** Machine-checkable descriptions of the data passed between steps, validated at every boundary.

**How it works:**
1. Define each data type with JSON Schema (json-schema.org), Avro or Protobuf: required fields, types, ranges, formats.
2. Validate each step's output before passing it on.
3. Reject or quarantine invalid data and record why.
4. Schemas live in the registry (G2) and are versioned (G3).

**Glue use:** A step that produces malformed output fails at its own boundary, not three steps later in a confusing way.

**Guardrails:** Validation can't be turned off for write steps.

---


---

## How it works end to end, with no AI involved

**Example task:** "Rename `getUser` to `fetchUser` in repos A and B, but only under `src/`."

1. **Goal and scope** become formal: the goal is `renamed(getUser→fetchUser) ∧ verified`, and the scope is repos {A, B} ∧ path src/** (G45).
2. **HTN planner** (G21) picks the "rename symbol" method. Its subtasks are: find references, plan edits, apply, verify.
3. **Rules and decision tables** (G26, G27) choose the implementations: the LSP rename is available for TypeScript, so use it (Code ref #90). For other files, use structural search (Code ref #81).
4. **Type-directed composition** (G23) inserts adapters, such as LSP positions → byte ranges (Code ref #119).
5. **CSP** (G25) sets the batch size and concurrency within the budgets.
6. **Plan validation** (G28) proves every precondition is satisfied.
7. **Executor:** scatter per repo (G32, G47) → topological order within each repo (G9) → idempotent writes (G40) → durable checkpoints (G37).
8. **Fixpoint loop** (G33): search for `getUser` again. If matches remain, re-plan for those only (G22), with at most 3 iterations (G34).
9. **On failure:** compensate (G38), and record the trace (G52) and lineage (G46).

Swap the goal for "keep the vector index fresh" or "answer a question from the knowledge graph", and the same six layers pick entirely different algorithms from the registry. That's the "any combination, any order, repeatable, scoped" property you asked for.

**Where AI is optional:** only to turn a natural-language request into the formal goal and scope in step 1. If you use fixed templates or forms for goals, the whole system runs with zero tokens.