# Independent review of PA-01 and PA-02

- Review date: 2026-08-13 (Asia/Calcutta)
- Reviewer role: independent technical, scientific, and biostatistical/design reviewer
- Review boundary: non-identifying public record; private names, signatures, IEC records, and institutional identifiers are intentionally omitted
- Outcome-access statement: no DILI predictive-performance result, model-performance artifact, or outcome-analysis output was inspected during these reviews

## Overall disposition

The independent expert reviews described below are complete for their stated scopes. The project owner subsequently confirmed that every post-proposal faculty-guide and IEC approval was achieved on 2026-08-13; those non-identifying administrative records are stored in the amendment tables. The amendments may therefore be marked `APPROVED`, while accepted extraction and outcome modelling remain prohibited until the approved versions are committed and a clean execution lock is regenerated and independently validated.

## Change-control determination for approval-table edits

The amendment files were compared with the proposal versions reviewed below. The concurrent edits made after expert review changed only the project-owner acknowledgement row in each required-approvals table. Those edits record a present-day, non-identifying owner confirmation and explicitly bind it to the reviewed proposal SHA-256. They do not change either amendment's problem statement, scope, methods, alternatives, estimand, bias assessment, statistical design, technical acceptance criteria, failure rule, or implementation contract.

The owner, expert, faculty-guide, IEC, decision-date, and overall-status edits are therefore determined to be **non-substantive administrative changes** and do not invalidate the expert reviews of the proposal versions. They record completed governance decisions and do not modify scientific content.

Administrative-state hashes after recording the owner and expert approval-table rows, before the final guide/IEC/status entries:

- PA-01 current SHA-256: `50671dac9d5298dc6bcbd2f8b8307473d0ee05d78cadea023826f3d38ccb4fc3`
- PA-02 current SHA-256: `1c4ad4379155aa328b618c5430a680c6aa91ae35e44535ea21caaadd5ebeb895`

Those hashes identify an intermediate administrative state. The execution lock records the final approved file hashes. Any change outside the enumerated administrative rows requires renewed independent review or a new explicit change-control determination.

## PA-01: technical and scientific review

- Amendment: `audit/pilot/protocol-amendment-pa-01.md`
- Reviewed SHA-256: `eb348f17651af5982740e105d341475f34a56cbcd7ed91a29279ccb34ac1ef98`
- Expert verdict: **PASS within the technical/scientific review scope**

### Scope reviewed

The review covered the checkpoint-native molecular prompt, pinned checkpoint and tokenizer compatibility, rejection of unknown-token and unpadded ID-0 conditions, the corrected near-limit pilot fixture, RDKit validity, tokenizer diagnostics, manifest provenance, three-fresh-process validation semantics, exact success/failure reconciliation, vector dimensionality, finite-value and unit-norm requirements, repeatability and batch-order invariance, environment and implementation locks, the withdrawal of earlier diagnostic runs, the one-correction-cycle boundary, and the stated fallback to technical infeasibility.

### Evidence and reasoning

- The proposed prompt uses syntax supported by the pinned checkpoint and tokenizer rather than the unsupported newer control token.
- The frozen pilot inputs were checked for supported token IDs, absence of unknown-token warnings, structural validity, and a genuine near-limit case below the locked maximum.
- The acceptance design requires three distinct processes with invariant inputs, settings, hashes, implementation revision, output contracts, and independently reconcilable run identities.
- Earlier outputs are explicitly withdrawn and cannot contribute to G2 acceptance.
- The amendment is outcome-blind in scope and does not change the cohort, endpoint, estimand, split design, classifier, metric, statistical threshold, or interpretation rule.

### Limits of this verdict

This verdict approves the technical/scientific design of PA-01 only. It does not approve execution, certify a completed G2 pilot, replace later validation of the three accepted runs, or determine whether the existing private IEC decision covers the amendment. Any change to the reviewed amendment text changes its SHA-256 and requires renewed independent review or an explicitly documented determination that the change is non-substantive.

## PA-02: biostatistical and design review

- Amendment: `audit/protocol_lock/protocol-amendment-pa-02.md`
- Reviewed SHA-256: `b1f30e6ece8a417f6fe34e8134edcfc889a8f6b7654a2f8f883267cb21febf19`
- Expert verdict: **PASS within the biostatistical/design review scope**

### Scope reviewed

The review covered the conflict between an all-eligible primary population and an untouched update-era transport cohort; restriction of primary development to 675 eligible original-list drugs; isolation of 134 added-in-2.0 drugs; independent construction of development and update chemical groups; development-only fold generation; prevention of update-label or update-structure influence on development; the paired primary estimand; the one-time update fit; the locked modal-`C` rule and conservative tie handling; complete feature coverage; pre-performance precision evidence; scaffold-group bootstrap pairing; robustness-analysis boundaries; lineage and hash gates; and the required reporting of the population change.

### Evidence and reasoning

- Removing update-era drugs before grouping and fold generation resolves the documented leakage/design conflict and preserves the intended transport boundary.
- The revised primary estimand is explicit: mean paired repeat-level `AUROC(D) - AUROC(B)` in eligible original-list drugs.
- The added-in-2.0 cohort remains secondary exploratory transport evidence and cannot replace the primary result.
- The precision simulation uses the actual development group vector and is treated as a planning diagnostic, not a performance result or a basis for post-hoc method selection.
- The update-fit regularisation rule is deterministic and fixed before update outcomes are accessed.
- The amendment discloses its effects on target population, uncertainty, schedule, reporting, and IEC/KUHS documentation.

### Limits of this verdict

This verdict approves the biostatistical/design resolution in PA-02 only. It does not authorize feature extraction, modelling, performance inspection, estimation, or reporting; it does not certify future G3/G4 artifacts; and it does not replace faculty-guide or IEC review. Any change to the reviewed amendment text changes its SHA-256 and requires renewed independent review or an explicitly documented determination that the change is non-substantive.

## Remaining governance requirements

Before either amendment may be marked `APPROVED` or incorporated into a new execution lock:

1. **Completed:** the project owner acknowledged both reviewed proposal versions on 2026-08-13; the amendment tables record the decision date and reviewed proposal hashes.
2. **Completed:** the project owner confirms fresh faculty-guide approval of both substantive proposal versions on 2026-08-13.
3. **Completed:** the project owner confirms a post-proposal IEC `approved` disposition for both substantive proposal versions on 2026-08-13.
4. Only non-identifying status, date, disposition, exact amendment hash, and a restricted-record locator may be stored publicly.
5. The protocol execution lock must be regenerated from a clean committed implementation only after every required approval row is complete.

The governance approvals are complete. This note still does not itself authorize execution: the approved amendment files must be committed, a clean execution lock must be regenerated and independently validated, and the prospective G2/G3/G4/G5 gates remain mandatory.
