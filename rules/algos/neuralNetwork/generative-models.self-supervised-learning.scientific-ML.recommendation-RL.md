# Part 4: Generative models, self-supervised learning, scientific ML, recommendation and RL foundations (#151–200)

Same format and the same contract (roles; rules NR1–NR8; guardrails NX1–NX5).

## D1. Autoencoders, GANs, flows and autoregressive models

### 151. Denoising autoencoder

**Definition:** A network trained to reconstruct clean inputs from corrupted versions, which forces it to learn the structure of the data rather than copy it.

**How it works:**
1. Corrupt the input: add noise, mask parts, drop features.
2. The encoder maps the corrupted input to a representation; the decoder reconstructs the original.
3. Loss: reconstruction error against the clean input (#13).
4. The learned representation captures robust features.
5. Denoising generalizes into masked modeling (#104, #174) and diffusion (#161), which are multi-level denoising.

**Cost:** One encoder and decoder pass per example.

**Agent use:**
- **Role:** Trainer and Analyst.
- **How:** Unsupervised feature learning, cleaning noisy signals, and anomaly detection (high reconstruction error flags unusual inputs: odd transactions, sensor readings, log patterns).
- **Rules:** Set anomaly thresholds on validation data with known normal and abnormal examples.
- **Guardrails:** Anomaly flags lead to investigation, not automatic action (NR8).

### 152. Variational autoencoder (VAE)

**Definition:** A generative model that encodes inputs into a probability distribution over a latent space, samples from it, and decodes, trained by maximizing a lower bound on the data likelihood.

**How it works:**
1. The encoder outputs a mean μ and variance σ² for each latent dimension.
2. Sample z = μ + σ × ε with the reparameterization trick (#30).
3. The decoder reconstructs the input from z.
4. **Loss (negative ELBO)** = reconstruction loss + KL(q(z | x) ‖ N(0, I)) (#19). The KL term keeps the latent space smooth and close to a standard normal.
5. Generate new samples by drawing z from N(0, I) and decoding.
6. **β-VAE:** weight the KL term by β to trade reconstruction for more disentangled latents.

**Cost:** Like an autoencoder.

**Agent use:**
- **Role:** Architect.
- **How:** Smooth latent spaces for generation and interpolation, and the compression stage of latent diffusion (#166).
- **Rules:** Monitor the KL term: if it collapses to zero ("posterior collapse"), the latent is unused. Use KL annealing or free bits.
- **Guardrails:** None specific.

### 153. Vector-quantized VAE (VQ-VAE)

**Definition:** An autoencoder whose latents are discrete codes from a learned codebook, turning images or audio into token sequences.

**How it works:**
1. The encoder outputs continuous vectors (one per spatial position or time step).
2. Replace each with its nearest codebook vector (the code index is the token).
3. The decoder reconstructs from the quantized vectors.
4. Gradients pass through the quantization with the straight-through estimator (#29).
5. **Loss:** reconstruction + codebook loss (move codes toward encoder outputs) + commitment loss (keep encoder outputs near their codes). Often an EMA codebook update replaces the codebook loss.
6. A second model (transformer) can then generate token sequences, which the decoder turns into images or audio.

**Cost:** Nearest-code search per position.

**Agent use:**
- **Role:** Architect.
- **How:** Discrete tokenizers for images, audio and video, so language-model-style transformers can generate or understand them.
- **Rules:** Monitor codebook usage. Many unused ("dead") codes waste capacity: reset them to active encoder outputs.
- **Guardrails:** None specific.

### 154. Generative adversarial networks (GANs)

**Definition:** Training a generator to produce realistic samples by competing against a discriminator that tries to tell real from generated samples.

**How it works:**
1. The generator G maps random noise z to a sample G(z).
2. The discriminator D outputs the probability that its input is real.
3. **D** is trained to classify real samples as real and generated ones as fake.
4. **G** is trained to make D classify its samples as real. The non-saturating loss (maximize log D(G(z))) gives stronger early gradients.
5. Alternate the updates. At the ideal equilibrium, G's distribution matches the data.
6. **Common problems:** mode collapse (G produces little variety) and unstable training.

**Cost:** Two networks trained together. Sampling is a single fast forward pass.

**Agent use:**
- **Role:** Architect.
- **How:** Fast one-pass generation (image synthesis, super-resolution, data augmentation), where diffusion's many steps are too slow.
- **Rules:** Use stabilizers: spectral normalization (#55), gradient penalties (#155), carefully tuned learning rates.
- **Guardrails:** Synthetic media of real people requires consent and disclosure (NX3).

### 155. Wasserstein GAN with gradient penalty (WGAN-GP)

**Definition:** A GAN that trains a "critic" to estimate the Wasserstein (earth mover's) distance between real and generated distributions, giving smoother, more stable training.

**How it works:**
1. The critic outputs a score (not a probability). Loss = mean critic score on fakes − mean score on reals.
2. The Wasserstein formulation requires the critic to be 1-Lipschitz (its output can't change faster than its input).
3. **Gradient penalty:** sample points between real and fake samples, and add λ × (‖∇critic‖ − 1)² to the loss.
4. The critic's loss correlates with sample quality, which is a useful training signal.
5. Train the critic several steps per generator step.

**Cost:** Extra gradient computation for the penalty.

**Agent use:**
- **Role:** Trainer.
- **How:** More reliable GAN training, with a loss value that actually tracks progress (NR4).
- **Rules:** Don't use batch normalization in the critic (it breaks the per-sample penalty). Use layer normalization or none.
- **Guardrails:** None specific.

### 156. StyleGAN (mapping network, style modulation)

**Definition:** A GAN generator that maps noise into an intermediate "style" space and injects styles at every resolution, giving high-quality, controllable images.

**How it works:**
1. **Mapping network:** an MLP maps z to an intermediate latent w, which is less entangled than z.
2. **Synthesis network:** starts from a learned constant and upsamples progressively. At each layer, w modulates the convolution weights (weight demodulation in StyleGAN2, replacing adaptive instance normalization).
3. Per-layer noise inputs add fine stochastic detail (hair, texture).
4. **Style mixing:** use different w vectors at different layers, so coarse layers control pose and shape, fine layers control texture and color.
5. Regularization (path length, lazy R1 penalty) improves smoothness.

**Cost:** One forward pass per image.

**Agent use:**
- **Role:** Architect.
- **How:** High-quality generation in narrow domains, and latent editing (changing attributes by moving w along learned directions).
- **Rules:** Use the published training configurations.
- **Guardrails:** Synthetic faces and deepfakes need consent, disclosure and policy review (NX3).

### 157. Conditional and image-to-image GANs (pix2pix, CycleGAN)

**Definition:** GANs that generate outputs conditioned on an input, with paired training data (pix2pix) or unpaired data using cycle consistency (CycleGAN).

**How it works:**
1. **pix2pix:** a U-Net generator (#79) maps input image → output image. A "PatchGAN" discriminator judges whether local patches of (input, output) pairs are real. Loss = adversarial + L1 to the true output.
2. **CycleGAN:** two generators (A→B and B→A) and two discriminators. **Cycle consistency loss:** translating A→B→A should give back the original, which allows training without paired examples.
3. Identity losses help preserve color and content.

**Cost:** Two (or four) networks trained together.

**Agent use:**
- **Role:** Architect.
- **How:** Converting between visual domains: sketches to renderings, scans to clean documents, day to night images, simulation to realistic images (for training data).
- **Rules:** Evaluate on paired held-out data where available.
- **Guardrails:** Unpaired translation can invent content ("hallucinated" details). Don't use it where exact fidelity matters (medical, legal evidence).

### 158. Normalizing flows (RealNVP, Glow)

**Definition:** Generative models built from invertible transformations, giving exact likelihoods and exact sampling.

**How it works:**
1. Transform a simple distribution (standard normal) into the data distribution with a chain of invertible functions.
2. **Change of variables:** log p(x) = log p(z) + Σ log |det Jacobian| of each step. Each step must have a cheap Jacobian determinant.
3. **Affine coupling layers (RealNVP):** split the dimensions in two halves. One half is scaled and shifted by functions of the other half. The Jacobian is triangular, so its determinant is the product of the scales, and inversion is easy.
4. **Glow:** adds invertible 1×1 convolutions (learned channel permutations) and activation normalization.
5. Train by maximizing exact log-likelihood.

**Cost:** One forward pass for likelihood or sampling. Architectures are constrained by invertibility.

**Agent use:**
- **Role:** Architect.
- **How:** Exact density estimation (anomaly scoring with real likelihoods), and invertible components in scientific models.
- **Rules:** Use bits per dimension to compare density models.
- **Guardrails:** High likelihood doesn't guarantee good out-of-distribution detection: flows can assign high likelihood to unrelated data. Validate the detection setup (#267).

### 159. Autoregressive pixel models (PixelCNN)

**Definition:** Generating images one pixel at a time, each conditioned on all previous pixels, using masked convolutions.

**How it works:**
1. Order the pixels (raster order) and channels.
2. p(image) = product over pixels of p(pixel | all previous pixels).
3. **Masked convolutions:** kernel weights for "future" pixels are zeroed, so each output only sees earlier pixels. Training is parallel across pixels.
4. Gated activations (#8) and two convolution stacks (vertical and horizontal) remove "blind spots" in the visible context.
5. Sampling is sequential: one pixel at a time (slow).

**Cost:** Parallel training, slow sequential sampling.

**Agent use:**
- **Role:** Architect.
- **How:** Exact likelihood models for images, and as the prior over VQ-VAE codes (#153).
- **Rules:** None specific.
- **Guardrails:** None specific.

### 160. Energy-based models and restricted Boltzmann machines (contrastive divergence)

**Definition:** Models that assign an energy (an unnormalized negative log-probability) to each input, trained by lowering energy on data and raising it elsewhere.

**How it works:**
1. p(x) ∝ exp(−E(x)). The normalizer (sum over all x) is intractable.
2. **Gradient:** lower E on data samples; raise E on samples from the model.
3. Model samples come from MCMC: Gibbs sampling for RBMs, or Langevin dynamics (gradient steps on E plus noise) for neural energy functions.
4. **Contrastive divergence:** run only a few MCMC steps starting from data samples, which approximates the gradient cheaply.
5. **RBM:** a bipartite network of visible and hidden units with easy block Gibbs sampling.

**Cost:** MCMC sampling during training.

**Agent use:**
- **Role:** Analyst.
- **How:** The energy view underlies score-based diffusion (#162) and modern contrastive methods. Direct EBMs are used for anomaly scoring and compositional generation (adding energies to combine constraints).
- **Rules:** Monitor sample quality to detect training instability.
- **Guardrails:** None specific.

## D2. Diffusion and flow models

### 161. Denoising diffusion probabilistic models (DDPM)

**Definition:** Generative models that learn to reverse a gradual noising process: start from pure noise and denoise step by step into a sample.

**How it works:**
1. **Forward process:** add Gaussian noise over T steps (for example 1,000), following a schedule β_t (#171), until the data becomes pure noise. Any step can be sampled directly: x_t = √ᾱ_t × x₀ + √(1 − ᾱ_t) × ε.
2. **Training:** pick a random step t, add noise, and train a network (U-Net #79, or transformer #167) to predict the noise ε from (x_t, t). Loss: MSE between the true and predicted noise.
3. The timestep t is given to the network through embeddings (#106).
4. **Sampling:** start from noise x_T and repeatedly remove the predicted noise (plus a little fresh noise) for T steps.

**Cost:** Simple, stable training. Slow sampling with many steps (fixed by #163, #164, #169).

**Agent use:**
- **Role:** Architect.
- **How:** The foundation of modern image, audio and video generation, and increasingly of other data (molecules, layouts, trajectories).
- **Rules:** Record the schedule, prediction target and sampler with the model (NR1).
- **Guardrails:** Generated media need provenance and disclosure policies (NX3).

### 162. Score-based generative modeling (score matching, SDEs)

**Definition:** Learning the gradient of the log data density (the "score") at many noise levels, and generating by following it, formalized as stochastic differential equations.

**How it works:**
1. **Score:** s(x) = ∇ₓ log p(x), which points toward higher data density.
2. **Denoising score matching:** perturb the data with noise at level σ, and train a network to predict the score of the noisy distribution. That's equivalent to predicting the added noise (linking to #161).
3. **SDE view:** the forward noising is an SDE. Its time reversal is another SDE that depends on the score, so a learned score allows reversing the noise into data.
4. **Probability flow ODE:** a deterministic ODE with the same marginal distributions as the reverse SDE. It enables deterministic sampling and exact likelihoods.
5. Samplers solve the reverse SDE or ODE numerically.

**Cost:** Like diffusion models.

**Agent use:**
- **Role:** Architect.
- **How:** The unifying theory for diffusion samplers and guidance methods. Explains why fast ODE solvers work (#164).
- **Rules:** None specific.
- **Guardrails:** None specific.

### 163. DDIM (deterministic, fewer-step sampling)

**Definition:** A sampling method for trained diffusion models that skips steps and can be deterministic, giving good samples in far fewer steps.

**How it works:**
1. Reformulate the reverse process as non-Markovian: from x_t, first predict the clean sample x̂₀ from the predicted noise.
2. Jump directly to an earlier step t′ (skipping steps) using x̂₀ and the predicted noise direction.
3. With the noise parameter η = 0, sampling is deterministic: the same noise always gives the same image.
4. Works with any model trained with DDPM, without retraining.
5. Deterministic mapping allows inversion: encode a real image into noise, edit, and regenerate.

**Cost:** 20–100 steps instead of 1,000.

**Agent use:**
- **Role:** Deployer.
- **How:** Faster generation, reproducible outputs, and image editing through inversion.
- **Rules:** Fix seeds and η for reproducible outputs (NR6).
- **Guardrails:** None specific.

### 164. Fast diffusion samplers (DPM-Solver, Euler and Heun methods)

**Definition:** Numerical ODE/SDE solvers specialized for diffusion models, producing good samples in about 10–25 steps.

**How it works:**
1. Sampling = solving the probability flow ODE (#162) from noise to data.
2. **Euler:** one model call per step; simple but needs many steps.
3. **Heun (second order):** a predictor step, then a corrector using the average slope. Two model calls per step, much more accurate.
4. **DPM-Solver / DPM-Solver++:** exploit the semi-linear structure of the diffusion ODE (solve the linear part exactly, approximate the rest with higher-order terms). Very good quality at 10–20 steps.
5. Step placement (where along the noise schedule steps go, for example the Karras schedule) matters as much as the solver.

**Cost:** 10–30 model evaluations per sample.

**Agent use:**
- **Role:** Deployer.
- **How:** Cuts generation cost and latency substantially, with little quality loss.
- **Rules:** Benchmark quality metrics (FID or task-specific) across samplers and step counts.
- **Guardrails:** None specific.

### 165. Classifier-free guidance (CFG)

**Definition:** Strengthening how closely a conditional generative model follows its condition (such as a text prompt), by extrapolating away from its unconditional prediction.

**How it works:**
1. During training, drop the condition (replace with a null token) for a fraction of examples (for example 10%), so one model learns both conditional and unconditional predictions.
2. At sampling, compute both: ε_cond and ε_uncond.
3. **Guided prediction:** ε = ε_uncond + w × (ε_cond − ε_uncond), with guidance scale w > 1.
4. Higher w: more faithful to the prompt, less diverse, with oversaturation at extreme values.
5. **Negative prompts** replace the unconditional branch with an "avoid this" condition.

**Cost:** Two model evaluations per step (batched together).

**Agent use:**
- **Role:** Deployer.
- **How:** The main dial for prompt adherence versus diversity in text-to-image and text-to-audio generation. The same idea is used to steer language models.
- **Rules:** Tune w per model. Record it with outputs (NR1).
- **Guardrails:** None specific.

### 166. Latent diffusion

**Definition:** Running diffusion in the compressed latent space of an autoencoder rather than on pixels, which makes high-resolution generation much cheaper.

**How it works:**
1. Train an autoencoder (a VAE with a perceptual and adversarial loss, #152) that compresses images by about 8× per side into latents.
2. Train the diffusion model on those latents (#161).
3. Condition on text through cross-attention (#131) from a text encoder (#132 or a language model).
4. **Sampling:** generate a latent with diffusion, then decode it to pixels.
5. The compute saving makes large-scale text-to-image models practical.

**Cost:** Diffusion on much smaller tensors, plus one decoder pass.

**Agent use:**
- **Role:** Architect and Deployer.
- **How:** The standard design for high-resolution image, and many video and audio, generation systems.
- **Rules:** The autoencoder sets the quality ceiling: evaluate its reconstructions separately.
- **Guardrails:** Content safety filtering on prompts and outputs (NX3).

### 167. Diffusion transformers (DiT)

**Definition:** Using a transformer instead of a U-Net as the denoising network in diffusion models.

**How it works:**
1. Split the noisy latent into patches, which become tokens (#128).
2. Standard transformer blocks process the tokens.
3. **Conditioning** (timestep, class or text) through adaptive layer normalization (adaLN-Zero: the condition predicts per-block scale, shift and gate parameters, with gates initialized to zero) or cross-attention.
4. Output: the predicted noise (or velocity) per patch, reassembled into a latent.
5. Scales predictably with model size and compute (#138), like language transformers.

**Cost:** Quadratic in the number of patches.

**Agent use:**
- **Role:** Architect.
- **How:** Large-scale image and video generation, where transformer scaling and infrastructure (#116, #234–237) can be reused.
- **Rules:** None specific.
- **Guardrails:** None specific.

### 168. Flow matching and rectified flow

**Definition:** Training generative models to learn a velocity field that moves noise samples to data samples along simple (often straight) paths, by direct regression.

**How it works:**
1. Pair a noise sample x₀ with a data sample x₁.
2. Define a path between them, typically straight: x_t = (1 − t) x₀ + t x₁.
3. Train a network to predict the velocity along the path: v = x₁ − x₀, given (x_t, t). Loss: MSE.
4. **Sampling:** start from noise and integrate the learned velocity field (ODE) to t = 1.
5. **Rectified flow ("reflow"):** regenerate pairs with the trained model and retrain on them, which makes paths straighter, so far fewer integration steps are needed.

**Cost:** Simulation-free training. Fewer sampling steps than standard diffusion.

**Agent use:**
- **Role:** Architect.
- **How:** A simpler, efficient alternative to diffusion training, used in many recent image, audio and video generators.
- **Rules:** Record the path type and solver used (NR1).
- **Guardrails:** None specific.

### 169. Consistency models and few-step distillation

**Definition:** Models that map any point along a diffusion trajectory directly to its clean endpoint, enabling generation in one or a few steps.

**How it works:**
1. **Consistency property:** for points on the same trajectory (same final sample), the model should output the same clean result.
2. **Consistency distillation:** from a trained diffusion model, take a point x_t, move one ODE step to x_t′ with the teacher, and train the student so f(x_t) matches f(x_t′) (computed with an EMA copy of the student, #42).
3. **Consistency training:** the same without a teacher, using the data directly.
4. **Sampling:** one step from noise, or a few steps alternating denoising and re-noising, for quality.
5. Related: progressive distillation (halve the steps repeatedly), adversarial diffusion distillation.

**Cost:** 1–4 model evaluations per sample.

**Agent use:**
- **Role:** Deployer.
- **How:** Real-time or low-cost generation, where many sampling steps are too slow or expensive.
- **Rules:** Compare quality against the full-step teacher (NR2).
- **Guardrails:** None specific.

### 170. ControlNet and conditioning adapters

**Definition:** Adding new kinds of spatial control (edges, depth, pose, layout, segmentation) to a pretrained diffusion model without retraining it.

**How it works:**
1. Freeze the pretrained diffusion network.
2. **ControlNet:** make a trainable copy of its encoder blocks. Feed the control image into the copy, and add the copy's outputs into the frozen network through "zero convolutions" (1×1 convolutions initialized to zero, so training starts from unchanged behavior).
3. Train on (control image, target image, prompt) examples.
4. **Lighter alternatives:** T2I-Adapter (small separate encoder), IP-Adapter (image prompts injected through extra cross-attention).
5. Several controls can be combined, with separate strengths.

**Cost:** Extra encoder compute at sampling. Training is much cheaper than retraining the base model.

**Agent use:**
- **Role:** Architect.
- **How:** Precise structural control: generating images that match given layouts, sketches or poses.
- **Rules:** Tune control strength per use.
- **Guardrails:** Pose and face controls on real people require consent (NX3).

### 171. Noise schedules and prediction targets (linear, cosine, v-prediction)

**Definition:** The choice of how quickly noise is added across diffusion steps, and what the network predicts (noise, clean data or "velocity"), which strongly affects quality.

**How it works:**
1. **Linear β schedule** (original DDPM): destroys information quickly in the later steps for high-resolution images.
2. **Cosine schedule:** ᾱ_t follows a cosine curve, so noise increases more gradually and fewer steps are wasted near pure noise.
3. **Resolution shift:** higher resolutions need more noise at a given step (shift the schedule toward noisier steps).
4. **Prediction targets:** ε (noise), x₀ (clean data), or **v** = α ε − σ x₀ (velocity), which is better behaved across all noise levels.
5. **Zero terminal SNR:** make sure the final step is truly pure noise, so the model learns to start from real noise (fixes brightness and contrast biases).

**Cost:** None. These are design choices.

**Agent use:**
- **Role:** Trainer.
- **How:** Getting these right is essential for training or fine-tuning diffusion models.
- **Rules:** Use the same schedule and target at sampling as in training (NR1).
- **Guardrails:** A schedule mismatch between training and inference silently degrades outputs.

## D3. Self-supervised representation learning

### 172. Non-contrastive self-supervision (BYOL, SimSiam)

**Definition:** Learning representations by making two augmented views of the same input predict each other, without negative examples, using asymmetry to avoid collapse.

**How it works:**
1. Make two augmented views of each image (#61).
2. **Online network:** encoder + projector + predictor. **Target:** encoder + projector.
3. Loss: the online prediction from view 1 should match the target projection of view 2 (cosine distance), and symmetrically.
4. **Avoiding collapse** (everything mapping to one constant): BYOL makes the target an EMA of the online network (#42). SimSiam uses the same weights but stops gradients through the target branch. The predictor's asymmetry is essential.
5. No large batches of negatives needed.

**Cost:** Two views per example.

**Agent use:**
- **Role:** Trainer.
- **How:** Pretraining encoders on unlabeled domain images (documents, products, industrial images) for later fine-tuning with few labels.
- **Rules:** Monitor representation collapse (the variance of embeddings across a batch).
- **Guardrails:** None specific.

### 173. Redundancy-reduction objectives (Barlow Twins, VICReg)

**Definition:** Self-supervised objectives that make embeddings of two views agree, while keeping the embedding dimensions varied and decorrelated, which prevents collapse without negatives or asymmetry.

**How it works:**
1. Embed two views of each example.
2. **Barlow Twins:** compute the cross-correlation matrix between the two views' embeddings over the batch. Push the diagonal to 1 (views agree) and the off-diagonal to 0 (dimensions carry different information).
3. **VICReg:** three explicit terms. **Variance:** keep each dimension's standard deviation above a threshold. **Invariance:** MSE between the views. **Covariance:** penalize off-diagonal covariance.
4. Both prevent collapse directly through the loss.

**Cost:** O(dimension²) for the correlation matrices.

**Agent use:**
- **Role:** Trainer.
- **How:** Simple, stable self-supervised pretraining, including for non-image data (sensor data, tabular features, multimodal pairs).
- **Rules:** Use large projector dimensions, as the methods recommend.
- **Guardrails:** None specific.

### 174. Masked autoencoders for vision (MAE)

**Definition:** Self-supervised pretraining of vision transformers by masking most image patches and reconstructing the missing pixels.

**How it works:**
1. Split the image into patches (#128) and randomly mask a large fraction (about 75%).
2. **Encoder:** a ViT processes only the visible patches, which makes pretraining about 3× faster.
3. **Decoder:** a light transformer receives the encoded visible patches plus mask tokens, and reconstructs the pixels of the masked patches.
4. Loss: MSE on the masked patches only (often on normalized pixels).
5. After pretraining, drop the decoder and fine-tune the encoder.

**Cost:** Efficient: the encoder sees only 25% of patches.

**Agent use:**
- **Role:** Trainer.
- **How:** Pretraining strong vision encoders on large unlabeled image collections (screenshots, documents, domain imagery).
- **Rules:** Fine-tuning works much better than linear probing for MAE features. Evaluate both.
- **Guardrails:** None specific.

### 175. Self-distillation without labels (DINO)

**Definition:** Training a student network to match a teacher's outputs on different views of the same image, where the teacher is an EMA of the student. It produces strong features that capture object structure.

**How it works:**
1. Make two global views and several small local crops of each image.
2. The teacher sees only the global views; the student sees all views.
3. Both output a probability distribution (softmax over K dimensions). Loss: cross-entropy between the teacher's and student's distributions across views.
4. **Avoiding collapse:** center the teacher outputs (subtract a running mean) and sharpen them (low temperature).
5. The teacher's weights are an EMA of the student's (#42).
6. Learned features support nearest-neighbor retrieval and segmentation without fine-tuning (DINOv2 scales this up with curated data).

**Cost:** Several views per image.

**Agent use:**
- **Role:** Trainer and Analyst.
- **How:** General-purpose image features for retrieval, clustering, duplicate detection and segmentation, often usable frozen.
- **Rules:** Evaluate frozen features with k-NN and linear probes on your domain.
- **Guardrails:** None specific.

### 176. Joint-embedding predictive architectures (JEPA)

**Definition:** Self-supervised learning that predicts the representations (not pixels) of masked parts of the input from visible parts.

**How it works:**
1. Split the input into a context region and target regions (for example image blocks, or video segments).
2. A context encoder embeds the visible part. A target encoder (an EMA copy) embeds the target regions.
3. A predictor, given the context embedding and the target positions, predicts the target embeddings.
4. Loss: distance between predicted and actual target embeddings.
5. Predicting in representation space lets the model ignore unpredictable pixel details and focus on semantics.

**Cost:** No pixel decoder.

**Agent use:**
- **Role:** Trainer.
- **How:** Semantic representation learning for images and video, with efficient training.
- **Rules:** Masking strategy (large semantic blocks) matters greatly. Use the published settings.
- **Guardrails:** None specific.

## D4. Few-shot learning, meta-learning and specialized architectures

### 177. Prototypical networks (few-shot classification)

**Definition:** Classifying new examples by comparing their embedding to the average embedding (prototype) of a few labeled examples per class.

**How it works:**
1. Embed the few labeled examples of each class (the "support set").
2. Prototype per class = the mean of its support embeddings.
3. Classify a query by the softmax over negative distances to the prototypes.
4. **Episodic training:** sample many small few-shot tasks from the training classes, so the embedding learns to work this way.
5. New classes need only a few examples, with no retraining.

**Cost:** One embedding pass per example.

**Agent use:**
- **Role:** Architect.
- **How:** Adding new categories with a handful of examples: new ticket types, new document classes, new product categories. Can be built on any good pretrained encoder.
- **Rules:** Evaluate on genuinely new classes, never seen in training (NR3).
- **Guardrails:** Few examples mean high variance. Collect more examples for important classes.

### 178. MAML (model-agnostic meta-learning)

**Definition:** Learning an initialization from which a model can adapt to a new task with a few gradient steps on a few examples.

**How it works:**
1. Sample a batch of tasks.
2. **Inner loop:** for each task, take a few gradient steps on its support data, starting from the shared initialization θ, giving task-specific weights θ′.
3. **Outer loop:** evaluate θ′ on each task's query data, and update θ to reduce that query loss. This requires gradients through the inner steps (second-order; first-order approximations like FOMAML and Reptile skip that).
4. The result: an initialization that adapts quickly.

**Cost:** Expensive (inner loops plus second-order gradients).

**Agent use:**
- **Role:** Trainer.
- **How:** Settings with many related tasks and little data each: per-customer models, per-site calibration, personalization.
- **Rules:** Compare against simply fine-tuning a pretrained model (NR2), which is often just as good.
- **Guardrails:** None specific.

### 179. Neural ordinary differential equations (neural ODEs)

**Definition:** Models whose hidden state evolves continuously over time according to a learned derivative function, solved with an ODE solver.

**How it works:**
1. Define dh/dt = f(h, t; θ), where f is a neural network.
2. The output h(T) is obtained by integrating from h(0) with a numerical solver (adaptive step size).
3. **Training:** backpropagate through the solver, or use the adjoint method (solve a second ODE backward in time), which uses constant memory.
4. Natural for irregularly sampled time series (evaluate at any time), and for continuous normalizing flows.
5. Cost adapts to the difficulty of the dynamics.

**Cost:** Depends on the number of solver steps.

**Agent use:**
- **Role:** Architect.
- **How:** Modeling continuous-time systems and irregular measurements (sensor data, event streams with irregular timestamps).
- **Rules:** Set solver tolerances, and monitor the number of function evaluations (it can grow during training).
- **Guardrails:** Stiff dynamics make training very slow. Check solver statistics.

### 180. Neural radiance fields (NeRF) and implicit neural representations

**Definition:** Representing a 3D scene (or any signal) as a neural network that maps coordinates to values, trained from observations such as images.

**How it works:**
1. **Implicit representation:** an MLP maps a coordinate (x, y, z, and viewing direction) to color and density.
2. **Positional encoding** of the input coordinates (sinusoids at many frequencies) lets MLPs represent fine detail. SIREN uses sine activations instead.
3. **Volume rendering:** for each image pixel, sample points along the camera ray, query the network, and composite the colors weighted by density and transmittance.
4. Train by comparing rendered pixels with the photos (known camera poses).
5. Fast variants use hash-grid encodings (Instant-NGP) for training in minutes.

**Cost:** Many network queries per ray. Accelerated variants are far faster.

**Agent use:**
- **Role:** Architect.
- **How:** 3D reconstruction from photos (digital twins, site documentation), novel view generation, and compact neural representations of signals.
- **Rules:** Camera poses must be accurate (estimate them with structure-from-motion first).
- **Guardrails:** Reconstructions of private spaces or people raise privacy issues (NX2).

### 181. 3D Gaussian splatting (differentiable rasterization)

**Definition:** Representing a scene as many 3D Gaussian blobs with color and opacity, rendered by fast rasterization and optimized from photos.

**How it works:**
1. Initialize Gaussians from a sparse point cloud (from structure-from-motion).
2. Each Gaussian has a position, covariance (shape and orientation), opacity and view-dependent color (spherical harmonics).
3. **Render:** project the Gaussians to the image plane, sort them by depth per tile, and alpha-blend them. The process is differentiable.
4. Optimize all parameters by comparing renderings with the photos.
5. **Adaptive density control:** clone or split Gaussians in under-reconstructed regions, and prune transparent ones.

**Cost:** Real-time rendering. Training takes minutes to tens of minutes.

**Agent use:**
- **Role:** Architect.
- **How:** Real-time 3D scene reconstruction and viewing (facilities, products, inspections), faster than NeRF.
- **Rules:** Same pose and capture requirements as NeRF.
- **Guardrails:** Same privacy considerations as #180.

### 182. Physics-informed neural networks (PINNs)

**Definition:** Neural networks trained to satisfy known physical laws (differential equations) in addition to fitting observed data.

**How it works:**
1. The network approximates the solution u(x, t) of a PDE.
2. **Physics loss:** use automatic differentiation (#23) to compute the derivatives of u, and penalize the PDE residual at many sampled points.
3. **Boundary and initial condition losses.**
4. **Data loss:** fit observations where available.
5. Total loss = weighted sum. It can also infer unknown parameters of the equations (inverse problems).

**Cost:** Many residual evaluations. Training can be slow and sensitive to loss weighting.

**Agent use:**
- **Role:** Architect.
- **How:** Combining sparse measurements with known physics (thermal, flow, structural models), and estimating hidden parameters.
- **Rules:** Balance the loss terms carefully (#22). Validate against trusted numerical solvers.
- **Guardrails:** Never use PINN results for safety-critical engineering without validation against established methods.

### 183. Neural operators (Fourier neural operator)

**Definition:** Networks that learn mappings between functions (for example from a PDE's initial conditions to its solution), working at any resolution.

**How it works:**
1. Lift the input function (sampled on a grid) to a higher-dimensional channel space.
2. **Fourier layer:** FFT the representation, apply learned linear weights to the lowest-frequency modes (truncating the others), inverse FFT, and add a local linear term.
3. Stack several Fourier layers with nonlinear activations.
4. Project back to the output function.
5. Because weights act on frequency modes, the model can run on different grid resolutions than it was trained on.

**Cost:** O(n log n) per layer (FFT).

**Agent use:**
- **Role:** Architect.
- **How:** Fast surrogate models replacing expensive simulations (weather, fluid flow, materials), for many repeated runs.
- **Rules:** Validate surrogate accuracy across the input range that will actually be used.
- **Guardrails:** Surrogates fail silently outside their training distribution. Monitor input ranges.

### 184. Hypernetworks

**Definition:** A network that generates the weights of another network, conditioned on some input (a task, a style, a user).

**How it works:**
1. The hypernetwork takes a conditioning input (task embedding, style code, layer index) and outputs weights (or weight updates) for the main network.
2. The main network runs with those generated weights.
3. Both are trained end to end through the main network's loss.
4. Generating low-rank or partial weights keeps the output size manageable.

**Cost:** Hypernetwork pass per condition. Generated weights can be cached.

**Agent use:**
- **Role:** Architect.
- **How:** Producing task- or user-specific adapters on demand (for example generating LoRA weights, #218, from a task description), and compact multi-task models.
- **Rules:** Cache generated weights per condition.
- **Guardrails:** None specific.

### 185. Differentiable memory (memory networks, neural Turing machines)

**Definition:** Networks with an external memory they can read from and write to with differentiable (soft) addressing.

**How it works:**
1. A memory matrix of N slots.
2. **Read:** compute attention weights over slots (by content similarity and/or location), and return the weighted sum.
3. **Write:** erase and add operations, weighted by write attention.
4. A controller network (RNN or transformer) decides the reads and writes at each step.
5. Memory networks for question answering store facts and attend over them for several "hops".

**Cost:** O(N) per read or write.

**Agent use:**
- **Role:** Architect.
- **How:** The conceptual ancestor of retrieval augmentation and agent memory. Useful for algorithmic tasks requiring explicit storage.
- **Rules:** Today, prefer retrieval with external stores (vector and graph references) for scale and auditability.
- **Guardrails:** None specific.

### 186. Differentiable neural architecture search (DARTS)

**Definition:** Searching for a good network architecture by relaxing the choice between operations into a continuous mixture, and learning the mixture weights by gradient descent.

**How it works:**
1. Define a cell: a small graph where each edge chooses among candidate operations (3×3 conv, 5×5 conv, pooling, skip, zero).
2. **Relaxation:** each edge computes a softmax-weighted sum of all candidate operations, with learnable architecture weights α.
3. **Bilevel optimization:** alternate updating the network weights (on training data) and α (on validation data).
4. **Discretize:** keep the operation with the highest α on each edge, then retrain the final architecture from scratch.
5. Known issues: collapse toward skip connections. Fixes include early stopping, regularization and progressive pruning.

**Cost:** About one to a few GPU-days, far less than reinforcement-learning-based search.

**Agent use:**
- **Role:** Architect.
- **How:** Tailoring efficient architectures for specific hardware and latency budgets (with latency in the objective).
- **Rules:** Always compare against well-tuned standard architectures (NR2); random search is a strong baseline.
- **Guardrails:** Search costs add up. Budget them (NX1).

### 187. Spiking neural networks (surrogate gradient training)

**Definition:** Networks of neurons that communicate with discrete spikes over time, which suit event-driven, low-power neuromorphic hardware.

**How it works:**
1. **Leaky integrate-and-fire neurons:** membrane potential accumulates input and leaks over time. When it crosses a threshold, the neuron emits a spike and resets.
2. Information is carried by spike timing and rates.
3. The spike function isn't differentiable. **Surrogate gradients:** use a smooth approximation of its derivative during backpropagation through time (#90).
4. Alternatively, convert a trained standard network into a spiking one (rate coding).
5. Computation happens only when spikes occur, so energy use can be very low on neuromorphic chips.

**Cost:** Simulation on GPUs is slow. Efficient on specialized hardware.

**Agent use:**
- **Role:** Architect.
- **How:** Ultra-low-power, always-on edge sensing (event cameras, audio wake-words) on neuromorphic hardware.
- **Rules:** Use only where the target hardware exists.
- **Guardrails:** None specific.

### 188. Mixture density networks

**Definition:** Networks that output the parameters of a mixture of distributions (for example several Gaussians), so they can represent multi-modal predictions.

**How it works:**
1. For each input, the network outputs K mixture weights (softmax), K means and K variances.
2. Loss: the negative log-likelihood of the target under the mixture (computed with log-sum-exp for stability, #7).
3. Captures cases where several different outputs are plausible for the same input. A plain MSE model would average them into a meaningless middle value.

**Cost:** K × output parameters.

**Agent use:**
- **Role:** Architect.
- **How:** Forecasts with multiple plausible outcomes (travel time with or without congestion, demand with promotions), giving honest uncertainty.
- **Rules:** Constrain variances to stay positive and above a floor.
- **Guardrails:** Mixture components can collapse. Monitor the component weights.

## D5. Time series and recommendation

### 189. Deep forecasting with basis expansion (N-BEATS, N-HiTS)

**Definition:** Pure MLP forecasting models built from stacked blocks that each produce part of the forecast and remove what they explained from the input.

**How it works:**
1. Each block takes the lookback window and outputs a "backcast" (its reconstruction of the input) and a forecast.
2. **Doubly residual stacking:** the next block receives the input minus the previous backcast (only what's left to explain); forecasts from all blocks are summed.
3. **Interpretable variant:** blocks constrained to trend (polynomial basis) and seasonality (Fourier basis).
4. **N-HiTS:** blocks work at different time resolutions (pooling the input, interpolating outputs) for efficient long-horizon forecasts.

**Cost:** Cheap MLP computation.

**Agent use:**
- **Role:** Architect.
- **How:** Strong forecasting for capacity, traffic, demand and cost series.
- **Rules:** Compare against seasonal naive and classical statistical baselines (NR2).
- **Guardrails:** Forecasts are proposals for planning, with uncertainty (#188, #270).

### 190. Time-series transformers with patching (PatchTST, Temporal Fusion Transformer)

**Definition:** Transformer forecasting models designed around time-series properties: treating segments of the series as tokens, and handling covariates and multiple horizons.

**How it works:**
1. **PatchTST:** split each series into patches (for example 16 time steps per token), which reduces sequence length and captures local patterns. Process each variable (channel) independently with shared weights. Normalize each series instance (RevIN) to handle distribution shifts.
2. **Temporal Fusion Transformer:** combines variable selection networks (learned feature importance), recurrent layers for local patterns, attention for long-range patterns, static covariates, and quantile outputs (#13).
3. Train on many related series together.

**Cost:** Moderate. Patching keeps attention cheap.

**Agent use:**
- **Role:** Architect.
- **How:** Forecasting many related metrics with known future covariates (holidays, planned events, campaigns), with quantile outputs for planning.
- **Rules:** Use time-ordered splits only (NR3). Never shuffle across time.
- **Guardrails:** Forecasts drift with regime changes. Monitor errors in production.

### 191. Feature-interaction recommenders (Wide & Deep, DeepFM, DCN)

**Definition:** Models for click and conversion prediction that combine learned feature interactions with deep networks on sparse categorical inputs.

**How it works:**
1. Embed the sparse categorical features (#9).
2. **Wide & Deep:** a linear model on hand-crafted cross features (memorization), plus an MLP on embeddings (generalization), trained jointly.
3. **DeepFM:** replaces the wide part with a factorization machine, which learns all pairwise interactions through embedding dot products automatically.
4. **DCN (deep and cross network):** cross layers compute x₀ × (W x_l) + b + x_l, building explicit higher-order feature interactions efficiently; DCN-v2 uses full-rank or low-rank weights.
5. Output: a probability of click or conversion (#15).

**Cost:** Embedding lookups plus small dense layers.

**Agent use:**
- **Role:** Architect.
- **How:** Ranking items, ads or notifications from rich categorical features.
- **Rules:** Evaluate with AUC and calibration, plus online experiments.
- **Guardrails:** Feedback loops (the model trains on what it showed) bias training. Log exploration data and correct for it.

### 192. Sequential recommendation (SASRec, BERT4Rec)

**Definition:** Recommending the next item from a user's ordered interaction history, using self-attention.

**How it works:**
1. Represent a user's history as a sequence of item embeddings, with position embeddings.
2. **SASRec:** causal self-attention (#103-style). Predict the next item at each position.
3. **BERT4Rec:** bidirectional, trained by masking items in the sequence (#104).
4. Score candidate items by the dot product between the sequence representation and item embeddings.
5. Training uses sampled negatives or sampled softmax over a large catalog.

**Cost:** Attention over the history length.

**Agent use:**
- **Role:** Architect.
- **How:** "Next likely action": next document, next tool, next product, from recent activity.
- **Rules:** Evaluate with time-ordered splits, leaving the last interactions per user for testing.
- **Guardrails:** Sampled-negative metrics can overstate quality. Also evaluate against the full catalog.

### 193. Multi-task recommendation (MMoE, PLE)

**Definition:** Predicting several objectives at once (click, conversion, watch time, satisfaction) with shared and task-specific experts.

**How it works:**
1. Several expert networks process the shared input.
2. **MMoE:** each task has its own gate (softmax) that mixes the experts' outputs, then its own tower (prediction head).
3. **PLE (progressive layered extraction):** adds task-specific experts alongside shared ones, over several levels, which reduces negative transfer between conflicting tasks.
4. Combine the task predictions into a final ranking score with business-defined weights.

**Cost:** Shared experts amortize compute.

**Agent use:**
- **Role:** Architect.
- **How:** Ranking that balances engagement with quality and satisfaction signals, instead of optimizing a single metric.
- **Rules:** Monitor each task's metric separately (#22).
- **Guardrails:** Optimizing engagement alone can harm users. Include quality and well-being signals, and review the weighting (NX3).

### 194. Target attention over user behavior (Deep Interest Network)

**Definition:** Representing a user's interests differently for each candidate item, by attending over their past behaviors relative to that item.

**How it works:**
1. Embed the user's past interactions (items, categories).
2. For a candidate item, compute attention weights between the candidate and each past interaction (a small MLP on their embeddings and interactions).
3. The user interest vector = weighted sum of past interactions, which is different for each candidate.
4. Feed it, with other features, into the prediction MLP.
5. **Long histories:** first search for the most relevant past interactions (by category or embedding similarity), then attend over those (SIM, ETA).

**Cost:** Attention over the history per candidate.

**Agent use:**
- **Role:** Architect.
- **How:** Personalized ranking when users have diverse interests.
- **Rules:** Truncate or retrieve history to bound latency.
- **Guardrails:** Behavioral histories are personal data (NX2): apply retention and minimization.

### 195. Large embedding-table recommenders (DLRM, hashing tricks)

**Definition:** Recommendation models dominated by huge embedding tables for categorical features, with techniques to keep their memory manageable.

**How it works:**
1. **DLRM:** dense features go through a bottom MLP. Sparse features are embedded. Pairwise dot products between all embeddings (feature interactions) are concatenated, then passed to a top MLP.
2. Embedding tables can reach terabytes. They're sharded across devices (model parallel), while MLPs are data parallel.
3. **Hashing trick:** map IDs into a fixed number of buckets with a hash (collisions share embeddings).
4. **Compositional embeddings (quotient-remainder trick):** represent each ID as a combination of two smaller tables' embeddings, which gives unique representations with much less memory.
5. Mixed-dimension embeddings: frequent IDs get larger vectors, rare IDs smaller.

**Cost:** Memory-bound, with heavy all-to-all communication for sharded tables.

**Agent use:**
- **Role:** Architect and Deployer.
- **How:** Planning memory and sharding for very large recommendation and ranking systems.
- **Rules:** Measure the quality impact of hashing collisions.
- **Guardrails:** None specific.

## D6. Reinforcement learning foundations

### 196. Deep Q-Networks (DQN)

**Definition:** Learning the value of each action in each state with a neural network, trained from stored experience, for problems with discrete actions.

**How it works:**
1. Q(s, a) estimates the expected total future reward of taking action a in state s.
2. **Act:** mostly take the action with the highest Q, with probability ε a random action (exploration).
3. **Experience replay:** store transitions (s, a, r, s′) in a buffer, and train on random mini-batches from it, which breaks correlations between consecutive steps.
4. **Target:** y = r + γ max_a′ Q_target(s′, a′), where Q_target is a periodically updated copy of the network (stabilizes training).
5. Loss: Huber loss between Q(s, a) and y (#13).

**Cost:** One forward and backward per mini-batch, plus environment interaction.

**Agent use:**
- **Role:** Trainer.
- **How:** Sequential decision problems with discrete choices and a simulator: scheduling, caching policies, resource allocation in simulation.
- **Rules:** Train and validate in simulation before any real deployment.
- **Guardrails:** Learned policies can exploit simulator flaws. Review behaviors before use, and keep safety constraints outside the learned policy (NR8).

### 197. DQN improvements (Double DQN, dueling networks, prioritized replay)

**Definition:** Standard extensions that make value-based deep RL more accurate and data-efficient.

**How it works:**
1. **Double DQN:** choose the next action with the online network, but evaluate it with the target network. Reduces the overestimation caused by taking a max over noisy estimates.
2. **Dueling network:** split the output into a state value V(s) and action advantages A(s, a), then combine: Q = V + A − mean(A). Learns state values even when actions matter little.
3. **Prioritized replay:** sample transitions with large prediction errors more often, with importance-sampling weights to correct the bias.
4. **N-step returns and distributional value estimates** (predicting a distribution of returns) further improve learning. Combining these gives "Rainbow".

**Cost:** Small overheads.

**Agent use:**
- **Role:** Trainer.
- **How:** Using the improved variants by default whenever DQN is the right tool.
- **Rules:** Evaluate with many random seeds (RL results vary a lot between seeds).
- **Guardrails:** Same as #196.

### 198. Policy gradients (REINFORCE) with baselines

**Definition:** Directly optimizing a stochastic policy by increasing the probability of actions that led to high returns.

**How it works:**
1. The policy π(a | s) outputs action probabilities.
2. Run episodes and compute the return G_t for each step (the sum of discounted future rewards).
3. **Gradient:** ∇J ≈ Σ ∇ log π(a_t | s_t) × (G_t − b), where b is a baseline.
4. **Baseline:** subtracting the average return (or a learned state value V(s)) doesn't change the expected gradient but greatly reduces its variance.
5. Works for continuous and discrete actions, and for non-differentiable rewards (including whole-sequence rewards for generated text).

**Cost:** High-variance gradients need many samples.

**Agent use:**
- **Role:** Trainer.
- **How:** Optimizing models against rewards that can't be differentiated (task success, test pass rates, user ratings). The base of LLM RL methods (#210, #213).
- **Rules:** Always use a baseline. Normalize advantages per batch.
- **Guardrails:** Reward hacking: the model optimizes the reward, not the intent. Inspect samples regularly.

### 199. Actor-critic with generalized advantage estimation (A2C, GAE)

**Definition:** Combining a policy (actor) with a learned value function (critic), where the critic's estimates reduce the variance of policy updates. GAE controls the bias-variance trade-off of advantage estimates.

**How it works:**
1. The **critic** V(s) estimates expected returns. Trained by regression toward observed returns or bootstrapped targets.
2. **TD error:** δ_t = r_t + γ V(s_{t+1}) − V(s_t).
3. **GAE:** advantage A_t = Σ_l (γλ)^l × δ_{t+l}. λ = 0 gives low variance but more bias (one-step); λ = 1 gives the full Monte Carlo return minus the baseline (unbiased, high variance). Typical λ: 0.95.
4. The **actor** updates with ∇ log π(a_t | s_t) × A_t, plus an entropy bonus to keep exploring.
5. **A2C:** synchronous parallel environments for stable batches.

**Cost:** Two networks (often sharing layers).

**Agent use:**
- **Role:** Trainer.
- **How:** The general-purpose policy optimization setup, used inside PPO (#200).
- **Rules:** Normalize advantages, and monitor the critic's explained variance (it shows whether the critic is learning).
- **Guardrails:** Same as #196.

### 200. Proximal policy optimization (PPO)

**Definition:** A policy-gradient method that limits how much the policy changes per update, by clipping the probability ratio. It's stable and simple, and widely used.

**How it works:**
1. Collect a batch of experience with the current policy π_old.
2. Compute advantages with GAE (#199).
3. **Ratio:** r_t = π_new(a_t | s_t) / π_old(a_t | s_t).
4. **Clipped objective:** maximize the mean of min(r_t × A_t, clip(r_t, 1 − ε, 1 + ε) × A_t), with ε ≈ 0.1–0.2. Updates that would move the policy too far get no extra benefit.
5. Train several epochs over the same batch in mini-batches, plus a value loss and an entropy bonus.
6. Track the KL divergence between old and new policies. Stop the epoch early if it grows too large.

**Cost:** Several passes over each batch. Needs value-network training.

**Agent use:**
- **Role:** Trainer.
- **How:** Standard for training policies in simulation, and the classic algorithm for RLHF (#210).
- **Rules:** Log the KL divergence, clip fraction, entropy and value loss (NR4).
- **Guardrails:** Policies trained against learned rewards can exploit them. Keep a KL penalty to a reference policy (#210), and review outputs.

---
