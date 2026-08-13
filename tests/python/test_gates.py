from pathlib import Path

import pandas as pd
import pytest

from mammal_dili import gates
from mammal_dili.gates import (
    _validate_held_out_update_manifest,
    _validate_prediction_frame,
)


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


def test_update_id_hash_contract_is_order_independent() -> None:
    import hashlib

    ids = {"new-2", "new-1"}
    digest = hashlib.sha256("\n".join(sorted(ids)).encode("utf-8")).hexdigest()
    assert digest == hashlib.sha256(b"new-1\nnew-2").hexdigest()


def test_g4_rejects_false_held_out_update_manifest() -> None:
    with pytest.raises(AssertionError, match="held-out update provenance"):
        _validate_held_out_update_manifest(
            {
                "update_cohort_held_out_drugs": 0,
                "update_cohort_drug_ids_sha256": __import__("hashlib").sha256(b"").hexdigest(),
            },
            {"new-1", "new-2"},
            "primary",
        )


def test_g3_requires_exact_current_amendment_map(tmp_path, monkeypatch) -> None:
    marker_path = tmp_path / "g3.json"
    marker_path.write_text(
        __import__("json").dumps(
            {
                "gate": "G3",
                "protocol_lock_sha256": "protocol-hash",
                "config_bundle_sha256": "config-hash",
                "amendment_hashes": {"PA-01": "one", "PA-02": "two"},
                "source_hashes": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(gates, "G3_PATH", marker_path)
    monkeypatch.setattr(gates, "LOCK_PATH", tmp_path / "lock.json")
    (tmp_path / "lock.json").write_bytes(b"lock")
    monkeypatch.setattr(gates, "sha256_file", lambda path: "protocol-hash")
    monkeypatch.setattr(
        gates,
        "require_protocol_lock",
        lambda: {
            "config_bundle_sha256": "config-hash",
            "approved_amendment_hashes": {
                "PA-01": "one",
                "PA-02": "two",
                "PA-03": "three",
            },
        },
    )
    with pytest.raises(RuntimeError, match="amendment lineage"):
        gates.require_feature_fold_lock(require_validator=False)


def test_g3_source_hashes_include_precision_simulation_csv() -> None:
    assert gates.FEATURE_PATHS["precision_simulation"] == Path(
        "audit/qc/precision_simulation.csv"
    )


def test_g3_rejects_precision_simulation_csv_drift(tmp_path, monkeypatch) -> None:
    lock_path = tmp_path / "lock.json"
    lock_path.write_bytes(b"lock")
    precision_path = tmp_path / "precision.csv"
    precision_path.write_text("changed", encoding="utf-8")
    marker_path = tmp_path / "g3.json"
    marker_path.write_text(
        __import__("json").dumps(
            {
                "gate": "G3",
                "protocol_lock_sha256": "protocol-hash",
                "config_bundle_sha256": "config-hash",
                "amendment_hashes": {"PA-03": "three"},
                "source_hashes": {"precision_simulation": "old-hash"},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(gates, "G3_PATH", marker_path)
    monkeypatch.setattr(gates, "LOCK_PATH", lock_path)
    monkeypatch.setattr(gates, "FEATURE_PATHS", {"precision_simulation": precision_path})
    monkeypatch.setattr(
        gates,
        "require_protocol_lock",
        lambda: {
            "config_bundle_sha256": "config-hash",
            "approved_amendment_hashes": {"PA-03": "three"},
        },
    )
    monkeypatch.setattr(gates, "_assert_complete_partition", lambda: None)

    def fake_hash(path):
        return "protocol-hash" if Path(path) == lock_path else "new-hash"

    monkeypatch.setattr(gates, "sha256_file", fake_hash)
    with pytest.raises(RuntimeError, match="precision_simulation"):
        gates.require_feature_fold_lock(require_validator=False)
