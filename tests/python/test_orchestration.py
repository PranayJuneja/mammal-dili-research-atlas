from pathlib import Path


def test_orchestrator_checks_every_native_exit_and_separates_gates() -> None:
    script = Path("scripts/run-locked-pipeline.ps1").read_text(encoding="utf-8")
    assert "if ($LASTEXITCODE -ne 0)" in script
    assert "Invoke-Checked \"pnpm.cmd\"" in script
    assert "Invoke-Checked \"git\"" in script
    assert "Assert-PilotAccepted" in script
    assert "Assert-G3Accepted" in script
    assert "Assert-G4Accepted" in script
    model_body = script.split("function Invoke-PredictionsAndFreezeG4", 1)[1].split(
        "function Invoke-FreezeG4", 1
    )[0]
    assert '"estimate"' not in model_body
