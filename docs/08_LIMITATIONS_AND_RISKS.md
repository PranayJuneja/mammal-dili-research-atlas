# Limitations and Risk Register

## How to read this document

Some risks can be prevented, some can only be measured and disclosed, and some are fundamental limits on interpretation. A safeguard lowers risk; it does not make the limitation disappear.

## Fundamental scientific limitations

### 1. Drug-level concern is not patient-level DILI

DILIrank assigns concern to drugs from labels and literature. It does not contain a patient's dose, genetics, comorbidities, co-medications, immune state, timing, or adjudicated clinical course.

**Consequence:** The model cannot estimate an individual's risk, identify causality in a case, or guide prescribing.

**Handling:** Use “DILI concern classification” throughout. Keep patient-risk claims explicitly out of scope.

### 2. DILIrank labels are curated evidence, not perfect truth

Concern categories reflect available regulatory and published evidence. Older, widely used drugs may have more opportunity for an association to be recognised. `vNo` can reflect absence of established evidence rather than biological impossibility.

**Consequence:** The model learns the dataset's concern construct, which may include ascertainment and labelling patterns.

**Handling:** Report approval era/release group, update-cohort results, and careful label language. Do not call `vNo` “safe.”

### 3. Structure alone omits major causal factors

Dose, route, exposure, reactive metabolism, immune effects, and host susceptibility matter. A molecule-only model cannot represent all of them.

**Handling:** Keep the primary question explicitly molecular. Add a limited oral-dose analysis without promoting it to patient prediction.

### 4. MAMMAL pretraining overlap is unknowable in full

The model was trained on more than two billion biological samples. Study molecules or related structures may have appeared during pretraining.

**Consequence:** Neither scaffold splitting nor the DILIrank update cohort proves that the representation is free from pretraining familiarity.

**Handling:** Avoid “unseen molecule” claims. Treat scaffold evaluation as protection against downstream train/test analogue leakage, not pretraining contamination.

### 5. One embedding recipe is not the whole model family

Layer, pooling, prompt, tokenizer, and sequence rules define the tested representation.

**Consequence:** A null result means this frozen representation did not add sufficient value under this classifier and dataset. It does not prove that fine-tuning, another layer, another prompt, or another foundation model cannot help.

## Methodological risks

| Risk | Likelihood | Impact | Control | Residual limitation |
|---|---|---|---|---|
| Close analogues leak across folds | High without control | High | Scaffold-grouped outer and inner folds | Scaffold definitions are imperfect measures of similarity |
| Exact duplicate parents receive different records | Medium | High | Parent standardisation and duplicate adjudication | Salt/tautomer decisions can be debatable |
| Preprocessing sees test data | Medium | High | Fold-contained pipelines | Implementation must be tested, not merely described |
| Hyperparameter tuning overfits | Medium | Medium-high | Nested validation and small fixed grid | Small inner folds can still be noisy |
| High-dimensional features destabilise regression | Medium | Medium-high | L2 regularisation, convergence checks, optional pre-locked reduction | Eligible sample remains modest |
| Repeated CV treated as independent samples | Medium | Medium | Repeat-aware, scaffold-clustered interval | CI method needs simulation validation |
| Threshold optimised on test outcomes | Medium | High | Select threshold inside training only | Thresholds may vary between folds |
| Outcome-guided engineering | Medium | High | Label-blind pilot and protocol lock | Blinding process must be credible and auditable |
| Extensive secondary analyses create false discoveries | Medium | Medium | One primary comparison; label others exploratory | Readers may still overfocus on best subgroup |

## Data and curation risks

