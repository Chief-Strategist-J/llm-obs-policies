# Part 5: Dynamic, streaming, temporal, parallel and distributed graph processing (#201–250)

Same format and the same contract (roles; rules GR1–GR8; guardrails GX1–GX5).

## E1. Dynamic graph algorithms

### 201. Dynamic single-source shortest paths (Ramalingam-Reps)

**Definition:** Updating shortest-path distances from a source after edge insertions, deletions or weight changes, touching only the affected vertices.

**How it works:**
1. Keep the current distances and the shortest-path tree (or DAG).
2. **Edge decrease or insertion (u, v):** if d(u) + w < d(v), run a Dijkstra-like propagation starting at v, updating only the vertices whose distance improves.
3. **Edge increase or deletion:** find the affected vertices (those whose every shortest path used that edge, found by walking the shortest-path DAG). Mark them.
4. Compute new tentative distances for the affected vertices from their unaffected neighbors, then run a Dijkstra restricted to the affected set.
5. The work is proportional to the number of vertices whose distance actually changes, plus their edges.

**Complexity:** Bounded by the size of the change ("output-sensitive"), not the graph size.

**Agent use:**
- **Role:** Analyst.
- **How:** Live distance maintenance for routing, reachability with costs, or "distance to the nearest critical asset", as links fail or costs change.
- **Rules:** Periodically cross-check with a full recomputation (GX5).
- **Guardrails:** Cascading changes near the source can touch most of the graph. Cap the work and fall back to a full recompute.

### 202. Incremental topological ordering (Pearce-Kelly)

**Definition:** Maintaining a valid topological order of a DAG as edges are added, and detecting immediately when an addition would create a cycle.

**How it works:**
1. Keep an order index ord(v) for every vertex.
2. Adding edge (u, v) with ord(u) < ord(v): the order is still valid, so do nothing.
3. If ord(u) > ord(v): the affected region is the vertices with order between ord(v) and ord(u).
4. DFS forward from v and backward from u, limited to that region. If the forward search reaches u, the new edge creates a cycle: reject it, with the cycle as the certificate.
5. Otherwise, reassign the order indices only within the affected region: backward-reached vertices first, then forward-reached ones, reusing the same index slots.

**Complexity:** Proportional to the size of the affected region, which is usually small.

