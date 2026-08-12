# Protocol amendment PA-01: checkpoint-compatible pilot representation

Date proposed: 2026-08-13 (Asia/Calcutta)  
Status: PROPOSED — accepted MAMMAL extraction remains on hold pending independent approval

## Scope and reason

This prospective, outcome-blind amendment supersedes the pilot-freeze and single-correction-cycle wording in `docs/05_MAMMAL_FEASIBILITY_PLAN.md` only for the technical defects listed below. It does not alter the cohort, DILI labels, endpoint, split groups, models, metrics, statistical thresholds or interpretation rules. No DILI outcome or predictive-performance result was inspected in finding or correcting these defects.

1. The first launch failed before tokenisation because the pinned tokenizer lives below `tokenizer/` in the checkpoint snapshot. The path and `Path`-conversion fixes are retained.
2. A completed diagnostic extraction showed that the original long-carbon fixture compressed to only 275 tokens. It was therefore not a near-limit fixture. `PILOT-20` is replaced by the already documented isotope-explicit, RDKit-valid carbon chain.
3. Independent review then found that the configured newer vLLM prompt token `MOLECULAR_ENTITY_OF_TYPE_SMALL_MOL` is unsupported by the pinned checkpoint tokenizer. Every old pilot prompt emitted an unknown-token warning and ID 0 values. All vectors from that prompt are withdrawn.

## Amended frozen representation

The accepted representation is the checkpoint-native MAMMAL molecule form used by the pinned code's molecule examples:

`<@TOKENIZER-TYPE=SMILES><MOLECULAR_ENTITY><MOLECULAR_ENTITY_SMALL_MOLECULE><SEQUENCE_NATURAL_START>{SMILES}<SEQUENCE_NATURAL_END><EOS>`

The modular-tokenizer hint is required by the installed pinned implementation but does not itself add an attended token. For `CCO`, the attended IDs are `[6, 286, 283, 798, 277, 5]`, with no ID 0 and no unknown-token warning. Under the same form, revised `PILOT-20` is 2,324 characters and 1,997 attended tokens, below and near the 2,100-token rejection threshold, with zero unknown tokens. The extractor now rejects any unpadded ID 0 or unknown-token warning and records per-row counts and warnings.

## Acceptance execution

After independent approval and a clean protocol re-lock, G2 will use three new Python processes on the same tracked 20-row input:

1. baseline in frozen order;
2. identical-order repeat;
3. reversed-order repeat.

Baseline versus identical order will assess fresh-process repeatability. Baseline versus reversed order will separately assess batch-order invariance. All three manifests must include input, config, implementation, code, checkpoint, weight and tokenizer hashes. At least 18 identical successful IDs must have finite vectors within the frozen absolute and relative tolerances in both comparisons. Any further representation or fixture correction is disallowed; a new technical failure will be reported as infeasibility unless separately amended before another accepted run.

## Disposition of earlier runs

All earlier pilot outputs are diagnostic and withdrawn because they either predate the final fixture or contain unknown-token IDs. They are not evidence for G2 acceptance and will not enter modelling.

## Alternatives considered

| Alternative | Disposition | Reason |
|---|---|---|
| Keep the newer vLLM prompt | Rejected | It yields unknown-token IDs for every pilot row under the pinned checkpoint tokenizer, so the vectors do not represent the stated molecular contract. |
| Switch to a different checkpoint or tokenizer | Rejected | This would change the frozen representation and broaden the amendment beyond a compatibility correction. |
| Remove the near-limit fixture | Rejected | It would weaken the prospective overlength/truncation test required by the pilot composition contract. |
| Stop and report MAMMAL infeasible | Retained fallback | This remains mandatory if the amended three-process run fails; there will be no further technical correction. |
| Use the pinned checkpoint-native syntax and keep the revised fixture | Selected | It is supported by pinned source examples, tokenizes every frozen row without unknowns, and changes no outcome-related method. |

## Impact assessment

- **Estimand:** no effect. The primary estimand remains mean repeated scaffold-grouped `AUROC(D) - AUROC(B)` on common eligible rows.
- **Bias:** the change reduces representation error by preventing unsupported control strings from becoming unknown tokens. It creates no outcome-selection pathway because the defect and correction were established without DILI labels or predictive performance.
- **Schedule/resources:** adds an independent amendment review, a clean re-lock, and three new CPU pilot processes. Earlier diagnostic compute is discarded.
- **KUHS documents:** the methods and reproducibility wording must name the checkpoint-native prompt and disclose PA-01; title, objectives, population, endpoint and analysis remain unchanged.
- **IEC determination:** no participant, personal-data, intervention, specimen, animal, source-data, endpoint or analysis-population change is introduced. Whether the existing private IEC determination requires notification remains an institutional decision and must be explicitly recorded below; this repository does not self-declare exemption or waive notification.

## Required approvals and notification disposition

| Role/action | Status | Evidence boundary |
|---|---|---|
| Project owner acknowledgement | Pending explicit PA-01 confirmation | May be recorded in a non-identifying public governance note. |
| Faculty guide approval | Pending explicit private confirmation | Names and signatures remain outside the public repository; only dated confirmation is recorded here. |
| Relevant technical/scientific expert approval | Pending independent validator verdict | Fermat independently verifies the prompt, hashes, pilot, and acceptance implementation. |
| IEC notification/approval disposition | Pending owner/guide confirmation against the private determination | Record `not required by determination`, `notified`, or `approved`, with date; do not copy identifying records here. |

Accepted extraction remains prohibited while any row is pending. Once all are confirmed, change the amendment status from `PROPOSED` to `APPROVED`, add the decision date and non-identifying evidence note, re-lock the configuration if needed, and only then launch the three fresh processes.
