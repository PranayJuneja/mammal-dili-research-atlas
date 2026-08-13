# G4 independent validator acceptance

Date: 2026-08-13 (Asia/Calcutta)

Status: PASS

Gate lock SHA-256: 26908c6a723a1e912bd1d16184a39978eacc2b4d78d2ab5e7b2781ce5eb6791e

## Review boundary

This independent review validates prediction, tuning, fold, manifest, and update-fit contracts only. It does not calculate or interpret AUROC, compare model performance, estimate an effect, run a bootstrap, inspect a result report, or state a scientific conclusion. Prespecified tuning-score fields were checked only for complete finite structural coverage.

## Lock and source lineage

The G4 candidate is bound to protocol-lock SHA-256 `058cc8082872fd27a98884cf6d8411d6ed7232a0b5197d5377d8e52879a04cdf` and accepted G3 SHA-256 `583ba6e319575b39fc1ebfb12d2b923be3d8895c18a8c2aa03e5ae090c2e09ff`. Every development and update manifest identifies locked modelling implementation revision `f8b1270cabbb02e7c3528935fa5290a6482d1b6b`, the current configuration bundle, current G3 lock, current protocol lock, and the exact frozen conventional and MAMMAL feature artifacts.

All 18 G4 source hashes independently match the current files: four prediction CSVs, four corresponding manifests, four tuning logs, four fold artifacts, the update prediction CSV, and its manifest. The prior withdrawn G4 marker is not reused.

## Prediction contracts

- Primary development predictions contain exactly 675 drugs, four models, and five repeats: 13,500 unique drug/model/repeat rows.
- The prespecified `vMost` versus `vNo` sensitivity population contains exactly 382 drugs, two models, and five repeats: 3,820 unique rows.
- The optimistic stratified-random robustness analysis contains exactly 675 drugs, two models, and five repeats: 6,750 unique rows.
- The balanced-class scaffold-grouped robustness analysis contains exactly 675 drugs, two models, and five repeats: 6,750 unique rows.
- Update transport contains exactly 134 drugs and four models: 536 unique drug/model rows.

For every contract, probabilities and all numeric tuning/threshold fields are finite, probabilities lie in `[0,1]`, outcomes are binary, required model pairing is exact, release groups match the prescribed population, and recorded outcome/category/scaffold fields match the G3 population artifact. All final-fit and outer-fit convergence-warning counts are zero.

## Fold and tuning integrity

- Every development prediction has the exact outer-fold assignment in its analysis fold artifact.
- Scaffold-grouped designs reproduce the accepted G3 fold assignments and never split a chemical group within a repeat.
- Every fold contains both outcome classes.
- The stratified-random analysis fold artifact was independently reproduced from the locked seeds while preserving the G3 chemical scaffold identifier for later grouped uncertainty analysis.
- Each model/design combination has one unique tuning entry for every five-repeat by five-outer-fold cell.
- Every tuning entry contains the complete seven-value locked regularisation grid, a selected value from that grid, finite prespecified inner-tuning scores, and zero candidate convergence warnings.
- Each prediction row's selected regularisation value agrees with its corresponding tuning cell.

## Held-out update provenance

All four development manifests now record exactly 134 held-out update drugs with sorted, newline-delimited ID SHA-256 `8ddd245694516063bdca95c8040cfdc7d421aa3e0748d504de5f5e4ca899fdb8`. This is the exact G3 update-group ID set and was derived using ID-only access before development tuning. No update outcome entered development grouping, folds, fitting, threshold selection, or tuning.

The update run is bound to the accepted primary prediction, tuning, manifest, development folds, update groups, and both feature families. For each of models A–D, the final regularisation value and all 25 outer-selection counts independently reproduce the locked rule: choose the modal value across the five-by-five development selections, resolving ties toward the smaller value. The update rows use those reconstructed values and have exact 134-by-four coverage.

## Gate decision and limits

G4 passes. The five prediction analyses, tuning records, analysis folds, corrected held-out-update provenance, and one-time update-fit contract are structurally complete and reproducibly bound to the accepted protocol and G3 feature/fold lock.

This verdict does not establish predictive performance, comparative benefit, statistical significance, calibration, transportability, or clinical utility. Estimation, bootstrap uncertainty, interpretation, reporting, and every later independent gate remain separate requirements. Any change to the G4 lock or one of its 18 source artifacts invalidates this hash-bound verdict.
