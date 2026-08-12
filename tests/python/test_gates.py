from pathlib import Path

import pandas as pd
import pytest

from mammal_dili.gates import _validate_prediction_frame


def _prediction_row(drug_id: str, model: str, repeat: int = 0) -> dict:
    return {
        "drug_id": drug_id,
        "outcome": 1,
        "scaffold_id": "group-1",
        "release_group": "original-list",
        "model": model,
        "repeat": repeat,
        "predicted_probability": 0.7,
        "selected_c": 1.0,
        "youden_threshold": 0.5,
        "sensitivity_threshold": 0.4,
        "convergence_warnings": 0,
    }


def test_prediction_gate_requires_exact_unique_model_repeat_coverage(tmp_path: Path) -> None:
    path = tmp_path / "predictions.csv"
    rows = [_prediction_row("drug-1", model) for model in ["B", "D"]]
    pd.DataFrame(rows).to_csv(path, index=False)
    summary = _validate_prediction_frame(
        path, {"drug-1"}, {"B", "D"}, 1, "original-list"
    )
    assert summary["rows"] == 2

    pd.DataFrame([*rows, rows[0]]).to_csv(path, index=False)
    with pytest.raises(AssertionError, match="duplicate"):
        _validate_prediction_frame(path, {"drug-1"}, {"B", "D"}, 1, "original-list")


def test_prediction_gate_rejects_nonfinite_or_out_of_range_probability(tmp_path: Path) -> None:
    path = tmp_path / "predictions.csv"
    rows = [_prediction_row("drug-1", model) for model in ["B", "D"]]
    rows[1]["predicted_probability"] = 1.2
    pd.DataFrame(rows).to_csv(path, index=False)
    with pytest.raises(AssertionError, match="invalid"):
        _validate_prediction_frame(path, {"drug-1"}, {"B", "D"}, 1, "original-list")
