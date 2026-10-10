# Part 6: Inference optimization, robustness, interpretability, safety and evaluation (#251–300)

Same format and the same contract (roles; rules NR1–NR8; guardrails NX1–NX5). This is the final part.

## F1. Quantization

### 251. Post-training quantization (INT8, per-channel, calibration)

**Definition:** Converting a trained model's weights (and often activations) from floating point to 8-bit integers without retraining, using a small calibration set.

**How it works:**
1. **Mapping:** q = round(x / scale) + zero_point, clipped to the integer range. Symmetric quantization uses zero_point = 0.
2. **Granularity:** per-tensor (one scale per tensor), per-channel (one per output channel, much more accurate for weights), or per-group (one per block of, say, 128 values).
3. **Calibration:** run representative inputs and record activation ranges. Choose scales by min/max, percentiles, or by minimizing error (MSE or KL between the original and quantized distributions).
4. Integer matrix multiplications with higher-precision accumulators, then rescale.
5. Sensitive layers (first and last layers, normalization) often stay in higher precision.

**Cost:** About 2–4× less memory than FP16/FP32, and faster integer arithmetic.

**Agent use:**
- **Role:** Deployer.
- **How:** The first step to cheaper inference for classifiers, encoders and many generative models.
- **Rules:** Calibrate on data resembling production traffic. Evaluate accuracy against the original (NR7).
- **Guardrails:** Activation outliers (common in LLMs) break naive INT8 activation quantization. Use #254.

### 252. GPTQ (second-order weight quantization)

**Definition:** Quantizing weights layer by layer to 3–4 bits, adjusting the not-yet-quantized weights to compensate for each rounding error, using second-order information from calibration data.

**How it works:**
1. For each layer, collect inputs X from a small calibration set, and compute H = X Xᵀ (it measures how errors in each input dimension affect the output).
2. Quantize the weights one column (or block) at a time.
3. After quantizing a column, spread its rounding error onto the remaining unquantized columns, weighted by the inverse of H, so the layer's output changes as little as possible.
4. Efficient updates using a Cholesky decomposition, processed in blocks for speed.
5. Usually combined with per-group scales (for example 128 weights per group).

**Cost:** Minutes to hours for large models, on a single GPU.

