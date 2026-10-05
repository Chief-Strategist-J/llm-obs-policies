
## Layer 2: Composition models (the shapes flows can take)

### G7. Pipes and filters

**Definition:** The simplest composition: a linear chain where each step's output is the next step's input.

**How it works:**
1. Steps (filters) are connected by pipes (data channels).
2. Each filter reads input, transforms it and writes output.
3. Filters are independent and replaceable, as long as the contracts match.
4. Streaming variants process items one at a time; batch variants process whole collections.

**Glue use:** For example: list files (Code ref #7) → ignore filter (Code ref #3) → binary filter (Code ref #5) → multi-literal search (Code ref #24) → dedupe → report.

**Guardrails:** Bounded buffers between filters (Code ref #168) stop one fast step from flooding the next.

### G8. DAG workflows

**Definition:** Representing a flow as a directed acyclic graph: steps are nodes, and edges mean "this step needs that step's output".

**How it works:**
1. Each node is an algorithm invocation with its parameters.
2. An edge A → B means B consumes A's output, or must run after A.
3. Nodes with no dependency between them can run in parallel.
4. "Acyclic" means no cycles, so the flow always terminates. Loops are handled separately (G14, G33).
5. Execution order comes from topological sorting (G9).

**Glue use:** The standard shape for most combined tasks. Example: vector search and BM25 search run in parallel, then fusion, then rerank, then graph expansion.

**Guardrails:** Run cycle detection (G49) on every DAG before execution.

### G9. Topological sort (Kahn's algorithm)

**Definition:** Ordering DAG steps so every step comes after all of its dependencies.

**How it works:**
1. Count each node's unfinished dependencies (its in-degree).
2. Put all nodes with zero dependencies into a ready queue.
3. Take one, run it (or output it), and decrease the dependency count of every node that depends on it. Add any that reach zero to the queue.
4. Repeat until the queue is empty.
5. If nodes remain unprocessed, there's a cycle, which is an error.

**Glue use:** Converts any composed DAG into a valid execution order. The nodes in the ready queue at the same moment can run in parallel.

**Guardrails:** Break ties deterministically (by node ID), so the same plan always runs in the same order. That makes runs reproducible.

### G10. Finite state machines (FSM)

**Definition:** A model where a process is always in exactly one state, and defined events move it to defined next states.

**How it works:**
1. Define the states ("searching", "planning", "applying", "verifying", "done", "failed").
2. Define the transitions: (state, event, condition) → next state, plus an action to run.
3. Only listed transitions are allowed. Anything else is rejected.
4. Final states end the process.
5. The current state is saved durably, so the process can resume (G37).

**Glue use:** Controls the high-level lifecycle of a task. The Scout → Planner → Editor → Verifier roles from the code reference map directly onto states. For example, "verification failed" moves back to "planning", up to N times.

**Guardrails:** Every state has a maximum time and a failure transition, so nothing gets stuck.

### G11. Statecharts (hierarchical state machines, W3C SCXML)

**Definition:** State machines with nested states, parallel regions and history. They're standardized for execution as W3C SCXML.

**How it works:**
1. **Hierarchy:** a state can contain sub-states. The "applying" state contains "writing" and "checking", for example.
2. **Parallel regions:** independent sub-machines run at the same time inside one state.
3. **History:** re-entering a state can resume its last sub-state.
4. Transitions on a parent state apply to all its children. A single "cancel" covers everything inside.
5. Guards, entry and exit actions, and timers are built in.

**Glue use:** Complex flows stay readable. A parent state "migration" contains parallel regions "backfill" and "live sync", with one shared "abort" transition.

**Guardrails:** Keep nesting shallow (3–4 levels at most) and test every transition.

### G12. Petri nets (ISO/IEC 15909)

**Definition:** A formal model of concurrent processes, with places, transitions and tokens. It's well suited to synchronization and parallel joins.

**How it works:**
1. **Places** hold tokens (resources or completed conditions). **Transitions** are steps.
2. A transition can fire when all its input places have enough tokens. Firing consumes those tokens and produces tokens in its output places.
3. Parallel split: one transition produces tokens in several places. Join: one transition needs tokens from several places.
4. Analysis can prove properties: no deadlock, bounded resources (boundedness), reachability of the final state.
5. Most workflow engines' semantics are formally based on Petri nets.

**Glue use:** Models "wait until all 5 shard searches are done, but at most 3 run at once". Resource limits become tokens.

**Guardrails:** Run the deadlock and boundedness analysis on complex flows before deployment.

### G13. Behavior trees

**Definition:** A tree of control nodes and actions that decides what to do next on every tick. Widely used in robotics and games for modular, reactive control.

**How it works:**
1. **Leaves** are actions (run an algorithm) or conditions (check something).
2. **Sequence node:** runs children in order and fails as soon as one fails.
3. **Fallback (selector) node:** tries children in order until one succeeds. That gives "try plan A, else B, else C".
4. **Parallel node:** runs children together, with a success policy (all must succeed, or any one).
5. **Decorators:** retry N times, timeout, invert, repeat until success.
6. Each tick evaluates the tree from the root, so behavior adapts to the current state.

**Glue use:** Ideal for "try the cheap algorithm, fall back to the expensive one". For example: exact search → fuzzy search (Code ref #23) → semantic search (Vector ref #108), stopping at the first success.

**Guardrails:** Every repeat or retry decorator has a maximum count.

### G14. Dataflow and Kahn process networks

**Definition:** Composition where steps run whenever their input data is available, connected by FIFO channels.

**How it works:**
1. Each process reads from input channels and writes to output channels.
2. A process blocks until data arrives (Kahn semantics), so results are deterministic regardless of timing.
3. Cycles are allowed, which gives iterative streaming flows.
4. Channel capacity limits provide backpressure.

**Glue use:** Continuous flows such as ingest → chunk → embed → index (Vector ref #125–131) running indefinitely, with each stage at its own speed.

**Guardrails:** Bounded channels everywhere, and monitoring of queue depth.

### G15. BPMN 2.0 (OMG standard)

**Definition:** The Object Management Group's standard notation and execution semantics for business and technical workflows.

**How it works:**
1. Elements: tasks, events (start, end, timer, message, error) and gateways.
2. **Gateways:** exclusive (pick one branch), parallel (all branches), inclusive (one or more), event-based (whichever event comes first).
3. Subprocesses, loops, multi-instance (run a task for each item in a list), and compensation (undo).
4. Engines (such as Camunda and Flowable) execute BPMN models directly.

**Glue use:** A standard, tool-supported way to define and visualize flows that combine algorithms. Human approval steps (the G5 guardrails in the earlier references) fit in naturally.

**Guardrails:** Version the models, and never edit a running instance's model in place.

### G16. Workflow control-flow patterns (van der Aalst catalog)

**Definition:** The established catalog of reusable control-flow building blocks for any workflow system.

**How it works:**
1. **Basic:** sequence, parallel split, synchronization (join), exclusive choice, simple merge.
2. **Advanced branching:** multi-choice, structured synchronizing merge, discriminator (continue after the first of N finishes).
3. **Multi-instance:** run a step N times in parallel, with N known at design time, at runtime, or discovered while running.
4. **Iteration:** structured loops, arbitrary cycles, recursion.
5. **Cancellation:** cancel a task, a region or the whole case.

**Glue use:** A checklist that guarantees your engine can express any combination you'll need. If an engine supports these patterns, it can express your flows.

**Guardrails:** Check that your chosen engine supports the patterns you use, especially cancellation and multi-instance.

### G17. Composite pattern (flows as building blocks)

**Definition:** Treating a whole flow as a single step with its own contract, so flows can be nested inside other flows.

**How it works:**
1. A flow declares its overall inputs, outputs, pre/postconditions and cost, just like one algorithm (G1).
2. It's registered in the registry (G2) as a reusable unit.
3. Larger flows use it as one node.
4. Internally, it still runs step by step.

**Glue use:** Build once, reuse everywhere. "Safe file edit" (Code ref #157–165) becomes one block. "Hybrid retrieve" (Vector ref #86–94) becomes one block. Bigger tasks combine blocks, not 40 individual algorithms.

**Guardrails:** A composite's contract must be tested against its internal behavior, using fixtures.

---