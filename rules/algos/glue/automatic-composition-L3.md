
## Layer 3: Automatic composition (the engine picks the combination)

This layer solves "I myself won't know how to combine them". You state the goal; these algorithms find the combination.

### G18. STRIPS / PDDL classical planning

**Definition:** Automatically finding a sequence of actions that turns a starting state into a goal state, where every action has preconditions and effects. PDDL is the standard language of the International Planning Competition.

**How it works:**
1. **State:** a set of facts ("files_listed", "matches_found", "edits_planned").
2. **Actions** (your algorithms): preconditions (facts that must hold) and effects (facts added or removed). These come straight from the contracts (G1, G5).
3. **Goal:** facts that must hold at the end ("edits_applied", "verified").
4. A planner searches for a sequence of actions where each one's preconditions are met by the state at that point.
5. Planners use heuristic search (G19) with automatically derived heuristics to find plans quickly.

**Glue use:** You declare the goal "matches_replaced AND verified", and the planner discovers: list → filter → search → plan edits → check overlaps → apply → verify. You never wrote that sequence.

**Guardrails:** Give actions accurate preconditions and effects. Wrong contracts produce wrong plans. Cap planning time.

### G19. A* search over plan space

**Definition:** Finding the cheapest plan by searching through partial plans, guided by an estimate of the remaining cost.

**How it works:**
1. Each search node is a state reached by a partial plan, with its cost so far, g.
2. A heuristic h estimates the remaining cost to the goal.
3. Always expand the node with the lowest g + h.
4. With an admissible heuristic (never overestimates), the first plan that reaches the goal is optimal.
5. Plan cost combines the algorithms' cost models: time, money, risk.

**Glue use:** When several combinations reach the goal, the engine picks the cheapest. Brute force is chosen for a tiny corpus, an index for a huge one.

**Guardrails:** Cap the number of expanded nodes. If no plan is found within the cap, report it instead of searching forever.

### G20. Backward chaining (goal regression)

**Definition:** Planning backward from the goal: find a step that produces the goal, then find steps producing that step's requirements, and so on.

**How it works:**
1. Start with the goal facts.
2. Find actions whose effects include a goal fact.
3. Their preconditions become new sub-goals.
4. Repeat until all sub-goals are satisfied by the current state.
5. Reverse the chain to get the execution order.

**Glue use:** Efficient when there are many algorithms but only a few relevant to the goal. Searching backward from "verified edits" skips every irrelevant algorithm.

**Guardrails:** Detect repeated sub-goals with memoization, to avoid infinite regress.

### G21. HTN planning (hierarchical task networks)

**Definition:** Planning by decomposing high-level tasks into subtasks using predefined "methods", like recipes, until only primitive actions remain.

**How it works:**
1. **Compound tasks:** "migrate API". **Primitive tasks:** actual algorithms.
2. **Methods:** each says how to decompose a compound task, under which conditions. "migrate API" → [find usages, generate codemod, test codemod, apply in batches, verify].
3. Several methods can exist for one task. The planner chooses by conditions, and backtracks on failure.
4. Decompose recursively until everything is primitive.
5. The result is a plan that follows known best practices.

**Glue use:** This is the most practical planner for your case. You encode industry recipes once as methods, such as the "How the entries fit together" sections at the end of each reference. The planner then adapts them to each task automatically.

**Guardrails:** Methods are reviewed like code. Cap the decomposition depth.

### G22. GOAP (goal-oriented action planning)

**Definition:** A lightweight planner, widely used in game AI, that chains actions by preconditions, effects and costs to reach a goal, re-planning quickly when the situation changes.

**How it works:**
1. The world state is a set of key-value facts.
2. Actions have preconditions, effects and costs.
3. A* (G19) searches over states, usually backward from the goal.
4. The plan is executed step by step. If a step fails or the world changes, re-plan from the current state.

**Glue use:** A good fit when flows must adapt at runtime. For example, an index turns out to be stale, so the engine re-plans to "rebuild, then search".

**Guardrails:** Limit how often re-planning can happen, so the flow doesn't oscillate.

### G23. Type-directed composition (graph search over types)

