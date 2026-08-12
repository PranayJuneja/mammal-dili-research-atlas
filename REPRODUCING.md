# Clean-room reproduction guide

This guide reconstructs the MAMMAL–DILI benchmark without notebook state. It deliberately separates technical generation, independent gate acceptance, prediction freezing, and result narration.

## Scope and prerequisites

- Windows PowerShell 5.1 or PowerShell 7.
- Git, Python 3.12, and pnpm 10.15.1.
- Approximately 8 GB free storage for environments, source checkout, model snapshot, and artifacts.
- Network access to the FDA snapshot transport, PubChem, GitHub, Hugging Face, and package registries.
- Access to the private governance record. Names, signatures, IEC letters, and student identifiers must remain outside this public checkout.

The tested execution target is Windows ARM64 on CPU. The MAMMAL checkpoint is approximately 1.83 GB and full extraction is intentionally CPU-compatible but slow.

## 1. Recreate environments

From a clean repository checkout:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap-environments.ps1
```

The script refuses to overwrite `.venv-chem` or `.venv-mammal`. It installs exact third-party versions from `environment/chemistry-lock.txt` and `environment/mammal-lock.txt`, installs this package editable without changing those dependency versions, checks out MAMMAL source revision `8cc56e9494b489ca86a63b76fa4cd2921f8af7f7`, and performs a frozen pnpm install.

## 2. Reconstruct and review the cohort

```powershell
.venv-chem\Scripts\python.exe -m mammal_dili acquire
.venv-chem\Scripts\python.exe -m mammal_dili resolve-pubchem
.venv-chem\Scripts\python.exe -m mammal_dili curate
.venv-chem\Scripts\python.exe -m mammal_dili make-review-packets
```

`acquire` downloads the immutable FDA page snapshot only when it is absent, then refuses unexpected record or label counts. PubChem responses are cached locally. Human review decisions must follow `docs/04_DATA_AND_CURATION_SPEC.md`; regeneration alone is not review acceptance.

Expected locked counts are 1,336 FDA records, 982 non-ambiguous records considered, 809 structurally eligible drugs, and 173 exclusions. The primary development cohort has 675 original-list drugs; 134 added-in-2.0 drugs remain untouched for the transport analysis.

## 3. Complete governance and lock execution

PA-01 and PA-02 must contain dated project-owner acknowledgement, private faculty-guide approval, and the IEC disposition (`not required by determination`, `notified`, or `approved`). Only non-identifying status is stored publicly.

After both amendments are marked `APPROVED` and contain no pending rows:

```powershell
git status --short
.venv-chem\Scripts\python.exe -m mammal_dili lock-protocol
git add audit/protocol_lock/execution_lock.json audit/pilot/protocol-amendment-pa-01.md audit/protocol_lock/protocol-amendment-pa-02.md
git commit -m "approve amendments and lock outcome execution"
```

The runtime rejects config changes, amendment changes, committed implementation drift, and dirty locked implementation paths after this commit.

## 4. Run and independently accept G2

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run-locked-pipeline.ps1 -Stage pilot
```

This launches three distinct processes: baseline order, same-order repeat, and reversed order. An independent reviewer verifies `artifacts/pilot/pilot_report.json`, then creates `audit/gates/g2-validator.md` with `Status: PASS` and the exact `Pilot report SHA-256: ...`. A failing or stale verdict blocks all later stages.

## 5. Generate features and freeze G3

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run-locked-pipeline.ps1 -Stage features
```

This requires accepted G2, exact 809/809 representation coverage, a separate deterministic 41-row embedding repeat, feature manifests, independently generated development/update groups, and the pre-performance precision simulation. It creates `audit/gates/g3_feature_fold_lock.json` but does not authorize modelling.

An independent reviewer binds a PASS verdict to the exact G3 lock hash in `audit/gates/g3-validator.md`:

```text
Status: PASS
Gate lock SHA-256: <sha256 of audit/gates/g3_feature_fold_lock.json>
```

## 6. Generate predictions and freeze G4

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run-locked-pipeline.ps1 -Stage models
```

This command generates predictions only. It does not calculate or print performance. G4 checks exact drug/model/repeat/fold coverage, finite probabilities, feature/fold/config lineage, complete 5×5 tuning grids, chemical-group identity, robustness contracts, and the one-time update fit rule.

An independent reviewer records `Status: PASS` and the exact G4 lock hash in `audit/gates/g4-validator.md`. Until that file is present and current, estimation and reporting refuse to run.

## 7. Estimate, report, and build the atlas

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run-locked-pipeline.ps1 -Stage estimate
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run-locked-pipeline.ps1 -Stage report
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run-locked-pipeline.ps1 -Stage verify
```

The report stage regenerates the paper, model and robustness tables, uncertainty companions, error analysis, figures, study-flow/scaffold summary, result manifest, and `src/data/generated-results.json`. The Next.js page imports that generated result directly.

## 8. Verification contract

`-Stage verify` checks:

- non-Torch Python tests in the chemistry environment;
- the real Torch pooling test in the MAMMAL environment;
- Ruff;
- TypeScript;
- ESLint with zero warnings;
- Vitest;
- a production Next.js build;
- Git whitespace errors.

For a complete release, independently compare all current file hashes with G3, G4, result, and report manifests; visually inspect desktop and mobile builds; screen public files for secrets and identifiers; and record the final independent G5 verdict.

## Failure behavior

Every native command in `scripts/run-locked-pipeline.ps1` is checked explicitly because Windows PowerShell 5.1 does not make `$ErrorActionPreference = "Stop"` sufficient for native exit codes. Any failed command, missing approval, stale hash, incomplete coverage, leakage contract violation, or missing independent verdict stops the pipeline. Do not bypass a gate by invoking a later CLI subcommand directly; the subcommands enforce the same locks.
