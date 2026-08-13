# Final reporting addendum

## Structured abstract

**Background:** We tested whether one prospectively frozen MAMMAL molecular embedding adds drug-level DILI concern discrimination beyond conventional physicochemical descriptors and a chirality-aware Morgan fingerprint. **Methods:** DILIrank 2.0 drugs were identity-adjudicated, split into 675 original-list development drugs (471 concern events; 204 non-events) and 134 added-drug transport records (44 events; 90 non-events), and evaluated with five repeats of nested scaffold-grouped cross-validation. The primary estimand was paired AUROC for Model D minus Model B; the interval used 2,000 whole-scaffold bootstrap resamples. **Results:** Primary delta AUROC was -0.0804 (95% CI -0.1142 to -0.0420). All three prespecified development robustness analyses were negative. The untouched update estimate was -0.0293 (95% CI -0.1093 to 0.0467), so it did not support an improvement and remained uncertain. **Conclusion:** Under this exact checkpoint, prompt, pooling rule, cohort, comparator, learner, and validation design, adding the frozen MAMMAL representation worsened development discrimination. This is a drug-level benchmark, not a patient-risk model or clinical recommendation.

## Outcome ascertainment

DILIrank 2.0 supplies regulatory/evidentiary drug-level concern categories. The public source describes its curation basis, but the locked source materials do not report predictor-aware assessor identities or whether upstream assessors were blinded to molecular predictors. Those details are therefore reported as unavailable, not silently assumed. Downstream feature generation and model development were outcome-controlled under the locked protocol.

## Governance and administrative declarations

- Ethics/governance: owner acknowledgement, faculty-guide approval, and IEC approval for PA-01, PA-02, and PA-03 were recorded on 2026-08-13; identifying private records remain outside the public repository.
- Funding: no project-specific funding or funder-role declaration was supplied in the public project record. No inference of funded or unfunded status should be made.
- Conflicts: no project-specific conflict-of-interest declaration was supplied in the public project record. This is an explicit unavailable disclosure, not a declaration of no conflicts.
- Registration: no prospective study-registration identifier was supplied in the project record.
- Patient/public involvement: none was documented for this non-person, public-drug-record benchmark.
- Availability: public report outputs, checksums, code, configuration, and audit gates are included in this repository. FDA/PubChem and model assets remain subject to their source terms; raw private governance evidence is restricted.

## Population and predictor characteristics

| Population | Drugs | Events | Non-events | Chemical groups | Descriptor missing cells | Median MW | Median logP | Median TPSA | Median HBD | Median HBA | Median rotatable bonds | Median rings | Median charge | Median fraction Csp3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Development/original list | 675 | 471 | 204 | 460 | 0 | 324.399 | 2.582 | 72.680 | 2 | 4 | 4 | 3 | 0 | 0.400 |
| Exploratory update/added drugs | 134 | 44 | 90 | 125 | 0 | 431.094 | 3.456 | 89.740 | 2 | 5 | 5 | 4 | 0 | 0.350 |

The update population is smaller, has a reversed class balance, and has higher median molecular weight, lipophilicity, polar surface area, acceptor count, rotatable-bond count, and ring count. Its estimate is therefore explicitly exploratory transport evidence.

## Analysis denominators

| Analysis | Unique drugs | Events | Non-events | Role |
|---|---:|---:|---:|---|
| Primary nested scaffold validation | 675 | 471 | 204 | Confirmatory |
| vMost versus vNo sensitivity | 382 | 178 | 204 | Prespecified robustness |
| Stratified random split | 675 | 471 | 204 | Optimistic robustness |
| Class-balanced learner | 675 | 471 | 204 | Prespecified robustness |
| Added-drug update transport | 134 | 44 | 90 | Exploratory |

The false-negative audit contains **277 model-drug rows representing 113 unique drugs**. Repeated rows reflect different models; they are not 277 distinct drugs. Empty curation-warning fields in the generated audit are rendered as `none`, and inapplicable active-moiety fields as `not applicable` in the public copy.

## Model specification and export

The benchmark intentionally has no single deployable fitted model: predictions come from repeated outer-fold fits and the estimand compares out-of-fold representations. Exporting one fitted object would misrepresent the evaluated procedure. The complete reproducible specification is the locked Python implementation, fixed feature definitions, seven-value regularisation grid, deterministic seeds, fold assignments, tuning records, prediction manifests, and protocol/G3/G4 hashes. No clinical or production model is claimed.

## Manifest clarification

`report_manifest.json` inventories the full internally generated report companion set, including large curve tables retained in the reproducible workspace. `download_manifest.json` inventories the smaller public download bundle. A file's absence from the public bundle does not mean it was absent from the internally validated report build.

