# Part 3: Centrality, similarity, dense structures, network measures and random graph models (#101–150)

Same format and the same contract (roles; rules GR1–GR8; guardrails GX1–GX5).

## C1. Centrality and ranking

### 101. Weighted degree (strength) and normalized degree

**Definition:** Measuring a vertex's direct connectedness by its edge count or total edge weight, separately for incoming and outgoing edges.

**How it works:**
1. **Degree:** the number of edges. **In-degree / out-degree:** separate counts for directed graphs.
2. **Strength:** the sum of edge weights (traffic volume, transaction amount).
3. **Normalization:** divide by n−1 (the maximum possible), or compare to a percentile within the vertex's type.
4. **Average neighbor degree:** shows whether hubs connect to hubs.

**Complexity:** O(n + m).

**Agent use:**
- **Role:** Analyst.
- **How:** The first look at any graph: who's most connected, which vertices are supernodes (GX2), and how skewed the distribution is (#135).
- **Rules:** Compare within vertex types. Degrees of people and of countries aren't comparable.
- **Guardrails:** Degree alone isn't importance. Combine it with other measures before ranking.

### 102. PageRank in depth (power iteration, dangling vertices, convergence)

**Definition:** The full computation details of PageRank (K#74): getting correct, fast, reproducible scores on real graphs.

**How it works:**
1. Represent the transition matrix implicitly through CSC (pull) or CSR (push) structures (#2).
2. **Dangling vertices** (no out-edges) spread their score uniformly, or to a personalization vector. Handle them explicitly each iteration.
3. **Power iteration:** r ← (1−d)·v + d·(Mᵀr + dangling mass). Stop when the L1 change < ε.
4. **Gauss-Seidel / asynchronous updates:** use freshly updated values within the same iteration. Converges in fewer iterations.
5. Convergence rate is governed by d (damping). With d = 0.85, about 50–100 iterations for ε = 10⁻⁸ is typical.
6. **Weighted PageRank:** transitions proportional to edge weights.

**Complexity:** O(m) per iteration.

**Agent use:**
- **Role:** Analyst.
- **How:** Global importance scores for ranking entities, documents, packages or services.
- **Rules:** Record d, ε, the iteration count and the snapshot (GR1, GR5).
- **Guardrails:** Spam rings and duplicate entities inflate scores. Clean the data first, and inspect the top results by hand.

### 103. Push-based personalized PageRank (Andersen-Chung-Lang)

**Definition:** Computing personalized PageRank (K#75) approximately by pushing "residual" mass locally from the seed, touching only nearby vertices.

**How it works:**
1. Keep two vectors: estimates p (initially 0) and residuals r (initially 1 at the seed).
2. While some vertex u has a residual r(u) > ε × degree(u):
   - Move α × r(u) into p(u) (α is the teleport probability).
   - Spread the remaining (1−α) × r(u) to u's neighbors' residuals (half kept at u in the "lazy" version).
   - Set r(u) to 0 or its lazy share.
3. Stop when every residual is below its threshold. The error is bounded by ε times the degrees.
4. The total work is independent of the graph's size.

**Complexity:** O(1/(α ε)) pushes, independent of n.

**Agent use:**
- **Role:** Analyst and Retriever.
- **How:** Fast, local relevance around seed entities, the standard way to pick a relevant subgraph for GraphRAG (K#157). Also the basis of local clustering (#161).
- **Rules:** Report ε (GR4). Use degree-normalized scores when comparing vertices.
- **Guardrails:** Pushes into supernodes spread mass to millions of neighbors. Cap or skip hubs (GX2).

### 104. Monte Carlo and bidirectional PPR estimation (FORA style)

**Definition:** Estimating personalized PageRank by combining local pushes with random walks, for accurate scores at low cost.

**How it works:**
1. **Monte Carlo:** run many random walks from the seed. Each stops with probability α at every step. The fraction of walks ending at v estimates PPR(seed, v).
2. **Forward push first** (#103), with a coarse threshold, which leaves small residuals.
3. **Then random walks** from vertices with leftover residual, weighted by that residual, to correct the estimate.
4. **Bidirectional:** for a single target t, combine backward pushes from t with forward walks from the seed.
5. These give error guarantees with high probability, at far lower cost than walks alone.

**Complexity:** Sublinear per query in practice.

**Agent use:**
- **Role:** Analyst.
- **How:** Fast, accurate PPR queries at scale, for recommendations, relevance ranking and similarity.
- **Rules:** Report the error and confidence parameters (GR4), and fix seeds (GR5).
- **Guardrails:** None specific.

### 105. SimRank

**Definition:** A similarity measure based on the idea that "two vertices are similar if they are referenced by similar vertices".

**How it works:**
1. s(a, a) = 1.
2. s(a, b) = C / (|In(a)| × |In(b)|) × Σ over in-neighbors i of a and j of b of s(i, j). C (about 0.6–0.8) is a decay constant.
3. Iterate from s = identity until it converges.
4. Random walk interpretation: s(a, b) relates to the expected meeting time of two random walks moving backward from a and b.
5. Fast variants: Monte Carlo walks, single-source SimRank, and linearized SimRank.

**Complexity:** The naive version costs O(k × n² × d²) and needs O(n²) memory. Only the approximate versions scale.

**Agent use:**
- **Role:** Analyst.
- **How:** Finds structurally similar items (products, papers, entities) from link structure alone, without content.
- **Rules:** Use single-source or top-k approximate versions on large graphs.
- **Guardrails:** All-pairs SimRank on large graphs is infeasible (GR3).

### 106. HITS and SALSA

**Definition:** Link analysis with two scores per vertex: hub (points to good authorities) and authority (pointed to by good hubs). SALSA is a random-walk variant that resists some manipulation.

**How it works:**
1. **HITS:** authority = Σ hub scores of in-neighbors. Hub = Σ authority scores of out-neighbors. Normalize and iterate. They converge to the principal eigenvectors of AᵀA and AAᵀ.
2. **SALSA:** build the bipartite hub–authority graph, and run alternating two-step random walks (hub → authority → hub). Scores come from the walk's stationary distribution, which reduces to degree-like measures within connected components.
3. Usually run on a topic-focused subgraph (the query results and their neighborhoods).

**Complexity:** O(m) per iteration.

**Agent use:**
- **Role:** Analyst.
- **How:** Separates curators (hubs: index pages, list owners, aggregators) from sources (authorities), for example finding authoritative documentation pages and good link lists.
- **Rules:** Run on query-focused subgraphs.
- **Guardrails:** HITS is sensitive to densely interlinked clusters ("tightly knit community" effect). Use SALSA, or combine signals.

### 107. Katz centrality

**Definition:** Importance from all paths reaching a vertex, with longer paths counting exponentially less.

**How it works:**
1. x = Σ over k ≥ 1 of αᵏ (Aᵀ)ᵏ 𝟏, or equivalently x = α Aᵀ x + β.
2. α must be less than 1 / λ_max (the largest eigenvalue), or the sum diverges.
3. Compute it by iteration: x ← α Aᵀ x + β, until it converges.
4. The constant β gives every vertex a baseline score, which handles vertices that eigenvector centrality would score as 0 (in DAGs, for example).

**Complexity:** O(m) per iteration.

**Agent use:**
- **Role:** Analyst.
- **How:** Influence measures in directed graphs where eigenvector centrality fails (citation graphs, dependency graphs).
- **Rules:** Estimate λ_max first (by power iteration) and choose α safely below 1/λ_max.
- **Guardrails:** α too close to the limit makes the iteration slow or unstable.

### 108. Eigenvector centrality and non-backtracking centrality

**Definition:** Importance from being connected to important vertices, computed as the principal eigenvector of the adjacency matrix. The non-backtracking variant fixes localization on hubs.

**How it works:**
1. x = (1/λ) A x. Compute by power iteration with normalization.
2. By the Perron-Frobenius theorem, for a connected graph, the principal eigenvector is positive and unique.
3. **Localization problem:** on graphs with hubs, the eigenvector concentrates on a hub and its neighbors, which is misleading.
4. **Non-backtracking (Hashimoto) matrix:** walks may not immediately return along the edge they came from. Its leading eigenvector spreads importance more meaningfully.

**Complexity:** O(m) per iteration. The non-backtracking matrix has 2m × 2m dimensions, but there are efficient reduced forms.

**Agent use:**
- **Role:** Analyst.
- **How:** Influence in undirected networks. The non-backtracking variant is more reliable on graphs with large hubs.
- **Rules:** Use it only on connected components. Disconnected graphs need per-component computation.
- **Guardrails:** Check for localization: if most of the score sits on a few vertices, switch measures.

### 109. Brandes betweenness (weighted and edge variants)

**Definition:** The exact computation of betweenness centrality (K#76) for vertices and edges, for weighted and unweighted graphs.

**How it works:**
1. For each source s: run BFS (unweighted) or Dijkstra (weighted). Record σ(v), the number of shortest paths from s to v, and the predecessor lists.
2. Process vertices in reverse order of distance, accumulating dependencies: δ(v) = Σ over successors w of (σ(v)/σ(w)) × (1 + δ(w)).
3. Add δ(v) to v's betweenness score (excluding s).
4. **Edge betweenness:** the same accumulation, assigned to edges.
5. Normalize by the number of vertex pairs.

**Complexity:** O(n × m) unweighted, O(n × m + n² log n) weighted.

**Agent use:**
- **Role:** Analyst.
- **How:** Exact broker and bottleneck identification on moderate-sized graphs, and the edge version drives Girvan-Newman (#153).
- **Rules:** Check GR3: the cost is quadratic or worse.
- **Guardrails:** Use the approximations (#110) on large graphs.

### 110. Approximate betweenness (Riondato-Kornaropoulos, KADABRA)

**Definition:** Estimating betweenness with guaranteed accuracy by sampling shortest paths instead of computing all of them.

**How it works:**
1. Sample a random pair of vertices (s, t), then one shortest path between them uniformly at random.
2. Give +1 to every interior vertex of that path.
3. Repeat r times. Normalized counts estimate betweenness.
4. **Riondato-Kornaropoulos:** chooses r from the graph's vertex diameter using VC-dimension bounds, giving ±ε error for all vertices with probability 1−δ.
5. **KADABRA:** adaptive sampling, with balanced bidirectional BFS to sample paths fast. It stops as soon as the needed accuracy is reached.

**Complexity:** Sample count independent of n for a fixed ε. Each sample costs about one bidirectional BFS.

**Agent use:**
- **Role:** Analyst.
- **How:** Practical betweenness on graphs with millions of vertices, typically for top-k broker detection.
- **Rules:** Report ε and δ (GR4). Use for ranking, not exact values.
- **Guardrails:** Fix seeds for reproducibility (GR5).

### 111. Closeness centrality via HyperBall (HyperLogLog counters)

**Definition:** Approximating closeness and harmonic centrality (K#77) for all vertices, using small probabilistic counters of reachable sets.

**How it works:**
1. Each vertex gets a HyperLogLog counter estimating the set of vertices it can reach within t steps.
2. At t = 0, each counter contains only its own vertex.
3. Each round: every vertex's counter = the union (register-wise maximum) of its own and its neighbors' counters.
4. The change in counter size between rounds gives the number of vertices at exactly distance t.
5. Sum the contributions: harmonic centrality += (count at distance t) / t.
6. Stop when no counter changes.

**Complexity:** O(m × diameter) operations on small counters. Memory O(n × counter size).

**Agent use:**
- **Role:** Analyst.
- **How:** All-vertex closeness or harmonic centrality, and distance distributions (#136), on billion-edge graphs.
- **Rules:** Report the counter error (HyperLogLog standard error ≈ 1.04/√registers) (GR4).
- **Guardrails:** None specific.

### 112. Current-flow (random-walk) betweenness and closeness

**Definition:** Centrality based on electrical current flow, which counts all paths weighted by how much current they carry, not just shortest paths.

**How it works:**
1. Treat edges as resistors (conductance = weight).
2. For each pair (s, t), inject one unit of current at s and extract it at t. Solve the Laplacian system L·v = b for the potentials (#178).
3. Current through each edge = conductance × potential difference.
4. **Current-flow betweenness:** the average current passing through a vertex over all pairs.
5. **Current-flow closeness:** based on effective resistances (#179).
6. Approximations use random projections and fast Laplacian solvers.

**Complexity:** Exact versions are cubic or worse. Approximations are near-linear per solve.

**Agent use:**
- **Role:** Analyst.
- **How:** More robust importance when traffic or information spreads along many routes, not just the shortest ones (diffusion, redundant networks).
- **Rules:** Use the approximate solvers on large graphs.
- **Guardrails:** Requires a connected graph. Compute per component.

### 113. Influence maximization (IC/LT models, CELF, reverse influence sampling)

**Definition:** Choosing k seed vertices that maximize the expected spread of a cascade in a diffusion model.

**How it works:**
1. **Diffusion models:** independent cascade (each newly activated vertex gets one chance to activate each neighbor with probability p) or linear threshold (a vertex activates when the weighted fraction of active neighbors exceeds its threshold).
2. The expected spread is submodular (diminishing returns), so greedy selection gives at least (1 − 1/e) ≈ 63% of the optimum.
3. **CELF:** lazy greedy. Cache marginal gains, and recompute only the top candidate's, since gains can only decrease.
4. **Reverse influence sampling (RIS, IMM):** sample random "reverse reachable" sets (the vertices that would have activated a random target). Picking seeds that cover the most sets is near-optimal, with far fewer simulations.

**Complexity:** IMM is near-linear in the graph size times k/ε².

**Agent use:**
- **Role:** Optimizer.
- **How:** Choosing where to start a rollout, announcement or cache warm-up for maximum reach, or the reverse: which vertices to protect first to limit spread (of failures or misinformation).
- **Rules:** Report the approximation guarantee and the model assumptions (GR4).
- **Guardrails:** Targeting people based on influence needs ethical and policy review (GX3, GX4).

### 114. Spreader ranking by coreness and collective influence

**Definition:** Identifying vertices that best spread (or block) diffusion, using core position and nonlocal measures instead of degree alone.

**How it works:**
1. **Coreness (k-shell index, K#84):** vertices in the innermost cores tend to be better spreaders than high-degree vertices on the periphery.
2. **Collective influence (CI):** CI_ℓ(v) = (degree(v) − 1) × Σ (degree(u) − 1) over vertices u at distance ℓ. Repeatedly remove the top-CI vertex and update the scores, which approximates optimal percolation (breaking the graph apart).
3. Compare rankings by simulating spread (#147).

**Complexity:** Coreness O(m). CI with updates is about O(n log n) with heaps.

**Agent use:**
- **Role:** Analyst.
- **How:** Finds which vertices to monitor or protect to stop spreading failures or attacks, or where to seed propagation.
- **Rules:** Validate rankings with simulation on the actual graph.
- **Guardrails:** Same as #113 for decisions affecting people.

## C2. Similarity, roles and local structure

### 115. Local similarity indices (Jaccard, Salton, Sørensen, hub-promoted)

**Definition:** Similarity of two vertices measured from their shared neighbors, normalized in various ways.

**How it works:**
1. Let N(x) and N(y) be the neighbor sets.
2. **Jaccard:** |N(x) ∩ N(y)| / |N(x) ∪ N(y)|.
3. **Salton (cosine):** |∩| / √(|N(x)| × |N(y)|).
4. **Sørensen:** 2|∩| / (|N(x)| + |N(y)|).
5. **Hub-promoted / hub-depressed:** divide by the min or max degree.
6. Computed fast with sorted-list intersection or bitmaps (#8). Many pairs at once with sparse matrix products, or MinHash for approximation (C#31).

**Complexity:** O(degree(x) + degree(y)) per pair.

**Agent use:**
- **Role:** Analyst.
- **How:** Duplicate detection (entities with nearly identical neighborhoods), "related items", and link prediction features (K#131).
- **Rules:** Pick the index matching the degree distribution. Jaccard penalizes pairs with very different degrees.
- **Guardrails:** All-pairs similarity is O(n²) pairs. Use candidate generation (MinHash LSH) first.

### 116. Global similarity indices (Katz index, local path index, LHN)

**Definition:** Similarity from paths of several lengths between two vertices, not just shared neighbors.

**How it works:**
1. **Katz index:** S = Σ over k of βᵏ Aᵏ = (I − βA)⁻¹ − I. Counts all paths, damped by length.
2. **Local path index:** only paths of length 2 and 3: S = A² + εA³. Much cheaper.
3. **Leicht-Holme-Newman (LHN):** paths normalized by the expected number of paths in a random graph with the same degrees.
4. Computed per query vertex (one row) with sparse matrix-vector products, not the full matrix.

**Complexity:** Full matrices are infeasible for large graphs. Per-row computation is about O(k × m).

**Agent use:**
- **Role:** Analyst.
- **How:** Stronger link prediction and relatedness when direct neighbors are sparse (new entities with few links).
- **Rules:** Compute per query vertex. Never the full matrix on large graphs (GR3).
- **Guardrails:** None specific.

### 117. Graph diffusion kernels (heat kernel, regularized Laplacian, von Neumann)

**Definition:** Similarity matrices defined by diffusion processes on the graph: how much "heat" or probability flows from one vertex to another.

**How it works:**
1. **Heat (diffusion) kernel:** K = exp(−t L), where L is the graph Laplacian and t is the diffusion time.
2. **Regularized Laplacian:** K = (I + γL)⁻¹.
3. **Von Neumann (similar to Katz):** K = (I − αA)⁻¹.
4. For one vertex, compute its row with Krylov methods (Lanczos), Chebyshev polynomial approximations, or truncated Taylor series. No full matrix.
5. Larger t (or γ) means more global smoothing.

**Complexity:** O(k × m) per row with k-term polynomial approximations.

**Agent use:**
- **Role:** Analyst.
- **How:** Smooth relevance propagation (spreading scores from seeds), denoising per-vertex signals, and similarity for retrieval.
- **Rules:** Choose t by validation on a known task.
- **Guardrails:** Use the normalized Laplacian on graphs with skewed degrees, or hubs dominate.

### 118. Role discovery (RolX) and structural equivalence

**Definition:** Grouping vertices by their structural position (for example "hub", "bridge", "peripheral"), regardless of where they are in the graph.

**How it works:**
1. **Structural equivalence:** two vertices have exactly the same neighbors. Find it by hashing sorted neighbor lists.
2. **RolX:** compute features for each vertex: degree, ego-network edge counts, and recursive aggregates (sums and means of neighbors' features, repeated).
3. Factorize the vertex × feature matrix with non-negative matrix factorization. Each factor is a role, and each vertex gets a mix of roles.
4. Choose the number of roles with a model selection criterion (minimum description length).

**Complexity:** About O(m × iterations) for the features, plus the factorization.

**Agent use:**
- **Role:** Analyst.
- **How:** Finds vertices that play the same role in different places, such as gateway services in different clusters, coordinators in different teams, or accounts with the same behavioral pattern.
- **Rules:** Explain roles through their top features, so they can be interpreted.
- **Guardrails:** Roles describe structure, not intent. Don't use them as accusations (GX3).

### 119. Regular equivalence and role similarity

**Definition:** Two vertices are regularly equivalent if they connect to equivalent vertices, even if not the same ones. For example, two managers, each with their own team.

**How it works:**
1. Start with all vertices similar (or with an initial partition by type).
2. Iteratively refine: two vertices remain similar if every neighbor of one has a similar counterpart among the neighbors of the other.
3. **REGE algorithm:** an iterative similarity version of this. **Partition refinement:** an exact coloring version (related to the Weisfeiler-Lehman refinement, K#140).
4. It converges to the coarsest equivalence consistent with the structure.

**Complexity:** About O(m log n) for partition refinement versions.

**Agent use:**
- **Role:** Analyst.
- **How:** Compares positions across different parts of an organization or system ("these two services play the same role in their respective stacks").
- **Rules:** Initialize with meaningful types if available.
- **Guardrails:** None specific.

### 120. Graphlet counting and graphlet degree vectors (ORCA)

**Definition:** Counting small connected subgraph patterns (graphlets) and how often each vertex appears in each position (orbit) of each pattern.

**How it works:**
1. Graphlets are all small connected shapes (for example the 30 graphlets with 2–5 vertices) with their 73 orbits (structural positions).
2. **ORCA:** counts the orbits for every vertex using a system of linear equations relating the orbit counts, so only a few counts are enumerated directly, and the rest are derived.
3. The **graphlet degree vector** of a vertex is its count in every orbit, a detailed structural fingerprint.
4. Graphlet frequency distributions compare whole networks.

**Complexity:** Roughly O(m × d³) for 5-vertex graphlets, where d is the maximum degree.

**Agent use:**
- **Role:** Analyst.
- **How:** Detailed structural features for classification and anomaly detection, and for comparing networks (is this transaction graph shaped like normal ones?).
- **Rules:** Normalize per-vertex counts when comparing vertices of different degrees.
- **Guardrails:** Cost explodes with high-degree vertices. Check GR3 and cap the degree.

### 121. Exact triangle counting (forward / compact-forward with degree ordering)

**Definition:** Counting all triangles (three mutually connected vertices) in a graph efficiently.

**How it works:**
1. Order the vertices by degree (ties broken by ID).
2. Orient each edge from the lower-ranked to the higher-ranked endpoint. Each vertex keeps only its "forward" neighbors, so high-degree vertices have short forward lists.
3. For each edge (u, v) in this orientation, count the common forward neighbors of u and v (sorted merge or a hash lookup). Each triangle is counted exactly once.
4. **Per-vertex counts:** credit each found triangle to all three of its vertices.

**Complexity:** O(m^1.5), much faster in practice on skewed graphs because of the degree ordering.

**Agent use:**
- **Role:** Analyst.
- **How:** Triangles measure clustering (#123), are features for spam and fraud detection (fake accounts often have few triangles), and are the basis of k-truss (#127).
- **Rules:** Always use degree ordering.
- **Guardrails:** Without the ordering, hubs cause quadratic blowups.

### 122. Approximate and streaming triangle counting (DOULION, wedge sampling, TRIEST)

**Definition:** Estimating triangle counts with sampling, for huge or streaming graphs.

**How it works:**
1. **DOULION:** keep each edge with probability p, count triangles in the sample exactly, and divide by p³.
2. **Wedge sampling:** sample random wedges (paths of length 2) and check whether they close into triangles. The closure fraction times the total wedge count estimates triangles, and also estimates the global clustering coefficient directly.
3. **TRIEST** (streaming): keep a fixed-size reservoir sample of edges (#210), and update the triangle estimates as edges arrive and are evicted, with correction factors.
4. The variance shrinks with the sample size.

**Complexity:** Sublinear memory. Constant memory for TRIEST.

**Agent use:**
- **Role:** Analyst.
- **How:** Monitoring clustering on streams (transaction or communication graphs) without storing the whole graph.
- **Rules:** Report confidence intervals (GR4).
- **Guardrails:** None specific.

### 123. Clustering coefficients (local, global, transitivity)

**Definition:** Measures of how often a vertex's neighbors are also connected to each other.

**How it works:**
1. **Local clustering of v:** triangles(v) / (degree(v) × (degree(v) − 1) / 2). It's the fraction of neighbor pairs that are linked.
2. **Average clustering:** the mean of the local values (watch how low-degree vertices are handled).
3. **Global clustering (transitivity):** 3 × triangles / wedges. Dominated by high-degree vertices.
4. Weighted and directed variants exist.

**Complexity:** Like triangle counting (#121).

**Agent use:**
- **Role:** Analyst.
- **How:** Detects unusually tight or loose neighborhoods: fake accounts (low clustering, many random links), collusion rings (very high clustering), and organizational silos.
- **Rules:** State which definition is used. Average and global clustering can differ a lot.
- **Guardrails:** Compare to null models (#141) before calling a value "high".

### 124. k-clique listing (Chiba-Nishizeki, kClist)

**Definition:** Listing or counting all complete subgraphs of exactly k vertices.

**How it works:**
1. Order the vertices (degeneracy ordering, #125) and orient edges forward, as in triangle counting.
2. **Recursively:** for each vertex v, consider its forward neighbors as the candidate set. Choose the next vertex from the candidates, intersect the candidates with that vertex's forward neighbors, and repeat until k vertices are chosen.
3. **kClist:** builds induced subgraphs on the forward neighborhoods, ordered by core numbers, which makes it efficient and parallel.
4. Each k-clique is found exactly once.

**Complexity:** O(k × m × (c/2)^(k−2)), where c is the degeneracy (small on real graphs).

**Agent use:**
- **Role:** Analyst.
- **How:** Detects tightly knit groups of a fixed size (for example groups of 4–5 accounts all transacting with each other), and counts higher-order structure.
- **Rules:** Count first (cheaper), and list only when needed.
- **Guardrails:** Cap k and the output size (GR7).

### 125. Maximal clique enumeration (Bron-Kerbosch with pivoting and degeneracy ordering)

**Definition:** Listing every clique that can't be extended by adding another vertex.

**How it works:**
1. Keep three sets: R (the current clique), P (candidates that can extend R), X (vertices already processed, so duplicates aren't reported).
2. If P and X are both empty, R is a maximal clique: report it.
3. **Pivoting:** pick a pivot u from P ∪ X with the most neighbors in P. Only branch on vertices in P that aren't neighbors of u. This greatly reduces branching.
4. For each such v: recurse with R ∪ {v}, P ∩ N(v), X ∩ N(v). Then move v from P to X.
5. **Outer loop in degeneracy order:** start each vertex with only its later neighbors as P, which bounds the work by the degeneracy.

**Complexity:** O(d × n × 3^(d/3)), where d is the degeneracy. Very fast on sparse real graphs.

**Agent use:**
- **Role:** Analyst.
- **How:** Finds all fully connected groups: co-occurrence groups, collusion groups, sets of mutually compatible items.
- **Rules:** Report counts and size distribution first. Then list with limits (GR7).
- **Guardrails:** Dense graphs can have exponentially many maximal cliques. Always cap time and output.

### 126. Maximum clique (branch and bound with coloring bounds)

**Definition:** Finding the largest clique in a graph, an NP-hard problem solved exactly on many practical instances.

**How it works:**
1. Branch: add a candidate vertex to the current clique, restricting the candidates to its neighbors.
2. **Bound:** greedily color the candidate set. The number of colors is an upper bound on the largest clique among the candidates, since clique vertices need different colors.
3. Prune a branch if (current clique size + color bound) ≤ the best size found so far.
4. Candidates are processed in color order; MCS and other variants re-color incrementally and use more refined bounds.
5. Preprocessing: k-core pruning (only vertices with coreness ≥ best size − 1 can be in a larger clique).

**Complexity:** Exponential worst case. Often fast on sparse real graphs.

**Agent use:**
- **Role:** Analyst.
- **How:** The largest tightly knit group, and a building block for other problems (maximum independent set in the complement graph, compatibility problems).
- **Rules:** Set a time limit. Report the best found and whether optimality was proven (GR4).
- **Guardrails:** None specific.

### 127. k-truss decomposition

**Definition:** Maximal subgraphs where every edge is part of at least k−2 triangles inside the subgraph: a stronger cohesion notion than k-core.

**How it works:**
1. Compute the support of every edge (the number of triangles containing it, #121).
2. Repeatedly remove edges with support < k−2, updating the support of edges in the triangles they were part of.
3. The remaining edges form the k-truss.
4. **Truss decomposition:** each edge's truss number = the largest k whose k-truss contains it. Computed with bucketed peeling, like k-core.

**Complexity:** O(m^1.5).

**Agent use:**
- **Role:** Analyst.
- **How:** Finds cohesive communities more precisely than k-core (every edge reinforced by triangles). Used in community search and fraud ring detection.
- **Rules:** Use truss numbers as features, alongside core numbers.
- **Guardrails:** None specific.

### 128. Nucleus decomposition (generalized cores and trusses)

**Definition:** A unified hierarchy of dense subgraphs, defined by how many larger cliques each small clique belongs to.

**How it works:**
1. Choose r < s: for example, r = 1 (vertices) and s = 2 (edges) gives k-core; r = 2 (edges) and s = 3 (triangles) gives k-truss; r = 3 and s = 4 gives denser structures.
2. Compute, for each r-clique, how many s-cliques contain it.
3. Peel the r-cliques with the lowest counts, updating the counts of the affected neighbors.
4. The resulting nested "nuclei" form a hierarchy (forest) of increasingly dense regions.

**Complexity:** Depends on (r, s). (3, 4) is expensive but gives very dense, meaningful structures.

**Agent use:**
- **Role:** Analyst.
- **How:** Multi-level views of dense regions, from loose clusters to very tight cores, useful for exploring community structure (#151 onward).
- **Rules:** Start with (1, 2) and (2, 3), and only go higher if needed.
- **Guardrails:** Check GR3 for higher (r, s) values.

### 129. Densest subgraph (Goldberg exact, Charikar peeling, Greedy++)

**Definition:** Finding the subgraph with the highest average degree (edges divided by vertices).

**How it works:**
1. **Goldberg (exact):** binary search on the density value g. Test "is there a subgraph with density > g?" with one min-cut each. Exact but costly.
2. **Charikar's greedy peeling:** repeatedly remove the minimum-degree vertex, tracking the density of what remains. The best intermediate subgraph is a 2-approximation. Linear time.
3. **Greedy++:** repeat the peeling, with vertex loads accumulated across rounds. Converges to the optimum.
4. Directed and weighted versions exist.

**Complexity:** Peeling O(m + n) per round with bucket queues. Exact: several max-flows.

**Agent use:**
- **Role:** Analyst.
- **How:** Finds suspiciously dense activity: bot groups, fake reviews, coordinated accounts, link farms. Also finds the core of a topic.
- **Rules:** Report the density with a baseline comparison.
- **Guardrails:** A dense subgraph is a signal, not proof (GR8, GX3).

### 130. Camouflage-resistant dense block detection (Fraudar)

**Definition:** Detecting dense blocks of fraudulent behavior in bipartite graphs (users–items), even when fraudsters add normal-looking "camouflage" edges.

**How it works:**
1. Score a subgraph by its edge density, with edges to popular items down-weighted (for example by 1/log(item degree + c)). Camouflage edges usually point to popular legitimate items, so they count little.
2. Greedily peel the vertex whose removal reduces the score the least (like #129), using a priority tree.
3. Keep the subgraph with the best score seen.
4. Remove it and repeat to find further blocks.
5. It has guarantees about how much camouflage can hide a fraud block.

**Complexity:** O(m log n).

**Agent use:**
- **Role:** Analyst.
- **How:** Detects fake follower and review rings, click fraud, and coordinated inauthentic behavior in user–item interaction graphs.
- **Rules:** Present blocks with evidence (edge counts, timing, shared attributes) to human reviewers.
- **Guardrails:** Enforcement decisions are human decisions (GR8, GX4).

### 131. Quasi-clique mining

**Definition:** Finding groups that are almost cliques: each vertex connected to at least a fraction γ of the others in the group.

**How it works:**
1. Define a γ-quasi-clique: every vertex is adjacent to at least γ × (size − 1) others inside the group.
2. Search with branch and bound, with pruning: minimum degree requirements, diameter bounds (γ ≥ 0.5 implies diameter ≤ 2), and core-based pruning.
3. Enumerate maximal quasi-cliques, or find the largest one.
4. Approximations use local search, starting from dense seeds.

**Complexity:** NP-hard. Practical with strong pruning on sparse graphs.

**Agent use:**
- **Role:** Analyst.
- **How:** Real groups are rarely perfect cliques (a missing edge or two). Quasi-cliques find realistic tight groups: protein complexes, collusion groups, project teams.
- **Rules:** Set γ and the minimum size explicitly, and justify them.
- **Guardrails:** Cap time and output (GX1, GR7).

### 132. Motif counting and statistical significance

**Definition:** Counting small subgraph patterns and testing whether they occur more (or less) often than expected by chance.

**How it works:**
1. Count the occurrences of each pattern of 3–4 vertices (directed motifs such as feed-forward loops or cycles), with algorithms like ESU or FANMOD.
2. Generate many randomized graphs with the same degree sequence (#141).
3. Count the same patterns in each.
4. Z-score = (real count − mean random count) / standard deviation. Large positive values are "motifs"; large negative values are "anti-motifs".
5. The motif profile characterizes the network's function.

**Complexity:** Dominated by the counting, repeated over the random samples.

**Agent use:**
- **Role:** Analyst.
- **How:** Discovers characteristic patterns in a system: unusual feedback loops in dependency graphs, recurring transaction shapes, regulatory patterns.
- **Rules:** Use a proper null model (degree-preserving) and enough random samples.
- **Guardrails:** Many patterns tested at once require multiple-comparison correction.

## C3. Network-level measures

### 133. Assortativity coefficient

**Definition:** The correlation between the degrees (or attributes) of connected vertices: do similar vertices connect to each other?

**How it works:**
1. For each edge, take the pair of endpoint degrees (or attribute values).
2. Assortativity r = the Pearson correlation of those pairs (directed versions use out-degree and in-degree).
3. r > 0: hubs connect to hubs (assortative, typical of social networks). r < 0: hubs connect to low-degree vertices (disassortative, typical of technical and biological networks).
4. Attribute assortativity uses a categorical version (mixing matrices).

**Complexity:** O(m).

**Agent use:**
- **Role:** Analyst.
- **How:** Characterizes structure for resilience (assortative networks have redundant cores; disassortative ones are vulnerable to hub failures) and checks how mixed groups are.
- **Rules:** Compare to null models.
- **Guardrails:** Attribute assortativity on protected attributes is sensitive (GX3).

### 134. Rich-club coefficient

**Definition:** Whether high-degree vertices are more densely connected to each other than expected.

**How it works:**
1. For each degree threshold k, take the vertices with degree > k.
2. φ(k) = (edges among them) / (maximum possible edges among them).
3. Normalize by φ for degree-preserving randomized graphs (#141): ρ(k) = φ(k) / φ_random(k).
4. ρ > 1 at high k means a rich club.

**Complexity:** O(m) per threshold, plus the randomized graphs.

**Agent use:**
- **Role:** Analyst.
- **How:** Reveals whether the core vertices (major services, key people, top accounts) form a tightly connected elite, which matters for resilience and for influence.
- **Rules:** Always use the normalized version.
- **Guardrails:** None specific.

### 135. Degree distribution fitting (Clauset-Shalizi-Newman power-law method)

**Definition:** Rigorously testing whether a degree distribution follows a power law, and estimating its parameters.

**How it works:**
1. For each candidate lower cutoff x_min, estimate the exponent α by maximum likelihood.
2. Choose the x_min that minimizes the Kolmogorov-Smirnov distance between the data and the fitted model.
3. Test goodness of fit with a bootstrap: generate synthetic data from the fit and compare KS distances (giving a p-value).
4. Compare against alternatives (log-normal, exponential, power law with cutoff) with likelihood ratio tests.

**Complexity:** O(n log n) per candidate x_min. The bootstrap repeats the fit many times.

**Agent use:**
- **Role:** Analyst.
- **How:** Correctly characterizes heavy-tailed graphs, which affects capacity planning (hub sizes), sampling strategies and algorithm choice.
- **Rules:** Never claim "scale-free" from a straight line on a log-log plot. Use this method.
- **Guardrails:** Report the alternatives tested and their likelihood ratios (GR4).

### 136. Effective diameter and distance distribution (HyperANF)

**Definition:** Approximating the full distribution of pairwise distances, and the effective diameter (the distance within which, say, 90% of pairs are connected).

**How it works:**
1. Use the HyperLogLog neighborhood counters from #111.
2. After round t, the total of all counters estimates the number of pairs within distance t.
3. The differences between rounds give the distance distribution.
4. Effective diameter = the (interpolated) distance at which the cumulative fraction reaches 90%.
5. The average distance comes from the same distribution.

**Complexity:** O(m × diameter) counter operations.

**Agent use:**
- **Role:** Analyst.
- **How:** Tells how "small" a graph is. Guides traversal depth limits (K6, GX1) and spreading-speed expectations.
- **Rules:** Report the estimation error (GR4).
- **Guardrails:** None specific.

### 137. Exact diameter (double sweep, iFUB)

**Definition:** Computing the exact largest shortest-path distance in a large graph, usually with only a few BFS runs.

**How it works:**
1. **Double sweep:** BFS from any vertex, find the farthest vertex u; BFS from u to find the farthest vertex v. The distance d(u, v) is a lower bound, and often the diameter itself.
2. **iFUB (iterative fringe upper bound):** choose a central vertex c and BFS from it, grouping vertices by distance (the "fringes").
3. Process fringes from the farthest inward, running BFS from those vertices to tighten the lower bound.
4. Stop when the lower bound is at least 2 × (the current fringe distance), which is the upper bound for anything not yet checked.

**Complexity:** O(n × m) worst case. In practice, often a handful of BFS runs.

**Agent use:**
- **Role:** Analyst.
- **How:** Exact worst-case hop distance: the maximum propagation depth or the longest dependency chain in an undirected structure.
- **Rules:** Use the double sweep for a quick bound, and iFUB when exactness is needed.
- **Guardrails:** For directed graphs, use the directed variants, and handle unreachable pairs explicitly.

### 138. Eccentricity bounding (Takes-Kosters)

**Definition:** Computing every vertex's eccentricity (its maximum distance to any other vertex) using bounds, so most vertices never need their own BFS.

**How it works:**
1. Every vertex has a lower and an upper bound on its eccentricity.
2. After a BFS from vertex w, for every v: e(v) ≥ max(d(v, w), e(w) − d(v, w)) and e(v) ≤ e(w) + d(v, w).
3. Vertices whose bounds meet are resolved.
4. Choose the next BFS source smartly: alternate between the vertices with the largest upper bound and the smallest lower bound.
5. Repeat until all are resolved. The center, periphery, radius and diameter come out of the same result.

**Complexity:** Often a few dozen BFS runs on real graphs.

**Agent use:**
- **Role:** Analyst.
- **How:** Finds the most central locations (lowest eccentricity) for placing services, caches or coordinators, and the most peripheral ones.
- **Rules:** Run on the largest connected component.
- **Guardrails:** None specific.

### 139. Small-world measures (σ and ω)

**Definition:** Quantifying whether a graph has both high clustering and short path lengths, compared with random and lattice reference graphs.

**How it works:**
1. Compute the average clustering C (#123) and the average shortest path length L (#136).
2. Compute C_rand and L_rand for degree-matched random graphs (#141).
3. **σ = (C / C_rand) / (L / L_rand).** σ > 1 suggests small-world structure.
4. **ω = L_rand / L − C / C_lattice.** Near 0 is small-world, near −1 is lattice-like, near +1 is random-like.

**Complexity:** Dominated by computing L and the reference graphs.

**Agent use:**
- **Role:** Analyst.
- **How:** Characterizes how information or failures propagate (small-world networks spread fast), which helps choose models and depth limits.
- **Rules:** Use ω over σ when possible (σ depends strongly on graph size).
- **Guardrails:** Report the reference models used (GR4).

### 140. Bow-tie decomposition (directed graph structure)

**Definition:** Splitting a directed graph into a giant strongly connected core, plus the regions feeding into it (IN), reached from it (OUT), and the rest (tendrils, tubes, disconnected parts).

**How it works:**
1. Find the largest SCC (#57): the CORE.
2. **IN:** vertices that can reach the core but aren't in it (BFS backward from the core).
3. **OUT:** vertices reachable from the core but not in it (BFS forward).
4. **Tendrils:** vertices reachable from IN, or reaching OUT, without passing through the core. **Tubes:** paths from IN to OUT that avoid the core.
5. **Disconnected:** everything else.

**Complexity:** O(n + m).

**Agent use:**
- **Role:** Analyst.
- **How:** Understands flow structure in directed systems: web links, citations, money flows, dependency graphs (IN = sources, CORE = the tightly coupled center, OUT = consumers).
- **Rules:** Report the size of each region.
- **Guardrails:** None specific.

## C4. Random graph models and null models

### 141. Configuration model and degree-preserving rewiring

**Definition:** Generating random graphs with exactly the same degree sequence as a real graph, to serve as a null model.

**How it works:**
1. **Configuration model:** give each vertex "stubs" equal to its degree, and pair stubs uniformly at random. Self-loops and multi-edges can occur; remove them or use simple-graph variants.
2. **Degree-preserving rewiring (edge swaps):** repeatedly pick two edges (a, b) and (c, d) and swap them to (a, d) and (c, b), if no duplicate edges or self-loops result. About 10 × m swaps randomize the graph.
3. The result keeps every vertex's degree but destroys other structure.

**Complexity:** O(m) for the configuration model. O(swaps) for rewiring.

**Agent use:**
- **Role:** Analyst.
- **How:** The essential baseline for "is this structure significant?": clustering, motifs (#132), rich clubs (#134), community strength.
- **Rules:** Always compare observed statistics to null-model distributions, never to intuition.
- **Guardrails:** Use enough null samples for stable estimates, and fix seeds (GR5).

### 142. Generative graph models (Erdős–Rényi, Barabási–Albert, Watts–Strogatz, Kronecker)

**Definition:** Standard random graph models for testing algorithms, generating synthetic data and understanding structure.

**How it works:**
1. **Erdős–Rényi G(n, p):** each possible edge exists independently with probability p. Poisson degrees, little clustering.
2. **Barabási–Albert:** vertices arrive one at a time, attaching to existing vertices with probability proportional to degree (preferential attachment). Gives power-law degrees.
3. **Watts–Strogatz:** start with a ring lattice and rewire each edge with probability β. Gives high clustering with short paths (small-world).
4. **Kronecker / R-MAT:** recursive matrix products (or recursive quadrant choices) produce realistic skewed degrees and community-like structure at large scale. The Graph500 benchmark uses this.

**Complexity:** About O(m) generation for each.

**Agent use:**
- **Role:** Builder.
- **How:** Synthetic graphs for testing algorithms and pipelines at scale, benchmarking (GR3 cost validation), and privacy-safe test data.
- **Rules:** Choose the model matching the real graph's properties (degree skew, clustering).
- **Guardrails:** Never present synthetic results as real-data findings.

### 143. Exponential random graph models (ERGM)

**Definition:** Statistical models of networks where the probability of a graph depends on its counts of chosen structures (edges, triangles, stars, attribute-based ties).

**How it works:**
1. P(G) ∝ exp(Σ θ_i × statistic_i(G)): for example θ₁ × edges + θ₂ × triangles + θ₃ × same-department ties.
2. Estimate θ by maximum likelihood with MCMC (sampling graphs and comparing their statistics with the observed graph).
3. Interpret the coefficients: a positive triangle coefficient means friends of friends tend to connect, beyond chance.
4. Goodness of fit: simulate from the model and compare with the observed graph's other properties.
5. Degeneracy (models that put all mass on empty or complete graphs) is avoided with curved statistics (GWESP and similar).

**Complexity:** Expensive. MCMC-based estimation suits graphs with up to tens of thousands of vertices.

**Agent use:**
- **Role:** Analyst.
- **How:** Explains why ties form (homophily, transitivity, reciprocity) with statistical evidence: social and organizational analysis.
- **Rules:** Report coefficients with uncertainty and goodness-of-fit results (GR4).
- **Guardrails:** Models involving protected attributes need governance review (GX3).

### 144. Percolation and robustness analysis

**Definition:** Measuring how a network breaks apart as vertices or edges are removed, randomly (failures) or deliberately (attacks).

**How it works:**
1. Remove vertices or edges in some order: random, by degree, by betweenness, or adaptive (recompute after each removal).
2. Track the size of the largest connected component as the removal fraction grows.
3. The **percolation threshold** is where the giant component collapses.
4. Efficient method (Newman-Ziff): add vertices back in reverse order using union-find (#51), giving the whole curve in near-linear time.
5. **Robustness index R:** the area under the giant-component curve.

**Complexity:** O(m × α(n)) for the whole curve with Newman-Ziff.

**Agent use:**
- **Role:** Analyst.
- **How:** Quantifies resilience. Heavy-tailed networks survive random failures well but collapse under targeted attacks on hubs. That guides where to add redundancy.
- **Rules:** Compare random and targeted strategies, with several random seeds.
- **Guardrails:** Results about attack strategies on real infrastructure are sensitive. Restrict access.

### 145. Cascade failure models (load redistribution, Motter-Lai)

**Definition:** Simulating how the failure of one component overloads others, causing chains of failures.

**How it works:**
1. Each vertex (or edge) has a load (for example betweenness, as traffic carried) and a capacity, often (1 + α) × initial load, with α the tolerance.
2. Remove the initial failing elements.
3. Recompute the loads on the remaining network (traffic reroutes).
4. Any element whose new load exceeds its capacity fails.
5. Repeat until no further failures. Record the cascade size.
6. Vary α and the initial failures to map vulnerability.

**Complexity:** One load recomputation per round, which can be expensive (betweenness, #110 approximations help).

**Agent use:**
- **Role:** Analyst.
- **How:** Capacity planning for networks and service meshes: how much headroom (α) prevents one failure from becoming an outage.
- **Rules:** Calibrate loads and capacities from real metrics.
- **Guardrails:** Simulation results are scenarios, not predictions (GR4, GR8).

### 146. Epidemic spreading simulation (SIR/SIS, Gillespie algorithm)

**Definition:** Simulating spreading processes (infection, information, malware) on graphs, with exact event timing.

**How it works:**
1. **States:** S (susceptible), I (infected), R (recovered). In SIS, recovery returns to S.
2. Infection happens along edges at rate β; recovery at rate γ.
3. **Gillespie algorithm:** compute the total event rate, draw the time to the next event from an exponential distribution, choose which event happens in proportion to its rate, update, and repeat. That gives exact continuous-time trajectories.
4. Run many simulations for distributions of outcomes (final size, peak time).
5. The epidemic threshold relates to the largest eigenvalue of the adjacency matrix (or of the non-backtracking matrix, #108).

**Complexity:** O(events × log n) with efficient rate tracking.

**Agent use:**
- **Role:** Analyst.
- **How:** Models how fast something spreads through a network (malware in a host graph, a breaking change in a dependency graph, information in an organization), and evaluates where interventions help most.
- **Rules:** Report distributions, not single runs. Fix seeds (GR5).
- **Guardrails:** Simulations are scenarios (GR8).

### 147. Independent cascade and linear threshold simulation

**Definition:** Monte Carlo simulation of the two standard information diffusion models, used to estimate spread.

**How it works:**
1. **Independent cascade:** seeds start active. Each newly active vertex tries once to activate each inactive neighbor, succeeding with the edge's probability. Continue until no new activations.
2. **Linear threshold:** each vertex draws a random threshold. It activates when the total weight of active in-neighbors reaches it.
3. Repeat thousands of times; average the final number of active vertices.
4. **Live-edge view (for IC):** sample each edge as present with its probability. The spread is then simple reachability from the seeds in the sampled graph.

**Complexity:** O(m) per simulation.

**Agent use:**
- **Role:** Analyst.
- **How:** Evaluates seed sets from influence maximization (#113), and compares intervention options.
- **Rules:** Report the confidence intervals of estimates (GR4).
- **Guardrails:** Edge probabilities must come from data, and their uncertainty should be acknowledged.

## C5. Graph sampling and estimation

### 148. Graph sampling (node, edge, random walk, Metropolis-Hastings random walk)

**Definition:** Selecting a subset of a graph to estimate properties of the whole, when the full graph is too large or only accessible by crawling.

**How it works:**
1. **Uniform node sampling:** pick vertices at random (needs random access to the ID space).
2. **Uniform edge sampling:** picks endpoints in proportion to degree (biased toward hubs).
3. **Random walk sampling:** walk the graph. Visits are proportional to degree, so correct with 1/degree weights (re-weighted estimators).
4. **Metropolis-Hastings random walk:** accept a move from u to v with probability min(1, deg(u)/deg(v)). The stationary distribution becomes uniform over vertices.
5. Multiple independent walkers and burn-in periods reduce correlation and starting-point bias.

**Complexity:** O(sample size) plus the walk mixing time.

**Agent use:**
- **Role:** Analyst.
- **How:** Estimates graph properties (degree distribution, attribute shares) from APIs or crawls that only allow neighbor queries.
- **Rules:** Always apply the correct bias correction for the sampling method (GR4).
- **Guardrails:** Respect rate limits and terms of use when crawling external graphs.

### 149. Snowball, forest fire and respondent-driven sampling with corrections

**Definition:** Sampling methods that expand from seeds through neighbors, with statistical corrections for their biases.

**How it works:**
1. **Snowball:** start from seeds and include all (or k) neighbors, level by level. Good for local structure, but heavily biased toward well-connected regions.
2. **Forest fire:** from a vertex, "burn" a geometrically distributed number of neighbors, then recurse from them. Keeps realistic properties like shrinking diameter.
3. **Respondent-driven sampling (RDS):** each sampled participant recruits a few others. The Volz-Heckathorn estimator corrects by weighting each sample by 1/degree.
4. **Hansen-Hurwitz style estimators** correct for unequal inclusion probabilities in general.

**Complexity:** O(sample size).

**Agent use:**
- **Role:** Analyst.
- **How:** Exploring hard-to-reach parts of a network, or building representative subgraphs for testing.
- **Rules:** Document the sampling design and the corrections used.
- **Guardrails:** Uncorrected snowball samples overstate connectivity. Never report them as population statistics.

### 150. Graph size and property estimation from samples (collision counting, capture-recapture)

**Definition:** Estimating how many vertices or edges a graph has, or the frequency of a property, when you can't enumerate it.

**How it works:**
1. **Collision counting (birthday paradox):** sample vertices uniformly. The number of repeats among k samples estimates n ≈ k² / (2 × collisions).
2. **Random-walk version:** weight the collisions by the inverse degrees to correct the walk's degree bias (Katzir et al.).
3. **Capture-recapture (Lincoln-Petersen):** two independent samples of sizes n₁ and n₂, with overlap m, give an estimate of N ≈ n₁ × n₂ / m.
4. Confidence intervals come from the sampling distribution or a bootstrap.

**Complexity:** O(√n) samples are often enough for a size estimate (birthday bound).

**Agent use:**
- **Role:** Analyst.
- **How:** Estimates the size of external or partially visible graphs (an ecosystem's package count, the reach of a network), and checks the coverage of the agent's own crawls and indexes.
- **Rules:** Report the estimate with confidence intervals and the method's assumptions (GR4).
- **Guardrails:** The estimators assume independent samples. Correlated samples (short walks) give biased estimates, so check mixing first.

---

Part 4 (#151–200) covers community detection (modularity theory, Leiden-CPM, Girvan-Newman, Infomap, Walktrap, spectral clustering, local clustering, Markov clustering, SBM inference, overlapping communities), partitioning (METIS, KL/FM refinement, streaming and vertex-cut partitioning, hypergraph partitioning), spectral methods (Laplacian eigensolvers, sparsification, Laplacian solvers, effective resistance, random spanning trees, graph signal processing), coloring and independent sets, isomorphism and subgraph matching, and structural decompositions (planarity, treewidth, chordal graphs, nested dissection).