# Modelling and Validation Framework

## Design principle

The primary comparison changes one information block and nothing else. Model D receives every predictor in Model B and adds only MAMMAL. Both models are trained and evaluated on the same drugs, folds, preprocessing rules, tuning opportunities, and prediction algorithm.

## Representation matrix

| Component | A | B | C | D |
|---|:---:|:---:|:---:|:---:|
| Physicochemical descriptors | Yes | Yes | No | Yes |
| Morgan fingerprint | No | Yes | No | Yes |
| Frozen MAMMAL embedding | No | No | Yes | Yes |
| Primary role | Supporting | Conventional baseline | Secondary | Expanded |

Model A and C explain representation behaviour. Only D versus B answers the primary incremental-value question.

## Feature preprocessing

### Descriptors

- Compute from the locked standardised molecule with a version-pinned chemistry toolkit.
- Inspect missing, infinite, and impossible values before outcomes are used.
- Fit median imputation, if needed, within training data only.
- Standardise continuous descriptors using training-fold means and standard deviations.

### Morgan fingerprint

- Radius 2.
- 2,048 binary bits.
- Chirality enabled.
- Generated from the same standardised molecule used by MAMMAL.
- Bits remain binary; no global feature selection.

### MAMMAL

- Use the pilot-locked vector without changing model weights.
- Standardise each embedding dimension within training folds.
- Do not select dimensions using the full dataset.

### Dimension reduction

No dimension reduction is planned in the primary pipeline. If label-blind technical evidence makes it necessary, the transformation, component grid, fitting scope, and application to each representation must be locked before outcomes. Any transformation is fitted within inner training data and applied to validation/test data.

## Primary classifier

L2-regularised logistic regression is used for Models A–D.

The provisional inverse-regularisation grid is logarithmic, for example:

`C ∈ {1e-4, 1e-3, 1e-2, 1e-1, 1, 10, 100}`

The final grid, solver, maximum iterations, convergence tolerance, intercept handling, random seed, and class-weight setting must be locked after feature dimensions are known and before performance is inspected.

Failure to converge is not ignored. The pipeline records warnings, applies a pre-specified iteration escalation if allowed, and reports unresolved failures.

## Scaffold grouping

### Ring-containing molecules

Compute the Bemis–Murcko scaffold from the locked standardised molecule. Molecules with the same scaffold identifier remain in the same outer group.

### Acyclic molecules

An empty Murcko scaffold is not informative. Acyclic molecules are clustered using radius-2 fingerprints, Tanimoto similarity, and Butina clustering with the pilot-locked threshold currently proposed as 0.50. The resulting cluster is the group.

### Duplicate and near-duplicate protection

Exact duplicate parents are resolved before folds. Scaffold groups are inspected for very large groups and label composition. No molecule may change group to improve a result.

## Outer-fold construction

- Five outer folds, repeated five times with fixed recorded seeds.
- Assignment is by scaffold/acyclic cluster, not individual molecule.
- Seek approximate outcome balance without splitting a group.
- Every test fold must contain both outcome classes.
- The fold-generation algorithm and tie-breaking rules are versioned.
- If constraints make five folds impossible, the fallback number of folds is selected from outcome-blind group statistics and documented before modelling.

## Inner tuning

Within each outer training set:

1. Create scaffold-grouped inner folds.
2. Fit preprocessing only on the inner training partition.
3. Evaluate the fixed regularisation grid on inner validation partitions.
4. Select the hyperparameter using a locked rule, provisionally mean inner AUROC with deterministic tie-breaking toward stronger regularisation.
5. Refit preprocessing and the classifier on the complete outer training set.
6. Predict probabilities for the untouched outer test fold.

Outer test outcomes are not used for tuning, threshold selection, convergence fixes, feature transformations, or recalibration.

## Prediction artefact

Write one row per drug, model, repeat, and outer fold containing:

- local drug identifier;
- scaffold group;
- repeat and fold;
- observed outcome;
- predicted probability;
- selected hyperparameter;
- convergence status;
- feature-pipeline revision;
- model configuration hash.

This long-form table is the basis for every primary performance calculation. Do not recompute headline numbers from ad hoc notebook state.

## Threshold selection

AUROC and precision-recall AUROC do not require a classification threshold. For thresholded measures:

- Primary descriptive threshold: maximises Youden's index using training-fold predictions only.
- Safety-oriented threshold: targets at least 80% sensitivity in training data, where feasible, with its resulting specificity reported.
- Apply the selected threshold once to the corresponding outer test fold.

No full-dataset “optimal threshold” may be used for out-of-fold performance.

## Calibration

Report calibration intercept and slope from out-of-fold predictions, with uncertainty where feasible. Because recalibration can mask representation differences, the primary models are assessed without post hoc test-set recalibration. Any calibration method must be trained inside the outer training process and labelled secondary.

## Update-cohort transport analysis

1. Identify original-list and 300-addition membership from DILIrank 2.0.
2. Develop all preprocessing and hyperparameters on eligible original-list records only.
3. Lock the pipeline.
4. Apply it once to eligible added records.
5. Report performance and uncertainty with the smaller update-cohort size clearly shown.

This analysis tests time/update-era transport. MAMMAL may have encountered these molecules during pretraining, and DILIrank labels were updated for some original drugs.

## Robustness analyses

Subject to protocol lock and resources:

- stratified random split to quantify how much easier non-scaffold evaluation appears;
- alternative scaffold-clustering threshold fixed before outcomes;
- class-weighted logistic regression;
- canonical versus randomised equivalent SMILES stability;
- Model A and C comparisons;
- `vMost` versus `vNo` outcome;
- original versus added-cohort transport;
- clearly secondary gradient-boosted classifier, only if pre-specified.

Robustness analyses cannot replace or redefine the primary result.

## Leakage checklist

- [ ] Structure duplicates resolved before fold assignment.
- [ ] Scaffold groups never split across train/test.
- [ ] Imputation fitted inside training data.
- [ ] Scaling fitted inside training data.
- [ ] Dimension reduction, if any, fitted inside training data.
- [ ] Hyperparameters selected in inner folds only.
- [ ] Thresholds selected using training predictions only.
- [ ] Update cohort touched once after pipeline lock.
- [ ] Pilot representation chosen without DILI labels or performance.
- [ ] All models use identical eligible rows and outer folds for paired comparison.

