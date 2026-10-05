# Part 2: Connectivity, trees, flows, cuts, matching and routing (#51–100)

Same format and the same contract (roles; rules GR1–GR8; guardrails GX1–GX5).

## B1. Connectivity

### 51. Union-find (disjoint set union) in depth

**Definition:** A structure that tracks a partition of elements into sets, supporting "merge two sets" and "which set is this in?" in nearly constant time.

**How it works:**
1. Each element points to a parent; a root (pointing to itself) represents its set.
2. **Find:** follow parents to the root. **Path compression:** afterward, point every visited element directly at the root (or every other element, with path halving).
3. **Union:** link one root under the other. **Union by rank or size:** attach the smaller tree under the larger, which keeps trees shallow.
4. With both optimizations, each operation costs O(α(n)) amortized, where α is the inverse Ackermann function, below 5 for any practical n.
5. Variants: weighted union-find (tracking an offset or relation to the root), rollback union-find (undo for offline algorithms), and concurrent union-find with atomic compare-and-swap.

**Complexity:** O(α(n)) amortized per operation, O(n) memory.

**Agent use:**
- **Role:** Analyst and Builder.
- **How:** Connected components (K#79), Kruskal's MST (#61), entity-resolution clustering (K#38) and equality reasoning (K#92). The rollback variant supports "what if we removed these merges".
- **Rules:** Record the set of unions applied, so components can be explained (which edge joined them).
- **Guardrails:** Union-find can't split sets. For deletions, use dynamic connectivity (#52) or rebuild.

### 52. Fully dynamic connectivity (Holm–de Lichtenberg–Thorup)

**Definition:** Maintaining connected components under both edge insertions and edge deletions, answering "are u and v connected?" quickly.

**How it works:**
1. Maintain a spanning forest using Euler tour trees (#71), so trees can be split and joined in O(log n).
2. Each edge has a level, starting at 0. There are log n levels, each with its own nested forest.
3. **Insert:** add the edge. If it connects two trees, it becomes a tree edge.
4. **Delete a tree edge:** the tree splits. Search for a replacement edge, starting at the edge's level, checking non-tree edges from the smaller side. Edges checked without success are promoted to a higher level, which bounds the total work by amortization.
5. **Query:** check whether u and v are in the same Euler tour tree.

**Complexity:** O(log² n) amortized per update, O(log n / log log n) per query.

**Agent use:**
- **Role:** Analyst.
- **How:** Live connectivity in changing networks: "is service A still reachable from B after this link failure?", or live component tracking in streaming graphs.
- **Rules:** Use a library implementation; this algorithm is complex to implement correctly.
- **Guardrails:** Cross-check against a periodic full recomputation (GX5).

### 53. Bridges and articulation points (Tarjan's lowlink)

**Definition:** Finding edges (bridges) and vertices (articulation points, or cut vertices) whose removal disconnects the graph.

**How it works:**
1. Run DFS (#14), recording each vertex's discovery time disc[v].
2. Compute low[v] = the smallest discovery time reachable from v's subtree using at most one back edge.
3. **Bridge:** a tree edge (u, v) is a bridge if low[v] > disc[u] (v's subtree can't reach u or above without that edge).
4. **Articulation point:** a non-root vertex u is a cut vertex if some child v has low[v] ≥ disc[u]. The root is a cut vertex if it has two or more DFS children.
5. One DFS finds all of them.

**Complexity:** O(n + m).

**Agent use:**
- **Role:** Analyst.
- **How:** Finds single points of failure: network links or routers whose loss splits the network, services everything depends on, and critical people or nodes in an organization graph.
- **Rules:** Report each critical element with the components it separates.
- **Guardrails:** Use an iterative DFS on large graphs (recursion limits).

### 54. Biconnected components and the block-cut tree

**Definition:** Splitting a graph into maximal pieces with no single vertex whose removal disconnects them, and connecting those pieces in a tree.

**How it works:**
1. During the articulation point DFS (#53), push edges on a stack.
2. When a child v satisfies low[v] ≥ disc[u], pop edges down to (u, v). Those edges form one biconnected component (a "block").
3. **Block-cut tree:** one node per block and one per articulation point, with edges where an articulation point belongs to a block.
4. That tree shows how robust parts of the graph hang together.

**Complexity:** O(n + m).

**Agent use:**
- **Role:** Analyst.
- **How:** Resilience design: a block-cut tree shows exactly which parts are robust and which hinge on single vertices, which guides redundancy planning.
- **Rules:** Present the tree with block sizes, and highlight critical articulation points.
- **Guardrails:** None specific.

### 55. 2-edge-connected components

**Definition:** Maximal subgraphs that stay connected after removing any one edge.

**How it works:**
1. Find all bridges (#53).
2. Remove the bridges. The remaining connected components are the 2-edge-connected components.
3. Contracting each component gives the bridge tree: a tree whose edges are exactly the bridges.

**Complexity:** O(n + m).

**Agent use:**
- **Role:** Analyst.
- **How:** Link-failure resilience: within a component, any single link failure leaves everything connected.
- **Rules:** Use for edge failures; use biconnected components (#54) for vertex failures.
- **Guardrails:** None specific.

### 56. SPQR trees (triconnected components, Hopcroft-Tarjan)

**Definition:** A tree decomposition of a biconnected graph into triconnected pieces, describing all its 2-vertex cuts (separation pairs).

**How it works:**
1. Start from a biconnected graph (#54).
2. Find separation pairs: pairs of vertices whose removal disconnects the graph.
3. Split at them recursively. Each piece is one of: **S** (a cycle), **P** (parallel edges between two vertices), **R** (a rigid triconnected graph), or **Q** (a single edge).
4. The pieces form a tree, joined by virtual edges at the separation pairs.
5. Linear-time algorithms exist (Hopcroft-Tarjan, corrected by Gutwenger and Mutzel).

**Complexity:** O(n + m), but complex to implement.

**Agent use:**
- **Role:** Analyst.
- **How:** Finds all two-element failure points in a network. Also used in planarity work and graph drawing (#195, #316).
- **Rules:** Use a tested library (OGDF, for example).
- **Guardrails:** Verify by removing reported separation pairs on samples (GX5).

### 57. Parallel strongly connected components (forward-backward, coloring)

**Definition:** Finding SCCs on large graphs with parallel algorithms, since Tarjan's DFS (K#80) is inherently sequential.

**How it works:**
1. **Trim:** repeatedly remove vertices with zero in-degree or zero out-degree. Each is its own SCC, and real graphs have many.
2. **Forward-backward:** pick a pivot vertex. Compute its forward-reachable set F and backward-reachable set B with parallel BFS. Then F ∩ B is one SCC. The remaining parts (F \ B, B \ F, and the rest) are independent subproblems, processed recursively in parallel.
3. **Coloring method:** propagate the maximum vertex ID forward. Each color class's root and its backward reachable set within the class form an SCC.
4. The large SCC (usually one giant component) is found quickly with BFS.

**Complexity:** O(n + m) work expected in practice. Highly parallel.

**Agent use:**
- **Role:** Analyst.
- **How:** SCC analysis on very large directed graphs (web, call graphs, dependency graphs) on many cores or machines.
- **Rules:** Trim first; it often removes most vertices.
- **Guardrails:** Cross-check SCC counts against a sequential run on samples (GX5).

### 58. Condensation and transitive reduction

**Definition:** Condensation collapses each SCC to one vertex, giving a DAG. Transitive reduction removes edges implied by other paths, giving the minimal graph with the same reachability.

**How it works:**
1. **Condensation:** find the SCCs and replace each with a single vertex. Keep one edge between components where any edge existed.
2. **Transitive reduction of a DAG:** remove each edge (u, v) when there's another path from u to v. Process vertices in topological order; for each, compute descendants with bitsets and drop edges to vertices already reachable through other children.
3. The result is unique for DAGs.

**Complexity:** Condensation O(n + m). Transitive reduction is about as hard as transitive closure, O(n × m) in general, faster with bitsets.

**Agent use:**
- **Role:** Builder.
- **How:** Simplifies dependency graphs for people (show only essential dependencies) and speeds up later algorithms that work on DAGs.
- **Rules:** Keep the original graph. The reduced graph is a view, recorded as derived (GR1).
- **Guardrails:** Reduction removes edges that may carry their own meaning (weights, labels). Use it for reachability only.

### 59. Dominator trees (Lengauer-Tarjan, Cooper-Harvey-Kennedy)

**Definition:** In a graph with a start vertex, vertex d dominates v if every path from the start to v passes through d. The dominator tree organizes all these relationships.

**How it works:**
1. **Iterative (Cooper-Harvey-Kennedy):** process vertices in reverse postorder. Set each vertex's immediate dominator to the "intersection" (nearest common ancestor in the current tree) of its processed predecessors. Repeat until nothing changes. Simple and fast in practice.
2. **Lengauer-Tarjan:** DFS numbering, then semi-dominators computed with a union-find-like structure, then immediate dominators. Near-linear time.
3. The dominator tree: each vertex's parent is its immediate dominator.
4. **Dominance frontier:** where a vertex's dominance ends. Used to place phi nodes in SSA form (C#95).

**Complexity:** Iterative: about O(n + m) on typical graphs. Lengauer-Tarjan: O(m × α(m, n)).

**Agent use:**
- **Role:** Analyst.
- **How:** Compiler analysis (SSA, loop detection), and in other graphs it finds mandatory checkpoints: "every request path to this database goes through this gateway", or "every route to this asset passes this control" (security).
- **Rules:** Results depend on the chosen start vertex. Record it.
- **Guardrails:** Unreachable vertices have no dominators. Report them separately.

### 60. Post-dominators and control dependence

**Definition:** Post-dominators are dominators on the reversed graph (relative to the exit). Control dependence says which branch decisions determine whether a step runs.

**How it works:**
1. Add a single exit vertex if there are several.
2. Compute dominators on the reversed graph from the exit. Those are the post-dominators.
3. **Control dependence:** v is control-dependent on edge (u, w) if v post-dominates w but doesn't strictly post-dominate u. Computed with the post-dominance frontier.
4. The result is the control dependence graph, a building block of program slicing.

**Complexity:** O(n + m) to O(m × α) for the dominators. Control dependence is about linear in practice.

**Agent use:**
- **Role:** Analyst.
- **How:** Program slicing ("which conditions affect whether this line runs?"), impact analysis for code edits, and in workflow graphs, which decisions gate which steps.
- **Rules:** Make sure there's a unique exit vertex.
- **Guardrails:** Infinite loops without exits need a virtual exit edge, or results are undefined.

## B2. Spanning trees and Steiner trees

### 61. Kruskal's minimum spanning tree

**Definition:** Building a minimum-weight spanning tree by adding the cheapest edges that don't form cycles.

**How it works:**
1. Sort the edges by weight.
2. Go through them in order. Add an edge if its endpoints are in different components (checked with union-find, #51), then union the components.
3. Stop after n−1 edges (or when the list ends, giving a forest for disconnected graphs).
4. **Cut property:** the lightest edge across any cut belongs to some MST, which proves correctness.
5. Stopping early (at k components) gives single-linkage clustering.

**Complexity:** O(m log m), dominated by the sort.

**Agent use:**
- **Role:** Optimizer and Analyst.
- **How:** Cheapest network design (cables, links), clustering (single linkage), and building a backbone for visualization.
- **Rules:** Use deterministic tie-breaking for reproducibility (GR5).
- **Guardrails:** Verify with the cycle property: every non-tree edge is at least as heavy as all edges on the tree path between its endpoints (GR6).

### 62. Prim's minimum spanning tree

**Definition:** Growing a minimum spanning tree from a start vertex by repeatedly adding the cheapest edge leaving the tree.

**How it works:**
1. Start with one vertex in the tree.
2. Keep a priority queue of the cheapest known edge to each outside vertex.
3. Add the outside vertex with the cheapest edge, then update its neighbors' best edges.
4. Repeat until all reachable vertices are in the tree.

**Complexity:** O(m log n) with a binary heap. O(n²) with an array, which suits dense graphs.

**Agent use:**
- **Role:** Optimizer.
- **How:** Preferred for dense graphs, or when the graph is implicit (edges computed on demand from coordinates or similarities).
- **Rules:** Same verification as #61.
- **Guardrails:** It covers only the start vertex's component. Run it per component for forests.

### 63. Borůvka's algorithm (parallel MST)

**Definition:** An MST algorithm where every component simultaneously picks its cheapest outgoing edge, which suits parallel and distributed execution.

**How it works:**
1. Start with every vertex as its own component.
2. In parallel, each component finds its cheapest edge to another component.
3. Add all those edges (with consistent tie-breaking to avoid cycles) and merge the components.
4. Each round at least halves the number of components, so there are at most log n rounds.

**Complexity:** O(m log n) total work. Highly parallel.

**Agent use:**
- **Role:** Optimizer.
- **How:** MST on huge graphs across many cores or machines. Also the basis of distributed MST (#228) and parts of fast clustering.
- **Rules:** Strict tie-breaking by (weight, edge ID) is required.
- **Guardrails:** Cross-check total weight against Kruskal on samples (GX5).

### 64. Minimum spanning arborescence (Chu-Liu/Edmonds)

**Definition:** The minimum-weight directed spanning tree rooted at a given vertex: every vertex reachable from the root along tree edges.

**How it works:**
1. For each non-root vertex, pick its cheapest incoming edge.
2. If those edges have no cycle, they form the answer.
3. If there's a cycle, contract it into one super-vertex. Adjust the weights of edges entering the cycle by subtracting the weight of the cycle edge they would replace.
4. Solve the smaller problem recursively.
5. Expand the contracted cycles: keep all cycle edges except the one replaced by the chosen incoming edge.

**Complexity:** O(n × m) simple version, O(m + n log n) with Gabow et al.'s improvements.

**Agent use:**
- **Role:** Optimizer.
- **How:** Directed hierarchies: optimal dependency or broadcast trees, minimum-cost directed distribution, and building the best parse tree in dependency parsing.
- **Rules:** Check that every vertex is reachable from the root first. If not, there's no solution.
- **Guardrails:** None specific.

### 65. Steiner tree approximation (Kou–Markowsky–Berman / Mehlhorn)

**Definition:** Connecting a required subset of vertices (terminals) at minimum total edge cost, optionally through extra vertices. The exact problem is NP-hard; good approximations are standard.

**How it works:**
1. Build the "metric closure" over the terminals: a complete graph whose edge weights are shortest-path distances between terminals.
2. Find its MST.
3. Replace each MST edge with the actual shortest path in the original graph.
4. Compute an MST of the resulting subgraph, and prune non-terminal leaves.
5. Mehlhorn's version computes this faster, using Voronoi regions around terminals (one multi-source Dijkstra).

**Complexity:** O(m + n log n) with Mehlhorn's method. Approximation factor 2 (within twice the optimum).

**Agent use:**
- **Role:** Optimizer and Analyst.
- **How:** Minimum network to connect given sites, and in knowledge graphs, the smallest connecting subgraph between the question's entities, which makes concise explanation context.
- **Rules:** Report the approximation factor (GR4).
- **Guardrails:** None specific.

### 66. Prize-collecting Steiner tree (Goemans-Williamson)

**Definition:** Choosing which vertices to connect, trading the cost of edges against penalties for leaving vertices out (or the value gained by including them).

**How it works:**
1. Each vertex has a prize (or penalty); each edge has a cost.
2. Goal: minimize edge costs + penalties of excluded vertices.
3. **Goemans-Williamson primal-dual:** grow dual variables around components simultaneously. Edges become tight (are added) when the duals paid on both sides cover their cost. Components "deactivate" when their prizes are used up.
4. A pruning step removes unprofitable branches.
5. Gives a 2-approximation. Strong heuristics and exact solvers exist for practical instances.

**Complexity:** About O(n² log n).

**Agent use:**
- **Role:** Optimizer.
- **How:** Network expansion planning (which customers are worth connecting), and finding the most "valuable" connected subgraph for a query (relevance as prizes, edge costs as noise).
- **Rules:** Calibrate prizes and costs on the same scale.
- **Guardrails:** None specific.

## B3. Tree algorithms

### 67. Lowest common ancestor (binary lifting, Euler tour + RMQ)

**Definition:** Finding the deepest vertex that is an ancestor of both given vertices in a rooted tree.

**How it works:**
1. **Binary lifting:** precompute up[k][v] = the 2^k-th ancestor of v. To answer, lift the deeper vertex to the same depth, then lift both together by decreasing powers of two while their ancestors differ. The answer is the parent where they meet.
2. **Euler tour + RMQ:** with an Euler tour (#19), the LCA is the minimum-depth vertex between the two vertices' first occurrences. A sparse table answers range-minimum queries in O(1).
3. Distance between u and v = depth(u) + depth(v) − 2 × depth(LCA).

**Complexity:** Binary lifting: O(n log n) preprocessing, O(log n) per query. Euler + sparse table: O(n log n) preprocessing, O(1) per query.

**Agent use:**
- **Role:** Analyst.
- **How:** Hierarchy queries: the nearest common category, the common manager of two people, the shared base directory, and fast tree distances.
- **Rules:** Rebuild after tree changes, or use dynamic structures (#70).
- **Guardrails:** None specific.

### 68. Heavy-light decomposition

**Definition:** Splitting a tree into paths so that any root-to-vertex path crosses only O(log n) of them, turning path queries into range queries.

**How it works:**
1. For each vertex, the child with the largest subtree is "heavy"; the others are "light".
2. Chains of heavy edges form heavy paths.
3. Any path from the root crosses at most O(log n) light edges, so at most O(log n) heavy paths.
4. Lay out each heavy path contiguously in an array, so a segment tree or Fenwick tree can answer range queries along it.
5. A path query (u, v) splits into O(log n) range queries.

**Complexity:** O(log² n) per path query or update with a segment tree.

**Agent use:**
- **Role:** Analyst.
- **How:** Fast aggregate queries along hierarchy paths, such as "maximum risk score on the path from this asset to the root" or "sum of costs along a chain of command", with updates.
- **Rules:** Use it when there are many path queries on a mostly stable tree.
- **Guardrails:** None specific.

### 69. Centroid decomposition

**Definition:** Recursively splitting a tree at its centroid (a vertex whose removal leaves pieces of at most half the size), giving a recursion of depth O(log n).

**How it works:**
1. Find the centroid: walk from any vertex toward the largest subtree until no subtree exceeds n/2.
2. Process all paths passing through the centroid (combining information from its subtrees).
3. Remove the centroid and recurse on each remaining piece.
4. Every path in the tree passes through exactly one centroid at the highest level where both its endpoints are still together.

**Complexity:** O(n log n) for the decomposition. Many path-counting problems solved in O(n log n) or O(n log² n).

**Agent use:**
- **Role:** Analyst.
- **How:** Counting or finding paths with constraints in trees ("how many pairs are within distance k?"), and nearest-marked-vertex queries in hierarchies.
- **Rules:** Use for offline batches of tree-path questions.
- **Guardrails:** None specific.

### 70. Link-cut trees

**Definition:** A dynamic forest structure supporting linking trees, cutting edges and path queries, all in O(log n) amortized time.

**How it works:**
1. Represent the forest as "preferred paths", each stored in a splay tree keyed by depth.
2. **Access(v):** make the path from the root to v preferred, restructuring the splay trees.
3. **Link(u, v):** make u a child of v. **Cut(v):** remove v from its parent.
4. Path aggregates (sum, max) are maintained inside the splay trees.
5. A "make root" operation (re-rooting) supports undirected use.

**Complexity:** O(log n) amortized per operation.

**Agent use:**
- **Role:** Analyst.
- **How:** Live hierarchies with frequent restructuring (dynamic org charts, network trees), and as a building block of advanced flow and MST algorithms.
- **Rules:** Use a tested library.
- **Guardrails:** Validate it against a simple recomputation on test cases.

### 71. Euler tour trees

**Definition:** Representing each tree of a dynamic forest by its Euler tour stored in a balanced search tree, so trees can be split and joined quickly.

**How it works:**
1. Each tree is stored as its Euler tour sequence (#19) in a balanced BST or treap.
2. **Link:** re-root one tour (a rotation) and splice it into the other.
3. **Cut:** split out the subsequence between the edge's two occurrences.
4. Subtree aggregates are kept in the BST nodes.
5. Connectivity query: check whether two vertices' tours have the same root.

**Complexity:** O(log n) per operation.

**Agent use:**
- **Role:** Analyst.
- **How:** The core structure inside dynamic connectivity (#52), and dynamic subtree aggregates.
- **Rules:** Use as a component, not usually directly.
- **Guardrails:** None specific.

### 72. Tree isomorphism (AHU algorithm)

**Definition:** Deciding whether two rooted trees have the same shape, in linear time, through canonical encoding.

**How it works:**
1. Process vertices from the leaves upward.
2. Each leaf gets code "()".
3. Each internal vertex's code = "(" + its children's codes, sorted + ")".
4. Two trees are isomorphic exactly when their root codes are equal.
5. For unrooted trees, root them at their center (one or two vertices) and compare.
6. Faster versions replace strings with integer IDs per level.

**Complexity:** O(n) with integer labeling, O(n log n) with sorting.

**Agent use:**
- **Role:** Analyst.
- **How:** Detects structurally identical hierarchies: duplicate folder structures, repeated config trees, identical syntax subtrees (C#85 clone detection).
- **Rules:** Include node labels in the codes when labels matter.
- **Guardrails:** None specific.

### 73. Tree dynamic programming with rerooting

**Definition:** Computing a value for every vertex as if it were the root, in linear total time, by reusing subtree results.

**How it works:**
1. **Downward pass:** with an arbitrary root, compute each vertex's subtree value from its children (post-order).
2. **Upward pass:** compute each vertex's "outside" value (from the rest of the tree) using its parent's outside value and its siblings' subtree values. Prefix and suffix combinations over the siblings avoid quadratic work.
3. Combine the inside and outside values to get each vertex's answer as root.

**Complexity:** O(n).

**Agent use:**
- **Role:** Analyst.
- **How:** Per-vertex totals in hierarchies or trees: total distance to all others, best placement of a service in a tree network, or eccentricity for every vertex.
- **Rules:** Check that the combine operation is associative, or that prefix/suffix methods handle it correctly.
- **Guardrails:** None specific.

## B4. Maximum flow and minimum cut

### 74. Ford-Fulkerson and Edmonds-Karp

**Definition:** Computing the maximum flow from a source to a sink by repeatedly finding augmenting paths in the residual graph.

**How it works:**
1. Flow on each edge starts at 0. The residual graph has forward edges with remaining capacity and backward edges with the flow that can be cancelled.
2. Find a path from source to sink in the residual graph.
3. Push the bottleneck amount along it, updating the residual capacities in both directions.
4. Repeat until there's no augmenting path.
5. **Edmonds-Karp:** always pick the shortest augmenting path (BFS). That guarantees O(n × m²) time.

**Complexity:** Edmonds-Karp O(n × m²).

**Agent use:**
- **Role:** Optimizer.
- **How:** The conceptual base for capacity questions: "how much traffic or how many tasks can flow from A to B?". Use Dinic or push-relabel (#75, #76) in practice.
- **Rules:** Integer capacities give integer flows (useful for assignment problems).
- **Guardrails:** Basic Ford-Fulkerson can run forever with irrational capacities and is very slow with large ones. Use Edmonds-Karp or better.

### 75. Dinic's algorithm

**Definition:** A maximum-flow algorithm that pushes flow along shortest paths in layers, using blocking flows.

**How it works:**
1. BFS from the source in the residual graph, giving each vertex a level (distance).
2. Use only edges going from level i to level i+1 (the level graph).
3. Find a blocking flow in the level graph with DFS, using a "current edge" pointer per vertex so dead edges are skipped permanently.
4. Repeat from step 1 until the sink is unreachable.
5. The shortest augmenting path length increases every phase, so there are at most n phases.

**Complexity:** O(n² × m) in general. O(m × √n) for unit-capacity graphs, including bipartite matching.

**Agent use:**
- **Role:** Optimizer.
- **How:** A fast, reliable default max-flow for most practical problems.
- **Rules:** Use the current-edge optimization, or performance degrades.
- **Guardrails:** Verify with the min-cut certificate (#77).

### 76. Push-relabel (Goldberg-Tarjan)

**Definition:** A maximum-flow algorithm that pushes excess flow locally between vertices, guided by height labels, instead of finding whole paths.

**How it works:**
1. Saturate all edges out of the source. Vertices now hold excess flow.
2. Each vertex has a height label. The source starts at height n, everything else at 0.
3. **Push:** move excess from a vertex to a residual neighbor exactly one height lower.
4. **Relabel:** if a vertex has excess but no lower neighbor, raise its height to one above its lowest residual neighbor.
5. Finish when no vertex except the source and sink has excess.
6. **Heuristics that matter a lot:** highest-label selection, global relabeling (periodically recompute exact distances to the sink by BFS), and the gap heuristic (if no vertex has height k, every vertex above k can't reach the sink).

**Complexity:** O(n² × √m) with highest-label selection. Very fast in practice with the heuristics.

**Agent use:**
- **Role:** Optimizer.
- **How:** Large and dense flow problems, and computer vision cuts. Parallel implementations exist, because work is local.
- **Rules:** Always enable global relabeling and the gap heuristic.
- **Guardrails:** Verify with the min-cut certificate (#77).

### 77. Min cut extraction (max-flow min-cut theorem)

**Definition:** After a maximum flow, extracting the minimum s-t cut: the cheapest set of edges whose removal separates source from sink. Its capacity equals the maximum flow.

**How it works:**
1. Compute a maximum flow (#75, #76).
2. In the final residual graph, find every vertex reachable from the source (by BFS). That's the source side S.
3. The cut is all original edges going from S to the rest.
4. **Certificate:** the cut's total capacity equals the flow value. Checking that proves both results are optimal.

**Complexity:** O(n + m) after the max-flow.

**Agent use:**
- **Role:** Optimizer and Verifier.
- **How:** Bottleneck identification: the smallest set of links, services or suppliers whose failure separates two parts. Also proves the flow's optimality.
- **Rules:** Always present the cut with the flow, as the proof (GR6).
- **Guardrails:** Several minimum cuts may exist. State that the one reported is one of possibly many.

### 78. Stoer-Wagner global minimum cut

**Definition:** Finding the minimum cut over all possible partitions of an undirected weighted graph, without choosing a source or sink.

**How it works:**
1. **Minimum cut phase:** starting from any vertex, repeatedly add the vertex most tightly connected to the current set (maximum adjacency ordering).
2. The last two vertices added, s and t: the cut separating t from everything else is a minimum s-t cut.
3. Record that cut's value, then merge s and t into one vertex.
4. Repeat n−1 phases. The smallest recorded cut is the global minimum.

**Complexity:** O(n × m + n² log n).

**Agent use:**
- **Role:** Analyst.
- **How:** Measures how robust a network is overall: the minimum number or capacity of links whose loss splits it anywhere. Also splits a graph at its weakest point.
- **Rules:** Use for undirected graphs with non-negative weights.
- **Guardrails:** O(n²) memory for dense versions. Check size first.

### 79. Karger and Karger-Stein randomized min cut

**Definition:** Finding a global minimum cut by randomly contracting edges, repeated many times.

**How it works:**
1. Repeatedly pick a random edge (weighted by capacity) and merge its endpoints, until only two vertices remain. The edges between them form a cut.
2. Any specific minimum cut survives with probability at least 2/(n(n−1)).
3. Repeat O(n² log n) times and keep the smallest cut found, which is minimal with high probability.
4. **Karger-Stein:** contract only down to about n/√2 vertices, then recurse twice. This greatly improves the success probability per unit of work.

**Complexity:** Karger-Stein: O(n² log³ n) for a high-probability result.

**Agent use:**
- **Role:** Analyst.
- **How:** Simple, parallel min-cut estimation on large graphs. The contraction process also inspires graph sparsification (#239).
- **Rules:** Report the confidence level (GR4).
- **Guardrails:** It's randomized: fix seeds (GR5), and verify the final cut's value.

### 80. Gomory-Hu tree

**Definition:** A weighted tree that encodes the minimum s-t cut value for every pair of vertices, using only n−1 max-flow computations.

**How it works:**
1. Start with all vertices in one tree node.
2. Pick two vertices s and t in the same tree node. Compute a minimum s-t cut in the original graph, with the other tree nodes contracted appropriately.
3. Split the tree node according to the cut, and connect the two parts with an edge weighted by the cut value.
4. Repeat until every tree node holds one vertex. (Gusfield's simplification avoids the contractions.)
5. Min cut between any u and v = the smallest edge weight on the tree path between them.

**Complexity:** n−1 max-flow computations.

**Agent use:**
- **Role:** Analyst.
- **How:** Answers "how many links must fail to separate X and Y?" for every pair at once. Gives a complete robustness map of a network.
- **Rules:** Use for undirected graphs.
- **Guardrails:** Cost is n max-flows. Check the GR3 budget for large graphs.

### 81. Minimum-cost flow (successive shortest paths with potentials)

**Definition:** Sending a required amount of flow through a network at minimum total cost, respecting capacities.

**How it works:**
1. Each edge has a capacity and a cost per unit of flow.
2. Maintain vertex potentials, so reduced costs (cost + potential(u) − potential(v)) stay non-negative (as in Johnson's reweighting, #26).
3. Repeatedly find the shortest path from source to sink in the residual graph using Dijkstra on the reduced costs.
4. Push as much flow as possible along it, and update the potentials with the new distances.
5. Stop when the required flow is sent, or no path remains.
6. **Optimality certificate:** no negative-cost cycle in the residual graph.

**Complexity:** O(F × m log n), where F is the flow value. Capacity scaling makes it polynomial in the input size.

**Agent use:**
- **Role:** Optimizer.
- **How:** Assignment with costs, transportation, load distribution across servers with different costs, and staffing with preferences.
- **Rules:** Check the result with the no-negative-cycle certificate (GR6).
- **Guardrails:** Optimization results that affect people or money are proposals (GR8).

### 82. Network simplex

**Definition:** The simplex method specialized for min-cost flow, operating on spanning trees instead of matrices.

**How it works:**
1. A basic solution corresponds to a spanning tree: non-tree edges are at their lower or upper bounds.
2. Compute vertex potentials from the tree, and the reduced costs of non-tree edges.
3. Pick an entering edge with negative reduced cost (a pricing rule such as block search).
4. Push flow around the cycle it creates in the tree, until some edge hits a bound. That edge leaves the tree.
5. Update the tree and the potentials incrementally. Repeat until no negative reduced costs remain.

**Complexity:** Exponential in the worst case. Typically among the fastest min-cost flow methods in practice.

**Agent use:**
- **Role:** Optimizer.
- **How:** Large logistics, transportation and allocation problems, through tested solvers (LEMON, OR-Tools).
- **Rules:** Use a library solver, and validate the optimality conditions.
- **Guardrails:** Use anti-cycling rules (strongly feasible trees), or degenerate problems can loop.

### 83. Circulation with demands and lower bounds

**Definition:** Finding a flow where every vertex has a fixed supply or demand, and every edge has a minimum and maximum flow.

**How it works:**
1. **Lower bounds:** for each edge with lower bound ℓ, pre-send ℓ units. Reduce its capacity by ℓ, and adjust the endpoint vertices' demands.
2. Add a super-source connected to all supply vertices and a super-sink connected to all demand vertices.
3. Run max-flow. A feasible circulation exists exactly when all super-source edges are saturated.
4. With costs on edges, run min-cost flow instead for the cheapest feasible circulation.

**Complexity:** One max-flow (or min-cost flow).

**Agent use:**
- **Role:** Optimizer.
- **How:** Feasibility of plans with minimum and maximum commitments: shift coverage (each shift needs at least k staff), contracted minimum volumes per supplier, quota routing.
- **Rules:** If infeasible, report the minimum cut showing why. That's the proof (GR6).
- **Guardrails:** None specific.

## B5. Matching and assignment

### 84. Hopcroft-Karp (maximum bipartite matching)

**Definition:** The fastest classical algorithm for maximum-cardinality matching in bipartite graphs.

**How it works:**
1. Start with any matching (possibly empty).
2. BFS from all free left vertices simultaneously, building layers of alternating paths (unmatched edge, matched edge, …) to find the shortest augmenting path length.
3. DFS to find a maximal set of vertex-disjoint augmenting paths of that length.
4. Flip all of them at once (unmatched edges become matched and vice versa), increasing the matching size.
5. Repeat until there are no augmenting paths. At most O(√n) phases are needed.

**Complexity:** O(m √n).

**Agent use:**
- **Role:** Optimizer.
- **How:** Assigning tasks to workers, reviewers to changes, or requests to servers, when only feasibility matters, not cost.
- **Rules:** A greedy initial matching speeds it up considerably.
- **Guardrails:** Verify maximality with König's theorem (#90): a vertex cover of the same size proves it.

### 85. Hungarian algorithm (assignment problem)

**Definition:** Finding a minimum-cost perfect matching in a weighted bipartite graph: the optimal one-to-one assignment.

**How it works:**
1. Keep dual potentials for both sides, so that every edge's reduced cost is ≥ 0.
2. Consider only "tight" edges (reduced cost 0). Try to extend the matching using augmenting paths along tight edges.
3. When stuck, adjust the potentials by the smallest slack value, creating new tight edges without breaking existing ones.
4. Repeat until every vertex is matched.
5. The final potentials prove optimality (complementary slackness).

**Complexity:** O(n³).

**Agent use:**
- **Role:** Optimizer.
- **How:** Optimal one-to-one assignment: tasks to people by cost or skill score, jobs to machines, entity alignment pairs (K#133) with one-to-one constraints.
- **Rules:** For rectangular problems, pad with dummy rows or columns. For maximizing a score, negate it.
- **Guardrails:** Assignments affecting people are proposals (GR8, GX4).

### 86. Auction algorithm (Bertsekas)

**Definition:** Solving the assignment problem through a simulated auction where people bid for objects, adjusting prices.

**How it works:**
1. Every object has a price (starting at 0).
2. Each unassigned person finds the object with the best value (benefit − price) and the second best.
3. The person bids on the best object, raising its price by (best − second best + ε).
4. The object goes to the highest bidder. The previous owner becomes unassigned.
5. Repeat until everyone is assigned. ε-scaling (large ε first, then smaller) speeds it up. The result is within n × ε of optimal.

**Complexity:** Pseudo-polynomial. With ε-scaling, very fast in practice, and easy to parallelize.

**Agent use:**
- **Role:** Optimizer.
- **How:** Large assignment problems, especially sparse ones, and distributed settings where bids can be processed in parallel.
- **Rules:** Choose ε small enough for the required accuracy, and report the bound (GR4).
- **Guardrails:** None specific.

### 87. Edmonds' blossom algorithm (general graph matching)

**Definition:** Maximum matching in general (non-bipartite) graphs, handling the odd cycles ("blossoms") that break bipartite methods.

**How it works:**
1. Search for augmenting paths with alternating trees, as in bipartite matching.
2. When the search finds an odd cycle of alternating edges (a blossom), contract it into a single vertex.
3. Continue the search in the contracted graph.
4. When an augmenting path is found, expand the blossoms to recover the actual path in the original graph.
5. Weighted versions (with dual variables) solve maximum-weight matching.

**Complexity:** O(n² × m) basic. O(m √n) with the Micali-Vazirani algorithm (cardinality).

**Agent use:**
- **Role:** Optimizer.
- **How:** Pairing problems without two distinct sides: pairing people for reviews or mentoring, pairing tasks for co-scheduling, pairing items for merges.
- **Rules:** Use a tested library (blossom implementations are error-prone).
- **Guardrails:** Verify matching validity (no shared vertices) and size against an upper bound.

### 88. Stable matching (Gale-Shapley)

**Definition:** Matching two sides with preference lists so that no pair would both rather be matched with each other than with their current partners.

**How it works:**
1. Each free proposer proposes to the most preferred receiver it hasn't yet proposed to.
2. Each receiver tentatively keeps the best proposal it has received and rejects the others.
3. Rejected proposers continue down their lists.
4. Stop when all proposers are matched or have exhausted their lists.
5. The result is stable, and optimal for the proposing side among all stable matchings. Variants handle capacities (hospitals with several positions) and ties.

**Complexity:** O(n²).

**Agent use:**
- **Role:** Optimizer.
- **How:** Matching with preferences on both sides: candidates and teams, students and projects, services and hosts with affinity preferences.
- **Rules:** State which side proposes. It changes who benefits.
- **Guardrails:** Matches affecting people are proposals (GR8). Explain the procedure to the people affected.

### 89. Approximate and greedy weighted matching

**Definition:** Fast matchings that are provably within a factor of the best weight, for graphs too large for exact algorithms.

**How it works:**
1. **Greedy:** sort the edges by weight, descending. Take an edge if both endpoints are free. Gives at least half the optimal weight.
2. **Locally dominant edges (Preis):** an edge heavier than all adjacent edges can be matched safely. Linear time, and parallel-friendly (suitor algorithm).
3. **Path growing:** grow paths from vertices by picking the heaviest edges, then take the better of the two alternating edge sets.
4. Local improvement (short augmentations) brings results close to optimal.

**Complexity:** O(m log m) greedy, O(m) for the linear-time methods.

**Agent use:**
- **Role:** Optimizer.
- **How:** Matching inside graph coarsening (#175), large-scale deduplication pairing, and when exact algorithms don't scale.
- **Rules:** Report the approximation guarantee (GR4).
- **Guardrails:** None specific.

### 90. König's theorem (minimum vertex cover in bipartite graphs)

**Definition:** In bipartite graphs, the size of a maximum matching equals the size of a minimum vertex cover (a smallest vertex set touching every edge). The cover can be constructed from the matching.

**How it works:**
1. Find a maximum matching (#84).
2. From all unmatched left vertices, run an alternating BFS (unmatched edges from left to right, matched edges from right to left). Let Z be all vertices reached.
3. Minimum vertex cover = (left vertices not in Z) ∪ (right vertices in Z).
4. Its size equals the matching size, which certifies both results as optimal.

**Complexity:** O(m √n), dominated by the matching.

**Agent use:**
- **Role:** Optimizer and Verifier.
- **How:** The fewest resources touching every requirement, such as the fewest reviewers covering every module in a bipartite review graph. Also the certificate for #84.
- **Rules:** Present the cover with the matching as proof (GR6).
- **Guardrails:** The theorem holds only for bipartite graphs. In general graphs, vertex cover is NP-hard (#186).

### 91. Disjoint paths (Menger's theorem)

**Definition:** The maximum number of edge-disjoint (or vertex-disjoint) paths between two vertices equals the minimum number of edges (or vertices) that separate them.

**How it works:**
1. **Edge-disjoint:** give every edge capacity 1, and run max-flow from s to t. The flow value is the maximum number of edge-disjoint paths.
2. **Vertex-disjoint:** split each vertex v into v_in → v_out with capacity 1, then run max-flow.
3. Decompose the flow into paths by walking the edges with flow from s.
4. The corresponding min cut is the minimum separator.

**Complexity:** O(m √n) for unit-capacity flow with Dinic.

**Agent use:**
- **Role:** Analyst.
- **How:** Quantifies the redundancy between two points: "how many independent routes exist between these data centers?". The minimum separator shows the weak points.
- **Rules:** Report both the paths and the separator.
- **Guardrails:** None specific.

### 92. Multi-commodity flow

**Definition:** Routing several different flows (commodities), each with its own source, sink and demand, through shared capacities.

**How it works:**
1. Each commodity has its own flow variables. Shared edges must satisfy: the sum over commodities ≤ capacity.
2. Exact solutions use linear programming. Integer versions are NP-hard.
3. Large instances use column generation (path-based formulations) or decomposition methods.
4. Fast approximations: multiplicative weights / Garg-Könemann (repeatedly route along the currently cheapest paths, then increase the cost of congested edges).
5. Typical objectives: minimize cost, maximize throughput, or minimize maximum utilization.

**Complexity:** Polynomial as an LP. Approximation schemes are faster in practice.

**Agent use:**
- **Role:** Optimizer.
- **How:** Network traffic engineering, multi-tenant capacity planning, logistics with several product types.
- **Rules:** Use an LP or MIP solver for exact answers. Report the approximation gap for heuristics (GR4).
- **Guardrails:** Applying routing changes to live networks requires approval and staged rollout (GX4).

### 93. Graph cuts for labeling (Boykov-Kolmogorov, α-expansion)

**Definition:** Assigning labels to vertices by minimizing an energy function (data cost + smoothness cost), solved exactly or approximately with min cuts.

**How it works:**
1. **Energy:** E = Σ cost of each vertex's label + Σ penalty for neighboring vertices with different labels.
2. **Two labels:** build a graph with source and sink as the labels. Edges from source and sink to vertices carry the data costs; edges between neighbors carry the smoothness penalties. A minimum cut gives the optimal labeling (for submodular energies).
3. **Boykov-Kolmogorov max-flow:** grows search trees from both terminals and reuses them, which is very fast on grid-like graphs.
4. **Multiple labels (α-expansion):** repeatedly ask "should some vertices switch to label α?", a two-label problem, for each label in turn, until no improvement.

**Complexity:** Each expansion step is one max-flow. Usually converges in a few rounds.

**Agent use:**
- **Role:** Optimizer.
- **How:** Smoothing noisy per-vertex classifications using graph structure: spam versus legitimate accounts where neighbors tend to agree, segmentation, and denoising labels on knowledge graphs.
- **Rules:** Check that the smoothness term is a metric (needed for α-expansion's guarantees).
- **Guardrails:** Labels affecting people are proposals (GR8). Keep the per-vertex data costs visible for review.

### 94. Transportation problem and b-matching

**Definition:** Matching where vertices can have more than one partner (capacities b(v)), including shipping goods from suppliers to customers at minimum cost.

**How it works:**
1. **b-matching:** each vertex v can be matched up to b(v) times.
2. **Bipartite with costs (the transportation problem):** suppliers have supply, customers have demand, routes have unit costs.
3. Model it as min-cost flow (#81): source → suppliers (capacity = supply), suppliers → customers (cost per unit), customers → sink (capacity = demand).
4. Solve with min-cost flow or network simplex (#82).

**Complexity:** That of the min-cost flow method used.

**Agent use:**
- **Role:** Optimizer.
- **How:** Load distribution (requests to servers with capacities), reviewer assignment with load limits, inventory allocation.
- **Rules:** Check feasibility (total supply ≥ total demand) first.
- **Guardrails:** None specific.

## B6. Routing problems

### 95. Chinese postman (route inspection)

**Definition:** The shortest closed walk that traverses every edge at least once.

**How it works:**
1. If every vertex has even degree, an Euler circuit (#96) is optimal, with no repeated edges.
2. Otherwise, find the odd-degree vertices (there's always an even number of them).
3. Compute shortest paths between all pairs of odd vertices.
4. Find a minimum-weight perfect matching between the odd vertices (#87, weighted).
5. Duplicate the edges of the matched shortest paths, making all degrees even, then find an Euler circuit.
6. Directed versions use min-cost flow to balance in-degrees and out-degrees.

**Complexity:** Polynomial: all-pairs shortest paths between odd vertices, plus a weighted matching.

**Agent use:**
- **Role:** Optimizer.
- **How:** Covering every edge: inspection routes, test coverage of every transition in a state machine, crawling every link.
- **Rules:** Use the directed or mixed variant matching the problem (GR2).
- **Guardrails:** Mixed graphs (some directed, some undirected edges) make the problem NP-hard. Use heuristics, and label results as approximate.

### 96. Eulerian paths and circuits (Hierholzer's algorithm)

**Definition:** A walk that uses every edge exactly once (a circuit if it returns to the start).

**How it works:**
1. **Existence (undirected):** connected (ignoring isolated vertices), with 0 odd-degree vertices for a circuit or exactly 2 for a path. **Directed:** in-degree equals out-degree everywhere (circuit), or one vertex has one extra out-edge and one has one extra in-edge (path).
2. **Hierholzer:** start at a valid vertex and follow unused edges until stuck, pushing vertices on a stack.
3. When a vertex has no unused edges, pop it onto the output.
4. The output, reversed, is the Euler path or circuit.

**Complexity:** O(m).

**Agent use:**
- **Role:** Analyst and Optimizer.
- **How:** Sequence reconstruction (de Bruijn graphs, as in genome assembly), covering every transition exactly once in testing, and drawing a graph without lifting the pen.
- **Rules:** Check the existence conditions first, and report the violating vertices if they fail (GR6).
- **Guardrails:** None specific.

### 97. Held-Karp (exact TSP by dynamic programming)

**Definition:** Solving the traveling salesman problem exactly by dynamic programming over subsets of vertices.

**How it works:**
1. State: (S, j) = the shortest path that starts at vertex 1, visits exactly the vertices in set S, and ends at j.
2. C(S, j) = min over i ∈ S \ {j} of C(S \ {j}, i) + d(i, j).
3. Build up from small subsets to the full set.
4. The tour cost = min over j of C(all, j) + d(j, 1).
5. Store predecessors to reconstruct the tour.

**Complexity:** O(n² × 2ⁿ) time, O(n × 2ⁿ) memory. Practical up to about 20–25 vertices.

**Agent use:**
- **Role:** Optimizer.
- **How:** Exact optimal ordering for small sets: visiting a handful of sites, ordering a small batch of operations to minimize total switching cost.
- **Rules:** Refuse n above the GR3 limit, and switch to heuristics (#98).
- **Guardrails:** Memory grows as 2ⁿ. n = 30 is already over a billion states.

### 98. TSP heuristics (Christofides, 2-opt, Or-opt, Lin-Kernighan)

**Definition:** Practical algorithms that find near-optimal traveling salesman tours for large instances.

**How it works:**
1. **Construction:** nearest neighbor, greedy edge, or **Christofides** (MST + minimum-weight perfect matching on odd-degree vertices + Euler circuit + shortcut repeated vertices). Christofides guarantees ≤ 1.5× optimal for metric distances.
2. **2-opt:** remove two edges and reconnect the tour the other way when that's shorter. Repeat until no improving move exists.
3. **Or-opt:** move short segments (1–3 vertices) to better positions.
4. **Lin-Kernighan (LKH):** variable-depth sequences of edge exchanges, among the best practical heuristics.
5. **Lower bounds** (1-trees, Held-Karp LP bound) measure how close a tour is to optimal.

**Complexity:** 2-opt passes cost O(n²) each, faster with neighbor lists. LKH is very effective on large instances.

**Agent use:**
- **Role:** Optimizer.
- **How:** Route ordering for many stops, order picking, and sequencing operations to minimize total transition cost.
- **Rules:** Report the gap to a lower bound (GR4).
- **Guardrails:** Verify that the distances satisfy the triangle inequality if using Christofides' guarantee.

### 99. Vehicle routing heuristics (Clarke-Wright savings, local search)

**Definition:** Planning routes for several vehicles from a depot to serve customers, with capacities and often time windows.

**How it works:**
1. **Clarke-Wright savings:** start with one route per customer. For each pair (i, j), saving = d(depot, i) + d(depot, j) − d(i, j). Merge routes in order of descending savings, when capacity and route-end constraints allow.
2. **Local search improvements:** relocate a customer between routes, swap customers, 2-opt inside routes and 2-opt* between routes.
3. **Metaheuristics:** tabu search, simulated annealing, adaptive large neighborhood search (destroy and repair parts of the solution).
4. Constraints: vehicle capacity, time windows, maximum route duration, driver breaks.

**Complexity:** Savings O(n² log n). Local search and metaheuristics trade time for quality.

**Agent use:**
- **Role:** Optimizer.
- **How:** Field service, delivery and pickup planning, and assigning ordered job sequences to several workers.
- **Rules:** Use established solvers (OR-Tools, VROOM). Validate every constraint on the final routes.
- **Guardrails:** Routes affecting staff or customers are proposals (GR8), with constraint violations reported explicitly.

### 100. Maximum weight closure (project selection)

**Definition:** Choosing a set of items with maximum total value, where choosing an item requires choosing all of its prerequisites. It's solved exactly with a minimum cut.

**How it works:**
1. Items have values: profits positive, costs negative. Edges mean "selecting A requires selecting B".
2. Build a flow network: source → each positive item (capacity = its value), each negative item → sink (capacity = |its value|), prerequisite edges with infinite capacity.
3. Compute a minimum s-t cut (#77).
4. The source side of the cut is the optimal selection. Its value = total positive values − cut capacity.

**Complexity:** One max-flow.

**Agent use:**
- **Role:** Optimizer.
- **How:** Choosing which projects, features or migrations to do when each has prerequisites with costs: "which refactors give the most value, including the groundwork they require?"
- **Rules:** Values must be on one scale. Document how they were estimated.
- **Guardrails:** The result is a recommendation (GR8). Values are estimates, so show how sensitive the choice is to changes in them.

---
