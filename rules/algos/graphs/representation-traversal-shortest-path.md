This is a new reference: **320 advanced and critical graph algorithms**, in 7 parts. Same format as before, with one addition: a **Complexity** line, because for graph algorithms the cost often decides whether an algorithm is usable at all.

To avoid repeating earlier references, basics already covered in depth are cross-referenced (K# = knowledge graph reference, G# = glue reference) and only expanded where there's an important advanced variant.

**Map of all 320 entries:**
- **Part 1 (#1–50): Representations, traversal, shortest paths.**
- **Part 2 (#51–100): Connectivity, trees, flows, cuts, matching, routing problems.**
- **Part 3 (#101–150): Centrality, similarity, dense structures, network measures, random graph models.**
- **Part 4 (#151–200): Communities, partitioning, spectral methods, coloring, isomorphism, structural decompositions.**
- **Part 5 (#201–250): Dynamic, streaming, temporal, parallel and distributed graph processing.**
- **Part 6 (#251–300): Graph embeddings, advanced GNNs, probabilistic graphical models, causal graphs, program analysis on graphs.**
- **Part 7 (#301–320): Graphs in systems: scheduling, memory management, networking, layout, geometry, security.**

---

# Graph agent contract (referenced in every entry)

| Role | Job | Can write? |
|---|---|---|
| **Builder** | Constructs, transforms and indexes graph representations | Derived structures only |
| **Analyst** | Runs read-only computations: paths, centrality, communities, metrics | No |
| **Optimizer** | Solves optimization problems: flows, matching, routing, partitioning | No (produces proposals) |
| **Verifier** | Checks results with certificates, invariants and cross-checks | No |
| **Operator** | Applies approved results to real systems | Through approved plans only |

**Rules:**
- **GR1. Pin a snapshot:** every computation runs on a fixed graph version, recorded with the result.
- **GR2. Declare assumptions:** directed or undirected, weighted or not, negative weights allowed or not, multi-edges, self-loops. They're checked before running.
- **GR3. Estimate cost first:** compute the expected time and memory from |V|, |E| and the complexity, and refuse runs over budget.
- **GR4. Label exact versus approximate:** approximate results state their error bound or confidence.
- **GR5. Deterministic runs:** fixed seeds, fixed tie-breaking, recorded parameters.
- **GR6. Certificates where possible:** use results that prove themselves (a cut proving a flow is maximal, a negative cycle proving infeasibility) and verify them independently.
- **GR7. Bounded output:** result limits, and summaries before full results.
- **GR8. Results are proposals:** computed answers about real systems or people are acted on only through the Operator, with approval.

**Guardrails:**
- **GX1. Resource caps:** memory, time and visited-node limits for every algorithm.
- **GX2. Supernode protection:** degree-aware limits on expansion (K#180).
- **GX3. No sensitive inference:** don't infer protected attributes from structure (communities, similarity) without governance approval.
- **GX4. Human approval for actions:** routing changes, partition moves, fraud or risk flags, infrastructure changes.
- **GX5. Verify before trust:** run independent checks on results that drive decisions.

---

# PART 1: REPRESENTATIONS, TRAVERSAL AND SHORTEST PATHS

## A1. Representations and core structures

### 1. Adjacency matrix

**Definition:** A |V| × |V| matrix where entry (i, j) holds the edge weight (or 1) if an edge from i to j exists, and 0 otherwise.

**How it works:**
1. Number the vertices 0 to n−1.
2. Store an n × n array; set entry (i, j) for each edge. For undirected graphs, the matrix is symmetric.
3. Edge lookup is a single array access.
4. Matrix operations become graph operations: A² counts paths of length 2, and the eigenvalues give spectral properties (#176).
5. Bit-packed versions use one bit per entry for unweighted graphs.

**Complexity:** O(n²) memory regardless of edge count. O(1) edge lookup. O(n) to list neighbors.

**Agent use:**
- **Role:** Builder and Analyst.
- **How:** Used for small or dense graphs, and as the mathematical form behind spectral and algebraic algorithms (#176–182, #220).
- **Rules:** Use only when n is small (thousands) or the density is high.
- **Guardrails:** n = 1 million means 10¹² entries. GR3 cost estimation must reject that.

### 2. Compressed sparse row (CSR) and column (CSC)

**Definition:** A compact array layout for sparse graphs: all neighbors stored contiguously, plus an offset array per vertex. CSR stores out-neighbors; CSC stores in-neighbors.

**How it works:**
1. Sort the edges by source vertex.
2. A `targets` array holds every edge's destination, grouped by source.
3. An `offsets` array of size n + 1: vertex v's neighbors are `targets[offsets[v] … offsets[v+1])`.
4. Parallel arrays hold the edge weights and properties.
5. CSC is the same, grouped by destination, so in-neighbors are fast to list.

**Complexity:** O(n + m) memory. O(1) to find a vertex's neighbor range, then O(degree) to scan it. Updates are expensive (rebuild or batch).

**Agent use:**
- **Role:** Builder.
- **How:** The standard format for analytics: export a snapshot to CSR (and CSC for pull-based algorithms), then run traversals, PageRank, communities and embeddings on it. It's cache-friendly and fast.
- **Rules:** Build CSR from a pinned snapshot (GR1). Store the vertex ID mapping (internal index ↔ external ID).
- **Guardrails:** Integer overflow: use 64-bit offsets when m > 2³¹.

### 3. Edge list (COO format)

**Definition:** The simplest representation: a list of (source, target, weight) records.

**How it works:**
1. Each edge is one record.
2. It's easy to append, shard and stream.
3. Sorting by source gives CSR (#2); sorting by target gives CSC.
4. Edge-centric algorithms process the list sequentially (#224).

**Complexity:** O(m) memory. Finding a vertex's neighbors costs O(m) unless the list is sorted or indexed.

**Agent use:**
- **Role:** Builder.
- **How:** The universal interchange and ingestion format: load from files or streams as an edge list, deduplicate and validate, then convert to CSR or a graph database.
- **Rules:** Deduplicate edges and decide explicitly whether multi-edges are allowed (GR2).
- **Guardrails:** Validate that every endpoint exists. Dangling IDs cause silent errors downstream.

### 4. Incidence matrix and hypergraph representation

**Definition:** A vertex × edge matrix (or vertex × hyperedge matrix) marking which vertices belong to which edges. Hyperedges can connect any number of vertices.

**How it works:**
1. Rows are vertices, columns are edges or hyperedges.
2. Entry (v, e) = 1 if v is in e (for directed graphs: +1 at the head, −1 at the tail).
3. A hypergraph is often stored as a bipartite graph: vertex nodes, hyperedge nodes, and membership edges.
4. B·Bᵀ gives co-membership counts (weighted vertex adjacency).

**Complexity:** O(total membership count) memory in sparse form.

**Agent use:**
- **Role:** Builder.
- **How:** Represents many-to-many relations natively: meetings with several participants, transactions with several parties, documents with several authors. Pairwise edges lose that group structure.
- **Rules:** Keep the hyperedge as a first-class object, and project to pairwise edges only for algorithms that require it, recording the projection.
- **Guardrails:** Pairwise projection of large hyperedges creates huge cliques (k² edges). Cap it or weight it.

### 5. Dynamic adjacency structures (hash-set adjacency, packed memory arrays)

**Definition:** Representations that support fast edge insertions and deletions while keeping traversal reasonably fast.

**How it works:**
1. **Hash-set adjacency:** each vertex has a hash set of neighbors. O(1) expected insert, delete and lookup; slower scans than CSR.
2. **Sorted adjacency with gaps (packed memory array, PMA):** neighbors stay sorted in an array with empty slots. Inserts shift a few elements; gaps are rebalanced periodically.
3. **Blocked or B-tree adjacency:** neighbor lists stored in tree blocks.
4. **Hybrid:** a static CSR base plus a small mutable delta that's merged periodically (the LSM idea).

**Complexity:** Updates in O(1) to O(log² n) amortized, depending on the structure. Scans are slower than pure CSR.

**Agent use:**
- **Role:** Builder.
- **How:** For graphs updated continuously (live dependency graphs, transaction graphs), while analytics still need traversals.
- **Rules:** Use a base-plus-delta design. Compact when the delta exceeds a threshold.
- **Guardrails:** Analytics read a consistent version (GR1). Never read while a compaction is half done.

### 6. WebGraph compression (BV coding)

**Definition:** Compression for large graphs that exploits locality and similarity of neighbor lists, from the WebGraph framework (Boldi and Vigna).

**How it works:**
1. Order vertices so that similar vertices have nearby IDs (#12).
2. **Reference compression:** encode a vertex's neighbor list as "copy these entries from vertex v−r's list, plus these extras".
3. **Intervals:** runs of consecutive IDs are stored as (start, length).
4. **Gap encoding:** remaining neighbors are stored as small differences, with variable-length codes (ζ codes, Elias γ).
5. Neighbor lists are decoded on demand while traversing.

**Complexity:** Often a few bits per edge for web and social graphs. Decoding cost per neighbor is small but not zero.

**Agent use:**
- **Role:** Builder.
- **How:** Lets the agent analyze graphs with billions of edges on a single machine, in memory.
- **Rules:** Reorder vertices before compressing; compression depends heavily on the ordering.
- **Guardrails:** Random access to a single vertex is slower than with CSR. Use it for scan-heavy analytics.

### 7. k²-tree (succinct graph representation)

**Definition:** A compact tree representation of the adjacency matrix that recursively skips empty regions.

**How it works:**
1. Split the n × n matrix into k² equal submatrices.
2. Store one bit per submatrix: 1 if it contains any edge, 0 if it's empty.
3. Recursively subdivide only the nonempty submatrices, down to individual cells.
4. Store the bits level by level in bit arrays, with rank support for navigation.
5. Both out-neighbors (row queries) and in-neighbors (column queries) are supported by the same structure.

**Complexity:** Very compact for sparse, clustered graphs. Neighbor queries cost roughly O(degree × log n).

**Agent use:**
- **Role:** Builder.
- **How:** When both directions must be queryable with tight memory: large RDF or link graphs, read-only.
- **Rules:** Use for static graphs only.
- **Guardrails:** None specific.

### 8. Bitmap adjacency for dense subsets

**Definition:** Storing neighbor sets as bitmaps, so set operations (intersection, union) run at hardware speed.

**How it works:**
1. Each vertex's neighbor set is a bitset over vertex IDs, or a compressed bitmap such as Roaring.
2. Common neighbors = bitwise AND, then popcount.
3. Used selectively for high-degree vertices, while low-degree vertices stay as sorted lists.
4. Hybrid: choose the format per vertex by degree.

**Complexity:** Set intersection in O(n / 64) word operations for plain bitsets, much less with compressed bitmaps.

**Agent use:**
- **Role:** Analyst.
- **How:** Speeds up triangle counting (#125), clique search (#129), similarity measures (#117) and multi-source BFS (#48).
- **Rules:** Use bitmaps for dense or hub vertices, sorted lists for sparse ones.
- **Guardrails:** Uncompressed bitsets for every vertex cost O(n²) memory. Never do that on large graphs.

### 9. Graph reordering for cache locality (RCM, degree sort, Gorder)

**Definition:** Renumbering vertices so that vertices accessed together are stored close together in memory.

**How it works:**
1. **Degree sorting:** high-degree vertices first. Simple and effective for skewed graphs.
2. **Reverse Cuthill-McKee (RCM):** a BFS-based ordering that reduces the matrix bandwidth (keeps neighbors' IDs close).
3. **Gorder:** greedily places vertices sharing many neighbors next to each other, to maximize locality within a window.
4. **Community-based ordering:** vertices numbered community by community.
5. Rebuild CSR with the new numbering.

**Complexity:** Degree sort O(n log n). RCM O(m). Gorder is more expensive but often gives the biggest speedups.

**Agent use:**
- **Role:** Builder.
- **How:** One reordering speeds up every later analytics run, sometimes severalfold, because of fewer cache misses.
- **Rules:** Keep the permutation, so results map back to original IDs.
- **Guardrails:** Results must be reported in the original IDs. Mixing up numberings is a classic silent bug.

### 10. Vertex ID mapping (dictionary)

**Definition:** The two-way mapping between external identifiers (strings, UUIDs) and dense internal integer IDs.

**How it works:**
1. Assign dense integers 0 to n−1 to external IDs, by hash map or by sorting.
2. Store both directions: external → internal (hash map) and internal → external (array).
3. Algorithms run on the integers; results are translated back at output.
4. For persistent systems, the mapping is versioned with the snapshot.

**Complexity:** O(n) memory. O(1) expected lookups.

**Agent use:**
- **Role:** Builder.
- **How:** Required for every array-based algorithm (CSR, bitmaps, matrices). The agent always reports results with external IDs.
- **Rules:** The mapping is part of the snapshot (GR1).
- **Guardrails:** Never compare internal IDs across snapshots. The same integer may mean a different vertex.

### 11. Multigraph and property-graph indexing by edge type

**Definition:** Organizing each vertex's edges by type and direction, so typed traversals don't scan unrelated edges.

**How it works:**
1. Group each vertex's edges by (direction, edge type).
2. Store per-group offsets, or separate CSR structures per type.
3. A typed traversal ("follow only `WORKS_FOR` outgoing") reads only that group.
4. Keep degree counts per group for cost estimation.

**Complexity:** Slight extra overhead for the offsets. Typed traversal becomes O(typed degree) instead of O(total degree).

**Agent use:**
- **Role:** Builder and Analyst.
- **How:** Critical for knowledge graphs and supernodes: a hub with millions of edges of many types stays cheap to traverse for one rare type.
- **Rules:** Filter by type before expanding neighbors.
- **Guardrails:** Use per-type degree statistics in planning (GR3).

### 12. Hierarchical and multi-level graph representations

**Definition:** Representing a graph at several levels of detail, with coarse summary graphs above detailed ones.

**How it works:**
1. Coarsen the graph: merge groups of vertices (communities, matched pairs, #175) into super-vertices, and sum the edges between groups.
2. Repeat to build a hierarchy.
3. Each super-vertex keeps links to its members.
4. Algorithms can start on the coarse level and refine only in the relevant regions.

**Complexity:** Building costs about O(m) per level with matching-based coarsening.

**Agent use:**
- **Role:** Builder and Analyst.
- **How:** Enables multilevel partitioning (#170), fast overviews, coarse-to-fine search and route planning (#37).
- **Rules:** Record the coarsening method and level for each derived graph.
- **Guardrails:** Coarse levels lose detail. Never answer exact questions from coarse levels.

## A2. Traversal

### 13. Direction-optimizing BFS (Beamer's algorithm)

**Definition:** A BFS that switches between pushing from the frontier ("top-down") and pulling into unvisited vertices ("bottom-up"), depending on the frontier size.

**How it works:**
1. **Top-down step:** each frontier vertex checks its neighbors, and marks unvisited ones. Efficient when the frontier is small.
2. **Bottom-up step:** each unvisited vertex checks whether any of its neighbors is in the frontier, and stops at the first one found. Efficient when the frontier is large, since most checks end early.
3. A heuristic compares the frontier's edge count with the unvisited vertices' edge count, and switches modes.
4. On low-diameter graphs (social, web), the middle levels hold most of the graph, and bottom-up skips most of the edge checks.

**Complexity:** Still O(n + m) in the worst case, but often several times faster on real graphs.

**Agent use:**
- **Role:** Analyst.
- **How:** The fastest practical BFS for large analytics: reachability, distances, component discovery.
- **Rules:** Needs both out-edges and in-edges (CSR and CSC) for directed graphs.
- **Guardrails:** GX1 caps on visited vertices still apply.

### 14. Iterative DFS with edge classification

**Definition:** Depth-first search with an explicit stack that classifies every edge as a tree, back, forward or cross edge.

**How it works:**
1. Keep a stack of (vertex, next-neighbor index), so recursion isn't needed.
2. Record discovery and finish times for each vertex.
3. Classify each edge (u, v): **tree** (v undiscovered), **back** (v discovered but not finished, so it's an ancestor, which means a cycle), **forward** (v is a finished descendant), **cross** (otherwise).
4. Back edges prove cycles. Reverse finish order gives a topological order of a DAG.

**Complexity:** O(n + m) time. O(n) memory for the stack.

**Agent use:**
- **Role:** Analyst and Verifier.
- **How:** Cycle detection, topological ordering, and the base of SCC, bridges, articulation points and dominators (#53–60).
- **Rules:** Always iterative on large graphs, to avoid recursion stack overflow.
- **Guardrails:** None specific.

### 15. Iterative deepening DFS (IDDFS)

**Definition:** Repeated depth-limited DFS with increasing depth limits. It finds shallow targets with BFS-like guarantees using DFS-level memory.

**How it works:**
1. Run DFS limited to depth 0, then 1, 2, … until the target is found or the maximum depth is reached.
2. Each round restarts from the root.
3. Because levels grow quickly in branching graphs, most of the work is in the last round, so the repeated work is modest.
4. It finds a shortest path (fewest hops) like BFS, using O(depth) memory.

**Complexity:** O(b^d) time for branching factor b and depth d, with O(d) memory.

**Agent use:**
- **Role:** Analyst.
- **How:** Useful for path search in huge or implicitly defined graphs, such as state spaces in planning (G18), where BFS memory would explode.
- **Rules:** Always set a maximum depth.
- **Guardrails:** Use visited sets, or IDA* with a heuristic, on graphs with many cycles to avoid exponential re-exploration.

### 16. Lexicographic BFS (LexBFS)

**Definition:** A BFS variant that breaks ties using the order of previously visited neighbors, producing orderings with strong structural properties.

**How it works:**
1. Start with all vertices in one set.
2. Pick a vertex from the first set and output it.
3. Split every set into "neighbors of the picked vertex" (moved forward) and "non-neighbors" (partition refinement).
4. Repeat until every vertex is output.
5. The resulting order has special properties. For example, its reverse is a perfect elimination ordering exactly when the graph is chordal (#198).

**Complexity:** O(n + m) with partition refinement.

**Agent use:**
- **Role:** Analyst.
- **How:** Recognizes structured graph classes (chordal, interval, cographs), which allows fast exact algorithms that are hard in general (#196–198).
- **Rules:** Check the class with the certificate the recognition produces.
- **Guardrails:** None specific.

### 17. Level-synchronous parallel BFS

**Definition:** BFS that processes each level's frontier in parallel across threads or machines.

**How it works:**
1. The frontier for level d is a set or bitmap of vertices.
2. All threads expand frontier vertices at once, writing newly discovered vertices into the next frontier, using atomic test-and-set on the visited flags.
3. A barrier ends each level.
4. Frontiers switch between sparse lists and dense bitmaps by size (#222).
5. Distributed versions exchange frontier vertices between partitions each level (#225).

**Complexity:** O(n + m) work. The span is proportional to the diameter.

**Agent use:**
- **Role:** Analyst.
- **How:** The parallel workhorse behind distances, components and many analytics on multi-core machines and clusters.
- **Rules:** Combine with direction optimization (#13).
- **Guardrails:** High-diameter graphs (road networks) have many small levels, where parallelism helps little. Use other methods there (#38).

### 18. Random walks and walk sampling

**Definition:** Generating sequences of vertices by moving to random neighbors, used for estimation, sampling and embeddings.

**How it works:**
1. From the current vertex, choose the next one at random: uniformly, by edge weight, or by a biased rule (node2vec, #253 area).
2. Weighted choice uses prefix sums with binary search, or alias tables for O(1) sampling.
3. Repeat for the walk length.
4. Restart, teleport or stop rules define the variant (random walk with restart, K#69).
5. Many walks run in parallel.

**Complexity:** O(walk length) per walk, with O(1) sampling per step using alias tables.

**Agent use:**
- **Role:** Analyst.
- **How:** The base of PageRank estimation (#104), embeddings, graph sampling (#150) and similarity measures.
- **Rules:** Fix seeds (GR5) and record walk parameters.
- **Guardrails:** Walks get trapped in dangling vertices and sink components. Define teleport behavior.

### 19. Euler tour technique

**Definition:** Turning a tree into a sequence by walking around it (each edge traversed down and up), so tree questions become array questions.

**How it works:**
1. Run a DFS, recording each vertex when it's entered and when it's left, giving a sequence of length 2n−1 or 2n.
2. A vertex's subtree is a contiguous range in that sequence.
3. Subtree queries (sums, counts) become range queries, answered with prefix sums or segment trees.
4. Lowest common ancestor becomes a range-minimum query over depths (#67).

**Complexity:** O(n) to build. Fast range queries afterwards.

**Agent use:**
- **Role:** Analyst.
- **How:** Fast subtree aggregation on hierarchies (org charts, category trees, file trees), such as "total size of everything under this folder".
- **Rules:** Rebuild after structural changes, or use Euler tour trees (#71) for dynamic trees.
- **Guardrails:** None specific.

### 20. Topological sort and longest-path layering on DAGs

**Definition:** Ordering a DAG's vertices so every edge points forward, and assigning layers by longest path.

**How it works:**
1. **Topological order:** Kahn's algorithm (G9) or reverse DFS finish order (#14).
2. **Layering:** process vertices in topological order, setting each vertex's layer = 1 + the maximum layer of its predecessors.
3. Vertices in the same layer have no dependencies on each other, so they can be processed in parallel.
4. Remaining vertices when the queue empties prove a cycle.

**Complexity:** O(n + m).

**Agent use:**
- **Role:** Analyst and Builder.
- **How:** Scheduling, build orders, pipeline stages, and drawing hierarchies (#316).
- **Rules:** Use deterministic tie-breaking (GR5).
- **Guardrails:** Report the cycle found, not just "not a DAG". The cycle is the certificate (GR6).

### 21. Cycle detection and cycle enumeration (Johnson's algorithm)

**Definition:** Detecting whether cycles exist, and listing all elementary cycles when needed.

**How it works:**
1. **Detection:** DFS back edges (directed, #14), or union-find seeing an edge between two vertices already in one component (undirected).
2. **Enumeration (Johnson's algorithm):** for each start vertex s (in order), search within the strongly connected component containing s, using only vertices numbered ≥ s. A blocking mechanism prevents re-exploring vertices that can't currently lead back to s.
3. Each elementary cycle is output exactly once.

**Complexity:** Detection O(n + m). Enumeration O((n + m)(c + 1)) for c cycles, and c can be exponential.

**Agent use:**
- **Role:** Analyst and Verifier.
- **How:** Detection: dependency cycles, circular ownership. Enumeration: small fraud loops (money cycling through accounts), circular references.
- **Rules:** For enumeration, always bound the cycle length and the count.
- **Guardrails:** Unbounded enumeration on dense graphs never finishes (GX1).

### 22. Bipartiteness testing (2-coloring)

**Definition:** Deciding whether vertices can be split into two groups with every edge crossing between the groups.

**How it works:**
1. BFS from each uncolored vertex, giving it color 0.
2. Give each neighbor the opposite color.
3. If an edge connects two vertices of the same color, the graph isn't bipartite. That edge plus the BFS tree paths form an odd cycle, which is the certificate.
4. Otherwise, the coloring is the bipartition.

**Complexity:** O(n + m).

**Agent use:**
- **Role:** Verifier.
- **How:** Validates data models that should be bipartite (users–items, authors–papers). An odd cycle indicates a data error.
- **Rules:** Report the odd cycle as evidence (GR6).
- **Guardrails:** None specific.

## A3. Shortest paths

### 23. Dijkstra with advanced priority queues

**Definition:** Dijkstra's algorithm (K#66) implemented with the priority queue best suited to the graph.

**How it works:**
1. **Binary heap:** O((n + m) log n). Simple, and the usual default.
2. **Lazy deletion:** push duplicate entries instead of decrease-key, and skip stale entries when popped. Simpler and often faster in practice.
3. **Fibonacci or pairing heaps:** O(m + n log n) in theory. Pairing heaps are often good in practice; Fibonacci heaps rarely are.
4. **Radix heaps:** for integer weights, O(m + n log C), where C is the maximum weight.
5. **Bucket queues** (Dial, #30) for small integer weights.

**Complexity:** As listed above, depending on the queue.

**Agent use:**
- **Role:** Analyst.
- **How:** Pick the queue by weight type and graph size; the right choice can halve the runtime.
- **Rules:** Verify that weights are non-negative before running (GR2).
- **Guardrails:** With negative weights, Dijkstra returns wrong answers silently. Reject the input.

### 24. Bellman-Ford with negative cycle detection

**Definition:** Shortest paths with negative edge weights allowed, which also detects negative cycles.

**How it works:**
1. Set the source distance to 0 and every other distance to ∞.
2. Repeat n−1 times: relax every edge (if d[u] + w < d[v], update d[v] and record u as v's predecessor).
3. Run one more round. If any distance still improves, a negative cycle is reachable from the source.
4. Follow predecessors from an improved vertex n times to land inside the cycle, then extract the cycle.
5. Early exit: stop when a round changes nothing.

**Complexity:** O(n × m).

**Agent use:**
- **Role:** Analyst and Verifier.
- **How:** Handles graphs with costs and gains, such as currency exchange (log-rate edges, where a negative cycle means an arbitrage opportunity), and constraint systems of the form x_v − x_u ≤ w (difference constraints).
- **Rules:** Report the actual negative cycle as the certificate (GR6).
- **Guardrails:** Slow on large graphs. Use Johnson's reweighting (#26) when you need many sources.

### 25. SPFA (queue-based Bellman-Ford)

**Definition:** A Bellman-Ford variant that only re-processes vertices whose distance just changed.

**How it works:**
1. Put the source in a queue.
2. Take a vertex, relax its outgoing edges, and add every improved neighbor to the queue if it isn't already there.
3. Count how many times each vertex is added. A count reaching n means there's a negative cycle.
4. Heuristics: small-label-first and large-label-last queue ordering.

**Complexity:** Worst case O(n × m), like Bellman-Ford, and adversarial inputs reach it. Often much faster on real data.

**Agent use:**
- **Role:** Analyst.
- **How:** A practical speedup when negative weights exist but are rare.
- **Rules:** Always keep the negative-cycle counter.
- **Guardrails:** Never assume the average-case speed. Set time caps (GX1).

### 26. Johnson's algorithm (all-pairs with reweighting)

**Definition:** All-pairs shortest paths on sparse graphs with negative weights, by reweighting so that Dijkstra can be used.

**How it works:**
1. Add a new vertex q with zero-weight edges to every vertex.
2. Run Bellman-Ford from q to get a potential h(v) for each vertex. A negative cycle stops the algorithm here.
3. Reweight every edge: w′(u, v) = w(u, v) + h(u) − h(v). The new weights are all non-negative, and shortest paths are preserved.
4. Run Dijkstra from every vertex with the new weights.
5. Convert back: d(u, v) = d′(u, v) − h(u) + h(v).

**Complexity:** O(n × m log n) total.

**Agent use:**
- **Role:** Analyst.
- **How:** All-pairs distances for sparse graphs with negative weights. The same potential trick speeds up min-cost flow (#81).
- **Rules:** Store the potentials with the result, for later reuse.
- **Guardrails:** The output has n² entries. Compute only the pairs actually needed (GR7).

### 27. Floyd-Warshall

**Definition:** All-pairs shortest paths by dynamic programming over intermediate vertices.

**How it works:**
1. Start with D[i][j] = the edge weight, or ∞, with D[i][i] = 0.
2. For each vertex k: for every pair (i, j), D[i][j] = min(D[i][j], D[i][k] + D[k][j]).
3. After processing all k, D holds every shortest distance.
4. A negative D[i][i] means a negative cycle.
5. A next-hop matrix records the paths for reconstruction.

**Complexity:** O(n³) time, O(n²) memory.

**Agent use:**
- **Role:** Analyst.
- **How:** Simple and robust for small dense graphs (up to a few thousand vertices). Also computes transitive closure (with boolean operations).
- **Rules:** Use only after a GR3 cost check.
- **Guardrails:** n = 100,000 means 10¹⁵ operations: reject.

### 28. Shortest and longest paths in DAGs

**Definition:** Linear-time path optimization on acyclic graphs, by processing vertices in topological order.

**How it works:**
1. Compute a topological order (#20).
2. Process vertices in that order, relaxing all outgoing edges.
3. Shortest paths work with any weights, including negative ones.
4. **Longest paths:** negate the weights, or use max instead of min. This is NP-hard in general graphs but easy in DAGs.
5. Predecessor links reconstruct the paths.

**Complexity:** O(n + m).

**Agent use:**
- **Role:** Analyst.
- **How:** Critical path analysis in task graphs (#302), build and pipeline duration estimates, and dynamic programming over dependency graphs.
- **Rules:** Verify acyclicity first. The cycle check is a certificate (#20).
- **Guardrails:** None specific.

### 29. 0-1 BFS

**Definition:** Shortest paths when edge weights are only 0 or 1, using a double-ended queue instead of a priority queue.

**How it works:**
1. Start with the source in a deque.
2. Pop from the front.
3. For each edge: if its weight is 0 and it improves the neighbor's distance, push the neighbor to the front; if its weight is 1 and it improves, push to the back.
4. The deque stays sorted by distance, so it works like Dijkstra without heap overhead.

**Complexity:** O(n + m).

**Agent use:**
- **Role:** Analyst.
- **How:** Problems with free and costly moves: "minimum number of risky hops", "minimum number of edge reversals", or paths where only some edge types cost anything.
- **Rules:** Verify that weights are only 0 or 1.
- **Guardrails:** None specific.

### 30. Dial's algorithm (bucket queue)

**Definition:** Dijkstra using an array of buckets indexed by distance, for small integer weights.

**How it works:**
1. Make buckets for distances 0 to (n−1) × C, or use circular buckets of size C + 1.
2. Put each vertex in the bucket for its current distance.
3. Scan the buckets in increasing order, processing every vertex found and relaxing its edges.
4. Moving a vertex between buckets is O(1).

**Complexity:** O(m + n × C).

**Agent use:**
- **Role:** Analyst.
- **How:** Very fast when weights are small integers (hop counts with small penalties, discrete costs).
- **Rules:** Use only when C is small.
- **Guardrails:** Large C makes memory and scanning expensive. Check C first.

### 31. Bidirectional Dijkstra

**Definition:** Point-to-point shortest path by running Dijkstra forward from the source and backward from the target at the same time.

**How it works:**
1. Run a forward search from s and a backward search from t (on reversed edges).
2. Alternate steps, usually expanding the side with the smaller frontier key.
3. Track the best path found so far: the minimum over edges (u, v) of d_forward(u) + w + d_backward(v).
4. Stop when the two frontiers' minimum keys sum to at least the best path found.
5. Each side explores roughly a radius of half the distance, which is much less area in large graphs.

**Complexity:** In practice, often a fraction of one-sided Dijkstra's work.

**Agent use:**
- **Role:** Analyst.
- **How:** The base for fast point-to-point queries, and the search component used inside contraction hierarchies (#33).
- **Rules:** Use the correct stopping condition. Stopping at the first meeting vertex is a common bug that gives non-optimal paths.
- **Guardrails:** None specific.

### 32. ALT (A*, landmarks, triangle inequality)

**Definition:** A* search with lower bounds computed from precomputed distances to a few landmark vertices.

**How it works:**
1. **Preprocessing:** choose k landmarks (spread out, often with farthest-first selection). Store the distances from and to every landmark for every vertex.
2. **Lower bound:** for a vertex v and target t, the triangle inequality gives d(v, t) ≥ max over landmarks L of |d(L, t) − d(L, v)| (with the directional variants).
3. Use that bound as the A* heuristic (K#67). It's admissible, so the result is optimal.
4. More, and better placed, landmarks give tighter bounds and fewer explored vertices.

**Complexity:** O(k × n) preprocessing memory. Queries explore far fewer vertices than Dijkstra.

**Agent use:**
- **Role:** Analyst.
- **How:** Fast exact queries on graphs where other speedup techniques don't fit, and it's simple to update when weights change (only the landmark distances are recomputed).
- **Rules:** Recompute landmark distances after weight changes.
- **Guardrails:** Stale landmark distances can make the heuristic inadmissible, giving wrong answers. Version them with the graph (GR1).

### 33. Contraction Hierarchies (CH)

**Definition:** A preprocessing technique that orders vertices by importance and adds shortcut edges, so queries only go "upward" in importance and touch very few vertices.

**How it works:**
1. **Order vertices by importance**, using heuristics like edge difference (shortcuts added minus edges removed), contracted neighbors and search space depth.
2. **Contract vertices in that order:** remove the vertex. For each pair of its neighbors whose shortest path ran through it, add a shortcut edge with the combined weight. A local "witness search" checks whether another path is equally short, in which case no shortcut is needed.
3. **Query:** bidirectional Dijkstra where both sides only follow edges toward more important vertices. They meet at the top.
4. **Unpacking:** shortcuts are expanded recursively to recover the real path.

**Complexity:** Preprocessing takes minutes for continental road networks. Queries take microseconds to milliseconds, touching only hundreds of vertices.

**Agent use:**
- **Role:** Analyst.
- **How:** The industry standard for road and logistics routing. Use it whenever there are many point-to-point queries on a mostly static graph.
- **Rules:** Re-preprocess when the graph or weights change (or use CRP, #37, when weights change often).
- **Guardrails:** Works best on hierarchical graphs like road networks. Social graphs produce too many shortcuts. Measure first.

### 34. Hub labeling

**Definition:** Precomputing for each vertex a small label of (hub, distance) pairs, so the distance between any two vertices comes from their labels alone.

**How it works:**
1. Each vertex v stores L(v) = a set of (hub, distance-to-hub) pairs.
2. **Cover property:** for every pair (s, t), some hub on a shortest s–t path appears in both labels.
3. **Query:** d(s, t) = min over common hubs h of d(s, h) + d(h, t). That's a merge of two sorted lists.
4. Labels are commonly built from a CH order (#33), or by pruned landmark labeling, which runs BFS or Dijkstra from vertices in order of importance and prunes visits already covered by earlier labels.

**Complexity:** Queries in microseconds or less. Memory can be large: label size times n.

**Agent use:**
- **Role:** Analyst.
- **How:** The fastest known exact distance queries on road networks, and also used for reachability (K#71).
- **Rules:** Measure the label sizes before committing memory.
- **Guardrails:** Rebuild after graph changes. Labels have no partial-update guarantee unless the algorithm supports it.

### 35. Transit node routing

**Definition:** Precomputing distances between a small set of "transit" vertices that almost every long route passes through.

**How it works:**
1. Choose transit vertices: important vertices that long-distance shortest paths pass through (top levels of a CH, for example).
2. For each vertex, store its few "access" transit vertices and the distances to them.
3. Precompute a table of distances between all pairs of transit vertices.
4. **Long queries:** d(s, t) = min over access pairs of d(s, a) + table(a, b) + d(b, t).
5. **Short (local) queries:** detected by a locality filter and answered with another method (CH).

**Complexity:** Extremely fast long-distance queries. Large preprocessing and memory cost.

**Agent use:**
- **Role:** Analyst.
- **How:** For extremely high query volumes of long-distance routes (logistics planning).
- **Rules:** Always pair it with a correct local-query method.
- **Guardrails:** The locality filter must be correct, or short queries return wrong results.

### 36. Arc flags

**Definition:** Precomputing, for each edge and each region of the graph, whether the edge lies on some shortest path into that region.

**How it works:**
1. Partition the graph into k regions.
2. For each edge, store k bits: bit r is 1 if the edge starts some shortest path to a vertex in region r.
3. **Query to target t in region r:** run Dijkstra, ignoring edges whose bit r is 0.
4. Computing the flags requires shortest-path trees from the boundary vertices of each region.

**Complexity:** Heavy preprocessing. k bits per edge. Queries explore only the relevant corridor.

**Agent use:**
- **Role:** Analyst.
- **How:** Effective goal-directed pruning, often combined with other techniques (CH plus arc flags).
- **Rules:** Use partitions with small boundaries (#170).
- **Guardrails:** Changing edge weights invalidates the flags.

### 37. Customizable Route Planning (CRP, multilevel overlay graphs)

**Definition:** A routing technique that separates the stable structure (preprocessed once) from frequently changing weights (applied quickly in a "customization" step).

**How it works:**
1. **Metric-independent preprocessing:** partition the graph into a multilevel hierarchy of cells with small boundaries (#170).
2. **Customization:** for each cell, compute the shortest distances between its boundary vertices under the current weights, giving "clique" overlay edges. This runs in seconds and can be parallelized per cell.
3. **Query:** bidirectional Dijkstra that uses detailed edges near the source and target, and overlay edges in between, going up and down the levels.
4. When weights change (traffic, closures), only the customization is re-run.

**Complexity:** Customization in seconds. Queries in milliseconds. Supports frequent weight changes.

**Agent use:**
- **Role:** Analyst and Operator.
- **How:** The choice for production routing with live costs (traffic, dynamic pricing, live latency in network graphs).
- **Rules:** Version the customized metric (GR1) and record the weight snapshot used for each result.
- **Guardrails:** Partial customization failures must fail the whole update. Never mix old and new cell metrics.

### 38. Delta-stepping (parallel single-source shortest paths)

**Definition:** A parallel shortest-path algorithm that processes buckets of vertices with similar distances at the same time.

**How it works:**
1. Choose a bucket width Δ. Bucket i holds vertices with tentative distances in [iΔ, (i+1)Δ).
2. Process the lowest non-empty bucket. First relax its "light" edges (weight ≤ Δ) in parallel, repeatedly, since they can add vertices back into the same bucket.
3. Then relax its "heavy" edges (weight > Δ) once, in parallel. They can only reach later buckets.
4. Move on to the next bucket.
5. Δ trades parallelism (large Δ) against wasted re-relaxations (small Δ).

**Complexity:** Good parallel performance on many graphs. Work depends on Δ and the weight distribution.

**Agent use:**
- **Role:** Analyst.
- **How:** Shortest paths on large graphs using many cores or GPUs, as in the Graph500 SSSP benchmark.
- **Rules:** Tune Δ on a sample of the graph.
- **Guardrails:** Results must match a sequential Dijkstra on test cases (GX5).

### 39. Eppstein's k shortest paths

**Definition:** Finding the k shortest paths between two vertices, allowing repeated vertices (walks), efficiently.

**How it works:**
1. Compute the shortest-path tree to the target (reverse Dijkstra).
2. Every non-tree edge (u, v) has a "detour cost": d(u, v edge) + d(v, t) − d(u, t).
3. Any path corresponds to a sequence of detours (sidetracks) from the tree.
4. Build a heap structure over the sidetracks reachable along each tree path, shared persistently between vertices.
5. Explore this heap in increasing cost order to produce paths one by one.

**Complexity:** O(m + n log n + k) after preprocessing.

**Agent use:**
- **Role:** Analyst.
- **How:** Many alternative routes quickly. If loop-free paths are required, use Yen's algorithm (K#68) or filter the results.
- **Rules:** State whether loops are allowed (GR2).
- **Guardrails:** Many of the k paths may be near-identical. Apply diversity filtering for presentation.

### 40. Suurballe / Bhandari (disjoint shortest paths)

**Definition:** Finding two (or k) paths between two vertices that share no edges (or no vertices), with minimum total length.

**How it works:**
1. Find a shortest path P1 with Dijkstra.
2. Reweight the edges with potentials (making them non-negative), and reverse the edges of P1 with negated weight in a residual graph.
3. Find a shortest path P2 in this modified graph.
4. Combine P1 and P2, cancelling edges used in opposite directions. The result is two disjoint paths with minimum total length.
5. For vertex-disjoint paths, split each vertex into an in-node and an out-node joined by a capacity-1 edge.
6. This is a special case of min-cost flow (#81) with flow value 2.

**Complexity:** About two Dijkstra runs.

**Agent use:**
- **Role:** Optimizer.
- **How:** Designing redundant routes: backup network paths, failover routing, resilient supply chains.
- **Rules:** Verify disjointness of the result explicitly (GR6).
- **Guardrails:** If two disjoint paths don't exist, report the single point of failure (the cut, #77).

### 41. Resource-constrained shortest path (label-setting with dominance)

**Definition:** Shortest paths subject to limits on additional resources (time, fuel, budget, number of hops). This is NP-hard in general, but solved well in practice.

**How it works:**
1. Each partial path is a label at its end vertex: (cost, resource 1 used, resource 2 used, …).
2. Extend labels along edges, adding costs and resources. Discard labels that exceed a resource limit.
3. **Dominance:** at a vertex, a label is discarded if another label is at least as good in every dimension.
4. Process labels in order of cost (label setting) until the target's best label is final.
5. Preprocessing bounds (shortest possible remaining resource use to the target) prune labels early.

**Complexity:** Exponential in the worst case. Dominance makes it practical in many real cases.

**Agent use:**
- **Role:** Optimizer.
- **How:** Routing with constraints: "cheapest route arriving before 9:00", "fastest path within a budget", "shortest path with at most 3 transfers".
- **Rules:** Cap the number of labels per vertex and overall (GX1).
- **Guardrails:** If the cap is hit, return the best feasible solution found so far, clearly marked as not proven optimal (GR4).

### 42. Multi-criteria (Pareto) shortest paths

**Definition:** Finding all paths that are not worse in every criterion than another path: the Pareto front of trade-offs.

**How it works:**
1. Labels hold vectors of criteria (time, cost, risk).
2. Extend them like #41. At each vertex, keep all non-dominated labels (the Pareto set).
3. The target's final label set is the Pareto front of trade-offs.
4. Speedups: target pruning, bounding with single-criterion distances, and approximations (ε-dominance) that merge similar labels.

**Complexity:** The Pareto front can be exponential. ε-approximation keeps it manageable.

**Agent use:**
- **Role:** Optimizer.
- **How:** Presents real trade-offs to people ("fastest", "cheapest", "balanced") instead of collapsing everything into one weighted score.
- **Rules:** Present a limited, diverse subset of the Pareto front.
- **Guardrails:** Cap the label counts (GX1).

### 43. Time-dependent shortest paths

**Definition:** Shortest paths where an edge's travel time depends on when you enter it (traffic, timetables, network congestion).

**How it works:**
1. Each edge has a travel-time function f(t), for example piecewise linear over the day.
2. **FIFO property:** leaving later never makes you arrive earlier. With it, time-dependent Dijkstra works: arrival = departure + f(departure).
3. **Earliest arrival:** a Dijkstra-like search on arrival times.
4. **Profile queries:** compute arrival time as a function of departure time over an interval, by propagating functions instead of numbers (more expensive).
5. Time-dependent variants of CH and other speedups exist.

**Complexity:** Like Dijkstra for single departure times. Profile queries are much heavier.

**Agent use:**
- **Role:** Analyst and Optimizer.
- **How:** Accurate travel or processing-time estimates when conditions vary by time of day.
- **Rules:** Verify the FIFO property of the input functions, and fix violations.
- **Guardrails:** Without FIFO, Dijkstra-style algorithms give wrong answers. Waiting must be modeled explicitly then.

### 44. Widest path (maximum bottleneck path)

**Definition:** The path whose smallest edge capacity is as large as possible.

**How it works:**
1. A Dijkstra variant: path value = minimum edge capacity along it. Maximize instead of minimizing.
2. Use a max-heap. Extending a path takes the min of its value and the edge capacity.
3. **Alternative:** in the maximum spanning tree (#61 with weights reversed), the unique path between two vertices is a widest path.

**Complexity:** O(m log n).

**Agent use:**
- **Role:** Optimizer.
- **How:** Bandwidth routing (the path that can carry the most traffic), the most reliable path (with multiplicative reliabilities converted using logs), and capacity planning.
- **Rules:** Be clear about which quantity is the bottleneck.
- **Guardrails:** None specific.

### 45. Karp's minimum mean cycle

**Definition:** Finding the cycle with the smallest average edge weight.

**How it works:**
1. Compute D_k(v) = the minimum weight of a walk with exactly k edges ending at v, for k = 0 to n, by dynamic programming from an added source.
2. The minimum mean cycle value is min over v of max over k of (D_n(v) − D_k(v)) / (n − k).
3. The cycle itself is recovered from the DP's predecessor information.
4. Faster in practice: Howard's policy iteration.

**Complexity:** O(n × m).

**Agent use:**
- **Role:** Analyst.
- **How:** Throughput and cycle-time analysis of processes (the bottleneck cycle in a dataflow or scheduling loop), and canceling cycles in min-cost flow algorithms.
- **Rules:** Report the cycle with its mean value (GR6).
- **Guardrails:** None specific.

### 46. Thorup-Zwick distance oracles

**Definition:** A compact structure that answers approximate distance queries between any two vertices quickly, with a guaranteed error bound.

**How it works:**
1. Pick nested random samples of vertices: A₀ = V ⊇ A₁ ⊇ … ⊇ A_k, each level sampling about n^(−1/k) of the previous one.
2. For each vertex, store its "bunch": the vertices of each level that are closer to it than the nearest vertex of the next level, with exact distances.
3. **Query:** walk up the levels, alternating between the two endpoints, until finding a vertex in the other endpoint's bunch.
4. The answer is at most (2k−1) times the true distance (its stretch).
5. Memory is about O(k × n^(1+1/k)).

**Complexity:** Query in O(k). Trades memory against accuracy through k.

**Agent use:**
- **Role:** Analyst.
- **How:** Approximate distances when exact all-pairs is impossible: similarity estimates and proximity features on large graphs.
- **Rules:** Always report the stretch bound with the result (GR4).
- **Guardrails:** Never use approximate distances where exactness matters (billing, safety-critical routing).

### 47. Seidel's algorithm (all-pairs for unweighted graphs via matrix multiplication)

**Definition:** All-pairs shortest path lengths in unweighted undirected graphs, using fast matrix multiplication recursively.

**How it works:**
1. Compute A² to build the "square graph" (vertices linked if they're within distance 2).
2. Recursively solve all-pairs on the square graph, which has about half the diameter.
3. Recover the true distances from the recursive result using one more matrix product and parity checks.
4. Recursion depth is about log(diameter).

**Complexity:** O(M(n) log n), where M(n) is the matrix multiplication cost.

**Agent use:**
- **Role:** Analyst.
- **How:** All-pairs distances on dense, unweighted graphs of moderate size, using optimized matrix libraries or GPUs.
- **Rules:** Use only after a GR3 check, since n² memory is required.
- **Guardrails:** Not for sparse large graphs. Use BFS from each source (#48) instead.

### 48. Multi-source bit-parallel BFS (MS-BFS)

**Definition:** Running many BFS searches at once, using one bit per search in each vertex's state.

**How it works:**
1. For up to 64 (or more, with wider SIMD) sources, each vertex keeps bitmasks: `seen` and `visit`, where bit i belongs to source i.
2. Each step: for every vertex with a nonzero `visit` mask, OR its mask into its neighbors' `next` masks, excluding bits already in their `seen` masks.
3. Bits newly set in a vertex's mask record its distance from the corresponding sources.
4. Many searches share the same memory accesses, which is much faster than separate runs.

**Complexity:** About the cost of a few BFS runs for 64 sources.

**Agent use:**
- **Role:** Analyst.
- **How:** Closeness centrality, all-pairs on samples, landmark preprocessing (#32) and multi-seed reachability, all accelerated.
- **Rules:** Group sources in batches matching the bit width.
- **Guardrails:** None specific.

### 49. Temporal path queries (earliest arrival, Connection Scan Algorithm)

**Definition:** Finding paths that respect time order (each step must start after the previous one ends), as in transit timetables or event logs.

**How it works:**
1. Model connections as (from, to, departure, arrival) records, sorted by departure time.
2. **Connection Scan Algorithm (CSA):** scan the connections in departure order. A connection is usable if its departure is at or after the current earliest arrival at its starting stop. If so, update the earliest arrival at its destination.
3. One linear pass gives the earliest arrival everywhere.
4. Profile variants compute arrivals for every departure time, by scanning in reverse.
5. Foremost, fastest and shortest temporal paths are related variants.

**Complexity:** O(number of connections) for earliest arrival.

**Agent use:**
- **Role:** Analyst.
- **How:** Time-respecting reachability: transit planning, and also "could this information or infection have spread from A to B, given when the contacts happened?"
- **Rules:** Sort by time once, and keep the data sorted.
- **Guardrails:** Ignoring time order overstates reachability. Never use static paths for temporal questions.

### 50. RAPTOR (round-based public transit routing)

**Definition:** A transit routing algorithm that finds the best journeys for each number of transfers, working on routes and trips without a priority queue.

**How it works:**
1. Round k computes the earliest arrival at each stop using at most k trips.
2. In each round, collect the routes serving stops that improved in the previous round.
3. Scan each such route once along its stop sequence: track the earliest catchable trip, and update arrivals at later stops.
4. Add footpath transfers after each round.
5. The result is a Pareto set of journeys over (arrival time, number of transfers).
6. Extensions: range queries over departure windows, more criteria (fare, walking).

**Complexity:** Fast in practice, with good cache behavior. Easy to parallelize.

**Agent use:**
- **Role:** Optimizer.
- **How:** Multi-modal and schedule-based routing, and any domain with timed "vehicle" services and transfers (batch pipelines with fixed schedules, for example).
- **Rules:** Present Pareto options (fewer transfers versus earlier arrival).
- **Guardrails:** Timetable data must be validated (no time-travel trips, consistent stop IDs).

---

Part 2 (#51–100) covers union-find in depth, dynamic connectivity, bridges and articulation points, biconnected and triconnected components (SPQR trees), dominator trees, spanning trees and arborescences, Steiner trees, tree algorithms (LCA, heavy-light, centroid and link-cut trees), maximum flow (Dinic, push-relabel), minimum cuts (Stoer-Wagner, Karger, Gomory-Hu), min-cost flow, matching (Hopcroft-Karp, Hungarian, blossom, auction, stable matching), and routing problems (Euler, Chinese postman, Held-Karp, TSP and vehicle routing heuristics).
