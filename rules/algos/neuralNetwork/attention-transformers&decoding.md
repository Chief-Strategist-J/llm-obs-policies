# Part 3: Attention, transformers and decoding (#101–150)

Same format and the same contract (roles; rules NR1–NR8; guardrails NX1–NX5).

## C1. Attention and training objectives

### 101. Scaled dot-product attention

**Definition:** Each position builds its output as a weighted mix of all positions' values, with weights from how well its query matches their keys.

**How it works:**
1. Project inputs into queries Q, keys K and values V (three linear layers).
2. Scores = Q Kᵀ / √d_k. The division by √d_k keeps the scores from growing with dimension, which would make the softmax too peaked.
3. Add a mask: −∞ at positions that must not be attended (future tokens, padding).
4. Weights = softmax(scores) per query (#7).
5. Output = weights × V.

**Cost:** O(n² × d) time and O(n²) memory for the score matrix (reduced by #116).

**Agent use:**
- **Role:** Architect and Deployer.
- **How:** The core operation of transformers. Its quadratic cost in sequence length drives context-length decisions and serving costs (NR5).
- **Rules:** Always use fused, memory-efficient kernels (#116).
- **Guardrails:** Masks must be correct. A padding or causal mask error leaks information silently (test it).

### 102. Multi-head attention

**Definition:** Running several attention operations in parallel on lower-dimensional projections, then combining them, so different heads can track different relationships.

**How it works:**
1. Split the model dimension d into h heads of size d/h.
2. Each head has its own Q, K and V projections and computes attention independently (#101).
3. Concatenate the head outputs.
4. Apply an output projection W_O.
5. Total cost is similar to one full-width attention.

**Cost:** About the same as single-head attention of full width.

**Agent use:**
- **Role:** Architect.
- **How:** Standard in every transformer. Head count interacts with KV-cache size (#114) and with tensor parallelism (#235): heads must divide evenly across devices.
- **Rules:** Choose head dimensions supported by fast kernels (64 or 128 are common).
- **Guardrails:** None specific.

### 103. Causal language modeling (next-token prediction)

**Definition:** Training a model to predict each token from the tokens before it, using a causal mask.

**How it works:**
1. Input: a token sequence. Target: the same sequence shifted by one position.
2. The causal mask prevents each position from attending to later positions.
3. Loss: cross-entropy (#14) averaged over every position, so one sequence trains on all its positions at once.
4. At inference, generate one token at a time, appending each to the input (with a KV cache, #117).

**Cost:** One forward and backward over the sequence per training example.

**Agent use:**
- **Role:** Trainer.
- **How:** The pretraining objective of decoder-only LLMs, and the objective for domain-adaptive continued pretraining.
- **Rules:** Mask out padding, and optionally prompt tokens, in fine-tuning losses (#208).
- **Guardrails:** Check for data contamination between training and evaluation sets (#289).

### 104. Masked language modeling (MLM)

**Definition:** Training a bidirectional encoder by hiding some input tokens and predicting them from both sides of context.

**How it works:**
1. Select about 15% of tokens.
2. Of those: replace 80% with a [MASK] token, 10% with a random token, keep 10% unchanged (so the model can't rely on seeing [MASK]).
3. The encoder attends bidirectionally (no causal mask).
4. Loss: cross-entropy only at the selected positions.
5. Variants: whole-word masking, span masking, and ELECTRA's replaced-token detection (a small generator replaces tokens; the main model classifies every token as original or replaced, which trains on all positions).

**Cost:** One forward and backward per sequence. Only selected positions give loss (ELECTRA uses all).

**Agent use:**
- **Role:** Trainer.
- **How:** Pretraining encoders for classification, extraction and embedding models.
- **Rules:** Use encoder models for understanding tasks where generation isn't needed: they're often smaller and faster.
- **Guardrails:** None specific.

### 105. Span corruption (denoising objectives, T5)

**Definition:** Pretraining an encoder-decoder by replacing random spans of text with sentinel tokens and training the decoder to output the missing spans.

**How it works:**
1. Randomly select spans (average length about 3 tokens, about 15% of tokens in total).
2. Replace each span with a unique sentinel token in the encoder input.
3. The decoder target: each sentinel followed by the tokens it replaced.
4. Shorter targets than reconstructing the whole input, so training is efficient.
5. Every task is then framed as text-to-text.

**Cost:** Encoder over the full input, decoder over the short targets.

**Agent use:**
- **Role:** Trainer.
- **How:** Pretraining encoder-decoder models for transformation tasks (summarization, extraction into structured output).
- **Rules:** None specific.
- **Guardrails:** None specific.

## C2. Position information

### 106. Sinusoidal positional encoding

**Definition:** Adding fixed sine and cosine waves of different frequencies to token embeddings, so the model knows each token's position.

**How it works:**
1. For position p and dimension pair i: PE(p, 2i) = sin(p / 10000^(2i/d)), PE(p, 2i+1) = cos(p / 10000^(2i/d)).
2. Low dimensions change quickly with position, high dimensions slowly: a multi-scale clock.
3. Add the encoding to the token embedding.
4. Relative offsets correspond to fixed linear transformations, which the model can learn to use.
5. No parameters, and defined for any length (though extrapolation beyond training length is poor in practice).

**Cost:** None (precomputable).

**Agent use:**
- **Role:** Architect.
- **How:** Mostly historical in LLMs (replaced by RoPE), but still used in diffusion timestep embeddings (#161) and some encoders.
- **Rules:** None specific.
- **Guardrails:** None specific.

### 107. Learned absolute position embeddings

**Definition:** A trainable vector for each position index, added to the token embeddings.

**How it works:**
1. A table of shape (maximum length × dimension).
2. Add the row for each position to the token's embedding.
3. Trained with the rest of the model.
4. Can't represent positions beyond the table size.

**Cost:** Maximum length × dimension parameters.

**Agent use:**
- **Role:** Architect.
- **How:** Used in BERT-style encoders and vision transformers (patch positions, #128).
- **Rules:** For longer inputs than trained on, interpolate the table (and fine-tune).
- **Guardrails:** Inputs longer than the table fail or degrade. Enforce the maximum length.

### 108. Rotary position embeddings (RoPE)

**Definition:** Encoding positions by rotating query and key vectors by angles proportional to their position, so attention scores depend on relative distance.

**How it works:**
1. Split each query and key vector into pairs of dimensions.
2. Rotate each pair by angle p × θ_i, where p is the position and θ_i is a per-pair frequency (as in sinusoidal encodings).
3. The dot product of a rotated query (position p) and key (position q) depends only on p − q: relative position is built in.
4. Applied to queries and keys only, not values, inside every attention layer.
5. No extra parameters.

**Cost:** Negligible.

**Agent use:**
- **Role:** Architect.
- **How:** The standard position method in modern LLMs. Context extension methods (#111) work by adjusting its frequencies.
- **Rules:** Keep the RoPE base (θ) and scaling identical between training and inference.
- **Guardrails:** Mismatched RoPE settings between training and serving silently degrade quality. Check the serving config.

### 109. ALiBi (attention with linear biases)

**Definition:** Adding a penalty to attention scores that grows linearly with distance, instead of adding position embeddings.

**How it works:**
1. For head h, add −m_h × |i − j| to the score between query i and key j.
2. Each head gets a different slope m_h (a geometric sequence), so some heads focus locally and some look further.
3. No position embeddings at all.
4. Extrapolates to longer sequences than seen in training better than many alternatives.

**Cost:** Negligible.

**Agent use:**
- **Role:** Architect.
- **How:** Used when length extrapolation without fine-tuning matters.
- **Rules:** Check kernel support for the bias (#116).
- **Guardrails:** Strong recency bias can hurt tasks needing distant information. Evaluate long-range retrieval (#111).

### 110. Relative position bias (T5 buckets, Transformer-XL)

**Definition:** Learned attention biases that depend on the relative distance between query and key positions.

**How it works:**
1. **T5:** map each relative distance to a bucket (exact buckets for small distances, logarithmic buckets for larger ones). Each bucket has a learned scalar bias per head, added to the attention scores.
2. **Transformer-XL:** decompose attention into content and position terms using sinusoidal relative encodings, plus learned global biases. Supports segment recurrence (#134).
3. Shared across layers (T5) to save parameters.

**Cost:** Small.

**Agent use:**
- **Role:** Architect.
- **How:** Found in encoder-decoder models (T5 family) and long-context designs.
- **Rules:** None specific.
- **Guardrails:** None specific.

### 111. Context window extension (position interpolation, NTK-aware scaling, YaRN)

**Definition:** Methods that let a RoPE-based model handle longer sequences than it was trained on, with little or no fine-tuning.

**How it works:**
1. **Position interpolation:** divide positions by a scale factor s, so a sequence s× longer maps into the trained position range. Needs a short fine-tune.
2. **NTK-aware scaling:** increase the RoPE base instead, which stretches low frequencies (long-range) more than high frequencies (local detail), preserving local resolution.
3. **YaRN:** different scaling per frequency band (high frequencies untouched, low frequencies interpolated) plus an attention temperature correction. Works with less fine-tuning.
4. Then fine-tune briefly on long sequences (#229).
5. Evaluate with long-context retrieval tests (finding a fact placed at different depths).

**Cost:** Fine-tuning on long sequences (quadratic attention cost, #116).

**Agent use:**
- **Role:** Trainer.
- **How:** Extending existing models to longer documents, repositories or conversations without full retraining.
- **Rules:** Evaluate both long-context tasks and short-context regressions (NR2).
- **Guardrails:** Claimed context length isn't usable context length. Test retrieval at many depths before relying on it.

## C3. Transformer architecture and efficiency

### 112. The transformer block

**Definition:** The repeated unit of transformers: attention to mix information across positions, and a feed-forward network to transform each position, each with a residual connection and normalization.

**How it works:**
1. **Pre-norm form:** x ← x + Attention(Norm(x)) (#56).
2. x ← x + FFN(Norm(x)), where the FFN is a two-layer MLP or gated unit (#8), usually about 4× (or 8/3× for SwiGLU) wider than the model.
3. Stack L blocks. Add an embedding layer at the start, a final normalization and an output head at the end.
4. Attention handles communication between positions; the FFN handles per-position computation (much of the model's stored knowledge sits in FFN weights).

**Cost:** About 12 × L × d² parameters (dense), roughly 2 FLOPs per parameter per token forward, plus attention's n² term.

**Agent use:**
- **Role:** Architect.
- **How:** The agent estimates parameters, memory and FLOPs per token from L, d and n (NR5): training ≈ 6 × parameters × tokens FLOPs.
- **Rules:** Keep dimensions hardware-friendly (#3).
- **Guardrails:** None specific.

### 113. Encoder-only, decoder-only and encoder-decoder transformers

**Definition:** The three main transformer layouts, each suited to different tasks.

**How it works:**
1. **Encoder-only** (BERT-style): bidirectional attention over the input. Outputs a representation per token. Good for classification, tagging, retrieval and embeddings.
2. **Decoder-only** (GPT-style): causal attention. Generates text one token at a time. Handles almost any task framed as text continuation.
3. **Encoder-decoder** (T5-style): a bidirectional encoder plus a causal decoder with cross-attention to the encoder (#131). Efficient for input-to-output transformations with long inputs and shorter outputs.

**Cost:** Depends on layout. Encoders are cheapest for understanding tasks.

**Agent use:**
- **Role:** Architect.
- **How:** The agent matches layout to task: small encoders for high-volume classification or routing (cheap), decoders for generation.
- **Rules:** Don't use a large generative model where a small encoder classifier suffices (cost, NR5).
- **Guardrails:** None specific.

### 114. Multi-query and grouped-query attention (MQA, GQA)

**Definition:** Sharing key and value projections across several query heads, to shrink the KV cache and speed up generation.

**How it works:**
1. **Standard multi-head:** each of h heads has its own K and V.
2. **MQA:** all query heads share one K and one V.
3. **GQA:** query heads are divided into g groups, and each group shares one K and V (1 < g < h).
4. KV cache size shrinks by h/g. Memory bandwidth during decoding (the bottleneck) drops accordingly.
5. Existing multi-head models can be converted ("uptrained") by averaging K/V heads within groups, then briefly training.

**Cost:** Fewer K/V parameters, and a smaller KV cache.

**Agent use:**
- **Role:** Architect and Deployer.
- **How:** GQA is the standard in modern LLMs: faster, cheaper inference with little quality loss.
- **Rules:** Choose the group count to divide evenly across tensor-parallel devices (#235).
- **Guardrails:** None specific.

### 115. Multi-head latent attention (MLA)

**Definition:** Compressing keys and values into a small shared latent vector per token, caching only that latent, and reconstructing keys and values from it.

**How it works:**
1. Project each token's hidden state down into a low-dimensional latent c (much smaller than all heads' keys and values combined).
2. Cache only c.
3. Keys and values for all heads are up-projections of c. The up-projection can be merged into the query and output projections, so no full K/V reconstruction is needed at inference.
4. Positional information (RoPE) is carried in a small separate part of the key that isn't compressed ("decoupled RoPE").

**Cost:** KV cache far smaller than standard multi-head attention, with quality comparable to or better than GQA.

**Agent use:**
- **Role:** Architect and Deployer.
- **How:** Long-context and high-throughput serving, where the KV cache dominates memory.
- **Rules:** Use serving engines with MLA-specific kernels.
- **Guardrails:** None specific.

### 116. FlashAttention (IO-aware tiled attention)

**Definition:** An exact attention algorithm that avoids writing the full n × n score matrix to GPU memory, by computing attention in tiles that fit in fast on-chip memory.

**How it works:**
1. Split Q, K and V into blocks.
2. For each block of queries, load K/V blocks one at a time into on-chip memory (SRAM).
3. Compute scores, and update the output with **online softmax** (#7): keep a running maximum and normalizer per query, rescaling the partial output as each new block arrives.
4. Never store the full score matrix. Memory becomes O(n) instead of O(n²).
5. **Backward pass:** recompute scores from Q and K blocks instead of storing them.
6. The result is identical to standard attention (exact, not approximate), and much faster, because attention is limited by memory traffic, not arithmetic.

**Cost:** Same FLOPs as standard attention. Much less memory traffic and memory.

**Agent use:**
- **Role:** Deployer and Trainer.
- **How:** Always enabled for training and inference. It's what makes long contexts practical.
- **Rules:** Check that the attention variant used (bias, soft-capping, masks) is supported by the kernel.
- **Guardrails:** A fallback to the slow path can happen silently. Verify which kernel runs (profiling).

### 117. KV cache

**Definition:** Storing the keys and values of already-processed tokens during generation, so each new token only computes its own.

**How it works:**
1. **Prefill:** process the whole prompt in parallel, storing K and V for every layer and position.
2. **Decode:** for each new token, compute only its Q, K and V, append K and V to the cache, and attend over the full cache.
3. Cost per new token becomes O(n) instead of recomputing O(n²).
4. Cache size = 2 × layers × KV heads × head dimension × sequence length × batch size × bytes per value. It often exceeds the model's own memory for long contexts and large batches.

**Cost:** Large memory. Decoding is memory-bandwidth-bound.

**Agent use:**
- **Role:** Deployer.
- **How:** The agent sizes serving hardware from the KV cache formula, and reduces it with GQA/MLA (#114, #115), cache quantization (#256), paging (#118) and prefix sharing (#260).
- **Rules:** Compute cache memory per request before setting batch sizes and context limits (NR5).
- **Guardrails:** Cache memory exhaustion causes failures or evictions under load. Use admission control.

### 118. PagedAttention (paged KV cache memory)

**Definition:** Storing the KV cache in fixed-size blocks (pages), like virtual memory, so memory isn't wasted and can be shared between requests.

**How it works:**
1. Split each sequence's KV cache into blocks of a fixed number of tokens.
2. A block table maps each sequence's logical blocks to physical blocks, which don't need to be contiguous.
3. Allocate blocks on demand as sequences grow, so there's no need to reserve the maximum length up front (much less fragmentation and waste).
4. **Copy-on-write sharing:** sequences with a common prefix (parallel samples, beam search, shared system prompts) share physical blocks until they diverge.
5. Attention kernels read K and V through the block table.

**Cost:** Small indirection overhead. Much higher achievable batch sizes.

**Agent use:**
- **Role:** Deployer.
- **How:** The standard memory manager in high-throughput serving engines (vLLM and others). Often multiplies throughput several times.
- **Rules:** Size the block pool from GPU memory after model weights.
- **Guardrails:** Under memory pressure, define the preemption policy (swap or recompute) explicitly.

### 119. Sliding window (local) attention

**Definition:** Each token attends only to a fixed number of recent tokens, so cost grows linearly with length.

**How it works:**
1. Token i attends to tokens in [i − w, i].
2. Cost per token is O(w), and the KV cache only needs the last w tokens (a rolling buffer).
3. Stacking L layers lets information travel up to L × w positions indirectly.
4. Often interleaved with global (full) attention layers, for example several local layers per global one.

**Cost:** O(n × w).

**Agent use:**
- **Role:** Architect.
- **How:** Cheaper long-context models, where most dependencies are local and a few global layers handle the rest.
- **Rules:** Evaluate long-range retrieval explicitly (#111).
- **Guardrails:** Pure sliding window can't directly retrieve information older than the window. Check the use case needs.

### 120. Sparse attention patterns (Longformer, BigBird)

**Definition:** Attention restricted to a structured subset of pairs (local windows plus a few global and random connections), giving linear cost for long documents.

**How it works:**
1. **Local window:** each token attends to its neighbors.
2. **Global tokens:** a few special tokens (or task-chosen ones, like a question) attend to everything and are attended by everything.
3. **Random connections** (BigBird): each token attends to a few random tokens, which helps information flow.
4. Theory: such patterns can approximate full attention's expressiveness.
5. Needs specialized block-sparse kernels.

**Cost:** O(n × (w + g + r)).

**Agent use:**
- **Role:** Architect.
- **How:** Encoders for long documents (contracts, reports, code files), where full attention is too expensive.
- **Rules:** Choose global tokens deliberately (the question or task tokens, section headers).
- **Guardrails:** None specific.

### 121. Linear attention (kernel feature maps)

**Definition:** Replacing softmax attention with a kernel form that can be computed in linear time, by reordering the multiplications.

**How it works:**
1. Approximate softmax similarity with a feature map: sim(q, k) ≈ φ(q) · φ(k).
2. Attention output = φ(Q) (φ(K)ᵀ V) / normalizer. Computing φ(K)ᵀ V first gives a d × d matrix, independent of n.
3. Cost becomes O(n × d²) instead of O(n² × d).
4. **Causal version:** keep a running sum of φ(k) vᵀ, which works like a recurrent network with a matrix-valued state. Constant memory per decoding step.
5. Usually weaker than softmax attention at precise recall. Modern variants add gating and decay to close the gap.

**Cost:** Linear in n.

**Agent use:**
- **Role:** Architect.
- **How:** Very long sequences and streaming, where constant per-token cost matters. Often used in hybrids with some softmax attention layers.
- **Rules:** Benchmark recall-heavy tasks (copying, lookup) specifically.
- **Guardrails:** None specific.

### 122. Structured state space models (S4)

**Definition:** Sequence models based on continuous-time linear state space systems, discretized and computed efficiently as either a long convolution (for training) or a recurrence (for inference).

**How it works:**
1. Continuous system: h′(t) = A h(t) + B x(t), y(t) = C h(t) + D x(t).
2. Discretize with a step size Δ, giving a linear recurrence h_t = Ā h_{t−1} + B̄ x_t.
3. Unrolled, the output is a convolution of the input with a kernel K = (C B̄, C Ā B̄, C Ā² B̄, …), computed with FFTs for parallel training.
4. A is structured (initialized with the HiPPO method, designed for long memory; diagonal-plus-low-rank or diagonal forms) so the kernel can be computed efficiently.
5. At inference, use the recurrence: constant cost per step.

**Cost:** O(n log n) training (FFT), O(1) per step inference.

**Agent use:**
- **Role:** Architect.
- **How:** Very long sequences (audio, time series, long logs) with linear scaling.
- **Rules:** Compare against transformers on the actual task (NR2).
- **Guardrails:** None specific.

### 123. Mamba (selective state space models)

**Definition:** A state space model whose parameters depend on the input, so it can choose what to remember or ignore, computed with a hardware-efficient parallel scan.

**How it works:**
1. Unlike S4, the parameters Δ, B and C are computed from the current input token.
2. That makes the recurrence content-dependent (selective): a large Δ resets the state to focus on the current token; a small Δ preserves the state.
3. Because parameters vary over time, the convolution trick doesn't apply. Instead use a **parallel scan** (associative prefix computation), fused in on-chip memory.
4. Blocks combine the SSM with gating and short convolutions. Later versions (Mamba-2) relate selective SSMs to structured forms of attention.
5. Constant memory and time per generated token.

**Cost:** Linear in sequence length in training, constant per step at inference.

**Agent use:**
- **Role:** Architect.
- **How:** Long-context and high-throughput generation where KV-cache growth is a problem. Often used in hybrids interleaving Mamba and attention layers.
- **Rules:** Evaluate in-context recall tasks: pure SSMs can lag attention there.
- **Guardrails:** Serving support is less mature than for transformers. Check the inference stack.

### 124. RWKV and RetNet (recurrent transformer alternatives)

**Definition:** Architectures that train in parallel like transformers but run as recurrent networks at inference, with constant memory per token.

**How it works:**
1. **RWKV:** replaces attention with a "time-mixing" operation: an exponentially decaying weighted average of past keys and values (learned per-channel decay). It can be computed as a recurrence with a small state.
2. Channel-mixing blocks act like feed-forward layers.
3. **RetNet:** "retention" with a decay factor γ: output = Σ γ^(n−m) (q_n · k_m) v_m. It has three equivalent forms: parallel (training), recurrent (inference) and chunk-wise (long sequences).
4. Both avoid a growing KV cache.

**Cost:** Constant per step at inference. Parallel training.

**Agent use:**
- **Role:** Architect.
- **How:** Long-running or streaming generation on memory-limited hardware.
- **Rules:** Benchmark against transformers of the same size on the target task.
- **Guardrails:** None specific.

## C4. Mixture of experts

### 125. Mixture of experts with top-k gating

**Definition:** Replacing a dense feed-forward layer with many expert networks and a router that sends each token to only a few of them, increasing parameters without proportional compute.

**How it works:**
1. E expert FFNs per MoE layer (for example 8, 64 or more).
2. **Router:** a linear layer gives a score per expert for each token. Softmax, then keep the top-k experts (k = 1 or 2 typically).
3. The token's output is the weighted sum of its chosen experts' outputs.
4. Total parameters grow with E, but compute per token only grows with k.
5. **Fine-grained experts** (many small experts, with more chosen) and **shared experts** (always active) are common refinements.

**Cost:** Compute ≈ k experts per token. Memory must hold all experts.

**Agent use:**
- **Role:** Architect and Deployer.
- **How:** Large-capacity models at lower compute per token. Serving needs memory for all experts and expert parallelism (#238).
- **Rules:** Plan memory for total parameters, and compute for active parameters (NR5).
- **Guardrails:** Routing imbalance causes overloaded devices and dropped tokens (#126). Monitor expert load.

### 126. Load balancing, capacity factors and token dropping

**Definition:** Techniques that keep MoE experts evenly used, because routers naturally collapse onto a few favorite experts.

**How it works:**
1. **Auxiliary load-balancing loss:** penalize the product of each expert's fraction of tokens and its average router probability, pushing toward uniform use.
2. **Capacity factor:** each expert processes at most C × (tokens / E) tokens per batch. Extra tokens are dropped (they skip the layer through the residual path) or sent to another expert.
3. **Router z-loss** (#140) keeps router logits small for stability.
4. **Auxiliary-loss-free balancing:** add a per-expert bias to the routing scores, adjusted up or down based on recent load, without changing the training loss.

**Cost:** Small overhead.

**Agent use:**
- **Role:** Trainer.
- **How:** Monitoring expert load and drop rates is required for MoE training health (NR4).
- **Rules:** Log per-expert token counts every N steps.
- **Guardrails:** High token-drop rates silently degrade quality. Alert on them.

### 127. Expert-choice routing

**Definition:** Instead of tokens choosing experts, each expert chooses its top tokens, guaranteeing perfect load balance.

**How it works:**
1. Compute router scores for all (token, expert) pairs in a batch.
2. Each expert selects the k tokens with the highest scores for it (k = capacity).
3. Tokens can be processed by zero, one or several experts.
4. Load is balanced by construction, with no auxiliary loss needed.

**Cost:** Same compute as top-k routing at equal capacity.

**Agent use:**
- **Role:** Architect.
- **How:** Balanced MoE training, especially for encoders.
- **Rules:** Not directly suited to autoregressive decoding: expert choice looks across the whole batch, including future tokens. Use token-choice routing for decoders.
- **Guardrails:** Some tokens get no expert. Monitor the fraction.

## C5. Vision, multimodal and memory-augmented transformers

### 128. Vision Transformer (ViT)

**Definition:** Applying a standard transformer to images by splitting them into fixed-size patches and treating each patch as a token.

**How it works:**
1. Split the image into patches (for example 16×16 pixels).
2. Flatten each patch and project it linearly to the model dimension (equivalent to a strided convolution).
3. Add position embeddings (#107), and optionally a [CLS] token whose output is used for classification.
4. Run a standard transformer encoder.
5. Needs large data or strong augmentation and regularization, because it has fewer built-in image assumptions than CNNs.

**Cost:** Quadratic in the number of patches.

**Agent use:**
- **Role:** Architect.
- **How:** A strong image backbone, especially when pretrained at scale (#132, #174, #175), and the vision encoder for multimodal models (#133).
- **Rules:** Use pretrained weights unless the dataset is very large.
- **Guardrails:** High-resolution images produce many patches. Check the cost (NR5).

### 129. Swin Transformer (shifted window attention)

**Definition:** A hierarchical vision transformer computing attention within local windows, shifting the windows between layers so information crosses window borders.

**How it works:**
1. Split the image into patches, then into non-overlapping windows of M × M patches.
2. Compute attention within each window: cost linear in image size.
3. In the next layer, shift the windows by half a window, so new windows span old window borders.
4. Merge neighboring patches between stages, producing a feature hierarchy like a CNN (good for detection and segmentation, #80).
5. Relative position bias within windows.

**Cost:** Linear in image size.

**Agent use:**
- **Role:** Architect.
- **How:** Dense prediction tasks (detection, segmentation) at high resolution.
- **Rules:** None specific.
- **Guardrails:** None specific.

### 130. Perceiver (cross-attention to a latent array)

**Definition:** An architecture that handles very large or varied inputs by having a small fixed set of latent vectors attend to the inputs, then processing only the latents.

**How it works:**
1. A small learned array of N latents (for example 256–512).
2. **Cross-attention:** the latents (queries) attend to the input elements (keys and values): cost O(N × input size), linear in input size.
3. Self-attention among the latents (cost O(N²), independent of input size).
4. Repeat cross-attention and latent self-attention blocks.
5. **Perceiver IO:** output queries attend to the latents, to produce outputs of any shape.

**Cost:** Linear in input size.

**Agent use:**
- **Role:** Architect.
- **How:** Very long or multimodal inputs (audio + video + text, large point clouds, many events), and the basis of "resampler" connectors in multimodal models (#133).
- **Rules:** Size N by the information the task needs.
- **Guardrails:** None specific.

### 131. Cross-attention for conditioning

**Definition:** Attention where queries come from one sequence and keys/values from another, letting a model condition on external information (an encoder output, an image, retrieved text).

**How it works:**
1. Queries from the main stream (decoder tokens, image latents).
2. Keys and values from the conditioning source (encoder states, text embeddings, image features).
3. Inserted in addition to self-attention, inside each block (encoder-decoder transformers, text-to-image diffusion models).
4. The conditioning source's K/V can be computed once and cached for all decoding steps.

**Cost:** O(query length × source length).

**Agent use:**
- **Role:** Architect.
- **How:** Conditioning generation on other modalities or retrieved content (#135, #166).
- **Rules:** None specific.
- **Guardrails:** Conditioning content is untrusted input (NX5). Prompt-injection risks apply to text sources.

### 132. CLIP (contrastive image-text pretraining)

**Definition:** Training an image encoder and a text encoder together so matching image-caption pairs have similar embeddings, enabling zero-shot classification and cross-modal search.

**How it works:**
1. An image encoder (ViT or ResNet) and a text encoder (transformer), each followed by a projection into a shared space.
2. For a batch of N image-text pairs, compute all N × N similarities.
3. A symmetric contrastive loss: each image should match its own caption among all captions, and vice versa (with a learned temperature).
4. **Zero-shot classification:** embed prompts like "a photo of a {class}", and pick the class whose embedding best matches the image.
5. Trained on very large web-scale image-text datasets. SigLIP replaces the softmax with a pairwise sigmoid loss, which scales better.

**Cost:** Large-batch training. Inference is two encoder passes.

**Agent use:**
- **Role:** Architect.
- **How:** Image search by text, zero-shot image tagging, and the vision encoder in multimodal LLMs (#133).
- **Rules:** Evaluate zero-shot quality on your own image domain before relying on it.
- **Guardrails:** Web-trained models carry social biases. Evaluate bias before use on people-related images (NX3).

### 133. Multimodal LLM connectors (projection layers, Q-Former, resamplers)

**Definition:** Modules that turn a vision (or audio) encoder's outputs into tokens a language model can read.

**How it works:**
1. A pretrained image encoder (#132) produces patch features.
2. **Linear or MLP projector:** map each patch feature into the LLM's embedding space, giving one visual token per patch. Simple and strong.
3. **Q-Former / resampler:** a small set of learned queries cross-attends to the patch features (#130), producing a fixed, small number of visual tokens (saves context).
4. Training usually happens in stages: first align the connector (encoder and LLM frozen), then fine-tune on instruction data (#208).
5. High-resolution images are handled by tiling: several crops, each encoded separately.

**Cost:** Visual tokens consume LLM context: hundreds to thousands per image.

**Agent use:**
- **Role:** Architect.
- **How:** Building or choosing models that read screenshots, documents, charts and photos.
- **Rules:** Budget visual tokens per image (NR5).
- **Guardrails:** Text inside images is untrusted input: injected instructions can arrive through images (NX5).

### 134. Segment-level recurrence (Transformer-XL)

**Definition:** Letting a transformer use cached hidden states from the previous text segment as extra context, extending its memory beyond one segment.

**How it works:**
1. Process text in segments of length L.
2. When processing segment t, keep the hidden states from segment t−1 (gradient stopped) and let attention also attend over them.
3. Memory reach grows with depth: about L × number of layers.
4. Requires relative position encodings (#110), since absolute positions would collide between segments.

**Cost:** Attention over L + memory length per segment.

**Agent use:**
- **Role:** Architect.
- **How:** Long text processing with bounded per-segment cost. The idea underlies many memory-augmented designs.
- **Rules:** None specific.
- **Guardrails:** None specific.

### 135. Retrieval-enhanced transformers (RETRO chunked cross-attention)

**Definition:** A model that retrieves similar text chunks from a large database during processing, and attends to them with cross-attention, so knowledge lives partly in the database instead of the weights.

**How it works:**
1. Split the input into chunks (for example 64 tokens).
2. For each chunk, retrieve the k nearest chunks (plus their continuations) from a database, using frozen embeddings and approximate nearest neighbor search.
3. Encode the retrieved chunks.
4. **Chunked cross-attention:** tokens of chunk i attend to the neighbors retrieved for chunk i−1 (preserving causality).
5. Smaller models can match larger ones on knowledge-heavy tasks, and the database can be updated without retraining.

**Cost:** Retrieval per chunk, plus cross-attention.

**Agent use:**
- **Role:** Architect.
- **How:** An architectural form of retrieval augmentation, where knowledge must be updatable and attributable.
- **Rules:** Deduplicate the database against evaluation data (#289).
- **Guardrails:** Retrieved text is untrusted (NX5). Database deletions must be honored (erasure).

### 136. Prefix language modeling and mixture of denoisers (UL2)

**Definition:** Training objectives that combine bidirectional understanding of a prefix with causal generation of the rest, and mix several denoising tasks in one model.

**How it works:**
1. **Prefix LM:** a causal decoder where the prefix positions attend to each other bidirectionally, and the rest is generated causally.
2. **UL2 mixture of denoisers:** sample per example among
   - R-denoising (short spans, like T5),
   - X-denoising (long spans, or high corruption),
   - S-denoising (prefix LM: continue a sequence).
3. A mode token tells the model which task it's doing.
4. The resulting model handles both understanding and generation tasks well.

**Cost:** Similar to standard pretraining.

**Agent use:**
- **Role:** Trainer.
- **How:** Pretraining general models that will be used for both comprehension and generation.
- **Rules:** None specific.
- **Guardrails:** None specific.

### 137. Multi-token prediction

**Definition:** Training a model to predict several future tokens at each position (not just the next one), using extra output heads.

**How it works:**
1. The shared trunk produces a hidden state per position.
2. n independent heads (or small sequential modules) predict tokens t+1, t+2, …, t+n.
3. Loss = the sum of their cross-entropy losses.
4. Gives a denser training signal, often improving quality on reasoning and code at scale.
5. At inference, the extra heads can serve as drafters for speculative decoding (#146, #147).

**Cost:** Small extra compute per position, with memory-efficient sequential head computation.

**Agent use:**
- **Role:** Trainer and Deployer.
- **How:** Better training efficiency, and faster inference through built-in drafting.
- **Rules:** Evaluate next-token quality and drafting acceptance rates.
- **Guardrails:** None specific.

## C6. Scaling and stability

### 138. Scaling laws (compute-optimal training)

**Definition:** Empirical power laws relating model size, data size and compute to loss, used to choose model and dataset sizes for a compute budget.

**How it works:**
1. Loss falls as a power law in parameters N, tokens D and compute C, until other limits apply.
2. **Compute-optimal (Chinchilla):** for a fixed compute budget C ≈ 6 × N × D, parameters and tokens should grow roughly equally. A rule of thumb is about 20 tokens per parameter.
3. **Fit the laws** from a series of small runs (with WSD schedules, #45, to reuse checkpoints), then extrapolate.
4. **Inference-aware:** if the model will serve many requests, train a smaller model on more tokens than compute-optimal, since inference cost depends on model size.
5. Data quality and repetition (multiple epochs) shift the curves.

**Cost:** The cost of the small fitting runs.

**Agent use:**
- **Role:** Architect and Trainer.
- **How:** Sizing training runs before spending large budgets (NR5): what model size, how many tokens, what expected loss.
- **Rules:** Fit scaling laws on your own data and setup. Published constants are guides only.
- **Guardrails:** Extrapolating far beyond the fitted range is risky. Validate with a medium-scale run.

### 139. Attention sinks and streaming generation (StreamingLLM)

**Definition:** The observation that models put large attention weight on the first few tokens regardless of content, and the method of keeping those tokens plus a recent window for unlimited-length streaming.

**How it works:**
1. Softmax attention must put weight somewhere. Models learn to "dump" unneeded attention on the initial tokens (the attention sinks).
2. Naive sliding windows that evict those first tokens make quality collapse.
3. **StreamingLLM:** keep the KV cache of the first few tokens (for example 4) plus a recent window. Positions are assigned within the cache.
4. That gives stable generation over very long streams with bounded memory.
5. Training with a dedicated learnable sink token improves this further.

**Cost:** Bounded KV cache.

**Agent use:**
- **Role:** Deployer.
- **How:** Long-running sessions (assistants, log monitors) with constant memory.
- **Rules:** This doesn't give recall of old content outside the window. Pair with retrieval or summaries for long-term memory.
- **Guardrails:** Users must not assume content outside the window is remembered.

### 140. Logit stabilization (output z-loss, router z-loss)

**Definition:** Small auxiliary losses that keep logits from growing too large, preventing numerical instability in large-scale training.

**How it works:**
1. **Output z-loss:** add α × (log Σ e^(logits))² to the loss, which pushes the softmax normalizer toward 1 (log Z ≈ 0).
2. Prevents logits drifting to large values, which cause overflow in low precision (#231) and loss spikes.
3. **Router z-loss** (MoE): the same penalty on router logits, stabilizing routing (#126).
4. Typical α: 10⁻⁴ (output) to 10⁻³ (router).

**Cost:** Negligible.

**Agent use:**
- **Role:** Trainer.
- **How:** A standard stability measure for large and low-precision training.
- **Rules:** Log the z-loss term separately (NR4).
- **Guardrails:** None specific.

## C7. Decoding

### 141. Greedy decoding and temperature sampling

**Definition:** The basic ways of choosing the next token: always the most likely (greedy), or sampling from the probability distribution, sharpened or flattened by a temperature.

**How it works:**
1. **Greedy:** pick argmax at each step. Deterministic, but can be repetitive and miss better overall sequences.
2. **Sampling:** draw from softmax(logits / T).
3. T < 1 sharpens toward the likely tokens. T > 1 flattens, adding diversity and risk. T → 0 approaches greedy.
4. Combined with truncation methods (#142, #143) in practice.

**Cost:** O(vocabulary) per step.

**Agent use:**
- **Role:** Deployer.
- **How:** Low temperature or greedy decoding for extraction, classification-like and code tasks (consistency). Higher temperatures for brainstorming and diverse candidates (#149).
- **Rules:** Set and record temperature per use case (NR1).
- **Guardrails:** Sampling makes outputs nondeterministic. Fix seeds where reproducibility matters (#295), knowing that batching can still change results.

### 142. Top-k sampling

**Definition:** Sampling only among the k most likely tokens.

**How it works:**
1. Sort tokens by probability.
2. Keep the top k and set the others to zero.
3. Renormalize and sample.
4. Removes the long tail of unlikely tokens that cause incoherent output.

**Cost:** O(vocabulary) per step (partial sort).

**Agent use:**
- **Role:** Deployer.
- **How:** A simple safeguard against rare garbage tokens.
- **Rules:** Prefer nucleus or min-p (#143) when the number of plausible tokens varies a lot by context.
- **Guardrails:** None specific.

### 143. Nucleus (top-p) and min-p sampling

**Definition:** Adaptive truncation: keep the smallest set of tokens whose probabilities sum to p (top-p), or every token at least a fraction of the top token's probability (min-p).

**How it works:**
1. **Top-p:** sort by probability, and keep tokens until the cumulative probability reaches p (for example 0.9). In confident contexts only a few tokens remain; in open contexts, many.
2. **Min-p:** keep tokens with probability ≥ min_p × (top probability), for example 0.05. Scales naturally with the model's confidence, and stays robust at higher temperatures.
3. Renormalize and sample.

**Cost:** O(vocabulary) per step.

**Agent use:**
- **Role:** Deployer.
- **How:** Default sampling settings for natural text generation.
- **Rules:** Tune on the target task. Order of operations (temperature before or after truncation) matters and should be consistent.
- **Guardrails:** None specific.

### 144. Repetition, frequency and presence penalties

**Definition:** Adjusting logits of tokens that already appeared, to reduce repetitive output.

**How it works:**
1. **Repetition penalty:** divide positive logits (multiply negative ones) by a factor for previously generated tokens.
2. **Frequency penalty:** subtract α × (count of the token so far).
3. **Presence penalty:** subtract β once if the token has appeared at all.
4. **No-repeat n-gram:** block any token that would repeat an n-gram already in the output.

**Cost:** O(generated length) bookkeeping.

**Agent use:**
- **Role:** Deployer.
- **How:** Reduces loops and repetition in long free-text generation.
- **Rules:** Disable or minimize penalties for structured output (code, JSON, identifiers), where repeating tokens is correct.
- **Guardrails:** Strong penalties corrupt structured outputs. Test with real formats.

### 145. Contrastive search and contrastive decoding

**Definition:** Decoding methods that balance likelihood with avoiding degenerate repetition, or that contrast a strong model with a weaker one to favor "expert" predictions.

**How it works:**
1. **Contrastive search:** among the top-k candidates, choose the one maximizing (1 − α) × probability − α × (maximum cosine similarity between the candidate's hidden state and previous hidden states). This penalizes tokens that make the text repeat itself.
2. **Contrastive decoding:** score = log p_expert − log p_amateur (a smaller model), restricted to tokens the expert finds plausible. Removes generic, low-quality continuations that both models like.
3. **DoLa:** contrast the final layer's predictions with an earlier layer's, to emphasize factual knowledge from later layers.

**Cost:** Extra computation per step (hidden-state similarities or a second model).

**Agent use:**
- **Role:** Deployer.
- **How:** Higher-quality open-ended text with less repetition, or fewer generic answers.
- **Rules:** Benchmark against nucleus sampling on the target task.
- **Guardrails:** None specific.

### 146. Speculative decoding (draft and verify)

**Definition:** Speeding up generation by having a small fast model propose several tokens, which the large model verifies in one parallel pass, with output identical in distribution to the large model alone.

**How it works:**
1. A draft model generates γ tokens quickly.
2. The target model scores all γ positions in one forward pass (parallel, like prefill).
3. **Accept/reject (rejection sampling):** accept each draft token with probability min(1, p_target / p_draft). At the first rejection, sample a replacement from the adjusted distribution (p_target − p_draft)₊, and discard the rest.
4. If all are accepted, sample one extra token from the target.
5. The output distribution is exactly the target model's. Speedup depends on the acceptance rate.

**Cost:** Draft model compute + one target pass per round. Typical speedups: 2–3×.

**Agent use:**
- **Role:** Deployer.
- **How:** Lower latency for large models without changing their outputs.
- **Rules:** Monitor acceptance rates per workload. Low acceptance means the draft model doesn't fit the domain.
- **Guardrails:** At large batch sizes, the extra compute can reduce throughput. Measure under realistic load.

### 147. Self-drafting decoding heads (Medusa, EAGLE)

**Definition:** Speculative decoding without a separate draft model: small extra heads on the target model predict several future tokens, verified with tree attention.

**How it works:**
1. **Medusa:** add k heads on the last hidden state, each predicting the token at offset i+1…i+k.
2. Combine the heads' top candidates into a tree of possible continuations.
3. **Tree attention:** verify the whole tree in one forward pass, with a mask so each branch only attends to its own ancestors.
4. Accept the longest verified prefix (typical acceptance, or exact rejection sampling).
5. **EAGLE:** drafts at the feature level, with a small autoregressive head over the target's hidden states, which gives higher acceptance rates.

**Cost:** Small extra heads. Often 2–3× or more speedup.

**Agent use:**
- **Role:** Deployer.
- **How:** Faster serving for models where training small heads is feasible, without maintaining a separate draft model.
- **Rules:** Train heads on data similar to production traffic.
- **Guardrails:** With non-exact acceptance schemes, outputs differ slightly from the base model. Evaluate quality.

### 148. Constrained (grammar-guided) decoding

**Definition:** Forcing generated text to follow a formal structure (JSON schema, regex, grammar) by masking out tokens that would break it at each step.

**How it works:**
1. Compile the constraint into an automaton: a finite-state machine for regular languages and JSON schemas, or a pushdown automaton for context-free grammars.
2. Precompute, for each automaton state, which vocabulary tokens are allowed (a token can span several characters, so map token strings through the automaton).
3. At each step, set the logits of disallowed tokens to −∞, then sample or pick as usual.
4. Advance the automaton with the chosen token.
5. The output is guaranteed to parse.

**Cost:** Precomputation of token masks. Small per-step overhead with good implementations.

**Agent use:**
- **Role:** Deployer.
- **How:** Guarantees valid structured outputs for tool calls, extraction and configs, so downstream parsing never fails. A key reliability tool for agents.
- **Rules:** Constrain structure, then validate content with schemas and business rules (validity of syntax doesn't mean correct values).
- **Guardrails:** Over-constraining can force the model into bad content. Allow an explicit "cannot answer" path in the schema.

### 149. Self-consistency (sample and vote)

**Definition:** Generating several independent answers (with reasoning) and taking the most common final answer.

**How it works:**
1. Sample N responses at a moderate temperature.
2. Extract each final answer (a number, a choice, a normalized string).
3. Choose the most frequent answer (majority vote), optionally weighted by model confidence.
4. The agreement rate is a useful confidence signal.

**Cost:** N× generation cost.

**Agent use:**
- **Role:** Deployer and Evaluator.
- **How:** Improves accuracy on questions with a checkable final answer, and gives a cheap confidence estimate: low agreement means escalate to a human or a stronger method.
- **Rules:** Only for tasks with comparable final answers.
- **Guardrails:** N× cost. Use adaptively (more samples only when early samples disagree).

### 150. Lookahead and Jacobi decoding (parallel decoding without a draft model)

**Definition:** Generating several tokens in parallel by iteratively refining guesses for future positions with the model itself, until they stabilize.

**How it works:**
1. **Jacobi decoding:** guess the next n tokens (for example, randomly or by copying). Run the model on all of them at once, updating every guess from the model's predictions.
2. Repeat until the guesses stop changing. That fixed point equals greedy decoding.
3. **Lookahead decoding:** a sliding window of Jacobi iterations generates candidate n-grams, kept in a pool. Verify candidates matching the current context in parallel (like speculative verification), accepting several tokens per step.
4. No separate draft model or extra heads.

**Cost:** Extra parallel computation per step. Speedups depend on the content's predictability.

**Agent use:**
- **Role:** Deployer.
- **How:** Latency reduction where draft models aren't available, especially for repetitive or structured outputs (code, templates).
- **Rules:** Measure speedups on real workloads.
- **Guardrails:** Gains shrink at high batch sizes, when compute is already saturated.

---
