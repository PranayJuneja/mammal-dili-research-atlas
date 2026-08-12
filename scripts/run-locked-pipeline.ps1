param(
    [ValidateSet("pilot", "features", "models", "report", "verify", "all")]
    [string]$Stage = "all"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot

$ChemPython = Join-Path $ProjectRoot ".venv-chem\Scripts\python.exe"
$MammalPython = Join-Path $ProjectRoot ".venv-mammal\Scripts\python.exe"
$Amendment = Join-Path $ProjectRoot "audit\pilot\protocol-amendment-pa-01.md"

if (-not (Test-Path -LiteralPath $ChemPython)) {
    throw "Missing chemistry environment: $ChemPython"
}
if (-not (Test-Path -LiteralPath $MammalPython)) {
    throw "Missing MAMMAL environment: $MammalPython"
}

function Assert-PilotGovernance {
    $amendmentText = Get-Content -LiteralPath $Amendment -Raw
    if ($amendmentText -notmatch "Status: APPROVED") {
        throw "PA-01 is not approved; accepted extraction is prohibited."
    }
    & $ChemPython -c "from mammal_dili.lock import require_protocol_lock; require_protocol_lock()"
}

function Invoke-AcceptedPilot {
    Assert-PilotGovernance
    if ((git status --porcelain).Length -ne 0) {
        throw "Accepted execution requires a clean worktree."
    }
    & $MammalPython -m mammal_dili extract-mammal --input audit/pilot/frozen_pilot_v2.csv --output artifacts/pilot/mammal_pilot_baseline.npz
    & $MammalPython -m mammal_dili extract-mammal --input audit/pilot/frozen_pilot_v2.csv --output artifacts/pilot/mammal_pilot_same_order.npz
    & $MammalPython -m mammal_dili extract-mammal --input audit/pilot/frozen_pilot_v2.csv --output artifacts/pilot/mammal_pilot_reordered.npz --reverse-order
    & $ChemPython -m mammal_dili validate-pilot
}

function Invoke-Features {
    & $ChemPython -m mammal_dili build-features
    & $ChemPython -m mammal_dili build-folds
    & $ChemPython -m mammal_dili prepare-mammal-input
    & $ChemPython -m mammal_dili select-embedding-qc-sample
    & $MammalPython -m mammal_dili extract-mammal --input data/processed/mammal_full_blind.csv --output artifacts/features/mammal.npz
    & $MammalPython -m mammal_dili extract-mammal --input data/processed/mammal_verification_sample.csv --output artifacts/features/mammal_verification_repeat.npz
    & $ChemPython -m mammal_dili validate-full-extraction
}

function Invoke-Models {
    & $ChemPython -m mammal_dili cross-validate
    & $ChemPython -m mammal_dili estimate
    & $ChemPython -m mammal_dili cross-validate-vmost
    & $ChemPython -m mammal_dili estimate-vmost
    & $ChemPython -m mammal_dili cross-validate-random
    & $ChemPython -m mammal_dili estimate-random
    & $ChemPython -m mammal_dili cross-validate-balanced
    & $ChemPython -m mammal_dili estimate-balanced
    & $ChemPython -m mammal_dili evaluate-update
    & $ChemPython -m mammal_dili estimate-update
}

function Invoke-Report {
    & $ChemPython -m mammal_dili generate-report
}

function Invoke-Verification {
    & $ChemPython -m pytest -q tests/python --ignore=tests/python/test_pooling_real_torch.py
    & $MammalPython -m pytest -q tests/python/test_pooling_real_torch.py
    & $ChemPython -m ruff check src tests
    pnpm typecheck
    pnpm lint
    pnpm test
    pnpm build
    git diff --check
}

switch ($Stage) {
    "pilot" { Invoke-AcceptedPilot }
    "features" { Invoke-Features }
    "models" { Invoke-Models }
    "report" { Invoke-Report }
    "verify" { Invoke-Verification }
    "all" {
        Invoke-AcceptedPilot
        Invoke-Features
        Invoke-Models
        Invoke-Report
        Invoke-Verification
    }
}
