# Master Protocol

## 1. Study identification

**Design:** Six-month retrospective secondary-data comparative prediction-model study.

**Study unit:** One eligible approved small-molecule drug.

**Intended use of results:** Research benchmarking and liver-safety prioritisation only.

## 2. Research question

Among eligible DILIrank 2.0 small-molecule drugs, does adding a pre-specified frozen MAMMAL embedding to Morgan fingerprints and physicochemical descriptors improve scaffold-separated prediction of established DILI concern?

## 3. Objectives and hypothesis

### Primary objective

Estimate the paired difference in discrimination between:

- **Model B:** Morgan fingerprint plus physicochemical descriptors; and
- **Model D:** the same Morgan fingerprint and descriptors plus a frozen MAMMAL embedding.

The primary estimand is:

`ΔAUROC = AUROC(D) - AUROC(B)`

The formal superiority hypothesis is `H0: ΔAUROC ≤ 0` versus `H1: ΔAUROC > 0`. A two-sided 95% confidence interval will be used for estimation and interpretation.

An AUROC gain of `0.03` is the proposed minimum practically important difference. It must be confirmed and signed off with the biostatistical adviser before outcome analysis.

### Secondary objectives

- Compare all four representation models using the same prediction algorithm.
- Evaluate precision-recall AUROC, calibration, classification performance, and important errors.
- Evaluate `vMost` versus `vNo` as the clearest concern contrast.
- Test the locked pipeline on eligible drugs added in DILIrank 2.0.
- Explore dose and the Rule of Two among reliably linked eligible oral drugs.

## 4. Data source and study population

DILIrank 2.0 supplies concern labels and release membership. It contains 1,336 approved drugs: 217 `vMost`, 351 `vLess`, 414 `vNo`, and 354 `Ambiguous`. The 982 non-ambiguous records form the census considered before structural eligibility and deduplication.

Molecular structures will be obtained mainly from PubChem and cross-checked using names, source identifiers, PubChem CIDs, and InChIKeys. The exact source hierarchy and conflict rules are defined in the data specification.

### Inclusion criteria

- DILIrank 2.0 category is `vMost`, `vLess`, or `vNo`.
- Record can be resolved to a clearly identifiable single small-molecule active drug.
- A chemically meaningful structure is available and processable by both conventional and MAMMAL pipelines.
- One standardised parent representation can be selected under the locked rules.

### Exclusion criteria

- `Ambiguous-DILI-concern` category.
- Biologic, peptide/macromolecule, mixture, polymer, unresolved inorganic agent, or other record without one meaningful small-molecule representation.
- Unresolved identity or unreliable chemical structure.
- Duplicate parent structure after standardisation, according to the locked duplicate policy.
- Persistent representation failure under the locked technical rules.

All exclusions and failures will be listed with reason codes. Coverage differences by outcome category will be reported.

## 5. Outcome

The primary binary outcome is:

- Positive: `vMost-DILI-concern` or `vLess-DILI-concern`.
- Negative: `vNo-DILI-concern`.

The main sensitivity outcome is `vMost` versus `vNo`.

DILIrank categories are curated drug-level concern labels derived from FDA-approved labelling and literature evidence. They are neither patient outcomes nor a flawless clinical gold standard.

## 6. Predictor representations

Every model receives features generated from the same standardised parent structure, with stereochemistry retained when source evidence supports it.

### Model A: descriptors only

- Molecular weight
- Calculated logP
- Topological polar surface area
- Hydrogen-bond donors and acceptors
- Rotatable bonds
- Ring counts
- Formal charge
- Fraction sp3 carbon

### Model B: conventional baseline

Model A plus a chirality-aware radius-2, 2,048-bit Morgan fingerprint.

### Model C: MAMMAL only

The frozen, pilot-locked MAMMAL embedding.

### Model D: expanded model

All Model B predictors plus the same frozen MAMMAL embedding used in Model C.

## 7. Label-blind technical pilot

After written IEC determination and before outcome analysis, 20 deliberately varied molecules will test:

