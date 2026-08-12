# Data and Curation Specification

## Purpose

The largest avoidable threat to this study is not the classifier. It is attaching the wrong structure to a drug, treating a salt as a different active molecule, leaking duplicate parents across folds, or excluding failures without an audit trail. This specification defines how the analysis cohort will be built before model performance is inspected.

## Data layers

Data must move through immutable, traceable layers:

1. **Raw source layer:** exact downloaded files, unchanged.
2. **Identity-resolution layer:** DILIrank record linked to chemical identifiers and evidence.
3. **Curated-structure layer:** standardised parent representation plus decisions and warnings.
4. **Eligibility layer:** one row per analysis unit, outcome retained but inaccessible to technical pilot work.
5. **Feature layer:** descriptors, Morgan bits, MAMMAL vector metadata, and feature checksums.
6. **Analysis layer:** locked cohort, scaffold assignment, fold assignment, and out-of-fold predictions.

Never overwrite one layer with another. Every derived row must retain the source record identifier.

## Required source records

### DILIrank 2.0

Record at minimum:

- LTKB identifier;
- compound name exactly as published;
- DILI concern category;
- severity class and label section when provided;
- whether the record belonged to the original list or the 300-drug update;
- source URL, download timestamp, file name, byte size, and SHA-256 checksum.

The FDA page asks downloaders to notify its support contact. Whether this is a request or licence condition must be checked and documented at acquisition.

### Chemical identity sources

PubChem is the primary structure source. Additional authoritative sources may resolve conflicts, but the hierarchy must be fixed before full curation. For each source capture:

- source database and record URL;
- source-specific identifier;
- preferred name and synonyms used for matching;
- original isomeric and canonical SMILES when available;
- InChI and InChIKey;
- molecular formula;
- access date and record version or last-updated date if exposed.

### Dose source for exploratory analysis

Dose is not required for primary eligibility. For the oral-drug subset, capture source, indication/regimen, amount, unit, frequency, route, selected harmonised daily amount, and the rule used when several therapeutic regimens exist. Never infer milligrams from a value with an unresolved unit.

## Minimum data dictionary

| Field | Type | Meaning |
|---|---|---|
| `dilirank_id` | string | Stable FDA/LTKB record identifier |
| `compound_name_source` | string | Name in DILIrank 2.0 |
| `dili_category` | category | `vMost`, `vLess`, `vNo`, or `Ambiguous` |
| `release_group` | category | original or added-in-2.0 |
| `pubchem_cid` | nullable string | Selected PubChem compound identifier |
| `identity_status` | category | resolved, disputed, unresolved |
| `original_smiles` | string | Structure before local standardisation |
| `standardised_isomeric_smiles` | string | Locked model input structure |
| `parent_inchikey` | string | Duplicate-detection key after parent selection |
| `curation_flags` | list | Salt, charge, tautomer, stereochemistry and other warnings |
| `eligibility` | boolean | Final eligibility status |
| `exclusion_code` | nullable category | One primary reason for exclusion |
| `scaffold_id` | string | Locked validation group |
| `review_status` | category | single review, second checked, adjudicated |
| `source_provenance` | object | URLs, dates, revisions and checksums |

Feature tables should join to this table by a stable local `drug_id`, never by a human-readable name.

## Identity-resolution procedure

For each non-ambiguous DILIrank record:

1. Search the exact name in the primary chemical source.
2. Compare synonyms, formula, known active moiety, and available identifiers.
3. Determine whether the DILIrank entry describes a parent active, a salt, a combination, or a special formulation.
4. Store every candidate considered and the reason for selection or rejection.
5. Mark unresolved conflicts for reviewer adjudication; do not choose the first search result silently.

Name matching alone is insufficient. The selected structure must be chemically and pharmacologically consistent with the labelled active drug.

## Structure-standardisation contract

The exact RDKit or other chemistry-toolkit version and function sequence will be locked before full curation. The intended order is:

1. Parse the source structure and record parsing warnings.
2. Separate disconnected components.
3. Select the parent active component under a documented largest-organic-fragment rule with explicit exceptions.
4. Apply the locked charge/normalisation rules.
5. Preserve supported stereochemistry.
6. Generate a standardised isomeric SMILES.
7. Generate InChIKey, formula, and exact/standard molecular checks for audit.
8. Detect duplicate parents.
9. Generate descriptors, fingerprint, and the exact SMILES passed to MAMMAL from this same object.

### Salts and counterions

Counterions are normally removed so that different salt formulations of the same active moiety do not become separate molecules. Exceptions must be adjudicated if removing a component changes the pharmacologically meaningful active entity.

### Stereochemistry

Retain stereochemistry when the drug identity specifies it and the source supports it. If stereochemistry is missing or disputed, flag the record. Do not invent an isomer. The Morgan fingerprint uses chirality; the primary MAMMAL input uses the same standardised isomeric representation.

### Tautomers and protonation

Do not perform aggressive tautomer canonicalisation or pH-dependent protonation without a pre-specified rule and chemical review. Such transformations can alter both fingerprints and language-model token sequences.

### Mixtures and combination products

Fixed-dose combinations and unresolved mixtures do not provide one defensible molecular input and are excluded unless DILIrank clearly supplies separable records for individual active components.

### Duplicate parents

After standardisation, identical parent structures cannot be allowed to appear in different validation folds. The default analysis unit is one standardised parent per active drug. When multiple DILIrank records collapse to one parent:

- retain the mapping table;
- inspect whether labels agree;
- if labels agree, apply the locked representative-record rule;
- if labels conflict, exclude from the primary analysis and report the conflict unless the scientific advisers approve a different pre-outcome rule.

## Exclusion codes

Use one primary code and optional secondary flags:

- `AMBIGUOUS_OUTCOME`
- `BIOLOGIC_OR_MACROMOLECULE`
- `MIXTURE_OR_COMBINATION`
- `POLYMER_OR_UNRESOLVED_INORGANIC`
- `IDENTITY_UNRESOLVED`
- `STRUCTURE_UNAVAILABLE`
- `STRUCTURE_PARSE_FAILURE`
- `DUPLICATE_PARENT`
- `DUPLICATE_LABEL_CONFLICT`
- `MAMMAL_UNPROCESSABLE`
- `OTHER_PREDEFINED`

Free-text “other” exclusions require reviewer approval and must not become an outcome-guided escape hatch.

## Quality control

- A second reviewer checks all exclusions, all conflicts, and a random sample of at least 10% of uncomplicated inclusions.
- The sample seed and selected rows are recorded.
- Reviewers see identity and chemistry information; outcome blinding should be used where feasible during technical decisions.
- Disagreements are resolved by the faculty guide or named pharmacology/computational adjudicator.
- Before feature generation, produce a cohort report showing counts by outcome, exclusion reason, release group, structure-warning category, and scaffold size.

## Cohort-lock outputs

The data stage is complete only when the following exist:

- immutable raw-source manifest;
- identity crosswalk;
- structure-curation audit table;
- eligible and excluded drug lists;
- duplicate-resolution report;
- class and release counts;
- scaffold assignments and scaffold-size distribution;
- machine-readable data dictionary;
- signed cohort-lock record stating that model performance has not been inspected.