**Definition:** Finding a chain of algorithms and adapters that converts an available input type into a required output type.

**How it works:**
1. Build a graph: nodes are data types; each algorithm or adapter is an edge from its input type to its output type, with a cost.
2. To get from type A to type Z, run a shortest-path search (Dijkstra or A*).
3. The path is the composed chain.
4. For algorithms with several inputs, use hypergraph search (AND-OR search).

**Glue use:** Automatic "plumbing". To turn "natural-language concept" into "byte-range edits", the engine finds: embed → vector search → chunk-to-file mapping → structural search → edit list.

**Guardrails:** Prefer lossless paths. Lossy adapters (G4) carry a cost penalty.

### G24. Cost-based plan optimization (dynamic programming, Selinger-style)

**Definition:** Choosing the cheapest way to execute a plan by comparing alternative orders and implementations with cost models, as database query optimizers do.

**How it works:**
1. For each step, list its alternative implementations (brute force, IVF or HNSW for search, for example).
2. Estimate costs from statistics: input sizes, selectivity, hardware.
3. Dynamic programming builds the best sub-plans for subsets of steps and combines them into the best full plan.
4. Reorder commutative steps, such as running the most selective filter first (Code ref #71).
5. Re-optimize when the statistics change.

**Glue use:** The same goal gets different combinations depending on data size and latency budget, chosen automatically.

**Guardrails:** Log the chosen plan and its estimated versus actual cost. Large estimation errors mean the cost models need updating.

### G25. Constraint satisfaction (CSP) for parameters and configuration

**Definition:** Choosing parameter values and component options that satisfy every constraint at once.

**How it works:**
1. **Variables:** for example k, ef, nprobe, batch size, which index type.
2. **Domains:** the allowed values for each.
3. **Constraints:** latency < 200 ms, memory < 8 GB, recall ≥ 0.95, "if binary quantization then re-scoring = on".
4. **Search:** backtracking with constraint propagation (arc consistency, AC-3) removes impossible values early.
5. **Optimization variant:** among valid settings, pick the cheapest (branch and bound).

**Glue use:** Once the planner picks the algorithms, CSP picks their settings so the combined flow meets every budget and rule.

**Guardrails:** If no valid configuration exists, report which constraints conflict (a minimal conflict set) instead of silently relaxing them.

### G26. Rule engines (Rete) for algorithm selection

**Definition:** Declarative "if conditions then choose or do X" rules, evaluated efficiently by the Rete algorithm.

**How it works:**
1. Rules: "IF corpus > 1M AND dims > 100 THEN use HNSW", "IF language unknown THEN use text edit plus review".
2. Rete compiles all the rules into a network that remembers partial matches.
3. When facts change, only the affected rules are re-evaluated.
4. Conflict resolution decides which matching rule fires first (by priority, specificity or recency).

**Glue use:** Encodes your expert selection knowledge (the "when to use what" advice from all three references) as rules the engine applies automatically.

**Guardrails:** Test the rules with fixtures. Detect conflicting rules (two rules recommending incompatible choices).

### G27. Decision tables (DMN, OMG standard)

**Definition:** Tabular decision logic, where each row is an input-condition combination with an output. Standardized by OMG as DMN.

**How it works:**
1. Columns: input conditions (data size, read or write, latency need) and outputs (chosen algorithm, parameters).
2. Rows: specific combinations.
3. A hit policy decides what happens when several rows match: first match, unique, priority, or collect all.
4. Tables can be checked for gaps (missing combinations) and overlaps.

**Glue use:** A readable, reviewable alternative to code for selection logic, which non-programmers can audit.

**Guardrails:** Run completeness checks, so every input combination has a defined outcome.

### G28. Plan validation (VAL-style)

**Definition:** Independently checking that a generated plan is valid before running it.

**How it works:**
1. Simulate the plan step by step against the declared contracts (G1, G5).
2. Check that every precondition holds when its step starts.
3. Check that the goal holds at the end.
4. Check resource and budget constraints.
5. Report the first failing step and why.

**Glue use:** A safety net between automatic planning and execution: a bad plan is caught before any step runs.

**Guardrails:** Plans that include write or destructive steps always go through validation, plus human approval where required.

---