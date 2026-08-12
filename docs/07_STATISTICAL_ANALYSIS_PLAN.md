# Statistical Analysis Plan

## Status and lock rule

This is the analysis specification to be reviewed with the biostatistical adviser. All highlighted open choices must be resolved before model performance is inspected. After lock, changes require a dated protocol deviation or amendment.

## Analysis populations

### Primary analysis population

All structurally eligible `vMost`, `vLess`, and `vNo` drugs with successful conventional and MAMMAL representations under the locked pipeline.

Primary outcome coding:

- `1`: `vMost` or `vLess`
- `0`: `vNo`

### Sensitivity population

Eligible `vMost` and `vNo` drugs only.

### Update cohort

Eligible members of the 300 drugs added in DILIrank 2.0, evaluated after development on eligible original-list records using current 2.0 labels.

### Dose/exposure subset

Eligible oral drugs with reliable, harmonised daily-dose data under the locked complete-case rule.

## Descriptive analysis

Before modelling, report:

- records considered, included, and excluded by reason;
- outcome distribution;
- original versus update membership;
- number and size distribution of scaffold groups;
- descriptor distributions by outcome without significance-screening predictors;
- token length, truncation, embedding success, and embedding norm summaries;
- characteristics of included versus excluded/failed drugs.

Continuous variables use mean and standard deviation when informative and median with interquartile range for skewed distributions. Categorical variables use counts and percentages. These summaries describe the cohort; they do not drive post hoc eligibility or feature selection.

## Primary estimand

`ΔAUROC = AUROC(Model D) - AUROC(Model B)`

The target is the average paired difference in out-of-fold ranking performance under the pre-specified repeated scaffold-grouped training procedure on the eligible DILIrank 2.0 population.

This estimand is algorithm-and-procedure specific. It does not estimate the effect of every possible MAMMAL representation or classifier.

## Out-of-fold aggregation

For each of five repeats, every drug receives exactly one held-out probability per model. For repeat `r`:

1. Calculate `AUROC_B,r` from the complete out-of-fold vector.
2. Calculate `AUROC_D,r` from the matching vector.
3. Calculate `Δr = AUROC_D,r - AUROC_B,r`.

The primary point estimate is the arithmetic mean of the five `Δr` values. Mean AUROCs for B and D are reported alongside it. Repeat-specific results are retained and shown, not treated as five independent studies.

## Primary confidence interval

Use 2,000 bootstrap resamples of complete scaffold groups. Within each resample, include all drugs in each selected group and calculate the mean repeat-level paired difference. The provisional interval is the 2.5th and 97.5th percentiles of the bootstrap distribution.

This method preserves chemical clustering and pairing. Before lock, simulation must test its coverage and stability under the observed number of groups, group-size imbalance, class balance, and repeated-prediction structure. The simulation may use outcomes only to reproduce prevalence, not model performance to choose the favourable interval.

If the adviser selects BCa, corrected repeated-CV, or another interval method, the exact algorithm and justification replace this provisional method before analysis. A naïve drug-level bootstrap that breaks scaffold groups is not acceptable as the primary interval.

## Practical interpretation regions

Let `L` and `U` be the lower and upper limits of the two-sided 95% confidence interval, and let `δ = 0.03` be the proposed minimum practically important gain.

| Confidence interval position | Primary wording |
|---|---|
| `L > δ` | Practically important improvement supported |
| `L > 0` and `L ≤ δ ≤ U` | Some improvement supported; practical importance uncertain |
| `L ≤ 0` and `U ≥ δ` | Inconclusive for both superiority and practical importance |
| `L ≤ 0` and `0 < U < δ` | No superiority established; the pre-specified important gain is excluded |
| `0 ≤ L` and `U < δ` | Small positive gain supported, but the pre-specified important gain is excluded |
| `U < 0` | Expanded model performs worse |

Do not use “equivalent” unless an explicit equivalence design and adequate precision have been agreed in advance.

## Secondary performance measures

For every model and relevant analysis set report:

- precision-recall AUROC;
- sensitivity;
- specificity;
- positive predictive value/precision;
- balanced accuracy;
- Brier score;
- calibration intercept;
- calibration slope.

Threshold-based measures are calculated from outer test predictions using thresholds selected within training data. Provide confidence intervals and paired differences where the resampling design supports them.

Because the outcome is a curated concern label rather than an intervention decision, decision-curve analysis is not part of the primary plan. It may be considered only if a defensible decision context and threshold consequences are specified before analysis.

## Important-error analysis

Define an important false negative as a `vMost` drug classified below the locked threshold. Report:

- drug name and identifiers;
- predicted probabilities from B and D;
- scaffold and related training-group context;
- drug/therapeutic class;
- structural and curation warnings;
- whether the error persists at the sensitivity-prioritised threshold.

This is descriptive error analysis. It must not be used to remove difficult drugs or tune the primary pipeline.

## Missingness and failures

- Primary molecular analysis uses common complete representation: both B and D must be available so the comparison is paired.
- Every structure and embedding failure is reported by reason and outcome after cohort lock.
- No imputation of an entire missing MAMMAL vector.
- Descriptor-level missingness, if any, uses training-fold median imputation.
- Dose analysis is complete case, with coverage and selection differences disclosed.

## Multiplicity

There is one primary comparison and one primary metric. Secondary metrics and analyses are supportive and will be labelled exploratory or sensitivity analyses. Their confidence intervals are descriptive; no claim of independent confirmatory significance will be made without a pre-specified multiplicity procedure.

## Precision assessment

After eligibility and scaffold groups are locked—but before any model performance is viewed—simulate plausible paired prediction scenarios to estimate confidence-interval width and coverage. Vary:

- eligible sample size and prevalence;
- number and size distribution of scaffold groups;
- baseline AUROC;
- correlation between B and D predictions;
- true `ΔAUROC` values around 0 and 0.03.

Use this to determine whether five repeats and 2,000 resamples provide adequate stability. It must not be used to select a procedure because it produces the preferred empirical result.

## Sensitivity analyses

- `vMost` versus `vNo`.
- Update-cohort transport.
- Random rather than scaffold-grouped split, clearly labelled optimistic robustness analysis.
- Alternative pre-locked acyclic clustering threshold.
- Class-weighted logistic regression.
- Canonical/randomised-SMILES stability.
- Dose/Rule-of-Two oral subset.
- Optional alternate classifier only if locked before outcomes.

## Reproducible outputs

The analysis script must generate from stored out-of-fold predictions:

- study flow table;
- cohort/scaffold table;
- model-performance table;
- primary `ΔAUROC` plot with confidence interval and 0/0.03 reference lines;
- ROC and precision-recall curves derived without pooling leakage;
- calibration plots;
- repeat-level stability plot;
- important-error table;
- sensitivity-analysis table;
- machine-readable results file containing estimates, intervals, seeds, and configuration hashes.