- structure preprocessing;
- exact checkpoint and tokenizer revisions;
- molecular prompt syntax;
- sequence-length and truncation handling;
- selected hidden layer and pooling rule;
- vector dimension, finiteness, determinism, runtime, and resource use.

At least 18 of 20 molecules must yield repeatable finite vectors within a pre-specified numerical tolerance. One documented technical correction cycle is permitted. Persistent failure ends the primary MAMMAL comparison as technically infeasible; it does not permit outcome-guided substitution of another representation.

## 8. Model development

The primary prediction algorithm for all four representations is L2-regularised logistic regression. Regularisation strength is selected only in inner training folds from a fixed grid. The mild class imbalance does not justify synthetic oversampling. The primary analysis will use unweighted likelihood unless the biostatistical adviser specifies otherwise before lock; class weighting may be a pre-specified sensitivity analysis.

Descriptor and embedding scaling is fitted on training data only. Binary Morgan bits remain binary. Principal-component or other dimension reduction is not part of the default primary pipeline; it may be introduced only if the label-blind pilot documents a technical necessity and the exact procedure is locked before outcomes are inspected.

## 9. Validation

Primary evaluation uses five repeats of nested five-fold cross-validation grouped by Bemis–Murcko scaffold. Acyclic molecules with an empty scaffold are assigned using a locked fingerprint-similarity clustering procedure. Each outer fold must include both outcome classes.

All of the following are fitted or selected within the appropriate training partition only:

- feature scaling and imputation;
- any permitted dimension reduction;
- regularisation;
- classification threshold;
- probability recalibration, if pre-specified.

A conventional stratified random split is a robustness analysis, not the headline result.

## 10. Statistical analysis

For every repeat, each eligible drug receives one out-of-fold probability from each model. Models are compared on identical held-out observations. The primary report contains Model B and D AUROCs, paired `ΔAUROC`, and a two-sided 95% confidence interval.

Uncertainty will be estimated with 2,000 resamples of complete scaffold groups. The final resampling unit, repeated-cross-validation aggregation rule, and confidence-interval construction must be simulation-checked and locked before performance is inspected.

Secondary metrics are:

- area under the precision-recall curve;
- sensitivity, specificity, precision, and balanced accuracy;
- Brier score;
- calibration intercept and slope;
- false-negative review focused on `vMost` drugs.

The main decision threshold maximises Youden's index within training data. A separate sensitivity-prioritised threshold targeting at least 80% sensitivity, where feasible, will be reported.

## 11. Secondary and exploratory analyses

### `vMost` versus `vNo`

Repeats the locked comparison after excluding `vLess`, providing a clearer but smaller contrast.

### DILIrank update cohort

Eligible records from the original 1,036-drug list form the development cohort using current DILIrank 2.0 labels. The locked pipeline is applied once to eligible records among the 300 additions. This is temporal/update-cohort transport analysis, not independent external validation, prospective validation, or proof of pretraining novelty.

### Oral-drug dose/exposure subset

Among eligible oral drugs that link reliably to a version-locked dose source, complete-case models compare:

- Model B plus log daily dose and a Rule-of-Two indicator; versus
- the same predictors plus MAMMAL.

The Rule of Two is daily dose at least 100 mg and calculated logP at least 3. Coverage, regimen rules, source dates, and differences between included and excluded drugs must be reported.

## 12. Ethics and data governance

A written Institutional Ethics Committee determination must precede the pilot or analysis. The study uses public drug-level data and no human participants, identifiable personal information, specimens, or animals. Consent is not applicable, but local IEC/KUHS documentation requirements still govern submission.

Access to working files will be limited to authorised investigators. Source licences and attribution requirements will be respected. Exclusions, embedding failures, deviations, funding, conflicts, and limitations will be disclosed.

## 13. Reporting

The final report will follow TRIPOD+AI where applicable while explicitly stating that this is drug-level classification, not an individual clinical diagnostic or prognostic model. The report will include a flow diagram, eligible cohort, exclusions, scaffold groups, complete model definitions, out-of-fold estimates, uncertainty, calibration, important errors, sensitivity analyses, and reproducibility artefacts.

