# G2 validation hold: Windows manifest path serialization

Date: 2026-08-13 (Asia/Calcutta)

Status: generated but not G2-accepted

## Event

The approved three-process G2 extraction completed for the baseline, fresh
same-order repeat, and fresh reversed-order repeat. The subsequent locked validator
stopped with `Tokenizer manifest omits tokenizer/config.yaml` before issuing a G2
verdict.

The tokenizer file was not omitted. Each manifest contains all five tokenizer files,
including `tokenizer\config.yaml`. Extraction serialized `Path.relative_to(...)` with
the host-native Windows separator while validation required the POSIX spelling
`tokenizer/config.yaml`. No prompt, tokenizer, checkpoint, input, vector, token count,
pooling operation, tolerance, or scientific result caused the failure.

## Frozen artifacts

These files must not be rewritten or regenerated. PA-03 may authorize validation-only
reuse after verifying these exact SHA-256 values before reading the artifacts.

| Artifact | SHA-256 | Bytes |
|---|---|---:|
| `mammal_pilot_baseline.npz` | `28984f63fb19c200671095b3838926aac1a20d74e606a57a493ca776c4f34de3` | 57,746 |
| `mammal_pilot_baseline.manifest.json` | `874b8d6fe364823028570d21b21cd996aec2f85a603142a4447e416d80e696dd` | 16,360 |
| `mammal_pilot_same_order.npz` | `28984f63fb19c200671095b3838926aac1a20d74e606a57a493ca776c4f34de3` | 57,746 |
| `mammal_pilot_same_order.manifest.json` | `6dd06e130771b071533bc1523541206f861b3a8bbb9566a36be348536932952d` | 16,360 |
| `mammal_pilot_reordered.npz` | `9eff4e485b946c9fe52e743d3b295e78077b7cb13dffdfb8b172cdf99326b683` | 57,746 |
| `mammal_pilot_reordered.manifest.json` | `a74c98cdf298033752b8c42a96f9da4baa773ebfa4b1da3e56015974f96c7beb` | 16,357 |

All three manifests record extraction implementation revision
`f6c35939f23ac27fa30c028589ef71888d316a26` and distinct processes, UUIDs, and
timezone-aware timestamps.

## Outcome-blind diagnostic boundary

Independent technical review normalized the manifest keys only in memory and did not
write any artifact. All other frozen validation checks passed: 20/20 successful rows,
768-dimensional finite unit vectors, same-order maximum absolute difference `0`, and
reversed-order maximum absolute difference `3.91155481338501e-08`. No DILI label,
prediction, model-performance, estimation, or outcome-analysis artifact was accessed.

## Disposition

G2 remains blocked. The event is scientifically non-substantive but PA-01 prohibits a
silent correction. Without a prospectively approved PA-03, it must be reported as
technical infeasibility. No feature generation, modelling, estimation, or result
inspection is authorized by this record.
