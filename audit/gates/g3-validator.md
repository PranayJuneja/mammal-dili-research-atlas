# G3 independent validator acceptance

Date: 2026-08-13 (Asia/Calcutta)

Status: PASS

Gate lock SHA-256: b10eed352cca35751c5ff695c3b53ba59db20274dbeb28e3c8a13cae3784b4f3

## Review boundary

This independent review covers the frozen cohort, conventional and MAMMAL feature artifacts, deterministic embedding repeat, development and update grouping, outer folds, precision evidence, and their G3 lineage. No model was fitted, and no prediction, model-performance, estimation, or results artifact was accessed.

## Lock and source lineage

The G3 candidate was generated at implementation revision `d1dd27c68be8f0e86c0101c6583e764202ead6dd` against protocol-lock SHA-256 `79ff95a5ff8ee34475f6e2278151ea236f23e208713cec862536d0ac0514116b` and configuration-bundle SHA-256 `6e3495e8c311e0db3dee467d45c95fe3d74229a06931de9882515e09434c50f6`.

Its amendment map exactly matches the active protocol lock:

- PA-01: `1c68ccf480b3d14da910e3e4f6a4267fc50fbcb39041d43c3ec4fb90b50bd773`
- PA-02: `ac1023e0d1a73ba3e226f1682a069a5c8e7997e68c47f78c944b903b19dcf7bf`
- PA-03: `3d568a21db5a3c6060eab906c59f888232665d2cdddd9cbd2f8b041c3c049d16`

All 19 source entries independently match their current SHA-256 values. This includes the cohort and label-blind inputs; both feature families and manifests; full and repeat MAMMAL artifacts; the full-extraction QC report; all-cohort, development, and update fold/group artifacts and summaries; and the precision CSV, summary, and assessment. `require_feature_fold_lock(require_validator=False)` passes without bypassing source, configuration, amendment, partition, or protocol-lock checks.

## Feature and extraction evidence

- The eligible feature population contains 809 unique drugs in one exact order. Conventional and MAMMAL NPZ IDs both match that order, whose SHA-256 JSON digest is `55b0bdd8c2ad3234c920696de2f6f37eed912fe56dd01fb7f20c26a4d92572fd`.
- Conventional features are common-complete: nine configured finite descriptors and a binary 2,048-bit chirality-aware Morgan fingerprint for every drug.
- Full MAMMAL extraction has 809 of 809 successful rows with 768-dimensional finite unit-normalized vectors, exact ID order, and no extraction failures, unknown-token IDs, truncation, or unknown-token warnings.
- Every recorded model and tokenizer file matches the pinned snapshot provenance. Full and repeat manifests agree on configuration, code, checkpoint, snapshot, prompt, pooling, numeric settings, environment locks, and tokenizer diagnostics.
- The deterministic verification sample contains the exact seeded, sorted 41 rows and hash `de1aad6d23c0f5991204d9c58b9184b0c385ce99ff9738bbfcee40ac2a74ebf5`. It was extracted in a distinct process and timestamp, with maximum absolute vector difference `4.470348358154297e-08`, within the locked `1e-05` tolerances.
- The restored full-extraction QC artifact remains unchanged at SHA-256 `a8e2f81226ab84e6bd3a7f77989b7c2998c58f03d4b89b83fdbe6c346936aa61`.

## Population, grouping, and folds

- The primary development population contains exactly 675 eligible `original-list` drugs and 460 groups; the largest group contains 69 drugs.
- The 134 eligible `added-in-2.0` drugs form a disjoint update population with 125 separately generated groups and no development-fold assignments.
- Development scaffold and acyclic groups were independently reproduced using only development structures. Update structures and labels therefore did not influence development grouping or fold allocation.
- Across five repeats and five folds, each development group occurs in exactly one test fold per repeat. Every fold contains both outcome classes, with no scaffold leakage or unassigned row.
- The development and update IDs are unique, disjoint, and together form the exact 809-drug feature population.

## Precision evidence

The current planning evidence is based on the locked 675-row, 460-group development folds, including the largest 69-drug group. Its fold hash matches the G3 development-fold artifact. The evidence records five paired prediction sets, 16 planning scenarios, minimum empirical coverage `0.825`, maximum mean interval width `0.05474011978982642`, and maximum 100-to-2,000-resample endpoint shift `0.007973629289142595`.

The precision simulation CSV is now explicitly frozen at SHA-256 `d6835f76be29e7d9843ff92894c69ea5b39b0acb3db852a73b70edacc4a97bd1`. The assessment appropriately treats this as an imprecise pre-performance planning diagnostic and retains estimation-focused, interval-based interpretation without changing the locked analysis.

## Gate decision and limits

G3 passes. The feature population, feature families, MAMMAL verification, development/update partition, scaffold-grouped folds, precision evidence, and complete protocol lineage are accepted for the locked modelling workflow.

This verdict does not validate any prediction, tuning choice, model performance, update-transport result, estimate, or report. G4 and all later independent gates remain mandatory. Any change to the G3 lock or any of its 19 source artifacts invalidates this hash-bound verdict.
