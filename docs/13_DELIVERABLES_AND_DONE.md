# Deliverables and Definition of Done

## Administrative deliverables

| Deliverable | Acceptance criteria |
|---|---|
| Current KUHS requirements record | Call date, deadline, eligibility, format, anonymity and upload limits captured from live source |
| Guide confirmation | Full-time status, FEP ID, institution and one-student availability confirmed |
| IEC determination | Written, project-specific, exact title/student/guide/status included as required |
| Application Attestation Form | Current template, complete, signed, stamped and within upload limit |
| Plagiarism certificate | Institution-issued and below the current KUHS threshold |

Administrative documents containing personal data remain outside the public repository.

## Protocol deliverables

- Signed master protocol.
- Word-limited anonymised KUHS protocol.
- Decision record.
- Statistical analysis plan.
- Data/curation codebook.
- MAMMAL embedding contract.
- Protocol-lock checklist.
- Any amendments and deviations.

**Done when:** all primary choices are explicit, internally consistent, approved, and timestamped before performance inspection.

## Data deliverables

- Raw-source provenance manifest and checksums.
- DILIrank-to-chemical identity crosswalk.
- Original and standardised structure table.
- Inclusion/exclusion table with reason codes.
- Duplicate and conflict report.
- Eligible cohort and release-membership table.
- Descriptor/fingerprint/embedding feature manifests.
- Scaffold groups and fold assignments.
- Dose-subset linkage table, if completed.

**Done when:** every modelled row traces to source evidence and every omitted row has a documented reason.

## Software deliverables

- Versioned install/lock files.
- Source acquisition and validation scripts.
- Structure curation pipeline.
- Descriptor and Morgan generation pipeline.
- MAMMAL extraction pipeline and pilot tests.
- Scaffold/fold generator.
- Nested modelling pipeline.
- Statistical/report generation pipeline.
- Unit, integration, determinism and leakage tests.
- Reproduction instructions from a clean environment.

**Done when:** a clean rerun recreates key artefacts within stated numerical tolerance and no primary result depends on manual notebook state.

## Analysis deliverables

- Long-form out-of-fold prediction table.
- Model A–D performance table.
- Paired D-versus-B `ΔAUROC` and 95% confidence interval.
- Primary effect figure with 0 and 0.03 references.
- ROC, precision-recall, calibration and repeat-stability plots.
- Thresholded performance table.
- `vMost` false-negative review.
- `vMost` versus `vNo` sensitivity analysis.
- Update-cohort transport analysis.
- Random-split robustness analysis.
- Dose/Rule-of-Two analysis if coverage meets the locked requirement.
- Failure, exclusion and deviation summaries.

**Done when:** all numbers regenerate from the frozen prediction artefact, pass independent review, and use the pre-specified interpretation rules.

## Reporting deliverables

- KUHS final report in required separate sections.
- TRIPOD+AI applicability checklist.
- Plain-language summary.
- Presentation/poster deck.
- Manuscript-ready tables and figures.
- Public reproducibility archive, subject to licence and institutional approval.

**Done when:** claims match the study scope, references are verified, personal identifiers are absent from scientific uploads, and the archive includes negative/failed findings.

## Global definition of done

The project is complete only if:

- [ ] The ethics and institutional pathway is documented.
- [ ] The protocol was locked before results.
- [ ] No unresolved critical curation conflict remains.
- [ ] Pilot success or infeasibility is transparently documented.
- [ ] All primary models use identical eligible drugs and folds.
- [ ] No known leakage defect remains.
- [ ] Primary effect and uncertainty are reported.
- [ ] Practical importance is interpreted separately from statistical superiority.
- [ ] Calibration and important errors accompany discrimination.
- [ ] Limitations and deviations are visible, not buried.
- [ ] Drug-level claims are not turned into patient-level claims.
- [ ] A second person can reproduce the result from the instructions.
- [ ] KUHS formatting, anonymity, integrity and attachment checks pass.

