# Protocol-Lock Checklist

No outcome performance may be inspected until every blocking item is resolved. Use initials, date, and a link to the decision evidence.

## Governance blockers

| ID | Decision/evidence required | Owner | Status |
|---|---|---|---|
| G-01 | Current KUHS call, deadline, eligibility and portal rules captured | Student | Open |
| G-02 | Guide eligibility, FEP ID, institution and one-student rule confirmed | Guide | Open |
| G-03 | Computational and pharmacology reviewers named | Guide | Open |
| G-04 | Biostatistical adviser accepts analysis responsibility | Guide | Open |
| G-05 | Written project-specific IEC determination obtained | Student/guide | Open |
| G-06 | Exact title aligned across KUHS and IEC documents | Student | Open |

## Scientific blockers

| ID | Decision/evidence required | Proposed choice | Status |
|---|---|---|---|
| S-01 | Primary outcome | `vMost/vLess` versus `vNo` | Proposed |
| S-02 | Primary comparator | Model D versus Model B | Proposed |
| S-03 | Practical-gain threshold and rationale | `ΔAUROC = 0.03` | Needs adviser sign-off |
| S-04 | Number of repeated outer CV runs | 5 | Needs precision check |
| S-05 | Primary class weighting | None | Needs adviser sign-off |
| S-06 | Primary dimension reduction | None | Pilot-dependent |
| S-07 | Primary classification threshold | Training-fold Youden | Needs adviser sign-off |
| S-08 | Sensitivity-prioritised threshold | Target sensitivity ≥80% if feasible | Needs adviser sign-off |
| S-09 | Primary CI algorithm | 2,000 scaffold-group percentile bootstraps over mean repeat Δ | Needs simulation/sign-off |
| S-10 | Missing descriptor handling | Training-fold median | Needs confirmation after audit |
| S-11 | Optional gradient boosting | Exclude from primary; secondary only if locked | Open |

## Chemistry and data blockers

| ID | Decision/evidence required | Proposed choice | Status |
|---|---|---|---|
| D-01 | DILIrank file revision and checksum | Acquire current 2.0 list | Open |
| D-02 | Structure source hierarchy | PubChem primary | Open |
| D-03 | Parent/salt standardisation code sequence | Defined in curation spec | Needs code review |
| D-04 | Stereochemistry policy | Retain supported stereochemistry | Proposed |
| D-05 | Tautomer/protonation policy | No aggressive transformation | Proposed |
| D-06 | Duplicate parent representative rule | Retain one; conflict exclusion | Needs review |
| D-07 | Murcko implementation/version | Version-pinned RDKit | Open |
| D-08 | Acyclic clustering method | Morgan/Tanimoto/Butina | Proposed |
| D-09 | Acyclic similarity threshold | 0.50 | Needs outcome-blind assessment |
| D-10 | Secondary-review fraction | All conflicts/exclusions + 10% routine | Proposed |
| D-11 | Embedding coverage stop rule | <90% otherwise eligible stops/review | Needs adviser sign-off |
| D-12 | Dose source, route and multiple-regimen rules | Version-locked source | Open |

## MAMMAL blockers

| ID | Decision/evidence required | Status |
|---|---|---|
| M-01 | Exact checkpoint namespace and immutable revision | Open |
| M-02 | Weight and tokenizer checksums | Open |
| M-03 | Package commit and environment lock | Open |
| M-04 | Exact small-molecule prompt | Open |
| M-05 | Exact hidden layer/output tensor | Open |
| M-06 | Mask-aware pooling rule | Open |
| M-07 | Sequence limit and overlength rule | Open |
| M-08 | Dtype, device, batch size and deterministic settings | Open |
| M-09 | Vector repeatability tolerance | Open |
| M-10 | Twenty pilot structures and label-blinding record | Open |
| M-11 | Pilot pass/fail report | Open |

## Reproducibility blockers

- [ ] Repository code/data boundary approved.
- [ ] Raw source and model licences reviewed.
- [ ] Environment can be recreated from scratch.
- [ ] Configuration files contain all primary parameters.
- [ ] Seed registry created.
- [ ] Unit and leakage tests pass.
- [ ] Data schemas and reason codes frozen.
- [ ] Reviewer can reproduce pilot vectors.
- [ ] Outcome access is technically or procedurally restricted during pilot.

## Lock declaration template

> We confirm that protocol version **[version]**, commit **[hash]**, data-curation rules **[version]**, MAMMAL embedding contract **[version]**, fold procedure **[version]**, and statistical analysis plan **[version]** were approved on **[date/time]** before any primary or secondary model performance was inspected. Known unresolved items: **[none/list]**.

| Role | Name | Signature/initials | Date |
|---|---|---|---|
| Student investigator | | | |
| Faculty guide | | | |
| Computational reviewer | | | |
| Pharmacology/toxicology reviewer | | | |
| Biostatistical adviser | | | |

