# Part 5: Advanced RL, LLM post-training, efficient tuning, distributed training and compression (#201–250)

Same format and the same contract (roles; rules NR1–NR8; guardrails NX1–NX5).

## E1. Advanced reinforcement learning

### 201. Soft actor-critic (SAC)

**Definition:** An off-policy actor-critic method for continuous actions that maximizes reward plus policy entropy, giving stable, sample-efficient learning with built-in exploration.

**How it works:**
1. **Objective:** expected return + α × entropy of the policy (prefer high reward while staying as random as possible).
2. **Two Q-networks:** use the minimum of their estimates for targets, which reduces overestimation. Target networks are updated by slow averaging (#42).
3. **Critic target:** r + γ (min Q_target(s′, a′) − α log π(a′ | s′)), with a′ sampled from the current policy.
4. **Actor:** trained to maximize min Q(s, a) − α log π(a | s), using the reparameterization trick (#30) with a squashed Gaussian policy.
5. **Automatic temperature:** adjust α so policy entropy stays near a target value.
6. Learns from a replay buffer (off-policy), so data is reused many times.

**Cost:** Several networks. Efficient use of environment samples.

**Agent use:**
- **Role:** Trainer.
- **How:** Continuous control in simulation: tuning continuous parameters (rates, thresholds, setpoints) through interaction.
- **Rules:** Validate policies in simulation across many seeds before any real use.
- **Guardrails:** Hard safety limits sit outside the learned policy (clamps, approval gates, NR8).

### 202. Deterministic policy gradients (DDPG, TD3)

**Definition:** Off-policy actor-critic methods with deterministic policies for continuous actions. TD3 adds fixes for DDPG's overestimation and instability.

**How it works:**
1. **DDPG:** a deterministic actor μ(s) and a critic Q(s, a). The actor is updated along ∇_a Q(s, a) at a = μ(s). Explores with added action noise. Target networks and a replay buffer.
2. **TD3 improvements:**
   - **Twin critics:** use the smaller of two Q estimates for targets.
   - **Delayed actor updates:** update the actor less often than the critics.
   - **Target policy smoothing:** add clipped noise to target actions, so the critic can't exploit sharp Q peaks.
3. Simpler than SAC, with comparable performance on many tasks.

**Cost:** Similar to SAC.

**Agent use:**
- **Role:** Trainer.
- **How:** Continuous control where a deterministic policy is preferred (reproducible decisions).
- **Rules:** Use TD3 rather than plain DDPG.
- **Guardrails:** Same as #201.

### 203. Model-based RL and world models (Dreamer)

**Definition:** Learning a model of the environment's dynamics, then training the policy largely inside that learned model ("in imagination"), which needs far fewer real interactions.

**How it works:**
1. **World model:** from observations, actions and rewards, learn an encoder into latent states, a dynamics model predicting the next latent state, and reward and continuation predictors. Dreamer uses a recurrent state space model with discrete or continuous latents.
2. Train the world model on real experience (reconstruction or prediction losses).
3. **Imagination:** roll out trajectories in the latent space using the learned dynamics.
4. Train actor and critic on those imagined trajectories (backpropagating through the dynamics, or with policy gradients).
5. Alternate collecting new real data and updating.

**Cost:** World-model training plus cheap imagined rollouts. Very sample-efficient.

**Agent use:**
- **Role:** Trainer.
- **How:** Problems where real interactions are expensive or slow (physical systems, costly APIs), and a learned simulator can stand in.
- **Rules:** Measure the world model's prediction errors. Policies exploit model errors, so keep imagination horizons short.
- **Guardrails:** Validate learned policies on real or high-fidelity simulation before deployment.

### 204. Monte Carlo tree search with learned networks (AlphaZero, MuZero)

**Definition:** Planning by tree search guided by a neural network that predicts move probabilities and position values, trained from the search's own results (self-play).

**How it works:**
1. **Network:** given a state, output a policy prior p(a | s) and a value v(s).
2. **Search (PUCT):** from the root, repeatedly select actions maximizing Q(s, a) + c × p(a | s) × √N(s) / (1 + N(s, a)), balancing value estimates and prior × exploration. At a new leaf, evaluate it with the network and back up the value along the path.
3. After many simulations, the visit counts give an improved policy.
4. **Training:** the network learns to predict the search's visit distribution (policy) and the final outcome (value). This creates a loop of self-improvement.
5. **MuZero:** learns its own dynamics model, so search works without known rules.

**Cost:** Many network evaluations per decision.

**Agent use:**
- **Role:** Trainer.
- **How:** Sequential decision problems with lookahead: scheduling, combinatorial optimization, games, and planning over action sequences.
- **Rules:** Budget the simulations per decision for latency (NX1).
- **Guardrails:** None specific.

### 205. Offline reinforcement learning (CQL, IQL)

**Definition:** Learning policies purely from a fixed dataset of past interactions, without new exploration, while avoiding over-optimistic estimates for actions the data never shows.

**How it works:**
1. Standard off-policy RL fails offline: Q-values for unseen actions get overestimated, and the policy chases them.
2. **Conservative Q-learning (CQL):** add a penalty that pushes down Q-values for actions sampled from the policy and pushes up Q-values for actions in the data, so estimates are pessimistic outside the data.
3. **Implicit Q-learning (IQL):** never query Q on unseen actions. Learn the value with expectile regression on dataset actions, then extract the policy by advantage-weighted regression on dataset actions.
4. Evaluate candidate policies with off-policy evaluation methods (importance sampling, fitted Q evaluation) before deployment.

**Cost:** Like off-policy RL, without environment cost.

**Agent use:**
- **Role:** Trainer.
- **How:** Improving decision policies from logged historical data (routing, scheduling, recommendations) where live exploration is risky.
- **Rules:** Document the data-collecting policy. Offline methods depend on its coverage.
- **Guardrails:** Off-policy evaluation is uncertain. Roll out new policies gradually with monitoring (NX4).

### 206. Imitation learning (behavior cloning, DAgger)

**Definition:** Learning a policy from demonstrations of good behavior instead of from rewards.

**How it works:**
1. **Behavior cloning:** supervised learning on (state, expert action) pairs.
2. **Compounding errors:** small mistakes lead to states the expert never visited, where the cloned policy behaves badly.
3. **DAgger:** run the learned policy, have the expert label the states it actually visits, add them to the data, retrain, and repeat. That covers the policy's own state distribution.
4. **Inverse RL / adversarial imitation (GAIL):** learn a reward that explains the expert's behavior, then optimize it.

**Cost:** Supervised training, plus expert labeling for DAgger.

**Agent use:**
- **Role:** Trainer.
- **How:** Teaching agents procedures from logged expert actions (operators handling incidents, analysts triaging tickets). That's also how supervised fine-tuning works for tool-using LLM agents (#208).
- **Rules:** Include correction data from the policy's own mistakes (DAgger-style).
- **Guardrails:** Demonstrations encode the experts' biases and errors. Review them.

## E2. LLM post-training and alignment

### 207. Curriculum learning

**Definition:** Ordering training data from easier to harder (or adjusting the mix over time), so the model learns more efficiently.

**How it works:**
1. Define difficulty: sequence length, a loss from a reference model, task complexity, or noise level.
2. **Schedule:** start with easy examples and gradually include harder ones (fixed pacing or self-paced, based on the model's current loss).
3. **Anti-curriculum or mixed strategies** sometimes work better. Evaluate.
4. In LLM training: short-to-long sequences (#229), and higher-quality data toward the end of training (annealing).

**Cost:** Scoring examples for difficulty.

**Agent use:**
- **Role:** Trainer.
- **How:** Faster convergence on hard tasks (reasoning, long contexts). Data quality annealing at the end of pretraining is a standard practice.
- **Rules:** Compare against random ordering (NR2).
- **Guardrails:** None specific.

### 208. Supervised fine-tuning (SFT) and instruction tuning

**Definition:** Fine-tuning a pretrained language model on example conversations or (instruction, response) pairs, so it follows instructions and uses a consistent format.

**How it works:**
1. Collect examples: instructions (or full multi-turn conversations, including tool calls) with high-quality responses.
2. Format them with the model's chat template (role markers, special tokens).
3. Train with next-token cross-entropy (#103), usually only on the response tokens (prompt tokens masked from the loss).
4. A few epochs at a low learning rate. Data quality and diversity matter more than quantity.
5. Evaluate on held-out tasks and on general capability benchmarks, to catch regressions.

**Cost:** Small relative to pretraining.

**Agent use:**
- **Role:** Trainer.
- **How:** Adapting models to specific formats, tools, styles and domains.
- **Rules:** Deduplicate training data against evaluation sets (#289). Keep a general-capability regression suite (NR7).
- **Guardrails:** Training data containing personal data or unsafe content transfers into the model (NX2, NX3). Screen it.

### 209. Reward modeling (Bradley-Terry preference models)

**Definition:** Training a model to score responses so that preferred responses score higher, from pairwise human (or AI) comparisons.

**How it works:**
1. Collect comparisons: for a prompt, two responses, and which one is better.
2. The reward model is usually the language model with a scalar output head.
3. **Bradley-Terry loss:** −log σ(r(chosen) − r(rejected)) (#15). It learns scores whose differences predict preferences.
4. Evaluate by accuracy on held-out comparisons, and on reward benchmarks.
5. Ensembles or uncertainty estimates detect where the reward model is unreliable.

**Cost:** One forward pass per response.

**Agent use:**
- **Role:** Trainer and Evaluator.
- **How:** Reward signals for RLHF (#210), and for ranking candidate responses (best-of-n, #216).
- **Rules:** Check for length bias (preferring longer answers regardless of quality) and correct it.
- **Guardrails:** The reward model is a proxy. Policies optimized against it find its blind spots (reward hacking). Monitor with fresh human evaluations.

### 210. RLHF with PPO and a KL penalty

**Definition:** Optimizing a language model's responses against a learned reward model with reinforcement learning, while keeping it close to its starting model.

**How it works:**
1. Start from the SFT model (#208). Keep a frozen copy as the reference.
2. Generate responses to prompts, and score them with the reward model (#209).
3. **Reward per response:** r(x, y) − β × KL(π(y | x) ‖ π_ref(y | x)), typically applied per token. The KL term stops the model from drifting into strange text that exploits the reward model.
4. Optimize with PPO (#200), with a value head estimating returns.
5. Monitor reward, KL, response length and human-evaluated quality.

**Cost:** Expensive: generation, reward scoring, policy and value training, and a reference model, all at once.

**Agent use:**
- **Role:** Trainer.
- **How:** Aligning model behavior with preferences that are hard to specify with examples alone.
- **Rules:** Prefer simpler methods (#211–213) unless PPO's flexibility is needed. Log KL and reward curves (NR4).
- **Guardrails:** Rising reward with falling human-evaluated quality signals reward hacking. Stop and investigate.

### 211. Direct preference optimization (DPO)

**Definition:** Training directly on preference pairs with a simple classification-style loss, without a separate reward model or RL loop.

**How it works:**
1. Uses the fact that, under the KL-regularized RLHF objective, the optimal policy defines an implicit reward: r(x, y) = β log(π(y | x) / π_ref(y | x)) (up to a constant).
2. Plug that into the Bradley-Terry loss: loss = −log σ(β × [log π(y_w | x)/π_ref(y_w | x) − log π(y_l | x)/π_ref(y_l | x)]), with y_w preferred and y_l rejected.
3. It increases the relative likelihood of preferred responses over rejected ones, relative to the reference model.
4. Only needs the policy and a frozen reference.

**Cost:** About 2× SFT cost (reference log-probabilities can be precomputed).

**Agent use:**
- **Role:** Trainer.
- **How:** The usual simple alternative to RLHF for preference alignment from comparison data.
- **Rules:** Tune β. Watch that the likelihood of preferred responses doesn't also drop (a known failure).
- **Guardrails:** Offline data limits what can be learned. Evaluate on fresh prompts (NR3).

### 212. DPO variants (IPO, KTO, ORPO, SimPO)

**Definition:** Modifications of DPO that address overfitting, unpaired data, the reference model's cost, or length bias.

**How it works:**
1. **IPO:** replaces the logistic loss with a squared loss toward a fixed margin, which prevents overfitting to deterministic preferences.
2. **KTO:** works with unpaired feedback (single responses labeled good or bad), using an objective inspired by prospect theory.
3. **ORPO:** combines SFT and preference learning in one stage, with an odds-ratio penalty, and needs no reference model.
4. **SimPO:** uses the length-normalized average log-probability as the implicit reward, with a target margin, and no reference model. Reduces length exploitation.

**Cost:** Similar to or lower than DPO.

**Agent use:**
- **Role:** Trainer.
- **How:** Choosing the method that fits the available feedback (pairs or thumbs up/down) and compute budget.
- **Rules:** Compare variants on the same data and evaluation suite (NR2).
- **Guardrails:** None specific beyond #211.

### 213. Group relative policy optimization (GRPO)

**Definition:** A PPO-style RL method for LLMs that estimates advantages by comparing several responses to the same prompt, removing the need for a value network.

**How it works:**
1. For each prompt, sample a group of G responses (for example 8–64).
2. Score each response (with a reward model or a verifier, #214).
3. **Advantage** of each response = (its reward − the group's mean) / the group's standard deviation.
4. Optimize with PPO's clipped objective (#200) using those advantages, plus a KL penalty to the reference model.
5. No critic network to train, which saves memory and simplifies training.

**Cost:** G generations per prompt. No value model.

**Agent use:**
- **Role:** Trainer.
- **How:** RL training for reasoning, code and tool use, especially with automatically checkable rewards.
- **Rules:** Prompts where every response gets the same reward give no learning signal. Filter for prompts of suitable difficulty.
- **Guardrails:** Monitor response length and format. Models learn to game reward checkers.

### 214. RL with verifiable rewards (RLVR)

**Definition:** Reinforcement learning where rewards come from automatic checks of correctness (tests passing, exact answers matching, formal verification), instead of learned reward models.

**How it works:**
1. Collect tasks with verifiable outcomes: math with known answers, code with unit tests, structured extraction with ground truth, formal proofs with a proof checker.
2. Generate responses, extract the final answer, and verify it (reward 1/0, or partial credit).
3. Add format rewards (answer present in the required form) if needed.
4. Optimize with GRPO or PPO (#213, #200).
5. Typically produces longer reasoning and better problem-solving on these domains.

**Cost:** Generation + verification (running tests can dominate).

**Agent use:**
- **Role:** Trainer.
- **How:** Improving coding and reasoning agents with objective feedback: the agent ecosystem's test suites become reward signals.
- **Rules:** Run verification in sandboxes (NX5-like isolation for executed code).
- **Guardrails:** Weak tests can be gamed (special-casing test inputs, editing tests). Use hidden tests, and check for hard-coding.

### 215. RL from AI feedback (RLAIF) and constitution-guided critique

**Definition:** Using AI models, guided by written principles, to generate preference labels or critiques, instead of (or alongside) human labels.

**How it works:**
1. Write a set of principles (a "constitution") describing desired behavior.
2. **Critique and revision:** the model critiques its own response against a principle and revises it. Revised responses become supervised training data.
3. **AI preference labels:** a model compares response pairs according to the principles. The labels train a reward model or are used directly in preference optimization (#211).
4. Human review checks samples of the AI labels for quality.

**Cost:** Model inference for labeling: cheaper and faster than human labeling at scale.

**Agent use:**
- **Role:** Trainer and Evaluator.
- **How:** Scaling alignment data for well-specified behaviors, while humans focus on reviewing and on hard cases.
- **Rules:** Measure agreement between AI labels and human labels on samples (NR3).
- **Guardrails:** AI labelers share blind spots with the models they label. Keep human evaluation in the loop for important behaviors.

### 216. Rejection sampling fine-tuning and best-of-n (expert iteration)

**Definition:** Generating many candidate responses, keeping the best by a reward or verifier, and either returning the best (best-of-n) or fine-tuning on the kept ones (iterating).

**How it works:**
1. For each prompt, sample n responses.
2. Score them with a reward model or verifier.
3. **Best-of-n at inference:** return the top-scored response.
4. **Rejection sampling fine-tuning:** keep the best (or all correct) responses, then run SFT on them (#208).
5. **Expert iteration:** repeat with the improved model.

**Cost:** n× generation per prompt.

**Agent use:**
- **Role:** Trainer and Deployer.
- **How:** A simple, robust way to improve models with a verifier or reward model, without RL complexity.
- **Rules:** Keep diversity: deduplicate kept responses.
- **Guardrails:** Best-of-n with a learned reward model overfits to that model's quirks at large n. Check quality with independent evaluation.

### 217. Process reward models (step-level verification)

**Definition:** Reward models that score each intermediate reasoning step, not just the final answer, giving denser and more precise feedback.

**How it works:**
1. Split solutions into steps.
2. Label each step as correct or not: by humans, or automatically (for example by sampling completions from each step and checking how often they reach the right answer).
3. Train a model to predict step correctness.
4. **Uses:** rank solutions by their weakest or average step score, guide tree or beam search over reasoning steps, and give step-level rewards in RL.

**Cost:** Expensive labeling. Inference is one pass per solution.

**Agent use:**
- **Role:** Evaluator and Deployer.
- **How:** Catches flawed reasoning that happens to reach correct answers, and supports search over multi-step agent plans.
- **Rules:** Validate step labels on human-reviewed samples.
- **Guardrails:** Step scores are still a proxy. Monitor for reasoning that "looks right" to the PRM but is wrong.

## E3. Parameter-efficient fine-tuning and model merging

### 218. LoRA (low-rank adaptation)

**Definition:** Fine-tuning by freezing the pretrained weights and learning a small low-rank update for selected weight matrices.

**How it works:**
1. For a frozen weight matrix W (d × k), add an update ΔW = B × A, with A (r × k) and B (d × r), and rank r much smaller than d and k (for example 8–64).
2. Initialize B = 0, so training starts exactly from the pretrained model.
3. Forward: h = W x + (α / r) × B A x.
4. Only A and B are trained: often under 1% of the parameters, with far less optimizer memory.
5. After training, merge W + BA for zero inference overhead, or keep adapters separate and swap them per task.

**Cost:** Small trainable parameter count. Little memory beyond the frozen model.

**Agent use:**
- **Role:** Trainer and Deployer.
- **How:** The default way to customize models per domain, customer or task. Many adapters can be served on one base model.
- **Rules:** Apply LoRA to all linear layers (attention and MLP) for best results. Version each adapter with its base model (NR1).
- **Guardrails:** Adapters only work with the exact base model version they were trained on.

### 219. QLoRA (quantized base with LoRA)

**Definition:** Training LoRA adapters on top of a base model stored in 4-bit, so large models can be fine-tuned on a single GPU.

**How it works:**
1. Quantize the frozen base weights to 4-bit **NF4** (a data type designed for normally distributed weights, #257).
2. **Double quantization:** quantize the quantization scales themselves, saving more memory.
3. During the forward pass, dequantize weights block by block to BF16 for computation.
4. Train LoRA adapters (#218) in BF16. Gradients flow through the dequantized weights to the adapters.
5. **Paged optimizers:** move optimizer state to CPU memory during memory spikes.

**Cost:** About 4× less memory for the base model.

**Agent use:**
- **Role:** Trainer.
- **How:** Fine-tuning large models on limited hardware.
- **Rules:** Evaluate the final adapter on the deployment configuration (quantized or full precision).
- **Guardrails:** Merging adapters into a quantized base needs care. Re-evaluate after merging.

### 220. LoRA variants (DoRA, rsLoRA, LoRA+, PiSSA)

**Definition:** Improvements to LoRA's parametrization, initialization or learning rates, to get closer to full fine-tuning quality.

**How it works:**
1. **DoRA:** decompose each weight into magnitude (a vector) and direction (normalized matrix). Apply LoRA only to the direction and train the magnitude separately, which resembles full fine-tuning's update patterns.
2. **rsLoRA:** scale the update by α / √r instead of α / r, so larger ranks train stably.
3. **LoRA+:** a higher learning rate for B than for A.
4. **PiSSA:** initialize A and B from the principal singular components of W (and freeze the residual), which converges faster.

**Cost:** Similar to LoRA.

**Agent use:**
- **Role:** Trainer.
- **How:** Better quality at the same adapter size, when plain LoRA falls short.
- **Rules:** Compare against plain LoRA and full fine-tuning on the same evaluation (NR2).
- **Guardrails:** None specific.

### 221. Adapter modules (bottleneck adapters)

**Definition:** Small trainable bottleneck networks inserted into each transformer layer, while the pretrained weights stay frozen.

**How it works:**
1. Each adapter: down-projection (d → r), nonlinearity, up-projection (r → d), with a residual connection.
2. Insert after the attention and/or feed-forward sublayers (sequential), or in parallel to them.
3. Initialize near identity (small up-projection), so training starts from the base model's behavior.
4. Only the adapters (and often the normalization layers) are trained.

**Cost:** Small parameter counts. Adds a little inference latency (unlike merged LoRA).

**Agent use:**
- **Role:** Trainer.
- **How:** Modular task-specific additions, which can be composed (stacking or fusing several adapters, as in AdapterFusion).
- **Rules:** Prefer LoRA when inference latency matters, since LoRA merges into the weights.
- **Guardrails:** None specific.

### 222. Prefix tuning and prompt tuning (soft prompts)

**Definition:** Adapting a frozen model by learning continuous "virtual tokens" prepended to the input (prompt tuning) or to every layer's keys and values (prefix tuning).

**How it works:**
1. **Prompt tuning:** learn k embedding vectors prepended to the input embeddings. Only those are trained.
2. **Prefix tuning:** learn prefix vectors for the keys and values at every attention layer (often via a small reparameterization network during training, for stability).
3. The rest of the model stays frozen.
4. Very few parameters per task. Many tasks can share a batch with different prefixes.

**Cost:** Tiny trainable parameter counts. Uses k extra context positions.

**Agent use:**
- **Role:** Trainer.
- **How:** Many lightweight task variants on a shared model. Works best on large models.
- **Rules:** Compare against LoRA on the task (NR2). Prompt tuning lags on small models.
- **Guardrails:** None specific.

### 223. Minimal-parameter tuning (IA³, BitFit)

**Definition:** Fine-tuning only tiny sets of parameters: learned scaling vectors on activations (IA³), or just the bias terms (BitFit).

**How it works:**
1. **IA³:** learn vectors that rescale the keys, values and feed-forward intermediate activations elementwise. Initialized to 1.
2. **BitFit:** train only the bias parameters of the network.
3. Both use far fewer parameters than LoRA.
4. Useful for few-shot adaptation with very little data.

**Cost:** Minimal.

**Agent use:**
- **Role:** Trainer.
- **How:** Extremely cheap per-user or per-task adaptation where storage of many adapters matters.
- **Rules:** Expect less capacity than LoRA. Evaluate.
- **Guardrails:** None specific.

### 224. Model merging (task arithmetic, TIES, DARE, SLERP)

**Definition:** Combining several fine-tuned models (from the same base) into one model by operating directly on their weights, without retraining.

**How it works:**
1. **Task vectors:** τ = fine-tuned weights − base weights.
2. **Task arithmetic:** merged = base + Σ λ_i τ_i. Subtracting a task vector can remove a behavior.
3. **TIES:** trim each task vector to its largest-magnitude values, resolve sign conflicts per parameter (majority sign), then average only the agreeing values.
4. **DARE:** randomly drop most of each task vector's entries and rescale the rest, reducing interference before merging.
5. **SLERP:** spherical interpolation between two models' weights, preserving weight norms.

**Cost:** Cheap (weight arithmetic, no training).

**Agent use:**
- **Role:** Trainer.
- **How:** Combining separately tuned skills (code, a language, a domain) into one deployable model, and quick experiments without retraining.
- **Rules:** Evaluate the merged model on every component task and on general regressions (NR7).
- **Guardrails:** Merging can silently reintroduce removed behaviors or weaken safety tuning. Run safety evaluation again (NX3).

## E4. Distillation and continual learning

### 225. Knowledge distillation (soft targets)

**Definition:** Training a smaller student model to match a larger teacher's output probabilities, not just the hard labels.

**How it works:**
1. Run the teacher on the training inputs to get logits.
2. Soften both teacher and student distributions with a temperature T > 1 (#7). Soft targets show which wrong classes the teacher considers similar ("dark knowledge").
3. **Loss:** α × KL(teacher_T ‖ student_T) × T² + (1 − α) × cross-entropy with the true labels.
4. **Feature distillation:** also match intermediate representations (with projection layers if sizes differ).
5. Students often reach accuracy close to the teacher at a fraction of the cost.

**Cost:** Teacher inference on the training data (can be precomputed).

**Agent use:**
- **Role:** Trainer.
- **How:** Producing cheap, fast models for high-volume tasks (classification, routing, extraction) from expensive ones.
- **Rules:** Evaluate the student against the teacher on held-out data (NR2).
- **Guardrails:** Teacher model licenses may restrict distillation. Check the terms (NX2).

### 226. Sequence-level and on-policy distillation for language models

**Definition:** Distilling generative models by training on the teacher's generated outputs (sequence-level) or by scoring the student's own generations with the teacher (on-policy).

**How it works:**
1. **Sequence-level distillation:** the teacher generates responses for many prompts. The student trains on them with SFT (#208). Simple and effective.
2. **Token-level distillation:** match the teacher's next-token distributions on given sequences (forward KL, #19).
3. **On-policy distillation:** the student generates responses; the teacher provides token-level targets (log-probabilities) on those, minimizing reverse KL or a mix. This fixes the mismatch where the student never learns from its own mistakes (exposure bias, #97).
4. Combining these with RL (#213) is common.

**Cost:** Teacher inference on generated sequences.

**Agent use:**
- **Role:** Trainer.
- **How:** Building small domain models that imitate large models' behavior for specific tasks, lowering serving cost.
- **Rules:** Filter teacher outputs for quality before training.
- **Guardrails:** Students inherit the teacher's errors and biases. Same license checks as #225.

### 227. Elastic weight consolidation (EWC)

**Definition:** Protecting knowledge from earlier tasks during new training by penalizing changes to the weights most important for the old tasks.

**How it works:**
1. After training task A, estimate each weight's importance with the diagonal of the Fisher information (the average squared gradient of the log-likelihood).
2. While training task B, add a penalty: λ/2 × Σ F_i (θ_i − θ*_A,i)², where θ*_A are the weights after task A.
3. Important weights stay close to their old values; unimportant weights are free to change.
4. With several tasks, accumulate the penalties (or use online variants).

**Cost:** One Fisher estimate per task, plus a penalty term.

**Agent use:**
- **Role:** Trainer.
- **How:** Sequential updates of production models with new data or tasks, without losing earlier capabilities.
- **Rules:** Evaluate old-task performance after every update (NR7).
- **Guardrails:** EWC reduces forgetting but doesn't eliminate it. Combine with replay (#228).

### 228. Replay and rehearsal against catastrophic forgetting

**Definition:** Mixing a sample of earlier training data (or generated substitutes) into new training, so the model doesn't forget earlier skills.

**How it works:**
1. Keep a buffer of representative past examples (reservoir sampling, or examples chosen for diversity).
2. Mix them into new training batches at a set ratio.
3. **Generative replay:** when old data can't be stored, generate substitutes with a model.
4. For LLM fine-tuning: mix general instruction data or pretraining-like text into domain fine-tuning.
5. Track a fixed suite of old-task evaluations.

**Cost:** Buffer storage and extra training compute.

**Agent use:**
- **Role:** Trainer.
- **How:** Standard practice for continual fine-tuning of domain models, keeping general capabilities.
- **Rules:** Choose the mixing ratio by measured regression on old tasks.
- **Guardrails:** Stored old data remains subject to deletion and retention rules (NX2).

## E5. Training at scale

### 229. Long-context training (progressive sequence lengths)

**Definition:** Training models to use long contexts efficiently, by training mostly on short sequences and extending to long ones in later stages.

**How it works:**
1. Pretrain mostly on shorter sequences (cheaper, since attention is quadratic).
2. In a final stage, train on long sequences with adjusted position encodings (#111), often with an increased RoPE base.
3. Data for the long stage needs genuinely long documents (books, repositories, long reports), not just concatenated short ones.
4. Use sequence and context parallelism for memory (#237).
5. Evaluate with long-context benchmarks (retrieval at various depths, multi-document reasoning).

**Cost:** The long stage is expensive per token, but short in duration.

**Agent use:**
- **Role:** Trainer.
- **How:** Extending context for repository-scale code understanding and long document analysis.
- **Rules:** Check short-context benchmarks for regression (NR7).
- **Guardrails:** Verify actual usable context length (#111) before advertising it.

### 230. Sequence packing with document masking

**Definition:** Filling each training sequence with several shorter documents back to back, so no compute is wasted on padding, while preventing documents from attending to each other.

**How it works:**
1. Concatenate tokenized documents (with separator tokens) into sequences of the full training length.
2. **Document masking:** block attention between different documents within a sequence (a block-diagonal causal mask), and reset position IDs at each document start.
3. Variable-length attention kernels handle this efficiently, without materializing masks.
4. **Bin packing heuristics** (first-fit decreasing) minimize leftover space.

**Cost:** Removes padding waste (often a large fraction of compute for short-sequence data).

**Agent use:**
- **Role:** Trainer.
- **How:** Standard for efficient pretraining and fine-tuning on datasets with varied lengths.
- **Rules:** Always use document masking in fine-tuning; cross-document attention adds noise.
- **Guardrails:** Check loss masking: prompt tokens and separators shouldn't count unintentionally.

### 231. Mixed-precision training (FP16 with loss scaling, BF16)

**Definition:** Doing most computation in 16-bit floating point while keeping critical values in 32-bit, for faster training and less memory.

**How it works:**
1. Keep an FP32 "master" copy of the weights for updates.
2. Forward and backward passes run in FP16 or BF16 on tensor cores.
3. **FP16:** has a small range, so small gradients underflow to zero. **Loss scaling:** multiply the loss by a large factor before backward, then divide the gradients before the update. Dynamic scaling reduces the factor when overflows (inf/NaN) occur and skips that step.
4. **BF16:** same range as FP32 (8 exponent bits), so no loss scaling is needed. The standard on modern hardware.
5. Keep sensitive operations in FP32: softmax, normalization statistics, loss computation, optimizer state.

**Cost:** Roughly 2× faster than FP32, with half the activation memory.

**Agent use:**
- **Role:** Trainer.
- **How:** Default for all training on modern accelerators.
- **Rules:** Use BF16 where supported. Log skipped steps when using FP16.
- **Guardrails:** Frequent overflow skips signal instability (#242).

### 232. FP8 training

**Definition:** Training with 8-bit floating-point formats for matrix multiplications, using per-tensor or per-block scaling factors, for further speed and memory gains.

**How it works:**
1. Two formats: **E4M3** (more precision, used for weights and activations) and **E5M2** (more range, used for gradients).
2. Each tensor (or block of a tensor) gets a scaling factor that maps its values into the representable range.
3. **Delayed scaling:** choose the scale from a history of past maximum values. **Current or fine-grained scaling:** compute the scale from the current tensor or per small block, which is more robust to outliers.
4. Matrix multiplications run in FP8 with higher-precision accumulation. Master weights and sensitive operations stay in higher precision.

**Cost:** Up to about 2× faster matrix multiplications than BF16 on supporting hardware.

**Agent use:**
- **Role:** Trainer.
- **How:** Cutting the cost of large training runs on hardware that supports FP8.
- **Rules:** Validate against a BF16 run at small scale first (loss curves should match closely).
- **Guardrails:** Outliers and loss spikes are more likely. Monitor closely (#242).

### 233. Data parallelism with all-reduce (ring and tree all-reduce)

**Definition:** Replicating the model on every device, giving each device different data, and averaging gradients across devices every step.

**How it works:**
1. Each device holds a full model copy and computes gradients on its own mini-batch.
2. **All-reduce** sums the gradients across all devices, so every device ends with the same average and applies the same update.
3. **Ring all-reduce:** devices form a ring. A reduce-scatter phase (each device ends with the full sum of one chunk) is followed by an all-gather phase (chunks are shared). Each device sends about 2 × (N−1)/N × the gradient size, independent of the number of devices.
4. **Tree and hierarchical all-reduce:** faster across nodes, by reducing within nodes (fast links) first.
5. Overlap communication with the backward pass (bucketing: start all-reducing early layers' gradients while later ones are still computing).

**Cost:** Communication proportional to model size per step.

**Agent use:**
- **Role:** Trainer.
- **How:** The first scaling dimension for any model that fits in one device's memory.
- **Rules:** Scale the learning rate with the global batch size (#46).
- **Guardrails:** One slow device slows everyone (stragglers). Monitor per-device step times.

### 234. ZeRO and fully sharded data parallelism (FSDP)

**Definition:** Data parallelism where the optimizer states, gradients and even parameters are split across devices instead of replicated, which makes much larger models trainable.

**How it works:**
1. **ZeRO stage 1:** shard the optimizer states (Adam's m and v, master weights) across N devices.
2. **Stage 2:** also shard the gradients (reduce-scatter instead of all-reduce).
3. **Stage 3 / FSDP:** also shard the parameters. Before each layer's forward (and backward), all-gather its full parameters; free them afterward.
4. Per-device memory for model states shrinks by roughly N.
5. Prefetching the next layer's parameters overlaps communication with computation.

**Cost:** About 1.5× the communication of plain data parallelism for stage 3, with far less memory.

**Agent use:**
- **Role:** Trainer.
- **How:** Training or fine-tuning models too large for one device's memory, with little code change.
- **Rules:** Estimate per-device memory before launch (NR5): parameters, gradients and optimizer states divided by N, plus activations.
- **Guardrails:** Checkpoints are sharded. Make sure tools can consolidate or reshard them (#241).

### 235. Tensor parallelism (Megatron-style)

**Definition:** Splitting individual weight matrices across devices, so each layer's computation is divided among them.

**How it works:**
1. **MLP:** split the first weight matrix by columns (each device computes part of the hidden activations) and the second by rows. Each device computes a partial output, and one all-reduce combines them.
2. **Attention:** split the heads across devices (each device computes some heads), and split the output projection by rows. One all-reduce per sublayer.
3. That gives two all-reduces per transformer block in the forward pass (and two in the backward).
4. Requires very fast links (within a node), because communication happens inside every layer.
5. **Sequence parallelism extension:** also split the normalization and dropout activations along the sequence, to save activation memory.

**Cost:** Frequent communication. Best within a node.

**Agent use:**
- **Role:** Trainer and Deployer.
- **How:** Large models whose layers don't fit or run fast enough on one device, for training and also for low-latency inference.
- **Rules:** Head counts and hidden sizes must divide evenly by the parallel degree (#102, #114).
- **Guardrails:** Across slow links, tensor parallelism stalls. Keep it within nodes.

### 236. Pipeline parallelism (GPipe, 1F1B, interleaved schedules)

**Definition:** Splitting a model's layers into stages on different devices, and feeding micro-batches through them like an assembly line.

**How it works:**
1. Divide the layers into P stages, one per device (or group).
2. Split each batch into M micro-batches.
3. **GPipe:** run all micro-batches forward through the pipeline, then all backward. The idle time at the start and end ("bubble") is about (P−1)/M of the total.
4. **1F1B:** after a warmup, each stage alternates one forward and one backward micro-batch, which limits stored activations to about P micro-batches.
5. **Interleaved schedules:** give each device several non-adjacent stages, which shrinks the bubble at the cost of more communication. Zero-bubble schedules split the backward pass to fill the gaps.

**Cost:** Point-to-point communication between stages only. Bubble overhead.

**Agent use:**
- **Role:** Trainer.
- **How:** Scaling across nodes for very large models (combined with tensor and data parallelism: "3D parallelism").
- **Rules:** Balance stages by compute time, not layer count (embedding and output layers are heavy).
- **Guardrails:** Unbalanced stages waste most of the cluster. Profile per-stage times.

### 237. Context and sequence parallelism (ring attention)

**Definition:** Splitting a long sequence across devices, and computing exact attention by passing key/value blocks around a ring of devices.

**How it works:**
1. Each device holds one chunk of the sequence (its queries, keys and values).
2. **Ring attention:** each device computes attention between its queries and the K/V block it currently holds, then passes that block to the next device and receives another. After N steps, every query has seen all keys.
3. Partial results are combined with online softmax (#7, #116), so the result is exact.
4. Communication of the next block overlaps with computation on the current one.
5. **Alternative (all-to-all, Ulysses-style):** redistribute so each device holds all positions for a subset of heads during attention.

**Cost:** Memory per device grows with the chunk, not the whole sequence.

**Agent use:**
- **Role:** Trainer.
- **How:** Training and serving very long contexts (hundreds of thousands to millions of tokens) that don't fit on one device.
- **Rules:** Balance causal workloads across devices (later chunks have more to attend to): use load-balanced chunk assignment.
- **Guardrails:** None specific.

### 238. Expert parallelism (all-to-all routing)

**Definition:** Placing different MoE experts on different devices, and sending each token to the device holding its chosen experts.

**How it works:**
1. Each device holds a subset of the experts (#125).
2. After routing, an **all-to-all** exchange sends each token's hidden state to the devices of its selected experts.
3. Experts process their tokens.
4. A second all-to-all returns the results to the tokens' original devices.
5. **Capacity limits** (#126) bound the per-device load. Communication-aware routing (limiting the number of devices per token) cuts traffic.

**Cost:** Two all-to-all exchanges per MoE layer, which are often the bottleneck.

**Agent use:**
- **Role:** Trainer and Deployer.
- **How:** Training and serving large MoE models across many devices.
- **Rules:** Monitor all-to-all time and per-device expert load (NR4).
- **Guardrails:** Load imbalance causes stragglers. Use balancing (#126).

### 239. Gradient accumulation

**Definition:** Simulating a larger batch by summing gradients over several smaller micro-batches before each optimizer update.

**How it works:**
1. Run forward and backward on micro-batch 1, keeping the gradients.
2. Repeat for micro-batches 2…k, adding to the gradients.
3. Divide by k (or by the total token count, for token-level losses), then take one optimizer step.
4. Zero the gradients and repeat.
5. With data parallelism, synchronize gradients only on the last micro-batch (saving communication).

**Cost:** Same compute as the large batch, but sequential: memory of only one micro-batch.

**Agent use:**
- **Role:** Trainer.
- **How:** Reaching the target batch size (#46, #244) on limited memory.
- **Rules:** Normalize losses correctly. Averaging per micro-batch instead of per token biases training when lengths vary.
- **Guardrails:** BatchNorm statistics still come from each micro-batch (#51).

### 240. Offloading (activations, optimizer states, parameters)

**Definition:** Moving training data that isn't needed right now from GPU memory to CPU memory or NVMe storage, and bringing it back when needed.

**How it works:**
1. **Optimizer offloading:** keep optimizer states (and the optimizer step) on the CPU. GPU computes gradients; CPU updates weights.
2. **Parameter offloading:** keep weights in CPU memory or on NVMe, and stream each layer to the GPU just before it's used (ZeRO-Infinity style).
3. **Activation offloading:** move saved activations to CPU during the forward pass, and back for the backward pass.
4. Overlap transfers with computation, so the GPU isn't idle.

**Cost:** PCIe or NVMe bandwidth limits speed. Large memory savings.

**Agent use:**
- **Role:** Trainer.
- **How:** Fine-tuning large models on few GPUs when sharding (#234) isn't enough.
- **Rules:** Measure throughput loss, and compare against using more devices.
- **Guardrails:** None specific.

### 241. Distributed checkpointing and exact resumption

**Definition:** Saving and restoring the full training state across many devices, so training can resume exactly where it stopped, even on a different number of devices.

**How it works:**
1. **Full state:** model shards, optimizer states, learning rate scheduler, step counter, random number generator states (per device), and the data loader's position.
2. Each device writes its shard in parallel, with metadata describing the global layout.
3. **Asynchronous checkpointing:** copy the state to CPU memory quickly, then write to storage in the background while training continues.
4. **Resharding on load:** reconstruct shards for a different parallel configuration from the metadata.
5. Verify checkpoint integrity (checksums), and keep several recent checkpoints.

**Cost:** I/O time (mostly hidden with asynchronous writes).

**Agent use:**
- **Role:** Trainer.
- **How:** Long training runs survive hardware failures and preemptions (glue-style durability, G37). Resharding allows scaling up or down mid-run.
- **Rules:** Test resumption regularly: loss curves after resuming should continue smoothly.
- **Guardrails:** A checkpoint without the data-loader state silently repeats or skips data. Include it (NR6).

### 242. Loss spike detection and recovery

**Definition:** Detecting sudden jumps in training loss (often caused by instability or bad data) and recovering without wasting the run.

**How it works:**
1. Monitor the loss, gradient norm, update-to-weight ratios and activation statistics every step (NR4).
2. **Detect spikes:** loss or gradient norm above a moving average by several standard deviations.
3. **Recover:** roll back to a checkpoint before the spike, and skip the data batches around it (if bad data caused it), lower the learning rate temporarily, or tighten gradient clipping.
4. **Prevent:** QK-norm (#57), z-loss (#140), careful initialization (#49), BF16, reasonable warmup (#43), lower β₂ in Adam (0.95).
5. Investigate the batches implicated (duplicated or garbage data is a common cause).

**Cost:** Rolled-back steps.

**Agent use:**
- **Role:** Trainer.
- **How:** Automatic spike handling keeps large runs healthy without human babysitting, with alerts for repeated problems.
- **Rules:** Keep frequent checkpoints so rollbacks are cheap (#241).
- **Guardrails:** Repeated spikes mean a systemic issue. Stop and investigate rather than looping on rollbacks.

### 243. Data mixture optimization (DoReMi and related methods)

**Definition:** Choosing the proportions of different data sources (web, code, books, domain data) in training, using small proxy models instead of guesswork.

**How it works:**
1. Train a small reference model on a baseline mixture.
2. **DoReMi:** train a small proxy model with group distributionally robust optimization: the mixture weights are increased for domains where the proxy's loss most exceeds the reference model's loss (most "learnable" excess loss).
3. Average the weights over training to get the optimized mixture.
4. Train the large model with that mixture.
5. **Alternatives:** regression-based approaches (fit a model predicting performance from mixture weights, using many small runs), and data selection by quality classifiers.

**Cost:** A few small proxy runs.

**Agent use:**
- **Role:** Trainer.
- **How:** Choosing data proportions for pretraining or large fine-tuning runs on evidence.
- **Rules:** Validate with a medium-scale run before full scale (NR5).
- **Guardrails:** Mixtures can underweight important minority domains. Check per-domain evaluations.

### 244. Critical batch size and batch size schedules

**Definition:** The batch size beyond which larger batches stop reducing the number of training steps much, estimated from gradient noise, and schedules that grow the batch during training.

**How it works:**
1. **Gradient noise scale:** B_noise ≈ trace(gradient covariance) / ‖mean gradient‖². It estimates the critical batch size.
2. Below B_noise, doubling the batch roughly halves the steps needed (efficient). Above it, returns diminish (wasted compute).
3. B_noise grows as the loss decreases during training.
4. **Batch size warmup / ramp:** start with smaller batches and increase them over training, tracking the critical size.
5. Estimate it from per-device gradient norms during training (cheap).

**Cost:** Negligible estimation cost.

**Agent use:**
- **Role:** Trainer.
- **How:** Choosing how many devices a run can use efficiently, and when adding more stops paying off (NR5).
- **Rules:** Re-estimate during training.
- **Guardrails:** None specific.

### 245. Synthetic data generation with filtering (self-instruct, evolution, verification)

**Definition:** Using models to generate training data (instructions, responses, problems with solutions), then filtering it for quality, diversity and correctness.

**How it works:**
1. **Seed:** a small set of human-written examples.
2. **Generate:** prompt a strong model to produce new instructions and responses (self-instruct), or to rewrite existing ones into harder or more varied versions (evolution-style methods).
3. **Filter:** remove duplicates (similarity thresholds), low-quality outputs (judges, reward models), and incorrect ones (verifiers, unit tests, executable checks).
4. Balance topics and difficulty.
5. Mix synthetic data with real data, and track which is which (NR1).

**Cost:** Generation and filtering compute.

**Agent use:**
- **Role:** Trainer.
- **How:** Expanding training data for domains with little labeled data: tool use, domain question answering, code tasks with tests.
- **Rules:** Verify factual and executable content. Unverified synthetic data amplifies the generator's mistakes.
- **Guardrails:** Check generator license terms (NX2). Over-reliance on synthetic data can narrow the model's outputs (model collapse). Keep real data in the mix.

### 246. Federated learning (FedAvg, secure aggregation)

**Definition:** Training a shared model across many devices or organizations without collecting their raw data in one place.

**How it works:**
1. The server sends the current model to a sample of clients.
2. Each client trains locally for several steps on its own data.
3. Clients send their model updates (not data) back.
4. **FedAvg:** the server averages the updates, weighted by each client's data size, and updates the global model.
5. **Secure aggregation:** cryptographic protocols let the server see only the sum of updates, not individual ones.
6. **Challenges:** non-identical data across clients (handled by FedProx and similar), unreliable clients, communication cost (compressed updates).

**Cost:** Many communication rounds. Client compute.

**Agent use:**
- **Role:** Trainer.
- **How:** Learning across data silos (devices, branches, partner organizations) where data can't be moved for privacy or legal reasons.
- **Rules:** Combine with differential privacy (#247) for formal privacy guarantees.
- **Guardrails:** Updates can still leak information without secure aggregation and DP. Don't treat federated training as private by default.

### 247. Differentially private training (DP-SGD)

**Definition:** Training with mathematical guarantees that the model reveals little about any single training example, by clipping each example's gradient and adding noise.

**How it works:**
1. Compute the gradient for each example separately.
2. **Clip** each per-example gradient to a maximum norm C, limiting any one example's influence.
3. Sum the clipped gradients and **add Gaussian noise** scaled to C (noise multiplier σ).
4. Average and update.
5. A privacy accountant tracks the total privacy loss (ε, δ) over all steps, given the sampling rate and noise.

**Cost:** Per-example gradients are expensive, and noise lowers accuracy (more data and larger batches help).

**Agent use:**
- **Role:** Trainer.
- **How:** Training on sensitive data (user records, communications) with provable privacy guarantees.
- **Rules:** Report ε and δ, and set them with governance input (NX2).
- **Guardrails:** DP doesn't fix bad data governance. Consent and minimization still apply.

## E6. Pruning and sparsity

### 248. Magnitude pruning and the lottery ticket hypothesis

**Definition:** Removing the weights with the smallest magnitudes, and the finding that dense networks contain sparse subnetworks that can train to similar accuracy.

**How it works:**
1. Train the network.
2. Remove (set to zero) the fraction of weights with the smallest absolute values, globally or per layer.
3. Fine-tune the remaining weights. Repeat gradually (iterative pruning) for high sparsity.
4. **Lottery ticket hypothesis:** rewinding the remaining weights to their early-training values and retraining often reaches the original accuracy.
5. Unstructured sparsity only speeds things up with sparse-aware kernels or hardware.

**Cost:** Retraining cycles.

**Agent use:**
- **Role:** Trainer and Deployer.
- **How:** Shrinking model storage, and enabling speedups on hardware that supports sparsity.
- **Rules:** Measure actual latency, not just parameter counts. Unstructured sparsity rarely speeds up standard GPUs.
- **Guardrails:** Re-run quality and safety evaluations after pruning (NR7).

### 249. Structured and one-shot pruning of LLMs (SparseGPT, Wanda, head and channel pruning)

**Definition:** Pruning large language models without full retraining, either by removing whole structures (heads, channels, layers) or with weight-level methods that compensate for removed weights.

**How it works:**
1. **SparseGPT:** prune layer by layer, using a small calibration set. For each layer, solve a local reconstruction problem (approximately, with second-order information) that updates the remaining weights to compensate for the removed ones.
2. **Wanda:** score each weight by |weight| × ‖input activation norm‖ (from calibration data), and prune the lowest per output row. No weight updates, very fast.
3. **Structured pruning:** remove attention heads, MLP channels or whole layers ranked by importance (gradients, activations), then fine-tune briefly to recover. Gives real speedups on any hardware.
4. Evaluate perplexity and downstream tasks.

**Cost:** Minutes to hours on calibration data.

**Agent use:**
- **Role:** Deployer.
- **How:** Making large models cheaper to serve without a full training run.
- **Rules:** Use calibration data similar to production traffic.
- **Guardrails:** Pruning can remove rare but important capabilities. Evaluate broadly, including safety (NX3).

### 250. Semi-structured 2:4 sparsity

**Definition:** A sparsity pattern where, in every group of 4 consecutive weights, exactly 2 are zero, which modern GPUs accelerate directly.

**How it works:**
1. For each group of 4 weights, keep the 2 with the highest importance (magnitude, or Wanda/SparseGPT scores, #249).
2. Store the 2 kept values plus 2-bit indices for their positions.
3. Sparse tensor cores skip the zeros, giving up to about 2× faster matrix multiplications and less memory.
4. Fine-tune with the mask fixed, to recover quality.

**Cost:** 50% sparsity, with hardware acceleration.

**Agent use:**
- **Role:** Deployer.
- **How:** Inference speedups on supporting GPUs, often combined with quantization (#251).
- **Rules:** Benchmark end-to-end latency (memory-bound decoding benefits less than compute-bound prefill).
- **Guardrails:** Quality drops can be larger than unstructured sparsity at 50%. Evaluate (NR7).

---