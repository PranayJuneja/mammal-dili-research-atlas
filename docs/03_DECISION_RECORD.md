# Decision Record

This file reconciles the supplied drafts and records which version governs implementation. Changes after protocol lock require a dated amendment with a reason and impact assessment.

## DR-001 — Primary comparator

**Decision:** Use Morgan fingerprints plus physicochemical descriptors as the primary conventional baseline.

**Earlier alternative:** Daily dose, logP, and the Rule of Two as the primary baseline.

**Reason:** The research claim concerns incremental molecular information. A strong chemical baseline is the fairest comparator for a molecular foundation-model representation. Dose is unavailable, route-specific, and regimen-dependent for part of the dataset; requiring it would reduce and potentially select the primary cohort.

**Consequence:** The Rule of Two becomes an exploratory oral-drug subset analysis.

## DR-002 — Primary model contrast

**Decision:** Compare Model D (`Morgan + descriptors + MAMMAL`) with Model B (`Morgan + descriptors`).

**Reason:** D contains all B predictors and adds only MAMMAL, so the paired difference has a clean incremental-value interpretation.

## DR-003 — Prediction algorithm

**Decision:** Use the same L2-regularised logistic regression for all representation sets.

**Earlier alternative:** Logistic regression plus gradient-boosted trees.

**Reason:** Holding the classifier constant makes the feature representation the principal difference. Gradient boosting may be retained only as a clearly secondary robustness analysis if resources allow and it is locked before outcomes.

## DR-004 — Primary validation

**Decision:** Repeated nested five-fold cross-validation grouped by chemical scaffold.

**Reason:** Random splitting can place close structural analogues in training and testing data and overstate generalisation. Inner folds are required for honest hyperparameter selection.

**Open detail:** The authoritative draft specifies five repeats; an earlier draft specified ten. Five is the current choice, subject to simulation-based precision and compute assessment before lock.

## DR-005 — Acyclic structures

**Decision:** Do not place all empty Bemis–Murcko scaffolds into one giant group. Cluster them using the same radius-2 fingerprint, Tanimoto similarity, and a pilot-locked Butina threshold currently proposed as `0.50`.

**Reason:** A single empty-scaffold group could make fold construction unstable, while treating every acyclic molecule as independent could leak close analogues.

## DR-006 — Primary performance measure

**Decision:** Paired `ΔAUROC` with a two-sided 95% confidence interval.

**Reason:** AUROC measures ranking across thresholds; pairing uses the fact that both models predict the same held-out drugs.

**Supporting measures:** Precision-recall AUROC, Brier score, calibration intercept/slope, sensitivity, specificity, precision, balanced accuracy, and important-error review.

## DR-007 — Practical importance threshold

**Decision:** Carry `0.03 AUROC` as the proposed operational benchmark.

**Earlier alternative:** `0.05 AUROC`.

**Reason:** The later protocol explicitly sets 0.03, but the value cannot be defended by assertion alone.

**Lock condition:** The biostatistical adviser must confirm the value and its rationale before outcome analysis. If changed, the change must occur while labels/performance remain unseen.

## DR-008 — Null-result language

**Decision:** A result near zero is interpreted using the entire confidence interval.

- Upper limit below 0.03: excludes the pre-specified practically important improvement.
- Interval crossing zero and 0.03: inconclusive.
- Lower limit above zero but not 0.03: evidence of some improvement, practical importance uncertain.
- Lower limit above 0.03: practically important improvement supported.

**Reason:** “No significant difference” is not proof of equivalence, and a point estimate of zero is not enough.

## DR-009 — Dimension reduction

**Decision:** No PCA by default. L2 regularisation is the primary control for high-dimensional predictors.

**Earlier alternative:** PCA applied to fingerprints and embeddings within folds.

**Reason:** PCA adds another tuned transformation and can affect the two feature blocks differently. If pilot evidence shows a computational or numerical need, the method and component grid must be frozen before outcomes.

## DR-010 — Class imbalance

**Decision:** No synthetic oversampling. Use unweighted primary logistic regression unless changed by the biostatistical adviser before lock; balanced class weighting may be a sensitivity analysis.

**Reason:** The pre-exclusion class split, 568 versus 414, is not extreme. Synthetic examples would be particularly questionable across scaffold boundaries.

## DR-011 — Update-cohort terminology

**Decision:** Call the 300 newly added DILIrank 2.0 drugs an update-cohort transport analysis.

**Forbidden claims:** independent external validation, prospective validation, unseen molecules, or protection against pretraining contamination.

## DR-012 — MAMMAL extraction

**Decision:** The checkpoint name alone does not define the embedding. A label-blind pilot must lock checkpoint revision, tokenizer revision, prompt, layer, pooling, sequence limit, truncation, dtype, device behavior, and vector tolerance.

**Reason:** IBM's public usage examples demonstrate model inference and task fine-tuning, but do not by themselves define the exact general-purpose molecular embedding required by this study.

## DR-013 — Ethics timing

**Decision:** Obtain a written IEC determination before the pilot or analysis.

**Reason:** Public non-identifiable drug data may qualify for exemption or another non-human-participant determination, but the investigator must not self-declare institutional status.

## DR-014 — Reporting framework

**Decision:** Use TRIPOD+AI where applicable and explicitly describe departures in applicability.

**Reason:** TRIPOD+AI is the current transparent-reporting framework for regression and machine-learning prediction studies. The project is drug-level classification, so patient-specific items must be handled as not applicable rather than implied.

