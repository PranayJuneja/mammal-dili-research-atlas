# Project Charter

## Working title

**Incremental Value of Frozen MAMMAL Molecular Embeddings for Predicting Drug-Induced Liver Injury Concern: A Comparative Validation Study Using DILIrank 2.0**

The final KUHS-facing title may need shortening to the portal's current word limit. The scientific meaning must not change when shortened.

## Why this project exists

Drug-induced liver injury (DILI) is a serious drug-safety problem. A medicine can be associated with liver-enzyme elevation, jaundice, acute liver failure, treatment interruption, regulatory restriction, or withdrawal. Predicting DILI concern before widespread exposure is difficult because risk reflects structure, dose, metabolism, immune responses, patient susceptibility, and the quality of available evidence.

Conventional chemical models represent a molecule using interpretable calculated properties and fingerprints of local chemical fragments. MAMMAL is a biomedical foundation model trained on more than two billion examples across small molecules, proteins, and gene-expression data. Its frozen encoder may produce a richer numerical summary of a drug's structure, but strong performance on other tasks does not prove that this summary adds useful information for DILI.

This project therefore evaluates **incremental value**, not “AI versus doctors” and not “whether AI can solve DILI.”

## North-star research question

Does a pre-specified frozen MAMMAL representation improve scaffold-separated prediction of DILIrank 2.0 concern labels when added to a conventional model containing Morgan fingerprints and physicochemical descriptors?

## Primary claim the study may support

The most that the primary study can claim is one of the following:

1. The selected MAMMAL representation improved drug-level discrimination on this curated dataset and evaluation design.
2. A practically important gain was not supported or was excluded with stated precision.
3. The result was inconclusive because uncertainty remained too wide.
4. The selected representation performed worse.
5. Reliable extraction was technically infeasible under the pre-specified pilot.

No outcome permits a claim about an individual patient's probability of DILI.

## Objectives

### Primary objective

Estimate the paired change in area under the receiver operating characteristic curve (AUROC) when frozen MAMMAL embeddings are added to Morgan fingerprints and standard physicochemical descriptors.

### Secondary objectives

- Compare descriptor-only, conventional, MAMMAL-only, and combined representations under the same L2-regularised logistic-regression framework.
- Assess calibration and classification measures using thresholds selected without access to outer test outcomes.
- Examine missed `vMost-DILI-concern` drugs by drug class and chemical scaffold.
- Repeat the comparison for the clearest label contrast: `vMost` versus `vNo`.
- Evaluate transport to eligible drugs added in DILIrank 2.0, while explicitly avoiding the label “external validation.”
- Explore daily dose and the Rule of Two in a complete-case subset of reliably linked oral drugs.

## In scope

- Public, non-identifiable, drug-level secondary data.
- DILIrank 2.0 `vMost`, `vLess`, and `vNo` concern categories.
- Identifiable single small molecules with structures processable by both conventional and MAMMAL pipelines.
- Frozen MAMMAL features; the pretrained weights do not change.
- Reproducible curation, validation, uncertainty estimation, error analysis, and transparent reporting.

## Out of scope

- Patient-level diagnosis, prognosis, or personalised treatment.
- Causal inference about why a particular drug injured a particular liver.
- Clinical recommendations to start, stop, or monitor a medicine.
- Replacement of regulatory, laboratory, animal, or clinical safety assessment.
- Training a deep neural network from scratch.
- Full fine-tuning of MAMMAL.
- Secret or proprietary datasets.
- Presenting DILIrank labels as perfect truth or `vNo` as proof of absolute safety.

## Stakeholders and required expertise

| Role | Responsibility |
|---|---|
| Student investigator | Protocol, audit trail, execution, interpretation and reporting |
| Faculty guide | Scientific supervision, institutional compliance and sign-off |
| Pharmacology/toxicology reviewer | Outcome language, drug identity, exposure logic and error review |
| Computational reviewer | Structure curation, MAMMAL extraction and reproducibility |
| Biostatistical adviser | Estimand, practical-gain threshold, resampling and precision plan |
| Institutional Ethics Committee | Written determination before pilot or analysis |

## Success criteria

The project is successful if it produces a credible answer, including a credible null or infeasibility result. Success requires all of the following:

- Written IEC determination obtained before the pilot or outcome analysis.
- All primary choices locked before inspecting model performance.
- Every included drug traceable from source label to final features.
- MAMMAL pilot passes the reproducibility and coverage gate, or failure is transparently reported.
- Conventional and expanded models evaluated on identical held-out drugs using identical folds and algorithms.
- Leakage prevented in standardisation, dimensionality reduction, tuning, threshold selection, and resampling.
- Paired effect estimates reported with uncertainty and practical interpretation.
- Code, environment, cohort, fold assignments, audit decisions, and results archived.
- Claims remain at the drug-level benchmark scope.

## Non-negotiable principles

1. **No outcomes before protocol lock.** Technical work may be label-blind; performance must remain unseen.
2. **One added information block.** The primary expanded model contains every conventional predictor and adds only MAMMAL.
3. **Same evaluation opportunities.** Models receive the same eligible drugs, folds, preprocessing discipline, and classifier family.
4. **Chemical relatedness matters.** Scaffold-grouped evaluation is primary; random splitting is only a robustness analysis.
5. **Uncertainty beats leaderboard thinking.** The result is an estimated difference with a confidence interval, not a model contest.
6. **Null does not automatically mean equivalence.** Precision and the practical-gain boundary determine interpretation.
7. **No patient-level overclaiming.** The endpoint is established concern assigned to a drug, not an individual's outcome.

