param(
    [ValidateSet("pilot", "features", "g3", "models", "g4", "estimate", "report", "verify", "all")]
    [string]$Stage = "all"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot

$ChemPython = Join-Path $ProjectRoot ".venv-chem\Scripts\python.exe"
$MammalPython = Join-Path $ProjectRoot ".venv-mammal\Scripts\python.exe"
$Pa01 = Join-Path $ProjectRoot "audit\pilot\protocol-amendment-pa-01.md"
$Pa02 = Join-Path $ProjectRoot "audit\protocol_lock\protocol-amendment-pa-02.md"

if (-not (Test-Path -LiteralPath $ChemPython)) { throw "Missing chemistry environment: $ChemPython" }
if (-not (Test-Path -LiteralPath $MammalPython)) { throw "Missing MAMMAL environment: $MammalPython" }

function Invoke-Checked {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Native command failed with exit code $LASTEXITCODE`: $Executable $($Arguments -join ' ')"
    }
}

function Invoke-Chem { param([string[]]$Arguments) Invoke-Checked $ChemPython $Arguments }
function Invoke-Mammal { param([string[]]$Arguments) Invoke-Checked $MammalPython $Arguments }

function Assert-Governance {
    foreach ($amendment in @($Pa01, $Pa02)) {
        if (-not (Test-Path -LiteralPath $amendment)) { throw "Missing amendment: $amendment" }
        if ((Get-Content -LiteralPath $amendment -Raw) -notmatch "Status: APPROVED") {
            throw "$(Split-Path -Leaf $amendment) is not approved; accepted execution is prohibited."
        }
    }
    Invoke-Chem @("-c", "from mammal_dili.lock import require_protocol_lock; require_protocol_lock()")
}

function Assert-CleanWorktree {
    $status = & git status --porcelain
    if ($LASTEXITCODE -ne 0) { throw "git status failed with exit code $LASTEXITCODE" }
    if ($status) { throw "Accepted execution requires a clean worktree." }
}

function Assert-PilotAccepted {
    Assert-Governance
    Invoke-Chem @("-c", "from pathlib import Path; import hashlib,json; p=Path('artifacts/pilot/pilot_report.json'); v=Path('audit/gates/g2-validator.md'); assert p.exists() and json.loads(p.read_text())['passed']; h=hashlib.sha256(p.read_bytes()).hexdigest(); assert v.exists() and 'Status: PASS' in v.read_text() and f'Pilot report SHA-256: {h}' in v.read_text(), 'G2 independent acceptance is missing or stale'")
}

function Assert-G3Accepted {
    Assert-Governance
    Invoke-Chem @("-c", "from mammal_dili.gates import require_feature_fold_lock; require_feature_fold_lock()")
}

function Assert-G4Accepted {
    Assert-Governance
    Invoke-Chem @("-c", "from mammal_dili.gates import require_prediction_lock; require_prediction_lock()")
}

function Invoke-AcceptedPilot {
    Assert-Governance
    Assert-CleanWorktree
    Invoke-Mammal @("-m", "mammal_dili", "extract-mammal", "--input", "audit/pilot/frozen_pilot_v2.csv", "--output", "artifacts/pilot/mammal_pilot_baseline.npz")
    Invoke-Mammal @("-m", "mammal_dili", "extract-mammal", "--input", "audit/pilot/frozen_pilot_v2.csv", "--output", "artifacts/pilot/mammal_pilot_same_order.npz")
    Invoke-Mammal @("-m", "mammal_dili", "extract-mammal", "--input", "audit/pilot/frozen_pilot_v2.csv", "--output", "artifacts/pilot/mammal_pilot_reordered.npz", "--reverse-order")
    Invoke-Chem @("-m", "mammal_dili", "validate-pilot")
}

function Invoke-FeaturesAndFreezeG3 {
    Assert-PilotAccepted
    Assert-CleanWorktree
    Invoke-Chem @("-m", "mammal_dili", "build-features")
    Invoke-Chem @("-m", "mammal_dili", "prepare-mammal-input")
    Invoke-Chem @("-m", "mammal_dili", "select-embedding-qc-sample")
    Invoke-Mammal @("-m", "mammal_dili", "extract-mammal", "--input", "data/processed/mammal_full_blind.csv", "--output", "artifacts/features/mammal.npz")
    Invoke-Mammal @("-m", "mammal_dili", "extract-mammal", "--input", "data/processed/mammal_verification_sample.csv", "--output", "artifacts/features/mammal_verification_repeat.npz")
    Invoke-Chem @("-m", "mammal_dili", "validate-full-extraction")
    Invoke-Chem @("-m", "mammal_dili", "build-folds")
    Invoke-Chem @("-m", "mammal_dili", "build-analysis-folds")
    Invoke-Chem @("-m", "mammal_dili", "simulate-precision")
    Invoke-Chem @("-m", "mammal_dili", "freeze-g3")
}

function Invoke-FreezeG3 { Assert-PilotAccepted; Invoke-Chem @("-m", "mammal_dili", "freeze-g3") }

function Invoke-PredictionsAndFreezeG4 {
    Assert-G3Accepted
    Assert-CleanWorktree
    Invoke-Chem @("-m", "mammal_dili", "cross-validate")
    Invoke-Chem @("-m", "mammal_dili", "cross-validate-vmost")
    Invoke-Chem @("-m", "mammal_dili", "cross-validate-random")
    Invoke-Chem @("-m", "mammal_dili", "cross-validate-balanced")
    Invoke-Chem @("-m", "mammal_dili", "evaluate-update")
    Invoke-Chem @("-m", "mammal_dili", "freeze-g4")
}

function Invoke-FreezeG4 { Assert-G3Accepted; Invoke-Chem @("-m", "mammal_dili", "freeze-g4") }

function Invoke-Estimates {
    Assert-G4Accepted
    Invoke-Chem @("-m", "mammal_dili", "estimate")
    Invoke-Chem @("-m", "mammal_dili", "estimate-vmost")
    Invoke-Chem @("-m", "mammal_dili", "estimate-random")
    Invoke-Chem @("-m", "mammal_dili", "estimate-balanced")
    Invoke-Chem @("-m", "mammal_dili", "estimate-update")
}

function Invoke-Report { Assert-G4Accepted; Invoke-Chem @("-m", "mammal_dili", "generate-report") }

function Invoke-Verification {
    Invoke-Chem @("-m", "pytest", "-q", "tests/python", "--ignore=tests/python/test_pooling.py")
    Invoke-Mammal @("-m", "pytest", "-q", "tests/python/test_pooling.py")
    Invoke-Chem @("-m", "ruff", "check", "src", "tests")
    Invoke-Checked "pnpm.cmd" @("typecheck")
    Invoke-Checked "pnpm.cmd" @("lint")
    Invoke-Checked "pnpm.cmd" @("test")
    Invoke-Checked "pnpm.cmd" @("build")
    Invoke-Checked "git" @("diff", "--check")
}

switch ($Stage) {
    "pilot" { Invoke-AcceptedPilot }
    "features" { Invoke-FeaturesAndFreezeG3 }
    "g3" { Invoke-FreezeG3 }
    "models" { Invoke-PredictionsAndFreezeG4 }
    "g4" { Invoke-FreezeG4 }
    "estimate" { Invoke-Estimates }
    "report" { Invoke-Report }
    "verify" { Invoke-Verification }
    "all" {
        Invoke-AcceptedPilot
        Invoke-FeaturesAndFreezeG3
        Invoke-PredictionsAndFreezeG4
        Invoke-Estimates
        Invoke-Report
        Invoke-Verification
    }
}
