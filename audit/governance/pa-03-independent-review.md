# Independent technical/scientific review of PA-03

Date: 2026-08-13 (Asia/Calcutta)

- Reviewed substantive proposal SHA-256: `81160c139e8da36c1e1c5b7040cc05a97e4acd303bc91bf76047359eb9ae5230`
- Pre-expert administrative-state SHA-256: `280639b901c71b4303d5ebd3c711412028f32b4411a9b57d5cfe173c59376f12`
- Failure-record SHA-256: `fe021df60f5c1e9d444f754772077cc317440b8dc444f003393ec15007fd1f08`
- Extraction implementation revision: `f6c35939f23ac27fa30c028589ef71888d316a26`
- Review boundary: non-identifying public record; private names, signatures, faculty-guide records, IEC records, and institutional identifiers are intentionally omitted
- Outcome-access statement: no DILI label, prediction, model-performance artifact, estimation output, or outcome-analysis artifact was accessed during this review

## Verdict

**PASS — PA-03 is technically and scientifically acceptable for the narrowly defined validation-only recovery.**

This verdict approves the amendment design only. It does not authorize an implementation edit, a new extraction, G2 acceptance, feature generation, modelling, estimation, performance inspection, or result reporting. Those actions remain subject to the approved amendment being committed, narrow implementation review and tests, clean relocking, independent lock validation, and a separate G2 verdict.

## Evidence reviewed

The review independently confirmed that the stopped validator compared the POSIX key `tokenizer/config.yaml` against Windows-generated manifest keys containing `tokenizer\config.yaml`. Every frozen manifest contains the tokenizer configuration and all five tokenizer-file records.

The SHA-256 and byte-size values for all six frozen NPZ and manifest artifacts exactly match `audit/pilot/g2-path-serialization-failure.md`. All three manifests identify extraction revision `f6c35939f23ac27fa30c028589ef71888d316a26`, which is the exact Git revision. The artifacts remain generated but not G2-accepted.

The prior outcome-blind, in-memory diagnostic established that the separator defect was the only blocking assertion: all three runs had 20 of 20 successful rows, 768-dimensional finite unit vectors, identical same-order vectors, reversed-order maximum absolute difference `3.91155481338501e-08`, and distinct run UUIDs, process IDs, and timezone-aware timestamps. That diagnostic did not rewrite or regenerate any source artifact.

## Contract assessment

PA-03 correctly requires future POSIX serialization for both model and tokenizer paths, read-only canonicalization of legacy separators, rejection of drive-qualified, UNC, rooted, empty, dot, and traversal paths, and failure on normalized-key collisions. It retains the required tokenizer configuration check, requires recorded hashes and sizes to match the pinned snapshot, and specifies regression coverage for Windows separators, omissions, unsafe paths, POSIX writing, and collisions.

Validation-only reuse is bound to the six immutable artifact hashes, the original extraction revision, and the future validation revision. Existing manifests and vectors may not be rewritten, and another extraction requires a separate amendment. The full PA-01 acceptance contract remains applicable after canonicalization.

The amendment changes no pilot molecule, structure, order, checkpoint, tokenizer byte, prompt, token rule, maximum length, hidden state, pooling operation, normalization, dtype, device, batch size, dimensionality, tolerance, required success count, cohort, DILI endpoint, split, model, estimand, metric, resampling rule, benchmark, or interpretation rule. It therefore creates no outcome-guided selection pathway.

## Administrative-change determination

The owner, faculty-guide, and IEC rows added after the corrected substantive proposal record completed governance decisions and are each bound to substantive SHA-256 `81160c139e8da36c1e1c5b7040cc05a97e4acd303bc91bf76047359eb9ae5230`. Those row changes do not alter PA-03's trigger, technical contract, immutable artifacts, scientific invariants, alternatives, impact assessment, failure rule, or execution conditions. They are non-substantive administrative changes and do not invalidate this review.

Recording the independent expert verdict and changing overall status from `PROPOSED` to `APPROVED` are likewise administrative. Approval does not itself satisfy G2: the implementation must remain within the reviewed scope, PA-03 must be enforced by the protocol lock and pipeline, the final clean revision must be relocked and independently validated, and the corrected validator must pass against the exact frozen artifacts.
