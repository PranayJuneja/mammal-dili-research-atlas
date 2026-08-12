# Repository Blueprint for the Implementation Phase

## Design goals

- Raw inputs remain immutable.
- Human curation decisions are explicit data, not hidden code branches.
- Every stage is runnable from the command line.
- Primary parameters live in configuration files.
- Outcome-blind pilot work is physically/logically separated from model evaluation.
- Generated artefacts are traceable but large/licensed files are not blindly committed.

## Planned layout

```text
.
├── README.md
├── docs/
├── configs/
│   ├── sources.yaml
│   ├── curation.yaml
│   ├── mammal_embedding.yaml
│   ├── features.yaml
│   ├── folds.yaml
│   └── analysis.yaml
├── data/
│   ├── raw/                 # immutable, normally Git-ignored
│   ├── interim/             # identity and curation working tables
│   ├── processed/           # locked eligible cohort
│   └── manifests/           # checksums, schemas, provenance
├── audit/
│   ├── identity_decisions/
│   ├── exclusions/
│   ├── reviews/
│   └── protocol_changes/
├── src/mammal_dili/
│   ├── acquisition/
│   ├── curation/
│   ├── chemistry/
│   ├── embeddings/
│   ├── grouping/
│   ├── modelling/
│   ├── statistics/
│   └── reporting/
├── scripts/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── leakage/
├── artifacts/
│   ├── pilot/
│   ├── cohort/
│   ├── features/
│   ├── folds/
│   ├── predictions/
│   └── results/
├── reports/
│   ├── kuhs_protocol/
│   ├── final_report/
│   └── figures/
└── environment/
    ├── chemistry/
    └── mammal/
```

Identifiable IEC/attestation documents must not live in this repository if it may become public.

## Pipeline stages

### 1. Acquire

Inputs: configured source URLs and versions.

Outputs: raw files plus provenance manifest and checksums.

Failure conditions: source unavailable, checksum mismatch, licence not recorded.

### 2. Resolve identity

Inputs: DILIrank records and chemical-source records.

Outputs: candidate mappings, selected identity, conflicts, reviewer queue.

Failure conditions: unresolved drug identity or inconsistent active moiety.

### 3. Curate structures

Inputs: selected source structures and curation config.

Outputs: standardised structure, parent keys, flags, exclusion codes, audit record.

Failure conditions: parse error, mixture, unsupported entity, unresolved duplicate conflict.

### 4. Run label-blind MAMMAL pilot

Inputs: frozen 20-molecule set and embedding config.

Outputs: vector/test report, runtime/memory estimate, embedding contract.

Failure conditions: acceptance gate not met after permitted correction.

### 5. Lock cohort and groups

Inputs: curated eligible structures.

Outputs: eligible cohort, scaffold/acyclic groups, descriptive lock report.

Failure conditions: duplicate leakage, invalid group structure, unresolved review.

### 6. Generate features

Inputs: locked structures and feature configs.

Outputs: descriptors, fingerprints, embeddings, feature manifest.

Failure conditions: dimensional mismatch, non-finite values, low embedding coverage.

### 7. Generate folds

Inputs: locked groups, outcome for balance constraints, seed registry.

Outputs: immutable outer/inner fold assignments.

Failure conditions: group split, missing class in an outer fold, non-reproducible assignments.

### 8. Train and predict

Inputs: features, folds, locked model grid.

Outputs: long-form out-of-fold predictions and fit diagnostics.

Failure conditions: leakage test failure, unresolved convergence, mismatched B/D rows.

### 9. Estimate and report

Inputs: frozen predictions and analysis config.

Outputs: estimates, confidence intervals, tables, figures, reporting checklist.

Failure conditions: headline results cannot be regenerated or do not map to the locked config.

## Command interface target

The implementation should expose commands with a shape similar to:

```powershell
python -m mammal_dili acquire --config configs/sources.yaml
python -m mammal_dili curate --config configs/curation.yaml
python -m mammal_dili pilot-mammal --config configs/mammal_embedding.yaml
python -m mammal_dili build-features --config configs/features.yaml
python -m mammal_dili build-folds --config configs/folds.yaml
python -m mammal_dili cross-validate --config configs/analysis.yaml
python -m mammal_dili report --config configs/analysis.yaml
```

The exact CLI may change during implementation; the stage boundaries and artefact contracts should not.

## Configuration rules

- Configs are declarative and schema-validated.
- Each run copies the resolved config into its artefact directory.
- Environment variables are used only for secrets or machine paths, never scientific defaults.
- Unknown configuration keys cause an error.
- Primary analysis refuses to run unless a protocol-lock marker and matching config hash exist.
- Overwriting a locked artefact requires an explicit new version, not a force flag.

## Minimum test fixtures

Create a tiny non-sensitive fixture set containing:

- parent plus salt pair;
- stereoisomer pair;
- charged molecule;
- disconnected mixture;
- duplicate parent with two names;
- ring-containing pair with same scaffold;
- acyclic similar pair;
- deliberately long SMILES;
- invalid SMILES;
- synthetic outcomes used only for pipeline tests.

These fixtures allow chemistry, grouping, leakage, and model orchestration to be tested without exposing or depending on the full research dataset.

## Implementation order

1. Schemas, configs, and provenance utilities.
2. Curation and chemistry tests.
3. Standalone MAMMAL pilot extractor.
4. Cohort/group locking.
5. Feature builders.
6. Nested cross-validation with synthetic fixtures.
7. Statistical resampling tests.
8. Report generator.
9. Full data run only after protocol lock.