**Agent use:**
- **Role:** Analyst and Verifier.
- **How:** Live dependency graphs (build systems, task schedulers, package graphs, the glue engine's DAGs, G8) that must stay acyclic. A new dependency creating a cycle is rejected with an explanation at the moment it's added.
- **Rules:** Report the exact cycle when rejecting (GR6).
- **Guardrails:** None specific.

### 203. Dynamic minimum spanning tree

**Definition:** Maintaining a minimum spanning tree (or forest) under edge insertions, deletions and weight changes.

**How it works:**
1. **Insertion of (u, v, w):** find the heaviest edge on the tree path between u and v, using link-cut trees (#70). If it's heavier than w, swap it for the new edge.
2. **Deletion of a non-tree edge:** nothing changes.
3. **Deletion of a tree edge:** the tree splits in two. Find the lightest non-tree edge reconnecting the two sides. Holm et al.'s level-based structure (like #52) makes this efficient.
4. Weight changes are a deletion followed by an insertion.

**Complexity:** O(log n) insertion with link-cut trees. Polylogarithmic amortized for full dynamics.

**Agent use:**
- **Role:** Analyst.
- **How:** Live backbone maintenance (cheapest network connecting everything, or single-linkage clusters) as links and costs change.
- **Rules:** Verify with the cycle property on samples (GX5).
- **Guardrails:** Use a library implementation; full dynamic MST is complex.

### 204. Dynamic PageRank with residual push

**Definition:** Updating PageRank after edge changes by pushing only the resulting "error" through the graph, instead of recomputing from scratch.

**How it works:**
1. Keep the scores p and the residuals r, as in forward push (#103), where the scores satisfy a known invariant relative to r.
2. When edge (u, v) is added or removed, u's out-degree changes. Correct u's contribution: adjust the residuals of u and its neighbors so the invariant holds again.
3. Run pushes from vertices whose residual exceeds the threshold.
4. The work is proportional to the size of the change's effect.
5. Many updates can be batched before pushing.

**Complexity:** Small per update for typical graphs.

**Agent use:**
- **Role:** Analyst.
- **How:** Keeps importance scores fresh in graphs that change constantly (link graphs, interaction graphs), for retrieval ranking and entity importance.
- **Rules:** Run a full recomputation periodically to bound accumulated numerical error.
- **Guardrails:** Edges added to or removed from hubs create large corrections. Batch them, and monitor the push volume.

### 205. Incremental triangle counting

**Definition:** Keeping exact triangle counts (global and per vertex) up to date as edges arrive and depart.

**How it works:**
1. **Edge (u, v) added:** count the common neighbors w of u and v (sorted-list or hash intersection). Each forms a new triangle. Add that count to the global total, and credit u, v and each w.
2. **Edge removed:** the same intersection, subtracted.
3. Keep neighbor sets as hash sets or sorted structures, for fast intersection.
4. High-degree vertices: use bitmaps (#8) or the smaller-set-first intersection.

**Complexity:** O(min(deg u, deg v)) per update with hash sets.

**Agent use:**
- **Role:** Analyst.
- **How:** Live clustering and community-tightness monitoring (fraud rings forming, cohesion changing), and the base for incremental k-truss.
- **Rules:** Process edge updates in order, idempotently: duplicate events must not double-count (G40).
- **Guardrails:** None specific.

## E2. Streaming graphs and sketches

### 206. Semi-streaming algorithms (connectivity, matching, spanners in one pass)

**Definition:** Graph algorithms that read edges as a stream, using memory O(n polylog n): enough for the vertices, not for all the edges.

**How it works:**
1. Edges arrive one at a time; each can be seen only once (or a few times).
2. **Connectivity:** maintain union-find over the vertices (#51). Each edge unions its endpoints. Exact, in one pass.
3. **Matching:** greedy maximal matching gives a 1/2-approximation in one pass. Multiple passes improve it.
4. **Spanners:** keep an edge only if its endpoints are currently far apart in the kept graph (#238).
5. **Bipartiteness, MST weight** and other properties have similar one-pass methods.

**Complexity:** O(n polylog n) memory, O(1) or polylog time per edge.

**Agent use:**
- **Role:** Analyst.
- **How:** Analyzing edge streams (communication logs, transactions, event streams) too big to store, with bounded memory per stream processor.
- **Rules:** State exactly what the algorithm guarantees (exact or approximate, GR4).
- **Guardrails:** Insert-only methods break with deletions. Use linear sketches (#207) when deletions occur.

### 207. Linear graph sketches (AGM sketches, ℓ₀-sampling)

**Definition:** Small linear summaries of each vertex's edges that support both insertions and deletions, and still allow recovering connectivity and spanning forests.

**How it works:**
1. Each vertex keeps a sketch of its incidence vector (a +1/−1 entry per incident edge, signed by direction of an ordering).
2. Sketches are linear: the sketch of a set of vertices = the sum of their sketches. Edges inside the set cancel, leaving only edges leaving the set.
3. **ℓ₀-sampling** recovers one nonzero entry (an outgoing edge) from a sketch with high probability, using hashing at several sampling levels.
4. **Connectivity (Borůvka style, #63):** each component sums its vertices' sketches, samples an outgoing edge, merges along it, and repeats. O(log n) independent sketch copies support the O(log n) rounds.
5. Deletions are handled by subtracting from the sketches.

**Complexity:** O(n polylog n) total space.

**Agent use:**
- **Role:** Analyst.
- **How:** Connectivity monitoring on fully dynamic streams (links added and removed) with bounded memory, and it's distributable: sketches from different machines just add up.
- **Rules:** Report the failure probability (GR4).
- **Guardrails:** Complex to implement correctly. Validate on known graphs first.

### 208. Graph stream frequency sketches (Count-Min, TCM)

**Definition:** Compact, approximate counters for edge frequencies and vertex activity in high-volume graph streams.

**How it works:**
1. **Count-Min for edges:** hash each (u, v) pair into d rows of w counters, increment all d positions. Estimate a count as the minimum of the d counters. It never underestimates; overestimation is bounded by ε × total with probability 1−δ.
2. **TCM (graph sketch):** hash the vertices into a small w × w matrix (several of them, with different hashes). Each edge increments a cell. The small matrices are compressed graphs that approximately answer edge, vertex and even reachability queries.
3. **Heavy hitters:** combine with heaps to track the most frequent edges or vertices.

**Complexity:** O(d) per update. Memory O(d × w) or O(d × w²).

**Agent use:**
- **Role:** Analyst.
- **How:** Real-time "top talkers" and the hottest relationships in communication or transaction streams, unusual pair frequencies, and early hotspot detection.
- **Rules:** Report the error bounds (GR4).
- **Guardrails:** Overestimates can falsely flag pairs. Confirm with exact counts before acting.

### 209. Distinct-neighbor counting (per-vertex HyperLogLog)

**Definition:** Estimating how many distinct neighbors each vertex has had in a stream, with small fixed memory per vertex.

**How it works:**
1. Each vertex keeps a small HyperLogLog sketch.
2. For each edge (u, v), insert v into u's sketch (and u into v's for undirected streams).
3. Duplicates don't increase the estimate, so repeated contacts with the same neighbor count once.
4. Sketches merge by register-wise maximum, for windows or distributed shards.

**Complexity:** O(1) per update, a few hundred bytes to a few KB per vertex.

**Agent use:**
- **Role:** Analyst.
- **How:** Detects fan-out anomalies (an account suddenly contacting many distinct counterparts: scanning, spam, account takeover) in real time.
- **Rules:** Use the sketch error in alert thresholds (GR4).
- **Guardrails:** Fan-out signals are evidence for review, not proof (GR8).

### 210. Reservoir sampling of edges

**Definition:** Keeping a fixed-size uniform random sample of all edges seen so far in a stream.

**How it works:**
1. Keep the first k edges.
2. For the t-th edge (t > k), with probability k/t, replace a random edge in the reservoir with it.
3. At any time, the reservoir is a uniform sample of all edges seen.
4. Estimators built on it (triangles in TRIEST, #122, or subgraph counts) scale up by the inverse sampling probabilities.
5. Weighted and time-decayed variants favor important or recent edges.

**Complexity:** O(1) per edge, O(k) memory.

**Agent use:**
- **Role:** Analyst.
- **How:** Bounded-memory samples for estimating structure in endless streams, and representative test data from production streams.
- **Rules:** Fix seeds (GR5).
- **Guardrails:** Reservoirs may contain personal data. Apply the same retention and access rules as the source.

### 211. Sliding-window graph maintenance

**Definition:** Maintaining a graph (or its statistics) over only the last W time units or the last N edges, with expiring edges removed.

**How it works:**
1. Edges carry timestamps. Keep them in arrival order (a queue).
2. When time advances, expire edges older than the window: pop them from the queue and delete them from the structures (decrement counts, update sketches, use dynamic algorithms #201–205).
3. For approximate statistics, use window-aware sketches: exponential histograms, or time-bucketed sketches merged on demand (keep per-minute sketches, sum the last W minutes).
4. Results always refer to the current window.

**Complexity:** Amortized O(1) to O(log n) per edge, depending on the statistic.

**Agent use:**
- **Role:** Analyst.
- **How:** "Who interacted with whom in the last hour?", recent communities, and current hotspots, without the long-past noise.
- **Rules:** State the window size and alignment with every result.
- **Guardrails:** Expiry must be exact for compliance-relevant data (no stale edges left behind).

## E3. Temporal graphs

### 212. Temporal reachability (foremost, fastest, shortest journeys)

**Definition:** Path problems where edges are only usable at specific times and paths must move forward in time, with several notions of "best".

**How it works:**
1. Each edge is a contact (u, v, t, duration).
2. A **journey** is a sequence of contacts with non-decreasing times (each next contact starts after the previous one arrives).
3. **Foremost:** the earliest arrival (Connection Scan, #49, or a time-ordered BFS).
4. **Fastest:** the minimum total duration (arrival − departure). Requires considering departure times, often with profile methods.
5. **Shortest:** the fewest hops among valid journeys.
6. **Temporal reachability sets** are not transitive: A reaches B and B reaches C doesn't imply A reaches C in time.

**Complexity:** About O(number of contacts) for foremost. More for fastest and profiles.

**Agent use:**
- **Role:** Analyst.
- **How:** Accurate spread analysis ("could a compromised host have reached this one, given when connections happened?"), contact tracing, and information-flow timelines.
- **Rules:** Use temporal algorithms for any question involving order of events (K8 equivalent).
- **Guardrails:** Static reachability overstates spread. Never substitute it.

### 213. Temporal motifs (δ-temporal motifs, Paranjape et al.)

**Definition:** Small patterns of edges that happen in a specific order within a time window δ.

**How it works:**
1. A motif is a sequence of edges among a few vertices, with an order, for example: A→B, then B→C, then C→A, all within δ seconds.
2. Count its occurrences in the timestamped edge stream.
3. Efficient counting: a sliding window over time-sorted edges, with counters for partial pattern matches (dynamic programming on motif prefixes). Special fast algorithms exist for 2–3 vertex motifs.
4. Compare counts with time-shuffled null models (#141 style) for significance.

**Complexity:** Near-linear in the number of edges for small motifs.

**Agent use:**
- **Role:** Analyst.
- **How:** Detects meaningful sequences: rapid money cycling (A→B→C→A within minutes), escalation chains in communication, attack steps in a specific order.
- **Rules:** Choose δ from domain knowledge, and report it.
- **Guardrails:** Patterns are evidence for investigation (GR8, GX3).

### 214. Temporal graph storage (time-indexed adjacency, event logs, interval structures)

**Definition:** Storing graphs whose edges and vertices exist during time intervals, so that both "graph at time t" and "history of this edge" queries are efficient.

**How it works:**
1. **Event log:** append every add or remove event with a timestamp. Replaying gives any past state (like event sourcing, G82).
2. **Snapshots plus deltas:** periodic full snapshots, with deltas in between. A query at time t loads the nearest snapshot and applies the deltas.
3. **Per-vertex time-sorted adjacency:** each neighbor list sorted by time, so "neighbors of v between t₁ and t₂" is a range scan.
4. **Interval indexes** (interval trees, time-partitioned segments) for validity periods.

**Complexity:** Trade-off between snapshot frequency (storage) and replay cost (query time).

**Agent use:**
- **Role:** Builder.
- **How:** The foundation for temporal queries (#212, #213), bitemporal knowledge graphs (K#12, K#173) and audit questions ("what did the network look like during the incident?").
- **Rules:** Tune snapshot frequency to the query patterns.
- **Guardrails:** History retention must follow erasure policies (K#185).

### 215. Anomaly and change-point detection in graph streams (MIDAS, SpotLight, structural change)

**Definition:** Detecting sudden structural changes or unusual edge activity in streaming graphs, in real time.

**How it works:**
1. **MIDAS:** count-min sketches (#208) of edge counts in the current time tick and in total. A chi-squared-style score flags edges (or vertex pairs) whose current count is far above what their history predicts. Constant time and memory per edge.
2. **SpotLight:** sketch each time window's graph into a vector (edge weights summed over random source-destination region pairs). Sudden jumps in that vector signal dense subgraphs appearing or disappearing.
3. **Structural change points:** track graph statistics over windows (density, degree distribution, community structure, spectral properties) and apply change-point tests (CUSUM, Bayesian online change-point detection).

**Complexity:** O(1) per edge for MIDAS.

**Agent use:**
- **Role:** Observer.
- **How:** Real-time detection of attacks (sudden bursts of connections), fraud bursts and outages (sudden drops), in event-ingestion pipelines.
- **Rules:** Tune thresholds against historical false-positive rates.
- **Guardrails:** Alerts lead to investigation, not automatic blocking, unless an approved policy says so (GX4).

## E4. Parallel graph processing models

### 216. Gather-Apply-Scatter (GAS, PowerGraph model)

**Definition:** A vertex-program model where computation is split into gathering information from edges, applying an update to the vertex, and scattering changes to neighbors. It's designed for power-law graphs.

**How it works:**
1. **Gather:** combine values from a vertex's neighbors and edges with a commutative, associative sum.
2. **Apply:** compute the vertex's new value from the gathered sum.
3. **Scatter:** update edge data, and activate neighbors that need recomputation.
4. Because gather is a sum, a hub's gathering can be split across machines (on its replicas, #173, #247) and combined, so high-degree vertices don't become bottlenecks.

**Complexity:** O(m) work per superstep, well balanced on skewed graphs.

**Agent use:**
- **Role:** Analyst.
- **How:** Expressing PageRank, label propagation, connected components and many other algorithms in a distribution-friendly way on huge power-law graphs.
- **Rules:** Gather operations must be commutative and associative.
- **Guardrails:** Verify results against a single-machine run on samples (GX5).

### 217. Block-centric ("think like a graph") processing

**Definition:** Running whole subgraph partitions as units: each worker solves its partition locally (with sequential algorithms), and partitions only exchange messages at boundaries.

**How it works:**
1. Partition the graph into blocks with few cut edges (#170).
2. Each superstep, each block runs a local algorithm to convergence on its own subgraph (for example, a full local BFS, or local connected components).
3. Only boundary vertex updates are exchanged between blocks.
4. Far fewer supersteps than vertex-centric models, since information crosses each block in one step.

**Complexity:** Supersteps drop from about the graph diameter to about the diameter of the block graph.

**Agent use:**
- **Role:** Analyst.
- **How:** Speeds up distributed algorithms on high-diameter graphs (road networks, meshes), where vertex-centric processing needs thousands of supersteps.
- **Rules:** Use good partitions (#170). Block quality determines the speedup.
- **Guardrails:** None specific.

### 218. Asynchronous graph processing (GraphLab consistency models)

**Definition:** Updating vertices as soon as possible, using neighbors' latest values, without global barriers between rounds.

**How it works:**
1. A scheduler keeps a set of vertices needing updates.
2. Workers update vertices whenever available, reading neighbors' current values.
3. **Consistency models** prevent harmful races: vertex consistency (no simultaneous updates of the same vertex), edge consistency (no simultaneous updates of adjacent vertices), or full consistency (no simultaneous updates within distance 2). Enforced with locks or graph coloring (#184).
4. Updates that change a vertex significantly schedule its neighbors.
5. Often converges in less total work than synchronous rounds (like Gauss-Seidel, #102).

**Complexity:** Often less total work than synchronous rounds. Results can vary with timing.

**Agent use:**
- **Role:** Analyst.
- **How:** Iterative algorithms that converge faster asynchronously (PageRank, belief propagation, #270, label propagation).
- **Rules:** Use the consistency model the algorithm requires for correctness.
- **Guardrails:** Asynchronous results aren't bit-for-bit reproducible. Use synchronous mode when reproducibility matters (GR5).

### 219. GPU frontier processing (Gunrock's advance and filter)

**Definition:** A data-centric GPU programming model where algorithms are sequences of operations on frontiers (sets of active vertices or edges).

**How it works:**
1. **Advance:** expand the frontier along edges to produce the next frontier (visiting neighbors), with load balancing across GPU threads for vertices of very different degrees.
2. **Filter:** remove duplicates and unwanted vertices from a frontier (already visited, not meeting a condition).
3. **Compute:** apply per-element operations.
4. Algorithms (BFS, SSSP, PageRank, connected components) are written as loops of these steps.
5. Load-balancing strategies switch depending on the frontier: per-thread, per-warp or per-block processing of neighbor lists.

**Complexity:** Same work as the CPU algorithm, with much higher throughput on suitable graphs.

**Agent use:**
- **Role:** Analyst.
- **How:** Very fast analytics on graphs that fit in GPU memory, which is useful for interactive exploration and repeated runs.
- **Rules:** Check memory fit first (GR3).
- **Guardrails:** Results must match CPU references on test graphs (GX5).

### 220. GraphBLAS (graph algorithms as sparse linear algebra)

**Definition:** A standard API (the GraphBLAS specification) that expresses graph algorithms as sparse matrix and vector operations over custom semirings.

**How it works:**
1. The graph is a sparse adjacency matrix. A frontier is a sparse vector.
2. **One BFS step:** a matrix-vector product, over the Boolean semiring (OR, AND).
3. **Shortest-path steps:** the (min, +) semiring: "multiply" = add a weight, "sum" = take the minimum.
4. **Masks** restrict outputs (for example "only unvisited vertices"), avoiding wasted work.
5. Triangle counting = a masked matrix product (#221). PageRank = repeated products over the usual (+, ×) semiring.
6. Implementations (such as SuiteSparse:GraphBLAS) optimize these operations for sparsity and parallelism.

**Complexity:** Depends on the sparse operation. Optimized libraries are highly efficient.

**Agent use:**
- **Role:** Analyst.
- **How:** A compact, portable and fast way to implement many graph algorithms on top of one well-optimized library.
- **Rules:** Choose the semiring explicitly, and document it.
- **Guardrails:** None specific.

### 221. Sparse matrix products for graph algorithms (SpMV, masked SpGEMM)

**Definition:** The core sparse matrix operations behind analytics: sparse matrix times vector (SpMV), and sparse matrix times sparse matrix (SpGEMM), often restricted by a mask.

**How it works:**
1. **SpMV** (y = A x): for CSR, each row dots with x. For sparse x, it's better to "push" from x's nonzeros through CSC (#222).
2. **SpGEMM** (C = A B): computing rows of C by merging rows of B selected by A's nonzeros, with hash tables or heaps as accumulators.
3. **Masked SpGEMM:** compute only the entries allowed by a mask M. **Triangle counting:** sum of (L × L) ⊙ L (L = lower triangular part), computed only where L has nonzeros.
4. Load balancing matters with skewed degrees: split work by output size estimates.

**Complexity:** SpMV O(m). SpGEMM depends on the intermediate products, which masks reduce dramatically.

**Agent use:**
- **Role:** Analyst.
- **How:** Path counting (A²: two-hop counts for recommendations), similarity (shared neighbor counts, K#131), metapath counting (#291), and triangle counting.
- **Rules:** Use masks whenever only some outputs are needed.
- **Guardrails:** Unmasked A² on graphs with hubs explodes in size. Check output size estimates (GR3).

### 222. Frontier representation switching (sparse lists versus dense bitmaps)

**Definition:** Representing the set of active vertices as a sparse list when it's small and a dense bitmap when it's large, and switching automatically.

**How it works:**
1. **Sparse frontier:** a list of vertex IDs. Efficient for "push" (iterate the frontier, update neighbors).
2. **Dense frontier:** a bitmap of n bits. Efficient for "pull" (iterate all vertices, check whether any neighbor is in the frontier).
3. Switch when the frontier's total out-degree exceeds a fraction of m (as in direction-optimizing BFS, #13).
4. Conversions are O(frontier size) or O(n).

**Complexity:** Each step runs in the cheaper of the two modes.

**Agent use:**
- **Role:** Analyst.
- **How:** A standard optimization inside every high-performance graph framework (#219, #220, #223).
- **Rules:** None beyond the framework defaults.
- **Guardrails:** None specific.

### 223. Ligra (edgeMap and vertexMap)

**Definition:** A lightweight shared-memory framework where graph algorithms are written with two operations over vertex subsets, with automatic push/pull switching.

**How it works:**
1. **vertexMap(U, f):** apply f to every vertex in subset U, in parallel.
2. **edgeMap(G, U, F, C):** for every edge from U to a vertex satisfying condition C, apply update F. Returns the subset of target vertices updated.
3. edgeMap chooses sparse push or dense pull automatically, by frontier size (#222).
4. Updates use atomic operations, such as compare-and-swap, for safe concurrent writes.
5. BFS, betweenness, connected components, PageRank and k-core are each a few lines.

**Complexity:** Work-efficient. Very fast on multi-core machines.

**Agent use:**
- **Role:** Analyst.
- **How:** High-performance single-machine analytics on graphs with billions of edges (machines with large RAM).
- **Rules:** Use deterministic variants when reproducibility matters (GR5).
- **Guardrails:** Memory fit (GR3).

### 224. Out-of-core graph processing (GraphChi PSW, X-Stream)

**Definition:** Processing graphs larger than RAM by streaming them from disk in a disk-friendly order.

**How it works:**
1. **GraphChi (parallel sliding windows):** split vertices into intervals. Each interval's in-edges are stored in a "shard", sorted by source. To process one interval, load its shard fully plus a sliding window of the other shards (the edges going out of the interval). Disk reads are mostly sequential.
2. **X-Stream (edge-centric scatter-gather):** stream all edges sequentially. Scatter updates for edges whose source changed into update files, then gather the updates per vertex partition. Only sequential I/O.
3. Both turn random graph access into sequential disk access.

**Complexity:** Several sequential passes over the edges per iteration.

**Agent use:**
- **Role:** Analyst.
- **How:** Analytics on huge graphs with one ordinary machine and fast SSDs, without a cluster.
- **Rules:** Preprocess (sharding) once, then reuse the shards for many algorithms.
- **Guardrails:** Iterations are slow. Estimate the total time before starting (GR3).

## E5. Distributed graph algorithms

### 225. Distributed BFS with 2D partitioning

**Definition:** Breadth-first search on a cluster, where the adjacency matrix is split into a 2D grid of blocks, reducing communication compared to splitting by vertex.

**How it works:**
1. Arrange P processors in a √P × √P grid. Processor (i, j) holds the matrix block of edges from vertex range j to vertex range i.
2. Each level: the frontier is exchanged within processor columns (expand phase), each processor computes its local neighbors, and results are combined within processor rows (fold phase).
3. Each processor talks to only O(√P) others per phase, instead of all P.
4. Combine with direction optimization (#13) and compressed frontiers (bitmaps).

**Complexity:** O(n + m) total work. Communication per processor is reduced to roughly O(n / √P) per level.

**Agent use:**
- **Role:** Analyst.
- **How:** Traversal at the largest scales (Graph500 class) on supercomputers or large clusters.
- **Rules:** Use when 1D partitioning's all-to-all communication becomes the bottleneck.
- **Guardrails:** Cross-check distances on samples (GX5).

### 226. Distributed triangle counting

**Definition:** Counting triangles in graphs partitioned across machines, minimizing data exchange.

**How it works:**
1. Orient edges by degree order (as in #121).
2. **Edge-iterator approach:** for each edge (u, v), the machine holding u's forward neighbor list needs v's forward list. Request it, or send u's list to v's owner, whichever is smaller.
3. **Optimizations:** cache hub lists (requested by many), batch requests, and use 2D partitioning of the adjacency matrix with masked SpGEMM (#221).
4. Sum the local counts globally.

**Complexity:** O(m^1.5) work total. Communication depends heavily on the partitioning.

**Agent use:**
- **Role:** Analyst.
- **How:** Clustering metrics and k-truss foundations on graphs too large for one machine.
- **Rules:** Use degree ordering, or hubs dominate the communication.
- **Guardrails:** None specific.

### 227. Distributed connected components (Shiloach-Vishkin, FastSV, min-label propagation)

**Definition:** Finding connected components in parallel and distributed settings with few rounds.

**How it works:**
1. **Min-label propagation:** each vertex repeatedly takes the minimum label among itself and its neighbors. Simple, but needs as many rounds as the graph's diameter.
2. **Shiloach-Vishkin:** maintain a forest of parent pointers. **Hooking:** for each edge, link the root of one tree under the root of the other (smaller under larger, or by ID). **Shortcutting (pointer jumping):** set each vertex's parent to its grandparent, halving tree heights. O(log n) rounds.
3. **FastSV:** an optimized version, with aggressive hooking and shortcutting, mapping well to linear-algebra frameworks (#220).
4. Afterwards, every vertex points to its component's root.

**Complexity:** O(log n) rounds for Shiloach-Vishkin variants.

**Agent use:**
- **Role:** Analyst.
- **How:** Components at cluster scale: entity resolution clusters (K#38) over billions of records, and network segmentation.
- **Rules:** Prefer the O(log n)-round algorithms on high-diameter graphs.
- **Guardrails:** Verify component counts against a single-machine run on samples (GX5).

### 228. Distributed minimum spanning tree (GHS algorithm)

**Definition:** The Gallager-Humblet-Spira algorithm builds an MST in a network where each vertex is a processor that knows only its own edges and communicates by messages.

**How it works:**
1. Each vertex starts as its own fragment (a Borůvka-style approach, #63).
2. Each fragment finds its minimum-weight outgoing edge through a coordinated search (messages within the fragment, coordinated by its "core" edge).
3. Fragments merge along those edges. Levels manage how fragments combine (a lower-level fragment joins a higher-level one; equal levels merge and increase their level).
4. This continues until a single fragment spans the network.

**Complexity:** O(n log n + m) messages.

**Agent use:**
- **Role:** Analyst.
- **How:** Building spanning trees inside networks without central control (sensor networks, peer-to-peer overlays), and the conceptual basis for distributed MST in cluster frameworks.
- **Rules:** Use for message-passing settings. In cluster frameworks, use parallel Borůvka.
- **Guardrails:** Requires distinct edge weights, or consistent tie-breaking (GR5).

### 229. Distributed subgraph matching (worst-case optimal distributed joins)

**Definition:** Finding pattern matches in distributed graphs, using worst-case optimal joins (K#56) adapted to distributed dataflow, so intermediate results don't explode.

**How it works:**
1. Order the pattern's vertices.
2. **Extend prefixes one vertex at a time:** for each partial match, intersect the candidate sets from every already-matched neighbor's adjacency. The machines holding those adjacencies participate.
3. **BiGJoin** (on timely dataflow): count the candidates first, have the smallest candidate set propose extensions, and the others verify by intersection. This balances work and bounds communication.
4. Process in batches to control memory.

**Complexity:** Worst-case optimal in total work, with bounded memory per batch.

**Agent use:**
- **Role:** Analyst.
- **How:** Exact pattern search (cycles, cliques, specific transaction shapes) on graphs too large for one machine.
- **Rules:** Anchor patterns at selective vertices where possible.
- **Guardrails:** Cap the output, and count before listing (GR7).

### 230. Factorized representations for query results

**Definition:** Storing query results compactly as a structure of nested unions and products, instead of a flat list of rows, avoiding the blowup of repeated values.

**How it works:**
1. Many graph query results contain repetitions. For example, each person × each of their 100 posts × each of 100 tags gives 10,000 flat rows.
2. **Factorized form:** person → {posts} × {tags}, stored as a tree. Its size is the sum of the parts, not their product.
3. Counting, aggregation and filtering can work directly on the factorized form.
4. Flat rows are produced only on demand.

**Complexity:** Results can be exponentially smaller than the flat output.

**Agent use:**
- **Role:** Retriever and Analyst.
- **How:** Graph queries with many-to-many hops produce huge flat results. Factorized execution (in engines that support it) keeps them manageable, and counts and aggregates become cheap.
- **Rules:** Prefer aggregates (count, group) over listing all combinations.
- **Guardrails:** Flattening a factorized result can explode output size. Cap it (GR7).

### 231. Hybrid query plans (binary joins plus worst-case optimal joins)

**Definition:** Query plans that use classic binary joins for acyclic, selective parts of a query and worst-case optimal joins for cyclic parts.

**How it works:**
1. Decompose the query pattern: acyclic parts (paths, trees), and cyclic cores (triangles, cycles, cliques).
2. Plan the cyclic cores with worst-case optimal joins (K#56) and the rest with hash or merge joins.
3. A cost-based optimizer (K#57) chooses the decomposition and order using cardinality estimates.
4. Some engines include a factorized output (#230).

**Complexity:** Avoids worst-case blowups on cyclic patterns while staying fast on simple ones.

**Agent use:**
- **Role:** Retriever.
- **How:** The agent benefits when graph engines plan this way, especially for fraud and network patterns containing cycles. It explains why some engines handle cyclic queries dramatically better than others.
- **Rules:** Check query plans for cyclic patterns (K#57).
- **Guardrails:** None specific.

## E6. Subgraph enumeration and counting at scale

### 232. Pattern-aware subgraph enumeration systems (AutoMine, GraphPi, Arabesque)

**Definition:** Systems that enumerate all occurrences of patterns (or all subgraphs up to a size) efficiently, by compiling patterns into optimized nested loops or by exploring embeddings systematically.

**How it works:**
1. **Embedding exploration (Arabesque):** grow all subgraphs one vertex or edge at a time, deduplicate with canonical forms (#189), and filter with user functions. General but heavy.
2. **Pattern compilation (AutoMine, GraphPi):** for a given pattern, generate a nested-loop plan: choose the vertex order, the set intersections at each level, and symmetry-breaking restrictions (#233).
3. Choose among several plans with a cost model.
4. Reuse the intersection results shared between patterns.

**Complexity:** Exponential in pattern size. Compiled plans are often much faster than generic exploration.

**Agent use:**
- **Role:** Analyst.
- **How:** Counting or listing many patterns at once (motif censuses, #132; graphlets, #120) on large graphs.
- **Rules:** Count before listing (GR7).
- **Guardrails:** Patterns larger than about 5–6 vertices need approximate methods (#234).

### 233. Symmetry breaking in subgraph enumeration

**Definition:** Adding ordering constraints so each occurrence of a symmetric pattern is found exactly once, instead of once per symmetry.

**How it works:**
1. Compute the pattern's automorphisms (#191). For example, a triangle has 6.
2. Without constraints, each triangle occurrence would be found 6 times (once per automorphism).
3. Add ordering constraints on the matched vertex IDs that only one of the symmetric mappings satisfies: for the triangle, require id(v1) < id(v2) < id(v3).
4. Constraints are derived systematically from the automorphism group's structure (for example with a stabilizer chain).
5. Constraints also prune the search early.

**Complexity:** Reduces work by up to the size of the automorphism group.

**Agent use:**
- **Role:** Analyst.
- **How:** Correct, non-duplicated pattern counts. Prevents overcounting when the agent counts patterns with custom search code.
- **Rules:** Always apply symmetry breaking when counting unlabeled patterns.
- **Guardrails:** Verify counts against brute force on small graphs (GX5).

### 234. Color coding for approximate subgraph counting

**Definition:** Randomly coloring vertices with k colors, then counting only "colorful" occurrences (all vertices differently colored). That's tractable by dynamic programming, and gives an unbiased estimate of the true count.

**How it works:**
1. Color every vertex uniformly at random with one of k colors (k = pattern size).
2. A specific occurrence is colorful with probability k! / kᵏ.
3. Count the colorful occurrences of tree-like patterns (or patterns with a tree decomposition) by dynamic programming over color subsets. No need to track exact vertex sets, just which colors are used.
4. Estimate = colorful count / (k! / kᵏ). Average over several colorings to reduce variance.
5. Extensions handle general patterns through tree decompositions (#196).

**Complexity:** O(2ᵏ × m) per coloring for tree patterns: exponential only in k.

**Agent use:**
- **Role:** Analyst.
- **How:** Counting larger patterns (paths and trees of 7–12 vertices) on big graphs, where exact enumeration is impossible: network motif statistics, long-path counts.
- **Rules:** Report the estimate's variance from repeated colorings (GR4).
- **Guardrails:** Fix seeds per coloring (GR5).

### 235. Color coding for path detection (k-path)

**Definition:** Deciding whether a simple path of length k exists, using random colorings, in time exponential only in k.

**How it works:**
1. Randomly color the vertices with k colors.
2. Dynamic programming: for each vertex v and each color set S, record whether some colorful path ends at v using exactly the colors in S.
3. Extend paths by edges to neighbors whose color isn't yet in S.
4. If some state with all k colors is reachable, a simple path of length k exists.
5. Repeat with enough colorings (about eᵏ times) to find an existing path with high probability.

**Complexity:** O(2ᵏ × eᵏ × m), polynomial for a fixed k.

**Agent use:**
- **Role:** Analyst.
- **How:** Detects long simple chains (long laundering paths, long dependency chains without repeated nodes) that BFS can't detect, since BFS paths can repeat vertices in the general search.
- **Rules:** Report the failure probability (GR4).
- **Guardrails:** Costs grow quickly with k. Check GR3.

## E7. Summarization, spanners and approximation structures

### 236. Graph summarization (SWeG and MDL-based summaries)

**Definition:** Grouping vertices into supernodes and edges into superedges, with a small list of corrections, to produce a compact summary of the graph (lossless or lossy).

**How it works:**
1. Group vertices with similar neighborhoods into supernodes (candidate groups via MinHash, C#31).
2. Between two supernodes, add a superedge if most possible vertex pairs are connected.
3. **Corrections:** list the missing edges (for superedges) and the extra edges (outside superedges), so the original graph can be rebuilt exactly (lossless).
4. Choose groupings that minimize total description cost (supernodes + superedges + corrections), as in MDL.
5. **Lossy version:** drop corrections below a threshold.

**Complexity:** Near-linear with MinHash-based candidate grouping (SWeG).

**Agent use:**
- **Role:** Builder.
- **How:** Compact graph views for people and for LLM context (a summary of a large subgraph), storage reduction, and faster approximate queries.
- **Rules:** Label lossy summaries as approximate (GR4).
- **Guardrails:** Never answer exact questions from lossy summaries.

### 237. Compression with virtual nodes (dense subgraph compression)

**Definition:** Replacing dense bipartite blocks (many sources each linked to the same many targets) with a virtual node in the middle, which drastically cuts edge counts.

**How it works:**
1. Find bicliques or near-bicliques: sets S and T where most of S links to most of T (using frequent itemset mining on neighbor lists).
2. Replace |S| × |T| edges with |S| + |T| edges through a new virtual node.
3. Repeat. Traversals pass through virtual nodes transparently.
4. Many algorithms (PageRank, reachability) can run directly on the compressed graph with small adjustments.

**Complexity:** Mining is the expensive part. The edge savings can be large on web and social graphs.

**Agent use:**
- **Role:** Builder.
- **How:** Shrinks graphs with repeated dense link patterns (shared navigation menus, group memberships), which speeds up analytics.
- **Rules:** Mark virtual nodes clearly, and exclude them from results (counts, rankings).
- **Guardrails:** Algorithms that aren't aware of virtual nodes give wrong answers on such graphs. Check compatibility.

### 238. Graph spanners (greedy k-spanner, Baswana-Sen)

**Definition:** A sparse subgraph that approximately preserves all distances: every distance in the spanner is at most k times the original distance (the stretch).

**How it works:**
1. **Greedy:** sort the edges by weight. Add edge (u, v) only if the current spanner distance between u and v is greater than k × w(u, v). For stretch 2t−1, this gives O(n^(1+1/t)) edges.
2. **Baswana-Sen (randomized, linear time):** sample cluster centers in rounds. Vertices join nearby clusters, and keep only a few edges per neighboring cluster.
3. The result is much sparser, with a guaranteed stretch.

**Complexity:** Greedy O(m × (shortest path cost)). Baswana-Sen about O(k × m).

**Agent use:**
- **Role:** Builder.
- **How:** Lightweight routing backbones, distance estimation on smaller graphs, and network design with bounded detour.
- **Rules:** Report the stretch k with all results (GR4).
- **Guardrails:** Never use spanner distances where exact distances are required.

### 239. Cut sparsifiers (Benczúr-Karger)

**Definition:** A sparse weighted subgraph where every cut has nearly the same weight as in the original graph.

**How it works:**
1. Compute each edge's "strength" (or connectivity): roughly, how strongly its region is connected. Weak edges (bridges between sparse regions) are important, and strong edges (inside dense clusters) are replaceable.
2. Sample each edge with probability inversely proportional to its strength.
3. Reweight the kept edges by 1/(sampling probability).
4. With O(n log n / ε²) edges, every cut is preserved within (1 ± ε).
5. Spectral sparsifiers (#177) are a stronger version.

**Complexity:** Near-linear.

**Agent use:**
- **Role:** Builder.
- **How:** Speeds up cut-based algorithms (min cut, partitioning, flow approximations) on dense graphs with a guaranteed error.
- **Rules:** Report ε (GR4).
- **Guardrails:** Results are approximate. Verify critical cuts on the original graph.

### 240. All-distances sketches (bottom-k, ADS)

**Definition:** A small per-vertex sketch that summarizes the vertex's distances to all other vertices, supporting estimates of neighborhood sizes, closeness and similarity.

**How it works:**
1. Give every vertex a random rank.
2. A vertex's ADS contains a vertex u (with its distance) if u's rank is among the k smallest among all vertices at distance ≤ d(v, u). Close vertices are kept generously, distant ones sparsely.
3. Built with pruned Dijkstra or BFS runs processed in rank order, with each run pruning at vertices whose sketch can't accept it.
4. Estimates: number of vertices within distance d, closeness centrality, distance-decayed similarity, and so on, with known variance.

**Complexity:** O(k log n) expected entries per vertex.

**Agent use:**
- **Role:** Analyst.
- **How:** Many distance-based statistics for every vertex from one compact structure, on large graphs.
- **Rules:** Report the estimator variance (GR4).
- **Guardrails:** None specific.

## E8. Engineering for scale and correctness

### 241. High-degree vertex splitting and degree-aware processing

**Definition:** Handling hubs specially (splitting their work, replicating them or processing them differently) so they don't create stragglers or memory spikes.

**How it works:**
1. Detect hubs by a degree threshold (#101).
2. **Split work:** divide a hub's neighbor list into chunks processed by different threads or machines, then combine the partial results (as with GAS gathers, #216).
3. **Replicate hubs** in vertex-cut partitioning (#173).
4. **Pull versus push:** compute hubs by pulling from neighbors, and low-degree vertices by pushing.
5. **Logical splitting** in storage: a hub becomes several sub-vertices by edge type or time bucket (K#180).

**Complexity:** Removes the straggler effect of single huge neighbor lists.

**Agent use:**
- **Role:** Builder and Analyst.
- **How:** Keeps distributed jobs and queries from stalling on a few huge vertices, which is the most common real-world performance problem in graph processing.
- **Rules:** Choose the hub threshold from the degree distribution (#135).
- **Guardrails:** GX2: supernode limits also apply to traversals.

### 242. Load balancing for irregular graph work (edge-balanced chunking, merge-path)

**Definition:** Splitting graph work so each thread or machine gets about the same number of edges, not just the same number of vertices.

**How it works:**
1. Compute a prefix sum of the degrees.
2. **Edge-balanced chunking:** split the vertex range at positions where the prefix sum crosses multiples of m/P. Each worker gets about m/P edges.
3. **Merge-path partitioning:** treat the work as merging the vertex list with the edge list, and split diagonals of the merge evenly, which is very balanced even within single vertices.
4. **Dynamic scheduling or work stealing** (G69) handles the remaining imbalance.

**Complexity:** O(n) setup with prefix sums, or O(P log n) with binary searches.

**Agent use:**
- **Role:** Builder.
- **How:** Avoids the situation where one worker gets the hubs and finishes last. That's essential for predictable job times.
- **Rules:** Balance by edges for edge-proportional work, by vertices for vertex-proportional work.
- **Guardrails:** None specific.

### 243. Checkpointing and recovery for graph jobs

**Definition:** Saving the state of long-running iterative graph computations so failures don't restart them from the beginning.

**How it works:**
1. Every few supersteps, write the vertex values, active flags and pending messages to durable storage.
2. On failure, reload the last checkpoint and replay from there.
3. **Confined recovery:** only the failed machine's partitions recompute, using logged messages from other machines, instead of rolling everyone back.
4. Choose the checkpoint interval to balance checkpoint cost against expected lost work (Young/Daly formula: about √(2 × checkpoint cost × mean time between failures)).

**Complexity:** Checkpoint cost is proportional to the state size.

**Agent use:**
- **Role:** Operator.
- **How:** Long analytics (embeddings, PageRank on billions of edges, community detection) survive machine failures and preemptions (G37-style durability for graph jobs).
- **Rules:** Checkpoints record the snapshot version and parameters (GR1).
- **Guardrails:** Test recovery regularly. An untested checkpoint is unproven.

### 244. Multi-version graph storage (LLAMA, delta chains)

**Definition:** Storing several versions of a graph efficiently by sharing unchanged parts, so analytics can run on stable snapshots while updates continue.

**How it works:**
1. **LLAMA:** a CSR-like structure split into snapshots. Each new snapshot stores only the changed vertices' adjacency fragments, with links to older fragments for unchanged data.
2. **Delta chains:** each vertex has a chain of changes with version numbers. A reader at version v follows the chain to the latest change at or before v.
3. Old versions are compacted or merged periodically.
4. Readers pin a version (GR1); writers create new versions.

**Complexity:** Storage proportional to the changes. Reads slightly slower than plain CSR, depending on chain length.

**Agent use:**
- **Role:** Builder.
- **How:** Lets analytics run on a consistent snapshot while the live graph keeps changing, and allows comparing results across versions.
- **Rules:** Pin the version for the duration of a computation (GR1).
- **Guardrails:** Long-pinned versions block compaction. Set a maximum pin time.

### 245. Graph transactions and isolation (snapshot isolation, write skew, locking)

**Definition:** Making concurrent graph updates correct: what anomalies can occur, and which mechanisms prevent them.

**How it works:**
1. **Snapshot isolation (MVCC):** each transaction reads a consistent snapshot. On commit, conflicting writes to the same item abort one transaction.
2. **Write skew:** two transactions read overlapping data and write different items, breaking a constraint involving both. For example, two transactions each check "fewer than 2 edges of type X from this node" and each add one. Snapshot isolation doesn't prevent this.
3. **Prevention:** serializable isolation (serializable snapshot isolation tracks read-write dependencies), explicit locks on the constrained item (lock the node, not just the edges), or uniqueness and cardinality constraints enforced by the database.
4. **Deadlocks** are detected with wait-for graphs (G49), and one transaction is aborted.

**Complexity:** Serializable modes cost extra checks and more aborts.

**Agent use:**
- **Role:** Operator.
- **How:** The agent's concurrent graph writes (K#172 merges, edge additions with limits) must use the isolation level their constraints need.
- **Rules:** Use database constraints, or serializable transactions, for any rule involving several items ("at most one active manager edge").
- **Guardrails:** Retry aborted transactions with backoff (G35). Never weaken isolation to reduce aborts without analyzing the anomalies that allows.

### 246. Graph query result caching and materialized views

**Definition:** Storing the results of expensive graph queries (paths, neighborhoods, aggregates) and keeping them correct as the graph changes.

**How it works:**
1. **Cache:** key = (canonical query, parameters, graph version, user permissions), so a new version invalidates automatically (K#62).
2. **Materialized views:** precomputed results (two-hop neighborhoods, transitive closures, common paths) stored and updated as the graph changes.
3. **Update strategies:** recompute fully, invalidate entries touched by changed vertices, or maintain incrementally (#248).
4. Track dependencies from cached entries to the vertices and edges they read.

**Complexity:** The trade-off is storage and maintenance cost against query savings.

**Agent use:**
- **Role:** Retriever.
- **How:** Fast repeated retrieval (popular entities' neighborhoods, frequent path queries) for GraphRAG and agent tools.
- **Rules:** Include permissions in cache keys (K#179).
- **Guardrails:** Stale materialized views give wrong answers. Monitor their lag behind the base graph.

### 247. Ghost and mirror vertices (replica synchronization)

**Definition:** Local copies of remote vertices on each machine, so local computation can read their values without network calls, synchronized after each step.

**How it works:**
1. Each machine stores its own vertices (masters) plus read-only copies of the remote neighbors it needs (ghosts or mirrors).
2. Computation reads ghost values locally.
3. After each superstep, masters send their updated values to their ghosts. With vertex-cut partitioning (#173), mirrors also send partial gather results to their master.
4. Only changed values are sent (delta synchronization), compressed and batched.

**Complexity:** Communication proportional to the changed boundary vertices per superstep.

**Agent use:**
- **Role:** Builder and Analyst.
- **How:** The standard mechanism inside distributed graph frameworks. Explains why cut size and replication factor drive performance.
- **Rules:** Minimize the replication factor through partitioning (#170, #173).
- **Guardrails:** Reading stale ghost values between synchronizations is only valid for algorithms designed for it (bulk synchronous semantics).

### 248. Incremental view maintenance for graph queries (delta queries, counting)

**Definition:** Updating the results of a graph query when the graph changes, by computing only the effect of the change.

**How it works:**
1. For a pattern query Q, the change in its results after adding edges ΔE comes from "delta queries": versions of Q where one edge pattern matches only the new edges, and the others match the full graph.
2. Run the delta queries anchored at the changed edges. That's usually tiny compared with re-running Q.
3. **Deletions:** the same, with negative counts. **The counting algorithm** keeps, for each result, how many derivations support it, and removes results whose count reaches zero.
4. Recursive queries (reachability) use DRed-style methods (K#91) or differential dataflow (#249).

**Complexity:** Proportional to the changes and their local neighborhoods.

**Agent use:**
- **Role:** Retriever and Observer.
- **How:** Live pattern alerts ("notify when a new cycle of transfers forms", "when a new path from internet to a database appears") without re-running heavy queries.
- **Rules:** Each maintained query is tested against full re-execution periodically (GX5).
- **Guardrails:** Changes on hubs make delta queries large. Cap them, and fall back to full recomputation.

### 249. Differential dataflow (incremental iterative computation)

**Definition:** A computation model that keeps iterative algorithms (connected components, shortest paths, PageRank, reachability) up to date under input changes, by tracking differences across both data changes and loop iterations.

**How it works:**
1. Data is represented as collections of (record, time, count change) differences.
2. Times are multi-dimensional: (input version, loop iteration).
3. Operators (map, join, reduce, iterate) process only the differences, and index their state so they can combine new changes with past ones.
4. When the input changes, only the differences that actually propagate are recomputed, at each iteration of each loop.
5. Built on timely dataflow, which tracks progress across these times in a distributed way.

**Complexity:** Updates cost roughly proportional to how much the output actually changes.

**Agent use:**
- **Role:** Analyst and Operator.
- **How:** Continuously correct graph analytics on streaming changes: live connected components, reachability, and maintained rules (K#89). This model fits naturally with event ingestion and stream processing platforms.
- **Rules:** Define the computation once; the framework keeps it current.
- **Guardrails:** State grows with the indexed history. Compact old times regularly.

### 250. Approximate query processing on graphs (sampling with error bounds)

**Definition:** Answering aggregate graph queries (counts, averages, distributions) quickly from samples, with stated error bounds, instead of exact full scans.

**How it works:**
1. Choose a sampling scheme matching the query: uniform vertices, edges, random walks (#148), or the precomputed reservoirs and sketches above (#207–210).
2. Compute the answer on the sample.
3. Scale up with unbiased estimators (inverse inclusion probabilities).
4. Compute confidence intervals (closed-form variance or bootstrap).
5. **Progressive refinement:** keep sampling until the interval is narrow enough, or the time budget runs out.

**Complexity:** Proportional to the sample size, independent of graph size.

**Agent use:**
- **Role:** Analyst.
- **How:** Interactive exploration of huge graphs ("roughly how many accounts have more than 1,000 connections?") in seconds, before deciding whether an exact run is worth it.
- **Rules:** Always show the confidence interval (GR4).
- **Guardrails:** Never use approximate answers for decisions requiring exact counts (billing, compliance) without an exact run.

---

Part 6 (#251–300) covers graph embeddings (spectral, LINE, struc2vec, matrix factorization methods, NetMF, ProNE, large-scale partitioned training), advanced GNNs (GIN, APPNP, SGC, heterophily-aware models, positional encodings, higher-order and subgraph GNNs, masked graph pretraining), probabilistic graphical models (belief propagation, junction trees, variable elimination, Gibbs sampling, mean-field inference, CRFs), causal graphs (d-separation, PC/FCI, do-calculus), graph construction from data (graphical lasso, NN-descent), graph-based ranking and recommendation (TextRank, Pixie, P3α/RP3β, PRA, PathSim), network alignment, and program analysis on graphs (IFDS, CFL-reachability, points-to analysis).