# Part 3: Embeddings and graph machine learning (#101–150)

Same format and the same contract (roles; rules K1–K8; guardrails KG1–KG6).

## C1. Knowledge graph embeddings

### 101. TransE

**Definition:** An embedding model where each relation is a translation (a vector shift) between entity vectors: head + relation ≈ tail.

**How it works:**
1. Give each entity and each relation a learned vector of the same size.
2. The score of a triple (h, r, t) is −‖h + r − t‖: the closer h + r lands to t, the more plausible the triple.
3. Training pushes true triples to high scores and corrupted triples (with h or t replaced at random, #108) to low scores, using a margin loss (#110).
4. Entity vectors are usually normalized to stop them growing without bound.
5. Simple and fast, but it can't model one-to-many relations well (all tails of one head get pushed to the same point) or symmetric relations.

**Agent use:**
- **Role:** Reasoner (link prediction baseline).
- **How:** A cheap first model to estimate missing links and find similar entities, before trying more expressive models.
- **Rules:** Predictions are candidates (K7), stored with their score and model version (K1).
- **Guardrails:** Check per-relation accuracy. TransE fails silently on relation types it can't represent.

### 102. TransH and TransR

**Definition:** TransE extensions that project entities into relation-specific spaces, so one entity can behave differently per relation.

**How it works:**
1. **TransH:** each relation has a hyperplane. Entities are projected onto it, and the translation happens within that plane. Several tails of a one-to-many relation can then share a projection while staying distinct in the full space.
2. **TransR:** each relation has a projection matrix into its own relation space, with the translation there.
3. Training and negative sampling work as for TransE.
4. More expressive, at a higher cost (TransR's matrices are large).

**Agent use:**
- **Role:** Reasoner.
- **How:** Useful when the graph has many one-to-many and many-to-many relations that TransE handles badly.
- **Rules:** Compare against simpler models on the same filtered evaluation (#111).
- **Guardrails:** More parameters mean more overfitting risk on small graphs. Use validation-based early stopping.

### 103. DistMult

**Definition:** A bilinear embedding model whose score is the elementwise product of the head, relation and tail vectors, summed.

**How it works:**
1. Score(h, r, t) = Σᵢ hᵢ × rᵢ × tᵢ (a diagonal bilinear form).
2. High scores mean a plausible triple.
3. Trained with logistic or cross-entropy loss (#110).
4. Because the score is symmetric in h and t, it can't tell (h, r, t) from (t, r, h), so it can't model asymmetric relations like `parentOf`.

**Agent use:**
- **Role:** Reasoner.
- **How:** A strong, simple baseline for symmetric or mostly symmetric relations (`similarTo`, `relatedTo`).
- **Rules:** Don't use it for directional relations.
- **Guardrails:** Test on asymmetric relations specifically. It will predict reversed facts with high confidence.

### 104. ComplEx

**Definition:** DistMult with complex-valued vectors, which can model both symmetric and asymmetric relations.

**How it works:**
1. Entities and relations are vectors of complex numbers.
2. Score = the real part of Σ hᵢ × rᵢ × conj(tᵢ), using the complex conjugate of the tail.
3. The conjugate breaks the symmetry, so (h, r, t) and (t, r, h) can score differently.
4. Relations with purely real parts behave symmetrically; imaginary parts give asymmetry.
5. Trained like DistMult, often with N3 regularization.

**Agent use:**
- **Role:** Reasoner.
- **How:** A robust, widely used default for link prediction on real knowledge graphs with mixed relation types.
- **Rules:** Tune embedding size and regularization on a validation set.
- **Guardrails:** Scores aren't probabilities. Calibrate them before using thresholds (#144).

### 105. RotatE

**Definition:** An embedding model where each relation rotates the head entity in complex space to reach the tail.

**How it works:**
1. Entities are complex vectors. Each relation is a vector of unit-length complex numbers, which are rotations.
2. Score = −‖h ∘ r − t‖, where ∘ is the elementwise product, rotating each coordinate of h by an angle.
3. Rotations naturally model symmetric relations (a rotation by π), inverse relations (the opposite rotation) and composition (adding angles).
4. Trained with self-adversarial negative sampling (#109).

**Agent use:**
- **Role:** Reasoner.
- **How:** A good choice when relation patterns matter (inverses, compositions such as "nationality via birthplace").
- **Rules:** Use with self-adversarial sampling, as designed.
- **Guardrails:** Same calibration caveat as #104.

### 106. TuckER

**Definition:** An embedding model based on Tucker tensor decomposition, with a shared core tensor that captures interactions between entities and relations.

**How it works:**
1. The knowledge graph is a 3D binary tensor (head × relation × tail).
2. TuckER factorizes it into entity embeddings, relation embeddings, and a shared core tensor W.
3. Score = W multiplied with h, r and t along its three dimensions.
4. The shared core lets relations share learned patterns, which helps relations with few examples.
5. Several earlier bilinear models (DistMult, ComplEx) are special cases.

**Agent use:**
- **Role:** Reasoner.
- **How:** Strong accuracy on benchmarks. Useful when many relations are rare and benefit from sharing.
- **Rules:** Use 1-N scoring (#110) for efficient training.
- **Guardrails:** The core tensor makes it heavier. Check the memory budget for large relation sets.

### 107. ConvE

**Definition:** An embedding model that applies 2D convolution over reshaped head and relation embeddings to score candidate tails.

**How it works:**
1. Reshape the head and relation vectors into 2D grids and stack them.
2. Apply convolution filters to capture interactions between their dimensions.
3. Flatten, project, and take the dot product with every candidate tail embedding.
4. Scores for all tails are computed at once (1-N scoring), which makes training efficient.
5. More expressive than simple translation or bilinear models with relatively few parameters.

**Agent use:**
- **Role:** Reasoner.
- **How:** Useful on large graphs with complex relation patterns, where the efficient 1-N scoring helps.
- **Rules:** Evaluate with filtered ranking (#111), and check test leakage (#149). ConvE's original evaluation surfaced the inverse-relation leakage problem.
- **Guardrails:** None specific beyond calibration.

### 108. Negative sampling (uniform and Bernoulli)

**Definition:** Creating false triples to train embeddings, since knowledge graphs only store true facts.

**How it works:**
1. For each true triple (h, r, t), corrupt it by replacing the head or the tail with a random entity.
2. **Uniform:** replace the head or tail with equal probability.
3. **Bernoulli:** for one-to-many relations, replace the head more often (and the reverse for many-to-one), which lowers the chance of accidentally producing true facts.
4. Optionally restrict corruptions to type-compatible entities, so negatives are realistic.
5. Train the model to score true triples above the corrupted ones.

**Agent use:**
- **Role:** Operator (training).
- **How:** The negatives define what the model learns to reject. Type-aware negatives make predictions more meaningful.
- **Rules:** Filter out corruptions that are actually true facts in the graph.
- **Guardrails:** Random negatives are often trivially easy. Monitor whether validation metrics actually improve, or the model learns nothing useful.

### 109. Self-adversarial negative sampling

**Definition:** Weighting negative samples by how plausible the current model finds them, so training focuses on hard negatives.

**How it works:**
1. Draw several negatives per positive triple.
2. Score them with the current model.
3. Compute weights with a softmax over the negatives' scores, scaled by a temperature: harder (higher-scoring) negatives get more weight.
4. Use the weights in the loss, without backpropagating through the weights.
5. Training concentrates on the confusing cases.

**Agent use:**
- **Role:** Operator.
- **How:** A standard improvement for KG embedding training, especially with RotatE (#105).
- **Rules:** Tune the temperature on validation data.
- **Guardrails:** Hard negatives may include true but unrecorded facts (open world, #96), which teaches the model wrong boundaries. Use type filtering and review.

### 110. Loss functions and scoring schemes for KG embeddings

**Definition:** The training objectives that turn triple scores into learning signals.

**How it works:**
1. **Margin ranking loss:** max(0, γ − score(true) + score(corrupted)). Pushes true triples above negatives by a margin γ.
2. **Logistic loss:** treat each triple as binary classification (true or false).
3. **1-N cross-entropy:** for (h, r, ?), score all entities as tails at once and apply softmax cross-entropy with the true tail(s) as targets. Efficient and usually the strongest.
4. Regularization (L2, N3) prevents embeddings from growing too large.
5. Add reciprocal relations (r⁻¹ for every r), so head prediction becomes tail prediction.

**Agent use:**
- **Role:** Operator.
- **How:** The agent picks the loss by model and graph size; 1-N cross-entropy with reciprocal relations is a strong default.
- **Rules:** Use the same training setup when comparing models, or the comparison is unfair.
- **Guardrails:** None specific.

### 111. Filtered ranking evaluation (MRR, Hits@k)

**Definition:** The standard evaluation of link prediction: how highly does the model rank the true answer among all candidates?

**How it works:**
1. For each test triple (h, r, t), score (h, r, x) for every entity x.
2. **Filtering:** remove other candidates that are also true triples (known from train, validation or test data), so the model isn't penalized for ranking other correct answers above t.
3. Find the rank of t.
4. **MRR:** the mean of 1/rank. **Hits@k:** the share of test triples where t ranks in the top k.
5. Repeat for head prediction (?, r, t), and report the averages.

**Agent use:**
- **Role:** Observer.
- **How:** The agent compares models with filtered MRR and Hits@k, reported per relation, not only overall.
- **Rules:** Always report filtered metrics, with the exact candidate set and the tie-breaking rule.
- **Guardrails:** Benchmark scores don't guarantee production usefulness. Also evaluate precision of the top predictions with human review (#148).

### 112. DeepWalk

**Definition:** Learning node embeddings by treating random walks as "sentences" and training a word-embedding model on them.

**How it works:**
1. From each node, run several random walks of fixed length.
2. Each walk is a sequence of node IDs, like a sentence of words.
3. Train a skip-gram model (word2vec): predict the nodes that appear near each node in the walks.
4. Nodes that co-occur in walks (structurally close) get similar embeddings.

**Agent use:**
- **Role:** Retriever and Observer.
- **How:** Quick structural similarity: "nodes positioned like this one". Also useful as features for downstream ML.
- **Rules:** Record walk length, walks per node, window size and seed.
- **Guardrails:** Embeddings are transductive. New nodes need retraining or an inductive method (#115, #119).

### 113. node2vec

**Definition:** DeepWalk with biased random walks that can favor local (BFS-like) or exploratory (DFS-like) movement.

**How it works:**
1. Walks are second-order: the next step depends on the current and previous node.
2. **Return parameter p:** controls the probability of going back to the previous node.
3. **In-out parameter q:** a low q favors moving farther away (exploration, capturing communities); a high q favors staying close (capturing structural roles).
4. Train skip-gram on the walks, as in DeepWalk.

**Agent use:**
- **Role:** Retriever and Observer.
- **How:** The agent tunes p and q for the goal: community similarity (same topic cluster) or role similarity (both are "hub" nodes).
- **Rules:** Evaluate embeddings on the actual downstream task, not on visual inspection.
- **Guardrails:** Same transductive limitation as #112.

### 114. Metapath2vec

**Definition:** Random-walk embeddings for heterogeneous graphs, where walks follow given metapaths (type sequences).

**How it works:**
1. Define metapaths such as Author → Paper → Venue → Paper → Author (#70).
2. Random walks must follow the metapath's sequence of node types.
3. Train skip-gram, optionally with negative sampling restricted by node type (the metapath2vec++ variant).
4. Embeddings capture relatedness according to the chosen meaning.

**Agent use:**
- **Role:** Retriever.
- **How:** Gives task-meaningful similarity in typed graphs: "authors similar by publication venues", rather than by any connection.
- **Rules:** Choose and document metapaths per use case.
- **Guardrails:** A poor metapath choice produces misleading similarity. Validate on known similar pairs.

### 115. Inductive entity representations (NodePiece and similar)

**Definition:** Representing entities by composing reusable parts (anchor nodes, relation types), so new, unseen entities get embeddings without retraining.

**How it works:**
1. Select a set of anchor nodes.
2. Represent each entity by its nearest anchors (and their distances) plus the relation types connected to it, a kind of "tokenization" of the entity.
3. An encoder (MLP or transformer) combines these tokens into an embedding.
4. A new entity is tokenized the same way and encoded immediately.
5. The parameter count depends on the vocabulary size, not on the number of entities.

**Agent use:**
- **Role:** Reasoner.
- **How:** Essential when entities are added constantly. The agent can predict links for new entities without waiting for retraining.
- **Rules:** Re-select anchors if the graph's structure changes a lot.
- **Guardrails:** Embedding quality for entities with very few connections is low. Use text features too (#116).

### 116. Text-enhanced KG embeddings (KG-BERT, SimKGC style)

**Definition:** Scoring or embedding triples using the text of entity names and descriptions, through language models.

**How it works:**
1. **KG-BERT:** feed "head text [SEP] relation text [SEP] tail text" into a transformer and classify plausibility. Accurate, but slow (each candidate triple is a separate forward pass).
2. **SimKGC style (bi-encoder):** embed "head + relation" text and "tail" text separately, and score by cosine similarity. Contrastive training with many negatives.
3. Works for entities never seen in training, as long as they have text.
4. Can be combined with structural embeddings.

**Agent use:**
- **Role:** Reasoner and Retriever.
- **How:** Predicts links for new or sparse entities using their descriptions. Bi-encoder versions support fast candidate search with vector indexes.
- **Rules:** Version the text model and the text fields used (K1).
- **Guardrails:** Text models may reproduce facts from their pretraining that aren't in your sources. Predictions remain proposals that need evidence (K7).

## C2. Graph neural networks

### 117. Message passing (the general GNN framework)

**Definition:** A framework where each node updates its representation by collecting "messages" from its neighbors, repeated over several layers.

**How it works:**
1. Each node starts with a feature vector: attributes, text embeddings, or learned IDs.
2. **Message:** each neighbor computes a message from its own vector (and the edge's features).
3. **Aggregate:** the node combines the incoming messages with a permutation-invariant function: sum, mean, max or attention.
4. **Update:** the node combines the aggregate with its own vector through a learned function.
5. After L layers, each node's vector reflects its L-hop neighborhood.

**Agent use:**
- **Role:** Operator and Reasoner.
- **How:** The common pattern behind GNN-based classification, link prediction and recommendation on knowledge graphs.
- **Rules:** Choose the number of layers by the hop range that matters; usually 2–3 is enough.
- **Guardrails:** Deep stacks cause over-smoothing (#126). Don't just add layers.

### 118. GCN (graph convolutional network)

**Definition:** A message-passing model that averages neighbor features with degree-based normalization, then applies a shared linear transformation.

**How it works:**
1. Add self-loops so each node keeps its own information.
2. Each node's new vector = activation(W × Σ over neighbors of (neighbor vector / √(deg(node) × deg(neighbor)))).
3. The symmetric normalization prevents high-degree nodes from dominating.
4. Stacking layers expands the receptive field.
5. Trained end to end for a task (node classification, #129).

**Agent use:**
- **Role:** Operator.
- **How:** A simple baseline for node classification on homogeneous graphs (one node type, one edge type).
- **Rules:** Use it as the baseline before trying more complex models.
- **Guardrails:** Classic GCN uses the full graph, so it's transductive. New nodes need methods like GraphSAGE (#119).

### 119. GraphSAGE (sampling and aggregation)

**Definition:** An inductive GNN that learns aggregation functions over sampled neighbors, so it works on unseen nodes and large graphs.

**How it works:**
1. For each node, sample a fixed number of neighbors per layer (for example 25 at hop 1, then 10 at hop 2).
2. Aggregate their vectors with mean, max-pooling or an LSTM aggregator.
3. Concatenate with the node's own vector, apply a linear layer and activation, and normalize.
4. The learned functions apply to any node with features, including new ones.
5. Sampling keeps the cost per node bounded, even with supernodes.

**Agent use:**
- **Role:** Operator and Reasoner.
- **How:** Practical for large, changing knowledge graphs: embeddings for new entities come from their features and neighbors, without retraining.
- **Rules:** Use the same sampling configuration in training and serving.
- **Guardrails:** Sampling makes outputs slightly random. Fix seeds, or average several samples, for stable predictions.

### 120. GAT (graph attention network)

**Definition:** A GNN that learns how much attention to give each neighbor, instead of fixed averaging.

**How it works:**
1. Transform each node's features with a shared weight matrix.
2. For each edge, compute an attention score from the two endpoints' transformed features.
3. Normalize the scores over each node's neighbors with softmax.
4. The node's new vector is the attention-weighted sum of its neighbors' vectors.
5. Multiple heads (independent attention mechanisms) are concatenated or averaged for stability.

**Agent use:**
- **Role:** Operator.
- **How:** Helps when neighbors differ in importance, which is common in noisy extracted graphs.
- **Rules:** Inspect attention weights as a hint of what matters, with explainability methods (#145) for real explanations.
- **Guardrails:** Attention weights aren't reliable explanations on their own.

### 121. R-GCN (relational graph convolutional network)

**Definition:** A GCN extension for multi-relational graphs, with separate weights per relation type.

**How it works:**
1. For each relation type r (and its inverse), use its own weight matrix W_r.
2. A node aggregates messages from neighbors separately per relation, then sums across relations, plus a self-connection.
3. Normalization per relation keeps scales balanced.
4. **Basis decomposition:** each W_r is a combination of a few shared basis matrices, which cuts parameters for graphs with many relations.
5. Used for entity classification, and as an encoder for link prediction (combined with a scorer like DistMult).

**Agent use:**
- **Role:** Operator and Reasoner.
- **How:** The natural GNN for knowledge graphs, where edge types carry the meaning.
- **Rules:** Use basis or block decomposition when there are many relation types.
- **Guardrails:** Rare relations get poorly trained weights. Check per-relation performance.

### 122. CompGCN

**Definition:** A GNN that learns both entity and relation embeddings together, by composing them in each message.

**How it works:**
1. Each message from a neighbor combines the neighbor's entity vector with the relation vector, using a composition operation: subtraction (TransE-like), multiplication (DistMult-like) or circular correlation.
2. Separate weights handle incoming edges, outgoing edges and self-loops.
3. Relation embeddings are also updated in each layer.
4. Output entity and relation embeddings feed a link-prediction scorer.

**Agent use:**
- **Role:** Reasoner.
- **How:** Combines the strengths of KG embeddings (#101–107) with neighborhood context from GNNs, which often helps link prediction.
- **Rules:** Pick the composition operation by validation results.
- **Guardrails:** None specific beyond those for GNNs in general.

### 123. Heterogeneous graph transformer (HGT)

**Definition:** An attention-based GNN for graphs with many node and edge types, with type-specific attention parameters.

**How it works:**
1. Separate projections for each node type and edge type.
2. Attention between a node and a neighbor uses parameters specific to (source type, edge type, target type).
3. Messages are also type-specific.
4. Relative temporal encoding can capture time on edges.
5. Mini-batches are sampled with type balance, so rare types are represented (HGSampling).

**Agent use:**
- **Role:** Operator.
- **How:** For rich enterprise knowledge graphs (people, documents, systems, tickets), where treating all node types alike loses meaning.
- **Rules:** Make sure each node type has enough training signal.
- **Guardrails:** Many type-specific parameters can overfit rare types. Monitor per-type performance.

### 124. Graph transformers with positional encodings

**Definition:** Transformer models over graph nodes, with positional and structural encodings that tell the model where each node sits in the graph.

**How it works:**
1. Attention can let every node attend to every other (or to a sampled subset), not only to neighbors.
2. Positional encodings add structure: Laplacian eigenvectors, random-walk probabilities, shortest-path distances, or degree.
3. Some models bias attention by graph distance or by the edges along the path.
4. Hybrid designs combine local message passing with global attention.
5. Full attention costs O(n²), so it's typically used on subgraphs.

**Agent use:**
- **Role:** Operator and Reasoner.
- **How:** Useful for reasoning over retrieved subgraphs (#157), where long-range connections inside the subgraph matter.
- **Rules:** Apply to bounded subgraphs, not the whole graph.
- **Guardrails:** Check the compute and memory cost per subgraph size.

### 125. Mini-batch subgraph training (Cluster-GCN, GraphSAINT)

**Definition:** Training GNNs on large graphs by sampling small subgraphs as mini-batches.

**How it works:**
1. **Cluster-GCN:** partition the graph into clusters (METIS, #20). Each batch combines a few clusters and keeps the edges between them.
2. **GraphSAINT:** sample subgraphs by nodes, edges or random walks, with normalization that corrects for the sampling bias.
3. Train the GNN on each subgraph as if it were the whole graph.
4. Memory stays bounded, unlike full-graph training or recursive neighbor expansion.

**Agent use:**
- **Role:** Operator.
- **How:** Lets the agent train GNNs on graphs with millions of nodes on limited hardware.
- **Rules:** Use the same feature preprocessing for training and serving.
- **Guardrails:** Biased sampling distorts training. Use the methods' normalization corrections.

### 126. Over-smoothing and over-squashing mitigation

**Definition:** Fixing two failure modes of deep GNNs: node vectors becoming all alike (over-smoothing), and distant information getting squeezed through bottlenecks (over-squashing).

**How it works:**
1. **Over-smoothing:** repeated averaging makes node vectors converge.
   - Fixes: residual or skip connections, jumping knowledge (combining all layers' outputs), normalization (PairNorm), DropEdge, or fewer layers.
2. **Over-squashing:** information from exponentially many distant nodes must pass through a few edges.
   - Fixes: graph rewiring (adding shortcut edges), global attention (#124), or virtual nodes connected to everything.
3. Diagnose by tracking how similar node vectors become with depth.

**Agent use:**
- **Role:** Operator.
- **How:** When adding layers makes a model worse, the agent uses these fixes instead of deeper stacks.
- **Rules:** Track performance against depth during model selection.
- **Guardrails:** Rewiring changes the graph the model sees. Document it, and never write rewired edges back into the knowledge graph.

### 127. Temporal graph networks (TGN)

**Definition:** GNNs for graphs where edges arrive over time, keeping a memory per node that's updated with each event.

**How it works:**
1. Events are timestamped edges (interactions, transactions).
2. Each node has a memory vector, updated by a recurrent unit (GRU) when an event involves it.
3. Time encodings represent the time since past events.
4. At prediction time, combine the node's memory with temporal neighborhood attention over recent events.
5. Train in time order: predict future events from past ones only.

**Agent use:**
- **Role:** Reasoner and Observer.
- **How:** For dynamic graphs (transactions, communication, interactions), where recent behavior matters: fraud, churn, next interaction.
- **Rules:** Strict time-ordered splits. Never let future events into training features (#149).
- **Guardrails:** Memory state must be checkpointed with the model. A restart without its memory gives degraded predictions.

### 128. SEAL (link prediction from enclosing subgraphs)

**Definition:** Predicting whether a link exists by classifying the local subgraph around the two candidate nodes with a GNN.

**How it works:**
1. For a candidate pair (u, v), extract the k-hop subgraph around both nodes.
2. Label each node in the subgraph by its distances to u and to v (double-radius node labeling), so the GNN knows each node's role relative to the pair.
3. Run a GNN on the subgraph and pool to a single score.
4. Train on existing links (positives) and sampled non-links (negatives).
5. The model learns its own heuristics, generalizing common neighbors, Adamic-Adar and Katz (#131).

**Agent use:**
- **Role:** Reasoner.
- **How:** Strong link prediction that also works for new nodes. The extracted subgraph doubles as context for explanations.
- **Rules:** Remove the target link from its own subgraph during training. Leaving it in leaks the answer.
- **Guardrails:** Extracting a subgraph per candidate is expensive. Score a pre-filtered candidate list (#131), not all pairs.

### 129. Node classification setup (transductive and inductive)

**Definition:** Predicting labels for nodes (entity type, risk class, topic) from their features and graph neighborhood.

**How it works:**
1. **Transductive:** the whole graph is visible during training. Some nodes are labeled and others are predicted, and test nodes are present (unlabeled) in training.
2. **Inductive:** test nodes or graphs are unseen during training. The model must generalize (GraphSAGE, #119).
3. Split the labeled nodes into train, validation and test sets, randomly or by time or structure.
4. Train the GNN with cross-entropy on the training labels, select by validation, and report test results.
5. Compare against non-graph baselines (features only) to check that the graph actually helps.

**Agent use:**
- **Role:** Reasoner and Curator.
- **How:** Fills missing labels such as types (#134), categories and risk flags, marked as inferred (K2) with confidence.
- **Rules:** Pick the setup matching production: inductive if new entities keep arriving.
- **Guardrails:** Neighbor labels can leak the answer (especially in duplicated or near-duplicate entities). Check the splits (#149).

### 130. Graph pooling and readout

**Definition:** Combining node representations into a single representation of a whole graph or subgraph.

**How it works:**
1. **Simple readout:** sum, mean or max over all node vectors.
2. **Attention readout:** a weighted sum with learned importance per node.
3. **Hierarchical pooling:** coarsen the graph step by step (learned clustering in DiffPool, top-k node selection in SAGPool), then read out.
4. The result feeds a classifier or similarity function.

**Agent use:**
- **Role:** Reasoner.
- **How:** Used to score retrieved subgraphs (is this subgraph relevant to the question?) and for subgraph-level classification (#128, #137).
- **Rules:** Use sum readout when graph size carries meaning; mean when it shouldn't.
- **Guardrails:** None specific.

## C3. Graph machine learning tasks

### 131. Link prediction heuristics (common neighbors, Adamic-Adar, Jaccard, Katz)

**Definition:** Simple scores from graph structure that estimate how likely two nodes are to be linked.

**How it works:**
1. **Common neighbors:** the number of shared neighbors.
2. **Jaccard:** shared neighbors / all neighbors of either node.
3. **Adamic-Adar:** a sum over shared neighbors of 1/log(degree), so rare shared neighbors count more than hubs.
4. **Resource allocation:** like Adamic-Adar, using 1/degree.
5. **Katz:** counts all paths between the nodes, with longer paths weighted exponentially less.

**Agent use:**
- **Role:** Reasoner.
- **How:** Cheap, explainable candidate generation for link prediction. The agent pre-filters candidate pairs with heuristics, then scores them with stronger models (#128).
- **Rules:** Always compare learned models against these baselines; they're surprisingly strong.
- **Guardrails:** Hub nodes dominate common-neighbor counts. Prefer degree-adjusted scores.

### 132. Knowledge graph completion pipeline

**Definition:** The end-to-end process of predicting missing facts, validating them and adding approved ones to the graph.

**How it works:**
1. **Target:** choose relations and entity types where gaps matter (for example missing `headquarteredIn`).
2. **Candidates:** generate them with heuristics, embeddings, GNNs, rule mining (#95) or LLM proposals.
3. **Score:** calibrated scores (#144) and supporting evidence (paths, rules, text).
4. **Validate:** type and shape checks (#5), consistency checks (#97), and evidence search in source documents.
5. **Review:** high-confidence facts with evidence can be auto-accepted per policy; the rest goes to humans (#148).
6. **Write:** accepted facts are marked inferred or predicted, with provenance (K1, K2).

**Agent use:**
- **Role:** Reasoner and Curator.
- **How:** The agent runs completion as a reviewed pipeline, never "model predicts, graph accepts".
- **Rules:** Every predicted fact carries its model, version, score, evidence and status (K1, K2, K7).
- **Guardrails:** Predicted facts about people (KG2) or with legal or financial impact always need human review.

### 133. Entity alignment across knowledge graphs

**Definition:** Finding which entities in two different knowledge graphs refer to the same real-world thing.

**How it works:**
1. Start with seed alignments (known matches from shared IDs or manual work).
2. Embed both graphs into a shared space: train with the seeds as anchors, or encode each with a GNN, then align.
3. Add attribute and name similarity (text embeddings, string similarity, #37).
4. For each entity, find nearest candidates in the other graph. Enforce one-to-one matching where appropriate (for example with stable matching or the Hungarian algorithm).
5. Iterative bootstrapping: add confident new matches as seeds and retrain.

**Agent use:**
- **Role:** Curator and Operator.
- **How:** Used when merging knowledge graphs (after an acquisition, or integrating a public KG). The output is a reviewed mapping, not automatic merges.
- **Rules:** Store alignments as mapping links with confidence (`skos:exactMatch`/`closeMatch`, #6), and only use `sameAs` after review.
- **Guardrails:** Bootstrapping amplifies early errors. Review samples of the newly added seeds each round.

### 134. Entity typing with embeddings and models

**Definition:** Predicting an entity's types (classes) from its embedding, relations and text.

**How it works:**
1. Build features: KG embeddings (#101–107), GNN outputs (#121), text embeddings of names and descriptions.
2. Train a multi-label classifier over the type hierarchy (an entity can have several types).
3. Enforce hierarchy consistency: predicting `Employee` implies `Person`.
4. Calibrate probabilities (#144).
5. Optionally combine with rule-based typing (#44).

**Agent use:**
- **Role:** Reasoner.
- **How:** Fills missing types, which makes type-based queries, shapes (#5) and retrieval filters work.
- **Rules:** Predicted types are marked inferred (K2), and must not conflict with disjointness axioms (#97).
- **Guardrails:** Never assign types used for access control or legal categorization automatically (KG1, KG3).

### 135. Relation prediction (which relation links two entities)

**Definition:** Predicting the relation type between two known-related entities.

**How it works:**
1. Given (h, ?, t), score every relation type, with KG embeddings or a classifier over pair features.
2. Features include: the entity types, paths between h and t (path ranking), shared neighbors, and text mentioning both.
3. Apply schema constraints: only relations whose domain and range allow these types.
4. Output the ranked relations with calibrated scores.

**Agent use:**
- **Role:** Extractor and Reasoner.
- **How:** Useful when extraction found a connection but not its type ("A and B are related"), or for checking whether an extracted relation is plausible.
- **Rules:** Schema constraints filter the candidates before scoring (K3).
- **Guardrails:** Low-margin predictions (two relations scored about equally) go to review.

### 136. Graph anomaly detection

**Definition:** Finding unusual nodes, edges or subgraphs that differ from normal patterns.

**How it works:**
1. **Structural signals:** unusual degree, sudden degree spikes, dense subgraphs (#84), unusual patterns in the ego network (OddBall: deviations from typical edge-count and weight relationships).
2. **Attribute signals:** values unusual relative to similar nodes.
3. **Learned:** train a graph autoencoder to reconstruct structure and attributes; nodes with high reconstruction error are anomalous.
4. **Temporal:** sudden changes in a node's behavior over time.
5. Rank anomalies by score for investigation.

**Agent use:**
- **Role:** Observer.
- **How:** Detects data errors (wrong merges, extraction bugs) as well as real-world anomalies (fraud, abuse).
- **Rules:** Anomaly scores lead to investigation, never to automatic action against people.
- **Guardrails:** Anomaly results about people are sensitive (KG2). Restrict access and keep audit logs.

### 137. Fraud ring detection

**Definition:** Finding groups of accounts or entities working together, revealed by shared attributes and interactions.

**How it works:**
1. Build a graph of accounts linked by shared attributes (device, address, phone, payment method) and by interactions (transfers).
2. Find suspicious structures: dense subgraphs, cycles of money transfers, many accounts sharing one device.
3. Use components (#79), communities (#82), k-cores (#84) and cycle detection (#64).
4. Score groups with graph features and learned models (GNNs, #121).
5. Send top-ranked groups to investigators with the evidence subgraph.

**Agent use:**
- **Role:** Observer and Retriever.
- **How:** The agent gathers evidence subgraphs and explains them ("12 accounts share 2 devices and transfer in a cycle"), so investigators decide faster.
- **Rules:** The agent presents evidence and scores; humans make enforcement decisions.
- **Guardrails:** Shared attributes have innocent explanations (shared offices, public Wi-Fi). Never auto-act on graph signals alone (KG2, KG3).

### 138. Knowledge-graph-based recommendation

**Definition:** Using knowledge graph relations between items (and users) to improve and explain recommendations.

**How it works:**
1. Link users to items (interactions) and items to knowledge graph entities (attributes, categories, creators).
2. **Embedding approach:** jointly learn interaction and KG embeddings, so items sharing KG attributes get similar vectors.
3. **Propagation approach (RippleNet, KGAT):** spread a user's preferences along KG edges from their items to related entities and items, using attention to weigh relations.
4. **Path explanations:** "recommended because you liked X, which has the same director as Y".
5. Helps cold-start items, which have KG connections but no interactions yet.

**Agent use:**
- **Role:** Retriever.
- **How:** The agent can produce explained recommendations grounded in actual graph paths.
- **Rules:** Explanations must come from real paths in the graph, not be generated after the fact.
- **Guardrails:** Avoid using sensitive attributes (KG2) as recommendation paths.

### 139. Collective classification

**Definition:** Classifying connected nodes together, using the predicted labels of neighbors as evidence for each other.

**How it works:**
1. Start with predictions from node features alone.
2. Iterate: re-predict each node using its own features plus a summary of its neighbors' current predicted labels (Iterative Classification Algorithm).
3. Alternatively, use loopy belief propagation over a probabilistic model.
4. Stop when the predictions are stable.
5. It exploits homophily (connected nodes tend to share labels).

**Agent use:**
- **Role:** Reasoner.
- **How:** Effective for labeling entities in networks where neighbors share categories, such as topic labeling of linked documents.
- **Rules:** Mark results as inferred (K2), with confidence.
- **Guardrails:** Fails in heterophilic graphs (where neighbors tend to differ, like buyer-seller). Check homophily first.

### 140. Weisfeiler-Lehman (WL) test and graph kernels

**Definition:** An iterative node-relabeling procedure that summarizes graph structure, used to compare graphs and to understand what GNNs can distinguish.

**How it works:**
1. Start with each node's label (or a constant).
2. Each round, give each node a new label: a hash of its current label plus the sorted multiset of its neighbors' labels.
3. After several rounds, the label counts summarize the graph's structure.
4. **WL kernel:** the similarity of two graphs is the dot product of their label-count vectors.
5. **Theory:** standard message-passing GNNs can't distinguish graphs that the 1-WL test can't distinguish.

**Agent use:**
- **Role:** Observer and Reasoner.
- **How:** Fast structural fingerprints for subgraphs: finding repeated patterns, comparing schemas, deduplicating subgraph templates.
- **Rules:** Use it for structural similarity, not semantic similarity.
- **Guardrails:** Different graphs can produce the same fingerprint. Confirm important matches with exact comparison.

### 141. Graph edit distance and subgraph similarity

**Definition:** The minimum cost of node and edge insertions, deletions and substitutions to turn one graph into another.

**How it works:**
1. Define costs for each edit operation (for example by label mismatch).
2. The exact computation is NP-hard: search over node mappings (A* with lower bounds).
3. Approximations: bipartite assignment of nodes with local structure costs (Hungarian algorithm), or learned GNN similarity models.
4. Output: the distance and the edit mapping.

**Agent use:**
- **Role:** Observer and Curator.
- **How:** Compares entity neighborhoods to support duplicate detection (two entities with nearly identical neighborhoods), or compares graph versions for change review.
- **Rules:** Use approximations for anything beyond small graphs.
- **Guardrails:** Set a timeout. Exact computation can run forever on medium-sized graphs.

### 142. Hyperbolic embeddings

**Definition:** Embedding nodes in hyperbolic space, which naturally represents tree-like hierarchies with low distortion.

**How it works:**
1. Hyperbolic space expands exponentially with radius, like a tree's branching.
2. Models such as the Poincaré ball place general concepts near the center and specific ones near the edge.
3. Distances are computed with the hyperbolic metric.
4. Training uses Riemannian optimization (gradient steps adapted to the curved space).
5. Hierarchies embed well even in few dimensions.

**Agent use:**
- **Role:** Reasoner and Retriever.
- **How:** Good for taxonomies and ontologies, as in predicting "is-a" links, finding the right category for a new concept, and hierarchy-aware similarity.
- **Rules:** Use for strongly hierarchical relations, and Euclidean models for the rest.
- **Guardrails:** Numerical instability near the boundary. Use clipping and stable implementations.

### 143. Temporal knowledge graph completion

**Definition:** Predicting missing facts when facts are valid at specific times: (h, r, t, time).

**How it works:**
1. Facts carry timestamps or intervals (K8).
2. Models add time to the embeddings: time-specific relation vectors, entity vectors that change over time (diachronic embeddings), or rotations by time (TeRo).
3. **Interpolation:** predict facts at past times inside the observed range. **Extrapolation:** predict future facts, often with recurrent models over time snapshots (RE-Net).
4. Evaluate with time-aware filtering.

**Agent use:**
- **Role:** Reasoner.
- **How:** Answers time-scoped questions with missing data ("who likely held this role in 2019?"), and forecasts events, always as estimates.
- **Rules:** Strict time-ordered evaluation for forecasting (#149).
- **Guardrails:** Forecasts must never be stored as facts. Store them as predictions with their date and confidence (K2).

### 144. Calibration of link prediction scores

**Definition:** Converting raw model scores into reliable probabilities that a predicted fact is true.

**How it works:**
1. Raw embedding scores aren't probabilities, and their scales differ by relation.
2. Hold out labeled true and false triples, with realistic negatives.
3. Fit a calibration mapping per relation (or with relation-specific parameters): Platt scaling (logistic), isotonic regression, or temperature scaling.
4. Check calibration with reliability diagrams and the expected calibration error.
5. Recalibrate after retraining or major data changes.

**Agent use:**
- **Role:** Reasoner and Observer.
- **How:** Lets the agent use meaningful thresholds ("auto-accept above 0.95 with evidence, review between 0.7 and 0.95") in the completion pipeline (#132).
- **Rules:** Thresholds are set per relation on calibrated scores.
- **Guardrails:** Calibration measured on easy random negatives is too optimistic. Use hard, type-consistent negatives.

### 145. GNN explainability (GNNExplainer and similar)

**Definition:** Identifying which edges and node features were most important for a GNN's prediction.

**How it works:**
1. For one prediction, learn a soft mask over the edges and features in the node's neighborhood.
2. Optimize the mask so the prediction stays the same using as few edges and features as possible (maximize mutual information, with a sparsity penalty).
3. High-mask edges form the explanation subgraph.
4. Alternatives: gradient-based attribution, perturbation-based methods, and counterfactual explanations ("removing edge X changes the prediction").

**Agent use:**
- **Role:** Observer and Reasoner.
- **How:** The agent attaches explanation subgraphs to predictions, so reviewers see why a fact or label was predicted.
- **Rules:** Present explanations as approximate model insights, not as proof.
- **Guardrails:** Explanations can look convincing while being unfaithful. Check them with counterfactual tests on samples.

### 146. Graph contrastive learning

**Definition:** Learning node or graph representations without labels, by making two augmented views of the same graph agree.

**How it works:**
1. Create two views of a graph or subgraph with augmentations: drop edges, mask features, sample subgraphs.
2. Encode both views with a GNN.
3. Train so the same node in both views has similar representations (positives), and different nodes don't (negatives), with an InfoNCE-style loss.
4. Variants without negatives use bootstrapping (BGRL).
5. The learned representations transfer to downstream tasks with few labels.

**Agent use:**
- **Role:** Operator.
- **How:** Useful when labels are scarce: pretrain representations on the full unlabeled graph, then fine-tune with a few labels.
- **Rules:** Choose augmentations that preserve meaning. Dropping critical edges changes what a node is.
- **Guardrails:** Evaluate on the downstream task; contrastive loss values alone say little.

### 147. Few-shot and inductive relation learning

**Definition:** Predicting facts for relations with very few examples, or for entities and graphs not seen in training.

**How it works:**
1. **Few-shot relations:** learn to compare a query pair with a handful of example pairs of the new relation, through matching networks or meta-learning across many training relations.
2. **Inductive link prediction on new graphs:** models learn from local subgraph structure (GraIL, similar to SEAL, #128), or from relation-level patterns, rather than from entity identities.
3. Inductive models apply to unseen entities, and sometimes to unseen relations.

**Agent use:**
- **Role:** Reasoner.
- **How:** When a new relation type is added to the schema, the agent can bootstrap predictions from a few curated examples.
- **Rules:** Few-shot predictions always go through review (#148).
- **Guardrails:** Performance varies widely by relation. Measure before trusting it.

### 148. Active learning for knowledge graph curation

**Definition:** Choosing which candidate facts people should review next, to improve quality fastest with limited review time.

**How it works:**
1. Score the candidate facts (extracted or predicted) with confidence.
2. Select review items by strategy: most uncertain (near the decision boundary), most impactful (high-centrality entities, frequently queried facts), or diverse (covering different relations and sources).
3. Humans label the selected items.
4. Use the labels to retrain extractors and predictors, and to recalibrate thresholds.
5. Repeat.

**Agent use:**
- **Role:** Curator and Operator.
- **How:** The agent prepares review queues with evidence, and learns from each decision. Human review time goes where it matters.
- **Rules:** Each reviewed item records the reviewer, the decision and the evidence shown.
- **Guardrails:** Also sample some high-confidence items for review. Otherwise systematic high-confidence errors are never caught.

### 149. Leakage-free evaluation splits

**Definition:** Splitting data so test answers can't be inferred trivially from training data.

**How it works:**
1. **Inverse-relation leakage:** if (h, parentOf, t) is in training and (t, childOf, h) is in test, the test is trivial. Remove near-duplicate and inverse relations, or split them together (as the FB15k-237 and WN18RR benchmarks were designed to do).
2. **Temporal leakage:** for time-based tasks, train only on the past and test on the future.
3. **Entity leakage:** duplicate entities (unresolved) put the same fact in both train and test.
4. **Feature leakage:** features computed on the full graph (including test edges) give away the answer.
5. Check splits with simple baselines. Suspiciously high baseline scores indicate leakage.

**Agent use:**
- **Role:** Observer and Operator.
- **How:** The agent designs and checks evaluation splits before trusting any reported metric.
- **Rules:** Document how splits were made, and recompute features within each split.
- **Guardrails:** Results that look too good are investigated before deployment, not celebrated.

### 150. Bias and fairness in graph machine learning

**Definition:** Detecting and reducing systematic unfairness in graph-based predictions, often amplified by network structure.

**How it works:**
1. **Sources of bias:** unequal data coverage (some groups less documented), homophily (predictions spreading along group lines), and historical bias in links.
2. **Measure:** compare error rates and positive rates across groups, where it's lawful and appropriate to use group data.
3. **Mitigate:** rebalance training data, use fairness-aware objectives, use adversarial training to remove group information from representations, and post-process thresholds.
4. Check coverage gaps: are some groups' entities missing facts more often?

**Agent use:**
- **Role:** Observer.
- **How:** The agent reports quality and coverage per segment (region, language, entity category), not only in aggregate, so gaps become visible.
- **Rules:** Predictions used in decisions about people get a fairness review before deployment.
- **Guardrails:** Never infer sensitive attributes (KG2) to "check fairness" without explicit governance approval. Graph-based inference of such attributes is itself a privacy risk.

---

Part 4 (#151–200) covers knowledge graphs with LLMs (text-to-query, entity linking for questions, GraphRAG local and global search, subgraph and path retrieval, hybrid vector-graph retrieval, fact verification, graph agents and agent memory), plus operations (incremental updates, MERGE semantics, change propagation, access control, distributed processing) and observability (quality, freshness, supernodes, text-to-query accuracy, GraphRAG evaluation).