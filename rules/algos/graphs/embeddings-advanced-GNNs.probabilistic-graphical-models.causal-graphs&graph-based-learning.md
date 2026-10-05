# Part 6: Embeddings, advanced GNNs, probabilistic graphical models, causal graphs and graph-based learning (#251–300)

Same format and the same contract (roles; rules GR1–GR8; guardrails GX1–GX5). Earlier references (K#101–150) covered TransE, RotatE, ComplEx, DeepWalk, node2vec, GCN, GraphSAGE, GAT, R-GCN and graph transformers. This part adds what they didn't.

## F1. Node embeddings

### 251. Adjacency spectral embedding (ASE)

**Definition:** Embedding vertices with the top eigenvectors of the adjacency matrix, scaled by the square roots of the eigenvalues. It's statistically justified under random dot product graph models.

**How it works:**
1. Compute the top d eigenvalues (by magnitude) and eigenvectors of A (#176).
2. Embedding X = U_d × |Λ_d|^(1/2).
3. **Random dot product graph model:** P(edge between i and j) = x_i · x_j. ASE consistently estimates the latent positions x_i.
4. Choose d from the "elbow" in the eigenvalue scree plot (Zhu-Ghodsi method).
5. Cluster the embeddings (Gaussian mixtures) to recover stochastic block models (#163).

**Complexity:** One partial eigendecomposition.

**Agent use:**
- **Role:** Analyst.
- **How:** A principled, deterministic embedding for clustering, two-graph comparison (testing whether two graphs come from the same model) and vertex nomination ("find vertices like these").
- **Rules:** Record d and the method used to choose it (GR5).
- **Guardrails:** Eigenvector signs and rotations are arbitrary. Align embeddings (Procrustes) before comparing across runs or graphs.

### 252. LINE (first- and second-order proximity)

**Definition:** An embedding method that preserves direct links (first-order proximity) and shared neighborhoods (second-order proximity), trained efficiently with edge sampling.

**How it works:**
1. **First order:** make linked vertices' embeddings similar: maximize log σ(u · v) for edges.
2. **Second order:** each vertex also has a "context" vector. Vertices with similar neighbors predict the same contexts, so their embeddings become similar.
3. Train with negative sampling, sampling edges in proportion to their weight (alias tables, #18), which keeps gradients stable on weighted graphs.
4. Concatenate the first- and second-order embeddings.

**Complexity:** O(m × d) per epoch.

**Agent use:**
- **Role:** Analyst.
- **How:** Fast, scalable embeddings for large weighted graphs (interaction counts, co-occurrence), for similarity search and downstream features.
- **Rules:** Version embeddings with the graph snapshot and parameters (GR1).
- **Guardrails:** Transductive: new vertices need retraining or an inductive method.

### 253. struc2vec (structural role embeddings)

**Definition:** Embeddings where vertices with similar structural roles (for example, both are hubs or both are bridges) are close, even if they're far apart in the graph.

**How it works:**
1. For each pair of vertices and each radius k, compare their ordered degree sequences of k-hop rings with dynamic time warping. That gives structural distances at several scales.
2. Build a multi-layer context graph: layer k connects vertices weighted by their structural similarity at radius k.
3. Run random walks over this multi-layer graph (moving within and between layers).
4. Train skip-gram on the walks.
5. Optimizations reduce the all-pairs comparisons: compressed degree sequences and candidate neighbors from degree similarity.

**Complexity:** Expensive without optimizations. Practical with them, for medium graphs.

**Agent use:**
- **Role:** Analyst.
- **How:** Finds "same role, different place": comparable gateway services across clusters, similar positions across organizations, similar account behavior patterns.
- **Rules:** Use when role similarity matters. Use node2vec when proximity matters.
- **Guardrails:** Role similarity isn't intent (GX3).

### 254. HOPE (high-order proximity preserving embeddings)

**Definition:** Embedding directed graphs by factorizing a high-order proximity matrix (such as the Katz index) into separate "source" and "target" vectors, which preserves asymmetry.

**How it works:**
1. Choose a proximity S, such as Katz S = (I − βA)⁻¹ βA, written as S = M_g⁻¹ M_l.
2. Use generalized SVD to factorize S ≈ U_s U_tᵀ without ever forming the dense S.
3. Each vertex gets a source embedding (U_s) and a target embedding (U_t).
4. The score for directed proximity from u to v is U_s(u) · U_t(v), which differs from v to u.

**Complexity:** About O(m × d²) with the generalized SVD.

**Agent use:**
- **Role:** Analyst.
- **How:** Directed link prediction and proximity (citations, follows, dependencies) where direction matters.
- **Rules:** Use the source embedding for "who does this point to" and the target embedding for "who points to this".
- **Guardrails:** Choose β below 1/λ_max (as for Katz, #107).

### 255. GraRep (multi-step transition factorization)

**Definition:** Embeddings capturing structure at several distances, by factorizing transition matrices of different step counts and concatenating the results.

**How it works:**
1. Compute the k-step transition probability matrices A¹, A², …, A^K (row-normalized).
2. For each k, build a log-shifted positive pointwise mutual information matrix from Aᵏ.
3. Factorize each with truncated SVD.
4. Concatenate the k representations.
5. Each part reflects proximity at a different number of hops.

**Complexity:** Dense k-step matrices limit it to small and medium graphs.

**Agent use:**
- **Role:** Analyst.
- **How:** Multi-scale embeddings on moderate graphs when both local and global structure matter.
- **Rules:** Check GR3: dense matrices.
- **Guardrails:** Use NetMF (#256) or ProNE (#257) at scale.

### 256. NetMF (DeepWalk as implicit matrix factorization)

**Definition:** The result that DeepWalk, LINE and node2vec implicitly factorize specific closed-form matrices, and computing those factorizations directly gives equal or better embeddings deterministically.

**How it works:**
1. DeepWalk with window T and b negative samples implicitly factorizes M = log(vol(G)/(bT) × (Σ_{r=1}^{T} (D⁻¹A)^r) D⁻¹).
2. **Small T:** compute M exactly, take elementwise log(max(M, 1)), then truncated SVD.
3. **Large T:** approximate the sum using the top eigenpairs of the normalized adjacency.
4. **NetSMF:** sparsify M with spectral sparsifiers (#177) to scale up.

**Complexity:** Dense M for small graphs. NetSMF scales to large graphs.

**Agent use:**
- **Role:** Analyst.
- **How:** Deterministic, reproducible versions of random-walk embeddings with no sampling noise.
- **Rules:** Prefer it when reproducibility matters more than raw speed (GR5).
- **Guardrails:** Memory for dense versions (GR3).

### 257. ProNE (fast sparse factorization with spectral propagation)

**Definition:** A very fast embedding method: factorize a sparse proximity matrix first, then refine the embedding by propagating it through a spectral filter of the graph.

**How it works:**
1. Build a sparse matrix with edge-based proximity (similar to LINE's objectives).
2. Factorize it with randomized truncated SVD (cheap, since it's sparse).
3. **Spectral propagation:** apply a band-pass graph filter (Chebyshev polynomial approximation, #181) to the embedding, which mixes in both local smoothness and global cluster structure.
4. Optionally orthogonalize the result.

**Complexity:** About O(m × d) overall. Very fast on large graphs, even single-threaded.

**Agent use:**
- **Role:** Analyst.
- **How:** Embeddings for graphs with millions to hundreds of millions of edges in minutes, as a strong default baseline.
- **Rules:** Record the filter parameters (GR5).
- **Guardrails:** None specific.

### 258. Partitioned large-scale embedding training (PyTorch-BigGraph style)

**Definition:** Training embeddings for graphs with billions of vertices by partitioning the vertices and training on edge buckets, so only a few partitions sit in memory at once.

**How it works:**
1. Split the vertices into P partitions. Edges are grouped into P × P buckets by the partitions of their endpoints.
2. Train one bucket at a time: load the two partitions' embeddings, train on that bucket's edges, and save them back to disk.
3. Order the buckets so partitions are reused between consecutive buckets (fewer loads).
4. Distributed mode: several machines train non-overlapping buckets in parallel, with a lock server and a parameter server for shared parameters.
5. Negative samples are drawn from the loaded partitions (plus batched negatives) to keep it efficient.

**Complexity:** Memory per machine is bounded by about two partitions.

**Agent use:**
- **Role:** Operator.
- **How:** Knowledge graph and interaction graph embeddings (K#101–107 models) at full organizational scale.
- **Rules:** Record the partitioning, the bucket order and the seeds (GR5). Evaluate with filtered ranking (K#111).
- **Guardrails:** Embeddings of personal data inherit its privacy rules (K#185).

### 259. Graph autoencoders (GAE, VGAE)

**Definition:** Unsupervised models that encode vertices with a GNN and are trained to reconstruct the graph's edges.

**How it works:**
1. **Encoder:** a GCN (K#118) produces embeddings Z from the adjacency and features.
2. **Decoder:** predicted edge probability = σ(z_u · z_v).
3. Train to reconstruct the observed edges, with negative samples for non-edges.
4. **VGAE:** the encoder outputs a mean and variance per vertex. Sample Z, and add a KL divergence term toward a prior (a variational autoencoder).
5. Use Z for link prediction, clustering or visualization.

**Complexity:** About O(m × d) per epoch with sampled negatives.

**Agent use:**
- **Role:** Analyst.
- **How:** Unsupervised embeddings using both features and structure. Reconstruction errors also flag anomalous edges (#136-style).
- **Rules:** Evaluate link prediction with leakage-free splits (K#149).
- **Guardrails:** None specific.

## F2. Advanced graph neural networks

### 260. GIN (graph isomorphism network)

**Definition:** A GNN designed to be as powerful as the 1-WL isomorphism test (K#140), the theoretical maximum for standard message passing.

**How it works:**
1. Update: h_v ← MLP((1 + ε) × h_v + Σ over neighbors u of h_u).
2. **Sum aggregation** (not mean or max) keeps multiset information, so different neighborhoods map to different results.
3. The MLP makes the update injective in practice.
4. **Graph readout:** sum the vertex embeddings from every layer, and concatenate them.

**Complexity:** O(m × d) per layer.

**Agent use:**
- **Role:** Analyst.
- **How:** The default for graph-level tasks where structure matters most: classifying execution traces, query plans, code graphs, molecules.
- **Rules:** Use sum readout for graph-level tasks (K#130).
- **Guardrails:** Can't distinguish graphs that 1-WL can't. Use higher-order models (#265) if that matters.

### 261. APPNP (personalized propagation of neural predictions)

**Definition:** A GNN that separates prediction from propagation: a neural network predicts per vertex, then personalized PageRank spreads those predictions over many hops without over-smoothing.

**How it works:**
1. An MLP produces initial predictions H⁰ from each vertex's own features.
2. **Propagation:** H^(k+1) = (1 − α) × Â H^(k) + α × H⁰, repeated K times (Â is the normalized adjacency). This is power iteration for personalized PageRank (#102).
3. The teleport term α keeps each vertex anchored to its own prediction, which avoids over-smoothing (K#126).
4. Many hops (K = 10 or more) cost nothing extra in parameters.

**Complexity:** O(K × m × classes) for propagation.

**Agent use:**
- **Role:** Analyst.
- **How:** Strong vertex classification in homophilous graphs, with long-range information and little tuning.
- **Rules:** Tune α (often 0.1–0.2) on validation data.
- **Guardrails:** Assumes homophily. Check it first (#263).

### 262. SGC (simplified graph convolution)

**Definition:** A linear GNN: smooth the features over K hops with the normalized adjacency once (no neural layers in between), then train a logistic regression.

**How it works:**
1. Precompute X̃ = Âᴷ X, by K sparse matrix-vector products per feature column.
2. Train a linear classifier on X̃.
3. All graph computation happens once, before training. Training is as cheap as ordinary logistic regression.

**Complexity:** O(K × m × features) preprocessing, then cheap training.

**Agent use:**
- **Role:** Analyst.
- **How:** Very fast, interpretable baseline vertex classification on large graphs. If it works nearly as well as complex GNNs, prefer it.
- **Rules:** Always compare complex GNNs against SGC.
- **Guardrails:** Over-smoothing grows with K. Validate K.

### 263. Heterophily-aware GNNs (H2GCN, GPR-GNN)

**Definition:** GNNs designed for graphs where connected vertices tend to be different (heterophily), where standard GNNs fail.

**How it works:**
1. **Measure homophily first:** the fraction of edges joining same-label vertices. Low values mean heterophily (buyer–seller, fraudster–victim).
2. **H2GCN:** keep each vertex's own embedding separate from its neighbors' aggregates (no mixing). Aggregate 1-hop and 2-hop neighbors separately, and combine all layers' outputs.
3. **GPR-GNN:** learn the propagation weights per hop (generalized PageRank coefficients), which can be negative, so the model can learn high-pass filters (emphasize differences from neighbors).
4. Other approaches: signed or directional message passing, and adaptive filters.

**Complexity:** Similar to standard GNNs.

**Agent use:**
- **Role:** Analyst.
- **How:** Fraud detection, bipartite and interaction graphs, and any setting where "connected to X" doesn't mean "like X".
- **Rules:** Always measure homophily before choosing a GNN.
- **Guardrails:** Vertex predictions about people are proposals (GR8).

### 264. Positional and structural encodings (Laplacian eigenvectors, random-walk encodings)

**Definition:** Extra input features that tell a GNN or graph transformer where each vertex sits in the graph, which message passing alone can't express.

**How it works:**
1. **Laplacian positional encodings:** the first k nontrivial Laplacian eigenvectors (#176) per vertex. Signs are arbitrary, so use random sign flipping during training, or sign-invariant networks (SignNet).
2. **Random-walk structural encodings (RWSE):** the probability that a k-step random walk returns to its start, for k = 1…K. Captures local cycle structure.
3. **Distance encodings:** shortest-path distances to anchors, or within sampled subgraphs.
4. Concatenate them with the vertex features.

**Complexity:** Eigenvectors cost an eigensolve. RWSE costs K sparse matrix products.

**Agent use:**
- **Role:** Analyst.
- **How:** Improves graph transformers (K#124) and GNNs on tasks needing structural awareness (distinguishing positions, detecting cycles).
- **Rules:** Compute encodings on the same snapshot as the features (GR1).
- **Guardrails:** Eigenvector encodings don't transfer across graphs of different sizes without care.

### 265. Higher-order and subgraph GNNs (k-WL, nested GNNs, ESAN)

**Definition:** GNNs more expressive than 1-WL, distinguishing structures that standard message passing can't, by processing tuples of vertices or bags of subgraphs.

**How it works:**
1. **k-WL GNNs:** messages pass between k-tuples of vertices. Very expressive, but the cost grows like nᵏ.
2. **Nested GNNs:** each vertex's embedding comes from a GNN run on its own rooted subgraph (its k-hop neighborhood).
3. **Subgraph GNNs (ESAN):** represent the graph as a bag of subgraphs (each with one vertex or edge removed, or marked). Run a shared GNN on each, then aggregate.
4. These can count cycles, detect triangles and distinguish regular graphs that 1-WL can't.

**Complexity:** Several times to orders of magnitude more expensive than standard GNNs.

**Agent use:**
- **Role:** Analyst.
- **How:** Tasks where fine structure decides the label: specific cycle patterns in fraud, ring structures in molecules, particular code dependency shapes.
- **Rules:** Use only when a simpler GNN fails because of expressiveness, not by default.
- **Guardrails:** Check GR3: costs grow quickly.

### 266. Equivariant GNNs (geometric graphs, E(n)-equivariant networks)

**Definition:** GNNs for graphs embedded in physical space (molecules, meshes, sensor layouts), whose outputs transform correctly when the input is rotated or translated.

**How it works:**
1. Vertices have coordinates in addition to features.
2. Messages depend only on invariant quantities (distances between vertices) or on equivariant ones (relative position vectors), never on absolute coordinates.
3. **EGNN:** update features using squared distances; update coordinates by moving along relative position vectors, weighted by learned functions.
4. Rotating the input rotates vector outputs and leaves scalar outputs unchanged.

**Complexity:** Similar to standard message passing, typically on spatial neighbor graphs.

**Agent use:**
- **Role:** Analyst.
- **How:** Physical and spatial graphs: datacenter or network layouts with coordinates, molecular data, sensor networks, where spatial geometry matters.
- **Rules:** Build the neighbor graph with a radius or k-NN in space (#284).
- **Guardrails:** None specific.

### 267. Masked graph autoencoder pretraining (GraphMAE)

**Definition:** Self-supervised pretraining that masks some vertex features and trains a GNN to reconstruct them, producing representations that transfer to tasks with few labels.

**How it works:**
1. Randomly mask a fraction of vertices' input features (replace them with a learnable mask token).
2. A GNN encoder processes the corrupted graph.
3. Re-mask the masked vertices' encodings, and decode with a light GNN decoder.
4. Loss: a scaled cosine error between reconstructed and original features, which focuses on hard examples.
5. Use the pretrained encoder for downstream tasks, frozen or fine-tuned.

**Complexity:** Like GNN training.

**Agent use:**
- **Role:** Operator.
- **How:** Pretrain once on a large unlabeled graph, then reuse for many small-label tasks (classification, anomaly detection).
- **Rules:** Version the pretrained model with the snapshot it was trained on (GR1).
- **Guardrails:** Pretrained models trained on personal data inherit its governance.

### 268. Layer-wise and importance neighbor sampling (FastGCN, LADIES)

**Definition:** Training GNNs on large graphs by sampling a fixed set of vertices per layer (not per vertex), avoiding the exponential neighborhood growth of per-vertex sampling.

**How it works:**
1. **GraphSAGE-style sampling** (K#119) samples neighbors per vertex: the cost grows exponentially with depth.
2. **FastGCN:** for each layer, independently sample a fixed number of vertices with importance probabilities (by degree), and correct with importance weights. Fast, but layers may be poorly connected.
3. **LADIES:** for each layer, sample from the neighbors of the vertices sampled in the layer above, with probabilities from the normalized adjacency. Layers stay connected, and variance is lower.
4. The memory and cost per batch are fixed.

**Complexity:** Linear in layers × sample size.

**Agent use:**
- **Role:** Operator.
- **How:** Scales GNN training to large graphs with predictable memory.
- **Rules:** Compare the accuracy to full-batch training on a smaller subgraph to check for sampling bias.
- **Guardrails:** None specific.

## F3. Probabilistic graphical models

### 269. Belief propagation on trees (sum-product)

**Definition:** Exact computation of marginal probabilities in tree-structured probabilistic models by passing messages along edges.

**How it works:**
1. The model is a product of local factors (vertex potentials and edge potentials) over a tree.
2. Each vertex sends each neighbor a message summarizing everything from its side of the tree: m_{i→j}(x_j) = Σ over x_i of ψ_i(x_i) ψ_ij(x_i, x_j) × the product of messages into i from its other neighbors.
3. Schedule: leaves to root, then root to leaves (two passes).
4. Marginal of each vertex = its potential × the product of all incoming messages, normalized.
5. Exact on trees, in linear time.

**Complexity:** O(n × k²) for k states per variable.

**Agent use:**
- **Role:** Analyst.
- **How:** Exact probabilistic reasoning on hierarchical models (fault trees, taxonomic classification, tree-structured risk propagation).
- **Rules:** Use log-space computation to avoid numerical underflow.
- **Guardrails:** Exact only on trees. With cycles, use #270 or #272.

### 270. Loopy belief propagation

**Definition:** Applying belief propagation's message updates to graphs with cycles, iterating until messages settle. It's approximate but widely effective.

**How it works:**
1. Initialize all messages uniformly.
2. Update messages repeatedly with the same rule as #269 (synchronously, or asynchronously, which often converges better).
3. **Damping:** new message = λ × old + (1 − λ) × computed. Reduces oscillation.
4. Stop when the messages change less than a tolerance, or after a maximum number of iterations.
5. Approximate marginals from the final messages. Related to minimizing the Bethe free energy.

**Complexity:** O(m × k²) per iteration.

**Agent use:**
- **Role:** Analyst.
- **How:** Propagating risk or trust labels through networks with known seeds (fraud propagation, reputation), error-correcting codes, and labeling problems.
- **Rules:** Report whether it converged (GR4). Use damping.
- **Guardrails:** It can fail to converge or converge to wrong marginals on graphs with many short, strong cycles. Validate on held-out labels.

### 271. Max-product belief propagation and Viterbi decoding

**Definition:** Finding the single most likely joint assignment (MAP), instead of marginals, by replacing sums with maximizations in message passing.

**How it works:**
1. Same as sum-product (#269), with max instead of sum: m_{i→j}(x_j) = max over x_i of […].
2. Usually done in log space as max-sum (sums of log-potentials).
3. Keep back-pointers (the argmax choices).
4. On chains this is the **Viterbi algorithm**: forward pass computing the best score for each state at each step, then a backtrack for the best sequence.
5. Exact on trees and chains; approximate with loops.

**Complexity:** Chains: O(T × k²).

**Agent use:**
- **Role:** Analyst.
- **How:** The most likely hidden sequence: map matching of GPS traces to roads (#319), sequence labeling, decoding states from noisy observations.
- **Rules:** Use log space.
- **Guardrails:** The MAP assignment hides uncertainty. Report marginals too when uncertainty matters.

### 272. Junction tree algorithm

**Definition:** Exact inference on graphs with cycles, by grouping variables into clusters that form a tree, then running belief propagation between clusters.

**How it works:**
1. **Moralize** (for Bayesian networks): connect the parents of each node and drop edge directions.
2. **Triangulate:** add fill-in edges to make the graph chordal (#198), choosing an elimination order with min-fill or min-degree heuristics (#196).
3. Find the maximal cliques. Connect them in a tree satisfying the running intersection property (a maximum-weight spanning tree over the clique overlaps).
4. Pass messages between cliques (sum-product over clique potentials).
5. Exact marginals for every variable.

**Complexity:** Exponential in the largest clique size (the treewidth + 1).

**Agent use:**
- **Role:** Analyst.
- **How:** Exact probabilistic reasoning on moderate models with cycles: diagnostic networks, reliability models, decision support.
- **Rules:** Check the treewidth first (GR3).
- **Guardrails:** Treewidth above about 20–25 makes it infeasible. Use approximate inference.

### 273. Variable elimination

**Definition:** Exact inference by summing out variables one at a time in a chosen order, multiplying the relevant factors together as you go.

**How it works:**
1. Choose an elimination order (min-fill or min-degree, #196).
2. For each variable: multiply all factors that mention it into one factor, then sum that variable out. The result is a new factor over its neighbors.
3. Continue until only the query variables remain. Normalize.
4. The largest intermediate factor depends on the order, which is related to treewidth.
5. Evidence is handled by restricting factors to the observed values first.

**Complexity:** Exponential in the induced width of the order.

**Agent use:**
- **Role:** Analyst.
- **How:** Single exact probability queries on small and medium models. Simpler than a junction tree when only one query is needed.
- **Rules:** Spend time finding a good order. It's the main factor in cost.
- **Guardrails:** Same width limits as #272.

### 274. Gibbs sampling on graphical models

**Definition:** Approximate inference by repeatedly resampling each variable from its distribution conditioned on its neighbors (its Markov blanket).

**How it works:**
1. Start from any assignment consistent with the evidence.
2. For each variable in turn, sample a new value from P(variable | its Markov blanket). That only involves the factors touching it, so each step is local and cheap.
3. Repeat many sweeps. Discard the early samples (burn-in).
4. Estimate marginals and expectations from the samples.
5. **Blocked Gibbs** (sampling groups of correlated variables together) and **chromatic Gibbs** (updating all variables of one color in parallel, using a graph coloring, #184) improve mixing and speed.

**Complexity:** O(local factor cost) per variable per sweep. The number of sweeps depends on mixing.

**Agent use:**
- **Role:** Analyst.
- **How:** Inference in large models where exact methods don't scale, with honest uncertainty estimates.
- **Rules:** Check convergence: several chains, the Gelman-Rubin statistic, effective sample size (GR4).
- **Guardrails:** Strongly correlated variables mix slowly. Results can look converged while not being so.

### 275. Mean-field variational inference

**Definition:** Approximating a complex distribution with a simpler, fully factorized one, optimized by coordinate updates.

**How it works:**
1. Approximate P(x) with Q(x) = Π Q_i(x_i), with each variable independent under Q.
2. Minimize the KL divergence KL(Q ‖ P), equivalently maximize the evidence lower bound (ELBO).
3. **Coordinate updates:** Q_i(x_i) ∝ exp(expected log-potentials, under the neighbors' current Q distributions).
4. Iterate until the ELBO stops improving.
5. Fast and deterministic, but it tends to underestimate uncertainty.

**Complexity:** O(m × k) per iteration.

**Agent use:**
- **Role:** Analyst.
- **How:** Fast approximate inference in large graphical models, such as community models (#163, #164) and label propagation with uncertainty.
- **Rules:** Report that variances are likely underestimated (GR4).
- **Guardrails:** Can converge to local optima. Use several initializations.

### 276. Conditional random fields (linear-chain and graph CRFs)

**Definition:** Models that predict labels for connected items jointly, conditioned on observed features, with learned label-compatibility between neighbors.

**How it works:**
1. P(labels | features) ∝ exp(Σ over vertices of feature weights × features + Σ over edges of compatibility weights for label pairs).
2. **Training:** maximize the conditional log-likelihood, using inference (forward-backward for chains, BP for trees, approximations for general graphs) to compute gradients.
3. **Prediction:** the most likely labeling (Viterbi or max-product, #271), or marginals.
4. Linear-chain CRFs are the classic for sequences. Graph CRFs handle networks.

**Complexity:** Training requires inference at every step. Exact for chains and trees.

**Agent use:**
- **Role:** Analyst.
- **How:** Labeling where neighbors' labels influence each other: entity tagging in text (K#26), classifying linked records consistently.
- **Rules:** Inspect the learned compatibility weights to see which label pairs the model favors.
- **Guardrails:** None specific.

### 277. Factor graphs and general message passing

**Definition:** A bipartite representation of how a global function factorizes into local functions (factors connected to the variables they involve), the common framework for most inference algorithms.

**How it works:**
1. Two kinds of vertices: variables and factors. An edge connects a factor to each variable it involves.
2. **Messages:** variable to factor (the product of the variable's other incoming messages), and factor to variable (sum or max over the factor's other variables, of the factor times its incoming messages).
3. Sum-product gives marginals; max-product gives MAP.
4. It also covers Kalman filtering, decoding of LDPC codes, and many signal processing algorithms.

**Complexity:** O(Σ over factors of k^(factor size)) per iteration.

**Agent use:**
- **Role:** Analyst.
- **How:** A clean way to model and solve custom probabilistic problems over graphs (sensor fusion, reliability, constraint networks) with one reusable message-passing engine.
- **Rules:** Keep factors small. Cost is exponential in factor size.
- **Guardrails:** Same convergence caveats as #270 with cycles.

## F4. Causal and statistical graph learning

### 278. Bayesian network structure learning (score-based: hill climbing, GES)

**Definition:** Learning the directed acyclic graph of a Bayesian network from data, by searching for the structure with the best score.

**How it works:**
1. **Score:** BIC or BDeu, balancing fit against complexity. Decomposable, so local changes are cheap to re-score.
2. **Hill climbing:** start from an empty or initial DAG. Repeatedly apply the single best operation (add, remove or reverse an edge) that keeps the graph acyclic (checked with #202), until no improvement is possible. Use random restarts or tabu lists to escape local optima.
3. **GES (greedy equivalence search):** search over equivalence classes (graphs that encode the same independencies). A forward phase adds edges, a backward phase removes them. Consistent with enough data.
4. Restrict the candidate parents (for example by correlation) to scale up.

**Complexity:** Exponential in general. Heuristics work for hundreds of variables.

**Agent use:**
- **Role:** Analyst.
- **How:** Discovers likely dependency structure among metrics or events (which signals predict which), as input for diagnostics and root-cause analysis.
- **Rules:** Present the learned structure as a hypothesis, with bootstrap confidence on each edge (GR4).
- **Guardrails:** Learned edges show statistical dependence, not proven causation. Never present them as causal without the assumptions of #280.

### 279. d-separation and the Bayes-ball algorithm

**Definition:** A graphical test that reads off conditional independencies from a DAG: whether X and Y are independent given Z.

**How it works:**
1. A path between X and Y is blocked by Z if it contains:
   - a chain (→ M →) or fork (← M →) where M is in Z, or
   - a collider (→ M ←) where neither M nor any descendant of M is in Z.
2. X and Y are d-separated by Z if every path between them is blocked. Then X ⊥ Y | Z in every distribution compatible with the graph.
3. **Bayes-ball:** a linear-time traversal where a "ball" moves through the graph following bouncing rules at each node type, finding everything reachable (dependent) given Z.

**Complexity:** O(n + m).

**Agent use:**
- **Role:** Analyst.
- **How:** Decides which variables need conditioning (or must not be conditioned on) in analyses, and checks whether a dashboard comparison is confounded.
- **Rules:** State the causal graph assumed.
- **Guardrails:** Conclusions are only as valid as the assumed graph.

### 280. Constraint-based causal discovery (PC and FCI algorithms)

**Definition:** Learning a causal graph (up to equivalence) from conditional independence tests in data.

**How it works:**
1. **PC algorithm:** start with a complete undirected graph.
2. For increasing conditioning-set sizes, remove the edge X–Y if X and Y are independent given some subset of their neighbors. Record that separating set.
3. **Orient colliders:** for X – M – Y with X and Y not adjacent, orient X → M ← Y if M isn't in their separating set.
4. Propagate orientations with rules (Meek's rules) that avoid new colliders and cycles.
5. **FCI:** allows hidden confounders and selection bias, producing a more conservative graph (PAG) with edge marks meaning "uncertain".

**Complexity:** Exponential worst case. Feasible for sparse graphs with a moderate number of variables.

**Agent use:**
- **Role:** Analyst.
- **How:** Generates causal hypotheses from observational data (which service metrics drive which outcomes), as input to experiments.
- **Rules:** Report the assumptions (causal sufficiency for PC, faithfulness) and the test used with its significance level (GR4).
- **Guardrails:** Results are hypotheses to validate with experiments or domain knowledge (GR8).

### 281. Do-calculus and adjustment criteria (backdoor and frontdoor)

**Definition:** Rules for deciding, from a causal graph, whether the effect of an intervention can be computed from observational data, and how.

**How it works:**
1. **Backdoor criterion:** a set Z blocks every path from X to Y that starts with an arrow into X, and contains no descendants of X. Then P(Y | do(X)) = Σ over z of P(Y | X, z) P(z).
2. **Frontdoor criterion:** if a mediator M intercepts all directed paths from X to Y, with no unblocked backdoor paths into M, and X blocks the backdoor paths from M to Y, then the effect is identifiable even with confounding between X and Y.
3. **Do-calculus:** three rules transforming expressions with do() into observational ones, complete for identifiability.
4. Algorithms (such as ID) decide identifiability automatically and produce the formula.

**Complexity:** Polynomial for the identification algorithms.

**Agent use:**
- **Role:** Analyst.
- **How:** Correct impact estimates from observational data ("what would happen to latency if we changed this setting?") when experiments aren't possible, with the right adjustment variables.
- **Rules:** Present the causal graph and the adjustment set used.
- **Guardrails:** Wrong graphs give confidently wrong estimates. Prefer experiments when feasible.

### 282. Graphical lasso (sparse inverse covariance estimation)

**Definition:** Learning an undirected graph of conditional dependencies among variables, by estimating a sparse inverse covariance (precision) matrix.

**How it works:**
1. For Gaussian data, a zero in the precision matrix Θ means two variables are conditionally independent given all others.
2. Maximize: log det Θ − trace(S Θ) − λ‖Θ‖₁, where S is the sample covariance.
3. The L1 penalty λ makes many entries exactly zero, giving a sparse graph.
4. Solve with block coordinate descent (each row is a lasso regression).
5. Choose λ by cross-validation or stability selection.

**Complexity:** O(p³) per iteration for p variables. Practical for hundreds to a few thousand variables.

**Agent use:**
- **Role:** Analyst.
- **How:** Builds dependency graphs between metrics (which signals are directly related, after accounting for the others), as input to anomaly detection and root-cause analysis.
- **Rules:** Standardize variables first. Report λ and the selection method.
- **Guardrails:** It assumes approximately Gaussian, stationary data. Check the assumptions.

### 283. NN-descent (approximate k-nearest-neighbor graph construction)

**Definition:** Building an approximate k-nearest-neighbor graph quickly, using the principle that "a neighbor of a neighbor is likely a neighbor".

**How it works:**
1. Start each point with k random neighbors.
2. Each iteration: for each point, check its neighbors' neighbors (and reverse neighbors) as candidates. Keep the k closest in a bounded heap.
3. Only "new" neighbors (added in the last iteration) generate candidates, which avoids repeated comparisons.
4. Stop when few updates happen.
5. Sampling the candidates controls the cost per iteration.

**Complexity:** Empirically about O(n^1.14) distance computations.

**Agent use:**
- **Role:** Builder.
- **How:** Creates k-NN graphs from vectors (embeddings, features) for spectral clustering (#158), label propagation (#286), graph-based ANN indexes (#295) and deduplication.
- **Rules:** Measure the k-NN graph's recall against brute force on a sample (GR4).
- **Guardrails:** None specific.

### 284. Similarity graph construction (ε-graphs, k-NN, mutual k-NN, adaptive kernels)

**Definition:** Turning a set of data points into a graph whose edges connect similar points, the step that defines what every later graph algorithm "sees".

**How it works:**
1. **ε-graph:** connect points within distance ε. Sensitive to density differences.
2. **k-NN graph:** connect each point to its k nearest neighbors (#283). Symmetrize by OR (keep if either is in the other's list) or AND (mutual k-NN, which removes hub effects).
3. **Edge weights:** Gaussian kernel exp(−d²/σ²). An adaptive σ per point (the distance to its k-th neighbor, self-tuning) handles varying density.
4. Check connectivity, and the hub structure (#21-style hubness from vector reference).

**Complexity:** Dominated by neighbor search.

**Agent use:**
- **Role:** Builder.
- **How:** The foundation of clustering, semi-supervised learning and manifold methods on vector data.
- **Rules:** Record k, symmetrization, kernel and σ (GR5). Test sensitivity to k.
- **Guardrails:** Results downstream can change completely with these choices. Never report clusters without saying how the graph was built.

## F5. Graph-based ranking and recommendation

### 285. TextRank (graph-based keyword and sentence ranking)

**Definition:** Applying PageRank to graphs built from text (words linked by co-occurrence, or sentences linked by similarity) to extract keywords and summary sentences.

**How it works:**
1. **Keywords:** vertices are candidate words (filtered by part of speech). Edges connect words co-occurring within a window of N words.
2. **Sentences:** vertices are sentences. Edges are weighted by similarity (word overlap, or embedding cosine).
3. Run weighted PageRank (#102).
4. Top-ranked words (merged into phrases when adjacent) are keywords. Top-ranked sentences form an extractive summary.

**Complexity:** O(text length) to build, plus PageRank.

**Agent use:**
- **Role:** Analyst.
- **How:** Deterministic, model-free keyword extraction and summarization, at zero token cost: tagging documents, chunk summaries, and quick overviews of logs or tickets.
- **Rules:** Use the same tokenization as downstream search.
- **Guardrails:** Extractive summaries can lose context. Keep links to the source sentences.

### 286. Harmonic label propagation (Zhu-Ghahramani)

**Definition:** Semi-supervised classification on a graph: labeled vertices keep their labels, and every unlabeled vertex takes the weighted average of its neighbors' labels.

**How it works:**
1. Fix the labels of the labeled vertices (as 0/1 or class probability vectors).
2. For unlabeled vertices, require f(v) = Σ w_uv f(u) / Σ w_uv (the harmonic property).
3. Solve the resulting Laplacian system L_uu f_u = −L_ul f_l (#178), or iterate until convergence.
4. Interpretation: f(v) = the probability that a random walk from v reaches a labeled vertex of the class first.
5. Class mass normalization corrects for class imbalance.

**Complexity:** One Laplacian solve.

**Agent use:**
- **Role:** Analyst.
- **How:** Spreads a few known labels (known fraud, known topic, known category) to unlabeled items through a similarity graph (#284), at zero token cost.
- **Rules:** Mark propagated labels as inferred, with scores (K2).
- **Guardrails:** Labels propagate along graph errors too. Validate on held-out labels.

### 287. Pixie (real-time random-walk recommendation)

**Definition:** A recommendation algorithm that runs many short random walks with restart on a bipartite user–item (or pin–board) graph, in real time.

**How it works:**
1. Start from the query items (a user's recent items), each with a weight.
2. Run many short random walks: item → random board containing it → random item on that board, restarting at the query items.
3. **Biased walks:** prefer edges matching the user's features (language, topic).
4. Count visits per item. Combine counts across query items so items visited from several query items are boosted.
5. **Early stopping:** stop when the top candidates have enough visits.

**Complexity:** Bounded number of walk steps per query: milliseconds.

**Agent use:**
- **Role:** Retriever.
- **How:** Fast, explainable "related items" for documents, entities or tools, using co-occurrence graphs.
- **Rules:** Prune very high-degree boards or items before walking (GX2).
- **Guardrails:** Popular items dominate visit counts. Apply popularity normalization.

### 288. P3α and RP3β (item-based random-walk recommenders)

**Definition:** Simple, strong recommenders that score items by three-step random walks on the user–item graph, with popularity correction.

**How it works:**
1. Walk: user → item → user → item (three steps on the bipartite graph).
2. The item-to-item similarity matrix W = P_iu × P_ui, where P are row-normalized transition matrices.
3. **P3α:** raise the transition probabilities to a power α, which controls how much strong edges dominate.
4. **RP3β:** divide each item's score by its popularity^β, which reduces the bias toward popular items.
5. Keep the top-k neighbors per item, and recommend by summing similarities from the user's items.

**Complexity:** Sparse matrix products with top-k pruning.

**Agent use:**
- **Role:** Retriever.
- **How:** Strong, fast, interpretable baselines for recommendation tasks: tools, documents, related code modules (co-change graphs).
- **Rules:** Tune α and β on held-out interactions. Always compare more complex recommenders against these baselines.
- **Guardrails:** None specific.

### 289. Path Ranking Algorithm (PRA)

**Definition:** Predicting relations in knowledge graphs by using the probabilities of reaching the target through typed relation paths as features.

**How it works:**
1. Enumerate relation-path types (sequences of edge labels) up to length L that frequently connect pairs having the target relation.
2. For a candidate pair (s, t), compute each path type's feature: the probability that a random walk following that path type from s ends at t.
3. Train a logistic regression on those features with known positive and negative pairs.
4. The learned weights show which path types predict the relation (interpretable rules).

**Complexity:** Path probability computation per candidate, which can be costly for long paths.

**Agent use:**
- **Role:** Analyst.
- **How:** Explainable knowledge graph completion (K#132), where each prediction is backed by readable paths.
- **Rules:** Use predicted facts only as proposals, with their supporting paths (K7).
- **Guardrails:** Limit the path length (GR3).

### 290. HeteSim (relevance along metapaths)

**Definition:** A relevance measure between objects of possibly different types in a heterogeneous graph, along a given metapath, symmetric by construction.

**How it works:**
1. Split the metapath in the middle (adding a virtual middle step for odd lengths).
2. Compute the probability distribution of where a walk from the source reaches the middle, and where a walk from the target (backward) reaches the middle.
3. HeteSim = the normalized cosine of those two distributions.
4. The result is symmetric, and comparable across object types.

**Complexity:** Sparse matrix products along the metapath halves.

**Agent use:**
- **Role:** Analyst.
- **How:** Relevance between different types (author–venue, user–tag, service–team) along a meaningful path.
- **Rules:** Choose metapaths carefully (K#70).
- **Guardrails:** None specific.

### 291. PathSim (metapath-based similarity via sparse products)

**Definition:** Similarity between objects of the same type based on the number of metapath instances connecting them, normalized so very popular objects don't dominate.

**How it works:**
1. Choose a symmetric metapath, for example Author–Paper–Venue–Paper–Author.
2. Compute the commuting matrix M = A₁ A₂ … A_k with sparse products (#221). M[x][y] = the number of path instances from x to y.
3. PathSim(x, y) = 2 × M[x][y] / (M[x][x] + M[y][y]).
4. This finds "peers": objects with similar visibility, not just the most connected objects.

**Complexity:** Sparse matrix products. Compute rows on demand for large graphs.

**Agent use:**
- **Role:** Analyst.
- **How:** Finds comparable peers in heterogeneous graphs: similar services by shared dependencies and teams, similar customers by shared products.
- **Rules:** Use row-on-demand computation (#116 style).
- **Guardrails:** None specific.

## F6. Network alignment and graph matching

### 292. IsoRank (spectral network alignment)

**Definition:** Aligning vertices of two networks by an iterative similarity: two vertices match well if their neighbors match well, combined with prior similarity (for example, names).

**How it works:**
1. Define R(i, j) = the similarity of vertex i in graph G₁ and vertex j in G₂.
2. Iterate: R ← α × (normalized sum of R over neighbor pairs) + (1 − α) × prior similarity H.
3. This is a PageRank-like eigenvector computation on the product graph.
4. Extract a one-to-one alignment from R with greedy matching or the Hungarian algorithm (#85).

**Complexity:** O(m₁ × m₂) per iteration on the product, often reduced by sparsifying the prior.

**Agent use:**
- **Role:** Curator and Analyst.
- **How:** Aligns two versions of a system graph, merges two organizational graphs, and supports knowledge graph entity alignment (K#133).
- **Rules:** Use a sparse prior (candidate pairs only) to scale.
- **Guardrails:** Alignments are proposals (GR8), reviewed before merging.

### 293. Embedding-based network alignment (REGAL, FINAL)

**Definition:** Aligning networks at scale by embedding both into a shared space with structural and attribute features, then matching nearest neighbors.

**How it works:**
1. **REGAL:** compute structural identity features per vertex (degree counts in k-hop rings, as in struc2vec) plus attributes.
2. Pick landmark vertices across both graphs, and compute each vertex's similarity to the landmarks.
3. Low-rank factorization (xNetMF) gives embeddings in a shared space.
4. Align by nearest neighbor search (k-d trees or ANN).
5. **FINAL:** an optimization-based method that combines structural and attribute consistency with priors, solved by iterative updates.

**Complexity:** Near-linear for REGAL.

**Agent use:**
- **Role:** Curator.
- **How:** Aligns large networks without seed matches, for example matching accounts across systems or nodes across infrastructure inventories.
- **Rules:** Validate on a sample with known matches. Report precision at the chosen threshold.
- **Guardrails:** Cross-system identity matching of people needs governance approval (GX3).

### 294. Gromov-Wasserstein graph matching (optimal transport)

**Definition:** Matching two graphs (possibly of different sizes, without shared features) by finding a soft correspondence that best preserves pairwise distances, using optimal transport.

**How it works:**
1. Each graph gives a structure matrix: shortest-path distances, adjacency or diffusion distances.
2. Find a transport plan T (soft matching) minimizing Σ (C₁(i, k) − C₂(j, l))² T(i, j) T(k, l): matched pairs should have matched distances.
3. Solve with iterative methods: entropic regularization plus Sinkhorn steps, or conditional gradient.
4. **Fused Gromov-Wasserstein:** also includes feature distances between matched vertices.
5. The plan gives a soft alignment; the optimal value is a distance between graphs.

**Complexity:** About O(n³) per iteration naively. Faster with sparse or low-rank approximations.

**Agent use:**
- **Role:** Analyst.
- **How:** Comparing and aligning graphs with no shared identifiers (two architecture graphs, two process graphs), and graph-level similarity measures.
- **Rules:** Use for small and medium graphs, or with approximations.
- **Guardrails:** The non-convex problem may give local optima. Use several initializations.

## F7. Navigable graphs and program analysis

### 295. Proximity graph construction for approximate nearest neighbor search (RNG, Delaunay, k-NN refinement)

**Definition:** The graph-theoretic foundations of graph-based vector search: which edges a proximity graph needs so that greedy search finds nearest neighbors.

**How it works:**
1. **Delaunay graph:** greedy search on it always finds the exact nearest neighbor. But it becomes almost complete in high dimensions.
2. **Relative neighborhood graph (RNG):** keep edge (u, v) only if no point w is closer to both u and v than they are to each other. Sparse and still navigable in practice. The pruning rules of HNSW and Vamana are RNG-style approximations.
3. **k-NN graph refinement:** start from an approximate k-NN graph (#283), add reverse edges, prune with the RNG rule, and ensure connectivity from the entry point.
4. Long-range edges (from hierarchy or α-pruning) shorten search paths.

**Complexity:** Construction is near-linear to n^1.x with approximate methods.

**Agent use:**
- **Role:** Builder.
- **How:** Understanding and tuning vector index graphs (vector reference V#65–76): why pruning parameters matter, and why connectivity checks are needed.
- **Rules:** Check reachability from the entry point after building (V#74).
- **Guardrails:** None specific.

### 296. Navigability and greedy routing (Kleinberg's small-world model)

**Definition:** The theory of when local greedy routing (always move to the neighbor closest to the target) finds short paths, which explains why graph-based search works.

**How it works:**
1. Kleinberg's model: a grid with local edges, plus a few long-range edges per vertex, with the probability of a long edge proportional to distance^(−r).
2. Greedy routing finds paths of O(log² n) steps only when r equals the grid dimension. Other exponents make greedy routing slow, even though short paths exist.
3. The key: long-range links must be spread across distance scales (some to each scale).
4. Hierarchical graphs (HNSW layers) create links at all scales by construction.

**Complexity:** O(log² n) greedy steps in the navigable regime.

**Agent use:**
- **Role:** Analyst.
- **How:** Explains search quality problems in navigable graphs, and guides the design of overlay networks, peer-to-peer routing and indexes.
- **Rules:** When greedy search stalls, check the distribution of long-range links.
- **Guardrails:** None specific.

### 297. IFDS and IDE (interprocedural dataflow analysis as graph reachability)

**Definition:** Precise analysis of how dataflow facts move across function calls, by turning the analysis into reachability on an "exploded supergraph".

**How it works:**
1. The supergraph links every function's control flow graph (C#94) through call and return edges.
2. **Exploded supergraph:** each node is (program point, dataflow fact). Edges describe how each statement transforms each fact. This works for "distributive" analyses: taint, uninitialized variables, possibly-null values.
3. A fact holds at a point if (point, fact) is reachable from the start along a "realizable" path, where calls and returns match.
4. The tabulation algorithm computes summary edges per function (input fact → output fact), reused at every call site.
5. **IDE** extends IFDS with values attached to facts (for example constant propagation).

**Complexity:** O(E × D³), with E the supergraph edges and D the number of facts.

**Agent use:**
- **Role:** Analyst.
- **How:** Precise taint analysis (C#97) across functions: does user input reach this sink through any call chain? Powers security scanning and impact analysis for code edits.
- **Rules:** Use established frameworks (Soot/Heros, PhASAR, and similar).
- **Guardrails:** Reflection and dynamic calls create blind spots. Report unanalyzed calls (C#92).

### 298. CFL-reachability (Dyck reachability)

**Definition:** Reachability where a path is valid only if its edge labels form a word of a context-free language, typically matched parentheses (calls matched with returns, or field stores matched with loads).

**How it works:**
1. Edges are labeled, for example "(₁" for a call at site 1 and ")₁" for the matching return.
2. A path is valid if its labels form a balanced (Dyck) word. That rules out returning to the wrong caller.
3. **Dynamic programming:** repeatedly add derived edges when two adjacent edges combine according to the grammar's rules (like transitive closure, with grammar productions).
4. Specialized algorithms speed this up for Dyck languages and bidirected graphs.

**Complexity:** O(n³) in general. Faster special cases exist.

**Agent use:**
- **Role:** Analyst.
- **How:** The precise backbone of context-sensitive program analyses (taint, points-to with field sensitivity), so the agent's impact analysis doesn't report impossible paths.
- **Rules:** Use bounded context depth when full precision is too expensive, and report the bound.
- **Guardrails:** Check GR3: cubic cost on large programs.

### 299. Andersen's points-to analysis (inclusion-based constraint graphs)

**Definition:** Computing which objects each pointer or reference may point to, by solving subset constraints with propagation over a constraint graph.

**How it works:**
1. Turn statements into constraints: `p = &x` gives x ∈ pts(p); `p = q` gives pts(q) ⊆ pts(p); `p = *q` and `*p = q` give complex constraints that add edges dynamically.
2. Build a constraint graph: an edge q → p means pts(q) flows into pts(p).
3. Propagate points-to sets along edges with a worklist. When pointer sets grow, add the new edges implied by complex constraints.
4. **Optimizations:** cycle detection and collapsing (all pointers in a cycle share one set, #57), difference propagation (only new elements), and bitset or BDD representation of sets.

**Complexity:** O(n³) worst case. Practical on large programs with these optimizations.

**Agent use:**
- **Role:** Analyst.
- **How:** Precise call graph construction (resolving virtual calls and function pointers, C#92) and alias analysis, which makes code search and edit impact analysis complete.
- **Rules:** Report the analysis's soundness limits (reflection, native code).
- **Guardrails:** None specific.

### 300. Steensgaard's points-to analysis (unification-based)

**Definition:** A fast, less precise points-to analysis that merges (unifies) pointer targets with union-find instead of tracking subset relations.

**How it works:**
1. Each pointer and object is a node in a union-find structure (#51).
2. An assignment `p = q` doesn't create a one-way subset relation. It unifies what p and q point to into one class.
3. Process each statement once, with union operations, recursively unifying the pointed-to classes too.
4. The result: equivalence classes of possibly aliased locations.

**Complexity:** Near-linear, O(n × α(n)).

**Agent use:**
- **Role:** Analyst.
- **How:** Very fast alias and call graph approximation for huge codebases, as a first pass that later analyses refine with Andersen's analysis (#299) where precision matters.
- **Rules:** Treat results as over-approximations: more possible targets than real ones.
- **Guardrails:** Imprecision adds false positives in impact analysis. Label them clearly (GR4).

---

Part 7 (#301–320), the final part, covers graphs in systems: register allocation by coloring, critical path scheduling, Coffman-Graham and HEFT scheduling, build-system graphs, garbage collection traversal, cycle collection, distributed deadlock detection, gossip and consensus averaging, network reliability, routing protocols (link-state, distance-vector, path-vector, spanning tree protocol), graph layout (force-directed, Sugiyama, edge bundling), geometric graphs, map matching, and attack graphs.