| Risk | Detection | Response |
|---|---|---|
| Drug name maps to wrong PubChem record | Formula, synonym and InChIKey mismatch | Reviewer adjudication or exclusion |
| Salt stripping removes meaningful active entity | Component and pharmacology review | Documented exception or exclusion |
| Stereochemistry missing or inconsistent | Isomeric source comparison | Flag; never invent stereochemistry |
| Duplicate labels conflict after parent collapse | Parent InChIKey grouping | Exclude primary or apply pre-locked adjudication |
| Mixture represented as one arbitrary component | Disconnected-component audit | Exclude mixture/combination |
| Long SMILES truncated silently | Token-count audit | Locked explicit rule and sensitivity disclosure |
| Embedding failures differ by outcome/scaffold | Failure table after lock | Report selection pattern; do not hide failures |
| Dose link selects a non-representative subset | Coverage and inclusion comparison | Keep exploratory and disclose complete-case bias |

## Technical risks

### MAMMAL package drift

The repository and model card can change. Package dependencies include large scientific libraries and hardware-sensitive components.

**Controls:** Pin immutable revisions, lock dependencies, checksum weights/tokenizer, record driver/device, and archive the environment definition.

### Hidden-state extraction ambiguity

Official examples focus on generation and task-specific fine-tuning, not a universally defined small-molecule embedding.

**Controls:** Obtain expert review of the extraction code, unit-test mask-aware pooling, and make the label-blind feasibility gate mandatory.

### Compute availability

The model weights are approximately 1.8 GB on the public repository, but runtime memory is larger. CPU extraction may be slow; GPU software compatibility may fail.

**Controls:** Measure actual peak memory and time on 20 molecules; estimate full cost before committing; maintain a small contingency budget.

### Non-determinism

GPU kernels, mixed precision, batching, or dropout state can change vectors.

**Controls:** `eval` mode, inference/no-gradient context, fixed dtype/device, repeat-and-reorder tests, deterministic settings where supported, and numerical tolerance rather than impossible bit identity across devices.

## Operational risks

| Risk | Early warning | Mitigation |
|---|---|---|
| IEC determination delayed | No submission date or committee agenda | Submit immediately; do not start pilot without written determination |
| Guide eligibility problem | FEP ID/full-time status unconfirmed | Confirm against current KUHS call before submission |
| Guide forwards another student | Competing application exists | Obtain written guide confirmation early |
| Protocol exceeds KUHS format | Word counts or combined sections | Maintain separate KUHS submission document and automated counts |
| Plagiarism certificate delayed | No institutional workflow booked | Arrange institutional check before final submission |
| GPU unavailable | Pilot cannot run on planned device | Reserve institutional/collaborator access and contingency cloud option |
| Curation consumes timeline | High unresolved rate after first batch | Pilot 50 records, refine rules while labels remain hidden, add reviewer capacity |
| Scope expands into model shopping | Requests for many models after results | Enforce decision record and amendment process |
| Key person unavailable | No backup reviewer | Name computational and statistical backups before Month 2 |

## Stop rules

Pause or stop the relevant analysis when:

- written IEC determination has not been obtained;
- the MAMMAL pilot fails twice under the permitted correction cycle;
- fewer than 90% of otherwise structurally eligible drugs receive embeddings, unless advisers approve a transparent revised feasibility claim before outcomes;
- fold construction cannot place both outcomes in every outer fold;
- identity or duplicate conflicts remain unresolved at cohort lock;
- the effective number of independent scaffold groups makes the planned precision unattainable;
- code tests show leakage or inconsistent results;
- a required dataset or model licence does not permit the planned use or redistribution.

Stopping one component is a valid result. It is safer than changing the question after seeing outcomes.

## Claims that are never allowed

- “MAMMAL predicts which patient will develop DILI.”
- “The model is clinically validated.”
- “The update cohort is an external prospective validation.”
- “Scaffold splitting guarantees molecules were unseen in pretraining.”
- “No significant difference proves the models are equivalent.”
- “A high AUROC proves calibrated or clinically useful probabilities.”
- “The Rule of Two is useless” based on a structure-focused dataset comparison.
- “MAMMAL adds no value anywhere” based on one frozen representation.

