# Results Interpretation and Reporting Guide

## The primary result sentence

Every abstract, presentation, and report should make the primary comparison explicit:

> In repeated scaffold-grouped evaluation of eligible DILIrank 2.0 drugs, adding the pre-specified frozen MAMMAL embedding to Morgan fingerprints and physicochemical descriptors changed AUROC by **[estimate]** (95% CI **[lower] to [upper]**).

Follow it immediately with interpretation relative to both zero and the pre-specified practical benchmark.

## Scenario language

### Scenario A — Confidence interval wholly above 0.03

**Say:** The results support a practically important incremental improvement for the selected frozen MAMMAL representation under this drug-level evaluation framework.

**Do not say:** MAMMAL is clinically useful, prevents DILI, or predicts patient outcomes.

### Scenario B — Above zero but overlapping 0.03

**Say:** The embedding improved discrimination, but the data do not establish that the gain reaches the pre-specified level of practical importance.

**Do not collapse this into:** “MAMMAL works.”

### Scenario C — Interval crosses zero and 0.03

**Say:** The estimate is too imprecise to determine whether MAMMAL adds no value or a practically important gain. The study is inconclusive.

**Do not say:** There is no difference.

### Scenario D — Upper limit below 0.03 but interval crosses zero

**Say:** Superiority was not established, and the analysis excludes an AUROC improvement as large as the pre-specified 0.03 benchmark under this design.

**Value of the result:** It argues against paying the complexity cost for a meaningfully larger gain in this exact setting, while allowing that a small gain may exist.

### Scenario E — Entire interval between 0 and 0.03

**Say:** A small positive improvement is supported, but it is below the pre-specified threshold for practical importance; the simpler model may therefore be preferred for this use.

### Scenario F — Entire interval below zero

**Say:** The expanded model discriminated worse than the conventional model under the locked evaluation procedure.

**Do not generalise to:** every MAMMAL checkpoint, prompt, layer, pooling strategy, or fine-tuned model.

### Scenario G — MAMMAL extraction infeasible

**Say:** The pre-specified extraction pipeline did not meet its repeatability/coverage gate after one documented correction cycle, so predictive incremental value was not evaluated.

This is an engineering feasibility result, not a negative predictive-performance result.

## AUROC is not enough

Interpret the result alongside:

- **Precision-recall AUROC:** ranking performance focused on the positive class and affected by prevalence.
- **Calibration:** whether predicted probabilities agree with observed concern frequency in this dataset.
- **Brier score:** overall probability error.
- **Sensitivity:** fraction of concern-positive drugs detected at a locked threshold.
- **Specificity:** fraction of `vNo` drugs correctly classified at that threshold.
- **Precision:** fraction of positive predictions that are concern-positive.
- **Important false negatives:** especially `vMost` drugs assigned low probability.

A higher AUROC with worse calibration or dangerous error patterns deserves qualified interpretation.

## Required result displays

### Main table

| Model | Mean AUROC | PR-AUROC | Brier | Calibration intercept | Calibration slope |
|---|---:|---:|---:|---:|---:|
| A | | | | | |
| B | | | | | |
| C | | | | | |
| D | | | | | |

Below the table report paired D-minus-B differences with confidence intervals.

### Primary effect figure

Plot `ΔAUROC` with:

- point estimate;
- 95% confidence interval;
- vertical line at `0`;
- vertical line at `0.03`;
- plain-language region labels.

### Calibration figure

Use held-out predictions, show observed versus predicted concern over sensible bins or a smooth curve, include uncertainty, and display the ideal line. Do not infer good calibration from AUROC.

### Error table

List important false-negative `vMost` drugs with both model probabilities, scaffold, class, and curation flags. Avoid mechanistic stories that the data cannot test.

## Subgroup and sensitivity discipline

Every secondary result must answer:

1. Was it pre-specified?
2. Does it use fewer or selected drugs?
3. Is its uncertainty wider?
4. Does it change the primary conclusion or merely explain it?
5. Could pretraining overlap, label ascertainment, or curation explain the difference?

Do not headline the best-performing sensitivity analysis when the primary result is weaker.

## Negative and null results are publishable only when precise and transparent

A credible null contribution requires:

- a strong comparator;
- an identical paired evaluation;
- a pre-specified practical threshold;
- enough precision to exclude that threshold;
- no hidden extraction or selection failures;
- claims limited to the selected representation and dataset.

If the interval is wide, the correct conclusion is uncertainty, not simplicity's victory.

## Final scope paragraph

Use a version of this paragraph in every dissemination artefact:

> This study evaluates drug-level prediction of curated DILI concern within DILIrank 2.0. It does not estimate an individual patient's probability of liver injury, establish drug-specific causality, recommend prescribing decisions, or replace laboratory, clinical, pharmacovigilance, or regulatory assessment. Results apply to the specified frozen MAMMAL representation, conventional comparator, eligible cohort, and validation procedure.

