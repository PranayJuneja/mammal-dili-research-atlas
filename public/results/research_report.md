# Development and evaluation of frozen MAMMAL representations for drug-level DILI concern prediction: a paired scaffold-grouped benchmark

## Abstract

**Objective.** To determine whether a pre-specified frozen MAMMAL molecular embedding adds discrimination beyond physicochemical descriptors and a chirality-aware Morgan fingerprint for drug-level DILIrank 2.0 concern classification.

**Design.** Repeated nested scaffold-grouped validation with a common L2-regularised logistic-regression learner. Model B used descriptors plus Morgan bits; Model D added the frozen 768-dimensional MAMMAL vector. The primary estimand was mean repeat-level `AUROC(D) - AUROC(B)`, with a 95% interval from 2,000 complete-scaffold bootstrap resamples and a pre-specified +0.03 practical benchmark.

**Data.** Of 1,336 DILIrank 2.0 records, 982 non-ambiguous records underwent structural review; 809 were eligible. The primary development cohort contained 675 original-list drugs and the untouched transport cohort contained 134 added drugs.

**Results.** Adding MAMMAL changed AUROC by **-0.080** (95% CI **-0.114 to -0.042**). The expanded model performs worse under the locked procedure. In the untouched update cohort, the paired AUROC change was -0.029 (95% CI -0.109 to +0.047); this is exploratory transport evidence.

**Conclusion.** The expanded model performs worse under the locked procedure. This conclusion applies only to the frozen checkpoint, prompt, pooling rule, eligible drug-level cohort, conventional comparator, learner, and validation procedure studied here. It is not a patient-risk estimate or clinical recommendation.

## Research question and estimand

The study asks an incremental question: does one frozen MAMMAL representation [3] improve ranking performance when added to a strong conventional molecular baseline? Models B and D used identical drugs, folds, preprocessing, hyperparameter opportunities, thresholds, and classifiers. The only intended difference was the MAMMAL block. The primary point estimate is the arithmetic mean of five paired repeat-level AUROC differences.

## Methods

### Cohort and outcome

DILIrank 2.0 categories [1,2] `vMost` and `vLess` were coded positive and `vNo` negative. Ambiguous labels were excluded before structural review. Names were mapped to PubChem candidates [4], active moieties were adjudicated, parent structures were standardised while preserving justified stereochemistry, unsupported biologics/complexes/mixtures were excluded, and duplicate parents were resolved before grouping.

### Representations

- Model A: pre-specified physicochemical descriptors.
- Model B: descriptors plus 2,048 radius-2 chirality-aware Morgan bits [5].
- Model C: frozen MAMMAL embedding alone [3].
- Model D: descriptors, Morgan bits, and frozen MAMMAL embedding [3,5].

MAMMAL weights were never updated using DILI labels. The checkpoint, revision, tokenizer bytes, checkpoint-native molecule syntax, final encoder state, attention-mask-aware mean pooling, L2 normalisation, maximum length, failure rules, and CPU execution were frozen after an outcome-blind 20-structure pilot.

### Validation and analysis

Bemis-Murcko scaffolds [6] defined groups for ring-containing structures; acyclic structures were similarity-clustered. Five outer folds were repeated five times. Preprocessing and regularisation selection occurred only inside training partitions. The 300-drug update-era source cohort was excluded from development and evaluated once after the development pipeline was fixed. The primary interval resampled complete scaffold groups, preserving model pairing and chemical clustering.

## Results

### Study flow

- DILIrank 2.0 records: 1,336
- Non-ambiguous records structurally considered: 982
- Eligible / excluded: 809 / 173
- Chemical groups: 568 across all eligible drugs; 460 constructed independently in development and 125 constructed separately in the update cohort
- Development / untouched update drugs: 675 / 134

### Model performance

| Model | AUROC mean (repeat SD) | PR-AUROC | Brier | Calibration intercept | Calibration slope |
|---|---:|---:|---:|---:|---:|
| A | 0.725 (0.006) | 0.830 | 0.180 | 0.110 | 0.854 |
| B | 0.763 (0.009) | 0.851 | 0.166 | -0.027 | 0.944 |
| C | 0.661 (0.008) | 0.790 | 0.219 | 0.702 | 0.761 |
| D | 0.682 (0.015) | 0.802 | 0.196 | 0.391 | 0.589 |

### Primary answer

The paired change was **-0.080** (95% CI **-0.114 to -0.042**) against the pre-specified practical benchmark of +0.03. **The expanded model performs worse under the locked procedure.** Repeat-specific differences were -0.067, -0.083, -0.094, -0.093, -0.065.

