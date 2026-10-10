# Part 4: Experimentation and statistics (#151–200)

Same format and the same contract (roles; rules T1–T8; guardrails TX1–TX5). This is the final part. Already covered elsewhere and not repeated: interleaving (V#166), bandits (G89), conformal prediction (NN#270), causal DAGs, d-separation, PC/FCI and do-calculus (graph #279–281), KS and PSI drift tests (V#170), change-point detection (graph #215, G89), off-policy evaluation (NN#205).

## D1. Testing foundations

### 151. Hypothesis testing framework (p-values, significance, power, MDE)

**Definition:** The standard framework for deciding whether an observed difference (between treatment and control) is larger than random noise would plausibly produce.

**How it works:**
1. **Null hypothesis H₀:** no difference. **Alternative H₁:** there is a difference.
2. **Test statistic:** for example (difference in means) / (standard error).
3. **p-value:** the probability of a statistic at least this extreme if H₀ were true. Small p-values are evidence against H₀.
4. **Significance level α** (for example 0.05): reject H₀ if p < α. That's the accepted false positive rate.
5. **Power (1 − β):** the probability of detecting a true effect of a given size. **MDE (minimum detectable effect):** the smallest effect detectable with the chosen power and α, for the available sample size.
6. Report effect sizes with **confidence intervals**, not only p-values.

**Cost:** Cheap computation. The real cost is sample size (#157).

**Agent use:**
- **Role:** Experimenter.
- **How:** The base of every experiment readout and decision.
- **Rules:** T5: fix the hypothesis, metric, α, power and MDE before launching. Report effects with confidence intervals (T6).
- **Guardrails:** A non-significant result isn't proof of no effect. Report the interval and the MDE (what effect sizes are ruled out).

### 152. t-tests and Welch's t-test

**Definition:** Tests comparing the means of two groups, with Welch's version not assuming equal variances.

**How it works:**
1. **Statistic:** t = (mean₁ − mean₂) / √(s₁²/n₁ + s₂²/n₂) (Welch's form).
2. **Degrees of freedom** from the Welch-Satterthwaite approximation.
3. Compare with the t distribution to get the p-value and confidence interval.
4. With large samples (common online), the central limit theorem makes it valid even for non-normal metrics, as long as they aren't extremely heavy-tailed (#164, #189).
5. **Paired t-test:** for before/after measurements on the same units.

**Cost:** O(n).

**Agent use:**
- **Role:** Experimenter.
- **How:** The default test for mean metrics in A/B tests (revenue per user, latency mean, sessions).
- **Rules:** Use Welch's version by default.
- **Guardrails:** The randomization unit must match the analysis unit. If randomized by user but analyzed per request, standard errors are wrong (#156, #192).

### 153. Tests for proportions (z-test, chi-squared, Fisher's exact test)

**Definition:** Tests comparing rates (conversion, error rate, click-through) between groups.

**How it works:**
1. **Two-proportion z-test:** z = (p₁ − p₂) / √(p̂(1 − p̂)(1/n₁ + 1/n₂)), with p̂ the pooled rate.
2. **Chi-squared test:** for contingency tables with several categories or groups: Σ (observed − expected)² / expected.
3. **Fisher's exact test:** for small counts, computing exact probabilities from the hypergeometric distribution.
4. **Confidence intervals** for the difference (Wald, or better, Newcombe/Wilson-based intervals for small rates).

**Cost:** Cheap.

**Agent use:**
- **Role:** Experimenter.
- **How:** Conversion and error-rate comparisons.
- **Rules:** Use exact or Wilson-type intervals when rates are near 0 or 1, or counts are small.
- **Guardrails:** Same unit-of-analysis caution as #152.

### 154. Nonparametric tests (Mann-Whitney U, permutation tests)

**Definition:** Tests that don't assume a particular distribution, comparing ranks (Mann-Whitney) or using reshuffling of group labels (permutation).

**How it works:**
1. **Mann-Whitney U:** rank all observations together. Compare the rank sums of the two groups. It tests whether one group tends to have larger values (stochastic dominance), not specifically whether means differ.
2. **Permutation test:** compute the observed difference in any statistic. Shuffle the group labels many times, recomputing the statistic each time. The p-value is the fraction of shuffles with a difference as large as observed.
3. Permutation tests work with any statistic (medians, ratios, custom metrics), and are exact under random assignment.

**Cost:** Mann-Whitney O(n log n). Permutation: many recomputations.

**Agent use:**
- **Role:** Experimenter.
- **How:** Heavy-tailed or unusual metrics, small samples, and any custom statistic where formulas don't exist.
- **Rules:** State what the test actually tests (Mann-Whitney is not a test of means or medians in general).
- **Guardrails:** Permutation must respect the randomization unit: shuffle labels at the unit level (users, clusters), not individual events.

### 155. Bootstrap confidence intervals (percentile, BCa)

**Definition:** Estimating a statistic's uncertainty by resampling the data with replacement many times and looking at the spread of the recomputed statistic.

**How it works:**
1. Resample n units with replacement from the data (B times, for example 1,000–10,000).
2. Compute the statistic on each resample.
3. **Percentile interval:** the 2.5th and 97.5th percentiles of the bootstrap statistics.
4. **BCa (bias-corrected and accelerated):** adjusts for bias and skewness, which gives better coverage.
5. Resample at the randomization unit level (users, not events).
6. **Poisson bootstrap:** give each unit a Poisson(1) weight instead of resampling, which is easy to distribute and to compute on streams.

**Cost:** B recomputations of the statistic.

**Agent use:**
- **Role:** Experimenter.
- **How:** Confidence intervals for complex statistics: percentiles, ratios, medians, custom metrics.
- **Rules:** Use BCa intervals by default for skewed statistics.
- **Guardrails:** The bootstrap struggles with extreme quantiles and very small samples. Check its behavior with A/A tests (#160).

### 156. Delta method for ratio metrics

**Definition:** Approximating the variance of a function of estimates (such as a ratio of two means), needed when the metric's denominator is random.

**How it works:**
1. **Ratio metrics:** for example clicks per page view, or errors per request, when randomized by user. Numerator X and denominator Y are both per-user sums.
2. The metric R = mean(X) / mean(Y). Its variance isn't simply the variance of per-event outcomes, because events within a user are correlated.
3. **Delta method (first-order Taylor expansion):** Var(R) ≈ (1/μ_Y²) × [Var(X̄) − 2R × Cov(X̄, Ȳ) + R² × Var(Ȳ)].
4. Compute the per-user variances and covariance, then the standard error and confidence interval.
5. It also applies to relative effects (percentage lift = treatment / control − 1).

**Cost:** O(n).

**Agent use:**
- **Role:** Experimenter.
- **How:** Correct standard errors for ratio metrics, which are among the most common online metrics (CTR, latency per request, error rate per request).
- **Rules:** Always use the delta method (or a unit-level bootstrap) for ratio metrics with user-level randomization.
- **Guardrails:** Treating events as independent underestimates variance badly, producing false positives.

### 157. Power analysis and sample size calculation

**Definition:** Calculating how many units (or how long) an experiment needs to detect an effect of a given size with given confidence.

**How it works:**
1. **Inputs:** α, desired power (often 0.8), the metric's variance (from historical data), and the MDE.
2. **For two equal groups:** n per group ≈ 2 × (z_{1−α/2} + z_{1−β})² × σ² / MDE².
3. **Proportions:** σ² = p(1 − p).
4. Adjust for variance reduction (#161–163), unequal splits, clustering (#171), and multiple metrics (#168).
5. Convert to duration with expected traffic, and cover whole weekly cycles.

**Cost:** Negligible.

**Agent use:**
- **Role:** Experimenter.
- **How:** Sets experiment size and duration before launch (T5), and rejects experiments that can't detect any realistic effect ("underpowered").
- **Rules:** Use historical variance from the actual metric and population.
- **Guardrails:** Never extend an experiment because results "look close", without sequential methods (#165, #166). That's peeking.

## D2. Randomization and validity checks

### 158. Randomization and hash-based bucketing

**Definition:** Assigning units to experiment variants randomly but deterministically, so each unit always gets the same variant.

**How it works:**
1. Compute hash(unit ID + experiment salt) into a bucket number (for example 0–9,999).
2. Map bucket ranges to variants (for example 0–4,999 control, 5,000–9,999 treatment).
3. The same unit always lands in the same bucket for the same experiment. Different salts give independent assignments across experiments.
4. **Randomization unit:** user, session, device, account, or cluster (#171), chosen by where the treatment's effects stay contained.
5. Log every exposure (when a unit actually experienced the variant).

**Cost:** One hash per assignment.

**Agent use:**
- **Role:** Experimenter.
- **How:** Consistent, reproducible assignments for experiments, feature rollouts and holdouts.
- **Rules:** Use a new salt per experiment, so previous experiments' assignments don't correlate with new ones (carryover).
- **Guardrails:** Changing the split percentages mid-experiment changes the populations. Treat it as a new experiment.

### 159. Sample ratio mismatch (SRM) check

**Definition:** Checking that the observed split of units between variants matches the designed split, which detects broken assignment or logging.

**How it works:**
1. Expected counts from the design (for example 50/50).
2. Chi-squared goodness-of-fit test on the observed counts.
3. A very small p-value (for example < 0.001) means the split is off beyond chance.
4. **Common causes:** bots filtered differently between variants, redirects or crashes dropping users in one variant, logging differences, assignment bugs.
5. Investigate by segment (browser, platform, date) to find the cause.

**Cost:** Negligible.

**Agent use:**
- **Role:** Verifier.
- **How:** A mandatory check before reading any experiment result. A mismatch invalidates the comparison.
- **Rules:** Block result readouts when SRM is detected (T5).
- **Guardrails:** Never "correct" an SRM by reweighting without finding its cause. The missing units are usually not random.

### 160. A/A tests

**Definition:** Running experiments where both variants are identical, to verify that the experimentation system and statistics behave correctly.

**How it works:**
1. Assign units to two identical variants.
2. Run the full analysis pipeline on all metrics.
3. About 5% of metrics should be "significant" at α = 0.05, purely by chance.
4. Repeat many A/A tests (or simulate them on historical data with random splits): p-values should be uniformly distributed.
5. Too many significant results means the variance estimates are wrong (for example from ignoring clustering, #156, #192).

**Cost:** Traffic or simulation.

**Agent use:**
- **Role:** Verifier.
- **How:** Validates the experiment platform, new metrics and new analysis methods before trusting them.
- **Rules:** Run simulated A/A tests on every new metric definition.
- **Guardrails:** None specific.

## D3. Variance reduction

### 161. CUPED (controlled experiments using pre-experiment data)

**Definition:** Reducing the variance of experiment metrics by adjusting each unit's outcome with its own pre-experiment behavior.

**How it works:**
1. For each unit, a covariate X measured before the experiment (usually the same metric in a pre-period).
2. θ = Cov(Y, X) / Var(X), estimated on pooled data.
3. **Adjusted outcome:** Y_cuped = Y − θ × (X − mean(X)).
4. Compare treatment and control on Y_cuped. The effect estimate stays unbiased (randomization makes X balanced), and variance drops by a factor of (1 − ρ²), where ρ is the correlation between Y and X.
5. Units without pre-period data get X = mean (or a separate indicator).

**Cost:** Negligible.

**Agent use:**
- **Role:** Experimenter.
- **How:** Often cuts the needed sample size by 20–50% or more for metrics that are stable per user. Faster, cheaper experiments.
- **Rules:** The covariate must be measured strictly before assignment.
- **Guardrails:** Covariates affected by the treatment bias the estimate. Use only pre-treatment data.

### 162. Stratification and post-stratification

**Definition:** Reducing variance by accounting for known subgroups (platform, country, user tenure), either in the assignment or in the analysis.

**How it works:**
1. **Stratified randomization:** randomize separately within each stratum, so each stratum is balanced by design.
2. **Post-stratification:** after a simple randomization, compute the effect within each stratum, then combine with weights equal to the strata's population shares.
3. Variance drops when strata differ a lot in their outcome levels.
4. Equivalent to regression adjustment with stratum indicators (#163).

**Cost:** Negligible.

**Agent use:**
- **Role:** Experimenter.
- **How:** Variance reduction when strong segment differences exist, and balanced designs for small experiments.
- **Rules:** Define strata before the experiment (T5).
- **Guardrails:** Too many tiny strata make estimates unstable. Merge small ones.

### 163. Regression adjustment (ANCOVA, Lin's estimator)

**Definition:** Estimating treatment effects with a regression of the outcome on the treatment indicator plus pre-treatment covariates, which reduces variance.

**How it works:**
1. Regress Y on treatment T and covariates X (pre-treatment only).
2. The coefficient on T is the treatment effect estimate.
3. **Lin's estimator:** include treatment × centered-covariate interactions. Guarantees no loss of precision compared with the simple difference, even if the model is wrong, under randomization.
4. Use robust (sandwich) standard errors (#192).
5. CUPED (#161) is the special case with one covariate.

**Cost:** One regression.

**Agent use:**
- **Role:** Experimenter.
- **How:** Combines several pre-period covariates for more variance reduction than CUPED alone.
- **Rules:** Pre-register the covariates (T5, TX5).
- **Guardrails:** Choosing covariates after looking at results is a form of p-hacking (TX5).

### 164. Winsorization and capping of heavy-tailed metrics

**Definition:** Limiting extreme values in a metric (for example revenue or session time per user) to reduce variance from a few outliers.

**How it works:**
1. Choose a cap, typically a high percentile (99th or 99.9th) computed on pooled data (or pre-period data), independent of the variant.
2. Replace values above the cap with the cap.
3. Analyze the capped metric with the usual tests.
4. Variance drops dramatically when a few extreme users dominate.
5. The estimand changes: you're estimating the effect on the capped metric.

**Cost:** Negligible.

**Agent use:**
- **Role:** Experimenter.
- **How:** Makes revenue and engagement metrics usable in experiments, where one whale user can swing results.
- **Rules:** Pre-specify the cap rule (T5). Report the uncapped result too, as a secondary check.
- **Guardrails:** If the treatment specifically affects extreme users, capping hides the effect. Check the tails separately.

## D4. Sequential and Bayesian testing

### 165. Group sequential designs and alpha spending (O'Brien-Fleming, Pocock)

**Definition:** Allowing a fixed number of planned interim analyses during an experiment, with adjusted significance thresholds so the total false positive rate stays at α.

**How it works:**
1. **The peeking problem:** checking a standard test repeatedly and stopping at the first significant result inflates false positives far above α.
2. Plan K analyses (for example 5, at equal information intervals).
3. **Alpha spending function:** decides how much of α is "spent" at each look.
   - **O'Brien-Fleming:** very strict early thresholds, close to the full α at the end.
   - **Pocock:** the same threshold at every look.
4. Stop early for efficacy if a threshold is crossed. Futility boundaries allow stopping when success is unlikely.
5. Lan-DeMets versions allow unplanned timing of looks.

**Cost:** Slightly larger maximum sample size than a fixed design.

**Agent use:**
- **Role:** Experimenter.
- **How:** Stopping clearly winning or harmful experiments early, while keeping valid error rates.
- **Rules:** The number of looks and the spending function are fixed in advance (T5).
- **Guardrails:** Early stops overestimate effect sizes (#198). Report adjusted estimates.

### 166. Always-valid inference (mSPRT, confidence sequences)

**Definition:** Methods that let you check results continuously at any time and stop whenever, while keeping the false positive rate guaranteed.

**How it works:**
1. **mSPRT (mixture sequential probability ratio test):** compute a likelihood ratio averaged over a prior (mixture) of possible effect sizes. Reject H₀ when the ratio exceeds 1/α. Valid at any stopping time.
2. **Always-valid p-values:** a running minimum of 1 / likelihood ratio, which can be checked anytime.
3. **Confidence sequences:** a sequence of intervals that contain the true effect at every time simultaneously, with probability 1 − α. They're wider than fixed-time intervals early on.
4. The mixture's scale parameter is tuned for the expected effect sizes.

**Cost:** Some loss of power compared with a fixed design, in exchange for flexibility.

**Agent use:**
- **Role:** Experimenter.
- **How:** Continuous monitoring dashboards and automated rollout guardrails (#195), where people (and agents) will look at results anytime.
- **Rules:** Use always-valid methods whenever results are monitored continuously.
- **Guardrails:** None specific.

### 167. Bayesian A/B testing (beta-binomial, expected loss)

**Definition:** Analyzing experiments by computing posterior distributions of each variant's metric, and deciding with probabilities and expected losses instead of p-values.

**How it works:**
1. **Conversion rates:** a Beta prior per variant. Update with the observed successes and failures, giving a Beta posterior.
2. P(treatment > control) = the probability, computed by sampling from both posteriors or in closed form.
3. **Expected loss:** the expected amount you'd lose by choosing a variant if it were actually worse. Ship when the expected loss is below a threshold of caring.
4. **Continuous metrics:** normal or Student-t models, or hierarchical models (#191).
5. Priors from historical experiments make estimates more realistic (#198).

**Cost:** Cheap.

**Agent use:**
- **Role:** Experimenter.
- **How:** Decision-oriented readouts ("94% chance treatment is better; expected loss if wrong: 0.02%") that stakeholders understand.
- **Rules:** Document the priors and the decision rule in advance (T5).
- **Guardrails:** Bayesian results are still affected by optional stopping when decision thresholds are naive. Use expected-loss thresholds, and don't treat P(better) alone as a stopping rule.

## D5. Multiple testing and metric design

### 168. Family-wise error control (Bonferroni, Holm)

**Definition:** Adjusting for many simultaneous tests, so the probability of at least one false positive across all of them stays at α.

**How it works:**
1. **Bonferroni:** test each of m hypotheses at α/m. Simple and conservative.
2. **Holm:** sort the p-values ascending. Compare the k-th smallest with α/(m − k + 1). Reject while comparisons pass, and stop at the first failure. Uniformly more powerful than Bonferroni, with the same guarantee.
3. Use when any single false positive is costly (for example primary decision metrics or guardrails that trigger rollbacks).

**Cost:** Negligible.

**Agent use:**
- **Role:** Experimenter.
- **How:** Correct inference with several primary metrics or several treatment arms.
- **Rules:** Pre-declare which metrics are primary (T5).
- **Guardrails:** None specific.

### 169. False discovery rate control (Benjamini-Hochberg)

**Definition:** Controlling the expected fraction of false positives among the results declared significant, which is less strict than family-wise control and suits many exploratory metrics.

**How it works:**
1. Sort the m p-values ascending: p₁ ≤ … ≤ p_m.
2. Find the largest k with p_k ≤ (k/m) × q, where q is the target FDR (for example 0.05 or 0.1).
3. Declare hypotheses 1…k significant.
4. Valid under independence and positive dependence. The Benjamini-Yekutieli version handles arbitrary dependence (more conservative).

**Cost:** Negligible.

**Agent use:**
- **Role:** Experimenter.
- **How:** Scanning many secondary metrics or segments, where some false discoveries are acceptable but should be limited.
- **Rules:** Label FDR-controlled findings as exploratory.
- **Guardrails:** Segment "discoveries" need confirmation in a new experiment before action (TX5).

### 170. Overall evaluation criterion and guardrail metrics

**Definition:** Designing the metric set for experiments: one primary decision metric (the OEC) that reflects long-term value, plus guardrails that must not degrade.

**How it works:**
1. **OEC:** a metric (or weighted combination) that predicts long-term value and is sensitive enough to move within an experiment (for example sessions per user, task success rate).
2. **Guardrails:** metrics that must not get worse: latency, error rates, crashes, unsubscribes, cost, safety signals.
3. **Debugging metrics:** detailed metrics explaining why the OEC moved.
4. **Validation:** check that the OEC moves in the expected direction in known-good and known-bad historical experiments (directionality), and that it's sensitive enough (power, #157).
5. **Decision rule:** ship when the OEC improves significantly and no guardrail degrades beyond its tolerance.

**Cost:** Design effort.

**Agent use:**
- **Role:** Experimenter.
- **How:** Consistent, defensible launch decisions across many experiments.
- **Rules:** Every experiment declares its OEC, guardrails and decision rule before launch (T5).
- **Guardrails:** Optimizing short-term engagement metrics can harm users. Include quality and well-being guardrails (TX3).

## D6. Complex experimental designs

### 171. Cluster randomization and intraclass correlation

**Definition:** Randomizing groups (teams, stores, regions, accounts) instead of individuals, when individuals within a group affect each other, and analyzing with the right variance.

**How it works:**
1. Assign whole clusters to variants.
2. Outcomes within a cluster are correlated: the intraclass correlation ρ.
3. **Design effect:** variance inflates by 1 + (m − 1) ρ, where m is the average cluster size. The effective sample size is much smaller than the number of individuals.
4. Analyze at the cluster level, or with cluster-robust standard errors (#192) or mixed models.
5. Need enough clusters (not just enough individuals): ideally dozens or more per arm.

**Cost:** Much larger sample sizes for the same power.

**Agent use:**
- **Role:** Experimenter.
- **How:** Experiments on shared features (team tools, marketplace pricing per region, B2B accounts).
- **Rules:** Power calculations use the design effect (#157).
- **Guardrails:** Analyzing clustered data as individual data produces false positives. A/A-check the method (#160).

### 172. Switchback experiments

**Definition:** Alternating the whole system (or a region) between treatment and control over time periods, for interventions that affect everyone at once (pricing algorithms, dispatch, matching).

**How it works:**
1. Split time into periods (for example 1 hour), per region.
2. Randomly assign each (region, period) to treatment or control.
3. Compare the outcomes across periods, accounting for time effects (hour of day, day of week) with regression or stratification.
4. **Carryover:** effects from one period can spill into the next. Use washout buffers (exclude the start of each period), or model the carryover.
5. Choose the period length to balance carryover (longer is better) and sample size (more periods is better).

**Cost:** Needs many periods for power.

**Agent use:**
- **Role:** Experimenter.
- **How:** Testing system-wide algorithms (schedulers, routing policies, autoscaling settings, cache policies) where user-level randomization is impossible.
- **Rules:** Randomize the period assignments (no fixed alternation patterns that align with cycles).
- **Guardrails:** Carryover biases results. Check by comparing early and late parts of periods.

### 173. Network experiments (graph cluster randomization)

**Definition:** Experiments on networks where treated units affect untreated neighbors (interference), designed by randomizing clusters of the network.

**How it works:**
1. **Interference:** a user's outcome depends on their friends' or counterparts' treatment (messaging features, marketplaces), which biases naive estimates.
2. Partition the graph into clusters with few edges between them (graph #152, #170).
3. Randomize whole clusters, so most of a unit's neighbors share its variant.
4. Estimate effects with exposure models (for example a unit counts as "fully treated" if more than 80% of its neighbors are treated), with appropriate variance estimation.
5. **Ego-network designs** and two-level designs (randomize clusters, then individuals within them) measure spillover directly.

**Cost:** Fewer effective units, so less power.

**Agent use:**
- **Role:** Experimenter.
- **How:** Correct effect estimates for social, communication and marketplace features.
- **Rules:** Report the estimated spillover alongside the direct effect.
- **Guardrails:** None specific.

### 174. Long-term effects (holdouts and surrogate indices)

**Definition:** Estimating the long-term impact of changes that experiments can only observe for a short time.

**How it works:**
1. **Long-term holdouts:** keep a small group (for example 1–5%) without a set of features for months, and compare long-term outcomes (retention, revenue).
2. **Surrogate index:** using historical data, build a model predicting the long-term outcome from short-term metrics (the surrogates). Apply it to the short-term experiment results to estimate the long-term effect.
3. **Validity condition:** the treatment must affect the long-term outcome only through the surrogates. Check with past experiments that had both short and long measurements.
4. **Cumulative holdouts** measure the combined effect of many launches.

**Cost:** Holdouts forgo improvements for some users. Surrogate models need historical data.

**Agent use:**
- **Role:** Experimenter.
- **How:** Avoids shipping changes that win short-term metrics and lose long-term value.
- **Rules:** Validate surrogate models on past experiments before using them.
- **Guardrails:** Holdout users miss improvements (including fixes). Never hold back safety or security fixes (TX3).

### 175. Heterogeneous treatment effects (causal forests)

**Definition:** Estimating how a treatment's effect varies across individuals, based on their characteristics, with honest uncertainty.

**How it works:**
1. **Causal trees:** split the data on covariates to maximize differences in treatment effect between leaves (not differences in outcome).
2. **Honesty:** one part of the data chooses the splits, another estimates the effects in the leaves. That gives valid confidence intervals.
3. **Causal forest:** average many honest causal trees (with subsampling), giving a personalized effect estimate τ(x) for each individual.
4. Inference uses an infinitesimal jackknife (or similar) for confidence intervals.
5. Summarize with the best linear projection of τ(x) on key covariates, and calibration tests.

**Cost:** Like random forests (#107).

**Agent use:**
- **Role:** Experimenter.
- **How:** Finds who benefits or is harmed by a change, to target rollouts and catch harm to subgroups.
- **Rules:** Treat discovered subgroups as hypotheses. Confirm them in new experiments (TX5).
- **Guardrails:** Targeting by protected characteristics needs governance review (TX3).

### 176. Uplift modeling (meta-learners: S, T and X-learners)

**Definition:** Predicting the incremental effect of a treatment for each individual (who would respond because of the treatment), using standard ML models arranged in specific ways.

**How it works:**
1. **S-learner:** one model with the treatment as a feature. Uplift = prediction(x, T = 1) − prediction(x, T = 0).
2. **T-learner:** separate models for treated and control. Uplift = difference of their predictions.
3. **X-learner:** fit T-learner models, compute imputed individual effects for each group (actual outcome minus the other group's model prediction), fit models on those, and combine them weighted by propensity. Good when groups are unbalanced.
4. **Evaluation:** Qini and uplift curves (sorting individuals by predicted uplift and checking the actual effect in each bucket), on randomized data.

**Cost:** A few model fits.

**Agent use:**
- **Role:** Experimenter and Modeler.
- **How:** Targeting interventions where they make a difference (offers, notifications, retention outreach), instead of where outcomes are simply likely.
- **Rules:** Train and evaluate on randomized experiment data.
- **Guardrails:** Uplift targeting decisions affecting people are proposals (T8). Check for unfair targeting (TX3).

### 177. Novelty and primacy effect detection

**Definition:** Detecting effects that change over time because users react to the newness of a change (novelty: initial excitement fades; primacy: initial resistance fades).

**How it works:**
1. Compute the treatment effect per day (or per exposure day, by how long each user has seen the treatment).
2. Look for a trend: a decaying effect suggests novelty, a growing effect suggests learning or primacy.
3. **Cohort analysis:** compare users by their first exposure date, tracking each cohort's effect as their exposure age grows.
4. Run experiments long enough for the effect to stabilize, or extrapolate the trend with care.

**Cost:** Requires longer experiments.

**Agent use:**
- **Role:** Experimenter.
- **How:** Avoids shipping decisions based on temporary novelty spikes (common for UI changes).
- **Rules:** Always check effect-over-time plots before deciding.
- **Guardrails:** None specific.

### 178. Trigger analysis and dilution

**Definition:** Analyzing only the users who could actually have experienced the change (the triggered population), then translating the effect back to the whole population.

**How it works:**
1. **Triggering:** log exactly when a user reaches the point where treatment and control differ (for example, opens the changed page). Ideally log it counterfactually in control too: "would have seen the change".
2. Analyze only triggered users in both variants. Effects aren't diluted by users who never encountered the change, which gives much more power.
3. **Dilution to the overall effect:** overall effect ≈ triggered effect × (triggered users' share of the metric).
4. Check the triggering is balanced: an SRM check on triggered users (#159).

**Cost:** Requires counterfactual trigger logging.

**Agent use:**
- **Role:** Experimenter.
- **How:** Much more sensitive experiments for features used by a small fraction of users.
- **Rules:** Triggering conditions must be identical in both variants (counterfactual logging in control).
- **Guardrails:** Triggers that depend on the treatment itself bias the comparison. Verify with SRM checks.

## D7. Causal inference from observational data

### 179. Difference-in-differences (DiD)

**Definition:** Estimating a causal effect by comparing the before/after change in a treated group with the before/after change in an untreated group.

**How it works:**
1. Effect = (treated after − treated before) − (control after − control before).
2. Removes fixed differences between groups and common time trends.
3. **Key assumption (parallel trends):** without treatment, both groups would have changed the same way. Check pre-period trends.
4. Regression form: Y = α + β × treated + γ × post + δ × (treated × post). δ is the effect. Use cluster-robust standard errors (#192).
5. **Staggered adoption** (units treated at different times) needs modern estimators (Callaway-Sant'Anna, Sun-Abraham), because the classic two-way fixed effects estimator can be biased.

**Cost:** Cheap.

**Agent use:**
- **Role:** Experimenter.
- **How:** Measuring the impact of changes rolled out without randomization: a feature launched in one region, a policy change for some customers.
- **Rules:** Always show pre-trend plots. Run placebo tests (fake treatment dates).
- **Guardrails:** Results depend on assumptions. Report them explicitly with the estimate (T6).

### 180. Synthetic control

**Definition:** Building a weighted combination of untreated units that closely matches the treated unit before treatment, and using it as the counterfactual afterward.

**How it works:**
1. One treated unit (a region, a product, a market) and a pool of untreated units.
2. Find non-negative weights (summing to 1) for the pool units, so the weighted combination matches the treated unit's pre-treatment outcomes (and covariates).
3. After treatment, the effect = treated outcome − synthetic outcome.
4. **Inference by placebo tests:** apply the method to each control unit as if it were treated. The real effect should be unusually large compared with the placebo effects.
5. Variants: augmented synthetic control, synthetic difference-in-differences.

**Cost:** One optimization per unit.

**Agent use:**
- **Role:** Experimenter.
- **How:** Measuring impact when only one or a few units were treated (a launch in one country, a migration of one cluster).
- **Rules:** Require a good pre-treatment fit. Report the placebo distribution.
- **Guardrails:** Poor pre-period fit makes the estimate unreliable. Don't report it then.

### 181. Regression discontinuity

**Definition:** Estimating causal effects where treatment is assigned by a threshold on a score, by comparing units just above and just below the threshold.

**How it works:**
1. A running variable (score) and a cutoff: units above get treatment (for example, a feature for accounts over 1,000 users, or a discount above a spending threshold).
2. Near the cutoff, units are nearly identical except for treatment.
3. Fit local regressions (often local linear) on each side within a bandwidth, and measure the jump at the cutoff.
4. Choose the bandwidth with data-driven methods, and check robustness to different bandwidths.
5. **Validity checks:** no manipulation of the score around the cutoff (density test), and covariates continuous across the cutoff.
6. **Fuzzy RD:** when the cutoff only changes the probability of treatment (use #182 logic).

**Cost:** Cheap.

**Agent use:**
- **Role:** Experimenter.
- **How:** Measuring the effects of threshold-based rules already in place: eligibility rules, tier boundaries, alert thresholds.
- **Rules:** Run the manipulation and covariate checks.
- **Guardrails:** The effect is only valid near the cutoff. Don't extrapolate to everyone.

### 182. Instrumental variables (two-stage least squares)

**Definition:** Estimating causal effects when the treatment is confounded, using a variable (instrument) that shifts the treatment but affects the outcome only through it.

**How it works:**
1. **Instrument Z requirements:** it affects the treatment (relevance), and it affects the outcome only through the treatment, with no confounding (exclusion and independence).
2. **Classic example:** a randomized encouragement (an invitation to use a feature) as the instrument for actual feature use.
3. **Stage 1:** regress the treatment on Z (and covariates).
4. **Stage 2:** regress the outcome on the predicted treatment from stage 1. Its coefficient is the causal effect for "compliers" (units whose treatment changes because of Z).
5. Use proper IV standard errors. Check instrument strength (first-stage F-statistic): weak instruments give biased, unreliable estimates.

**Cost:** Cheap.

**Agent use:**
- **Role:** Experimenter.
- **How:** Estimating the effect of actually using a feature from experiments that randomize only its availability or promotion.
- **Rules:** Justify the exclusion restriction explicitly. It can't be tested directly.
- **Guardrails:** Weak or invalid instruments give confidently wrong answers. Report first-stage strength.

### 183. Propensity scores (matching, inverse probability weighting)

**Definition:** Adjusting observational comparisons for confounding by modeling each unit's probability of receiving treatment from observed covariates.

**How it works:**
1. **Propensity score:** e(x) = P(treated | covariates), estimated with logistic regression or boosted trees.
2. **Matching:** pair each treated unit with control units with similar scores, then compare outcomes.
3. **Inverse probability weighting (IPW):** weight treated units by 1/e(x) and controls by 1/(1 − e(x)), creating a pseudo-population where treatment is unrelated to the covariates.
4. **Check balance:** after matching or weighting, covariates should be similar between groups (standardized mean differences).
5. **Overlap:** units with scores near 0 or 1 have no comparable counterparts. Trim them, or use overlap weights.

**Cost:** One model fit plus matching or weighting.

**Agent use:**
- **Role:** Experimenter.
- **How:** Estimating effects from logged data when experiments weren't run (who adopted a feature versus who didn't).
- **Rules:** Report balance diagnostics and overlap.
- **Guardrails:** Only adjusts for observed confounders. Unobserved confounding remains (#200).

### 184. Doubly robust estimation (AIPW) and double machine learning

**Definition:** Effect estimators that combine an outcome model and a propensity model, remaining correct if either one is correct, and allowing flexible ML models with valid inference.

**How it works:**
1. **AIPW (augmented inverse probability weighting):** the effect estimate combines the outcome model's predictions with propensity-weighted corrections of its residuals.
2. **Doubly robust:** consistent if either the outcome model or the propensity model is correctly specified.
3. **Double/debiased machine learning (DML):** use flexible ML models for both nuisance functions (outcome and propensity), with cross-fitting (fit on some folds, predict on others), then solve an orthogonal estimating equation. This gives valid confidence intervals despite using ML.
4. Works for average effects and, with extensions, for heterogeneous effects.

**Cost:** Several model fits with cross-fitting.

**Agent use:**
- **Role:** Experimenter.
- **How:** The most reliable standard tool for observational effect estimation with many covariates.
- **Rules:** Use cross-fitting. Report overlap diagnostics, as for #183.
- **Guardrails:** Still assumes no unobserved confounding. Pair with sensitivity analysis (#200).

### 185. Interrupted time series and Bayesian structural time series (CausalImpact)

**Definition:** Estimating the effect of an intervention on a single time series by forecasting what would have happened without it, from its pre-intervention behavior and related unaffected series.

**How it works:**
1. **Interrupted time series:** fit the pre-intervention trend and seasonality, and test for a change in level or slope at the intervention point (segmented regression).
2. **Bayesian structural time series:** a state space model (local level and trend, seasonality) plus regression on control series that weren't affected (for example, other regions' metrics). The model is fit on the pre-period.
3. Forecast the post-period counterfactual with uncertainty.
4. **Effect** = actual − counterfactual, with credible intervals, pointwise and cumulative.
5. **Assumption:** the control series aren't affected by the intervention, and their relationship with the target is stable.

**Cost:** Moderate (MCMC for the Bayesian model).

**Agent use:**
- **Role:** Experimenter.
- **How:** Measuring the impact of infrastructure changes, migrations, incidents or launches on a metric when no control group exists.
- **Rules:** Check that the control series weren't affected. Run placebo tests on fake intervention dates.
- **Guardrails:** Other events at the same time get attributed to the intervention. Check timelines.

## D8. Operational statistics and robust estimation

### 186. Statistical process control charts (Shewhart, EWMA charts)

**Definition:** Monitoring a process metric over time with control limits that separate normal variation from signals needing investigation.

**How it works:**
1. Establish a baseline period: mean and standard deviation (or moving-range estimates) of the metric.
2. **Shewhart chart:** control limits at mean ± 3σ. A point outside signals a special cause.
3. **Run rules (Western Electric):** for example, several consecutive points on one side of the mean, or trends, signal smaller shifts.
4. **EWMA chart:** monitor an exponentially weighted moving average with narrower limits, which is sensitive to small, persistent shifts.
5. **Attribute charts** for proportions (p-charts) and counts (c-charts).

**Cost:** Negligible.

**Agent use:**
- **Role:** Verifier.
- **How:** Monitoring operational quality metrics (error rates, deployment failure rates, data quality metrics) with fewer false alarms than ad hoc thresholds.
- **Rules:** Recompute baselines after confirmed process changes.
- **Guardrails:** Autocorrelated metrics inflate false alarms. Model or aggregate them first.

### 187. Survival analysis (Kaplan-Meier, Cox proportional hazards)

**Definition:** Analyzing time until an event (churn, failure, conversion, resolution) when some units haven't experienced the event yet (censoring).

**How it works:**
1. **Censoring:** units still "alive" at the end of observation contribute partial information. Ignoring them or dropping them biases results.
2. **Kaplan-Meier estimator:** S(t) = Π over event times of (1 − events / at-risk units). A step function estimating the probability of surviving past t.
3. **Log-rank test:** compares survival curves between groups.
4. **Cox proportional hazards model:** hazard(t | x) = baseline hazard(t) × exp(xᵀβ). Coefficients give hazard ratios for covariates, without specifying the baseline.
5. Check the proportional hazards assumption (Schoenfeld residuals).

**Cost:** Cheap.

**Agent use:**
- **Role:** Experimenter and Modeler.
- **How:** Churn analysis, time-to-resolution for incidents and tickets, hardware failure times, and experiment effects on retention over time.
- **Rules:** Always handle censoring explicitly.
- **Guardrails:** None specific.

### 188. Comparing tail latencies (quantile confidence intervals and tests)

**Definition:** Correctly comparing high percentiles (p95, p99) of latency or other heavy-tailed metrics between versions.

**How it works:**
1. **Quantile confidence intervals:** for a quantile q of n samples, the interval is between order statistics around n × q, with ranks from the binomial distribution. Distribution-free.
2. **Comparing two versions:** bootstrap the difference in quantiles (#155) at the randomization unit level, or use quantile regression with clustered errors.
3. **Watch for correlation:** requests from the same user or server are correlated. Resample users or servers, not requests.
4. Compare whole distributions with quantile-quantile plots, not only one percentile.

**Cost:** Moderate (bootstrap).

**Agent use:**
- **Role:** Verifier.
- **How:** Deciding whether a release really changed p99 latency, instead of reacting to noise in tail percentiles.
- **Rules:** Report confidence intervals for every tail percentile comparison.
- **Guardrails:** Never compare averaged percentiles across servers. Merge sketches or raw data (V#190).

### 189. Robust estimators (Huber M-estimators, trimmed means, median of means)

**Definition:** Estimators of central tendency and effects that are much less affected by outliers and heavy tails than plain means.

**How it works:**
1. **Trimmed mean:** discard a fraction (for example 5%) of the smallest and largest values, and average the rest.
2. **Huber M-estimator:** minimize a loss that's quadratic for small residuals and linear for large ones (NN#13), solved by iteratively reweighted least squares. Combines efficiency and robustness.
3. **Median of means:** split the data into groups, average each, and take the median of the group averages. Gives strong guarantees under heavy tails.
4. **Robust regression** uses the same M-estimation ideas for coefficients.

**Cost:** Cheap.

**Agent use:**
- **Role:** Experimenter.
- **How:** Stable estimates for heavy-tailed metrics (revenue, durations), alongside winsorization (#164).
- **Rules:** Pre-specify the estimator (TX5).
- **Guardrails:** Robust estimators estimate a different quantity than the mean. Make sure that's the decision-relevant quantity.

### 190. Jackknife variance estimation

**Definition:** Estimating the variance of a statistic by recomputing it with each unit (or group) left out.

**How it works:**
1. Compute the statistic on the full data: θ̂.
2. For each unit (or block of units) i, recompute the statistic without it: θ̂₍ᵢ₎.
3. Variance ≈ ((n − 1)/n) × Σ (θ̂₍ᵢ₎ − mean of the θ̂₍ᵢ₎)².
4. **Block (grouped) jackknife:** leave out groups (for example the buckets of a bucketed experiment) instead of single units, which is cheap and handles clustering.
5. Also estimates bias.

**Cost:** n (or number of groups) recomputations.

**Agent use:**
- **Role:** Experimenter.
- **How:** Variance estimates for complex metrics in experiment platforms, especially with a bucketed jackknife over a modest number of randomization buckets.
- **Rules:** Use blocks that match the randomization structure.
- **Guardrails:** Unreliable for non-smooth statistics like medians. Use the bootstrap there.

### 191. Hierarchical models and partial pooling (empirical Bayes)

**Definition:** Estimating many related quantities (effects per segment, per country, per store) by sharing information across them, shrinking noisy estimates toward the group average.

**How it works:**
1. Model each group's true value as drawn from a common distribution: θ_g ~ N(μ, τ²).
2. Each group's observed estimate has its own noise: y_g ~ N(θ_g, σ_g²).
3. **Partial pooling:** the posterior estimate for each group is a weighted average of its own estimate and the overall mean, weighted by their precisions. Noisy groups (small samples) are shrunk more.
4. **Empirical Bayes:** estimate μ and τ² from the data itself. **Full Bayes:** put priors on them and fit with MCMC.
5. Results in more accurate estimates for every group on average (the James-Stein effect).

**Cost:** Cheap (empirical Bayes) to moderate (full Bayes).

**Agent use:**
- **Role:** Experimenter and Modeler.
- **How:** Per-segment experiment readouts, per-region metrics and per-service error rates with small samples, without the extreme values that raw estimates produce.
- **Rules:** Report both raw and pooled estimates for transparency.
- **Guardrails:** Pooling hides real outliers when the groups truly differ. Check the estimated between-group variance.

### 192. Cluster-robust (sandwich) standard errors

**Definition:** Standard errors that remain valid when observations are correlated within groups, or have unequal variances.

**How it works:**
1. Ordinary standard errors assume independent, equal-variance errors.
2. **Heteroskedasticity-robust (HC) standard errors:** the "sandwich" formula (XᵀX)⁻¹ (Σ x_i x_iᵀ e_i²) (XᵀX)⁻¹, valid with unequal variances.
3. **Cluster-robust:** sum the score contributions within each cluster first, then form the sandwich. Valid with arbitrary correlation inside clusters.
4. Needs many clusters (dozens or more). With few clusters, use the wild cluster bootstrap.

**Cost:** Cheap.

**Agent use:**
- **Role:** Experimenter.
- **How:** Correct inference whenever the analysis unit is finer than the randomization unit (per-request analysis with per-user randomization), and in DiD (#179) and regressions on grouped data.
- **Rules:** Cluster at the level of randomization (or treatment assignment).
- **Guardrails:** Ignoring clustering is one of the most common sources of false positives. A/A-check it (#160).

### 193. Exact tests and rare-event analysis (Poisson and exact binomial tests)

**Definition:** Statistical tests and intervals that stay valid when events are rare (incidents, failures, fraud cases), where normal approximations break down.

**How it works:**
1. **Poisson rate test:** compare event counts given exposure (for example incidents per 1,000 deploys), using the conditional binomial test: given the total count, how events split between groups follows a binomial distribution.
2. **Exact binomial confidence intervals** (Clopper-Pearson) for small counts.
3. **Zero events observed:** the "rule of three": with n trials and zero events, the 95% upper bound on the rate is about 3/n.
4. **Overdispersion:** if counts vary more than Poisson allows, use negative binomial models.

**Cost:** Cheap.

**Agent use:**
- **Role:** Verifier.
- **How:** Judging reliability claims: "zero failures in 500 runs means the failure rate is likely below 0.6%", or whether a new release increased the rare crash rate.
- **Rules:** Use exact methods whenever event counts are small (under about 30).
- **Guardrails:** None specific.

## D9. Experiment platforms and decision quality

### 194. Overlapping (layered) experiment infrastructure

**Definition:** Running many experiments simultaneously on the same users, by organizing them into independent layers so experiments don't interfere and traffic isn't wasted.

**How it works:**
1. **Layers:** each layer covers a set of parameters (for example ranking, UI, infrastructure settings). Every user is in exactly one experiment (or control) per layer.
2. Each layer has its own hash salt (#158), so assignments in different layers are independent.
3. Experiments that might interact (they change the same parameters) go in the same layer, so they're mutually exclusive.
4. **Domains** can split traffic for experiments needing exclusive access to everything.
5. Interaction detection: periodically test for interactions between concurrent experiments in different layers.

**Cost:** Platform complexity.

**Agent use:**
- **Role:** Experimenter.
- **How:** Scaling experimentation to many concurrent tests without running out of traffic.
- **Rules:** Classify every new experiment into the right layer by which parameters it changes.
- **Guardrails:** Interactions between layers violate the independence assumption. Monitor for them.

### 195. Staged rollouts with statistical guardrails

**Definition:** Releasing changes in increasing percentages of traffic, automatically checking guardrail metrics with valid sequential statistics at each stage, and rolling back on degradation.

**How it works:**
1. **Stages:** for example 1% → 5% → 25% → 50% → 100%, with minimum durations.
2. At each stage, compare the guardrails (errors, latency, crash rate, key business metrics) between exposed and unexposed units, as an experiment.
3. Use always-valid tests (#166) for continuous monitoring, with one-sided tests for degradation and pre-set tolerances.
4. **Automatic rollback** when a guardrail degrades significantly beyond its tolerance. Advance automatically (or with approval) when all pass.
5. Log every decision with its evidence.

**Cost:** Slower full rollout.

**Agent use:**
- **Role:** Verifier and Experimenter.
- **How:** The agent's safe deployment process for code, models, configs and infrastructure changes (connects to glue G185 and NN#NR7 promotion gates).
- **Rules:** Every production change uses staged rollout with guardrails, unless it's an emergency fix (with documented justification).
- **Guardrails:** Rollback must always be possible and tested (TX4).

### 196. Metric change decomposition (root-causing KPI movements)

**Definition:** Explaining why a top-level metric changed, by attributing the change to segments, components or factors.

**How it works:**
1. **Additive metrics:** the change in total = Σ changes per segment. Rank segments by contribution.
2. **Mix versus rate effects:** for a rate metric (conversion), separate changes due to the segment mix shifting from changes in each segment's own rate (shift-share decomposition).
3. **Ratio and multiplicative metrics:** use log-ratio decompositions, or Shapley-value attribution across factors (order-independent).
4. **Drill-down search:** automatically search segment combinations for the ones explaining most of the change (with significance checks, to avoid chasing noise).
5. Compare against the normal variation of each segment.

**Cost:** Grows with the number of dimensions and their combinations.

**Agent use:**
- **Role:** Experimenter.
- **How:** Fast, systematic answers to "why did this metric drop?" for incidents and business reviews.
- **Rules:** Separate mix effects from rate effects explicitly.
- **Guardrails:** Searching many segments finds spurious explanations. Correct for multiple comparisons (#169), and confirm before acting.

### 197. Meta-analysis across experiments (fixed and random effects)

**Definition:** Combining the results of several experiments (or several runs of similar experiments) into one overall estimate.

**How it works:**
1. Each experiment provides an effect estimate and its standard error.
2. **Fixed-effect model:** assumes one true effect. Combined estimate = inverse-variance weighted average.
3. **Random-effects model:** assumes true effects vary between experiments with variance τ² (estimated, for example, by DerSimonian-Laird or REML). Weights account for both the within-experiment and between-experiment variance.
4. **Heterogeneity statistics** (I², Q test) show how much the effects differ.
5. Check for publication or selection bias (only "successful" experiments being reported).

**Cost:** Cheap.

**Agent use:**
- **Role:** Experimenter.
- **How:** Learning what kinds of changes tend to work across many experiments, and combining repeated tests into stronger conclusions.
- **Rules:** Include all relevant experiments, not only winners.
- **Guardrails:** None specific.

### 198. Winner's curse correction (shrinkage of experiment effects)

**Definition:** Correcting the systematic overestimation of effects for experiments that were selected because they looked successful.

**How it works:**
1. Experiments that are shipped are those with large observed effects, which partly reflect lucky noise. On average, their true effects are smaller than observed.
2. **Empirical Bayes shrinkage:** build a prior for true effects from the distribution of many past experiments' results (#191). Shrink each new estimate toward that prior, in proportion to its noise.
3. **Conditional (selection-adjusted) estimators:** estimate the effect accounting for the fact that it passed a significance threshold.
4. Track realized long-term impact against predicted impact to calibrate.

**Cost:** Cheap with historical experiment data.

**Agent use:**
- **Role:** Experimenter.
- **How:** Realistic impact estimates for roadmaps and reporting, instead of summing inflated wins.
- **Rules:** Report shrunken estimates for impact projections.
- **Guardrails:** None specific.

### 199. Simpson's paradox and regression-to-the-mean checks

**Definition:** Checks for two common statistical traps: an aggregate trend reversing within subgroups (Simpson's paradox), and extreme measurements naturally becoming less extreme on remeasurement (regression to the mean).

**How it works:**
1. **Simpson's paradox:** a comparison can favor A overall while favoring B in every subgroup, because group sizes differ between A and B (the mix differs). Check comparisons within strata (#162), and use causal reasoning about which comparison is right.
2. In randomized experiments, assignment protects the overall comparison, but observational comparisons and ramp-ups with changing traffic mixes don't.
3. **Regression to the mean:** units selected because they had extreme values (the worst-performing services, the most errors last week) will look better next time even without any intervention.
4. **Defense:** a control group, or compare against the expected regression from the same selection (selected from a comparable period without intervention).

**Cost:** Analysis discipline.

**Agent use:**
- **Role:** Verifier.
- **How:** Prevents wrong conclusions such as "our fix improved the worst services" when they would have improved anyway, or "the new version is worse" from mixed traffic.
- **Rules:** Any "before/after on selected extreme units" claim needs a control group.
- **Guardrails:** None specific.

### 200. Sensitivity analysis for unobserved confounding (E-values, Rosenbaum bounds)

**Definition:** Quantifying how strong an unmeasured confounder would have to be to explain away an observational effect estimate.

**How it works:**
1. Observational estimates (#179–185) assume no unobserved confounding, which can't be verified directly.
2. **E-value:** the minimum strength of association (on the risk-ratio scale) an unmeasured confounder would need with both treatment and outcome to fully explain away the observed effect. For a risk ratio RR > 1: E = RR + √(RR × (RR − 1)).
3. Also compute the E-value for the confidence limit closest to the null.
4. **Rosenbaum bounds** (for matched studies): how much hidden bias (Γ, the factor by which treatment odds could differ between matched units) would change the conclusion.
5. Compare these thresholds with the strength of known measured confounders.

**Cost:** Cheap.

**Agent use:**
- **Role:** Experimenter.
- **How:** Makes observational claims honest: "this effect would require an unmeasured factor 3× as strong as anything measured to be explained away" is far more defensible than a bare estimate.
- **Rules:** Report a sensitivity analysis with every observational causal estimate (T6).
- **Guardrails:** Robustness to confounding still doesn't make an observational estimate equivalent to a randomized experiment. Prefer experiments when feasible.

---
