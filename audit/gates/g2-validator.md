# G2 independent validator acceptance

Date: 2026-08-13 (Asia/Calcutta)

Status: PASS

Pilot report SHA-256: 8b442cf2f477b1ebc0ac5c67d2d65b4fac95ab37953aeb0187ffff0d7ce53fc2

## Review boundary

This independent review covers only the label-blind MAMMAL pilot, the approved PA-01 representation contract, and the PA-03 validation-only recovery. No DILI outcome, prediction, model-performance artifact, downstream feature matrix, estimation output, or result report was accessed. No extraction or feature-generation process was launched during this review.

## Provenance and immutability

The corrected validator ran under clean locked implementation revision `6cbbcbe51125b63f177c10f23cc8d47798eaa1d6` at reviewed HEAD `793de7faea34de4bdd5a45a020da110aaa3f258c`. The execution lock binds unchanged configuration bundle SHA-256 `6e3495e8c311e0db3dee467d45c95fe3d74229a06931de9882515e09434c50f6` and approved PA-03 SHA-256 `3d568a21db5a3c6060eab906c59f888232665d2cdddd9cbd2f8b041c3c049d16`.

The report correctly separates extraction implementation revision `f6c35939f23ac27fa30c028589ef71888d316a26` from validation implementation revision `6cbbcbe51125b63f177c10f23cc8d47798eaa1d6`. Validation reused the immutable pre-PA-03 artifacts and did not rewrite or regenerate them.

All frozen hashes and byte sizes were independently recomputed before technical inspection:

| Artifact | SHA-256 | Bytes |
|---|---|---:|
| `mammal_pilot_baseline.npz` | `28984f63fb19c200671095b3838926aac1a20d74e606a57a493ca776c4f34de3` | 57,746 |
| `mammal_pilot_baseline.manifest.json` | `874b8d6fe364823028570d21b21cd996aec2f85a603142a4447e416d80e696dd` | 16,360 |
| `mammal_pilot_same_order.npz` | `28984f63fb19c200671095b3838926aac1a20d74e606a57a493ca776c4f34de3` | 57,746 |
| `mammal_pilot_same_order.manifest.json` | `6dd06e130771b071533bc1523541206f861b3a8bbb9566a36be348536932952d` | 16,360 |
| `mammal_pilot_reordered.npz` | `9eff4e485b946c9fe52e743d3b295e78077b7cb13dffdfb8b172cdf99326b683` | 57,746 |
| `mammal_pilot_reordered.manifest.json` | `a74c98cdf298033752b8c42a96f9da4baa773ebfa4b1da3e56015974f96c7beb` | 16,357 |

Every canonical model and tokenizer record in all three manifests was resolved against the current pinned checkpoint snapshot and independently verified by SHA-256 and byte size. This covered 18 manifest records representing one model file and five tokenizer files per run, including `tokenizer/config.yaml`. Input CSV, embedding configuration file, and validated-configuration hashes also match their current locked files.

## Acceptance evidence

- All three processes requested and successfully represented 20 of 20 unique pilot IDs, with no failures.
- Every vector is 768-dimensional, finite, and unit-normalized within the locked numerical checks.
- Token counts and diagnostics align exactly with NPZ row order. Every successful row has zero unknown tokens, no truncation, and no unknown-token warning.
- The baseline, identical-order repeat, and reversed-order repeat have three distinct UUIDs, process IDs, and timezone-aware start timestamps.
- Baseline versus identical-order repeat has the same 20 successful IDs and maximum absolute difference `0`.
- Baseline versus reversed-order repeat has the same 20 successful IDs and maximum absolute difference `3.91155481338501e-08`.
- Both comparisons are finite and remain within the locked absolute and relative tolerances of `1e-05`, exceeding the required minimum of 18 common successful IDs.
- Manifest invariants agree across input, configuration, code, extraction revision, checkpoint and snapshot, model/tokenizer provenance, prompt, pooling, device, dtype, batch size, length and unknown-token rules, environment locks, and tokenizer diagnostics.

## Gate decision and limits

G2 passes. The frozen MAMMAL representation is technically feasible, repeatable across fresh processes, and invariant to the tested batch-order reversal under the approved PA-01 and PA-03 contracts.

This gate does not validate the full 809-molecule extraction, accept G3 feature/fold artifacts, authorize outcome inspection, approve modelling, or establish predictive utility. All later protocol locks and independent scientific gates remain required. Any change to the accepted pilot report or any of its six source artifacts invalidates this hash-bound G2 record.
