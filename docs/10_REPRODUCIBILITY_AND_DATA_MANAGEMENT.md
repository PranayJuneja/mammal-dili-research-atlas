# Reproducibility and Data Management Plan

## Reproducibility target

An independent researcher with lawful access to the public sources should be able to reconstruct the eligible cohort, regenerate every feature, reproduce all fold assignments, rerun every model, and obtain the reported tables within documented numerical tolerance.

Reproducibility does not require redistributing third-party files when their terms prohibit it. In that case, provide retrieval instructions, checksums, and transformation code.

## Provenance manifest

Every external artefact must have:

- source name and canonical URL;
- retrieval timestamp in UTC;
- licence or terms URL;
- original filename;
- byte size;
- SHA-256 checksum;
- repository/database revision when available;
- person or automated step responsible for retrieval.

The manifest itself is version controlled. Raw files are read-only after acquisition.

## Environment capture

Maintain separate locked environments if chemistry/modelling and MAMMAL cannot coexist cleanly.

Capture:

- operating system and architecture;
- Python version;
- exact package versions and hashes;
- RDKit build;
- PyTorch, CUDA, cuDNN, driver, and GPU model;
- MAMMAL code commit;
- checkpoint and tokenizer commits/checksums;
- CPU model and memory where timing is reported;
- deterministic environment variables and seeds.

The final archive includes human-readable setup instructions and a machine-readable lock file.

## Randomness

Use a central seed registry rather than scattered literal seeds. Record separate seeds for:

- quality-control sample selection;
- scaffold fold construction by repeat;
- inner fold construction;
- classifier components that use randomness;
- bootstrap resampling;
- randomised-SMILES robustness checks;
- simulation-based precision analysis.

Seeds support replay; they do not remove all hardware-level nondeterminism.

## Configuration over notebook state

All primary parameters belong in versioned configuration files:

- source versions;
- curation rules;
- descriptor list;
- fingerprint settings;
- MAMMAL embedding contract;
- eligibility codes;
- scaffold and acyclic clustering rules;
- fold/repeat count;
- regularisation grid;
- thresholds;
- metrics and bootstrap settings.

Notebooks may explore and present data, but they must call tested library code and read stored artefacts. The definitive pipeline cannot depend on cells run in an undocumented order.

## Data contracts and validation

Each pipeline stage validates its input and output schema. Minimum automated assertions include:

- unique local drug identifier;
- allowed outcome values;
- one eligibility decision per source record;
- no missing standardised structure in eligible rows;
- no duplicate parent across analysis units;
- fixed descriptor and embedding dimensions;
- finite numeric values;
- no scaffold group split within an outer fold;
- exactly one outer-test prediction per drug/model/repeat;
- identical drug keys for B and D comparisons;
- probabilities within `[0,1]`;
- fixed configuration and code hashes attached to outputs.

## Test strategy

### Unit tests

- parsing and parent selection examples;
- exclusion-code assignment;
- descriptor and fingerprint determinism;
- scaffold and acyclic group creation;
- mask-aware embedding pooling;
- metric calculation on known toy data;
- paired bootstrap retaining whole groups.

### Integration tests

- raw record through curated molecule;
- curated molecule through all three feature blocks;
- small synthetic nested-CV run with no leakage;
- environment recreation and cached-embedding validation.

### Leakage tests

- intentionally duplicated structures must land in one group;
- fitted scaler statistics must differ when training data differ;
- shuffled outer-test outcomes must not affect trained pipelines;
- test-only extreme values must not alter training preprocessing;
- update cohort must not appear in development fit objects.

## Artefact versioning

Name every major release with a protocol and data version, for example:

- `protocol-v1.0`
- `cohort-v1.0`
- `features-v1.0`
- `analysis-v1.0`

Record the Git commit, config hash, input manifest hash, and output checksum for each. Do not use mutable names such as `final_final.csv`.

## Audit logs

Separate human decisions from automated transformations.

Human decision log fields:

- record ID;
- issue;
- evidence reviewed;
- initial decision and reviewer;
- second review;
- adjudicated decision;
- timestamp;
- applicable protocol rule.

Automated logs should contain run ID, code commit, configuration hash, start/end time, warnings, errors, counts, and output locations without exposing credentials.

## Backup and access

- Maintain at least two copies of irreplaceable audit/ethics records on institution-approved storage.
- Keep secrets and identifiable administrative files outside Git.
- Limit write access to authorised investigators.
- Test restoration before Month 3.
- Never commit access tokens, private keys, cloud credentials, or signed institutional documents.

## Public archive contents

Subject to source licences and institutional approval:

- protocol and amendments;
- data dictionary and curation rules;
- source retrieval script/manifest;
- eligible/excluded identifiers permitted for sharing;
- feature-generation and modelling code;
- environment files;
- fold assignments;
- out-of-fold predictions if redistribution is permitted;
- results and figures;
- machine-readable reporting checklist;
- README with a clean-room reproduction path.

The archive must include known deviations, failed embeddings, and negative results, not only the successful path.

