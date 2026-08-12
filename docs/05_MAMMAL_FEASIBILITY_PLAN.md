# MAMMAL Feasibility and Embedding Plan

## Why this stage exists

The public checkpoint is real and usable, but “the MAMMAL embedding” is underspecified. The model accepts task-formatted inputs, and internal numerical representations depend on choices that are not fixed by the checkpoint name. This study needs a reproducible representation contract before DILI labels influence any engineering decision.

## Intended software resource

- Model family: MAMMAL, Molecular Aligned Multi-Modal Architecture and Language.
- Intended checkpoint: `ibm-research/biomed.omics.bl.sm.ma-ted-458m`.
- Public model size: approximately 0.5 billion parameters.
- Codebase: `BiomedSciAI/biomed-multi-alignment`.
- Current project requirement: Python 3.10–3.12 according to the repository package metadata; exact versions will be pinned at pilot time.
- Model weights remain frozen throughout the study.

The checkpoint alias `ibm/...` versus `ibm-research/...` must be resolved to the exact repository and commit used. Aliases are not adequate provenance.

## Embedding contract to lock

The pilot must produce a signed machine-readable record containing:

| Item | Required value |
|---|---|
| Checkpoint repository | Exact namespace/name |
| Checkpoint revision | Immutable commit SHA |
| Weight file | Name, byte size and SHA-256 |
| Tokenizer revision | Immutable commit SHA and tokenizer checksums |
| MAMMAL package | Version and source commit |
| Prompt | Exact byte-for-byte molecular prompt template |
| Structure string | Standardised isomeric SMILES field |
| Maximum sequence length | Integer |
| Overlength rule | reject, truncate, or another fixed rule |
| Hidden state | Exact encoder layer/output tensor |
| Pooling | Exact mask-aware operation |
| Special-token handling | Which positions are included/excluded |
| Embedding dimension | Integer |
| Numeric dtype | Input and stored output dtype |
| Device | CPU/GPU model and driver information |
| Batch size | Fixed or deterministic selection rule |
| Tolerance | Absolute/relative repeatability threshold |
| Failure codes | Exhaustive technical reason set |

No field may be described only as “default.” Defaults can change between revisions.

## Label-blind pilot set

Twenty molecules will be chosen using chemistry and technical characteristics only. DILI labels must be hidden from the pilot operator. The set should include:

- ordinary neutral drug-like molecules;
- salt-source examples after parent selection;
- positively and negatively charged molecules;
- stereochemical examples;
- acyclic molecules;
- fused and aromatic ring systems;
- a macrocycle;
- an unusually long valid SMILES;
- uncommon but supported elements;
- structures near the expected tokenizer length limit;
- at least one molecule that previously produced a parsing or standardisation warning.

The selection rationale and structure strings are frozen before extraction.

## Pilot procedure

1. Create a clean environment from a lock file.
2. Download the pinned checkpoint and tokenizer; calculate checksums.
3. Verify that all 20 standardised SMILES parse in the conventional chemistry pipeline.
4. Tokenise each exact prompt and record token count, special-token layout, and truncation status.
5. Extract a vector for each molecule with the proposed layer and pooling rule.
6. Repeat extraction in a fresh process using identical settings.
7. Repeat with a different batch order to detect batch-dependent behaviour.
8. Compare vector shape, finiteness, norm, and element-wise difference.
9. Record wall time, peak CPU/GPU memory, storage per molecule, warnings, and failures.
10. Estimate full-cohort runtime and storage with a safety margin.

If CPU and GPU paths are both available, compare a small fixed subset and document expected numeric differences. The production device is then locked.

## Acceptance gate

Proceed to full extraction only if:

- at least 18 of 20 molecules produce valid finite vectors;
- every successful molecule has the expected fixed dimension;
- repeated vectors meet the locked numerical tolerance;
- batch reordering does not change outputs beyond tolerance;
- all truncation is visible and governed by the locked rule;
- estimated full-cohort time and memory are feasible;
- no labels or model-performance results were used to select the representation.

## One correction cycle

If the gate fails, one technical correction cycle may address a demonstrable implementation issue such as incorrect prompt syntax, mask-aware pooling, unsupported dtype, or package mismatch. The failure, diagnosis, change, and rerun must be recorded.

The correction cannot choose a layer or pooling rule because it produces better DILI performance; outcomes remain hidden.

## Persistent failure

If the second attempt fails, the study reports that the pre-specified frozen-embedding comparison was infeasible in the available environment. It must not silently:

- drop a large set of inconvenient molecules;
- switch to a fine-tuned task head;
- substitute a different checkpoint;
- average multiple representations after seeing labels;
- change the primary question into a post hoc model search.

Any future alternative becomes a separately labelled protocol amendment or follow-up study.

## Full-cohort extraction controls

- Cache embeddings by `SHA256(checkpoint revision + tokenizer revision + prompt bytes + SMILES + layer + pooling rule)`.
- Store vectors in a non-lossy format with row identifiers and schema metadata.
- Never use outcome labels in the embedding-generation process.
- Recompute a fixed 5% verification sample in a clean process.
- Report success rate and failure rate overall and by outcome only after cohort lock.
- Compare included versus embedding-failed molecules on available non-outcome characteristics and later disclose outcome distribution.
- Keep raw token counts and truncation flags; do not store only the final vector.

## Robustness check for SMILES representation

The primary input is one locked canonical/isomeric SMILES per drug. A secondary check generates valid randomised SMILES for a subset and measures embedding similarity and prediction stability. This tests sensitivity to equivalent text representations; it does not redefine the primary model or permit averaging randomised embeddings unless separately pre-specified.

