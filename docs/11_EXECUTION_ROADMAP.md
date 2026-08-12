# Execution Roadmap

## Phase gates

The project progresses through evidence gates, not just calendar dates.

| Gate | Required evidence | May proceed to |
|---|---|---|
| G0 Governance | Guide/advisers confirmed; written IEC determination | Technical pilot |
| G1 Protocol | Protocol, estimand, thresholds, curation and analysis choices signed | Label-blind pilot |
| G2 MAMMAL feasibility | At least 18/20 repeatable vectors and feasible resource estimate | Full data curation/extraction |
| G3 Cohort lock | Eligible/excluded lists, duplicates, scaffold groups and QC signed | Outcome modelling |
| G4 Prediction lock | Complete OOF predictions, no unresolved convergence/leakage defects | Statistical reporting |
| G5 Results lock | Tables, figures, sensitivity analyses and deviations reproduced | Final report/submission |

## Immediate next actions: first two weeks

1. Confirm current KUHS call, eligibility, deadline, portal fields, anonymity rule, and attachment limits.
2. Confirm guide's regular full-time status, KUHS FEP ID, institution, and one-student availability.
3. Name the computational reviewer and biostatistical adviser.
4. Submit the exact protocol for a written IEC determination.
5. Review and sign the open items in the protocol-lock checklist.
6. Create the repository skeleton and environment smoke tests.
7. Acquire the DILIrank source file and record its provenance without beginning outcome modelling.
8. Select the 20 pilot molecules by technical characteristics with labels hidden.

## Six-month plan

### Month 1 — Governance, protocol, and feasibility

**Work**

- Obtain IEC determination.
- Reconcile KUHS submission format and prepare the word-limited protocol.
- Finalise data form, curation codebook, and statistical choices.
- Pin MAMMAL code/model/tokenizer revisions.
- Run the label-blind 20-molecule pilot.

**Milestone**

G0–G2 passed, or MAMMAL infeasibility documented.

**Do not do**

Do not inspect AUROC or tune the representation against DILI labels.

### Month 2 — Acquisition and structure curation

**Work**

- Retrieve and checksum sources.
- Resolve DILIrank records to structures.
- Standardise parents and stereochemistry.
- Resolve duplicates and exclusion reasons.
- Conduct second-review checks.
- Generate and inspect scaffold groups without model performance.

**Milestone**

Eligible cohort, exclusions, and scaffold assignments locked.

### Month 3 — Feature generation

**Work**

- Generate descriptors and chirality-aware Morgan fingerprints.
- Generate frozen MAMMAL embeddings.
- Validate dimensions, finite values, norms, token lengths, truncation, and coverage.
- Recompute the verification sample.
- Freeze feature manifest.

**Milestone**

Audited predictor matrices and feature contract complete.

### Month 4 — Nested validation

**Work**

- Generate fixed outer and inner scaffold folds.
- Run Models A–D with the locked pipeline.
- Complete update-cohort transport analysis.
- Produce long-form out-of-fold prediction artefact.
- Run leakage and convergence checks.

**Milestone**

G4 passed; predictions frozen before result narration.

### Month 5 — Estimation and error analysis

**Work**

- Calculate paired `ΔAUROC` and scaffold-clustered intervals.
- Calculate calibration and classification measures.
- Run pre-specified sensitivity analyses.
- Complete `vMost` false-negative review.
- Complete oral-dose subset if linkage coverage is adequate.

**Milestone**

Reproducible tables and figures reviewed by the statistical and pharmacology advisers.

### Month 6 — Interpretation and dissemination

**Work**

- Interpret against 0 and the practical-gain benchmark.
- Complete TRIPOD+AI mapping.
- Write final KUHS report with separate required sections.
- Run plagiarism/integrity, anonymity, reference, and PDF checks.
- Create public reproducibility archive subject to approval/licences.
- Prepare oral/poster presentation.

**Milestone**

G5 passed; final report and archive submitted.

## Roles by workstream

| Workstream | Lead | Mandatory reviewer |
|---|---|---|
| Clinical rationale and claims | Student + faculty guide | Pharmacology/toxicology reviewer |
| Identity and structure curation | Student | Computational + pharmacology reviewer |
| MAMMAL extraction | Computational reviewer/student | Independent code reviewer |
| Fold and model pipeline | Student/computational reviewer | Biostatistical adviser |
| Statistical estimands and CI | Biostatistical adviser/student | Faculty guide |
| KUHS and ethics package | Student/faculty guide | Institutional research office/IEC |

## Budget envelope

| Resource | Planned INR |
|---|---:|
| Public datasets and open-source software | 0 |
| Institutional/collaborator compute | 0 |
| Contingency cloud GPU | 4,000 |
| Printing/report preparation | 1,000 |
| Storage/backup | 500 |
| **Maximum planned** | **5,500** |

Confirm cloud terms, institutional reimbursement, and whether the award permits these expenses before purchase.

## Weekly operating rhythm

- Monday: review gate status and blockers.
- During work: record decisions immediately in audit logs.
- Friday: freeze a read-only status snapshot with counts, failures, and next actions.
- At each phase end: reviewer sign-off and configuration tag.
- After protocol lock: every change is classified as clarification, amendment, or deviation.

## Critical path

The critical path is:

`IEC determination → protocol lock → MAMMAL pilot → cohort lock → feature lock → nested validation → results lock → KUHS report`

Writing, reference verification, and repository setup can proceed in parallel with waiting for IEC, but the pilot and analysis cannot.

