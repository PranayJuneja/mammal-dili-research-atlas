# G2 pilot technical correction 01

Date: 2026-08-13 (Asia/Calcutta)

## Failure

The first accepted pilot launch loaded the pinned model snapshot, then failed before tokenisation because `ModularTokenizerOp.from_pretrained` was given the checkpoint root. The tokenizer package looked for `config.yaml` at the root, while the pinned repository stores it at `tokenizer/config.yaml`.

No molecule was tokenised, no embedding was produced, and no DILI outcome or model-performance result was inspected.

## Correction

Pass the checkpoint's immutable `tokenizer/` directory to `ModularTokenizerOp.from_pretrained`. Checkpoint revision, tokenizer files, prompt bytes, hidden state, mask-aware pooling, dtype, device, batch size, tolerance and pilot molecules are unchanged.

The first correction invocation also revealed that `snapshot_download` returns a string in this installed `huggingface_hub` version. The snapshot return value is now converted to `Path` before joining `tokenizer/`. This second exception also occurred before tokenisation or vector production and is part of the same path-type correction, not a representation change.

This is the single implementation correction cycle allowed by `docs/05_MAMMAL_FEASIBILITY_PLAN.md`.
