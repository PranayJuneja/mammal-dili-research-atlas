# Environment separation

- `.venv-chem` contains RDKit, curation, modelling, and reporting dependencies.
- `.venv-mammal` contains the pinned MAMMAL code path, PyTorch, tokenizer stack, and model cache.
- The environments are intentionally separate because the MAMMAL dependency graph is much larger and hardware-sensitive.

Generated virtual environments and downloaded model weights are local-only and ignored by Git.
