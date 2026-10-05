# Part 4: Communities, partitioning, spectral methods, coloring, isomorphism and decompositions (#151–200)

Same format and the same contract (roles; rules GR1–GR8; guardrails GX1–GX5).

## D1. Community detection

### 151. Modularity and its resolution limit

**Definition:** Modularity scores a partition by how many edges fall inside communities, compared with what's expected by chance. It's the most widely used community quality measure, with known limitations.

**How it works:**
1. Q = (1/2m) × Σ over vertex pairs in the same community of [A_ij − γ × k_i k_j / (2m)].
2. k_i k_j / 2m is the expected number of edges between i and j in a random graph with the same degrees (configuration model, #141).
3. γ is the resolution parameter: higher γ favors more, smaller communities.
4. **Resolution limit:** with γ = 1, modularity can't detect communities smaller than about √(2m) edges. Small real communities get merged.
5. **Degeneracy:** many very different partitions can have nearly the same high modularity.

**Complexity:** O(m) to evaluate a partition. Maximizing it exactly is NP-hard.

**Agent use:**
- **Role:** Analyst.
- **How:** Scores and compares partitions, and serves as the objective for Louvain and Leiden (K#81–82).
- **Rules:** Sweep γ and report how stable the communities are across values.
- **Guardrails:** Never treat one high-modularity partition as "the" structure. Check stability across runs and resolutions.

### 152. Leiden with the constant Potts model (CPM)

**Definition:** Leiden community detection (K#82) with the CPM objective, which avoids modularity's resolution limit.

**How it works:**
1. CPM quality = Σ over communities of [edges inside − γ × (number of vertex pairs inside)].
2. γ acts as a density threshold. Communities are groups denser than γ inside and sparser than γ between groups.
3. Unlike modularity, this doesn't depend on the total graph size, so there's no resolution limit.
4. Optimize with Leiden's moves, refinement and aggregation.
5. Choose γ by scanning, often using the "resolution profile": the stable plateaus where partitions don't change.

**Complexity:** About O(m) per iteration.

**Agent use:**
- **Role:** Analyst.
- **How:** Reliable communities at a chosen density level, useful for GraphRAG hierarchies (K#155), where each level needs a consistent meaning.
- **Rules:** Record γ, the seed and the graph version (GR1, GR5).
- **Guardrails:** Results vary between runs. Report agreement across seeds (#168).

### 153. Girvan-Newman (edge betweenness removal)

**Definition:** Finding communities by repeatedly removing the edge with the highest betweenness, which tends to be a bridge between communities.

**How it works:**
1. Compute edge betweenness for all edges (#109).
2. Remove the edge with the highest score.
3. Recompute the betweenness of the affected edges.
4. Repeat. Components that separate are the communities.
5. Recording the order of splits gives a hierarchy (dendrogram). Cut it where modularity is highest.

**Complexity:** O(m² × n) overall. Only feasible for small graphs.

**Agent use:**
- **Role:** Analyst.
- **How:** Gives an interpretable hierarchical split of small graphs (up to a few thousand vertices) and shows exactly which links separate groups.
- **Rules:** Use only on small graphs (GR3).
- **Guardrails:** Use Leiden or Infomap on large graphs.

### 154. Overlapping label propagation (SLPA)

**Definition:** A label propagation variant where vertices remember the labels they've received, allowing each vertex to belong to several communities.

**How it works:**
1. Each vertex has a memory of labels, starting with its own ID.
2. **Each round:** a "listener" vertex receives one label from each neighbor (each neighbor "speaks" a label chosen in proportion to its memory frequencies). The listener adds the most frequent received label to its memory.
3. After T rounds, labels appearing in a vertex's memory above a threshold r are its communities.
4. Low r gives more overlap; high r gives less.

**Complexity:** O(T × m).

**Agent use:**
- **Role:** Analyst.
- **How:** Fast overlapping communities, where people belong to several groups and topics span several areas.
- **Rules:** Fix seeds (GR5), and sweep r.
- **Guardrails:** Results vary between runs. Combine several runs for stability.

### 155. Infomap (the map equation)

**Definition:** Community detection that finds the partition giving the shortest description of a random walk on the graph. Communities are regions where the walker stays for a long time.

**How it works:**
1. Compute random-walk flow: PageRank-like visit rates and edge flows.
2. The **map equation** gives the average code length for describing the walk with a two-level code: module names when the walker enters a module, and vertex names within modules.
3. Good partitions (where the walker rarely leaves modules) give short descriptions.
4. Minimize it with Louvain-like local moves, aggregation and refinement.
5. Hierarchical and overlapping versions exist, plus "memory" networks for higher-order flow.

**Complexity:** About O(m) per pass.

**Agent use:**
- **Role:** Analyst.
- **How:** Communities based on flow rather than density, which works well for directed and weighted graphs: citation flow, transaction flow, traffic.
- **Rules:** Use it on directed and weighted graphs where flow matters.
- **Guardrails:** Compare against Leiden on the same graph. Large disagreements show the structure is ambiguous.

### 156. Walktrap

**Definition:** Hierarchical community detection using distances based on short random walks.

**How it works:**
1. For each vertex, compute the probability distribution after a t-step random walk (t ≈ 3–5).
2. Distance between vertices (and between communities) = a degree-weighted distance between their walk distributions.
3. Agglomerative clustering: start with single vertices, and repeatedly merge the two adjacent communities whose merge least increases the within-community distance (Ward's method).
4. Cut the dendrogram where modularity is highest.

**Complexity:** O(m × n²) worst case, about O(n² log n) on sparse graphs.

**Agent use:**
- **Role:** Analyst.
- **How:** A good, interpretable hierarchy for small and medium graphs.
- **Rules:** Use moderate t values. Report t.
- **Guardrails:** Memory grows with n². Check GR3.

### 157. Fast greedy modularity (Clauset-Newman-Moore)

**Definition:** Agglomerative community detection that repeatedly merges the pair of communities giving the largest modularity increase.

**How it works:**
1. Start with every vertex as its own community.
2. Keep, for each pair of adjacent communities, the modularity gain ΔQ of merging them, in max-heaps.
3. Merge the pair with the largest ΔQ, and update the gains of the affected communities.
4. Continue until a single community remains. Keep the partition with the highest Q.

**Complexity:** O(m × d × log n), where d is the dendrogram depth. Near-linear on many sparse graphs.

**Agent use:**
- **Role:** Analyst.
- **How:** A deterministic baseline and hierarchy, with no randomness.
- **Rules:** Prefer Leiden for quality. Use this when determinism is required.
- **Guardrails:** Tends to create unbalanced, very large communities. Check the size distribution.

### 158. Spectral clustering (normalized Laplacian + k-means)

**Definition:** Clustering vertices with the eigenvectors of the graph Laplacian, which turns graph structure into a geometry where clusters separate easily.

**How it works:**
1. Build the normalized Laplacian L_sym = I − D^(−1/2) A D^(−1/2) (or the random-walk version).
2. Compute its k smallest eigenvectors (#176).
3. Each vertex becomes a point in k dimensions (its entries in those eigenvectors). Normalize the rows (Ng-Jordan-Weiss).
4. Run k-means on those points.
5. The eigenvalue gap (eigengap) suggests a good k.

**Complexity:** Dominated by the eigensolver: about O(k × m × iterations) with sparse iterative methods.

**Agent use:**
- **Role:** Analyst.
- **How:** Strong clustering when clusters are well separated, and for similarity graphs built from data (k-nearest-neighbor graphs, #284).
- **Rules:** Use the normalized Laplacian on graphs with uneven degrees.
- **Guardrails:** Requires k in advance. Check the eigengap, and test stability across k values.

### 159. Spectral bisection (Fiedler vector)

**Definition:** Splitting a graph in two using the eigenvector of the second-smallest Laplacian eigenvalue.

**How it works:**
1. Compute the Fiedler vector: the eigenvector of the second-smallest eigenvalue λ₂ of the Laplacian.
2. Sort the vertices by their Fiedler values.
3. Split at the median (for balanced halves), at zero, or at the best "sweep cut" (#160).
4. λ₂ itself (the algebraic connectivity) measures how well connected the graph is. λ₂ = 0 means it's disconnected.
5. Recursive bisection gives more parts.

**Complexity:** One eigenvector computation (Lanczos, #176).

**Agent use:**
- **Role:** Analyst.
- **How:** Finds natural two-way splits, measures connectivity (λ₂), and gives an initial partition for refinement (#171).
- **Rules:** Use a sweep cut rather than a fixed threshold.
- **Guardrails:** None specific.

### 160. Conductance, sweep cuts and the Cheeger inequality

**Definition:** Conductance measures how cleanly a vertex set is separated from the rest (cut edges relative to the set's total degree). The Cheeger inequality links it to the Laplacian spectrum.

**How it works:**
1. Conductance φ(S) = cut(S, rest) / min(vol(S), vol(rest)), where vol is the sum of degrees.
2. **Sweep cut:** order the vertices by a vector (Fiedler vector, PPR scores), and evaluate the conductance of each prefix. Choose the lowest.
3. **Cheeger inequality:** λ₂/2 ≤ φ(G) ≤ √(2λ₂). That guarantees spectral methods find cuts close to the best possible conductance.

**Complexity:** O(m) for a sweep, using a sorted order and incremental updates.

**Agent use:**
- **Role:** Analyst and Verifier.
- **How:** A quality score for any cluster: low conductance means it's well separated. Also the step that turns score vectors into clusters.
- **Rules:** Report each cluster's conductance with it.
- **Guardrails:** Very small sets can have deceptively low conductance. Set a minimum size.

### 161. Local graph clustering (PageRank-Nibble with sweep cut)

**Definition:** Finding a good cluster around a seed vertex while touching only a small part of the graph.

**How it works:**
1. Compute approximate personalized PageRank from the seed with pushes (#103).
2. Divide each score by the vertex's degree.
3. Sort the vertices touched by the push by that normalized score.
4. Sweep cut (#160): choose the prefix with the lowest conductance.
5. Guarantees: if a low-conductance cluster contains the seed, this finds a cluster with provably low conductance, with work independent of the graph's size.

**Complexity:** Proportional to the cluster size and 1/ε, not to the graph size.

**Agent use:**
- **Role:** Analyst and Retriever.
- **How:** "Find the community around this entity", on demand, on huge graphs. Useful for retrieval context, investigations, and expanding from a known suspicious account.
- **Rules:** Report the cluster's conductance and size.
- **Guardrails:** Seeds on hubs give noisy clusters. Use several seeds, or skip hubs (GX2).

### 162. Markov clustering (MCL)

**Definition:** Clustering by simulating random-walk flow, alternately spreading it out (expansion) and strengthening strong flows (inflation), until flow settles into clusters.

**How it works:**
1. Start with the column-stochastic transition matrix, with self-loops added.
2. **Expansion:** square the matrix (flow spreads through 2-step paths).
3. **Inflation:** raise each entry to a power r > 1, then re-normalize the columns. Strong flows get stronger, weak ones fade.
4. Prune tiny entries to keep the matrix sparse.
5. Repeat until it converges. Vertices whose flow ends at the same "attractor" form a cluster.
6. A higher inflation r gives smaller, tighter clusters.

**Complexity:** Sparse matrix products with pruning. Practical on large sparse graphs.

**Agent use:**
- **Role:** Analyst.
- **How:** Robust clustering of similarity graphs (protein families, duplicate groups, related documents), with the number of clusters emerging automatically.
- **Rules:** Tune r on known examples. Record the pruning thresholds.
- **Guardrails:** Pruning too aggressively changes the results. Validate against samples.

### 163. Stochastic block model inference (degree-corrected, Bayesian/MDL)

**Definition:** Fitting a statistical model where vertices belong to groups and edge probabilities depend only on group membership. That finds communities and other structures (core-periphery, bipartite) in a principled way.

**How it works:**
1. Model: each vertex has a group. Edge counts between groups follow group-pair rates. The degree-corrected version also accounts for each vertex's degree.
2. Inference: find the group assignment maximizing the posterior probability, or minimizing the description length (MDL) of the graph plus the model.
3. MDL automatically picks the number of groups, avoiding overfitting.
4. Optimization: MCMC with merge-split moves, often in nested (hierarchical) form (Peixoto's methods, graph-tool).
5. The output can be assortative (communities), disassortative or core-periphery, whatever fits the data best.

**Complexity:** About O(m log² n) for efficient MCMC versions.

**Agent use:**
- **Role:** Analyst.
- **How:** When you need statistically justified structure, including the number of groups and the uncertainty of each vertex's assignment, rather than a heuristic optimum.
- **Rules:** Report the description length and the posterior uncertainty (GR4).
- **Guardrails:** Group labels are statistical. Don't treat them as identities, especially about people (GX3).

### 164. Overlapping communities with BigCLAM

**Definition:** A model-based method where each vertex has a non-negative affiliation strength with each community, and overlaps naturally increase the chance of edges.

**How it works:**
1. Each vertex u has a vector F_u ≥ 0 of community affiliation strengths.
2. P(edge between u and v) = 1 − exp(−F_u · F_v). Shared communities make edges likely.
3. Fit F by maximizing the likelihood of the observed edges and non-edges, with gradient methods. Non-edges are handled efficiently through sums.
4. A vertex belongs to community c if F_uc exceeds a threshold.
5. Choose the number of communities by held-out likelihood.

**Complexity:** About O(m) per iteration (linear in edges).

**Agent use:**
- **Role:** Analyst.
- **How:** Large-scale overlapping communities, where overlaps are dense (people in several teams and interest groups).
- **Rules:** Validate the number of communities on held-out edges.
- **Guardrails:** Thresholds strongly affect membership. Report them.

### 165. Clique percolation

**Definition:** Communities defined as unions of adjacent k-cliques (two k-cliques are adjacent if they share k−1 vertices). That allows overlap naturally.

**How it works:**
1. Find all k-cliques (#124), or maximal cliques (#125) of size ≥ k.
2. Build a clique graph: link two cliques if they share at least k−1 vertices.
3. Each connected component of the clique graph is a community.
4. A vertex in cliques of several components belongs to several communities.

**Complexity:** Dominated by clique enumeration. Feasible on sparse graphs.

**Agent use:**
- **Role:** Analyst.
- **How:** Strict, tight overlapping communities: groups where everyone is densely interconnected.
- **Rules:** Typically k = 3 or 4. Report k.
- **Guardrails:** Sparse regions get no community at all. Report the share of vertices left uncovered.

### 166. Hierarchical agglomerative clustering on graphs

**Definition:** Building a tree of nested clusters by repeatedly merging the most similar clusters, using graph similarities or distances.

**How it works:**
1. Start with each vertex as a cluster.
2. Define the similarity between clusters with a linkage: single (the closest pair, equivalent to MST-based clustering, #61), complete (the farthest pair), average, or Ward.
3. Merge the two most similar clusters, and update the similarities (Lance-Williams formulas).
4. Repeat to build the dendrogram.
5. Cut it at a level, or by a quality criterion.

**Complexity:** O(n² log n) generally. Single linkage is O(m log m) through an MST.

**Agent use:**
- **Role:** Analyst.
- **How:** Multi-level grouping where the hierarchy itself matters: taxonomies, nested service groups, topic trees.
- **Rules:** Choose the linkage deliberately (single linkage creates long chains; average or Ward give compact clusters).
- **Guardrails:** Memory for full similarity matrices. Use graph-based or approximate variants on large data.

### 167. Correlation clustering (pivot / KwikCluster)

**Definition:** Clustering items from "same / different" pairwise judgments, minimizing disagreements, without choosing the number of clusters.

**How it works:**
1. Input: edges labeled "+" (should be together) or "−" (should be apart), possibly weighted.
2. **Pivot algorithm:** pick a random unclustered vertex as the pivot. Make a cluster of the pivot plus all its unclustered "+" neighbors. Remove them, and repeat.
3. It's a 3-approximation in expectation for complete graphs.
4. Improvements: repeat with several random orders and keep the best, then refine with local moves.

**Complexity:** O(m) per run.

**Agent use:**
- **Role:** Curator and Analyst.
- **How:** Turns pairwise match decisions into consistent entity clusters (K#38), avoiding chain merges.
- **Rules:** Use the weighted version with calibrated match scores.
- **Guardrails:** Large resulting clusters get reviewed before merging (K#174).

### 168. Community evaluation (NMI, ARI, conductance, stability)

**Definition:** Measuring how good a community partition is, against ground truth or by internal quality, and how stable it is.

**How it works:**
1. **With ground truth:** normalized mutual information (NMI), adjusted Rand index (ARI, corrected for chance), and the F1 score of best-matching communities. Overlapping versions exist.
2. **Without ground truth:** modularity, conductance (#160), coverage, cluster density.
3. **Stability:** run with different seeds or on perturbed graphs (removing a few edges), and measure agreement with NMI or ARI. Stable communities are trustworthy.
4. Check the size distribution: one giant community plus many tiny ones signals a problem.

**Complexity:** O(n) to O(n log n) per comparison.

**Agent use:**
- **Role:** Verifier.
- **How:** No community result is used without quality and stability numbers.
- **Rules:** Report stability across at least several seeds.
- **Guardrails:** Unstable communities shouldn't drive decisions or GraphRAG summaries (K#155).

### 169. Dynamic community tracking

**Definition:** Following communities across graph snapshots over time, and detecting events: birth, death, growth, shrinkage, merge, split.

**How it works:**
1. Detect communities in each snapshot (independently, or warm-started from the previous partition, which gives more stable results).
2. Match communities between consecutive snapshots by overlap (Jaccard similarity of member sets).
3. Classify the changes: one-to-one with a size change (growth or shrinkage), one-to-many (split), many-to-one (merge), no match (birth or death).
4. Keep stable community IDs across matches.

**Complexity:** Detection per snapshot, plus overlap matching (efficient with hashing).

**Agent use:**
- **Role:** Analyst.
- **How:** Monitors how groups evolve: teams reorganizing, topic clusters merging, fraud rings splitting to evade detection. It also decides when GraphRAG summaries need refreshing (K#176).
- **Rules:** Use warm starts so small graph changes don't cause big partition changes.
- **Guardrails:** Distinguish real change from algorithm noise. Compare against stability baselines (#168).

## D2. Partitioning

### 170. METIS multilevel partitioning

**Definition:** The standard method for splitting a graph into k balanced parts with few edges between them: coarsen, partition the small graph, then refine while expanding.

**How it works:**
1. **Coarsening:** repeatedly contract a matching (#175), especially heavy edges, to get smaller graphs, down to a few hundred vertices.
2. **Initial partitioning:** split the smallest graph with a good but slow method (recursive bisection, spectral, greedy growing).
3. **Uncoarsening:** project the partition back level by level, refining at each level with KL/FM moves (#171) to reduce the cut while keeping balance.
4. Works for k-way partitioning directly or by recursive bisection.
5. Constraints: balance tolerance, vertex weights, several balance constraints at once.

**Complexity:** Near-linear: O(m) per level, with a logarithmic number of levels.

**Agent use:**
- **Role:** Optimizer and Builder.
- **How:** Sharding graph data across machines (fewer cross-machine hops), splitting work for parallel jobs, and the cells used in route planning (#37).
- **Rules:** Report the cut size and the balance. Record the seed and parameters (GR5).
- **Guardrails:** Moving data based on a new partition is an operational change (GX4). Plan it (K#182).

### 171. Kernighan-Lin and Fiduccia-Mattheyses refinement

**Definition:** Local improvement for graph partitions: move or swap vertices between parts to reduce the cut while keeping balance.

**How it works:**
1. For each boundary vertex, compute its gain: how much the cut shrinks if it moves to the other part.
2. **FM:** repeatedly move the vertex with the highest gain (even if negative), while balance allows, and lock it so it doesn't move again in this pass.
3. Track the best partition seen during the pass, and roll back to it at the end. Allowing temporarily worse moves helps escape local minima.
4. Gain buckets give O(1) access to the best move.
5. **KL:** the original version, which swaps pairs of vertices.

**Complexity:** FM passes are O(m) with bucket structures.

**Agent use:**
- **Role:** Optimizer.
- **How:** Improves any partition (from METIS, streaming partitioning or manual assignment) with small, controlled changes. That's good for incremental rebalancing with minimal data movement.
- **Rules:** Limit the number of moved vertices when movement has a cost.
- **Guardrails:** None specific.

### 172. Streaming partitioning (LDG, FENNEL)

**Definition:** Assigning vertices to partitions in one pass as they arrive, using only already-placed neighbors and partition sizes.

**How it works:**
1. Vertices arrive one at a time with their edge lists.
2. **LDG (linear deterministic greedy):** place the vertex in the partition holding the most of its already-placed neighbors, weighted by (1 − partition size / capacity).
3. **FENNEL:** maximize (neighbors in the partition) − α × (size penalty), with a modularity-inspired objective.
4. Decisions are made immediately, never revisited (or revisited with restreaming: several passes improve the result).

**Complexity:** O(m) in one pass, with low memory.

**Agent use:**
- **Role:** Builder.
- **How:** Partitioning graphs too large to load completely, or placing new vertices into existing shards on arrival.
- **Rules:** Use restreaming passes for better quality if time allows.
- **Guardrails:** Arrival order affects quality a lot. BFS-like orders work better than random orders.

### 173. Vertex-cut partitioning (PowerGraph greedy, HDRF)

**Definition:** Partitioning edges instead of vertices, so high-degree vertices are split (replicated) across machines. That's better for skewed graphs.

**How it works:**
1. Each edge is assigned to one partition. A vertex appears (as replicas) in every partition holding one of its edges.
2. **Goal:** balanced edge counts with a low replication factor (average replicas per vertex).
3. **PowerGraph greedy:** place each edge where its endpoints already have replicas, preferring less loaded partitions.
4. **HDRF (high-degree replicated first):** when choosing, prefer replicating the higher-degree endpoint, since hubs are going to be replicated anyway.
5. One replica of each vertex is the master; others are mirrors, synchronized after computation (#247).

**Complexity:** O(m) streaming.

**Agent use:**
- **Role:** Builder.
- **How:** Distributed analytics on power-law graphs (social, web, transactions), where vertex-based partitioning puts hubs' edges all on one machine.
- **Rules:** Report the replication factor and edge balance.
- **Guardrails:** Replicas must be synchronized correctly. Verify results against a single-machine run on samples (GX5).

### 174. Hypergraph partitioning (hMETIS, KaHyPar, PaToH)

**Definition:** Partitioning a hypergraph so that hyperedges are split across as few parts as possible. It models communication cost more accurately than graph partitioning.

**How it works:**
1. Hyperedges represent sets that should stay together (a net in a circuit, a matrix column, a transaction with several parties).
2. **Objectives:** cut-net (count the hyperedges spanning more than one part), or connectivity − 1 (for each hyperedge, the number of parts it spans, minus 1). The second matches communication volume exactly.
3. Multilevel approach as in METIS, with hypergraph-specific coarsening and FM refinement.
4. KaHyPar uses n-level coarsening (one vertex at a time) for high quality.

**Complexity:** Near-linear in the number of pins (vertex–hyperedge memberships), heavier than graph partitioning.

**Agent use:**
- **Role:** Optimizer.
- **How:** Sharding when operations touch groups of items: placing data used together by queries, distributing sparse matrix computations, circuit layout.
- **Rules:** Use connectivity − 1 when communication volume is the cost.
- **Guardrails:** None specific.

### 175. Graph coarsening by heavy-edge matching

**Definition:** Shrinking a graph by merging pairs of vertices connected by heavy edges, keeping its structure. The coarsening step of multilevel algorithms.

**How it works:**
1. Visit the vertices in random order (or by degree).
2. Match each unmatched vertex with its unmatched neighbor connected by the heaviest edge.
3. Merge matched pairs into super-vertices: vertex weights add up, edges between the same super-vertices combine with summed weights.
4. Repeat to build levels, until the graph is small.
5. Keep the mapping from each fine vertex to its coarse vertex, for uncoarsening.

**Complexity:** O(m) per level.

**Agent use:**
- **Role:** Builder.
- **How:** The first phase of multilevel partitioning (#170) and multilevel layout (#315), and a quick way to build a summary graph (#236).
- **Rules:** Keep the mappings with each level (GR1).
- **Guardrails:** None specific.

## D3. Spectral methods and graph signal processing

### 176. Graph Laplacian eigensolvers (Lanczos, LOBPCG)

**Definition:** Computing a few eigenvalues and eigenvectors of large sparse graph matrices, using iterative methods based only on matrix-vector products.

**How it works:**
1. **Laplacians:** L = D − A (combinatorial), L_sym = I − D^(−1/2) A D^(−1/2) (normalized), L_rw = I − D⁻¹A (random walk).
2. **Lanczos:** builds an orthonormal basis of the Krylov space {v, Lv, L²v, …}, giving a small tridiagonal matrix whose eigenvalues approximate L's extreme eigenvalues. Restarted versions (ARPACK) and reorthogonalization keep it stable.
3. **LOBPCG:** a block method that iterates on several vectors at once, and uses preconditioners. Good for the smallest eigenvalues.
4. **Shift-and-invert:** targets interior eigenvalues using linear solves.
5. Each iteration costs one sparse matrix-vector product, O(m).

**Complexity:** O(m × iterations × k) for k eigenpairs.

**Agent use:**
- **Role:** Analyst.
- **How:** The engine behind spectral clustering (#158), bisection (#159), embeddings (#182, #251) and connectivity measures (λ₂).
- **Rules:** Check the residuals (‖Lx − λx‖) of the results (GR6).
- **Guardrails:** Disconnected graphs have repeated zero eigenvalues. Handle components separately.

### 177. Spectral sparsification (effective resistance sampling)

**Definition:** Replacing a dense graph with a much sparser one that has nearly the same Laplacian, so it behaves almost identically for cuts, flows and spectral algorithms.

**How it works:**
1. Compute each edge's effective resistance R_e (#179), approximately with fast solvers and random projections.
2. Sample each edge with probability proportional to w_e × R_e. Edges that are the only connection between regions (high resistance) are almost always kept.
3. Reweight the kept edges by 1/(sampling probability).
4. With O(n log n / ε²) edges, every cut and every quadratic form is within a factor of (1 ± ε) (Spielman-Srivastava).

**Complexity:** Near-linear time with fast Laplacian solvers.

**Agent use:**
- **Role:** Builder.
- **How:** Shrinks dense graphs (similarity graphs, dense interaction graphs) before running expensive algorithms, with guaranteed accuracy.
- **Rules:** Report ε (GR4).
- **Guardrails:** Results on sparsified graphs are approximate. Never use them for exact claims.

### 178. Laplacian solvers (conjugate gradient, preconditioning, algebraic multigrid)

**Definition:** Solving linear systems Lx = b with graph Laplacians, a core operation behind many graph algorithms (electrical flows, effective resistance, diffusion, semi-supervised learning).

**How it works:**
1. **Conjugate gradient (CG):** an iterative method for symmetric positive (semi-)definite systems. Its convergence depends on the condition number.
2. **Preconditioning:** solve an easier approximate system each iteration to speed convergence. Options: diagonal (Jacobi), incomplete Cholesky, spanning-tree preconditioners.
3. **Algebraic multigrid (AMG):** builds coarser versions of the graph (#175-like aggregation), corrects errors at multiple scales. Often nearly linear in practice.
4. Theoretical nearly-linear-time solvers exist (Spielman-Teng and successors). In practice, AMG and preconditioned CG are used.
5. Laplacians are singular: ensure b sums to zero (per component), or pin one vertex.

**Complexity:** Near-linear per solve with good preconditioners.

**Agent use:**
- **Role:** Analyst.
- **How:** Powers current-flow centrality (#112), effective resistance (#179), label propagation by harmonic functions (#286) and graph signal smoothing.
- **Rules:** Check the residual ‖Lx − b‖ after solving (GR6).
- **Guardrails:** Handle disconnected components and the null space explicitly.

### 179. Effective resistance and commute time

**Definition:** Treating edges as resistors, the effective resistance between two vertices measures how well connected they are through all paths. Commute time is the expected random-walk round-trip time, proportional to it.

**How it works:**
1. R(u, v) = (e_u − e_v)ᵀ L⁺ (e_u − e_v), where L⁺ is the Laplacian's pseudoinverse.
2. Compute it for one pair with a Laplacian solve (#178). For all edges, use the Spielman-Srivastava method: random projections plus O(log n) solves.
3. Many parallel paths give low resistance; a single path gives high resistance.
4. **Commute time** = 2m × R(u, v).
5. An edge's resistance R_e equals the probability that the edge appears in a uniform random spanning tree (#180).

**Complexity:** Near-linear for all edges, approximately.

**Agent use:**
- **Role:** Analyst.
- **How:** A robust proximity measure (more resilient to a single path than shortest-path distance), identification of critical edges (high R_e), and the basis of sparsification (#177).
- **Rules:** Use approximations on large graphs, with stated error.
- **Guardrails:** Commute times are dominated by degree in very large graphs (they become uninformative). Use normalized or local variants.

### 180. Uniform random spanning trees (Wilson's algorithm)

**Definition:** Sampling a spanning tree uniformly at random from all spanning trees of a graph.

**How it works:**
1. Start the tree with one root vertex.
2. Pick any vertex not in the tree. Run a random walk from it until it hits the tree.
3. Erase the loops from the walk (loop-erased random walk), and add the resulting path to the tree.
4. Repeat until every vertex is in the tree.
5. The result is exactly uniform over all spanning trees.

**Complexity:** Expected time = the mean hitting time, efficient on most graphs.

**Agent use:**
- **Role:** Analyst.
- **How:** Estimates edge importance by sampling (the fraction of sampled trees containing an edge estimates its effective resistance), generates random network backbones, and provides tests.
- **Rules:** Fix seeds (GR5).
- **Guardrails:** None specific.

### 181. Graph signal processing (graph Fourier transform, Chebyshev filters)

**Definition:** Treating values on vertices as signals and filtering them by graph frequency (smooth versus rapidly varying across edges), using the Laplacian's eigenvectors.

**How it works:**
1. **Graph Fourier transform:** project the signal onto the Laplacian eigenvectors. Low eigenvalues correspond to smooth patterns, high ones to sharp variation.
2. **Filtering:** multiply each frequency component by a response h(λ). Low-pass filters smooth; high-pass filters detect anomalies.
3. **Chebyshev polynomial approximation:** approximate h(L) with a k-term polynomial, so filtering costs k sparse matrix-vector products, with no eigendecomposition.
4. Spectral GNNs (such as ChebNet) and simplified GCNs are built on this.

**Complexity:** O(k × m) per filtered signal.

**Agent use:**
- **Role:** Analyst.
- **How:** Smooths noisy per-vertex metrics using structure (sensor networks, service metrics on a dependency graph), and highlights vertices whose values differ sharply from their neighbors' (anomalies).
- **Rules:** Use the normalized Laplacian for degree-uneven graphs.
- **Guardrails:** Smoothing hides real local anomalies. Keep the raw signals alongside.

### 182. Laplacian eigenmaps and diffusion maps

**Definition:** Embedding vertices into low-dimensional space with Laplacian or diffusion eigenvectors, so that nearby vertices in the graph are nearby in the embedding.

**How it works:**
1. **Laplacian eigenmaps:** use the eigenvectors of the smallest nonzero eigenvalues of the normalized Laplacian as coordinates. Minimizes Σ w_ij ‖y_i − y_j‖², with constraints.
2. **Diffusion maps:** use eigenvectors of the random-walk matrix, scaled by eigenvalue^t. Euclidean distance in the embedding approximates the "diffusion distance" after t steps.
3. The dimension is chosen by the eigenvalue decay.
4. New points can be added approximately (Nyström extension).

**Complexity:** Dominated by the eigensolver (#176).

**Agent use:**
- **Role:** Analyst.
- **How:** Visualization and features for downstream ML, especially on k-nearest-neighbor graphs built from data (#284).
- **Rules:** Report the dimension choice and the parameter t.
- **Guardrails:** Embeddings of disconnected graphs need per-component handling.

## D4. Coloring, independent sets and covers

### 183. Greedy coloring and DSatur

**Definition:** Assigning colors to vertices so that adjacent vertices differ, using few colors. Optimal coloring is NP-hard; greedy methods are standard.

**How it works:**
1. **Greedy:** visit the vertices in some order, and give each the smallest color not used by its colored neighbors. Uses at most (max degree + 1) colors.
2. **Order matters:** largest-first, or smallest-last (degeneracy order, which gives at most degeneracy + 1 colors).
3. **DSatur:** always color next the vertex with the most distinct colors among its neighbors (saturation degree), breaking ties by degree. Usually uses fewer colors.
4. **Local search improvement:** tabu search (TabuCol) to reduce the color count further.

**Complexity:** Greedy O(n + m). DSatur O((n + m) log n).

**Agent use:**
- **Role:** Optimizer.
- **How:** Scheduling conflicting tasks (colors = time slots), assigning resources that can't be shared by neighbors (frequencies, exam slots), and register allocation (#301).
- **Rules:** Report the number of colors and a lower bound (the size of a clique found), so the gap is visible (GR4).
- **Guardrails:** Verify the coloring is proper (no edge with equal colors) (GR6).

### 184. Parallel coloring (Jones-Plassmann)

**Definition:** Coloring vertices in parallel, by coloring in rounds the vertices that are local maxima of random priorities.

**How it works:**
1. Give each vertex a random priority.
2. Each round, every uncolored vertex with a higher priority than all its uncolored neighbors colors itself with the smallest color not used by colored neighbors.
3. Those vertices form an independent set, so no conflicts arise.
4. Repeat until all are colored.
5. Speculative variants: color everything in parallel, detect conflicts, then recolor the conflicting vertices.

**Complexity:** O(log n / log log n) rounds expected on bounded-degree graphs.

**Agent use:**
- **Role:** Optimizer.
- **How:** Coloring large graphs fast, often to schedule parallel updates without conflicts (vertices with the same color can be updated at once).
- **Rules:** Fix seeds (GR5).
- **Guardrails:** Verify properness after parallel runs (GR6).

### 185. Maximal independent set (Luby's algorithm)

**Definition:** Finding a set of vertices with no two adjacent, that can't be extended. Done in parallel with randomized rounds.

**How it works:**
1. Each round, every remaining vertex picks a random number.
2. A vertex joins the set if its number is lower than all its remaining neighbors' numbers.
3. Remove the new set members and their neighbors.
4. Repeat until no vertices remain.
5. Each round removes a constant fraction of edges in expectation.

**Complexity:** O(log n) rounds expected. O(m) total work.

**Agent use:**
- **Role:** Optimizer.
- **How:** Choosing non-conflicting items to process together (independent tasks, non-overlapping edits, cluster centers), and a building block of parallel coloring and coarsening.
- **Rules:** Maximal isn't maximum. Use exact or heuristic maximum methods when size matters.
- **Guardrails:** None specific.

### 186. Vertex cover approximation (matching-based, LP rounding, kernelization)

**Definition:** Finding a small set of vertices touching every edge. NP-hard in general graphs, but with good approximations and exact methods for small covers.

**How it works:**
1. **2-approximation:** find a maximal matching, and take both endpoints of every matched edge.
2. **LP rounding:** solve the LP relaxation and take every vertex with value ≥ 0.5. Also a 2-approximation, and it gives a lower bound.
3. **Kernelization (for exact solutions):** reduction rules shrink the problem. A vertex with degree > k must be in any cover of size k; degree-1 vertices can be handled by taking their neighbor; LP-based crown reductions.
4. Then exact branch-and-bound on the small kernel.

**Complexity:** O(m) for the approximation. Exact: fixed-parameter tractable, about O(1.27^k + k × n).

**Agent use:**
- **Role:** Optimizer.
- **How:** Placing monitors on the fewest vertices so that every link is observed, and choosing the fewest services to instrument so every interaction is captured.
- **Rules:** Report the lower bound with the solution (GR4).
- **Guardrails:** None specific.

### 187. Dominating set (greedy approximation)

**Definition:** Choosing a small set of vertices such that every vertex is in the set or adjacent to it.

**How it works:**
1. Greedy: repeatedly pick the vertex that covers the most not-yet-covered vertices (itself and its neighbors).
2. That gives a ln(Δ + 1)-approximation, which is essentially the best possible unless P = NP.
3. Variants: connected dominating sets (the chosen vertices must form a connected subgraph, for routing backbones), and k-domination.
4. Exact methods use integer programming for moderate sizes.

**Complexity:** O(m log n) with priority structures.

**Agent use:**
- **Role:** Optimizer.
- **How:** Placing caches, sensors, relays or support staff so everyone is within one hop of one.
- **Rules:** Report the approximation bound (GR4).
- **Guardrails:** None specific.

### 188. Feedback arc set and feedback vertex set (Eades-Lin-Smyth and others)

**Definition:** Finding the smallest set of edges (or vertices) whose removal makes a directed graph acyclic.

**How it works:**
1. Exact versions are NP-hard. Heuristics are used in practice.
2. **Eades-Lin-Smyth:** repeatedly remove sinks (append to the end of an order) and sources (prepend to the start). When neither exists, pick the vertex maximizing (out-degree − in-degree) and place it next at the start.
3. In the resulting vertex order, backward edges form the feedback arc set.
4. Work per strongly connected component (#57), since only edges inside SCCs can be in cycles.
5. Improve with local search (swapping positions in the order).

**Complexity:** O(m) for Eades-Lin-Smyth.

**Agent use:**
- **Role:** Optimizer.
- **How:** Breaking dependency cycles with the fewest changes (packages, modules, build steps), and ordering items consistently from inconsistent pairwise preferences (ranking aggregation).
- **Rules:** Present the arcs to remove as candidates for review.
- **Guardrails:** Removing dependencies is a code or system change (GR8). It needs review.

## D5. Isomorphism, matching and pattern mining

### 189. Canonical labeling and graph isomorphism (nauty, Traces, bliss)

**Definition:** Computing a canonical form for a graph, so that two graphs are isomorphic exactly when their canonical forms are identical.

**How it works:**
1. **Color refinement:** start with vertex colors (labels or degrees). Repeatedly split colors by the multiset of neighbor colors (1-WL, K#140) until stable.
2. If vertices still share colors, **individualize** one: give it a unique color and refine again. Branch over the choices, forming a search tree.
3. Each leaf gives a discrete coloring, which is a vertex ordering. The canonical form is the best leaf under a fixed comparison.
4. **Pruning with automorphisms:** symmetries found during the search let equivalent branches be skipped (#191).
5. Exponential in the worst case, but extremely fast in practice.

**Complexity:** Quasi-polynomial in theory (Babai). Usually fast in practice.

**Agent use:**
- **Role:** Analyst.
- **How:** Exact deduplication of graph structures (identical workflows, identical subgraph patterns, duplicate molecules), and keys for caching graph-shaped results (G59-style canonical hashing for graphs).
- **Rules:** Include vertex and edge labels in the initial coloring when they matter.
- **Guardrails:** Set a time limit for adversarial or highly symmetric inputs.

### 190. Advanced subgraph isomorphism (VF3, Glasgow subgraph solver, Ullmann)

**Definition:** Finding all occurrences of a pattern graph inside a larger target graph, with strong pruning methods.

**How it works:**
1. **Ullmann:** keep a candidate matrix (which target vertices each pattern vertex could map to) and refine it by neighborhood consistency.
2. **VF2/VF3 (K#55):** extend a partial mapping one vertex at a time, with feasibility rules on the neighborhoods. VF3 adds a better pattern vertex ordering and classification of vertices.
3. **Glasgow subgraph solver (constraint programming):** domains for each pattern vertex, all-different constraints, and filtering with degree sequences, neighborhood degree sequences and supplemental graphs (paths of length 2), plus restarts.
4. Induced versus non-induced matching (whether pattern non-edges must also be non-edges in the target).

**Complexity:** NP-complete. These solvers handle practical sizes with strong pruning.

**Agent use:**
- **Role:** Analyst.
- **How:** Finding exact structural patterns: known attack patterns in a provenance graph, specific transaction shapes, code structures in program graphs.
- **Rules:** State whether matching is induced or not (GR2), and anchor at labeled or rare vertices.
- **Guardrails:** Set time limits, and count before listing (GR7).

### 191. Automorphism groups and symmetry detection

**Definition:** Finding the symmetries of a graph: the vertex permutations that preserve every edge.

**How it works:**
1. Run the canonical labeling search (#189). Different leaves with the same canonical form reveal automorphisms.
2. Generators of the automorphism group are collected along the way.
3. **Orbits:** sets of vertices that symmetries can map onto each other (structurally indistinguishable vertices).
4. Group size and orbits are computed from the generators (Schreier-Sims).

**Complexity:** Like canonical labeling (#189).

**Agent use:**
- **Role:** Analyst.
- **How:** Removing redundant work (symmetric vertices only need to be analyzed once), breaking symmetry in pattern search (#233), and detecting structurally interchangeable components (redundant replicas in a system graph).
- **Rules:** Use orbits to deduplicate computations.
- **Guardrails:** None specific.

### 192. Maximum common subgraph (McSplit)

**Definition:** Finding the largest subgraph appearing in both of two graphs.

**How it works:**
1. Branch and bound over vertex mappings between the two graphs.
2. **McSplit:** after each mapping decision, partition the unmatched vertices of both graphs into "label classes" by their adjacency to the already-mapped vertices. Only vertices in the same class can still be matched.
3. **Bound:** the sum over classes of min(class size in graph 1, class size in graph 2). Prune when the current size + bound ≤ the best found.
4. Very memory-efficient, with fast bounds.

**Complexity:** NP-hard. Practical for graphs of tens to a few hundred vertices.

**Agent use:**
- **Role:** Analyst.
- **How:** Comparing two structures for their common core: two versions of a workflow, two architectures, two molecules, two config graphs.
- **Rules:** Set time limits, and report whether the result is proven optimal (GR4).
- **Guardrails:** None specific.

### 193. Frequent subgraph mining (gSpan)

**Definition:** Finding subgraph patterns that occur in many graphs of a collection (or many times in one large graph).

**How it works:**
1. Represent each pattern by its minimum DFS code: a canonical sequence of edges from a DFS, which avoids generating duplicate patterns.
2. Grow patterns by adding one edge at a time, only on the "rightmost path" of the DFS tree, so each pattern is generated once.
3. Count the support (in how many graphs it appears), and prune patterns below the minimum support. Supersets of infrequent patterns are also infrequent (anti-monotonicity).
4. For a single large graph, use support measures that keep anti-monotonicity (such as MNI, minimum image-based support).

**Complexity:** Exponential in pattern size. Feasible with a reasonable minimum support.

**Agent use:**
- **Role:** Analyst.
- **How:** Discovering recurring structures in collections: common workflow shapes, recurring code dependency patterns, typical incident propagation subgraphs.
- **Rules:** Start with a high minimum support, then lower it gradually.
- **Guardrails:** Cap the pattern size and the run time (GX1).

### 194. Graph kernels (random walk, shortest path, WL subtree)

**Definition:** Similarity functions between whole graphs, used for classification and clustering of graphs.

**How it works:**
1. **Weisfeiler-Lehman subtree kernel (K#140):** compare counts of refined labels. Fast and strong.
2. **Shortest-path kernel:** compare the multisets of (label, label, distance) triples from all shortest paths.
3. **Random walk kernel:** count matching walks in both graphs, via their direct product graph, with decay by length.
4. **Graphlet kernel:** compare the frequencies of small subgraphs (#120).
5. The kernel matrices feed SVMs or similar classifiers.

**Complexity:** WL is O(h × m) per graph. Random walk kernels are cubic or worse unless approximated.

**Agent use:**
- **Role:** Analyst.
- **How:** Classifies or clusters graph-shaped items: execution traces, query plans, code structure graphs, molecules.
- **Rules:** Use WL as the default baseline.
- **Guardrails:** None specific.

## D6. Structural decompositions

### 195. Planarity testing and embedding (Boyer-Myrvold)

**Definition:** Deciding whether a graph can be drawn in the plane without edge crossings, and producing such a drawing's combinatorial structure (an embedding).

**How it works:**
1. Run a DFS and process vertices in reverse DFS order.
2. Add back edges one at a time, maintaining biconnected components as embedded "bicomps", which can be flipped (mirrored) as needed.
3. When an edge can't be embedded without crossing, the algorithm extracts a Kuratowski subgraph (a subdivision of K₅ or K₃,₃) as the proof of non-planarity.
4. Otherwise, the result is a planar embedding: the circular order of edges around each vertex.

**Complexity:** O(n) (planar graphs have at most 3n − 6 edges).

**Agent use:**
- **Role:** Analyst.
- **How:** Clean diagram layouts (#316), circuit and layout design, and enabling fast planar-graph algorithms (separators, #199).
- **Rules:** Report the Kuratowski subgraph as the certificate when the graph isn't planar (GR6).
- **Guardrails:** None specific.

### 196. Tree decompositions and treewidth heuristics (min-degree, min-fill)

**Definition:** Representing a graph as a tree of overlapping vertex groups (bags). Treewidth (the largest bag size − 1) measures how "tree-like" a graph is. Many hard problems become easy on low-treewidth graphs.

**How it works:**
1. **Elimination ordering:** eliminate vertices one at a time. When a vertex is eliminated, connect all its remaining neighbors (fill-in edges). Each vertex with its neighbors at elimination forms a bag.
2. **Min-degree heuristic:** eliminate the vertex with the fewest remaining neighbors. **Min-fill:** eliminate the vertex that adds the fewest fill edges.
3. The bags, connected in elimination order, form a valid tree decomposition.
4. Lower bounds (minor-min-width, degeneracy) show how far from optimal the result is.
5. Exact treewidth is NP-hard; exact solvers work for small graphs.

**Complexity:** About O(n × m) for the heuristics.

**Agent use:**
- **Role:** Analyst.
- **How:** Finds whether a problem instance is tractable by structure: low treewidth enables exact algorithms (#197) for problems otherwise NP-hard. Also used for probabilistic inference (#272) and query optimization.
- **Rules:** Report the width with a lower bound.
- **Guardrails:** High width (more than about 20–30) means the dynamic programming in #197 isn't feasible (GR3).

### 197. Dynamic programming over tree decompositions

**Definition:** Solving hard graph problems exactly by processing a tree decomposition bottom-up, keeping a table of partial solutions per bag.

**How it works:**
1. Convert the decomposition into a "nice" form: leaf, introduce-vertex, forget-vertex and join bags.
2. For each bag, the table maps each "state" of the bag's vertices (in or out of the solution, a color, and so on) to the best partial solution value.
3. Combine tables bottom-up with rules per bag type.
4. The root table gives the optimum. Backtracking gives the solution itself.
5. Runtime is exponential only in the bag size, not in n.

**Complexity:** O(c^w × n), with w the treewidth and c depending on the problem (for example 2 for independent set, k for k-coloring).

**Agent use:**
- **Role:** Optimizer.
- **How:** Exact solutions for NP-hard problems (independent set, coloring, dominating set, Steiner tree, constraint satisfaction) on graphs with small treewidth: many real networks of trees, series-parallel structures and road networks have small width locally.
- **Rules:** Check the width before running (GR3).
- **Guardrails:** Table sizes grow exponentially with width. Enforce memory caps (GX1).

### 198. Chordal graphs and perfect elimination orderings (maximum cardinality search)

**Definition:** Chordal graphs (every cycle of length 4 or more has a chord) have perfect elimination orderings, which make many hard problems easy. Chordal completion turns any graph into one.

**How it works:**
1. **Maximum cardinality search (MCS):** repeatedly visit the unvisited vertex with the most visited neighbors. The reverse of the visit order is a perfect elimination ordering (each vertex's later neighbors form a clique), if the graph is chordal.
2. **Check:** verify that the ordering is perfect. If it fails, the graph isn't chordal (with a chordless cycle as the certificate).
3. **On chordal graphs:** maximum clique, optimal coloring and maximum independent set are all solvable in linear time.
4. **Chordal completion (triangulation):** add fill-in edges (as in #196) to make any graph chordal. Minimum fill-in is NP-hard, so use heuristics.

**Complexity:** O(n + m) for MCS and recognition.

**Agent use:**
- **Role:** Analyst.
- **How:** Junction tree construction for inference (#272), sparse matrix factorization ordering (#200), and exact solutions on chordal structures.
- **Rules:** Verify chordality with the certificate (GR6).
- **Guardrails:** None specific.

### 199. Graph separators (planar separator theorem, flow-based vertex separators)

**Definition:** Small sets of vertices whose removal splits a graph into balanced pieces. They're the basis of divide-and-conquer algorithms on graphs.

**How it works:**
1. **Lipton-Tarjan planar separator theorem:** every planar graph has a separator of O(√n) vertices splitting it into pieces of at most 2n/3. Found from a BFS tree and a fundamental cycle.
2. **General graphs:** find vertex separators with flow (min vertex cuts between candidate regions, #91), or from a partition (#170) by taking a minimum vertex cover of the cut edges (#90).
3. Recursive separation builds a separator tree.

**Complexity:** O(n) for planar separators. Flow-based methods cost one or more max-flows.

**Agent use:**
- **Role:** Analyst and Optimizer.
- **How:** Divide-and-conquer on large graphs (shortest paths, partitioning), nested dissection (#200), and identifying the minimal "boundary" between regions of a system.
- **Rules:** Report the separator size and the balance achieved.
- **Guardrails:** None specific.

### 200. Nested dissection ordering

**Definition:** Ordering the vertices for sparse matrix factorization by recursively finding separators and numbering separator vertices last. That minimizes fill-in and enables parallelism.

**How it works:**
1. Find a small balanced separator (#199) of the graph (the sparsity graph of the matrix).
2. Recursively order the two separated parts.
3. Number the separator vertices after both parts.
4. Eliminating in this order keeps the fill-in (new nonzeros) small. The independent parts can be factorized in parallel.
5. Alternatives: (approximate) minimum degree ordering, often better for small problems. METIS provides nested dissection ordering.

**Complexity:** For planar graphs, O(n log n) fill and O(n^1.5) factorization operations.

**Agent use:**
- **Role:** Builder.
- **How:** Speeds up every Laplacian or linear-system-heavy computation (#178) with direct solvers, and orders computations for parallel tree-structured processing.
- **Rules:** Compare against minimum degree ordering on the actual problem, and keep the faster.
- **Guardrails:** None specific.

---

Part 5 (#201–250) covers dynamic graph algorithms (dynamic shortest paths, incremental topological order, dynamic MST), streaming graph algorithms and sketches, temporal graphs, and parallel and distributed processing models (Gather-Apply-Scatter, block-centric, GPU frontier models, GraphBLAS, Ligra, out-of-core engines, distributed BFS, connected components, triangle counting and MST), plus subgraph enumeration systems, color coding, graph summarization, spanners, sparsifiers, multi-version graph storage, graph transactions, incremental view maintenance and differential dataflow.