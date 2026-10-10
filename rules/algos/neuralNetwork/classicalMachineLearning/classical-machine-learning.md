# Part 3: Classical machine learning (#101–150)

Same format and the same contract (roles; rules T1–T8; guardrails TX1–TX5). Already covered elsewhere and not repeated: k-means (V#39–42), PCA/SVD (V#23–24), Platt and isotonic calibration (V#20, K#144), CRFs (graph #276), Bayesian optimization (G92), bandits (G89), conformal prediction (NN#270), SHAP (NN#273), Mahalanobis OOD scoring (NN#267).

## C1. Linear and generalized linear models

### 101. Ordinary least squares (OLS) regression

**Definition:** Fitting a linear model y ≈ Xβ by minimizing the sum of squared residuals.

**How it works:**
1. **Closed form:** β = (XᵀX)⁻¹ Xᵀy (the normal equations).
2. **In practice,** solve with a QR decomposition (X = QR, then Rβ = Qᵀy), which is numerically stable. Avoid forming XᵀX, which squares the condition number.
3. **Large data:** iterative solvers (conjugate gradient, SGD) or streaming accumulation of XᵀX for low dimensions.
4. **Inference:** standard errors from σ² (XᵀX)⁻¹, which assumes independent, constant-variance errors. Use robust (sandwich) standard errors when that doesn't hold (Part 4).
5. **Diagnostics:** residual plots, leverage, influence (Cook's distance), and multicollinearity (variance inflation factors).

**Cost:** O(n × p²) for QR.

**Agent use:**
- **Role:** Modeler.
- **How:** Baselines, interpretable effects ("each extra request adds X ms"), capacity models, and the base of regression adjustment in experiments (Part 4).
- **Rules:** Check residual diagnostics before trusting coefficients or intervals (T6).
- **Guardrails:** Coefficients describe associations, not causes (Part 4 for causal claims).

### 102. Regularized regression (ridge, lasso, elastic net)

**Definition:** Linear models with penalties on coefficient size, which reduce overfitting and (with lasso) select features.

**How it works:**
1. **Ridge (L2):** minimize squared error + λ‖β‖². Shrinks all coefficients smoothly, and handles correlated features well. Closed form: (XᵀX + λI)⁻¹ Xᵀy.
2. **Lasso (L1):** minimize squared error + λ‖β‖₁. Sets many coefficients exactly to zero (feature selection).
3. **Elastic net:** a mix of L1 and L2. Selects groups of correlated features together, rather than arbitrarily one of them.
4. **Coordinate descent:** update one coefficient at a time with a soft-thresholding formula, cycling until convergence. Computing a whole "regularization path" (many λ values, each starting from the previous solution) is fast.
5. Choose λ by cross-validation (#140). Standardize features first, so the penalty treats them equally.

**Cost:** Fast with coordinate descent, even for many features.

**Agent use:**
- **Role:** Modeler.
- **How:** Strong baselines for high-dimensional data (text features, many metrics), and sparse, interpretable models.
- **Rules:** Standardize features. Choose λ by cross-validation, and report it (T7).
- **Guardrails:** Lasso's selected features are unstable with correlated inputs. Don't interpret the selection as "the true causes".

### 103. Logistic regression (IRLS, L-BFGS)

**Definition:** A linear model for binary outcomes, predicting the log-odds as a linear function of features, fitted by maximum likelihood.

**How it works:**
1. P(y = 1 | x) = σ(xᵀβ), where σ is the sigmoid.
2. **Loss:** the negative log-likelihood (binary cross-entropy), plus optional L1/L2 penalties (#102).
3. **IRLS (iteratively reweighted least squares):** Newton's method, where each step solves a weighted least-squares problem with weights p(1 − p). Converges in a few iterations for moderate dimensions.
4. **L-BFGS:** a quasi-Newton method using a limited history of gradients. Scales to many features.
5. **Multiclass:** softmax (multinomial) regression, or one-versus-rest.
6. Coefficients are log-odds ratios: exp(β_j) = how the odds multiply per unit of feature j.

**Cost:** Fast. A few seconds to minutes even on large data.

**Agent use:**
- **Role:** Modeler.
- **How:** Interpretable, well-calibrated classifiers (often well calibrated out of the box), and baselines for every classification task (NR2-style).
- **Rules:** Regularize by default. Check calibration on held-out data.
- **Guardrails:** Perfect separation makes unregularized coefficients diverge. Regularization fixes it.

### 104. Generalized linear models (Poisson, Gamma, Tweedie)

**Definition:** Linear models for targets that aren't normally distributed (counts, positive amounts, zero-inflated amounts), using a link function and an appropriate distribution.

**How it works:**
1. **Components:** a distribution from the exponential family, a link function g, and a linear predictor: g(E[y]) = xᵀβ.
2. **Poisson** (counts): log link. E[y] = exp(xᵀβ). Use an offset (log exposure) for rates: events per hour, per user.
3. **Gamma** (positive, skewed amounts like durations or costs): log link.
4. **Tweedie** (non-negative amounts with many exact zeros, like insurance claims or spend per user): a compound Poisson-Gamma distribution, with a power parameter between 1 and 2.
5. Fitted by IRLS (#103). Check overdispersion (variance much larger than the mean for Poisson counts), and use negative binomial if needed.

**Cost:** Like logistic regression.

**Agent use:**
- **Role:** Modeler.
- **How:** Modeling incident counts, request rates, durations and per-user costs with the right distribution: honest predictions and intervals.
- **Rules:** Pick the distribution from the target's actual shape. Check overdispersion.
- **Guardrails:** Using plain linear regression on counts or skewed amounts gives negative predictions and wrong intervals.

### 105. Generalized additive models (GAMs)

**Definition:** Models where the prediction is a sum of smooth, learned functions of individual features (plus selected interactions), keeping interpretability while capturing nonlinear effects.

**How it works:**
1. g(E[y]) = β₀ + f₁(x₁) + f₂(x₂) + … , with each f_j a smooth function.
2. Each f_j is represented with spline basis functions, with a smoothness penalty (penalized regression splines).
3. Fit with penalized IRLS. Choose the smoothness by generalized cross-validation or REML.
4. Each feature's effect can be plotted directly as its own curve.
5. **Explainable boosting machines (EBMs):** a boosting-based GAM, learning each f_j with shallow trees in rotation, plus a few detected pairwise interactions.

**Cost:** Moderate.

**Agent use:**
- **Role:** Modeler.
- **How:** High-stakes predictions where every feature's effect must be inspectable (risk scoring, pricing, capacity planning), with accuracy close to boosted trees in many cases.
- **Rules:** Review each feature's curve for implausible shapes before deployment.
- **Guardrails:** Interpretability doesn't remove bias. Still audit for proxy features (TX3).

## C2. Trees and ensembles

### 106. CART decision trees

**Definition:** Recursive partitioning of the feature space by binary splits, chosen greedily to make each resulting group as pure (classification) or homogeneous (regression) as possible.

**How it works:**
1. At a node, for each feature and each candidate threshold, compute the impurity reduction: Gini impurity or entropy for classification, variance (squared error) for regression.
2. Choose the best split. Sorting each feature lets every threshold be evaluated in one scan.
3. Recurse on the two children.
4. Stop at a maximum depth, a minimum number of samples per leaf, or a minimum impurity decrease.
5. **Cost-complexity pruning:** grow a large tree, then prune back by a penalty α × (number of leaves), choosing α by cross-validation.
6. Leaves predict the majority class or the mean value.

**Cost:** About O(p × n log n) per level.

**Agent use:**
- **Role:** Modeler.
- **How:** Readable rules ("if latency > X and region = Y then…"), and the building block of forests and boosting.
- **Rules:** Single trees are unstable (small data changes give different trees). Use ensembles for predictions.
- **Guardrails:** None specific.

### 107. Random forest

**Definition:** An ensemble of decision trees, each trained on a bootstrap sample of the data with random feature subsets at each split, averaged for predictions.

**How it works:**
1. For each of B trees: draw a bootstrap sample (n rows with replacement).
2. Grow a deep tree. At each split, consider only a random subset of features (about √p for classification, p/3 for regression).
3. **Predict:** average (regression) or majority vote / average probability (classification).
4. **Out-of-bag (OOB) error:** each row is left out of about 37% of the trees. Predicting it with only those trees gives a free validation estimate.
5. Feature randomness decorrelates the trees, so averaging reduces variance a lot.

**Cost:** O(B × p_subset × n log n). Trivially parallel.

**Agent use:**
- **Role:** Modeler.
- **How:** A robust, low-tuning baseline for tabular data, and OOB-based quick validation.
- **Rules:** Tune mainly the number of trees (more is never worse, just slower) and the features per split.
- **Guardrails:** Impurity-based importances are biased toward high-cardinality features. Use permutation importance (#114).

### 108. Extremely randomized trees (Extra Trees)

**Definition:** A random forest variant where split thresholds are drawn at random instead of optimized, giving more randomness, lower variance and faster training.

**How it works:**
1. For each tree (usually using all the data, no bootstrap):
2. At each node, pick a random subset of features. For each, draw one random threshold within the feature's range at that node.
3. Choose the best of those random splits by impurity reduction.
4. Average the trees' predictions.

**Cost:** Faster than random forests (no threshold search).

**Agent use:**
- **Role:** Modeler.
- **How:** A fast alternative to random forests, often with similar or better accuracy on noisy data.
- **Rules:** Compare against random forests on the same validation (#140).
- **Guardrails:** None specific.

### 109. Gradient boosting (Friedman's gradient boosting machine)

**Definition:** Building an ensemble of small trees sequentially, each fitted to the negative gradient (residual errors) of the current model's loss.

**How it works:**
1. Start with a constant prediction (for example the mean, or the log-odds of the base rate).
2. For each round m: compute the negative gradient of the loss for every example (for squared error, the residuals y − prediction).
3. Fit a small regression tree (depth 3–8) to those gradients.
4. Set each leaf's value to minimize the loss for the examples in it.
5. Add the tree to the model, scaled by a learning rate η (shrinkage, for example 0.05).
6. **Subsampling** rows per round (stochastic gradient boosting) adds regularization.
7. Stop by early stopping on validation loss.

**Cost:** O(rounds × tree cost). Sequential across rounds.

**Agent use:**
- **Role:** Modeler.
- **How:** Usually the strongest model family for tabular data. The baseline every neural tabular model must beat.
- **Rules:** Always use early stopping (#114), and a small learning rate with more rounds.
- **Guardrails:** Overfits noisy labels with too many rounds or too deep trees. Monitor validation curves.

### 110. Histogram-based gradient boosting (LightGBM: histograms, GOSS, EFB, leaf-wise growth)

**Definition:** A fast gradient boosting implementation that buckets feature values into histograms and adds sampling and feature-bundling techniques.

**How it works:**
1. **Histograms:** pre-bin each feature into up to 255 buckets (quantile-based). Split finding scans bins instead of sorted values: O(bins) per feature instead of O(n).
2. **Histogram subtraction:** a child's histogram = the parent's histogram − the sibling's, so only the smaller child needs to be computed.
3. **Leaf-wise growth:** expand the leaf with the largest loss reduction (rather than whole levels). More accurate for the same number of leaves; limit it with a maximum leaf count or depth.
4. **GOSS (gradient-based one-side sampling):** keep all examples with large gradients, sample the small-gradient ones, and reweight them.
5. **EFB (exclusive feature bundling):** combine sparse features that are rarely nonzero at the same time into single features.
6. **Native categorical splits:** sort categories by gradient statistics and split optimally.

**Cost:** Much faster than exact gradient boosting on large data.

**Agent use:**
- **Role:** Modeler.
- **How:** The default choice for large tabular datasets: ranking features, risk scores, demand prediction.
- **Rules:** Constrain the number of leaves and the minimum data per leaf to control overfitting.
- **Guardrails:** Leaf-wise growth overfits small datasets. Use smaller leaf limits there.

### 111. XGBoost (second-order, regularized, sparsity-aware boosting)

**Definition:** A gradient boosting implementation that uses second-order gradient information and explicit regularization on tree structure.

**How it works:**
1. **Second-order approximation** of the loss per round: use the gradient g_i and Hessian h_i per example.
2. **Optimal leaf weight:** w* = −Σg / (Σh + λ). Split gain = ½ [G_L²/(H_L+λ) + G_R²/(H_R+λ) − (G_L+G_R)²/(H_L+H_R+λ)] − γ. λ regularizes leaf values; γ penalizes extra leaves (pruning splits with small gains).
3. **Sparsity-aware splits:** learn a default direction for missing values at each split.
4. **Weighted quantile sketch** for approximate split candidates. The histogram method is also available.
5. Column subsampling, shrinkage and early stopping.

**Cost:** Efficient. Parallel split finding, with GPU support.

**Agent use:**
- **Role:** Modeler.
- **How:** Robust boosting with good handling of missing values and custom losses (any loss with gradients and Hessians).
- **Rules:** Tune depth, learning rate, λ and γ by cross-validation.
- **Guardrails:** None specific beyond #109.

### 112. CatBoost (ordered boosting and ordered target statistics)

**Definition:** A gradient boosting implementation designed to handle categorical features well and avoid a subtle form of target leakage.

**How it works:**
1. **Target leakage problem:** encoding a category by its average target, computed on the same data used for training, leaks each row's own label into its features.
2. **Ordered target statistics:** take a random permutation of the rows. Encode each row's category using only the target values of rows before it in the permutation (with a prior for smoothing).
3. **Ordered boosting:** similarly, compute each row's residuals using models trained without that row (approximated with several permutations), which removes prediction shift.
4. **Symmetric (oblivious) trees:** every node at the same depth uses the same split. Fast prediction and natural regularization.
5. Automatic combinations of categorical features.

**Cost:** Moderate. Fast inference.

**Agent use:**
- **Role:** Modeler.
- **How:** Tabular data with many high-cardinality categorical features (IDs, codes, categories), with less manual encoding.
- **Rules:** Compare against LightGBM with good target encoding (#141).
- **Guardrails:** None specific.

### 113. Monotonic and interaction constraints for tree ensembles

**Definition:** Constraining boosted models so predictions only go up (or down) with chosen features, or only allow chosen features to interact.

**How it works:**
1. **Monotonic constraints:** for a feature declared increasing, reject any split where the left child's value exceeds the right child's, and bound the leaf values so the whole model stays monotone in that feature.
2. **Interaction constraints:** declare groups of features allowed to appear together on a tree path. A split may only use features from groups compatible with the features already used above it.
3. Both are supported natively in LightGBM and XGBoost.

**Cost:** Slight accuracy cost in some cases. Same training speed.

**Agent use:**
- **Role:** Modeler.
- **How:** Encodes domain knowledge and fairness or business rules: "risk never decreases as overdue days increase", "price never decreases with quantity". Prevents implausible model behavior.
- **Rules:** Constrain every feature with a known monotone relationship in high-stakes models.
- **Guardrails:** Verify constraints hold on the trained model by checking partial dependence (#148).

### 114. Early stopping and feature importance (gain, permutation)

**Definition:** Stopping boosting rounds when validation performance stops improving, and measuring which features matter, with methods that don't mislead.

**How it works:**
1. **Early stopping:** evaluate the validation loss after each round. Stop when it hasn't improved for k rounds, and keep the best round.
2. **Gain importance:** the total loss reduction from splits on each feature. Fast, but biased toward features with many unique values.
3. **Permutation importance:** shuffle one feature's values in the validation data and measure how much performance drops. Model-agnostic and measured on held-out data.
4. **Correlated features** share or hide importance under permutation. Permute groups of correlated features together.
5. **SHAP values** (NN#273) give per-prediction attributions.

**Cost:** Permutation importance needs one evaluation per feature (or group), repeated for stability.

**Agent use:**
- **Role:** Modeler.
- **How:** Prevents overfitting and gives honest answers to "which inputs drive this model?".
- **Rules:** Use a validation set separate from the final test set for early stopping (T5).
- **Guardrails:** Importance means predictive usefulness in this model, not causal effect.

## C3. Kernel and instance-based methods

### 115. Support vector machines (SMO training)

**Definition:** Classifiers that find the separating boundary with the largest margin to the nearest training points (the support vectors), optionally in a kernel-induced feature space.

**How it works:**
1. **Linear SVM:** minimize ½‖w‖² + C × Σ hinge losses max(0, 1 − y_i (w · x_i + b)).
2. **Dual form:** the solution depends only on dot products between examples, which allows kernels (#116).
3. **SMO (sequential minimal optimization):** repeatedly pick two dual variables, solve the tiny problem for them analytically, and update, until the optimality conditions hold.
4. **Linear SVMs at scale:** coordinate descent or SGD on the primal (LIBLINEAR-style).
5. Only the support vectors (points on or inside the margin) determine the model.

**Cost:** Kernel SVMs: between O(n²) and O(n³), so they're limited to moderate n. Linear SVMs scale to large data.

**Agent use:**
- **Role:** Modeler.
- **How:** Strong text classification with linear SVMs on sparse features, and small-to-medium nonlinear problems with kernels.
- **Rules:** Scale features first. Tune C (and the kernel width) by cross-validation.
- **Guardrails:** SVM scores aren't probabilities. Calibrate before using them as such (V#20).

### 116. Kernel methods and random Fourier features

**Definition:** Using kernel functions to work implicitly in high-dimensional feature spaces, and approximating them with explicit random features to scale to large data.

**How it works:**
1. **Kernel trick:** k(x, y) = φ(x) · φ(y) for some feature map φ that never needs to be computed. Examples: the RBF kernel exp(−‖x − y‖² / 2σ²), polynomial kernels.
2. **Kernel ridge regression:** α = (K + λI)⁻¹ y, prediction = Σ α_i k(x_i, x). O(n³) training.
3. **Random Fourier features (for shift-invariant kernels like RBF):** sample random frequencies ω from the kernel's spectral distribution, and use the features z(x) = √(2/D) cos(ωᵀx + b). Then z(x) · z(y) ≈ k(x, y).
4. Train a linear model on those D features: linear cost in n.
5. **Nyström approximation:** a low-rank approximation of the kernel matrix from m sampled landmark points.

**Cost:** Exact kernels: O(n³). Approximations: linear in n.

**Agent use:**
- **Role:** Modeler.
- **How:** Nonlinear models with strong theory on moderate data, and fast approximate kernels at scale.
- **Rules:** Choose D or m by validation accuracy.
- **Guardrails:** None specific.

### 117. k-nearest neighbors classification and regression

**Definition:** Predicting by looking at the k most similar training examples, and taking their majority label or average value.

**How it works:**
1. Store the training data (no training phase).
2. For a query, find its k nearest neighbors by a distance (Euclidean, cosine, or a learned metric), with brute force or an index (KD-trees for low dimensions, ANN indexes, V#57–79, for high).
3. **Classification:** majority vote, optionally weighted by 1/distance. **Regression:** average.
4. Choose k by cross-validation: small k is noisy, large k is oversmoothed.

**Cost:** No training. Query cost is dominated by the neighbor search.

**Agent use:**
- **Role:** Modeler.
- **How:** Simple, explainable predictions ("similar past cases were labeled X"), and few-shot classification on good embeddings.
- **Rules:** Scale features (or use normalized embeddings).
- **Guardrails:** Neighbor evidence can include personal data from other cases (TX3). Show neighbors only where permitted.

### 118. Naive Bayes classifiers

**Definition:** Probabilistic classifiers that assume features are independent given the class, which makes them extremely fast and data-efficient.

**How it works:**
1. P(class | features) ∝ P(class) × Π P(feature_j | class).
2. **Multinomial NB** (word counts): P(word | class) estimated from counts, with Laplace (add-one) smoothing.
3. **Bernoulli NB** (word presence), **Gaussian NB** (continuous features).
4. Compute in log space and pick the class with the highest score.
5. **Complement NB:** better for imbalanced text classes.

**Cost:** One pass over the data to train. O(features) per prediction.

**Agent use:**
- **Role:** Modeler.
- **How:** Very fast text classification baselines (spam, routing, intent), trainable on tiny data and updatable incrementally.
- **Rules:** Use as a baseline (NR2-style).
- **Guardrails:** Probabilities are badly calibrated because of the independence assumption. Calibrate before using them.

## C4. Clustering and mixture models

### 119. DBSCAN (density-based clustering)

**Definition:** Clustering points into dense regions, finding clusters of arbitrary shape and labeling isolated points as noise.

**How it works:**
1. Parameters: ε (neighborhood radius) and minPts (minimum neighbors to be a "core" point).
2. **Core point:** at least minPts points within ε.
3. Start from an unvisited core point, and expand its cluster through all points reachable via chains of core points (BFS over ε-neighborhoods).
4. **Border points** (within ε of a core point, but not core themselves) join the cluster.
5. Points reachable from no core point are noise.
6. Use spatial indexes for neighbor queries.

**Cost:** O(n log n) with good indexes, O(n²) worst case.

**Agent use:**
- **Role:** Modeler.
- **How:** Clustering with unknown cluster counts and noise: grouping similar incidents, geographic hotspots, error-signature clusters.
- **Rules:** Choose ε from the k-distance plot (sorted distances to the k-th neighbor, look for the elbow).
- **Guardrails:** A single ε fails when cluster densities differ a lot. Use HDBSCAN (#120).

### 120. HDBSCAN (hierarchical density-based clustering)

**Definition:** A density-based clustering method that builds a hierarchy over all density levels and selects the most stable clusters, handling clusters of different densities without choosing ε.

**How it works:**
1. **Core distance** of a point: the distance to its k-th nearest neighbor (its local density).
2. **Mutual reachability distance** between a and b = max(core(a), core(b), d(a, b)). Spreads sparse points apart, keeps dense ones close.
3. Build a minimum spanning tree on mutual reachability distances (graph #61).
4. Remove edges from longest to shortest, giving a cluster hierarchy. Condense it by ignoring splits that shed fewer than min_cluster_size points.
5. Select the clusters with the highest stability (how long they persist across density levels).
6. Each point gets a cluster or noise label, plus a membership strength.

**Cost:** About O(n log n) with spatial acceleration on moderate dimensions.

**Agent use:**
- **Role:** Modeler.
- **How:** A robust default for clustering embeddings and feature vectors (often after dimensionality reduction): log patterns, document topics, user behavior groups.
- **Rules:** Set min_cluster_size from the smallest group that matters.
- **Guardrails:** Results in very high dimensions degrade. Reduce dimensions first (V#23, V#27).

### 121. Gaussian mixture models (fitted by EM)

**Definition:** Modeling data as a mixture of several Gaussian distributions, giving soft cluster memberships and a density estimate.

**How it works:**
1. Model: p(x) = Σ_k π_k N(x | μ_k, Σ_k).
2. **E-step:** compute each point's responsibility for each component: r_ik ∝ π_k N(x_i | μ_k, Σ_k).
3. **M-step:** update π_k, μ_k and Σ_k as responsibility-weighted averages.
4. Repeat until the log-likelihood stops improving (#124).
5. Covariance options: full, diagonal, spherical or tied (fewer parameters).
6. Choose the number of components by BIC, or use Bayesian variants that prune unused components.

**Cost:** O(n × K × d²) per iteration for full covariances.

**Agent use:**
- **Role:** Modeler.
- **How:** Soft clustering (an item can be 70% one group, 30% another), and density estimation for anomaly scoring (low likelihood = unusual).
- **Rules:** Initialize with k-means (V#39) and run several restarts.
- **Guardrails:** Components can collapse onto single points (infinite likelihood). Add a small regularization to the covariances.

### 122. Mean shift clustering

**Definition:** Finding clusters as the peaks (modes) of the data density, by moving each point uphill toward the nearest peak.

**How it works:**
1. For each point, repeatedly compute the kernel-weighted mean of points within a bandwidth h, and move the point there.
2. Points converge to density peaks.
3. Points converging to the same peak form one cluster.
4. The number of clusters follows from the data and h, not chosen in advance.

**Cost:** O(n²) per iteration naively. Speedups with spatial indexes and binning.

**Agent use:**
- **Role:** Modeler.
- **How:** Mode finding in low-dimensional data: locations, image color segmentation, finding typical operating points of a system.
- **Rules:** Choose h by domain scale or bandwidth estimators.
- **Guardrails:** Doesn't scale to large or high-dimensional data.

### 123. k-medoids (PAM)

**Definition:** Clustering where each cluster's center must be an actual data point (a medoid), which works with any distance measure and is robust to outliers.

**How it works:**
1. **Build:** choose k initial medoids greedily, each minimizing the total distance.
2. **Swap:** for each medoid and non-medoid pair, compute the change in total distance if they were swapped. Make the best improving swap.
3. Repeat until no swap improves.
4. Each point belongs to its nearest medoid.
5. **FasterPAM** and sampling variants (CLARA, CLARANS) make it scale.

**Cost:** Classic PAM O(k × (n − k)²) per iteration. Faster variants are much cheaper.

**Agent use:**
- **Role:** Modeler.
- **How:** Clustering with arbitrary distances (edit distances between configs or code, custom similarities), where centers must be real examples, so each cluster is represented by a real item to show people.
- **Rules:** Use the faster variants for large n.
- **Guardrails:** None specific.

## C5. Probabilistic models

### 124. The expectation-maximization (EM) algorithm

**Definition:** A general method for maximum-likelihood fitting of models with hidden variables, alternating between estimating the hidden variables and updating the parameters.

**How it works:**
1. Start with initial parameters θ.
2. **E-step:** compute the distribution of the hidden variables given the data and current θ (responsibilities, posterior state probabilities).
3. **M-step:** choose θ to maximize the expected complete-data log-likelihood under that distribution (often in closed form).
4. Repeat. The likelihood never decreases.
5. Converges to a local maximum, so use several initializations.

**Cost:** Depends on the model. Each iteration is usually linear in n.

**Agent use:**
- **Role:** Modeler.
- **How:** Underlies mixtures (#121), HMM training (#125), learning with missing data, and record-linkage parameter estimation (K#36).
- **Rules:** Monitor the log-likelihood, and run several restarts.
- **Guardrails:** Local optima can give poor solutions that look converged.

### 125. Hidden Markov model training (forward-backward, Baum-Welch)

**Definition:** Learning the parameters of a hidden Markov model (hidden states, transitions, emissions) from observation sequences, using EM with the forward-backward algorithm.

**How it works:**
1. An HMM has hidden states with transition probabilities A, an initial distribution π, and emission probabilities B (the probability of each observation per state).
2. **Forward pass:** α_t(i) = P(observations up to t, state i at t), computed recursively.
3. **Backward pass:** β_t(i) = P(observations after t | state i at t).
4. **E-step:** state posteriors γ_t(i) ∝ α_t(i) β_t(i), and transition posteriors ξ_t(i, j).
5. **M-step (Baum-Welch):** re-estimate A, B and π from the expected counts.
6. Use scaling or log space to avoid numerical underflow. Viterbi (graph #271) decodes the most likely state sequence.

**Cost:** O(T × S²) per sequence per iteration.

**Agent use:**
- **Role:** Modeler.
- **How:** Modeling systems with hidden regimes: normal, degraded and failing service states from metrics; user intent states from clickstreams; noisy sensor states.
- **Rules:** Choose the number of states by likelihood on held-out sequences and interpretability.
- **Guardrails:** Local optima (#124). Use several restarts.

### 126. Latent Dirichlet allocation (LDA topic models)

**Definition:** A probabilistic model of documents as mixtures of topics, where each topic is a distribution over words.

**How it works:**
1. **Generative story:** each document has a topic mixture θ (Dirichlet prior α). Each topic has a word distribution φ (Dirichlet prior β). Each word is generated by picking a topic from θ, then a word from that topic.
2. **Inference** recovers θ (per document) and φ (per topic) from word counts.
3. **Collapsed Gibbs sampling:** repeatedly resample each word's topic in proportion to (document's count of that topic + α) × (topic's count of that word + β) / (topic's total count + V β).
4. **Variational inference** (online versions) scales to large corpora.
5. Choose the number of topics by coherence measures and held-out likelihood.

**Cost:** Linear in corpus tokens per iteration.

**Agent use:**
- **Role:** Modeler.
- **How:** Cheap, model-free (no LLM) topic discovery over tickets, logs, feedback or documents, with interpretable word lists.
- **Rules:** Remove stop words and very rare or frequent words first. Evaluate topic coherence.
- **Guardrails:** Topic labels are human interpretations. Validate them on samples.

### 127. Gaussian processes

**Definition:** A Bayesian non-parametric model that defines a distribution over functions, giving predictions with calibrated uncertainty.

**How it works:**
1. Assume any finite set of function values is jointly Gaussian, with covariance from a kernel k(x, x′) (#116), for example RBF or Matérn.
2. **Posterior prediction at x*:** mean = k*ᵀ (K + σ²I)⁻¹ y; variance = k(x*, x*) − k*ᵀ (K + σ²I)⁻¹ k*.
3. Fit kernel hyperparameters (length scale, signal variance, noise) by maximizing the marginal likelihood.
4. Uncertainty grows away from observed data.
5. **Scaling:** sparse or inducing-point approximations (m inducing points) for large n.

**Cost:** Exact O(n³). Sparse approximations O(n × m²).

**Agent use:**
- **Role:** Modeler.
- **How:** Small-data regression with honest uncertainty: performance modeling from few benchmarks, sensor interpolation, and the engine of Bayesian optimization (G92).
- **Rules:** Choose the kernel to match expected smoothness and periodicity.
- **Guardrails:** Exact GPs don't scale beyond about 10,000 points. Use sparse variants.

### 128. Alternating least squares for matrix factorization (implicit feedback)

**Definition:** Factorizing a user × item interaction matrix into low-dimensional user and item vectors, by alternately solving least-squares problems for each side.

**How it works:**
1. Model: preference ≈ u_userᵀ v_item.
2. **Implicit feedback version:** every user-item pair has preference 1 (interacted) or 0 (not), with confidence c = 1 + α × interaction count. Minimize Σ c (p − uᵀv)² + λ (‖u‖² + ‖v‖²) over all pairs.
3. **Alternate:** fix the item vectors and solve for every user vector in closed form (a small linear system each), then fix users and solve for items.
4. The trick: (VᵀCᵤV) = VᵀV + Vᵀ(Cᵤ − I)V, where the second term only involves the user's interacted items, so all-pairs sums are cheap.
5. Embarrassingly parallel per user and per item.

**Cost:** O(nnz × f² + (users + items) × f³) per iteration.

**Agent use:**
- **Role:** Modeler.
- **How:** Collaborative filtering for recommending documents, tools, products or content from interaction logs, at scale.
- **Rules:** Tune α, λ and the dimension f on time-ordered splits.
- **Guardrails:** Cold-start items and users have no vectors. Combine with content features.

### 129. Factorization machines

**Definition:** Models that capture all pairwise feature interactions through factorized (low-rank) interaction weights, working well with sparse data.

**How it works:**
1. Prediction = w₀ + Σ w_i x_i + Σ_{i<j} ⟨v_i, v_j⟩ x_i x_j, where each feature has a latent vector v_i.
2. Interactions between features never seen together in training can still be estimated (via their latent vectors).
3. The pairwise term can be computed in O(k × nonzeros) using: ½ Σ_f [(Σ_i v_if x_i)² − Σ_i v_if² x_i²].
4. Trained with SGD, ALS or MCMC.
5. **Field-aware FMs:** a separate latent vector per feature per other field, which is more expressive.

**Cost:** Linear in nonzero features.

**Agent use:**
- **Role:** Modeler.
- **How:** Click and conversion prediction, and recommendation with many sparse categorical features. A strong, cheap baseline before deep models (NN#191).
- **Rules:** Use as the baseline for deep recommenders.
- **Guardrails:** None specific.

## C6. Anomaly detection

### 130. Isolation forest

**Definition:** Detecting anomalies by how easily they're isolated by random splits: unusual points get isolated in fewer splits.

**How it works:**
1. Build many isolation trees, each on a small random subsample (for example 256 points).
2. Each tree splits recursively on a random feature at a random value between its min and max, until each point is alone (or a depth limit is reached).
3. Anomalies, being few and different, end up isolated close to the root (short paths).
4. **Anomaly score** = 2^(−average path length / c(n)), where c(n) normalizes by the expected path length for n points. Near 1 means anomalous; well below 0.5 means normal.
5. **Extended isolation forest:** random hyperplane splits, which removes axis-aligned artifacts.

**Cost:** Linear in data. Very fast.

**Agent use:**
- **Role:** Modeler.
- **How:** Unsupervised anomaly detection on tabular features: transactions, resource usage, request patterns.
- **Rules:** Set the contamination (expected anomaly fraction) from domain knowledge, or rank instead of thresholding.
- **Guardrails:** Anomalies are candidates for review, not verdicts (T8).

### 131. One-class SVM

**Definition:** Learning a boundary around normal data in a kernel feature space, so points outside it are flagged as anomalies.

**How it works:**
1. Train only on normal (or mostly normal) data.
2. Find the hyperplane separating the data from the origin with maximum margin in kernel space (#116), allowing a fraction ν of points outside.
3. ν is an upper bound on the fraction of training outliers and a lower bound on support vectors.
4. **Score:** signed distance to the boundary.

**Cost:** Kernel SVM costs (#115), so moderate data sizes.

**Agent use:**
- **Role:** Modeler.
- **How:** Anomaly detection when you have a clean sample of normal behavior and smooth boundaries matter.
- **Rules:** Scale features. Tune ν and the kernel width on validation data with some known anomalies.
- **Guardrails:** Sensitive to the kernel width. Validate thoroughly.

### 132. Robust covariance (minimum covariance determinant)

**Definition:** Estimating the center and covariance of data while ignoring outliers, so outliers can then be detected by their distance.

**How it works:**
1. Find the subset of h points (for example 75% of the data) whose covariance matrix has the smallest determinant: the tightest core of the data.
2. **FAST-MCD:** start from random subsets and repeatedly keep the h points closest (in Mahalanobis distance) to the current estimate, which converges quickly.
3. Compute the robust mean and covariance from that subset (with a consistency correction).
4. **Robust Mahalanobis distance** for each point. Large distances (beyond a chi-squared quantile) are outliers.

**Cost:** Moderate, for low to moderate dimensions.

**Agent use:**
- **Role:** Modeler.
- **How:** Detecting multivariate outliers in correlated metrics (CPU, memory and latency together), where each metric alone looks normal.
- **Rules:** Use when dimensions are modest (tens, not thousands).
- **Guardrails:** Assumes roughly elliptical normal data. Check the data's shape.

### 133. Seasonal hybrid ESD (S-H-ESD) anomaly detection

**Definition:** Detecting anomalies in seasonal time series by removing seasonality and trend, then applying a robust statistical test for outliers.

**How it works:**
1. Decompose the series into seasonal, trend and residual parts (STL decomposition), using the median instead of the trend for robustness.
2. Compute residuals: value − seasonal component − median.
3. **Generalized ESD test:** repeatedly find the largest residual (measured in robust units: deviation from the median divided by the median absolute deviation), test it against a critical value, and remove it. Repeat up to a maximum number of anomalies.
4. Every point that passes the test is an anomaly.

**Cost:** Linear per series.

**Agent use:**
- **Role:** Modeler.
- **How:** Anomaly detection on seasonal business and operational metrics (traffic with daily and weekly cycles), where simple thresholds fire on normal peaks.
- **Rules:** Set the period from the data's actual seasonality.
- **Guardrails:** Long anomalies distort the decomposition. Use robust decomposition.

## C7. Time series forecasting

### 134. ARIMA and seasonal ARIMA

**Definition:** Forecasting models combining autoregression (past values), differencing (removing trends) and moving averages (past errors), with seasonal extensions.

**How it works:**
1. **Differencing (d):** subtract the previous value (once or twice) until the series is stationary (checked with unit-root tests like ADF or KPSS).
2. **AR(p):** the value depends linearly on its last p values.
3. **MA(q):** it also depends on the last q forecast errors.
4. **SARIMA:** adds seasonal terms (P, D, Q) at the season length s (for example 7 days, 24 hours).
5. Fit by maximum likelihood. Choose orders by AIC/BIC (automated search), and check that residuals look like white noise (Ljung-Box test).
6. Exogenous variables (ARIMAX) for known drivers.

**Cost:** Fast per series.

**Agent use:**
- **Role:** Modeler.
- **How:** Forecasting individual metrics with clear autocorrelation, with prediction intervals.
- **Rules:** Compare against seasonal naive and exponential smoothing baselines (#135).
- **Guardrails:** Intervals assume the model's structure stays valid. Regime changes break them.

### 135. Exponential smoothing (ETS, Holt-Winters)

**Definition:** Forecasting by exponentially weighted averages of past observations, with separate components for level, trend and seasonality.

**How it works:**
1. **Simple exponential smoothing:** level ℓ_t = α y_t + (1 − α) ℓ_{t−1}. The forecast is the current level.
2. **Holt's method:** adds a trend component (optionally damped, so long-range forecasts flatten).
3. **Holt-Winters:** adds a seasonal component, additive or multiplicative.
4. **ETS framework:** state space models with error, trend and seasonal types (additive, multiplicative or none). Fit by maximum likelihood, choose the type by AIC, and get proper prediction intervals.

**Cost:** Very fast. Scales to millions of series.

**Agent use:**
- **Role:** Modeler.
- **How:** Robust automatic forecasting at scale: capacity, demand and traffic per service or region.
- **Rules:** Use damped trends by default for long horizons.
- **Guardrails:** None specific.

### 136. Decomposable forecasting models (Prophet-style)

**Definition:** Forecasting with an additive model of trend, seasonalities and holiday or event effects, fitted as a regression, designed for business series with known calendar effects.

**How it works:**
1. y(t) = trend(t) + seasonality(t) + holidays(t) + error.
2. **Trend:** piecewise linear (or logistic with a capacity limit), with automatically placed changepoints (with a sparse prior).
3. **Seasonality:** Fourier series per period (yearly, weekly, daily).
4. **Holidays and events:** indicator variables for known dates, with windows around them.
5. Fit as a Bayesian or regularized regression. Uncertainty comes from trend change simulation and observation noise.

**Cost:** Fast per series.

**Agent use:**
- **Role:** Modeler.
- **How:** Business metrics with strong calendar effects (holidays, campaigns, end-of-quarter), where analysts want interpretable components.
- **Rules:** Always benchmark against ETS and seasonal naive (#135). This model is often outperformed on accuracy.
- **Guardrails:** Trend extrapolation can be wildly off for long horizons. Check uncertainty bands.

### 137. Intermittent demand forecasting (Croston, SBA, TSB)

**Definition:** Forecasting series with many zeros and occasional demand (spare parts, rare events), by separately forecasting the size and the frequency of nonzero values.

**How it works:**
1. **Croston:** apply exponential smoothing separately to (a) the sizes of nonzero demands, (b) the intervals between them. Forecast rate = smoothed size / smoothed interval.
2. **SBA correction:** multiply by (1 − α/2) to fix Croston's upward bias.
3. **TSB:** smooth the probability of a nonzero demand each period instead of the interval, so the forecast decays toward zero when demand stops (obsolescence).
4. Evaluate with metrics suited to zeros (scaled errors, not percentage errors).

**Cost:** Very fast.

**Agent use:**
- **Role:** Modeler.
- **How:** Sparse series: rare incident types, infrequent large orders, low-volume API endpoints.
- **Rules:** Don't evaluate with MAPE (undefined with zeros).
- **Guardrails:** None specific.

### 138. Hierarchical forecast reconciliation (MinT)

**Definition:** Making forecasts across a hierarchy (total, per region, per service) add up consistently, while improving accuracy at every level.

**How it works:**
1. Forecast every series in the hierarchy independently ("base forecasts"). They usually don't add up.
2. **Simple methods:** bottom-up (sum the lowest level), top-down (split the total by proportions).
3. **MinT (minimum trace):** find adjusted forecasts that add up, as a weighted combination of all base forecasts, with weights from the base forecasts' error covariance (often shrunk, for stability).
4. The reconciled forecasts are coherent, and usually more accurate than the base forecasts at most levels.

**Cost:** One matrix computation per forecast run.

**Agent use:**
- **Role:** Modeler.
- **How:** Consistent capacity and demand plans across organizational or infrastructure hierarchies (global → region → cluster → service).
- **Rules:** Use shrinkage estimators for the error covariance.
- **Guardrails:** None specific.

### 139. Time-series cross-validation (rolling origin)

**Definition:** Evaluating forecasting models by repeatedly training on the past and testing on the following period, never on shuffled data.

**How it works:**
1. Choose a series of cutoff times.
2. For each cutoff: train on data up to the cutoff, forecast the next h periods, and record the errors.
3. **Expanding window:** the training data grows with each cutoff. **Sliding window:** fixed-length training data.
4. Add a gap between training and test periods when features use lagged information that would leak.
5. Aggregate the errors per horizon (errors usually grow with h).
6. **Metrics:** MASE (scaled by the naive forecast error), sMAPE with care, and quantile and interval coverage for probabilistic forecasts.

**Cost:** One model fit per cutoff.

**Agent use:**
- **Role:** Verifier.
- **How:** The only valid way to evaluate forecasts (T5): it simulates real forecasting conditions.
- **Rules:** Never use random k-fold on time series.
- **Guardrails:** Feature leakage (using information not available at the cutoff) inflates results. Audit feature timestamps.

## C8. Model selection, data preparation and ensembles

### 140. Cross-validation (k-fold, stratified, grouped, nested)

**Definition:** Estimating a model's performance on new data by training and testing on different splits of the available data.

**How it works:**
1. **k-fold:** split the data into k parts. Train on k−1 and test on the remaining one, rotating. Average the results.
2. **Stratified:** keep class proportions the same in every fold (for imbalanced classes).
3. **Group k-fold:** keep all rows of a group (user, account, session) in the same fold, so the model is tested on genuinely unseen groups.
4. **Nested cross-validation:** an inner loop tunes hyperparameters, an outer loop estimates the performance of the whole tuning procedure. Avoids optimistic bias from tuning on the evaluation data.
5. Report the mean and the spread across folds (T6).

**Cost:** k × training cost (k × k_inner for nested).

**Agent use:**
- **Role:** Verifier.
- **How:** Honest model evaluation and selection.
- **Rules:** Use group folds whenever rows from the same entity are correlated. Use time-based splits for temporal data (#139).
- **Guardrails:** Preprocessing (scaling, encoding, imputation, feature selection) must be fit inside each fold, or it leaks information.

### 141. Categorical encoding (one-hot, target encoding with smoothing, hashing)

**Definition:** Turning categorical values into numbers models can use, without leaking labels or exploding dimensions.

**How it works:**
1. **One-hot:** one binary column per category. Fine for low cardinality.
2. **Target (mean) encoding:** replace each category with the average target for that category, smoothed toward the global mean for rare categories: (n × category mean + m × global mean) / (n + m).
3. **Out-of-fold target encoding:** compute each row's encoding from the other folds only, which prevents leakage of its own label (see CatBoost's ordered approach, #112).
4. **Hashing:** map categories into a fixed number of buckets by hash. Handles unseen categories and huge cardinalities, with some collisions.
5. **Frequency encoding:** replace a category with its count.

**Cost:** Cheap.

**Agent use:**
- **Role:** Modeler.
- **How:** Handling IDs, codes and categories in tabular models correctly.
- **Rules:** Always use out-of-fold target encoding during training.
- **Guardrails:** In-fold target encoding is a classic silent leak that makes validation look great and production fail.

### 142. Missing value imputation (indicators, iterative imputation / MICE)

**Definition:** Handling missing data by filling it in sensibly and recording where values were missing.

**How it works:**
1. **Simple imputation:** median for numbers, most frequent value or "missing" category for categoricals.
2. **Missingness indicators:** add a binary feature "was missing", because missingness itself is often informative.
3. **Iterative imputation (MICE):** model each feature with missing values as a function of the others, imputing in rounds until the values stabilize. Multiple imputation produces several completed datasets, to carry uncertainty into the analysis.
4. **k-NN imputation:** fill from similar rows.
5. Many tree models handle missing values natively (#111).

**Cost:** Simple: negligible. MICE: several model fits per round.

**Agent use:**
- **Role:** Modeler.
- **How:** Making models robust to the incomplete data that's normal in production (missing telemetry, optional fields).
- **Rules:** Fit imputers on training folds only (#140). Always add missingness indicators for important features.
- **Guardrails:** Imputation can hide data quality problems. Monitor missing rates as a metric.

### 143. Feature selection (mutual information, recursive elimination, stability selection)

**Definition:** Choosing a smaller set of useful features, to improve generalization, speed and interpretability.

**How it works:**
1. **Filter methods:** rank features by a statistic independent of the final model: mutual information with the target, correlation, chi-squared.
2. **Wrapper methods:** recursive feature elimination: train, drop the least important feature (or several), repeat, and pick the best-performing feature count by cross-validation.
3. **Embedded methods:** L1 regularization (#102), tree-based importance (#114).
4. **Stability selection:** repeat selection on many subsamples, and keep the features chosen most consistently.

**Cost:** Filters: cheap. Wrappers: many model fits.

**Agent use:**
- **Role:** Modeler.
- **How:** Leaner, more robust models and simpler data pipelines (fewer features to compute and monitor).
- **Rules:** Do selection inside cross-validation folds (#140).
- **Guardrails:** Removing a sensitive feature doesn't remove bias if proxies remain (TX3).

### 144. SMOTE (synthetic minority oversampling)

**Definition:** Balancing imbalanced classes by creating synthetic minority examples between existing ones.

**How it works:**
1. For each minority example, find its k nearest minority neighbors.
2. Create a synthetic example at a random point on the line between the example and a randomly chosen neighbor.
3. Repeat until the desired class balance is reached.
4. **Variants:** Borderline-SMOTE (only near the class boundary), ADASYN (more synthesis where minority examples are harder), SMOTE-NC for categorical features.

**Cost:** Neighbor search on the minority class.

**Agent use:**
- **Role:** Modeler.
- **How:** One option for rare-class problems. Often, class weights or threshold tuning (NN#298) work as well or better, so compare.
- **Rules:** Apply only to training folds, never to validation or test data.
- **Guardrails:** Oversampling before splitting leaks synthetic copies of test points into training. Synthetic points can also distort calibration.

### 145. Stacking and blending ensembles

**Definition:** Combining several different models by training a "meta-model" on their predictions.

**How it works:**
1. Train several diverse base models (boosting, linear, k-NN, neural).
2. Produce out-of-fold predictions for every training row from each base model (#140).
3. Train a meta-model (often a regularized linear model) on those predictions to produce the final prediction.
4. At inference, the base models (trained on all data) feed the meta-model.
5. **Blending:** a simpler version using one held-out split instead of cross-validation.

**Cost:** The cost of all base models plus the meta-model.

**Agent use:**
- **Role:** Modeler.
- **How:** Squeezing out extra accuracy when it's worth the complexity (high-value predictions).
- **Rules:** Only out-of-fold predictions may train the meta-model.
- **Guardrails:** Operational complexity grows (many models to maintain and monitor). Weigh it against the gain.

### 146. Bagging (bootstrap aggregating)

**Definition:** Reducing a model's variance by training copies on bootstrap samples of the data and averaging their predictions.

**How it works:**
1. Draw B bootstrap samples (n rows with replacement).
2. Train the same model type on each.
3. Average the predictions (or take a vote).
4. Works best for high-variance, low-bias models (deep trees, k-NN with small k).
5. Out-of-bag estimates (#107) give free validation.
6. The bootstrap also gives prediction spread, a rough uncertainty estimate.

**Cost:** B× training cost, parallel.

**Agent use:**
- **Role:** Modeler.
- **How:** Stabilizing unstable models, and producing simple uncertainty estimates for any model.
- **Rules:** None specific.
- **Guardrails:** None specific.

### 147. AdaBoost

**Definition:** The original boosting algorithm: train weak models one after another, each focusing on the examples the previous ones got wrong, by reweighting examples.

**How it works:**
1. Start with equal weights on all examples.
2. Train a weak learner (often a one-split tree, a "stump") on the weighted data.
3. Compute its weighted error ε and its vote α = ½ ln((1 − ε)/ε).
4. Increase the weights of misclassified examples (multiply by e^α), decrease the others, and renormalize.
5. Repeat. The final prediction is the α-weighted vote of all weak learners.
6. It's equivalent to gradient boosting with exponential loss.

**Cost:** Sequential, with cheap weak learners.

**Agent use:**
- **Role:** Modeler.
- **How:** Mostly superseded by gradient boosting (#109–112), but still useful for very fast, compact models (cascade detectors).
- **Rules:** Prefer modern gradient boosting for accuracy.
- **Guardrails:** Very sensitive to label noise (mislabeled examples get huge weights).

### 148. Partial dependence, ICE and accumulated local effects (ALE)

**Definition:** Visualizing how a model's prediction changes as one feature changes, on average and for individual examples.

**How it works:**
1. **Partial dependence (PDP):** for each value v of a feature, set that feature to v for every row, predict, and average. Plot the average against v.
2. **ICE (individual conditional expectation):** the same, plotting one curve per row. Reveals interactions (curves with different shapes) that the average hides.
3. **ALE (accumulated local effects):** compute prediction changes within small intervals of the feature, using only rows actually in that interval, then accumulate. Avoids PDP's unrealistic combinations when features are correlated.
4. Two-feature versions show interactions.

**Cost:** Many predictions per feature.

**Agent use:**
- **Role:** Analyst.
- **How:** Explaining and sanity-checking models: does risk rise with overdue days as expected? Also verifies monotonic constraints (#113).
- **Rules:** Use ALE when features are correlated.
- **Guardrails:** These show model behavior, not real-world causal effects.

## C9. Online learning and drift

### 149. Online learning with FTRL-Proximal

**Definition:** Training linear models (especially logistic regression) one example at a time on huge, sparse data streams, producing sparse weights.

**How it works:**
1. Process examples as they arrive, updating weights after each one.
2. **FTRL-Proximal (follow-the-regularized-leader):** keep per-feature accumulated gradients z_i and squared gradient sums n_i.
3. Each weight is computed in closed form from z_i and n_i, with L1 and L2 terms. Features with small accumulated evidence get weight exactly 0 (sparsity).
4. **Per-coordinate learning rates:** α / (β + √n_i), so frequent features take smaller steps.
5. Combine with feature hashing (#141) for unbounded feature spaces.

**Cost:** O(nonzero features) per example.

**Agent use:**
- **Role:** Modeler.
- **How:** Continuously updated models on event streams (click prediction, spam scoring, routing), learning from new data within minutes. A natural fit for streaming pipelines (Part 1).
- **Rules:** Monitor online metrics (progressive validation: evaluate each example before training on it).
- **Guardrails:** Online models can learn from manipulated or poisoned streams quickly. Monitor for sudden weight shifts (#150).

### 150. Concept drift detection (DDM, ADWIN, Page-Hinkley)

**Definition:** Detecting when the relationship between inputs and outcomes (or the data distribution) changes, so models can be retrained or adjusted.

**How it works:**
1. **DDM (drift detection method):** track the model's online error rate p and its standard deviation s. Record the minimum p + s. Warn when the current value exceeds that minimum + 2s, and signal drift at + 3s.
2. **ADWIN (adaptive windowing):** keep a variable-length window of recent values. If two sub-windows have significantly different means (by a bound derived from Hoeffding's inequality), drop the older part. The window shrinks automatically after changes.
3. **Page-Hinkley:** a cumulative sum of deviations from the running mean. Signal when the cumulative deviation exceeds a threshold (CUSUM-style).
4. **Distribution drift** on inputs without labels: compare feature distributions over time (PSI, KS, V#170).

**Cost:** O(1) or O(log n) per observation.

**Agent use:**
- **Role:** Verifier.
- **How:** Monitors production models, and triggers retraining or alerts when performance or data drift.
- **Rules:** Distinguish label-based drift (needs feedback, slower) from input drift (fast, but doesn't always hurt performance).
- **Guardrails:** Drift alerts trigger review and evaluation (T8). Automatic retraining needs the same promotion gates as any model release.

---
