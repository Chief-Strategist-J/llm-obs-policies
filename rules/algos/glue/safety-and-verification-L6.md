
## Layer 6: Safety and verification

### G48. Invariant checking

**Definition:** Conditions that must hold at every step of every flow, checked continuously.

**How it works:**
1. Declare invariants: "scope never grows", "no write without a precondition hash", "budget never negative", "every write has lineage".
2. The executor checks them after each step.
3. A violation stops the flow immediately and triggers compensation (G38).

**Glue use:** Global safety rules hold no matter how algorithms are combined.

**Guardrails:** Invariants can't be disabled by individual flows.

### G49. Cycle and deadlock detection

**Definition:** Detecting circular dependencies and waits that would make a flow hang forever.

**How it works:**
1. **Cycles in a DAG:** DFS-based detection or Kahn's leftover nodes (G9).
2. **Deadlocks at runtime:** build a wait-for graph (step A waits for a resource held by B); a cycle means deadlock.
3. **Static analysis** of Petri net models (G12).
4. Resolve by aborting and compensating one step, then retrying with ordered resource acquisition.

**Glue use:** Automatically composed plans can't hang.

**Guardrails:** Run cycle checks at planning time and deadlock checks at runtime.

### G50. Model checking of flows (temporal logic)

**Definition:** Exhaustively verifying that a flow model satisfies properties such as "always eventually finishes" or "never writes before approval".

**How it works:**
1. Model the flow as a state machine (G10–G12).
2. Express properties in temporal logic (LTL or CTL): "every apply is preceded by a validation", "every started flow eventually ends".
3. A model checker explores every reachable state and either proves the property or returns a counterexample (an execution that breaks it).
4. Specification languages such as TLA+ are widely used in industry for this.

**Glue use:** For critical reusable flows (safe edits, migrations, deletions), it proves that no combination of events or failures breaks the safety rules.

**Guardrails:** Keep models small and abstract. Check the critical properties, not every detail.

### G51. Deterministic replay testing

**Definition:** Re-running a recorded flow with the same inputs and checking that it produces exactly the same decisions and outputs.

**How it works:**
1. Record the inputs, the recorded non-deterministic values (G37) and the outputs.
2. Replay against new versions of the algorithms or the engine.
3. Compare step by step, and report the first divergence.

**Glue use:** Lets you upgrade any algorithm and prove that existing combined flows still behave the same, or see exactly where they differ.

**Guardrails:** Treat any unexplained divergence as a failure.

### G52. Distributed tracing of flows (OpenTelemetry)

**Definition:** Recording every step of every flow as linked, timed spans, using the CNCF OpenTelemetry standard.

**How it works:**
1. Each flow is a trace, and each step a span with attributes: algorithm, version, parameters, input and output sizes, status.
2. Parent-child links reflect the composition (sub-flows, fan-out).
3. Spans are exported to a tracing backend for search, timing analysis and debugging.

**Glue use:** For any combination, you can see exactly what ran, in which order, how long each step took, and where it failed.

**Guardrails:** No sensitive data in span attributes. Record IDs and hashes instead.
