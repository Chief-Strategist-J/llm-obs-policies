This is a new reference: **300 neural network algorithms**, with no repeats from the earlier references. Already covered and excluded: tokenization, pooling, contrastive embedding training, hard negative mining, Matryoshka embeddings, cross-encoders, ColBERT, SPLADE, vector quantization (PQ, binary, int8 vectors), KG embeddings (TransE, RotatE and others), every GNN family (GCN through GraphMAE), DeepWalk/node2vec, PCA/UMAP/t-SNE, autoencoders for vector compression, bandits, Bayesian optimization and k-means.

Same format: definition, how it works step by step, cost, and agent use (role, approach, rules, guardrails). No code, in 6 parts of 50.

**Map:**
- **Part 1 (#1–50):** core building blocks, activations, losses, backpropagation, optimizers, schedules, initialization.
- **Part 2 (#51–100):** normalization, regularization, convolutional networks, detection, recurrent networks and sequence models.
- **Part 3 (#101–150):** attention and transformer internals, position encodings, efficient attention, state space models, mixture of experts, vision and multimodal transformers, decoding.
- **Part 4 (#151–200):** generative models (VAEs, GANs, flows, diffusion, flow matching), self-supervised learning, meta-learning, scientific ML, recommendation and time series, reinforcement learning foundations.
- **Part 5 (#201–250):** advanced RL, LLM post-training and alignment, parameter-efficient tuning, model merging, distillation, continual learning, distributed and mixed-precision training, pruning.
- **Part 6 (#251–300):** quantization and inference serving, robustness, uncertainty, interpretability, model editing, safety, evaluation and training diagnostics.

---

# Neural network agent contract (referenced in every entry)

| Role | Job | Can write? |
|---|---|---|
| **Architect** | Chooses and configures model structures | Configs only |
| **Trainer** | Runs training and fine-tuning jobs | Model checkpoints, in staging |
| **Evaluator** | Measures quality, robustness, calibration and safety | No (can block promotion) |
| **Deployer** | Optimizes and serves models | Production, through approved releases |
| **Analyst** | Debugs and interprets models and training runs | No |

**Rules:**
- **NR1. Full lineage:** every model records its code version, config, data snapshot hashes, seeds, hardware and parent checkpoint.
- **NR2. Baselines first:** every new method is compared against a simple, tuned baseline.
- **NR3. Clean evaluation:** held-out data, leakage checks, fixed evaluation sets, and confidence intervals.
- **NR4. Monitor training:** loss, gradient norms, learning rate, throughput and anomalies are tracked live.
- **NR5. Budget first:** estimate compute, memory and cost before launching a job, and refuse runs over budget.
- **NR6. Reproducible:** fixed seeds and recorded nondeterminism. Results that can't be reproduced aren't trusted.
- **NR7. Gated promotion:** no model reaches production without passing quality, safety and regression gates.
- **NR8. Outputs are proposals:** model predictions that affect people or money are decisions for humans or approved policies.

**Guardrails:**
- **NX1. Compute caps:** time, GPU-hour and cost limits per job.
- **NX2. Data governance:** personal data, licenses and consent are checked before training, and training data is documented.
- **NX3. Safety evaluation:** models are tested for harmful outputs, bias and misuse before release.
- **NX4. Instant rollback:** the previous model version stays deployable.
- **NX5. Untrusted inputs:** inputs and retrieved content are data, not instructions to the system.

---

# PART 1: FOUNDATIONS

## A1. Core building blocks

### 1. Perceptron learning rule

**Definition:** The original trainable neuron: a weighted sum followed by a threshold, with a simple rule that updates weights only on mistakes.

**How it works:**
1. Output = 1 if w · x + b > 0, else 0 (or ±1).
2. For each training example, compute the output.
3. If it's wrong, update: w ← w + η × (target − output) × x, and the same for b.
4. If it's right, change nothing.
5. **Convergence theorem:** if the data is linearly separable, the rule finds a separating line in a finite number of updates. If not, it never settles.

**Cost:** O(d) per example.



### 2. Multilayer perceptron (MLP) and universal approximation

**Definition:** Stacked layers of neurons with nonlinear activations between them, able to approximate any continuous function given enough width.

**How it works:**
1. **Each layer:** h = activation(W × previous + b).
2. Stack several layers. The last layer gives outputs (scores, probabilities, values).
3. Without nonlinear activations, stacked layers collapse into one linear map.
4. **Universal approximation theorem:** one hidden layer with enough units can approximate any continuous function on a bounded region. Depth makes this far more efficient for many functions.
5. Trained with backpropagation (#24) and an optimizer (#31–42).

**Cost:** O(Σ layer_in × layer_out) per example, forward and backward.

**Agent use:**
- **Role:** Architect.
- **How:** The default model for tabular or fixed-size feature data, and the building block inside every larger architecture (transformer feed-forward layers, prediction heads).
- **Rules:** Compare against gradient-boosted trees on tabular data (NR2). They often win.
- **Guardrails:** None specific.

### 3. Linear (affine) layer and fan-in / fan-out

**Definition:** The fundamental parametric operation: output = W × input + b.

**How it works:**
1. W has shape (out_features × in_features). b has one value per output.
2. **Fan-in** (number of inputs) and **fan-out** (number of outputs) determine how weights should be initialized (#47, #48).
3. In batches, it's a matrix multiplication: Y = X Wᵀ + b, which runs efficiently on GPUs.
4. Gradients: ∂L/∂W = (∂L/∂Y)ᵀ X, and ∂L/∂X = (∂L/∂Y) W.

**Cost:** O(batch × in × out) multiply-adds.

**Agent use:**
- **Role:** Architect and Deployer.
- **How:** Nearly all neural network compute is linear layers, so the agent estimates cost by summing their sizes (NR5), and targets them first for quantization and fusion (#251, #258).
- **Rules:** Keep dimensions multiples of 8, 16 or 64 for tensor-core efficiency.
- **Guardrails:** None specific.

### 4. ReLU family (ReLU, Leaky ReLU, PReLU)

**Definition:** Piecewise linear activations: ReLU(x) = max(0, x), and variants that let a small signal through for negative inputs.

**How it works:**
1. **ReLU:** passes positive inputs, zeroes negative ones. The gradient is 1 or 0. It doesn't saturate for positive inputs, which helps deep networks train.
2. **Dead ReLU problem:** a unit whose inputs are always negative gets zero gradient forever.
3. **Leaky ReLU:** max(αx, x) with a small α (0.01), so negatives keep a small gradient.
4. **PReLU:** α is learned per channel.
5. **ELU/SELU:** smooth exponential curves for negatives. SELU has self-normalizing properties with matching initialization.

**Cost:** O(1) per element.

**Agent use:**
- **Role:** Architect.
- **How:** A robust default for CNNs and MLPs. The agent monitors the fraction of dead units during training (#293).
- **Rules:** Use He initialization with ReLU-family activations (#48).
- **Guardrails:** If many units are dead, lower the learning rate or switch to Leaky ReLU or GELU.

### 5. Smooth activations (GELU, SiLU/Swish, Mish)

**Definition:** Smooth, non-monotonic activations that weight inputs by how "positive" they are. Standard in transformers.

**How it works:**
1. **GELU:** x × Φ(x), where Φ is the standard normal CDF. It approximately gates each input by the probability it's positive. A tanh-based approximation is common.
2. **SiLU (Swish):** x × σ(x), with σ the sigmoid.
3. **Mish:** x × tanh(softplus(x)).
4. Smooth gradients everywhere, slightly negative outputs for small negative inputs, and no dead units.

**Cost:** A few transcendental operations per element (still small next to matrix multiplications).

**Agent use:**
- **Role:** Architect.
- **How:** Default activations for transformers and modern CNNs, usually inside gated units (#8).
- **Rules:** Match the activation used by any pretrained model being fine-tuned. Changing it breaks the weights.
- **Guardrails:** None specific.

### 6. Sigmoid and tanh (and saturation)

**Definition:** S-shaped activations: sigmoid maps to (0, 1), tanh maps to (−1, 1).

**How it works:**
1. Sigmoid σ(x) = 1/(1 + e^(−x)). tanh(x) = 2σ(2x) − 1.
2. **Saturation:** for large |x|, the output flattens and the gradient approaches 0.
3. Stacked saturating layers multiply small gradients together, so early layers barely learn (vanishing gradients, #28).
4. Still essential where a bounded output is needed: gates in LSTMs and GRUs (#92, #93), probabilities in binary outputs, attention gates.

**Cost:** O(1) per element.

**Agent use:**
- **Role:** Architect.
- **How:** Uses them for gates and bounded outputs, not as hidden-layer activations in deep networks.
- **Rules:** Combine the final sigmoid with its loss (#15), for numerical stability.
- **Guardrails:** None specific.

### 7. Softmax with log-sum-exp stability

**Definition:** Turning a vector of scores (logits) into probabilities that sum to 1, computed in a way that avoids numerical overflow.

**How it works:**
1. softmax(z)_i = e^(z_i) / Σ_j e^(z_j).
2. **Stability:** subtract the maximum logit first (e^(z_i − max)). That doesn't change the result but prevents overflow.
3. **Log-softmax:** z_i − log Σ e^(z_j), computed with the log-sum-exp trick (subtract the max inside the log). Used directly in cross-entropy (#14).
4. **Temperature:** dividing logits by T before softmax makes the distribution sharper (T < 1) or flatter (T > 1).
5. **Online softmax:** computes the max and the sum in one streaming pass, which FlashAttention relies on (#116).

**Cost:** O(n) per vector.

**Agent use:**
- **Role:** Architect and Deployer.
- **How:** Every classifier and language model output uses it. The agent always uses fused, stable implementations.
- **Rules:** Use log-softmax plus negative log-likelihood, never log(softmax(x)) computed separately.
- **Guardrails:** Very large vocabularies make the softmax expensive. Account for it in cost estimates (NR5).

### 8. Gated linear units (GLU, SwiGLU, GeGLU)

**Definition:** Feed-forward layers where one linear projection is multiplied elementwise by an activated second projection, acting as a learned gate.

**How it works:**
1. GLU(x) = (x W₁) ⊙ σ(x W₂).
2. **SwiGLU:** (x W₁) ⊙ SiLU(x W₂). **GeGLU:** uses GELU.
3. In transformers, the feed-forward block becomes: output = (SwiGLU(x)) W₃.
4. To keep the parameter count equal to a standard feed-forward layer, the hidden size is reduced to about 2/3 of the usual 4× width.
5. Consistently improves quality per parameter in language models.

**Cost:** Three weight matrices instead of two, at a smaller hidden width.

**Agent use:**
- **Role:** Architect.
- **How:** The standard feed-forward choice in modern LLMs. The agent uses it for new transformer designs.
- **Rules:** Adjust the hidden size so comparisons are at equal parameter counts (NR2).
- **Guardrails:** None specific.

### 9. Embedding lookup layers (categorical inputs, sparse gradients)

**Definition:** A trainable table that maps each discrete ID (token, user, product, category) to a learned vector.

**How it works:**
1. A matrix E of shape (vocabulary size × dimension).
2. **Forward:** select rows by ID. Equivalent to multiplying a one-hot vector by E, but much faster.
3. **Backward:** only the selected rows get gradients (sparse gradients). Specialized optimizers or sparse updates save memory.
4. Several IDs per example (a bag of features) are combined with sum, mean or attention.
5. Huge tables (billions of rows) are sharded across devices, or hashed (#195).

**Cost:** O(dimension) per lookup. Memory O(vocabulary × dimension).

**Agent use:**
- **Role:** Architect.
- **How:** Represents categorical features and tokens. Large tables dominate memory in recommendation models, so the agent plans sharding and hashing.
- **Rules:** Reserve IDs for unknown values and padding.
- **Guardrails:** Rare IDs get few updates and poor vectors. Use frequency thresholds or shared buckets.

### 10. Residual connections

**Definition:** Adding a layer's input to its output (x + F(x)), so the network only learns changes and gradients flow directly through many layers.

**How it works:**
1. Output = x + F(x), where F is a block (convolutions, attention, feed-forward).
2. Gradients flow back through the identity path unchanged, which avoids vanishing gradients in very deep networks.
3. Blocks can learn F ≈ 0 when they aren't needed, so adding depth rarely hurts.
4. Shapes must match. Otherwise use a projection on the skip path (a 1×1 convolution or linear layer).
5. Enables networks with hundreds of layers (ResNets, #74; transformers, #112).

**Cost:** One addition per element.

**Agent use:**
- **Role:** Architect.
- **How:** Every deep architecture the agent builds uses residual paths.
- **Rules:** Combine with normalization placement chosen deliberately (#56).
- **Guardrails:** In very deep networks, scale residual branches at initialization (#49) to keep activations stable.

### 11. Dense and highway connections

**Definition:** Alternatives to residual addition: concatenating all earlier layers' outputs (DenseNet) or gating the skip path (highway networks).

**How it works:**
1. **DenseNet:** layer ℓ receives the concatenation of all previous layers' outputs in a block. Each layer adds a few new channels ("growth rate"). Features get reused heavily.
2. Transition layers (1×1 convolution plus pooling) control the growing channel count.
3. **Highway networks:** y = T(x) ⊙ H(x) + (1 − T(x)) ⊙ x, with a learned gate T. An ancestor of residual connections.
4. Concatenation keeps information explicit but increases memory use.

**Cost:** DenseNet memory grows with the concatenated feature maps (mitigated by recomputation, #27).

**Agent use:**
- **Role:** Architect.
- **How:** DenseNet-style feature reuse is useful for small-data vision tasks. Highway-style gating appears inside recurrent and some transformer variants.
- **Rules:** Prefer residual connections by default. Use dense connections when parameter efficiency matters more than memory.
- **Guardrails:** Check activation memory (NR5).

### 12. Weight tying (shared input and output embeddings)

**Definition:** Using the same matrix for the input token embeddings and the output projection to vocabulary logits.

**How it works:**
1. The input embedding E maps token IDs to vectors.
2. The output layer computes logits = hidden × Eᵀ, reusing E.
3. That halves the vocabulary-related parameters, which matters for large vocabularies in small models.
4. It also regularizes: tokens that appear similar as inputs and outputs share one representation.

**Cost:** Saves vocabulary × dimension parameters.

**Agent use:**
- **Role:** Architect.
- **How:** A standard choice for small and medium language models, where the vocabulary matrix is a large share of all parameters.
- **Rules:** Large models often untie for slightly better quality. Decide by benchmark (NR2).
- **Guardrails:** None specific.

## A2. Loss functions

### 13. Regression losses (MSE, L1, Huber)

**Definition:** Measures of prediction error for continuous targets.

**How it works:**
1. **MSE (L2):** mean of (prediction − target)². Penalizes big errors heavily; predicts the conditional mean.
2. **L1 (MAE):** mean of |prediction − target|. Robust to outliers; predicts the conditional median.
3. **Huber:** quadratic for small errors (below δ), linear for large ones. Combines smooth optimization with outlier robustness.
4. **Quantile (pinball) loss:** asymmetric L1, which predicts a chosen quantile (for example the 90th percentile).

**Cost:** O(n).

**Agent use:**
- **Role:** Architect.
- **How:** Chooses the loss by what the prediction should mean: average (MSE), typical (L1), robust (Huber), or a risk bound (quantile, such as "the latency won't exceed X 90% of the time").
- **Rules:** Normalize targets to a standard scale before training.
- **Guardrails:** MSE on heavy-tailed targets lets a few outliers dominate training. Inspect the target distribution first.

### 14. Cross-entropy and negative log-likelihood

**Definition:** The standard classification and language modeling loss: the negative log of the probability assigned to the correct class.

**How it works:**
1. Compute log-softmax of the logits (#7).
2. Loss = −log p(correct class), averaged over examples (or tokens).
3. Equivalent to minimizing the KL divergence between the true labels and the predicted distribution.
4. Gradient with respect to the logits = predicted probabilities − one-hot target. Simple and well-behaved.
5. Class weights handle imbalance (#298). An ignore index skips padding tokens.

**Cost:** O(classes) per example. Large vocabularies are often handled with fused or chunked kernels to save memory.

**Agent use:**
- **Role:** Trainer.
- **How:** The default loss for classification and next-token prediction. The per-token loss (perplexity, #288) is the key training metric.
- **Rules:** Use the fused log-softmax + NLL operation for stability.
- **Guardrails:** Large-vocabulary losses can dominate memory. Use chunked computation for long sequences.

### 15. Binary cross-entropy with logits

**Definition:** The loss for yes/no (and multi-label) predictions, computed directly from logits for numerical stability.

**How it works:**
1. For each label independently: loss = −[y log σ(z) + (1 − y) log(1 − σ(z))].
2. The "with logits" form combines the sigmoid and the log into a stable expression (log-sum-exp style), avoiding log(0).
3. **Multi-label:** apply per label. Each output is independent (an item can belong to several classes).
4. `pos_weight` rebalances rare positives.

**Cost:** O(labels).

**Agent use:**
- **Role:** Trainer.
- **How:** Multi-label tagging, binary classifiers (spam, relevance, risk), and reward models (#209).
- **Rules:** Always use the logits version, never a separate sigmoid followed by log.
- **Guardrails:** Choose thresholds on validation data, per label. 0.5 is rarely right for imbalanced labels.

### 16. Label smoothing

**Definition:** Training against slightly softened targets (for example 0.9 for the correct class, the remainder spread across others), to prevent overconfidence.

**How it works:**
1. Target distribution = (1 − ε) × one-hot + ε / K for every class.
2. Train with cross-entropy against this target.
3. The model can't push logits to infinity, which improves calibration and generalization.
4. Typical ε: 0.05–0.1.

**Cost:** None extra.

**Agent use:**
- **Role:** Trainer.
- **How:** Improves calibration and robustness for classifiers and translation models.
- **Rules:** Don't combine with knowledge distillation targets without care: they already soften the labels (#225).
- **Guardrails:** Smoothing can hurt tasks where the model's confidence values are used directly. Recalibrate if so.

### 17. Focal loss

**Definition:** Cross-entropy that down-weights easy, well-classified examples, so training focuses on hard ones.

**How it works:**
1. Focal loss = −α (1 − p_t)^γ log(p_t), where p_t is the probability of the true class.
2. For confident correct predictions (p_t near 1), the factor (1 − p_t)^γ shrinks the loss to almost nothing.
3. γ (often 2) controls the focusing. α balances the classes.
4. Designed for dense object detection, where background examples vastly outnumber objects (#85).

**Cost:** None extra.

**Agent use:**
- **Role:** Trainer.
- **How:** Heavily imbalanced detection and classification (rare defects, rare fraud, rare events).
- **Rules:** Compare against class reweighting and logit adjustment (#298). Simpler methods may suffice.
- **Guardrails:** Changes calibration. Recalibrate before using scores as probabilities.

### 18. Triplet and angular-margin metric learning losses

**Definition:** Losses that train an embedding space so same-identity items are close and different items are far, by a margin.

**How it works:**
1. **Triplet loss:** for (anchor, positive, negative), loss = max(0, d(a, p) − d(a, n) + margin).
2. **Mining** (semi-hard negatives: farther than the positive but within the margin) is essential, since most random triplets are already satisfied.
3. **Angular margin losses (ArcFace, CosFace):** normalize embeddings and class weight vectors, then add a margin to the angle (or cosine) of the true class inside a softmax. More stable than triplet training at scale.
4. Output: embeddings compared with cosine similarity.

**Cost:** Triplet mining can be expensive. Angular-margin losses cost about the same as a softmax.

**Agent use:**
- **Role:** Trainer.
- **How:** Identity and verification tasks: face, voice, document or product matching, where new identities appear after training.
- **Rules:** Evaluate with verification metrics (true accept rate at a fixed false accept rate).
- **Guardrails:** Biometric identification is high-risk. It needs legal and ethical review (NX3, NR8).

### 19. KL divergence loss

**Definition:** A loss measuring how one probability distribution differs from another, used to match a model's output distribution to a target distribution.

**How it works:**
1. KL(P ‖ Q) = Σ P(x) log(P(x)/Q(x)). It's asymmetric: KL(P ‖ Q) ≠ KL(Q ‖ P).
2. **Forward KL** (target P, model Q): Q must cover everywhere P has probability (mode-covering).
3. **Reverse KL:** Q concentrates on one high-probability region of P (mode-seeking).
4. Used in distillation (#225), VAEs (#152), RLHF regularization (#210), and policy constraints.
5. Compute in log space for stability.

**Cost:** O(classes).

**Agent use:**
- **Role:** Trainer.
- **How:** Keeping a fine-tuned model close to its reference (preventing drift), and transferring knowledge from teacher models.
- **Rules:** Choose forward or reverse KL deliberately, by the behavior you want.
- **Guardrails:** None specific.

### 20. CTC loss (connectionist temporal classification)

**Definition:** A loss for aligning a long input sequence (audio frames, image columns) to a shorter label sequence when the exact alignment is unknown.

**How it works:**
1. Add a "blank" symbol. The model outputs a distribution over labels + blank at every input frame.
2. Any frame-level path collapses to a label sequence by merging repeats and removing blanks.
3. The loss = −log of the sum of probabilities over all paths that collapse to the correct label sequence.
4. That sum is computed efficiently with forward-backward dynamic programming.
5. Decode with greedy collapse or beam search, optionally with a language model.

**Cost:** O(T × L) per sequence, for T frames and L labels.

**Agent use:**
- **Role:** Trainer.
- **How:** Speech recognition, handwriting and OCR, and any sequence task without frame-level labels.
- **Rules:** The input must be long enough: T ≥ label length + repeats.
- **Guardrails:** None specific.

### 21. Overlap losses for segmentation (Dice, IoU/Jaccard)

**Definition:** Losses that directly optimize the overlap between predicted and true regions, good for small structures.

**How it works:**
1. **Soft Dice:** 1 − 2 × Σ(p × g) / (Σp + Σg), using predicted probabilities p and ground truth g.
2. **Soft IoU (Jaccard):** 1 − Σ(p × g) / (Σp + Σg − Σ(p × g)). Lovász-softmax optimizes IoU more directly.
3. Insensitive to the large background, so small objects matter.
4. Often combined with cross-entropy for stable gradients.

**Cost:** O(pixels).

**Agent use:**
- **Role:** Trainer.
- **How:** Segmentation of small regions (defects in images, regions in documents, medical structures).
- **Rules:** Combine with cross-entropy, and report IoU per class.
- **Guardrails:** Medical uses require clinical validation (NX3).

### 22. Multi-task loss weighting (uncertainty weighting, GradNorm)

**Definition:** Balancing several losses trained together, so no single task dominates.

**How it works:**
1. Total loss = Σ w_i × L_i. Fixed weights are hard to tune because loss scales differ.
2. **Uncertainty weighting:** learn a variance σ_i per task; the loss becomes Σ (L_i / (2σ_i²) + log σ_i). Noisy tasks automatically get less weight.
3. **GradNorm:** adjust the weights so each task's gradient norm on shared layers grows at a similar rate.
4. **PCGrad:** when task gradients conflict (negative cosine), project each onto the normal plane of the other.

**Cost:** Small overhead (extra gradient norms for GradNorm or PCGrad).

**Agent use:**
- **Role:** Trainer.
- **How:** Training one model for several outputs (classification + regression, several labels, auxiliary losses) without hand-tuning weights.
- **Rules:** Monitor each task's validation metric separately.
- **Guardrails:** Watch for one task silently degrading while the total loss improves.

## A3. Backpropagation and automatic differentiation

### 23. Computational graphs and reverse-mode automatic differentiation

**Definition:** Recording the operations of a computation as a graph, then computing gradients of a scalar output with respect to all inputs in one backward pass.

**How it works:**
1. **Forward pass:** execute operations and record each one (inputs, outputs, saved values) in a graph or "tape".
2. **Backward pass:** start from the output with gradient 1. Visit operations in reverse topological order.
3. Each operation applies its vector-Jacobian product: it turns the gradient of its output into gradients of its inputs.
4. Gradients from several paths into the same variable are summed.
5. Cost: about 2–3× the forward pass, regardless of the number of parameters.

**Cost:** Time about 2–3× forward. Memory for saved activations (#27 reduces it).

**Agent use:**
- **Role:** Trainer and Analyst.
- **How:** Underlies all training. The agent also uses it for sensitivity analysis: gradients of outputs with respect to inputs (#271).
- **Rules:** Make sure no part of the graph accidentally stops gradients (detach misuse), or blocks silently don't train.
- **Guardrails:** Check that parameters actually change during training (#294).

### 24. Backpropagation through layers

**Definition:** The chain rule applied layer by layer, to compute every weight's gradient in a neural network.

**How it works:**
1. For layer h = f(W x): given ∂L/∂h, compute ∂L/∂W = (∂L/∂h ⊙ f′) × xᵀ, and ∂L/∂x = Wᵀ (∂L/∂h ⊙ f′).
2. Start at the loss and repeat backward through every layer.
3. Activation derivatives (f′) and saved inputs (x) come from the forward pass.
4. Each layer passes the gradient on to the layer before it.

**Cost:** About one matrix multiplication per layer for each of the two gradients.

**Agent use:**
- **Role:** Analyst.
- **How:** Understanding backpropagation explains vanishing and exploding gradients (#28), the effect of initialization (#47–50) and the memory cost of training.
- **Rules:** When writing custom layers, verify gradients numerically (#26).
- **Guardrails:** None specific.

### 25. Forward-mode differentiation (Jacobian-vector products)

**Definition:** Computing how outputs change for a given input direction, carried along with the forward pass.

**How it works:**
1. Each value carries its derivative along a chosen direction v (dual numbers).
2. Each operation computes its output and its directional derivative together.
3. The result is J × v (a Jacobian-vector product) in about one extra forward pass.
4. Efficient when there are few inputs and many outputs. Reverse mode wins for many inputs and one output (training).
5. Combined forward and reverse modes give Hessian-vector products cheaply (#40).

**Cost:** About one forward pass per direction.

**Agent use:**
- **Role:** Analyst.
- **How:** Sensitivity of many outputs to one input knob, curvature estimates (Hessian-vector products) and some meta-learning methods.
- **Rules:** Pick the mode by the input/output shape of the problem.
- **Guardrails:** None specific.

### 26. Gradient checking (finite differences)

**Definition:** Verifying analytic gradients by comparing them with numerical estimates from small input perturbations.

**How it works:**
1. For a parameter θ, estimate the gradient as (L(θ + ε) − L(θ − ε)) / (2ε).
2. Compare with the analytic gradient using relative error: |a − n| / max(|a|, |n|).
3. A relative error of about 10⁻⁷ is good (in double precision); 10⁻² means a bug.
4. Check a random sample of parameters, in double precision, with dropout and other randomness disabled.

**Cost:** Two forward passes per checked parameter.

**Agent use:**
- **Role:** Analyst.
- **How:** Validates custom layers, custom losses and custom kernels before trusting them for training.
- **Rules:** Run gradient checks in CI for every custom differentiable component.
- **Guardrails:** Non-smooth points (ReLU at 0) give spurious mismatches. Avoid them in tests.

### 27. Gradient checkpointing (activation recomputation)

**Definition:** Saving memory during training by storing only some activations, and recomputing the others during the backward pass.

**How it works:**
1. Normally, every layer's activations are stored for the backward pass. Memory grows with depth × batch × sequence length.
2. **Checkpointing:** store activations only at selected layers (checkpoints).
3. During the backward pass, recompute the activations of each segment from its checkpoint, just before they're needed.
4. With √L checkpoints in L layers, memory drops to O(√L) at about one extra forward pass of compute.
5. **Selective checkpointing:** recompute only cheap operations (activations, normalizations), and keep expensive ones (attention outputs).

**Cost:** About 30% more compute for large memory savings.

**Agent use:**
- **Role:** Trainer.
- **How:** Lets the agent train larger models or longer sequences on the same hardware.
- **Rules:** Profile memory first, and checkpoint only as much as needed.
- **Guardrails:** Recomputation with randomness (dropout) must reuse the same random seeds, or gradients are wrong.

### 28. Vanishing and exploding gradients, and gradient clipping

**Definition:** The problem of gradients shrinking to nothing or growing without bound through many layers, and the standard fix for the explosion side.

**How it works:**
1. Backpropagation multiplies many layer Jacobians. If their typical scale is below 1, gradients vanish; above 1, they explode.
2. **Causes:** saturating activations, poor initialization, long recurrent chains.
3. **Fixes for vanishing:** ReLU-family activations, residual connections (#10), normalization (#51–56), good initialization (#47–50), LSTM gates (#92).
4. **Gradient clipping by global norm:** if the norm of all gradients exceeds a threshold, scale them all down to it. Preserves direction.
5. **Clipping by value:** cap each element (cruder, and changes direction).

**Cost:** One norm computation per step.

**Agent use:**
- **Role:** Trainer.
- **How:** Clipping by global norm (often 1.0) is standard in transformer and RNN training. The agent logs the gradient norm every step (NR4).
- **Rules:** Track how often clipping activates. Frequent clipping means an instability to investigate.
- **Guardrails:** Clipping hides problems rather than fixing them. Investigate spikes (#242).

### 29. Straight-through estimator (STE)

**Definition:** A trick for training through non-differentiable operations (rounding, thresholding, sampling discrete values): use the real operation forward, and pretend it's the identity (or a smooth surrogate) backward.

**How it works:**
1. **Forward:** apply the discrete operation, for example round(x) or sign(x).
2. **Backward:** pass the gradient through unchanged, as if the operation were the identity (optionally zeroed outside a range).
3. The gradient is biased, but works well in practice.
4. Used in quantization-aware training (#255), binary networks and VQ-VAE codebooks (#153).

**Cost:** None extra.

**Agent use:**
- **Role:** Trainer.
- **How:** Enables training models that are later deployed with discrete operations (low-bit weights, discrete codes).
- **Rules:** Validate on the true discrete model, not the training-time approximation.
- **Guardrails:** None specific.

### 30. Reparameterization trick and Gumbel-softmax

**Definition:** Ways to backpropagate through random sampling, by expressing samples as a deterministic function of parameters plus independent noise.

**How it works:**
1. **Continuous (Gaussian):** instead of sampling z ~ N(μ, σ²), sample ε ~ N(0, 1) and compute z = μ + σ × ε. Gradients flow to μ and σ.
2. **Discrete (Gumbel-softmax):** add Gumbel noise to the logits and take a softmax with temperature τ: a "soft" one-hot sample that's differentiable.
3. As τ → 0, samples become nearly one-hot. Anneal τ during training.
4. **Straight-through Gumbel:** a hard one-hot forward, with soft gradients backward (#29).

**Cost:** None extra beyond sampling.

**Agent use:**
- **Role:** Trainer.
- **How:** Training VAEs (#152), learning discrete choices (routing, architecture search, #186), and stochastic layers.
- **Rules:** Anneal temperatures on a schedule, and log the schedule (NR1).
- **Guardrails:** None specific.

## A4. Optimizers

### 31. Stochastic gradient descent (SGD)

**Definition:** Updating weights in the direction opposite to the gradient of the loss on a small random batch.

**How it works:**
1. Sample a mini-batch.
2. Compute the gradient g of the loss on it.
3. Update: θ ← θ − η × g (η = learning rate).
4. The noise from mini-batches helps escape poor regions and often generalizes better than exact gradients.
5. Repeat for many steps, usually with a learning rate schedule (#43–46).

**Cost:** One forward and backward per step. No extra memory.

**Agent use:**
- **Role:** Trainer.
- **How:** With momentum (#32), still a strong choice for CNNs on vision. Its zero optimizer memory matters when memory is tight.
- **Rules:** Tune the learning rate first. It's the most important hyperparameter.
- **Guardrails:** None specific.

### 32. Momentum and Nesterov momentum

**Definition:** Accumulating a running average of past gradients, to accelerate along consistent directions and dampen oscillation.

**How it works:**
1. Velocity: v ← β v + g (β ≈ 0.9).
2. Update: θ ← θ − η v.
3. Consistent gradient directions build up speed; oscillating directions cancel out.
4. **Nesterov:** compute the gradient at the "look-ahead" position θ − ηβv, which gives a corrective effect and often slightly better convergence.

**Cost:** One extra buffer the size of the parameters.

**Agent use:**
- **Role:** Trainer.
- **How:** The standard SGD variant for vision models.
- **Rules:** When changing β, retune the learning rate (the effective step is about η / (1 − β)).
- **Guardrails:** None specific.

### 33. AdaGrad

**Definition:** Per-parameter learning rates scaled by the inverse square root of the accumulated squared gradients.

**How it works:**
1. Accumulate G ← G + g² (elementwise).
2. Update: θ ← θ − η × g / (√G + ε).
3. Parameters with rare, large gradients get relatively larger steps; frequently updated ones get smaller steps.
4. G only grows, so learning rates keep shrinking, which can stop training too early.

**Cost:** One extra buffer.

**Agent use:**
- **Role:** Trainer.
- **How:** Useful for sparse features (large embedding tables with rare IDs).
- **Rules:** For long training, use RMSProp or Adam instead.
- **Guardrails:** None specific.

### 34. RMSProp

**Definition:** AdaGrad with an exponential moving average of squared gradients instead of a sum, so learning rates don't decay to zero.

**How it works:**
1. s ← ρ s + (1 − ρ) g² (ρ ≈ 0.9–0.99).
2. Update: θ ← θ − η × g / (√s + ε).
3. Adapts to recent gradient scales.
4. Often combined with momentum.

**Cost:** One extra buffer.

**Agent use:**
- **Role:** Trainer.
- **How:** Historically used for recurrent networks and reinforcement learning. Adam (#35) is the usual modern default.
- **Rules:** Tune ε when gradients are tiny (it sets a floor on the step denominator).
- **Guardrails:** None specific.

### 35. Adam

**Definition:** Combining momentum (first moment) with RMSProp-style scaling (second moment), with bias correction for early steps.

**How it works:**
1. m ← β₁ m + (1 − β₁) g (mean of gradients).
2. v ← β₂ v + (1 − β₂) g² (mean of squared gradients).
3. **Bias correction:** m̂ = m / (1 − β₁ᵗ), v̂ = v / (1 − β₂ᵗ), since both start at zero.
4. Update: θ ← θ − η × m̂ / (√v̂ + ε).
5. Typical values: β₁ = 0.9, β₂ = 0.999 (0.95 for large transformers), ε = 10⁻⁸.

**Cost:** Two extra buffers: optimizer state is 2× the parameters (in FP32 for mixed-precision training).

**Agent use:**
- **Role:** Trainer.
- **How:** A robust default for most neural networks.
- **Rules:** Use AdamW (#36) when regularizing with weight decay.
- **Guardrails:** Optimizer state memory is large. Include it in memory planning (NR5, #234).

### 36. AdamW (decoupled weight decay)

**Definition:** Adam with weight decay applied directly to the weights, instead of being added to the gradient, which makes regularization work as intended.

**How it works:**
1. In plain Adam, an L2 term added to the gradient gets divided by √v̂, so parameters with large gradients get almost no decay.
2. **AdamW:** apply the Adam update, then separately θ ← θ − η × λ × θ.
3. The decay is the same for every parameter, independent of gradient history.
4. Commonly, biases and normalization weights are excluded from decay.

**Cost:** Same as Adam.

**Agent use:**
- **Role:** Trainer.
- **How:** The standard optimizer for transformers and most modern models.
- **Rules:** Exclude biases, normalization parameters and often embeddings from weight decay. Typical λ: 0.01–0.1.
- **Guardrails:** None specific.

### 37. LARS and LAMB (layer-wise adaptive rates for large batches)

**Definition:** Optimizers that scale each layer's update by the ratio of the layer's weight norm to its update norm, enabling very large batch sizes.

**How it works:**
1. Compute the usual update for a layer (SGD momentum for LARS; Adam for LAMB).
2. **Trust ratio** = ‖weights‖ / ‖update‖ for that layer.
3. Scale the layer's step by the trust ratio, so each layer moves by a consistent relative amount.
4. Prevents some layers diverging when the global learning rate is large.

**Cost:** One norm per layer per step.

**Agent use:**
- **Role:** Trainer.
- **How:** Very large batch training (thousands to tens of thousands of examples per step) to use many accelerators efficiently.
- **Rules:** Use warmup (#43). Large batches still have a critical-size limit (#244).
- **Guardrails:** Check final quality against small-batch baselines (NR2).

### 38. Adafactor (factored second moments)

**Definition:** An Adam-like optimizer that stores the second-moment statistics of each weight matrix as row and column averages, cutting optimizer memory drastically.

**How it works:**
1. For an (m × n) matrix, keep a row vector R (size m) and a column vector C (size n) of averaged squared gradients, instead of m × n values.
2. Approximate the full second moment as R × C / sum(R) (a rank-1 approximation).
3. Optionally drop the first moment (momentum) entirely.
4. Relative step sizes and update clipping help stability.

**Cost:** O(m + n) memory per matrix instead of O(m × n).

**Agent use:**
- **Role:** Trainer.
- **How:** Training large models when optimizer memory is the bottleneck.
- **Rules:** Compare stability with AdamW on a small run first (NR2).
- **Guardrails:** It can be less stable without momentum. Monitor loss spikes (#242).

### 39. Lion and sign-based optimizers

**Definition:** Optimizers that use only the sign of a momentum-based update, so every parameter moves by the same magnitude.

**How it works:**
1. update = sign(β₁ m + (1 − β₁) g).
2. θ ← θ − η × (update + λ θ).
3. m ← β₂ m + (1 − β₂) g.
4. Only one state buffer (momentum), half of Adam's.
5. Needs a smaller learning rate than AdamW (often 3–10× smaller), with larger weight decay.

**Cost:** One state buffer.

**Agent use:**
- **Role:** Trainer.
- **How:** A memory-saving alternative to AdamW, sometimes with equal or better results.
- **Rules:** Retune the learning rate and weight decay. Don't reuse AdamW settings.
- **Guardrails:** Benchmark before switching production training (NR2).

### 40. Second-order preconditioning (Shampoo, K-FAC)

**Definition:** Optimizers that use curvature information (approximations of the Hessian or Fisher matrix) to precondition gradients, so steps are better scaled across directions.

**How it works:**
1. **K-FAC:** approximate each layer's Fisher information as the Kronecker product of two small matrices (input activation covariance and output gradient covariance). Invert those small matrices to precondition the gradient.
2. **Shampoo:** keep left and right preconditioner matrices per weight matrix (L = Σ G Gᵀ, R = Σ Gᵀ G). Update = L^(−1/4) G R^(−1/4).
3. Matrix roots and inverses are computed only every N steps, often on separate hardware.
4. Distributed Shampoo has been competitive with or better than AdamW in large-scale benchmarks.

**Cost:** Extra memory and periodic expensive matrix operations.

**Agent use:**
- **Role:** Trainer.
- **How:** Faster convergence (fewer steps to target quality) for large training runs where step count dominates cost.
- **Rules:** Use mature distributed implementations. Grafting (copying Adam's step size per layer) improves stability.
- **Guardrails:** Numerical issues in matrix roots. Use regularization (ε added to the diagonal) and monitoring.

### 41. Sharpness-aware minimization (SAM)

**Definition:** An optimizer that seeks flat regions of the loss (where nearby weights also have low loss), which tends to generalize better.

**How it works:**
1. Compute the gradient g at the current weights.
2. Move to the "worst" nearby point: ε = ρ × g / ‖g‖.
3. Compute the gradient at θ + ε.
4. Update the original weights θ with that second gradient.
5. ρ controls the neighborhood size.

**Cost:** Two forward and backward passes per step (2× compute).

**Agent use:**
- **Role:** Trainer.
- **How:** Improves generalization and robustness to label noise, especially for vision models trained from scratch.
- **Rules:** Use when generalization matters more than training cost.
- **Guardrails:** Doubles compute (NR5).

### 42. Lookahead and weight averaging (EMA / Polyak averaging)

**Definition:** Keeping a smoothed version of the weights, either by periodically pulling "slow" weights toward "fast" ones (Lookahead) or with an exponential moving average.

**How it works:**
1. **EMA:** θ_EMA ← α θ_EMA + (1 − α) θ after every step (α ≈ 0.999–0.9999). Evaluate and deploy the EMA weights.
2. **Lookahead:** an inner optimizer takes k fast steps, then the slow weights move a fraction of the way toward the fast weights, and the fast weights reset to the slow ones.
3. Both reduce noise from the last steps and often improve final quality.
4. EMA is standard for diffusion models and self-distillation (#175).

**Cost:** One extra copy of the weights.

**Agent use:**
- **Role:** Trainer.
- **How:** A cheap, reliable improvement: the agent keeps EMA weights and evaluates both versions.
- **Rules:** Store EMA weights with checkpoints (NR1).
- **Guardrails:** EMA lags during fast changes. Evaluate it before trusting it.

## A5. Schedules and initialization

### 43. Learning rate warmup

**Definition:** Starting training with a small learning rate and increasing it gradually over the first steps.

**How it works:**
1. Increase the learning rate linearly from about 0 to the target over N warmup steps (often 1–5% of training).
2. Early in training, adaptive optimizer statistics (Adam's v) are unreliable and gradients are large. Small steps prevent divergence.
3. Especially important with large batches, large learning rates, and transformers with post-norm placement (#56).

**Cost:** None.

**Agent use:**
- **Role:** Trainer.
- **How:** Default for every transformer or large-batch run.
- **Rules:** Record the warmup length in the config (NR1).
- **Guardrails:** If training diverges early, lengthen the warmup before changing anything else.

### 44. Cosine decay and warm restarts

**Definition:** Lowering the learning rate along a half cosine curve, optionally restarting it periodically.

**How it works:**
1. η(t) = η_min + ½ (η_max − η_min) (1 + cos(π t / T)).
2. Slow decrease at first, faster in the middle, gentle at the end.
3. **Warm restarts (SGDR):** reset to η_max at intervals (often growing longer), which explores new regions. Snapshots at the end of each cycle can be ensembled.
4. Requires knowing the total number of steps T in advance.

**Cost:** None.

**Agent use:**
- **Role:** Trainer.
- **How:** A strong default schedule for fixed-length training runs.
- **Rules:** Use WSD (#45) if the total length might change.
- **Guardrails:** None specific.

### 45. Warmup-stable-decay (WSD), linear decay and one-cycle schedules

**Definition:** Schedules that keep the learning rate high for most of training and decay it at the end, or (one-cycle) ramp up then down within one run.

**How it works:**
1. **WSD:** warmup → a long constant phase → a short decay phase (often 10–20% of steps).
2. Any checkpoint from the stable phase can be "cooled down" with a short decay to get a strong model, so training can be extended without restarting.
3. **Linear decay to zero:** simple and effective for fine-tuning.
4. **One-cycle:** increase the learning rate to a maximum, then decrease below the starting value, with momentum moving in the opposite direction.

**Cost:** None.

**Agent use:**
- **Role:** Trainer.
- **How:** WSD is ideal when the training budget isn't fixed: continue training, then decay when needed. Useful for scaling studies (#138).
- **Rules:** Save checkpoints from the stable phase for branching.
- **Guardrails:** None specific.

### 46. Batch size and learning rate scaling rules

**Definition:** Rules for adjusting the learning rate when changing the batch size, so training behaves similarly.

**How it works:**
1. **Linear scaling (SGD):** multiply the batch size by k, multiply the learning rate by k (with warmup). Works up to a limit.
2. **Square-root scaling (Adam-like optimizers):** multiply the learning rate by √k.
3. Beyond the critical batch size (#244), larger batches give diminishing returns: more compute without fewer steps.
4. **Learning rate range test:** increase the learning rate exponentially during a short run and pick a value just below where the loss starts rising.

**Cost:** None, or one short calibration run.

**Agent use:**
- **Role:** Trainer.
- **How:** Moving runs between hardware sizes (8 to 256 GPUs) without retuning from scratch.
- **Rules:** Re-validate after any batch size change (NR2).
- **Guardrails:** Rules are approximate. Verify with short runs.

### 47. Xavier (Glorot) initialization

**Definition:** Setting initial weights with variance 2 / (fan_in + fan_out), so signal variance stays roughly constant forward and backward for tanh or sigmoid networks.

**How it works:**
1. Sample weights uniformly in ±√(6 / (fan_in + fan_out)), or normally with variance 2 / (fan_in + fan_out).
2. Keeps activations and gradients from shrinking or exploding at the start of training.
3. Derived assuming symmetric, roughly linear activations near zero.

**Cost:** None.

**Agent use:**
- **Role:** Architect.
- **How:** Initialization for tanh, sigmoid and linear layers (attention projections in many implementations).
- **Rules:** Use He initialization (#48) for ReLU-family layers.
- **Guardrails:** None specific.

### 48. He (Kaiming) initialization

**Definition:** Initial weights with variance 2 / fan_in, compensating for ReLU zeroing half the activations.

**How it works:**
1. Sample from a normal distribution with variance 2 / fan_in (or uniform in ±√(6 / fan_in)).
2. The factor 2 offsets the variance lost by ReLU.
3. Keeps activation variance stable through deep ReLU networks.
4. "fan_out" mode instead stabilizes backward gradients.

**Cost:** None.

**Agent use:**
- **Role:** Architect.
- **How:** The default initialization for ReLU CNNs and MLPs.
- **Rules:** Match the initialization to the activation function.
- **Guardrails:** None specific.

### 49. Initialization for deep residual networks (scaled residual init, Fixup, zero-init)

**Definition:** Initialization rules that keep very deep residual networks stable by making each residual branch start small.

**How it works:**
1. With many residual blocks, outputs add up and variance grows with depth.
2. **Scaled initialization:** scale each residual branch's output layer by 1/√(2 × number of layers) (as in GPT-2).
3. **Zero-init:** initialize the last layer (or normalization gain) of each residual branch to zero, so each block starts as the identity.
4. **Fixup:** rescale branch weights by a depth-dependent factor, enabling training without normalization.

**Cost:** None.

**Agent use:**
- **Role:** Architect.
- **How:** Stable training of deep transformers and ResNets, with fewer early loss spikes.
- **Rules:** Use the scaling scheme that matches the architecture's reference implementation.
- **Guardrails:** None specific.

### 50. Maximal update parametrization (μP) and hyperparameter transfer

**Definition:** A way of scaling initialization and per-layer learning rates with model width, so the best hyperparameters found on a small model transfer directly to a large one.

**How it works:**
1. Standard parametrization: optimal learning rates shift as width grows, so every size needs retuning.
2. **μP:** scale initializations and learning rates per layer type by width (hidden layers' learning rates scale as 1/width for Adam; the output layer is scaled down), so each layer's update size stays stable as width grows.
3. Tune hyperparameters on a narrow proxy model.
4. Transfer them to the wide model unchanged ("μTransfer").
5. Extensions handle depth scaling as well.

**Cost:** None at runtime. Saves most of the hyperparameter tuning cost at scale.

**Agent use:**
- **Role:** Trainer and Architect.
- **How:** Tuning large training runs cheaply: sweep on small models, transfer to the big one, which greatly reduces the compute risk of large runs (NR5).
- **Rules:** Verify transfer with a medium-size checkpoint before the full run.
- **Guardrails:** Transfer only works when the parametrization is implemented exactly. Test it with width sweeps.

---

Part 2 (#51–100) covers normalization (BatchNorm, LayerNorm, RMSNorm, GroupNorm, weight and spectral normalization, norm placement, QK-norm), regularization (dropout, stochastic depth, data augmentation, Mixup and CutMix, adversarial training, consistency regularization), convolutional networks (fast convolution algorithms, dilated, depthwise separable and transposed convolutions, ResNet, Inception, MobileNet, squeeze-and-excitation, EfficientNet scaling, U-Net, feature pyramids, ConvNeXt, deformable convolution), object detection (region proposals, single-stage detectors, non-maximum suppression, DETR, RoIAlign, anchor-free detectors) and recurrent sequence models (BPTT, LSTM, GRU, seq2seq, attention, teacher forcing, beam search, pointer networks, temporal convolutional networks).