The pre-performance precision simulation on the final development group vector had minimum empirical coverage 0.825, maximum mean interval width 0.055, and maximum 100-versus-2,000-resample endpoint shift 0.008. These diagnostics motivate cautious interval interpretation and do not alter the frozen estimator.

### Transport and error review

The untouched added-drug cohort estimate was -0.029 (95% CI -0.109 to +0.047). The machine-readable error table contains 277 model-drug rows in which a `vMost` drug fell below the training-derived Youden threshold in at least one repeat.

### Pre-specified robustness analyses

| Analysis | D-minus-B AUROC | 95% CI |
|---|---:|---:|
| vmost vs vno | -0.076 | -0.118 to -0.040 |
| stratified random | -0.066 | -0.094 to -0.036 |
| class balanced | -0.078 | -0.111 to -0.039 |

The random-split analysis is explicitly optimistic and cannot replace scaffold-grouped validation. The `vMost`-versus-`vNo` and class-balanced analyses are sensitivity checks; none redefines the primary estimand.

Across the primary fits, 0 convergence warnings were recorded. All are retained and disclosed; no prediction is silently removed. Repeat-level metric ranges and standard deviations, the cohort/scaffold table, sensitivity table, and both false-negative persistence definitions are provided as machine-readable companion files.

## Interpretation

The expanded model performs worse under the locked procedure. The result should be interpreted jointly with precision-recall performance, probability error, calibration, sensitivity/specificity, transport behavior, and important false negatives. A positive AUROC difference does not establish clinical utility; an interval crossing zero does not prove equivalence; and an upper interval below +0.03 addresses only the pre-specified size of improvement under this design.

## Limitations

The outcome is a curated drug-level concern category, not individual patient injury. Molecular structure omits dose, exposure, metabolism, immune mechanisms, genetics, comorbidity, and co-medication. Labels are imperfect regulatory/evidentiary constructs. Scaffold separation limits downstream analogue leakage but cannot establish whether a pretrained foundation model encountered study molecules. Results concern one frozen representation recipe and one conventional learner, not the full MAMMAL family. The source contains no person-level sociodemographic attributes, so clinical subgroup fairness cannot be assessed.

## Future research

Future work should evaluate independently curated drug sets, representation recipes fixed without outcome feedback, exposure and host-context features, and—before any clinical claim—patient-level cohorts with explicit fairness and clinical-utility assessment. The current benchmark is not implementation-ready.

## Reporting completeness

The companion `tripod_ai_applicability.md` and `tripod_ai_checklist.csv` map all 52 TRIPOD+AI subitems [7]. Pending author, governance, registration, archive, and model-export declarations remain visibly pending until their responsible owners complete them.

## Scope statement

This study evaluates drug-level prediction of curated DILI concern within DILIrank 2.0. It does not estimate an individual patient's probability of liver injury, establish drug-specific causality, recommend prescribing decisions, or replace laboratory, clinical, pharmacovigilance, or regulatory assessment.

## References

1. Olubamiwa AO, Qu Y, Connor S, Tong W, Li D, Chen M. DILIrank 2.0: an updated and expanded database for drug-induced liver injury risk based on FDA labeling and a literature review. Drug Discov Today. 2025;30(11):104485. doi:10.1016/j.drudis.2025.104485.
2. US Food and Drug Administration. Drug-Induced Liver Injury Rank (DILIrank) 2.0 Dataset. Available from: https://www.fda.gov/science-research/liver-toxicity-knowledge-base-ltkb/drug-induced-liver-injury-rank-dilirank-20-dataset. Accessed 2026 Aug 12.
3. Shoshan Y, Raboh M, Ozery-Flato M, Ratner V, Golts A, Weber JK, et al. MAMMAL—Molecular Aligned Multi-Modal Architecture and Language for biomedical discovery. npj Drug Discov. 2026;3:14. doi:10.1038/s44386-026-00047-4.
4. Kim S, Chen J, Cheng T, Gindulyte A, He J, He S, et al. PubChem 2023 update. Nucleic Acids Res. 2023;51(D1):D1373–D1380. doi:10.1093/nar/gkac956.
5. Rogers D, Hahn M. Extended-connectivity fingerprints. J Chem Inf Model. 2010;50(5):742–754. doi:10.1021/ci100050t.
6. Bemis GW, Murcko MA. The properties of known drugs. 1. Molecular frameworks. J Med Chem. 1996;39(15):2887–2893. doi:10.1021/jm9602928.
7. Collins GS, Moons KGM, Dhiman P, Riley RD, Beam AL, Van Calster B, et al. TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use regression or machine learning methods. BMJ. 2024;385:e078378. doi:10.1136/bmj-2023-078378.
