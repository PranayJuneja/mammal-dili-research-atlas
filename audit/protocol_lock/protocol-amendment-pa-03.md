# Protocol amendment PA-03: platform-independent manifest path validation

Date proposed: 2026-08-13 (Asia/Calcutta)

Status: PROPOSED — G2 acceptance and all downstream execution remain prohibited

## Trigger and scope

After the approved PA-01 three-process extraction completed, the validator stopped
because Windows serialized the tokenizer configuration key as
`tokenizer\config.yaml` while the validator required `tokenizer/config.yaml`. The file
and its correct hash are present in every manifest. This amendment is prospective,
outcome-blind, and limited to manifest path representation and validation. It does not
authorize another extraction.

The frozen artifacts and their pre-amendment hashes are recorded in
`audit/pilot/g2-path-serialization-failure.md`. They were generated at extraction
revision `f6c3593d9d43349061146730809c31ac4d31ed91` and remain immutable.

## Amended implementation contract

1. Future model and tokenizer manifest keys are serialized with
   `Path.relative_to(snapshot).as_posix()`.
2. The validation read path accepts legacy relative keys using either `/` or `\`,
   canonicalizes separators to `/` in memory, and never rewrites a source manifest.
3. Before canonicalization, every key must be relative. Drive-qualified paths, UNC
   paths, rooted paths, empty path segments, `.` segments, and `..` traversal segments
   are rejected.
4. Canonicalization must be injective. If two original keys normalize to the same
   canonical key, validation fails with a collision error.
5. Both `model_files` and `tokenizer_files` use the same canonicalization and safety
   rules before invariant comparison.
6. `tokenizer/config.yaml` must still be present after canonicalization, and all
   recorded file hashes and byte sizes must still match the pinned snapshot.
7. Windows-separator acceptance, POSIX serialization, omission, traversal, absolute
   path, and normalized-key-collision cases receive regression tests.

## Validation-only reuse

After PA-03 approval, implementation, clean commit, relock, and independent lock
review, the corrected validator may read the existing three artifacts only after
verifying all six exact hashes in the failure record. It must separately record:

- extraction implementation revision `f6c3593d9d43349061146730809c31ac4d31ed91`;
- validation implementation revision from the new execution lock; and
- the immutable NPZ and manifest hashes used for the verdict.

The validator then applies the entire unchanged PA-01 contract. The old manifests and
NPZ files are never modified. No new extraction process is launched unless a separate
future amendment explicitly authorizes it.

## Scientific invariants

PA-03 changes none of the following: the 20 pilot molecules, input order, SMILES,
checkpoint, checkpoint revision, tokenizer bytes, checkpoint-native prompt, special
tokens, unknown-token rule, maximum length, overlength rule, hidden state, pooling,
L2 normalization, dtype, device, batch size, vector dimension, tolerances, required
success count, cohort, DILI labels, endpoint, models, folds, estimand, metrics,
resampling, practical benchmark, or interpretation wording.

No DILI outcome or predictive-performance result was generated or inspected when the
defect was found, diagnosed, or specified.

## Alternatives considered

| Alternative | Disposition | Reason |
|---|---|---|
| Declare MAMMAL infeasible | Retained fallback | Mandatory if PA-03 is not approved or corrected validation fails. |
| Rewrite the three manifests | Rejected | Would destroy the immutable evidence and obscure the original defect. |
| Rerun extraction after changing serialization | Rejected | The vectors are valid and PA-03 is validation-only; rerunning would add unnecessary researcher degrees of freedom. |
| Accept backslashes without safety checks | Rejected | Naive replacement can hide collisions, absolute paths, or traversal. |
| Canonicalize safely in memory and use POSIX keys prospectively | Selected | Preserves exact evidence while making the manifest contract platform-independent. |

## Impact assessment

- **Estimand and outcomes:** no effect. No outcome data or model performance is used.
- **Bias:** no scientific selection pathway is added; validation remains bound to six
  pre-specified immutable artifact hashes.
- **Reproducibility:** improves cross-platform manifest stability and explicitly
  separates extraction and validation revisions.
- **Schedule/resources:** requires a narrow code/test change, new clean lock, and
  validation-only G2 review; it avoids repeating approximately 200 seconds of valid
  CPU extraction.
- **KUHS/reporting:** disclose the stopped validation, PA-03, immutable artifact reuse,
  and revision split in the reproducibility record.
- **IEC:** no participant, personal-data, intervention, specimen, animal, source,
  endpoint, population, or scientific analysis change. A post-proposal IEC disposition
  must nevertheless be recorded under the project's change-control policy.

## Required approvals and disposition

| Role/action | Status | Evidence boundary |
|---|---|---|
| Project owner acknowledgement | Confirmed 2026-08-13 | Direct owner confirmation is bound to substantive PA-03 SHA-256 `1ec939366936f664a2730156bdee6b8869f1b667edc8113257919797a6b3a0de`. |
| Faculty guide approval | Pending explicit private confirmation | Retain identifying evidence only in the restricted governance record. |
| Independent technical/scientific approval | Pending independent validator verdict | Verify defect, immutable hashes, normalization contract, tests, and no scientific change. |
| IEC notification/approval disposition | Pending explicit post-proposal confirmation | Record `approved`, `notified`, or `not required by determination` with date and exact PA-03 hash. |

G2 acceptance remains prohibited while any row is pending. After all approvals are
complete, PA-03 must be marked `APPROVED`; the narrow implementation and tests must be
committed; PA-03 must be added to execution-lock and pipeline governance enforcement;
and a new clean execution lock must be generated and independently validated before
validation-only reuse of the frozen artifacts.
