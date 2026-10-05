# Part 7: Graphs in systems (#301–320)

Same format and the same contract (roles; rules GR1–GR8; guardrails GX1–GX5). This is the final part.

## G1. Scheduling and build systems

### 301. Register allocation by graph coloring (Chaitin-Briggs)

**Definition:** Assigning program variables to a limited number of CPU registers by coloring an interference graph, the classic compiler use of graph coloring.

**How it works:**
1. Compute liveness: where each variable's value is still needed (dataflow, C#96).
2. Build the interference graph: one vertex per variable, an edge between two variables live at the same time (they can't share a register).
3. **Simplify:** repeatedly remove vertices with fewer than k neighbors (k = number of registers), pushing them on a stack. Such vertices can always be colored later.
4. **Spill:** if every remaining vertex has ≥ k neighbors, pick one to store in memory (by spill cost heuristics). Briggs' optimistic coloring pushes it anyway and only spills if no color remains when popping.
5. **Select:** pop vertices and give each a color (register) not used by its neighbors.
6. **Coalescing:** merge vertices joined by copy instructions, when safe (conservative tests by Briggs or George), to remove moves.

**Complexity:** About O(n + m) per round, with a few rounds when spilling.

**Agent use:**
- **Role:** Optimizer.
- **How:** Beyond compilers, the same pattern assigns limited shared resources to things that overlap in time: connection pool slots, license seats, meeting rooms, GPU slots for overlapping jobs.
- **Rules:** Use interval-based coloring when the conflicts come from time intervals (interval graphs color optimally by a greedy sweep).
- **Guardrails:** Verify the coloring has no conflicts (GR6).

### 302. Critical path method (CPM) and PERT

**Definition:** Finding the longest chain of dependent tasks in a project DAG, which determines the minimum total duration, and computing each task's slack.

**How it works:**
1. Build a DAG: vertices are tasks with durations, edges are "must finish before".
2. **Forward pass** in topological order (#20): earliest start = max over predecessors of (their earliest start + duration).
3. **Backward pass** in reverse order: latest start = min over successors of (their latest start) − duration.
4. **Slack** = latest start − earliest start. Tasks with zero slack form the critical path.
5. **PERT:** durations become distributions (optimistic, most likely, pessimistic estimates). Estimate the completion time distribution, or simulate it with Monte Carlo for better accuracy.

**Complexity:** O(n + m).

**Agent use:**
- **Role:** Optimizer and Analyst.
- **How:** Bulk migrations, campaigns and multi-step plans (glue G30): shows which steps determine the completion time and where delays don't matter.
- **Rules:** Update durations from measured actuals as work proceeds.
- **Guardrails:** Single-number estimates hide risk. Present the critical path with uncertainty ranges.

### 303. Coffman-Graham scheduling

**Definition:** Scheduling unit-time tasks with dependencies on a fixed number of processors (or arranging a DAG into layers of bounded width), using a lexicographic labeling.

**How it works:**
1. Remove transitive edges (#58).
2. **Labeling:** give labels 1, 2, … to tasks in order. At each step, among tasks whose successors are all labeled, choose the one whose list of successor labels (sorted in decreasing order) is lexicographically smallest.
3. **Scheduling:** fill processor slots in time order, always picking the ready task with the highest label.
4. Optimal for two processors. A good approximation for more (within 2 − 2/w of optimal).
5. Also used to assign layers of bounded width in hierarchical drawings (#316).

**Complexity:** About O(n² ) straightforwardly, faster with careful implementation.

**Agent use:**
- **Role:** Optimizer.
- **How:** Schedules dependent jobs onto a fixed number of workers, with good theoretical guarantees.
- **Rules:** Use for unit or near-unit task times. Use HEFT (#304) for varied durations and machines.
- **Guardrails:** None specific.

### 304. HEFT (heterogeneous earliest finish time)

**Definition:** A list-scheduling algorithm for assigning dependent tasks to machines of different speeds, minimizing the total completion time.

**How it works:**
1. For each task, compute its average cost across machines, and the average communication costs of its edges.
2. **Upward rank:** rank(t) = average cost(t) + max over successors s of (communication(t, s) + rank(s)). This is the length of the longest path from t to the end.
3. Sort the tasks by decreasing rank (it respects dependencies).
4. For each task in that order, assign it to the machine where it finishes earliest, considering data transfers and idle gaps (insertion-based: a task can fill an earlier gap if it fits).
5. Variants handle uncertainty and energy limits.

**Complexity:** O(n² × p) for n tasks and p machines.

**Agent use:**
- **Role:** Optimizer.
- **How:** Placing workflow steps (glue engine plans, G29) on mixed hardware: CPU and GPU workers, fast and slow nodes, or local and remote executors with transfer costs.
- **Rules:** Calibrate task costs from measurements (G90).
- **Guardrails:** Schedules are plans. Execution must adapt when tasks overrun (G71, G94).

### 305. Build system graphs (early cutoff, constructive traces)

**Definition:** Modeling builds as dependency graphs of tasks and files, and rebuilding only what's actually affected by a change.

**How it works:**
1. Vertices are build tasks and their outputs. Edges are dependencies, declared statically (Make, Bazel) or discovered while running (Shake, Salsa).
2. **Dirty bit / timestamp model:** rebuild any task whose inputs are newer than its outputs (Make).
3. **Verifying traces:** record the hashes of each task's inputs. Rebuild only if a hash changed.
4. **Constructive traces:** also store the outputs by input hash, so results can be fetched from a cache instead of rebuilt (shared remote caches, Bazel).
5. **Early cutoff:** if a rebuilt task produces the same output as before, don't rebuild its dependents.
6. Builds are scheduled in topological order, in parallel where possible.

**Complexity:** Work proportional to what actually changed.

**Agent use:**
- **Role:** Operator.
- **How:** The model behind the glue engine's incremental recomputation and content-addressed caching (G39, G41), and behind validation after code edits (C#181).
- **Rules:** Declare every input of every task. Missing dependencies give stale, wrong results.
- **Guardrails:** Tasks with hidden inputs (time, network, environment variables) break caching. Make them explicit, or mark them uncacheable.

## G2. Memory and resource graphs

### 306. Tracing garbage collection (mark-sweep, tri-color marking, write barriers)

**Definition:** Finding unused memory by traversing the object graph from roots: everything unreachable is garbage.

**How it works:**
1. **Roots:** stacks, globals and registers.
2. **Mark:** traverse from the roots (BFS or DFS with an explicit stack), marking every reachable object.
3. **Sweep:** free every unmarked object (or, in copying collectors, copy live objects into a new space).
4. **Tri-color marking (for concurrent collection):** white (not yet seen), gray (seen, children not yet scanned), black (fully scanned). The invariant: no black object points to a white one.
5. **Write barriers:** when the program changes pointers during concurrent marking, a barrier shades the involved objects (Dijkstra insertion barrier, or Yuasa deletion/snapshot barrier), so nothing reachable gets freed.
6. **Generational collection:** most objects die young, so collect the young space often, using remembered sets of old-to-young pointers.

**Complexity:** O(live objects + pointers) per collection.

**Agent use:**
- **Role:** Operator and Analyst.
- **How:** The same reachability idea cleans up artifacts in any system: orphaned files, unused cache entries, old index segments, and intermediate glue artifacts (G88). Reachable from active roots means keep; otherwise collect.
- **Rules:** Define the roots explicitly (active flows, pinned snapshots, audit holds).
- **Guardrails:** Concurrent collection without barriers deletes live data. Changes during marking need equivalent protection.

### 307. Cycle collection for reference counting (Bacon-Rajan)

**Definition:** Finding and freeing groups of objects that reference each other in cycles, which plain reference counting never frees.

**How it works:**
1. Reference counting frees an object when its count reaches zero. Cyclic garbage keeps nonzero counts forever.
2. **Candidate roots:** objects whose count was decremented to a non-zero value (possibly the last outside reference to a cycle was just removed).
3. **Mark gray:** from each candidate, traverse and subtract internal references (trial deletion).
4. **Scan:** objects whose count stays above zero have outside references. Restore them (black). Objects at zero are white: garbage.
5. **Collect** the white objects.
6. Can run concurrently, with extra validation for counts that changed.

**Complexity:** Proportional to the subgraph reachable from the candidates.

**Agent use:**
- **Role:** Analyst.
- **How:** Detecting cyclic leaks in any reference-tracked system: circular references in caches, mutually referencing records, or services that keep each other alive.
- **Rules:** Check from recent decrement points, not the whole graph.
- **Guardrails:** Never delete before validating that no outside reference appeared during the check.

### 308. Distributed deadlock detection (Chandy-Misra-Haas edge chasing)

**Definition:** Detecting deadlock cycles in a wait-for graph spread across machines, by passing probe messages along wait edges.

**How it works:**
1. Each process knows only which other processes it's waiting for (its local outgoing edges in the global wait-for graph).
2. When a process is blocked, it sends a probe (initiator, sender, receiver) to each process it waits for.
3. A blocked process that receives a probe forwards it along its own wait edges.
4. If a probe returns to its initiator, there's a cycle: a deadlock.
5. Resolve by aborting a victim (by priority, age or cost), and releasing its resources.

**Complexity:** Messages proportional to the edges in the cycle.

**Agent use:**
- **Role:** Analyst.
- **How:** Detecting deadlocks between distributed workers, locks and transactions (the distributed version of glue G49, K#245).
- **Rules:** Victim selection policy is documented and deterministic.
- **Guardrails:** Phantom deadlocks (reported cycles that already resolved) can appear. Confirm before aborting important work.

## G3. Networks and protocols

### 309. Gossip (epidemic) protocols

**Definition:** Spreading information in a network by having each node repeatedly share what it knows with a few random peers.

**How it works:**
1. Each round, every node picks one or a few random peers.
2. **Push:** send updates. **Pull:** ask for updates. **Push-pull:** both, which spreads fastest.
3. News reaches all n nodes in O(log n) rounds with high probability.
4. **Anti-entropy:** periodically compare full state (using Merkle trees, V#127 style) to repair missed updates.
5. **Membership and failure detection (SWIM):** nodes probe random peers, with indirect probes through others before suspecting failure. Membership changes are piggybacked on probe messages.

**Complexity:** O(log n) rounds. O(n log n) total messages for one update.

**Agent use:**
- **Role:** Operator.
- **How:** Robust, decentralized propagation of configuration, cluster membership and cache invalidations, without a single point of failure.
- **Rules:** Version every gossiped item, so newer values always win (G80).
- **Guardrails:** Gossip is eventually consistent. Don't use it for decisions requiring strong consistency (use consensus, G76).

### 310. Consensus averaging on graphs (distributed averaging, Laplacian dynamics)

**Definition:** Nodes reach agreement on the average of their initial values by repeatedly averaging with their neighbors.

**How it works:**
1. Each node holds a value x_i.
2. Each round: x_i ← x_i + ε × Σ over neighbors j of (x_j − x_i). In matrix form, x ← (I − εL) x.
3. With a connected graph and a small enough ε, all values converge to the average.
4. Convergence speed depends on λ₂ (the algebraic connectivity, #159): well-connected graphs converge fast.
5. Push-sum variants work on directed graphs and with asynchronous communication.

**Complexity:** O(1/λ₂ × log(1/ε)) rounds.

**Agent use:**
- **Role:** Analyst and Operator.
- **How:** Decentralized aggregation (global averages, sums or counts of metrics across many nodes without a coordinator), and understanding how fast information mixes in a network.
- **Rules:** Use push-sum for directed or unreliable links.
- **Guardrails:** Byzantine (malicious) nodes break averaging. Use robust aggregation where nodes aren't trusted.

### 311. Network reliability (terminal reliability, Monte Carlo estimation)

**Definition:** The probability that specified nodes stay connected when edges (or nodes) fail independently with given probabilities.

**How it works:**
1. Each edge fails with probability q_e.
2. **Two-terminal reliability:** P(s and t stay connected). **All-terminal:** P(the whole network stays connected). Exact computation is #P-hard in general.
3. **Exact for small or special graphs:** series-parallel reductions, factoring (condition on one edge working or failing, recurse), and BDD-based methods.
4. **Monte Carlo:** sample failure scenarios, test connectivity (union-find, #51), and count. Importance sampling helps when failures are rare.
5. **Bounds:** from minimal cut sets and path sets (Gomory-Hu, #80; Menger, #91).

**Complexity:** Monte Carlo cost is samples × O(m α(n)).

**Agent use:**
- **Role:** Analyst.
- **How:** Quantifies the availability of critical paths (data center to region, service to database) given component failure rates, and compares redundancy options.
- **Rules:** Report confidence intervals (GR4), and the failure-probability sources.
- **Guardrails:** Independent-failure assumptions understate correlated failures (shared power, shared software). State the assumption.

### 312. Link-state and distance-vector routing (OSPF, RIP)

**Definition:** The two classic families of routing protocols: every router computes shortest paths from a full map (link-state), or routers exchange distance estimates with neighbors (distance-vector).

**How it works:**
1. **Link-state (OSPF, IETF RFC 2328; IS-IS):** each router floods descriptions of its own links to all routers. Every router gets the full topology and runs Dijkstra (#23) to build its forwarding table. Converges fast, with consistent views.
2. **Distance-vector (RIP, IETF RFC 2453):** each router sends its distance table to its neighbors. Each updates its distances with distributed Bellman-Ford (#24): d(dest) = min over neighbors (link cost + neighbor's distance).
3. **Count-to-infinity problem:** after a failure, distance-vector routers can keep increasing their distances through each other for a long time. Mitigations: split horizon, poison reverse, maximum hop counts.
4. **Areas and hierarchy** limit the flooding and computation scope in large networks.

**Complexity:** Link-state: one Dijkstra per router per change. Distance-vector: iterative exchanges.

**Agent use:**
- **Role:** Analyst.
- **How:** Understanding and simulating how routing reacts to failures (convergence time, transient loops), and the same patterns in service mesh and overlay routing.
- **Rules:** Simulate routing changes before applying them.
- **Guardrails:** Routing configuration changes on live networks need approval and staged rollout (GX4).

### 313. Path-vector routing (BGP)

**Definition:** The internet's inter-domain routing: each network announces full paths (lists of networks) to destinations, and chooses routes by policy, not just shortest distance.

**How it works:**
1. Each autonomous system (AS) advertises routes to address prefixes, with the AS path (BGP-4, IETF RFC 4271).
2. A receiving AS rejects paths that already contain its own number (loop prevention).
3. **Route selection by policy:** local preference (business relationships: customer routes preferred over peer, over provider), then shortest AS path, then other tie-breakers.
4. **Export policies** control which routes are shared with whom (the Gao-Rexford "valley-free" model).
5. Policies can make convergence slow or even impossible (no stable solution exists in some configurations).

**Complexity:** Convergence depends on topology and policies.

**Agent use:**
- **Role:** Analyst.
- **How:** Understanding reachability and path selection across organizational or network boundaries, and analyzing route leaks and policy conflicts.
- **Rules:** Model the policies explicitly when simulating.
- **Guardrails:** Route announcement changes affect external networks. Treat them as high-risk changes (GX4).

### 314. Spanning Tree Protocol (IEEE 802.1D, RSTP)

**Definition:** A distributed protocol that lets Ethernet switches with redundant links agree on a loop-free spanning tree, disabling the extra links until needed.

**How it works:**
1. Switches elect a root bridge (the lowest bridge ID) by exchanging BPDUs (bridge protocol data units).
2. Each switch chooses its root port: the port with the lowest-cost path to the root.
3. On each network segment, one designated port (the one offering the lowest cost to the root) forwards traffic. Other ports are blocked.
4. The active links form a spanning tree (a distributed shortest-path tree to the root), so broadcast loops are impossible.
5. On failure, blocked ports activate. **RSTP** (IEEE 802.1w, now part of 802.1D/802.1Q) converges in seconds instead of tens of seconds, using explicit handshakes.

**Complexity:** Convergence time bounded by protocol timers or handshake rounds.

**Agent use:**
- **Role:** Analyst.
- **How:** The pattern of "agree on a single loop-free tree among redundant links, keep the rest as standby" applies to any redundant distribution system (replication topologies, broadcast overlays).
- **Rules:** Choose the root deliberately (the most central, reliable node).
- **Guardrails:** Misconfigured priorities can elect a poor root. Validate the tree after changes.

## G4. Layout and visualization

### 315. Force-directed layout (Fruchterman-Reingold, Barnes-Hut, multilevel)

**Definition:** Drawing graphs by simulating physical forces: edges pull connected vertices together, and all vertices push each other apart.

**How it works:**
1. **Attraction** along edges (like springs). **Repulsion** between all pairs (like charges).
2. Move each vertex along its net force, with a step size that decreases over time ("cooling").
3. **Barnes-Hut approximation:** group distant vertices in a quadtree or octree and treat each group as one combined charge. Repulsion cost drops from O(n²) to O(n log n).
4. **Multilevel layout:** coarsen the graph (#175), lay out the small graph, then refine the layout at each finer level. Avoids poor local minima and is much faster.
5. Variants: stress majorization (match drawing distances to graph distances), ForceAtlas2 (for networks with communities).

**Complexity:** O(n log n + m) per iteration with Barnes-Hut.

**Agent use:**
- **Role:** Analyst and Reporter.
- **How:** Showing people structure (clusters, hubs, bridges) in subgraphs the agent found: evidence subgraphs, communities, dependency neighborhoods.
- **Rules:** Lay out bounded subgraphs (hundreds to low thousands of vertices), not whole graphs.
- **Guardrails:** Visual closeness isn't graph closeness. Don't draw conclusions from layout distances alone.

### 316. Hierarchical (layered) layout (Sugiyama framework)

**Definition:** Drawing directed graphs in layers so most edges point the same way (downward), with few crossings. The standard for dependency and flow diagrams.

**How it works:**
1. **Remove cycles:** reverse a small set of edges (feedback arc set, #188), and draw them back reversed later.
2. **Assign layers:** longest path layering (#20), Coffman-Graham (#303), or network simplex layering (minimizes total edge length).
3. **Add dummy vertices** where edges span several layers, so every edge connects adjacent layers.
4. **Reduce crossings:** reorder the vertices within each layer, sweeping up and down with barycenter or median heuristics (exact minimization is NP-hard).
5. **Assign coordinates:** horizontal positions that straighten edges and keep vertices balanced (Brandes-Köpf).

**Complexity:** Each step is near-linear to polynomial with heuristics.

**Agent use:**
- **Role:** Reporter.
- **How:** Drawing plans (glue engine DAGs), dependency graphs, call chains, data lineage and causal graphs in readable form for review and approval.
- **Rules:** Keep the reversed edges visually marked, so cycles are visible.
- **Guardrails:** Large graphs become unreadable. Summarize or collapse (#236) before drawing.

### 317. Edge bundling and large-graph visualization

**Definition:** Techniques that make large graphs readable by grouping similar edges into bundles and aggregating vertices.

**How it works:**
1. **Hierarchical edge bundling:** route edges along a hierarchy (such as the community tree), so edges between the same regions curve together.
2. **Force-directed edge bundling:** subdivide edges into points, and attract compatible edges (similar direction, length and position) to each other.
3. **Aggregation:** collapse communities into super-vertices, with expandable details (#236).
4. **Matrix views** (adjacency matrices with reordered rows, #9) for dense graphs, where node-link drawings fail.

**Complexity:** Bundling is about O(m × iterations) with spatial acceleration.

**Agent use:**
- **Role:** Reporter.
- **How:** Overviews of large structures for people, such as main flows between groups and dominant dependency directions, with drill-down.
- **Rules:** Always provide drill-down to exact data. Bundles are a visual summary.
- **Guardrails:** Bundling can suggest relationships that don't exist (merged edges look shared). Label it clearly.

## G5. Geometry, maps and security

### 318. Geometric graphs (Delaunay triangulation, Voronoi diagrams, Euclidean MST)

**Definition:** Graphs built from points in space by geometric rules, with useful guarantees for nearest neighbors, coverage and networks.

**How it works:**
1. **Voronoi diagram:** each point's region is everything closer to it than to any other point.
2. **Delaunay triangulation:** the dual graph of the Voronoi diagram. Connects points whose regions share a border. No point lies inside the circumcircle of any triangle. Built in O(n log n) (Fortune's sweep, or randomized incremental construction).
3. **Euclidean MST:** always a subgraph of the Delaunay triangulation, so compute it in O(n log n) by running Kruskal (#61) on Delaunay edges only.
4. **Other proximity graphs:** Gabriel graph, relative neighborhood graph (#295), nested inside Delaunay.

**Complexity:** O(n log n) in 2D. Higher dimensions grow much more expensive.

**Agent use:**
- **Role:** Analyst.
- **How:** Service area planning (which site serves which location: Voronoi), the cheapest network connecting sites (Euclidean MST), and nearest-facility lookups.
- **Rules:** Use proper geographic distances (great-circle, or projected coordinates) for map data.
- **Guardrails:** Planar geometry on raw latitude/longitude gives distorted results over large areas.

### 319. Map matching (hidden Markov model with Viterbi)

**Definition:** Snapping noisy GPS points to the actual road path traveled, by treating road segments as hidden states.

**How it works:**
1. For each GPS point, find candidate road segments within a radius (spatial index).
2. **Emission probability:** how likely the point is given the candidate. Gaussian in the distance from the point to the road.
3. **Transition probability:** how likely moving between candidates of consecutive points is. Compare the route distance between them on the road graph (shortest path, #23) with the straight-line distance between the points. Similar distances are likely.
4. **Viterbi** (#271) finds the most likely sequence of segments.
5. Handle gaps (missing points) and breaks (no feasible transition) by splitting the trace.

**Complexity:** O(T × k²) shortest-path queries for T points with k candidates each. Speedups from CH (#33) or caching.

**Agent use:**
- **Role:** Analyst.
- **How:** Turns raw location traces into road-level paths for analytics: travel times, route choices, fleet behavior. The same HMM pattern matches noisy event sequences to a known state graph (for example logs to a workflow).
- **Rules:** Tune the noise and transition parameters on labeled traces.
- **Guardrails:** Location traces are personal data (GX3, KG2-style). Minimize and protect them.

### 320. Attack graphs and attack path analysis (MulVAL-style)

**Definition:** Modeling how an attacker could chain vulnerabilities, misconfigurations and access rights through a system to reach critical assets, and finding the most important paths to break.

**How it works:**
1. **Facts:** hosts, network reachability, services, known vulnerabilities, credentials, privileges, trust relationships.
2. **Rules (logic, as in MulVAL's Datalog rules, K#89):** for example, "if the attacker can reach host H on port P, and service S on H at that port has a remote code execution vulnerability, the attacker gains code execution on H".
3. Derive everything the attacker can achieve. The derivation graph (facts and rules connecting them) is the attack graph.
4. **Analysis:** shortest or easiest attack paths to crown-jewel assets (#23, with difficulty weights); minimum cut sets of fixable conditions that block every path (#77, #100); and the most "central" weaknesses (#110).
5. **Probabilistic versions** use exploit likelihoods to estimate the risk of reaching each asset (#311-style).

**Complexity:** Logic-based generation is polynomial in the number of facts (avoids the explosion of state-enumeration approaches).

**Agent use:**
- **Role:** Analyst.
- **How:** Prioritizing security fixes: patching the few conditions on the minimum cut protects the critical assets, instead of fixing everything at random. Also verifies whether a proposed change opens new paths.
- **Rules:** Keep the facts fresh from inventories and scans. Results describe the snapshot (GR1).
- **Guardrails:** Attack paths are sensitive information: restrict access, and never run exploit actions. This is analysis only (GX4).

---

## How the 320 graph algorithms fit together

1. **Represent** (#1–12): choose the structure for the job. Live data in adjacency or base-plus-delta storage; analytics on CSR snapshots with reordering; huge graphs compressed; versions pinned (#244, GR1).
2. **Traverse and route** (#13–50): direction-optimizing BFS for reach; Dijkstra variants or ALT for one-off paths; contraction hierarchies, hub labels or CRP for heavy query loads; resource-constrained, Pareto and temporal variants when constraints or time matter.
3. **Find structure** (#51–100, #121–131, #151–169): connectivity and weak points (bridges, articulation points, cuts, dominators); dense groups (cores, trusses, cliques, densest subgraphs); communities (Leiden, Infomap, SBM), always with stability checks.
4. **Rank and compare** (#101–120, #251–258, #285–294): PageRank and push PPR for relevance; approximate betweenness for brokers; similarity indices, embeddings and metapath measures for "like this"; alignment for matching across graphs.
5. **Optimize** (#61–100, #183–188, #197, #301–304): flows, cuts, matching and assignment, routing problems, coloring, covers and scheduling. Always with certificates (cuts for flows, covers for matchings) and approximation bounds.
6. **Scale** (#170–175, #201–250): partition (METIS, streaming, vertex-cut), process (GAS, Ligra, GraphBLAS, GPU, out-of-core, distributed), keep results current incrementally (dynamic algorithms, differential dataflow, IVM), and use sketches, samples and sparsifiers with stated error bounds.
7. **Infer and learn** (#259–284): GNNs suited to the graph (homophily checked), probabilistic inference with convergence checks, causal reasoning with explicit assumptions, graph construction choices recorded.
8. **Apply in systems** (#295–320): program analysis for code-aware tooling, build graphs and garbage collection for the glue engine's incremental work and cleanup, protocols for distribution, layouts for human review, attack graphs for security.

Each algorithm plugs into the composition engine through its contract (G1): the input graph type and its assumptions (GR2), the cost model (GR3), exactness (GR4), and the certificate it provides (GR6). With these, the planner can pick and combine graph algorithms just like the code, vector and knowledge graph algorithms.