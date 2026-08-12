# Protocol amendment PA-02: primary development population and untouched update transport

Date proposed: 2026-08-13 (Asia/Calcutta)  
Status: PROPOSED — outcome modelling remains prohibited

## Problem discovered before performance inspection

The written documents contain an internal conflict. `docs/07_STATISTICAL_ANALYSIS_PLAN.md` calls all eligible `vMost`, `vLess`, and `vNo` drugs the primary population, while `docs/06_MODELLING_AND_VALIDATION.md` requires every eligible drug added in DILIrank 2.0 to remain outside development and be evaluated once as an update-era transport cohort. Both cannot hold simultaneously. The first implementation filtered added drugs before fitting but inherited chemical groups and folds constructed on all 809 eligible rows, allowing update structures and labels to influence development grouping and fold allocation.

No model was fitted and no predictive performance, AUROC, calibration, error, transport, or robustness result was generated or inspected when this conflict was identified by independent review.

## Proposed resolution

1. Define the **primary development population** as eligible original-list DILIrank drugs only: 675 drugs under the current locked cohort.
2. Remove the 134 eligible added-in-2.0 drugs before scaffold/acyclic grouping and fold generation, not merely before fitting.
3. Construct development chemical groups and repeated folds from the 675 rows alone. Current outcome-blind construction yields 460 development groups, largest size 69.
4. Construct group identifiers for the 134 update drugs separately, without assigning development folds. Current outcome-blind construction yields 125 update groups, largest size 5.
5. Develop preprocessing, regularisation and thresholds only on the original-list cohort. Fit the final development pipeline once and apply it once to the untouched update cohort.
6. Re-run the pre-performance precision simulation on the actual 675-row/460-group development vector before any model performance is computed.
7. Require successful frozen MAMMAL extraction for all 809 structurally eligible drugs. Any failure stops G3; the population, groups, folds and precision evidence are not silently reduced after feature generation.
8. For the one-time update fit, select each model's final `C` as the modal value among its 25 outer-fold selections (five repeats by five folds); ties choose the smaller `C`, corresponding to stronger regularisation. This rule is locked in `configs/analysis.yaml`, and the tuning file must be hash-bound to the accepted development predictions before update outcomes are accessed.

The primary estimand becomes the mean paired repeat-level `AUROC(D) - AUROC(B)` under repeated scaffold-grouped validation in eligible original-list drugs. The added-drug estimate is explicitly secondary exploratory transport evidence and cannot replace the primary result.

## Alternatives considered

| Alternative | Disposition | Reason |
|---|---|---|
| Use all 809 drugs as the primary population and abandon untouched transport | Rejected | It resolves the contradiction but destroys the protocol's stronger update-era isolation test. |
| Use 675 for fitting but retain groups/folds built on all 809 | Rejected | Update structures and labels would influence primary development design before the purported untouched evaluation. |
| Treat the 134 additions as an ordinary outer fold | Rejected | Hyperparameter development across other folds and repeated reuse would no longer be a one-time transport evaluation. |
| Use original-list-only primary development plus one untouched update evaluation | Selected | It satisfies the explicit transport workflow and creates a clean temporal/update-era boundary. |

## Impact assessment

- **Estimand:** narrows the primary target population from all eligible DILIrank 2.0 drugs to eligible original-list drugs under current 2.0 labels. This is a substantive population clarification and will be disclosed in the abstract, methods, flow diagram and limitations.
- **Bias:** removes update-era influence from development grouping, fold assignment, preprocessing, tuning and threshold selection. It may increase uncertainty because the primary sample decreases from 809 to 675.
- **Precision:** the existing 809-row simulation is retained as superseded planning history. The completed replacement simulation used the 675-row/460-group development vector, with minimum empirical coverage 0.825, maximum mean interval width 0.0547 and maximum 100-versus-2,000-resample endpoint shift 0.0080 across planning scenarios. These diagnostics require cautious estimation/inconclusive wording; no analysis setting was changed in response.
- **Schedule/resources:** requires regeneration of analysis-specific groups/folds, precision evidence, modelling manifests, report text and independent review. Molecular curation and the 809-row embedding extraction target do not change.
- **KUHS documents:** methodology, analysis population, sample flow, primary estimand wording and update analysis must be revised. Title and research objective remain unchanged.
- **IEC determination:** no participant, personal-data, intervention, specimen, animal, public source, molecular eligibility rule or outcome definition changes. Notification disposition must nevertheless be confirmed against the private determination.

## Required approvals and disposition

| Role/action | Status | Evidence boundary |
|---|---|---|
| Project owner acknowledgement | Pending explicit PA-02 confirmation | Record only a dated, non-identifying status. |
| Faculty guide approval | Pending explicit private confirmation | Names/signatures remain outside this repository. |
| Biostatistical/design expert approval | Pending independent validator gate | Must verify the revised population, grouping, precision, estimators and leakage controls. |
| IEC notification/approval disposition | Pending owner/guide confirmation | Record `not required by determination`, `notified`, or `approved`, with date. |

Outcome modelling remains prohibited while any row is pending. On approval, this amendment must be marked `APPROVED`, the final implementation/configuration must be committed, the protocol execution lock must be regenerated from that clean implementation revision, and the lock must actively reject later code or config drift.