**Agent use:**
- **Role:** Deployer.
- **How:** 4-bit weight-only quantization of LLMs with small quality loss, so large models fit on less hardware.
- **Rules:** Use calibration data from the target domain. Evaluate perplexity and task benchmarks (#288).
- **Guardrails:** Quality loss is uneven across tasks (reasoning and long-context often suffer more). Evaluate broadly.

### 253. AWQ (activation-aware weight quantization)

**Definition:** 4-bit weight quantization that protects the small fraction of weights connected to large activations, by scaling them before quantization.

**How it works:**
1. Run calibration data and measure the average activation magnitude per input channel.
2. Channels with large activations matter most: rounding errors in their weights cause large output errors.
3. Scale those weight channels up by a factor s (and the corresponding activations down by 1/s, folded into the previous operation), so their relative rounding error shrinks.
4. Search s per layer to minimize the output error.
5. Then quantize all weights uniformly (per group).

**Cost:** Fast (no weight reconstruction like GPTQ).

**Agent use:**
- **Role:** Deployer.
- **How:** Robust 4-bit LLM quantization, widely supported by serving engines.
- **Rules:** Same evaluation rules as #252.
- **Guardrails:** Same as #252.

### 254. SmoothQuant (migrating activation outliers into weights)

**Definition:** Making both weights and activations quantizable to INT8 by moving the difficulty of activation outliers into the weights, through a mathematically equivalent rescaling.

**How it works:**
1. LLM activations have a few channels with huge values, which makes per-tensor activation quantization inaccurate. Weights are easy to quantize.
2. For each input channel j, choose a scale s_j = max|X_j|^α / max|W_j|^(1−α), with α ≈ 0.5.
3. Divide the activations by s (folded into the previous normalization layer), and multiply the weights by s. The product is unchanged.
4. Activations become smoother; weights absorb some of the range.
5. Then quantize both to INT8 (W8A8) for fast integer matrix multiplications.

**Cost:** Offline rescaling only.

**Agent use:**
- **Role:** Deployer.
- **How:** Full INT8 inference for LLMs (faster prefill and higher throughput), not just weight compression.
- **Rules:** Tune α per model.
- **Guardrails:** Evaluate on long and diverse inputs, where activation ranges differ most.

### 255. Quantization-aware training (QAT)

**Definition:** Training (or fine-tuning) with simulated quantization in the forward pass, so the model learns weights that stay accurate after quantization.

**How it works:**
1. Insert "fake quantization" operations: quantize then dequantize weights (and activations) in the forward pass.
2. Backward: straight-through estimator (#29) passes gradients through the rounding.
3. Optionally learn the scales too (LSQ: learned step size).
4. The model adapts to the quantization error during training.
5. Export to real integer kernels after training.

**Cost:** Training or fine-tuning compute.

**Agent use:**
- **Role:** Trainer and Deployer.
- **How:** When post-training quantization (#251–254) loses too much quality, especially at very low bit widths (4-bit and below) or on edge devices.
- **Rules:** Fine-tune briefly from the trained model rather than training from scratch.
- **Guardrails:** Evaluate the real exported integer model, not the fake-quantized one.

### 256. KV-cache quantization

**Definition:** Storing the attention key/value cache (#117) in 8-bit or 4-bit precision to fit longer contexts and larger batches.

**How it works:**
1. Quantize K and V as they're written to the cache, dequantize them when attention reads them.
2. **Granularity:** keys have outlier channels, so per-channel quantization suits keys; values suit per-token quantization (as in KIVI).
3. Keep the most recent tokens in full precision (they matter most and change the cache fastest), quantizing older ones.
4. Formats: INT8, FP8, or INT4 with group scales.

**Cost:** 2–4× less KV memory, with small dequantization overhead.

**Agent use:**
- **Role:** Deployer.
- **How:** Raises the number of concurrent requests and the context length per GPU, which directly lowers serving costs.
- **Rules:** Evaluate long-context tasks specifically (errors accumulate over long caches).
- **Guardrails:** None specific.

### 257. Low-bit number formats (NF4, block floating point, MXFP4, GGUF k-quants)

**Definition:** Specialized 4-bit and mixed formats designed to represent neural network weights accurately with shared scales.

**How it works:**
1. **NF4 (NormalFloat4):** the 16 representable values are placed at quantiles of a normal distribution, matching the typical shape of weights (used in QLoRA, #219).
2. **Block floating point / microscaling (MX formats, specified by the Open Compute Project):** small blocks (for example 32 values) share one exponent (scale), and each value has a few bits. MXFP4 and MXFP8 have hardware support on newer accelerators.
3. **GGUF k-quants (llama.cpp):** hierarchical blocks, where super-blocks hold scales for sub-blocks, with mixed bit widths per tensor type (for example more bits for attention and output layers).
4. Choosing the format means trading off accuracy, memory and kernel support.

**Cost:** About 4–5 bits per weight including scales.

**Agent use:**
- **Role:** Deployer.
- **How:** Choosing formats for each deployment target: datacenter GPUs, CPUs, laptops, edge devices.
- **Rules:** Use the format the target runtime accelerates natively.
- **Guardrails:** Evaluate quality per format (NR7). Formats with the same nominal bits differ in accuracy.

## F2. Inference optimization and serving

### 258. Kernel fusion and compilation (XLA, TorchInductor, Triton)

**Definition:** Combining sequences of operations into single GPU kernels, and compiling model graphs into optimized code, to cut memory traffic and launch overhead.

**How it works:**
1. Many neural network operations (activations, normalization, adds) are memory-bound: each separate kernel reads and writes the whole tensor.
2. **Fusion:** merge consecutive elementwise and reduction operations into one kernel, so data stays in fast memory (registers or SRAM).
3. **Graph compilers** (XLA, TorchInductor, TensorRT) capture the model's computation graph, fuse operations, choose memory layouts, and generate kernels (often in Triton, a Python-like language for GPU kernels).
4. **Autotuning:** try several tile sizes and configurations per shape, and pick the fastest.
5. **CUDA graphs:** record a sequence of kernel launches once and replay it, which removes per-launch CPU overhead (important for small-batch decoding).

**Cost:** Compilation time. Often 1.3–3× faster execution.

**Agent use:**
- **Role:** Deployer and Trainer.
- **How:** A low-effort speedup for training and inference.
- **Rules:** Compile with production shapes. Changing shapes trigger recompilation (use bucketing).
- **Guardrails:** Compiled outputs can differ slightly numerically. Validate against eager execution.

### 259. Continuous batching (iteration-level scheduling)

**Definition:** Serving generative models by adding and removing requests from the running batch at every decoding step, instead of waiting for a whole batch to finish.

**How it works:**
1. **Static batching:** a batch runs until its longest request finishes. Short requests waste slots and new requests wait.
2. **Continuous batching:** after each decoding step, finished sequences leave the batch, and waiting requests join (their prefill is inserted).
3. The GPU stays fully used, and new requests start quickly.
4. Works with paged KV-cache memory (#118) to allocate memory flexibly.
5. A scheduler decides admission based on memory, priorities and latency targets.

**Cost:** Scheduling overhead is small. Throughput often several times higher than static batching.

**Agent use:**
- **Role:** Deployer.
- **How:** The standard serving approach for LLM endpoints that handle many agent requests.
- **Rules:** Set admission limits from KV memory (#117) and latency targets.
- **Guardrails:** Long prefills can stall ongoing decodes. Use chunked prefill (#261).

### 260. Prefix caching (radix-tree KV reuse)

**Definition:** Reusing the KV cache of shared prompt prefixes (system prompts, documents, conversation history) across requests, so the shared part isn't recomputed.

**How it works:**
1. Store computed KV blocks indexed by the token sequence they correspond to.
2. **Radix tree:** organize cached prefixes as a tree of token sequences. A new request walks the tree to find its longest cached prefix.
3. Reuse those blocks, and compute only the new suffix.
4. Evict least-recently-used leaves when memory runs low (shared blocks are reference-counted).
5. Works with paged memory (#118).

**Cost:** Memory for cached prefixes. Large savings in prefill compute and time to first token.

**Agent use:**
- **Role:** Deployer.
- **How:** Agents send repeated long prefixes (tool definitions, system prompts, shared documents, conversation history). Prefix caching cuts their cost and latency substantially.
- **Rules:** Put stable content first in prompts (system prompt, tools, documents) and variable content last, to maximize prefix reuse.
- **Guardrails:** Never share cached prefixes across tenants when content is private. Scope cache keys by tenant (NX2).

### 261. Chunked prefill and prefill/decode disaggregation

**Definition:** Separating the two phases of LLM inference (compute-heavy prompt processing and memory-heavy token generation) so they don't interfere with each other.

**How it works:**
1. **Prefill** processes the whole prompt at once: compute-bound. **Decode** generates one token per step: memory-bandwidth-bound.
2. **Chunked prefill:** split long prompts into chunks, and schedule each chunk together with ongoing decode steps in the same batch. Decodes keep making progress, and the GPU is used well.
3. **Disaggregation:** run prefill and decode on separate GPU pools, each sized and configured for its phase. Transfer the KV cache from the prefill workers to the decode workers.
4. This lets you tune time to first token and inter-token latency independently.

**Cost:** KV transfer bandwidth (for disaggregation).

**Agent use:**
- **Role:** Deployer.
- **How:** Meeting latency targets for both first-token and streaming speed at high load.
- **Rules:** Track time to first token and time per output token separately as service-level indicators.
- **Guardrails:** None specific.

### 262. Early exit and adaptive computation

**Definition:** Letting easy inputs leave the network early, using intermediate prediction heads, while hard inputs use the full depth.

**How it works:**
1. Attach classifier heads after several intermediate layers.
2. Train all heads (with a weighted sum of their losses, or by distillation from the final head).
3. At inference, after each head, check a confidence criterion (maximum probability, entropy, or a learned halting score). If confident enough, stop and return.
4. **For generation:** layer skipping per token, with mechanisms to fill in the skipped layers' KV cache.
5. **Adaptive computation time:** a learned halting unit decides how many steps to compute.

**Cost:** Saves compute on easy inputs.

**Agent use:**
- **Role:** Deployer.
- **How:** Cheaper high-volume classification and routing, where most inputs are easy.
- **Rules:** Calibrate exit thresholds on validation data for a target accuracy.
- **Guardrails:** Easy-looking inputs can be wrong. Monitor accuracy of early exits separately.

### 263. Low-rank weight compression (SVD factorization)

**Definition:** Replacing large weight matrices with products of two thin matrices, found by singular value decomposition.

**How it works:**
1. Compute the SVD of a weight matrix: W = U Σ Vᵀ.
2. Keep the top r singular values: W ≈ (U_r Σ_r)(V_rᵀ), which is two matrices of sizes d × r and r × k.
3. **Activation-aware variants:** weight the approximation by calibration activations, so errors in important directions are smaller.
4. Fine-tune briefly to recover accuracy.
5. Choose r per layer, by how fast its singular values decay.

**Cost:** Parameters and compute drop from d × k to r × (d + k).

**Agent use:**
- **Role:** Deployer.
- **How:** Compresses models (especially large MLP and embedding layers) where quantization alone isn't enough, or combined with it.
- **Rules:** Evaluate per-layer sensitivity before choosing ranks.
- **Guardrails:** Quality and safety re-evaluation after compression (NR7, NX3).

### 264. Graph-level model optimization (ONNX, constant folding, layout optimization)

**Definition:** Optimizing the model's computation graph before deployment: removing redundant operations, precomputing constants, and choosing efficient data layouts, often through the ONNX interchange format (a Linux Foundation project).

**How it works:**
1. Export the model to a graph format (ONNX, or a framework's own).
2. **Constant folding:** precompute parts that don't depend on input.
3. **Operator fusion** (#258) and **elimination** of no-op operations (identity, redundant reshapes and transposes).
4. **Layout optimization:** choose memory layouts (channels-first or channels-last, tiled) that suit the target hardware.
5. **Folding normalization into weights:** BatchNorm at inference is a linear transform that merges into the preceding convolution.
6. Runtimes (ONNX Runtime, TensorRT, OpenVINO) apply hardware-specific optimizations.

**Cost:** One-time optimization.

**Agent use:**
- **Role:** Deployer.
- **How:** Portable, optimized deployment across CPUs, GPUs and edge devices.
- **Rules:** Validate numerical equivalence of the exported graph against the original on test inputs.
- **Guardrails:** Some custom operations don't export. Check before planning deployment.

### 265. Model cascades and routing (cheap first, expensive on demand)

**Definition:** Sending each request first to a cheap model, and only escalating to a larger model when the cheap one is uncertain or the request looks hard.

**How it works:**
1. Order models by cost: small classifier → small LLM → large LLM (or similar).
2. **Cascade:** run the cheap model, compute its confidence (probability, self-consistency #149, a verifier score), and escalate if confidence is below a threshold.
3. **Router:** a small classifier predicts which model is needed from the request alone, without running the cheap model first.
4. Tune thresholds for the target quality/cost trade-off on validation data.

**Cost:** Average cost is close to the cheap model's when most requests are easy.

**Agent use:**
- **Role:** Deployer.
- **How:** Large cost savings for agent workloads, where many steps are simple (classification, extraction, formatting) and few need a large model.
- **Rules:** Measure quality on the escalated and non-escalated slices separately.
- **Guardrails:** Cheap models can be confidently wrong. Use calibrated confidence (#270), and audit samples of non-escalated outputs.

## F3. Robustness and uncertainty

### 266. Certified robustness (randomized smoothing, interval bound propagation)

**Definition:** Methods that give a provable guarantee that a model's prediction doesn't change for any input perturbation within a given size.

**How it works:**
1. **Randomized smoothing:** the smoothed classifier predicts the class most often chosen by the base model under Gaussian noise added to the input. If the top class is chosen with probability p_A (estimated by sampling), the prediction is provably unchanged within an L2 radius of about σ × Φ⁻¹(p_A).
2. **Interval bound propagation (IBP):** propagate lower and upper bounds of every activation through the network for an input region. If the correct class's lower bound beats every other class's upper bound, the prediction is certified for that region.
3. Train with these bounds (certified training) to make certificates larger.

**Cost:** Randomized smoothing needs many noisy samples per prediction. IBP is cheap but loose.

**Agent use:**
- **Role:** Evaluator.
- **How:** Gives provable robustness for high-stakes classifiers facing adversarial inputs.
- **Rules:** Report certified accuracy at stated radii, alongside clean accuracy.
- **Guardrails:** Certificates only cover the stated threat model (for example small L2 changes), not other manipulations.

### 267. Out-of-distribution detection (max softmax, energy score, Mahalanobis distance)

**Definition:** Detecting inputs that differ from the training data, where predictions are unreliable.

**How it works:**
1. **Maximum softmax probability:** a low top-class probability suggests an unfamiliar input. Simple, but overconfident models make it weak.
2. **Energy score:** −T × log Σ exp(logits / T). Separates in-distribution and out-of-distribution inputs better than softmax probabilities.
3. **Mahalanobis distance:** fit class-conditional Gaussians to features (from an intermediate layer). Distance to the nearest class mean indicates how unusual the input is.
4. **Feature-based k-NN:** distance to the nearest training features.
5. Set thresholds on validation data containing known OOD examples.

**Cost:** Cheap at inference (feature extraction plus a score).

**Agent use:**
- **Role:** Evaluator and Deployer.
- **How:** Routes unfamiliar inputs to fallback handling (human review, a larger model, a "can't classify" response) instead of a confident wrong answer.
- **Rules:** Test on realistic OOD data for the domain (new product types, new languages, new log formats).
- **Guardrails:** OOD detectors miss some kinds of shift. Monitor production data drift too.

### 268. Deep ensembles

**Definition:** Training several networks independently (different random initializations and data orders), and averaging their predictions, which gives better accuracy and more reliable uncertainty.

**How it works:**
1. Train M models (often 5) with different seeds.
2. Average their predicted probabilities (or means and variances, for regression).
3. **Disagreement** between members indicates uncertainty, especially on unfamiliar inputs.
4. Cheaper variants: snapshot ensembles (checkpoints from cyclic schedules, #44), BatchEnsemble (shared weights with small per-member factors), multi-head ensembles.

**Cost:** M× training and inference cost.

**Agent use:**
- **Role:** Evaluator and Deployer.
- **How:** High-quality uncertainty estimates where errors are costly, and for detecting when to defer to humans.
- **Rules:** Use cheaper variants or distill the ensemble into one model (#225) for deployment.
- **Guardrails:** Ensembles share data biases, so agreement isn't proof of correctness.

### 269. Monte Carlo dropout for uncertainty

**Definition:** Estimating prediction uncertainty by keeping dropout active at inference and running several forward passes.

**How it works:**
1. Keep dropout on at test time (#58).
2. Run T forward passes (for example 10–50) with different dropout masks.
3. The mean of the predictions is the estimate; the spread (variance, or entropy of the mean prediction) is the uncertainty.
4. Interpreted as approximate Bayesian inference over the weights.

**Cost:** T× inference.

**Agent use:**
- **Role:** Evaluator.
- **How:** Cheap uncertainty for existing models trained with dropout, without retraining.
- **Rules:** Check that uncertainty actually correlates with errors on validation data.
- **Guardrails:** Often underestimates uncertainty compared with ensembles (#268).

### 270. Conformal prediction

**Definition:** Turning any model's outputs into prediction sets (or intervals) with a guaranteed coverage rate, such as "the true label is in this set 90% of the time", with no assumptions about the model.

**How it works:**
1. Hold out a calibration set (not used for training).
2. Define a nonconformity score: for classification, 1 − predicted probability of the true class; for regression, |prediction − true value|.
3. Compute the scores on the calibration set. Take the (1 − α) quantile (with a small finite-sample correction).
4. **At prediction:** include every label whose score is below the threshold (classification), or output prediction ± threshold (regression).
5. **Guarantee:** coverage ≥ 1 − α on average, assuming new data is exchangeable with the calibration data.
6. Variants: adaptive sets (APS), conformalized quantile regression (intervals that adapt to input difficulty), conditional coverage per group.

**Cost:** Cheap after calibration.

**Agent use:**
- **Role:** Evaluator and Deployer.
- **How:** Honest, guaranteed uncertainty for decisions: "these 3 categories are possible", or "the forecast is 120–150 with 90% coverage". Large sets mean the case should go to a human.
- **Rules:** Recalibrate when the data distribution changes.
- **Guardrails:** The guarantee is on average, not for every subgroup. Check coverage per important segment.

## F4. Interpretability and explanation

### 271. Integrated gradients and gradient saliency

**Definition:** Attributing a prediction to input features by accumulating gradients along a path from a baseline input to the actual input.

**How it works:**
1. **Plain gradient saliency:** |∂output / ∂input|. Simple, but noisy, and suffers from saturation (gradients near zero even for important features).
2. **Integrated gradients:** choose a baseline x′ (for example a black image or zero embeddings). Attribution for feature i = (x_i − x′_i) × the average of ∂output/∂x_i along the straight path from x′ to x (approximated with 20–300 steps).
3. **Completeness:** attributions sum to output(x) − output(x′).
4. **SmoothGrad:** average gradients over noisy copies of the input to reduce noise.

**Cost:** Tens to hundreds of backward passes per explanation.

**Agent use:**
- **Role:** Analyst.
- **How:** Shows which input tokens, features or pixels drove a prediction, for debugging and reviewer explanations.
- **Rules:** Report the baseline choice. Attributions depend on it.
- **Guardrails:** Attributions show model sensitivity, not causation in the world. Don't present them as reasons a human would give.

### 272. Grad-CAM (class activation mapping)

**Definition:** A coarse heatmap showing which regions of an image a CNN used for a given class, using gradients flowing into the last convolutional layer.

**How it works:**
1. Pick the final convolutional layer's feature maps A^k.
2. Compute the gradient of the class score with respect to each feature map, and average it spatially: that's the importance weight α_k of channel k.
3. Heatmap = ReLU(Σ_k α_k A^k).
4. Upsample to the input size and overlay on the image.
5. Variants: Grad-CAM++ (better for multiple object instances), and versions for vision transformers.

**Cost:** One forward and backward pass.

**Agent use:**
- **Role:** Analyst.
- **How:** Quick visual sanity checks: is the model looking at the defect, or at a watermark, background or label in the corner (shortcut learning)?
- **Rules:** Check heatmaps on a sample of correct and incorrect predictions.
- **Guardrails:** Heatmaps are low-resolution and approximate. Use them for inspection, not as proof.

### 273. SHAP (Shapley value attribution)

**Definition:** Attributing a prediction among input features using Shapley values from cooperative game theory: each feature's average marginal contribution across all combinations of features.

**How it works:**
1. A feature's Shapley value = the weighted average, over all subsets of the other features, of how much adding that feature changes the prediction.
2. Exact computation is exponential, so approximate:
   - **KernelSHAP:** sample feature subsets and fit a weighted linear model (model-agnostic).
   - **TreeSHAP:** exact, fast computation for tree ensembles.
   - **DeepSHAP / GradientSHAP:** approximations for neural networks using backpropagation and reference inputs.
3. Missing features are filled with values from a background dataset.
4. **Properties:** contributions sum to the difference between the prediction and the average prediction.

**Cost:** From cheap (trees) to expensive (KernelSHAP on large models).

**Agent use:**
- **Role:** Analyst.
- **How:** Per-prediction explanations for tabular models (risk scores, forecasts) and global feature importance (averaging absolute SHAP values).
- **Rules:** Choose the background dataset deliberately, and report it.
- **Guardrails:** Correlated features share credit in ways that can mislead. Use explanations to investigate, not to justify decisions automatically (NR8).

### 274. Attention attribution and attention rollout

**Definition:** Using attention weights to estimate which input tokens influenced an output, with methods that account for multiple layers.

**How it works:**
1. **Raw attention:** look at one layer's attention weights. Easy, but a single layer shows only part of the information flow.
2. **Attention rollout:** combine attention across layers, by multiplying the attention matrices (each averaged with the identity, to account for residual connections) from the first layer to the last.
3. **Gradient-weighted attention:** multiply attention by its gradients with respect to the output, to keep only relevant heads and positions.
4. Display as token-level or patch-level heatmaps.

**Cost:** Cheap: attention weights are computed anyway.

**Agent use:**
- **Role:** Analyst.
- **How:** Quick inspection of which context parts a transformer used, for example which retrieved chunk an answer drew on.
- **Rules:** Cross-check with perturbation tests: remove the highlighted tokens and see if the output changes.
- **Guardrails:** Attention weights aren't reliable explanations on their own. Never present them as definitive.

### 275. Probing classifiers

**Definition:** Training small classifiers on a model's internal activations to test whether specific information (syntax, entity types, truth values, task state) is represented there.

**How it works:**
1. Collect activations from a chosen layer for inputs with known labels (for example "is this statement true").
2. Train a simple classifier (usually linear) to predict the label from the activations.
3. High accuracy means the information is linearly decodable at that layer.
4. Compare across layers to see where the information appears.
5. **Controls:** compare against probes on random features or with shuffled labels, so the probe isn't just learning the task itself.

**Cost:** Cheap.

**Agent use:**
- **Role:** Analyst.
- **How:** Understanding what a model has learned, and whether it tracks properties relevant to reliability (for example whether it internally represents "I'm uncertain").
- **Rules:** Always run control tasks and baselines.
- **Guardrails:** Decodable doesn't mean used by the model. Combine with interventions (#276).

### 276. Activation patching (causal tracing)

**Definition:** Testing which internal components cause a behavior, by replacing activations from one run with activations from another and measuring the output change.

**How it works:**
1. Two inputs: a clean one (gives the behavior, for example the correct fact) and a corrupted one (for example the subject's name replaced or noised).
2. Run the corrupted input, but **patch in** the clean run's activation at one specific location (layer, position, head or neuron).
3. Measure how much the correct output is restored.
4. Repeat for every location to map which components carry the behavior's information.
5. The reverse (patching corrupted activations into the clean run) shows which components are necessary.

**Cost:** One forward pass per patched location.

**Agent use:**
- **Role:** Analyst.
- **How:** Locating where a model stores or computes specific behaviors, before editing (#281) or for debugging failures.
- **Rules:** Choose corruption carefully. Results depend on the corruption method.
- **Guardrails:** None specific.

### 277. Sparse autoencoders for interpretable features (dictionary learning)

**Definition:** Decomposing a model's internal activations into a large set of sparse, more interpretable features.

**How it works:**
1. Collect activations (for example from the residual stream at one layer) across many inputs.
2. Train an autoencoder with a much wider hidden layer (many times the activation dimension) and a sparsity penalty (L1, or a top-k constraint), so each activation is explained by few active features.
3. Each learned feature (a decoder direction) often corresponds to an interpretable concept (a language, a topic, a code construct, a safety-relevant pattern).
4. Inspect features by their top-activating examples. Label them automatically or manually.
5. Use features to analyze or steer the model (#280).

**Cost:** Training on very many activations. Large dictionaries.

**Agent use:**
- **Role:** Analyst.
- **How:** Finding concepts the model uses, auditing for concerning internal features, and building monitors that flag when specific features activate.
- **Rules:** Measure reconstruction quality: features explaining only part of the activations give an incomplete picture.
- **Guardrails:** Feature labels are interpretations. Validate them with interventions.

### 278. Logit lens and tuned lens

**Definition:** Reading out what a transformer "currently predicts" at intermediate layers, by applying the output head to intermediate hidden states.

**How it works:**
1. **Logit lens:** take the residual stream at layer ℓ, apply the final normalization and the unembedding matrix, and look at the resulting token distribution.
2. Shows how the prediction forms over layers (when the correct answer first appears).
3. **Tuned lens:** train a small affine transform per layer that maps its hidden state into the final layer's space before unembedding. More accurate, especially for early layers.

**Cost:** Cheap.

**Agent use:**
- **Role:** Analyst.
- **How:** Diagnosing where predictions go wrong, and supports early-exit design (#262).
- **Rules:** Use the tuned lens for quantitative comparisons.
- **Guardrails:** None specific.

### 279. Circuit discovery (automated component tracing)

**Definition:** Identifying the minimal subgraph of model components (attention heads, MLP neurons and their connections) that implements a specific behavior.

**How it works:**
1. Define the task and a metric (for example the logit difference between the correct and incorrect answer).
2. Represent the model as a graph of components and connections.
3. **Automated pruning (as in ACDC):** remove (patch out, #276) connections one at a time. Keep only those whose removal noticeably hurts the metric.
4. Faster approximations use gradient-based attribution for all edges at once (attribution patching).
5. Verify that the resulting circuit alone reproduces the behavior.

**Cost:** Many forward passes (fewer with gradient approximations).

**Agent use:**
- **Role:** Analyst.
- **How:** Deep investigation of specific model behaviors, for example why a model fails a specific structured task, or how it decides to refuse.
- **Rules:** Verify faithfulness: the circuit must reproduce the behavior when isolated.
- **Guardrails:** Circuits found on narrow prompts may not generalize. Test on varied inputs.

### 280. Activation steering (steering vectors, representation engineering)

**Definition:** Changing a model's behavior at inference by adding a direction vector to its internal activations.

**How it works:**
1. **Find a direction:** take the difference between average activations on contrasting prompts (for example formal versus casual, or truthful versus untruthful), at a chosen layer. Or use a sparse autoencoder feature (#277).
2. **Steer:** during inference, add α × that direction to the activations at that layer (at all positions, or selected ones).
3. Tune α: too small does nothing; too large degrades fluency.
4. Also usable as a monitor: project activations onto the direction to read how strongly a concept is present.

**Cost:** Negligible at inference.

**Agent use:**
- **Role:** Analyst and Deployer.
- **How:** Lightweight behavior adjustments without fine-tuning, and monitors for internal states.
- **Rules:** Evaluate side effects on unrelated tasks.
- **Guardrails:** Steering can weaken safety behaviors or have unexpected effects. Run safety evaluations before any deployment (NX3).

## F5. Model editing, unlearning, privacy and security

### 281. Model editing (ROME, MEMIT)

**Definition:** Changing specific facts stored in a model (for example "the CEO of X is Y") by directly editing a few weights, without retraining.

**How it works:**
1. Locate where the fact is stored: causal tracing (#276) typically points to MLP layers in middle layers, at the subject's last token.
2. Treat the MLP's output projection as a key-value memory: the key is the subject representation, the value encodes the fact.
3. **ROME:** a rank-one update to one layer's MLP weights, so the subject's key now maps to a value producing the new fact, with minimal change for other keys.
4. **MEMIT:** spreads updates for many facts across several layers, enabling batch edits.
5. Evaluate: the edit works, generalizes to paraphrases, and doesn't change unrelated facts.

**Cost:** Seconds to minutes per edit batch.

**Agent use:**
- **Role:** Trainer.
- **How:** Quick, targeted corrections of outdated or wrong facts in deployed models.
- **Rules:** Prefer retrieval augmentation for facts that change often; editing is for rare, stable corrections.
- **Guardrails:** Edits can have side effects and may not generalize. Evaluate thoroughly, and keep the original model for rollback (NX4).

### 282. Machine unlearning

**Definition:** Removing the influence of specific training data or knowledge from a trained model, ideally as if the data had never been used.

**How it works:**
1. **Exact unlearning:** retrain without the data. Sharded training (SISA: separate models on data shards, aggregated) makes this cheaper, since only the affected shard is retrained.
2. **Approximate unlearning:** gradient ascent on the data to forget (increase its loss), balanced with continued training on retained data to preserve other abilities.
3. **Preference-based and representation-based methods:** train the model to prefer refusals or alternative answers for the target knowledge, or disrupt its internal representation.
4. **Evaluate:** forget quality (membership inference on the forgotten data, #283; question answering about it) and retained utility.

**Cost:** From cheap (approximate) to full retraining (exact).

**Agent use:**
- **Role:** Trainer.
- **How:** Responding to data removal requests and removing hazardous or licensed content from models.
- **Rules:** Document what was removed and how it was verified.
- **Guardrails:** Approximate unlearning doesn't guarantee removal: knowledge can often be recovered with fine-tuning. Don't claim more than the evaluation shows. Legal deletion obligations may require retraining.

### 283. Membership inference testing

**Definition:** Testing whether an attacker could tell if a specific example was in a model's training data, as a measure of privacy leakage.

**How it works:**
1. Models often have lower loss (higher confidence) on training examples than on unseen ones.
2. **Simple attack:** threshold the loss or confidence on a candidate example.
3. **Calibrated attacks:** compare the target model's loss with reference models trained with and without the example (likelihood ratio attacks, LiRA). Much stronger.
4. Measure the true positive rate at a low false positive rate, which matters most for privacy.

**Cost:** Reference model training (for strong attacks).

**Agent use:**
- **Role:** Evaluator.
- **How:** Privacy audits before releasing models trained on sensitive data, and evaluating unlearning (#282) and DP training (#247).
- **Rules:** Use the strongest feasible attack for audits.
- **Guardrails:** Run these tests only on your own models and data, as a defensive audit.

### 284. Watermarking generated text

**Definition:** Embedding a statistical signal in generated text that a detector can recognize, without noticeably changing quality.

**How it works:**
1. At each generation step, use a secret key and the previous token(s) to pseudo-randomly split the vocabulary into a "green" list and a "red" list.
2. Add a small bias δ to green tokens' logits before sampling, so generated text contains more green tokens than chance.
3. **Detection:** with the key, count the green tokens in a text. A z-test shows whether the count is significantly above the expected fraction.
4. Detection needs no access to the model, only the key.
5. Distortion-free variants change the sampling procedure without biasing the distribution.

**Cost:** Negligible.

**Agent use:**
- **Role:** Deployer and Evaluator.
- **How:** Tracing AI-generated content from your systems, for provenance and policy compliance.
- **Rules:** Keep keys secret and rotate them by policy.
- **Guardrails:** Paraphrasing weakens watermarks, and short texts can't be detected reliably. Never use detection results alone to accuse people.

### 285. Backdoor and data-poisoning detection (spectral signatures, activation clustering)

**Definition:** Detecting training examples that were manipulated to plant hidden triggers or corrupt a model's behavior.

**How it works:**
1. **Backdoor attacks** pair a trigger (a pattern or phrase) with a target behavior in some training examples.
2. **Spectral signatures:** for each class, compute the top singular vector of the centered feature representations. Poisoned examples tend to have large projections on it. Remove the outliers and retrain.
3. **Activation clustering:** cluster each class's activations into two groups. A small, distinct cluster suggests poisoning.
4. **Trigger reconstruction (Neural Cleanse):** for each label, search for the smallest input pattern that flips predictions to that label. An unusually small one suggests a backdoor.
5. **Data provenance checks** and deduplication reduce the risk at the source.

**Cost:** Feature extraction and clustering or SVD per class.

**Agent use:**
- **Role:** Evaluator.
- **How:** Auditing models trained on data from untrusted sources (web data, user submissions, third-party datasets).
- **Rules:** Keep data provenance records (NR1, NX2).
- **Guardrails:** Detection isn't guaranteed. Combine with source vetting.

### 286. Guard models (input and output safety classifiers)

**Definition:** Separate classifiers that screen model inputs and outputs for policy violations (harmful content, injection attempts, sensitive data) before they're processed or returned.

**How it works:**
1. Define a safety taxonomy (categories of disallowed content and actions).
2. Train or fine-tune a classifier (often a small LLM) to label prompts and responses against it, with explanations or category labels.
3. **Placement:** screen user inputs, retrieved content (injection detection, NX5), tool calls (before execution) and final outputs.
4. Thresholds per category, with policies: block, rewrite, escalate or log.
5. Evaluate on labeled test sets with precision and recall per category.

**Cost:** An extra small-model call per screened item.

**Agent use:**
- **Role:** Deployer.
- **How:** Defense in depth for agent systems: screening content that enters and leaves, especially before tool actions.
- **Rules:** Monitor false positive rates, since over-blocking harms usability.
- **Guardrails:** Guards can be bypassed. They complement (never replace) permission controls, sandboxing and human approval for risky actions.

### 287. Automated red-teaming and adversarial evaluation

**Definition:** Systematically searching for inputs that make a model behave badly, using automated generators and human experts, before attackers or users find them.

**How it works:**
1. Define the behaviors to test against (policy violations, data leaks, unsafe tool use, injection susceptibility).
2. **Generate test inputs:** templates, mutation of known failures, and attacker models trained or prompted to find failures (rewarded for success and diversity).
3. Run them against the target system, including its full agent setup (tools, retrieval).
4. Score the responses with guard models (#286) and human review.
5. Feed confirmed failures into training data, guard updates and regression suites.

**Cost:** Generation and evaluation compute, plus expert time.

**Agent use:**
- **Role:** Evaluator.
- **How:** A required gate before releasing models and agent capabilities (NR7, NX3).
- **Rules:** Run red-teaming against the complete deployed system, not just the bare model.
- **Guardrails:** Red-team artifacts (successful attack inputs) are sensitive. Restrict access to them.

## F6. Evaluation, tuning and diagnostics

### 288. Perplexity and bits per byte

**Definition:** Measures of how well a language model predicts held-out text: the exponential of the average per-token negative log-likelihood, or that loss normalized per byte.

**How it works:**
1. Compute the cross-entropy loss (#14) on held-out text, averaged per token.
2. **Perplexity** = exp(average loss). Lower is better: the model is "as uncertain as choosing among PPL equally likely tokens".
3. **Bits per byte** = total loss in bits / number of bytes of text. Comparable across models with different tokenizers (perplexity isn't).
4. Use a sliding window with overlap for long texts, so every token has enough context.

**Cost:** One forward pass over the evaluation text.

**Agent use:**
- **Role:** Evaluator.
- **How:** Tracks pretraining progress and detects regressions from quantization, pruning or merging (#251–264).
- **Rules:** Compare models with different tokenizers using bits per byte, not perplexity.
- **Guardrails:** Lower perplexity doesn't guarantee better task performance. Use task evaluations too.

### 289. Benchmark contamination detection

**Definition:** Checking whether evaluation data leaked into training data, which would make benchmark scores misleadingly high.

**How it works:**
1. **N-gram overlap:** search the training data for long n-grams (for example 13-grams) from each test example. Flag examples with significant overlap.
2. **Embedding similarity:** catch paraphrased leaks.
3. **Behavioral tests:** the model completes test questions verbatim, performance drops sharply on rephrased or newly written equivalents, or the model's likelihood of test examples is unusually high compared with similar unseen examples.
4. Report results on clean and contaminated subsets separately.

**Cost:** Large-scale n-gram search over training data (with suffix arrays or Bloom filters).

**Agent use:**
- **Role:** Evaluator.
- **How:** Making sure the agent's model comparisons and promotion gates (NR7) are valid.
- **Rules:** Keep private, versioned evaluation sets that are never published or used for training.
- **Guardrails:** Treat benchmark gains with suspicion until contamination is checked.

### 290. Population-based training (PBT)

**Definition:** Tuning hyperparameters during training by running a population of models, periodically copying the best performers and perturbing their hyperparameters.

**How it works:**
1. Start N training runs with different hyperparameters.
2. Every few steps, evaluate each run.
3. **Exploit:** poorly performing runs copy the weights and hyperparameters of better runs.
4. **Explore:** perturb the copied hyperparameters (for example multiply by 0.8 or 1.2).
5. The result is a hyperparameter schedule (learning rate, augmentation strength) that changes over training, found in one combined run.

**Cost:** N parallel runs, but no repeated full training cycles.

**Agent use:**
- **Role:** Trainer.
- **How:** Tuning schedules and hyperparameters in one pass, especially for RL and long training runs.
- **Rules:** Record the final hyperparameter schedule for reproducibility (NR1).
- **Guardrails:** Can overfit to the validation metric used for selection. Keep a separate test set.

### 291. Hyperband and ASHA (early-stopping hyperparameter search)

**Definition:** Hyperparameter search that starts many configurations with small budgets, and repeatedly continues only the best ones with larger budgets.

**How it works:**
1. **Successive halving:** train n configurations for a small budget (steps, epochs or data). Keep the top 1/η (for example the top third), give them η× more budget. Repeat until one remains.
2. **Hyperband:** run successive halving several times with different starting trade-offs between the number of configurations and the initial budget, which hedges against slow starters.
3. **ASHA:** an asynchronous version: promote a configuration as soon as it ranks in the top fraction of its level, so workers never wait.
4. Can be combined with Bayesian sampling of configurations (BOHB).

**Cost:** Much less than full training of every configuration.

**Agent use:**
- **Role:** Trainer.
- **How:** Efficient tuning under a compute budget (NR5, NX1).
- **Rules:** Low budgets must correlate with final performance. Check on a few full runs.
- **Guardrails:** Settings that start slowly (such as small learning rates) get stopped early. Hyperband's brackets reduce this risk.

### 292. Stochastic weight averaging (SWA)

**Definition:** Averaging model weights from several points late in training (with a constant or cyclic learning rate), which finds flatter solutions and better generalization.

**How it works:**
1. Train normally for most of the run.
2. In the final phase, use a constant or cyclic learning rate (#44).
3. Average the weights collected at regular intervals (for example the end of each epoch or cycle).
4. Recompute BatchNorm statistics for the averaged weights (#51) with a pass over training data.
5. Related: EMA (#42) and checkpoint averaging for LLMs.

**Cost:** One extra copy of the weights.

**Agent use:**
- **Role:** Trainer.
- **How:** Cheap generalization improvement for most supervised training.
- **Rules:** Always recompute normalization statistics after averaging, if BatchNorm is used.
- **Guardrails:** None specific.

### 293. Training dynamics monitoring

**Definition:** Tracking signals during training that reveal problems before they ruin a run: gradient norms, update-to-weight ratios, activation statistics, dead units and throughput.

**How it works:**
1. **Losses:** training and validation, with smoothing. A widening gap means overfitting.
2. **Gradient norms:** per layer and global. Spikes signal instability (#242); near-zero norms signal vanishing gradients (#28).
3. **Update-to-weight ratio:** ‖update‖ / ‖weights‖ per layer, typically around 10⁻³. Much larger means the learning rate is too high; much smaller means layers barely learn.
4. **Activations:** mean, variance, fraction of dead ReLUs (#4), attention entropy (collapse), and logit magnitudes.
5. **System metrics:** throughput (tokens or samples per second), GPU utilization, data-loader wait time and memory use.

**Cost:** Small overhead.

**Agent use:**
- **Role:** Trainer and Analyst.
- **How:** Automated alerts on these metrics (NR4) catch problems early, before compute is wasted.
- **Rules:** Log these signals for every run in a standard format, so runs are comparable.
- **Guardrails:** None specific.

### 294. Sanity checks (overfit one batch, initial loss check, gradient flow)

**Definition:** Quick tests before any long training run that catch most implementation bugs.

**How it works:**
1. **Initial loss check:** at initialization, a classifier's loss should be about log(number of classes). Very different values mean a bug in initialization or the loss.
2. **Overfit one batch:** training on a single small batch should drive the loss to almost zero. If it doesn't, something is broken (labels, loss, gradients, frozen layers).
3. **Gradient flow:** every trainable parameter should receive a nonzero gradient. Find detached or unused components.
4. **Data checks:** visualize a few training batches after preprocessing and augmentation. Verify labels match inputs.
5. **Zero-input baseline:** with inputs zeroed out, performance should drop to chance. Otherwise labels may be leaking.

**Cost:** Minutes.

**Agent use:**
- **Role:** Trainer.
- **How:** A required pre-flight checklist before any significant training run (NR5).
- **Rules:** Automate these checks in the training pipeline.
- **Guardrails:** None specific.

### 295. Reproducibility and determinism in training

**Definition:** Making training and evaluation results repeatable: same inputs, same results, or at least within a known tolerance.

**How it works:**
1. **Seeds:** set the random seeds for every library and every worker, including data-loader workers.
2. **Deterministic kernels:** some GPU operations (atomic additions in some backward kernels) are nondeterministic. Enable deterministic modes, accepting some slowdown.
3. **Data order:** record the shuffle seed and the data-loader position (#241).
4. **Environment:** pin library versions, drivers and hardware type, since results differ across them.
5. **Inference:** batch composition can change results slightly (different kernel paths). Use batch-invariant kernels where exact reproducibility is required.
6. When exact reproducibility isn't possible, report variance across several seeds.

**Cost:** Some speed loss in deterministic modes.

**Agent use:**
- **Role:** Trainer and Evaluator.
- **How:** Makes comparisons valid (NR6): an improvement smaller than the variance across seeds isn't a real improvement.
- **Rules:** Report the mean and spread over several seeds for important comparisons.
- **Guardrails:** None specific.

### 296. Learning curves and data scaling estimation

**Definition:** Measuring how performance changes with the amount of training data, to predict whether more data (or a bigger model) is worth collecting.

**How it works:**
1. Train on increasing data subsets (for example 10%, 20%, 40%, 80%, 100%), with the same evaluation set.
2. Plot error against data size. Typically it follows a power law in the middle region, flattening toward a floor (irreducible error).
3. Fit the curve, and extrapolate to estimate the gain from more data.
4. Compare training and validation curves: a large gap (overfitting) suggests more data or regularization; both errors high (underfitting) suggests a bigger model.

**Cost:** Several training runs on subsets.

**Agent use:**
- **Role:** Evaluator and Trainer.
- **How:** Decides between collecting more labels, changing the model or stopping (NR5): "doubling labeled data would reduce errors by about X%".
- **Rules:** Use several seeds per point for stable curves.
- **Guardrails:** Extrapolation is uncertain beyond the measured range.

### 297. Learning with noisy labels (co-teaching, loss correction)

**Definition:** Training methods that limit the damage from incorrectly labeled examples.

**How it works:**
1. **Small-loss trick:** networks learn clean, easy examples first, so examples with large loss early in training are more likely mislabeled.
2. **Co-teaching:** train two networks at once. Each selects its small-loss examples to train the other network, which prevents either from confirming its own mistakes.
3. **Loss correction:** estimate the label noise transition matrix (the probability that true class i is labeled j), and adjust the loss with it.
4. **Robust losses:** generalized cross-entropy and symmetric cross-entropy are less sensitive to wrong labels.
5. **Confident learning:** flag examples whose predicted probabilities strongly disagree with their labels, for review or removal.

**Cost:** Modest overhead (two networks for co-teaching).

**Agent use:**
- **Role:** Trainer.
- **How:** Datasets labeled cheaply (heuristics, weak supervision, crowdsourcing, user feedback) contain noise. These methods train well anyway, and help find labels to fix.
- **Rules:** Route flagged examples to human review rather than silently dropping them.
- **Guardrails:** Rare but correct examples can look like noise. Check flagged minority-class examples carefully.

### 298. Class imbalance handling (reweighting, resampling, logit adjustment)

**Definition:** Methods that keep models from ignoring rare classes when some classes vastly outnumber others.

**How it works:**
1. **Reweighting:** weight the loss of each class by the inverse of its frequency (or by the "effective number" of samples, to avoid over-weighting).
2. **Resampling:** oversample rare classes or undersample common ones in batches.
3. **Logit adjustment:** add τ × log(class prior) to the logits during training (or subtract it at inference). Gives balanced error with theoretical grounding.
4. **Decoupled training:** learn features with natural sampling, then retrain only the classifier head with balanced sampling.
5. **Evaluate** with balanced accuracy, per-class recall, and precision-recall curves, not plain accuracy.

**Cost:** Negligible.

**Agent use:**
- **Role:** Trainer.
- **How:** Rare-event tasks: fraud, failures, critical tickets, rare document types.
- **Rules:** Choose thresholds per class on validation data with the business cost of each error type.
- **Guardrails:** Prior shift between training and production changes the right adjustment. Monitor class frequencies in production.

### 299. Test-time augmentation and test-time adaptation (TENT)

**Definition:** Improving predictions at inference by averaging over augmented versions of the input (augmentation), or by adapting a few parameters to the incoming test data (adaptation).

**How it works:**
1. **Test-time augmentation:** create several augmented versions of each input (flips, crops, scales), predict on each, and average the predictions. Often a small accuracy gain and better calibration.
2. **TENT (test-time entropy minimization):** for a batch of test inputs, update only the normalization layers' scale and shift parameters to minimize prediction entropy. This adapts to distribution shifts (new camera, new lighting, new data source) without labels.
3. Reset or limit adaptation over time to avoid drift.

**Cost:** Test-time augmentation multiplies inference cost. TENT adds a backward pass on small parameter sets.

**Agent use:**
- **Role:** Deployer.
- **How:** Robustness when production inputs differ from training data, and quick accuracy gains for offline batch processing.
- **Rules:** Monitor accuracy on labeled samples when adapting online.
- **Guardrails:** Unsupervised adaptation can drift into confident errors. Keep the original model for reset (NX4).

### 300. Once-for-all and elastic networks (slimmable models)

**Definition:** Training one network that contains many smaller subnetworks (fewer layers, narrower layers, smaller kernels), so a fitting model can be extracted for each hardware target without retraining.

**How it works:**
1. Train the largest network first.
2. **Progressive shrinking:** then train sampled subnetworks with smaller depth, width and kernel size, sharing weights with the large network, often with distillation from the large network (#225).
3. Each subnetwork's weights are taken directly from the shared network.
4. **Deployment:** search (or look up) the best subnetwork for each device's latency and memory constraints, using accuracy and latency predictors.
5. **Slimmable networks:** the same idea for width only, switchable at runtime.

**Cost:** One expensive training run, then nearly free specialization for many targets.

**Agent use:**
- **Role:** Deployer.
- **How:** Serving the same capability on many device classes (servers, laptops, phones, edge boxes), or adjusting model size at runtime to load.
- **Rules:** Evaluate each extracted subnetwork before deployment (NR7).
- **Guardrails:** Smaller subnetworks may behave differently on safety-relevant inputs. Evaluate each separately (NX3).

---
