# Part 2: Normalization, regularization, convolutional networks, detection and recurrent models (#51–100)

Same format and the same contract (roles; rules NR1–NR8; guardrails NX1–NX5).

## B1. Normalization

### 51. Batch normalization

**Definition:** Normalizing each feature (channel) to zero mean and unit variance over the current mini-batch, then applying a learned scale and shift.

**How it works:**
1. For each channel, compute the mean and variance over the batch (and the spatial positions, for CNNs).
2. Normalize: x̂ = (x − mean) / √(variance + ε).
3. Scale and shift: y = γ x̂ + β, with learned γ and β.
4. **Training** uses batch statistics. **Inference** uses running averages accumulated during training.
5. Allows higher learning rates, and stabilizes and speeds up CNN training.

**Cost:** O(elements). Needs synchronization across devices for "sync BatchNorm".

**Agent use:**
- **Role:** Architect.
- **How:** The standard normalization for CNNs with reasonable batch sizes.
- **Rules:** Put the model in evaluation mode for inference, so running statistics are used.
- **Guardrails:** Small batches (under about 16) give noisy statistics. Use GroupNorm (#54) instead. Train/inference mismatch is a classic silent bug: test both modes.

### 52. Layer normalization

**Definition:** Normalizing across the features of each individual example, independent of the batch.

**How it works:**
1. For each example (each token, in transformers), compute the mean and variance across its feature dimension.
2. Normalize, then apply a learned per-feature scale γ and shift β.
3. Identical behavior in training and inference, with no batch dependence.
4. Works with any batch size and variable-length sequences.

**Cost:** O(features) per example.

**Agent use:**
- **Role:** Architect.
- **How:** The standard normalization in transformers and RNNs.
- **Rules:** Compute statistics in FP32 even during mixed-precision training (#231).
- **Guardrails:** None specific.

### 53. RMSNorm

**Definition:** A simplified layer normalization that only rescales by the root mean square, without centering (no mean subtraction, no bias).

**How it works:**
1. RMS = √(mean of x² + ε) over the features.
2. y = γ × x / RMS.
3. Removes the mean computation and the bias parameter.
4. About as effective as LayerNorm in practice, and slightly faster.

**Cost:** Cheaper than LayerNorm.

**Agent use:**
- **Role:** Architect.
- **How:** The usual normalization in modern LLMs.
- **Rules:** Match the pretrained model's choice when fine-tuning.
- **Guardrails:** None specific.

### 54. Group normalization and instance normalization

**Definition:** Normalizing over groups of channels (GroupNorm) or each channel separately (InstanceNorm), per example, so results don't depend on the batch size.

**How it works:**
1. **GroupNorm:** split the channels into G groups. Compute the mean and variance over each group's channels and spatial positions, per example.
2. **InstanceNorm:** G = number of channels (each channel alone). Removes per-image contrast and style, which suits style transfer.
3. **LayerNorm** is the case G = 1.
4. Learned scale and shift per channel.

**Cost:** O(elements).

**Agent use:**
- **Role:** Architect.
- **How:** CNNs trained with small batches (detection, segmentation, high-resolution images), and diffusion U-Nets (#79, #166).
- **Rules:** G = 32 is a common default.
- **Guardrails:** None specific.

### 55. Weight normalization and spectral normalization

**Definition:** Normalizing the weights themselves rather than the activations: separating direction from magnitude (weight norm), or limiting the largest singular value (spectral norm).

**How it works:**
1. **Weight normalization:** w = g × v / ‖v‖. Learn the direction v and the scale g separately, which often eases optimization.
2. **Spectral normalization:** divide W by its largest singular value σ(W), estimated cheaply with one power iteration per step.
3. That bounds each layer's Lipschitz constant (how much it can amplify changes in its input).
4. Spectral normalization stabilizes GAN discriminators (#154) and helps robustness.

**Cost:** One power iteration per layer per step for spectral normalization.

**Agent use:**
- **Role:** Architect.
- **How:** Stabilizes adversarial training (GANs), and constrains sensitivity for robustness-critical models.
- **Rules:** Use spectral normalization in GAN discriminators by default.
- **Guardrails:** None specific.

### 56. Normalization placement (pre-norm, post-norm, sandwich, DeepNorm)

**Definition:** Where normalization sits relative to residual connections in a transformer block, which strongly affects training stability.

**How it works:**
1. **Post-norm** (original transformer): x ← Norm(x + F(x)). Often better final quality, but unstable for deep models without careful warmup.
2. **Pre-norm:** x ← x + F(Norm(x)). The residual path is clean, so training is stable even very deep. The standard in modern LLMs.
3. **Sandwich norm:** normalize both before and after F.
4. **DeepNorm:** post-norm with up-scaled residual and down-scaled initialization, enabling very deep post-norm models.
5. Pre-norm models need a final normalization before the output head.

**Cost:** None, or one extra normalization.

**Agent use:**
- **Role:** Architect.
- **How:** Uses pre-norm by default for new transformers, for stable training.
- **Rules:** Record the placement in the architecture config (NR1).
- **Guardrails:** Changing placement in a pretrained model breaks it. Never change it when fine-tuning.

### 57. QK-norm and logit soft-capping

**Definition:** Stabilization techniques for large transformers: normalizing attention queries and keys, and smoothly limiting the size of logits.

**How it works:**
1. **QK-norm:** apply LayerNorm or RMSNorm to queries and keys before their dot product. Prevents attention logits from growing too large, which otherwise causes attention collapse and loss spikes.
2. **Logit soft-capping:** logits ← c × tanh(logits / c). Smoothly limits the values to (−c, c), in attention scores and/or final output logits.
3. Both reduce the risk of numerical overflow and training divergence at scale.

**Cost:** Negligible.

**Agent use:**
- **Role:** Architect.
- **How:** Used in large-scale or high-learning-rate training to prevent instability (#242).
- **Rules:** Keep the same settings at inference as in training.
- **Guardrails:** Some fast attention kernels don't support soft-capping. Check kernel compatibility (#116).

## B2. Regularization and augmentation

### 58. Dropout

**Definition:** Randomly zeroing a fraction of activations during training, so the network can't rely on any single unit.

**How it works:**
1. During training, each activation is kept with probability 1 − p and zeroed with probability p.
2. **Inverted dropout:** kept activations are divided by (1 − p), so the expected value is unchanged and inference needs no scaling.
3. At inference, dropout is off.
4. It acts like training an ensemble of thinned networks.
5. Typical p: 0.1 in transformers, 0.2–0.5 in MLPs. Large pretraining runs often use 0.

**Cost:** Negligible.

**Agent use:**
- **Role:** Trainer.
- **How:** Regularizes small-data training and fine-tuning. Also used for uncertainty estimation (#269).
- **Rules:** Make sure inference runs in evaluation mode.
- **Guardrails:** Dropout left on at inference gives random outputs. Test for deterministic outputs (#295).

### 59. Stochastic depth (DropPath)

**Definition:** Randomly skipping entire residual blocks during training, so each block's output is sometimes replaced by its input.

**How it works:**
1. For each residual block and each example, keep the branch with probability 1 − p and drop it with probability p (output = input only).
2. Scale kept branches by 1/(1 − p).
3. Usually p increases linearly with depth (deeper blocks dropped more often).
4. Shortens the effective depth during training, reduces overfitting, and speeds training slightly.

**Cost:** Saves some compute in training.

**Agent use:**
- **Role:** Trainer.
- **How:** A standard regularizer for vision transformers and deep CNNs.
- **Rules:** Typical maximum rate: 0.1–0.5, increasing with model size.
- **Guardrails:** None specific.

### 60. Early stopping and checkpoint selection

**Definition:** Stopping training (or choosing the checkpoint) when validation performance stops improving.

**How it works:**
1. Evaluate on a validation set every N steps.
2. Keep the checkpoint with the best validation metric.
3. Stop when there's no improvement for a "patience" number of evaluations.
4. Optionally average the last few or best few checkpoints.

**Cost:** The cost of validation runs.

**Agent use:**
- **Role:** Trainer.
- **How:** Prevents overfitting and wasted compute (NX1).
- **Rules:** Use a validation set separate from the final test set (NR3). Selecting on the test set inflates results.
- **Guardrails:** Noisy validation metrics trigger early stops by chance. Smooth them, or use enough patience.

### 61. Image data augmentation (geometric, photometric, RandAugment)

**Definition:** Creating varied training examples by transforming images in ways that don't change their label.

**How it works:**
1. **Geometric:** random crops, flips, rotations, scaling, translation.
2. **Photometric:** brightness, contrast, color jitter, blur, noise.
3. **RandAugment:** pick N transforms at random from a list, each applied with magnitude M. Only two hyperparameters to tune (unlike AutoAugment's learned policies).
4. **Random erasing / Cutout:** blank out random patches.
5. Augmentation happens on the fly during data loading.

**Cost:** CPU or GPU time in the data pipeline.

**Agent use:**
- **Role:** Trainer.
- **How:** Improves generalization, especially with limited data.
- **Rules:** Only use transforms that preserve the label (horizontal flips are wrong for text images and some medical images).
- **Guardrails:** Make sure the data loader isn't the bottleneck (#293). Augmentations must not leak into the evaluation pipeline.

### 62. Mixup and CutMix

**Definition:** Training on blends of two examples (and their labels): a pixel-wise blend (Mixup) or a pasted patch from one image into another (CutMix).

**How it works:**
1. **Mixup:** x = λ x₁ + (1 − λ) x₂, y = λ y₁ + (1 − λ) y₂, with λ drawn from a Beta distribution.
2. **CutMix:** cut a rectangle from x₂ and paste it into x₁. The label mixes by area: λ = the remaining area of x₁.
3. Smooths decision boundaries, reduces overconfidence and improves robustness.
4. Often both are used, alternating per batch.

**Cost:** Negligible.

**Agent use:**
- **Role:** Trainer.
- **How:** Standard regularization for image classifiers trained from scratch.
- **Rules:** Use soft-label cross-entropy, not hard labels.
- **Guardrails:** It affects calibration measurements. Evaluate on unmixed data.

### 63. Adversarial training (FGSM, PGD)

**Definition:** Training on inputs deliberately perturbed to fool the model, to make it robust against small adversarial changes.

**How it works:**
1. **FGSM:** perturb the input by ε × sign(∂Loss/∂input): one step in the direction that increases the loss most.
2. **PGD:** several small steps of that kind, projecting back into the allowed perturbation range (an ε-ball) after each. A stronger attack.
3. **Adversarial training:** at each step, generate perturbed inputs with PGD and train on them (optionally mixed with clean examples).
4. **TRADES:** balances clean accuracy and robustness with a KL term between clean and adversarial predictions.

**Cost:** Several extra forward and backward passes per step (about 3–10× training cost).

**Agent use:**
- **Role:** Trainer and Evaluator.
- **How:** Hardens models where adversaries exist: spam, fraud and abuse classifiers. Evaluators use PGD to measure robustness.
- **Rules:** Report clean accuracy and robust accuracy together.
- **Guardrails:** Robustness against one attack doesn't imply robustness against others. Evaluate with several, including adaptive attacks.

### 64. Consistency regularization and pseudo-labeling (FixMatch)

**Definition:** Semi-supervised learning: train the model to give the same prediction on differently augmented versions of unlabeled data, using its own confident predictions as targets.

**How it works:**
1. For each unlabeled example, make a weakly augmented version (flip, crop) and a strongly augmented one (RandAugment, Cutout).
2. Predict on the weak version. If the top class probability exceeds a threshold (for example 0.95), use that class as a pseudo-label.
3. Train the strongly augmented version to predict the pseudo-label.
4. Combine with ordinary supervised loss on labeled data.
5. Uses a large amount of unlabeled data with few labels.

**Cost:** Extra forward passes on unlabeled data.

**Agent use:**
- **Role:** Trainer.
- **How:** When labels are expensive and unlabeled data is plentiful: support tickets, logs, documents.
- **Rules:** Keep a labeled validation set to monitor pseudo-label quality (NR3).
- **Guardrails:** Confirmation bias: wrong confident pseudo-labels reinforce themselves. Monitor class balance and accuracy over time.

### 65. SpecAugment (audio augmentation)

**Definition:** Augmenting speech data directly on its spectrogram by masking blocks of time steps and frequency bands.

**How it works:**
1. Convert audio to a log-mel spectrogram.
2. **Frequency masking:** zero out a random range of consecutive frequency channels.
3. **Time masking:** zero out a random range of consecutive time steps.
4. **Time warping:** (optionally) slightly stretch or squeeze the spectrogram along time.
5. Applied on the fly during training.

**Cost:** Negligible.

**Agent use:**
- **Role:** Trainer.
- **How:** Standard regularization for speech recognition and audio classification.
- **Rules:** Tune the mask sizes to the dataset's audio length.
- **Guardrails:** None specific.

### 66. Text augmentation (back-translation, token-level noise)

**Definition:** Creating varied text training examples while preserving meaning.

**How it works:**
1. **Back-translation:** translate to another language and back, giving paraphrases.
2. **Token-level operations:** synonym replacement, random insertion, deletion or swapping (EDA).
3. **Masked-language-model replacement:** mask some words and fill them with a pretrained model's predictions.
4. **Noise injection:** typos, casing changes, whitespace changes, for robustness to messy input.

**Cost:** Back-translation needs model inference. Token operations are cheap.

**Agent use:**
- **Role:** Trainer.
- **How:** Expands small labeled text datasets (intent classification, routing, extraction) and builds robustness to real-world input noise.
- **Rules:** Spot-check augmented examples for label preservation.
- **Guardrails:** Augmentation can change meaning ("not" deleted). Exclude negation and key entities from random edits.

## B3. Convolutional networks

### 67. Convolution operation (kernels, stride, padding, channels)

**Definition:** Sliding small learned filters over an input grid (image, audio, sequence), computing weighted sums at each position.

**How it works:**
1. A kernel of size k × k × C_in produces one output channel. C_out kernels produce C_out channels.
2. At each position, output = Σ of kernel weights × input patch + bias.
3. **Stride:** the step between positions (stride 2 halves the resolution). **Padding:** adds borders so the output size can match the input.
4. Weight sharing (the same kernel everywhere) gives translation equivariance and far fewer parameters than a dense layer.
5. Stacking layers grows the receptive field (#83).

**Cost:** O(H × W × k² × C_in × C_out) per layer.

**Agent use:**
- **Role:** Architect.
- **How:** The base operation for images, spectrograms and some sequence tasks.
- **Rules:** Compute output shapes and compute cost per layer before training (NR5).
- **Guardrails:** None specific.

### 68. Fast convolution algorithms (im2col + GEMM, Winograd, FFT)

**Definition:** Implementation methods that make convolutions fast on real hardware.

**How it works:**
1. **im2col:** unfold every input patch into a column, then compute the whole convolution as one large matrix multiplication (GEMM). Uses highly optimized matrix libraries, at the cost of extra memory.
2. **Implicit GEMM:** the same idea without materializing the unfolded matrix.
3. **Winograd:** for small kernels (3×3), algebraic transforms reduce the number of multiplications (about 2.25× fewer for 3×3).
4. **FFT convolution:** convolution becomes elementwise multiplication in the frequency domain. Efficient for large kernels.
5. Libraries (cuDNN, oneDNN) pick an algorithm per layer by benchmarking.

**Cost:** Depends on the algorithm. Auto-tuning picks the fastest per shape.

**Agent use:**
- **Role:** Deployer.
- **How:** Enabling the library's auto-tuning, and keeping shapes and layouts friendly to fast algorithms, often gives large speedups.
- **Rules:** Benchmark with production input shapes.
- **Guardrails:** Some fast algorithms have slightly different numerical results. Validate the accuracy after switching.

### 69. Pooling (max, average, global)

**Definition:** Downsampling feature maps by summarizing small regions.

**How it works:**
1. **Max pooling:** take the maximum in each window (for example 2×2, stride 2). Keeps the strongest activations.
2. **Average pooling:** take the mean.
3. **Global average pooling:** average each channel over the whole map, giving one value per channel. Used before classifier heads, replacing large dense layers.
4. Adds some translation invariance and reduces compute for later layers.
5. Modern networks often use strided convolutions instead of pooling.

**Cost:** O(elements).

**Agent use:**
- **Role:** Architect.
- **How:** Global average pooling makes classifiers work with variable input sizes.
- **Rules:** None specific.
- **Guardrails:** None specific.

### 70. Dilated (atrous) convolution

**Definition:** Convolution with gaps between kernel elements, which enlarges the receptive field without more parameters or lower resolution.

**How it works:**
1. With dilation rate r, kernel elements are applied r positions apart.
2. A 3×3 kernel with dilation 2 covers a 5×5 area.
3. Stacking layers with dilations 1, 2, 4, 8… grows the receptive field exponentially with depth.
4. **Atrous spatial pyramid pooling (ASPP):** parallel dilated convolutions at several rates, capturing context at several scales.

**Cost:** Same as a normal convolution with the same kernel size.

**Agent use:**
- **Role:** Architect.
- **How:** Segmentation (keeping full resolution with wide context), and audio and time series (#100).
- **Rules:** Mix dilation rates to avoid "gridding" artifacts (gaps in coverage).
- **Guardrails:** None specific.

### 71. Depthwise separable convolution

**Definition:** Splitting a standard convolution into a per-channel spatial convolution followed by a 1×1 convolution that mixes channels, cutting compute dramatically.

**How it works:**
1. **Depthwise:** apply one k×k filter per input channel separately (no mixing between channels).
2. **Pointwise:** a 1×1 convolution mixes the channels into the output channels.
3. Cost ratio compared to standard convolution ≈ 1/C_out + 1/k², often 8–9× fewer operations for 3×3 kernels.

**Cost:** O(H × W × C_in × (k² + C_out)).

**Agent use:**
- **Role:** Architect.
- **How:** Efficient models for mobile, edge and CPU inference (#76).
- **Rules:** Depthwise layers are memory-bound on GPUs. Measure the actual latency, not just operation counts.
- **Guardrails:** None specific.

### 72. Transposed convolution and learned upsampling (pixel shuffle)

**Definition:** Increasing spatial resolution with learned layers, used in decoders and generators.

**How it works:**
1. **Transposed convolution:** the gradient operation of a strided convolution, used forward to upsample. Each input value spreads into a k×k output region.
2. **Checkerboard artifacts** appear when the kernel size isn't divisible by the stride (uneven overlap).
3. **Alternative:** nearest or bilinear resize followed by a normal convolution (avoids artifacts).
4. **Pixel shuffle (sub-pixel convolution):** produce r² × C channels at low resolution, then rearrange them into an r× larger map with C channels. Efficient and artifact-free.

**Cost:** Similar to the corresponding convolution.

**Agent use:**
- **Role:** Architect.
- **How:** Segmentation decoders (#79), super-resolution and image generators.
- **Rules:** Prefer resize + convolution or pixel shuffle for visual quality.
- **Guardrails:** None specific.

### 73. 1×1 convolutions and bottleneck blocks

**Definition:** Convolutions with 1×1 kernels that mix channels at each position, used to shrink and expand channel counts cheaply.

**How it works:**
1. A 1×1 convolution is a linear layer applied independently at every position across channels.
2. **Bottleneck:** reduce the channels with 1×1 (for example 256 → 64), do the expensive 3×3 convolution on fewer channels, then expand back with 1×1 (64 → 256).
3. Large compute savings with little quality loss.

**Cost:** O(H × W × C_in × C_out).

**Agent use:**
- **Role:** Architect.
- **How:** Controls compute in deep CNNs, and adapts channel counts between stages (projection shortcuts, #74).
- **Rules:** None specific.
- **Guardrails:** None specific.

### 74. Residual network (ResNet) blocks

**Definition:** The CNN architecture built from residual blocks, which made very deep networks trainable.

**How it works:**
1. **Basic block:** two 3×3 convolutions with normalization and ReLU, plus a residual connection (#10).
2. **Bottleneck block:** 1×1 reduce → 3×3 → 1×1 expand, plus a residual connection (#73).
3. **Downsampling:** a strided convolution in the main path, with a projection (1×1 strided) on the shortcut to match shapes.
4. Stages of blocks with increasing channels and decreasing resolution.
5. Variants: ResNeXt (grouped convolutions), Wide ResNet (wider, shallower).

**Cost:** ResNet-50: about 4 GFLOPs per 224×224 image.

**Agent use:**
- **Role:** Architect.
- **How:** A reliable, well-understood baseline for vision tasks, and a common backbone for detection and segmentation (NR2).
- **Rules:** Start from pretrained weights for small datasets.
- **Guardrails:** None specific.

### 75. Inception (multi-branch) modules

**Definition:** Blocks that run several convolution sizes in parallel and concatenate their outputs, capturing features at several scales.

**How it works:**
1. Parallel branches: 1×1, 3×3, 5×5 (often factorized as two 3×3) convolutions and pooling.
2. 1×1 bottlenecks before the expensive branches keep compute in check (#73).
3. Concatenate the branch outputs along the channel dimension.
4. Later versions factorize n×n convolutions into 1×n and n×1.

**Cost:** Controlled by the bottleneck widths.

**Agent use:**
- **Role:** Architect.
- **How:** The multi-branch idea (several receptive field sizes at once) recurs in many modern designs, such as feature pyramids and ASPP (#70, #80).
- **Rules:** None specific.
- **Guardrails:** None specific.

### 76. Inverted residuals with linear bottlenecks (MobileNetV2)

**Definition:** An efficient block that expands channels, applies a depthwise convolution, then projects back down, with the residual connection between the narrow layers.

**How it works:**
1. 1×1 expansion (for example 6× the channels), with ReLU6.
2. 3×3 depthwise convolution (#71), with ReLU6.
3. 1×1 projection back to few channels, without an activation (a linear bottleneck), since nonlinearities in narrow layers destroy information.
4. Residual connection between the narrow input and output when shapes match.

**Cost:** Very low compute per block.

**Agent use:**
- **Role:** Architect.
- **How:** The basis of efficient on-device vision models.
- **Rules:** Measure latency on the target device.
- **Guardrails:** None specific.

### 77. Squeeze-and-excitation and channel/spatial attention modules (SE, CBAM)

**Definition:** Small modules that learn to reweight channels (and, in CBAM, spatial positions) according to global context.

**How it works:**
1. **Squeeze:** global average pooling gives one value per channel.
2. **Excitation:** a small two-layer MLP (with a reduction ratio, for example 16) and sigmoid produce a weight per channel.
3. **Scale:** multiply each channel by its weight.
4. **CBAM** adds spatial attention: pool across channels, convolve, sigmoid, and reweight positions.
5. Insert them inside residual blocks.

**Cost:** A small number of extra parameters and operations.

**Agent use:**
- **Role:** Architect.
- **How:** Cheap accuracy gains for CNNs. The gating idea appears in many architectures.
- **Rules:** Benchmark the added latency on the target hardware.
- **Guardrails:** None specific.

### 78. Compound model scaling (EfficientNet)

**Definition:** Scaling a network's depth, width and input resolution together, in fixed proportions, for the best accuracy per unit of compute.

**How it works:**
1. Start with a good small base network (found by architecture search).
2. Scale depth by α^φ, width by β^φ, and resolution by γ^φ, with α × β² × γ² ≈ 2, so each step of φ roughly doubles the compute.
3. Find α, β and γ by a small grid search at φ = 1, then reuse them for larger φ.
4. Balanced scaling beats scaling a single dimension.

**Cost:** Grows about 2^φ.

**Agent use:**
- **Role:** Architect.
- **How:** A principled way to pick model size for a compute budget (NR5).
- **Rules:** Measure real latency. Depthwise-heavy models can be slower than their operation counts suggest.
- **Guardrails:** None specific.

### 79. U-Net (encoder-decoder with skip connections)

**Definition:** An architecture that downsamples to capture context, then upsamples to full resolution, with skip connections that pass fine details from encoder to decoder.

**How it works:**
1. **Encoder:** convolution blocks with downsampling, increasing channels.
2. **Bottleneck** at the lowest resolution.
3. **Decoder:** upsampling (#72), concatenating the encoder features at the same resolution, then convolutions.
4. The output has the input's resolution: per-pixel predictions.
5. Widely used in segmentation and as the denoising network in diffusion models (#161, #166).

**Cost:** Moderate. Memory use is high at full resolution.

**Agent use:**
- **Role:** Architect.
- **How:** Per-pixel tasks: segmentation, restoration, denoising, document layout masks.
- **Rules:** Use overlap-dice losses for small regions (#21).
- **Guardrails:** Memory limits for large images. Use tiling with overlapping borders.

### 80. Feature pyramid networks (FPN)

**Definition:** Combining feature maps from several network depths into a pyramid where every level has both strong semantics and appropriate resolution.

**How it works:**
1. Take feature maps from several backbone stages (high resolution but semantically weak at early stages; low resolution but strong at late stages).
2. **Top-down path:** upsample the deeper maps and add them to the earlier ones (after 1×1 projection).
3. Smooth each merged map with a 3×3 convolution.
4. Run detection or segmentation heads at each pyramid level, with each level handling objects of a matching size.

**Cost:** Moderate overhead on top of the backbone.

**Agent use:**
- **Role:** Architect.
- **How:** Standard in detection and segmentation where objects vary greatly in size.
- **Rules:** Match the anchor or object sizes to the pyramid levels.
- **Guardrails:** None specific.

### 81. ConvNeXt (modernized CNN design)

**Definition:** A pure convolutional network redesigned with transformer-era choices, matching vision transformers on many benchmarks.

**How it works:**
1. "Patchify" stem: a 4×4 convolution with stride 4.
2. Large 7×7 depthwise convolutions (#71).
3. Inverted bottleneck (expand 4× with 1×1 convolutions, #76) with GELU (#5).
4. LayerNorm instead of BatchNorm, and fewer activations and normalizations per block.
5. Separate downsampling layers between stages.
6. Trained with modern recipes: AdamW, heavy augmentation, stochastic depth.

**Cost:** Similar to vision transformers of comparable size.

**Agent use:**
- **Role:** Architect.
- **How:** A strong vision backbone with efficient convolution kernels, which suits high-resolution and dense prediction tasks.
- **Rules:** Use the published training recipe. The design depends on it.
- **Guardrails:** None specific.

### 82. Deformable convolution

**Definition:** Convolution where each sampling position gets a learned offset, so the kernel adapts its shape to the content.

**How it works:**
1. A small convolution predicts 2D offsets for each kernel position (and, in v2, a modulation weight).
2. Sample the input at the shifted, fractional positions with bilinear interpolation.
3. Apply the kernel weights to those samples.
4. The receptive field adapts to object shapes and scales.

**Cost:** More expensive than standard convolution, because of irregular memory access.

**Agent use:**
- **Role:** Architect.
- **How:** Detection and segmentation with objects of varied shape (documents with irregular layouts, deformed objects).
- **Rules:** Use optimized kernels; naive implementations are slow.
- **Guardrails:** None specific.

### 83. Receptive field analysis

**Definition:** Computing which input region each output unit can see, which determines what context a CNN can actually use.

**How it works:**
1. **Theoretical receptive field:** for each layer, rf ← rf + (kernel size − 1) × (product of previous strides). Dilation multiplies the kernel's span.
2. **Effective receptive field:** the actual influence is concentrated near the center (roughly Gaussian), and is much smaller than the theoretical one. Measure it with gradients of an output unit with respect to the input.
3. Compare with the size of the objects or patterns the task needs to see.

**Cost:** Cheap to compute.

**Agent use:**
- **Role:** Analyst.
- **How:** Diagnoses failures where a model misses large-scale context or large objects. Guides adding dilation, depth or attention.
- **Rules:** Check the effective receptive field, not only the theoretical one.
- **Guardrails:** None specific.

## B4. Object detection

### 84. Region proposal networks and two-stage detection (Faster R-CNN)

**Definition:** Detection in two stages: first propose likely object regions with a small network, then classify and refine each proposal.

**How it works:**
1. A backbone (with FPN, #80) produces feature maps.
2. **Region proposal network:** at every position, for several anchor boxes (different sizes and aspect ratios), predict an "objectness" score and box adjustments.
3. Keep the top proposals after non-maximum suppression (#86).
4. **Second stage:** extract features for each proposal (RoIAlign, #88), then classify the object and refine its box.
5. **Training:** match anchors and proposals to ground-truth boxes by IoU thresholds, with classification and box regression losses.

**Cost:** Slower than single-stage detectors, often more accurate.

**Agent use:**
- **Role:** Architect.
- **How:** Accurate detection where speed is less critical: document element detection, inspection images.
- **Rules:** Tune anchor sizes and aspect ratios to the dataset's objects.
- **Guardrails:** None specific.

### 85. Single-stage detectors (YOLO, SSD, RetinaNet)

**Definition:** Detection in one pass: predict classes and boxes directly from feature maps at every location, without a separate proposal stage.

**How it works:**
1. Divide feature maps (often several pyramid levels) into grid cells or anchor positions.
2. At each, predict class scores and box coordinates (relative to anchors or the cell).
3. **Class imbalance** (mostly background) is handled with focal loss (RetinaNet, #17) or objectness scores (YOLO).
4. Post-process with confidence thresholds and non-maximum suppression (#86).
5. Many YOLO versions refine the design (anchor-free heads, better assignment of targets, data augmentation).

**Cost:** Real-time inference on GPUs and many edge devices.

**Agent use:**
- **Role:** Architect and Deployer.
- **How:** Real-time detection (video, high-throughput image streams).
- **Rules:** Evaluate with mAP at the IoU thresholds relevant to the use case.
- **Guardrails:** Surveillance-type uses of detection on people require legal and ethical review (NX3).

### 86. Non-maximum suppression (NMS) and Soft-NMS

**Definition:** Removing duplicate detections of the same object by keeping the highest-scoring box and suppressing overlapping ones.

**How it works:**
1. Sort the boxes by score (per class).
2. Take the top box and keep it.
3. Remove every remaining box whose IoU with it exceeds a threshold (for example 0.5).
4. Repeat until no boxes remain.
5. **Soft-NMS:** instead of removing overlapping boxes, lower their scores in proportion to the overlap. Better for crowded scenes where real objects overlap.
6. Batched GPU implementations exist.

**Cost:** O(n²) worst case per class, fast in practice.

**Agent use:**
- **Role:** Deployer.
- **How:** Standard post-processing for detectors. The IoU threshold strongly affects results in crowded scenes.
- **Rules:** Tune the threshold on validation data.
- **Guardrails:** Ensure training and evaluation use the same NMS settings.

### 87. DETR (detection as set prediction with bipartite matching)

**Definition:** A transformer-based detector that predicts a fixed set of objects directly, matched one-to-one with the ground truth, removing anchors and NMS.

**How it works:**
1. A CNN backbone plus transformer encoder processes the image.
2. A transformer decoder takes N learned "object queries" and outputs N predictions (class + box), including "no object".
3. **Training:** find the optimal one-to-one matching between predictions and ground-truth objects with the Hungarian algorithm (G#85 of graphs), using a cost combining class probability and box distance (L1 + generalized IoU).
4. Loss is computed on the matched pairs only.
5. Variants (Deformable DETR, DINO-DETR) fix the slow convergence and small-object weaknesses.

**Cost:** Transformer cost on image features. Original DETR trains slowly.

**Agent use:**
- **Role:** Architect.
- **How:** Clean end-to-end detection, without hand-designed anchors or NMS. The set-prediction approach also applies to other "predict a set of items" problems.
- **Rules:** Use improved variants for practical training time.
- **Guardrails:** None specific.

### 88. RoIAlign and instance segmentation (Mask R-CNN)

**Definition:** Extracting fixed-size features for arbitrary boxes with exact bilinear sampling, and adding a mask branch for per-object segmentation.

**How it works:**
1. For each proposed box, divide it into a fixed grid (for example 7×7).
2. **RoIAlign:** in each grid cell, sample a few points at exact fractional positions with bilinear interpolation, then pool them. No rounding of coordinates (the older RoIPool rounded, which misaligned features).
3. **Mask R-CNN:** add a small fully convolutional branch predicting a binary mask for each detected object, alongside the class and box branches.
4. Mask loss: per-pixel binary cross-entropy for the predicted class's mask only.

**Cost:** Moderate overhead on top of two-stage detection.

**Agent use:**
- **Role:** Architect.
- **How:** Per-object masks: counting and measuring objects, extracting regions of documents and diagrams.
- **Rules:** Evaluate with mask mAP.
- **Guardrails:** None specific.

### 89. Anchor-free detectors (FCOS, CenterNet)

**Definition:** Detectors that predict objects directly from points (pixel locations or object centers) without predefined anchor boxes.

**How it works:**
1. **FCOS:** every location inside a ground-truth box predicts the distances to the box's four sides, plus a "centerness" score that down-weights locations near the edges. Pyramid levels are assigned by object size.
2. **CenterNet:** predict a heatmap of object centers. At each peak, predict the box size and offset. Peak extraction replaces NMS (a 3×3 max-pool finds local maxima).
3. Fewer hyperparameters than anchor-based detectors.

**Cost:** Similar to single-stage detectors.

**Agent use:**
- **Role:** Architect.
- **How:** Simpler detection pipelines with fewer tuning knobs, and natural extensions to keypoints and other point-based outputs.
- **Rules:** None specific.
- **Guardrails:** None specific.

## B5. Recurrent networks and sequence models

### 90. Recurrent neural networks and backpropagation through time (BPTT)

**Definition:** Networks that process sequences step by step, keeping a hidden state that carries information forward, trained by unrolling the steps.

**How it works:**
1. h_t = tanh(W_h h_{t−1} + W_x x_t + b). Output y_t = W_y h_t.
2. The same weights are used at every step.
3. **BPTT:** unroll the network over the sequence as one deep network, then backpropagate through all steps, summing the gradients for the shared weights.
4. Gradients pass through repeated multiplications by W_h, so they vanish or explode over long sequences (#28).

**Cost:** O(T × hidden²) per sequence. Steps are sequential (hard to parallelize).

**Agent use:**
- **Role:** Architect.
- **How:** Mostly replaced by LSTMs, GRUs and transformers, but still useful for small streaming models where constant memory per step matters.
- **Rules:** Use gated variants (#92, #93) for anything beyond short sequences.
- **Guardrails:** Clip gradients (#28).

### 91. Truncated BPTT

**Definition:** Training recurrent networks on long sequences by backpropagating only through a limited window of recent steps, while still carrying the hidden state forward.

**How it works:**
1. Split long sequences into chunks of length k.
2. Process chunks in order, passing the final hidden state of each chunk into the next.
3. Backpropagate only within each chunk: the hidden state passed between chunks is detached from the gradient graph.
4. Memory and compute per update are bounded, and dependencies longer than k are learned only indirectly.

**Cost:** O(k) memory per update.

**Agent use:**
- **Role:** Trainer.
- **How:** Training on very long streams (logs, sensor data, long texts with RNNs or recurrent-style models, #124).
- **Rules:** Keep chunk order consistent within each sequence.
- **Guardrails:** None specific.

### 92. LSTM (long short-term memory)

**Definition:** A recurrent unit with a separate memory cell and gates that control what to forget, what to add and what to output, allowing long-range dependencies.

**How it works:**
1. **Forget gate:** f = σ(W_f [h_{t−1}, x_t] + b_f), what to keep from the cell.
2. **Input gate:** i = σ(…), and candidate values c̃ = tanh(…).
3. **Cell update:** c_t = f ⊙ c_{t−1} + i ⊙ c̃. This additive path lets gradients flow over many steps.
4. **Output gate:** o = σ(…). Hidden state: h_t = o ⊙ tanh(c_t).
5. Initializing the forget gate bias to 1 helps remember by default.

**Cost:** About 4× a vanilla RNN per step.

**Agent use:**
- **Role:** Architect.
- **How:** Streaming sequence models with small memory (on-device, real-time signals), and time series baselines.
- **Rules:** Compare against transformers and temporal convolutional networks (#100) on the same task (NR2).
- **Guardrails:** None specific.

### 93. GRU (gated recurrent unit)

**Definition:** A simplified gated recurrent unit with two gates and no separate cell state.

**How it works:**
1. **Update gate:** z = σ(…), how much to update the state.
2. **Reset gate:** r = σ(…), how much of the previous state to use in the candidate.
3. Candidate: h̃ = tanh(W [r ⊙ h_{t−1}, x_t]).
4. New state: h_t = (1 − z) ⊙ h_{t−1} + z ⊙ h̃.
5. Fewer parameters than an LSTM, with similar performance on many tasks.

**Cost:** About 3× a vanilla RNN per step.

**Agent use:**
- **Role:** Architect.
- **How:** A lighter alternative to LSTMs for streaming or small models (also used in temporal graph memory, as in the TGN model).
- **Rules:** Benchmark against LSTM. The better one varies by task.
- **Guardrails:** None specific.

### 94. Bidirectional RNNs

**Definition:** Two recurrent networks, one reading the sequence forward and one backward, with their states combined at each position.

**How it works:**
1. A forward RNN gives states h→_t from the start to t.
2. A backward RNN gives states h←_t from the end to t.
3. Concatenate [h→_t, h←_t] at each position, so each position sees both past and future context.
4. Only usable when the whole sequence is available (not for real-time generation).

**Cost:** 2× a single RNN.

**Agent use:**
- **Role:** Architect.
- **How:** Sequence labeling with full context (tagging, extraction), often with a CRF on top.
- **Rules:** Never use bidirectional models for streaming or autoregressive tasks: they'd use future information.
- **Guardrails:** None specific.

### 95. Sequence-to-sequence encoder-decoder

**Definition:** An architecture mapping an input sequence to an output sequence of different length: an encoder reads the input, and a decoder generates the output step by step.

**How it works:**
1. The encoder (RNN or transformer) processes the input into a representation (originally one final vector; with attention, all encoder states).
2. The decoder generates output tokens one at a time, conditioned on that representation and the tokens generated so far.
3. Generation starts with a start token and ends with an end token.
4. Training uses teacher forcing (#97). Inference uses greedy, sampling or beam search (#98).

**Cost:** Encoder pass + sequential decoder steps.

**Agent use:**
- **Role:** Architect.
- **How:** Translation, summarization, and structured transformations (text to query, text to code), now usually with transformers (#113).
- **Rules:** None specific.
- **Guardrails:** None specific.

### 96. Additive and multiplicative attention (Bahdanau, Luong)

**Definition:** Letting the decoder look back at all encoder states at each step, weighting them by relevance, instead of compressing the input into one vector.

**How it works:**
1. At each decoder step, compute a score between the decoder state and every encoder state.
2. **Additive (Bahdanau):** score = vᵀ tanh(W₁ s + W₂ h). **Multiplicative (Luong):** score = sᵀ W h, or just the dot product sᵀ h.
3. Softmax the scores into weights (#7).
4. **Context vector** = the weighted sum of encoder states.
5. Combine the context with the decoder state to predict the next token.
6. The predecessor of transformer attention (#101).

**Cost:** O(input length) per decoder step.

**Agent use:**
- **Role:** Architect and Analyst.
- **How:** The base concept of attention. Attention weights also show alignment (which input parts were used), with caveats (#274).
- **Rules:** None specific.
- **Guardrails:** None specific.

### 97. Teacher forcing and scheduled sampling

**Definition:** Training sequence generators by feeding the true previous token as input (teacher forcing), optionally mixing in the model's own predictions (scheduled sampling).

**How it works:**
1. **Teacher forcing:** at step t, the decoder input is the ground-truth token from step t−1. All steps can be trained in parallel (in transformers).
2. **Exposure bias:** at inference, the model receives its own possibly wrong predictions, a situation never seen in training.
3. **Scheduled sampling:** with a probability that increases over training, feed the model's own prediction instead of the true token.
4. Sequence-level training (RL-style, #198) is another fix.

**Cost:** Teacher forcing is cheap and parallel. Scheduled sampling needs sequential sampling for the sampled steps.

**Agent use:**
- **Role:** Trainer.
- **How:** Teacher forcing is the default for sequence models and LLMs. The agent watches for exposure-bias symptoms (errors compounding in long outputs).
- **Rules:** Evaluate on full generation, not only teacher-forced loss.
- **Guardrails:** None specific.

### 98. Beam search with length normalization

**Definition:** Approximate search for the most likely output sequence, keeping the B best partial sequences at each step.

**How it works:**
1. Start with the start token: one hypothesis.
2. At each step, extend every hypothesis with every possible next token, scoring by the summed log-probabilities.
3. Keep the top B (the beam width).
4. Hypotheses ending with the end token move to the finished set.
5. **Length normalization:** divide the score by length^α, since raw log-probability sums favor short outputs.
6. Variants: diverse beam search (penalizes similar beams) and constrained beam search (must include given tokens).

**Cost:** O(B × vocabulary) per step.

**Agent use:**
- **Role:** Deployer.
- **How:** Translation, speech recognition and structured outputs, where the single most likely answer is wanted.
- **Rules:** Tune B and α on validation data. Larger beams aren't always better.
- **Guardrails:** For open-ended LLM text, beam search produces repetitive output. Use sampling (#141–143) instead.

### 99. Pointer networks and copy mechanisms

**Definition:** Decoders that can output positions in the input (pointing) or copy input tokens directly, instead of only generating from a fixed vocabulary.

**How it works:**
1. **Pointer network:** use attention weights over the input positions as the output distribution. The model "points" at an input element.
2. **Copy mechanism (pointer-generator):** at each step, compute p_gen, the probability of generating from the vocabulary versus copying.
3. Final distribution = p_gen × vocabulary distribution + (1 − p_gen) × attention distribution over input tokens.
4. Handles rare words, names, numbers and identifiers that aren't in the vocabulary.

**Cost:** Small overhead on attention-based decoders.

**Agent use:**
- **Role:** Architect.
- **How:** Tasks where outputs must reproduce exact strings from the input: extraction, summarization with names, code editing with identifiers, and ordering or selection problems.
- **Rules:** Evaluate copy accuracy on rare tokens separately.
- **Guardrails:** None specific.

### 100. Temporal convolutional networks (WaveNet-style dilated causal convolutions)

**Definition:** Sequence models built from causal convolutions (using only past inputs) with exponentially increasing dilation, giving long memory with parallel training.

**How it works:**
1. **Causal convolution:** the output at time t depends only on inputs at t and earlier (pad on the left).
2. **Dilation** doubling each layer (1, 2, 4, 8…, #70) gives a receptive field that grows exponentially with depth.
3. Residual and gated activations (WaveNet uses tanh × sigmoid gates, #8).
4. Training is fully parallel across time steps. Inference for generation is sequential, but can cache past activations.

**Cost:** O(T × layers × kernel × channels²), parallel in training.

**Agent use:**
- **Role:** Architect.
- **How:** Strong, simple baselines for time series forecasting, audio and event sequences, often matching RNNs with faster training.
- **Rules:** Size the receptive field to cover the needed history (#83).
- **Guardrails:** Check causality: any leak of future inputs inflates validation results (NR3).

---
