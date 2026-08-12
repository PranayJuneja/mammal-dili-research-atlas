from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from mammal_dili.config import validate_config, validate_config_bundle
from mammal_dili.io import sha256_file, sha256_json, write_json
from mammal_dili.lock import LOCK_PATH, require_protocol_lock

G3_PATH = Path("audit/gates/g3_feature_fold_lock.json")
G3_VERDICT_PATH = Path("audit/gates/g3-validator.md")
G4_PATH = Path("audit/gates/g4_prediction_lock.json")
G4_VERDICT_PATH = Path("audit/gates/g4-validator.md")

FEATURE_PATHS = {
    "cohort": Path("data/processed/cohort_audit.csv"),
    "full_blind_input": Path("data/processed/mammal_full_blind.csv"),
    "verification_sample": Path("data/processed/mammal_verification_sample.csv"),
    "conventional": Path("artifacts/features/conventional.npz"),
    "conventional_manifest": Path("artifacts/features/conventional.manifest.json"),
    "mammal": Path("artifacts/features/mammal.npz"),
    "mammal_manifest": Path("artifacts/features/mammal.manifest.json"),
    "mammal_verification_repeat": Path("artifacts/features/mammal_verification_repeat.npz"),
    "mammal_verification_repeat_manifest": Path("artifacts/features/mammal_verification_repeat.manifest.json"),
    "full_embedding_validation": Path("audit/qc/full_embedding_validation.json"),
    "all_cohort_folds": Path("artifacts/folds/outer_folds.csv"),
    "all_cohort_folds_summary": Path("artifacts/folds/outer_folds.summary.json"),
    "development_folds": Path("artifacts/folds/development_folds.csv"),
    "development_folds_summary": Path("artifacts/folds/development_folds.summary.json"),
    "update_groups": Path("artifacts/folds/update_groups.csv"),
    "update_groups_summary": Path("artifacts/folds/update_groups.summary.json"),
    "precision_summary": Path("audit/qc/precision_simulation.summary.json"),
    "precision_assessment": Path("audit/qc/precision_assessment.md"),
}

PREDICTION_PATHS = {
    "primary": Path("artifacts/predictions/oof_predictions.csv"),
    "vmost_vs_vno": Path("artifacts/predictions/vmost_vno_oof_predictions.csv"),
    "stratified_random": Path("artifacts/predictions/random_split_oof_predictions.csv"),
    "class_balanced": Path("artifacts/predictions/balanced_oof_predictions.csv"),
    "update_transport": Path("artifacts/predictions/update_predictions.csv"),
}


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _git_revision() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def _ids(path: str | Path) -> list[str]:
    with np.load(path) as arrays:
        return arrays["drug_ids"].astype(str).tolist()


def _approved_amendments() -> dict[str, str]:
    paths = {
        "PA-01": Path("audit/pilot/protocol-amendment-pa-01.md"),
        "PA-02": Path("audit/protocol_lock/protocol-amendment-pa-02.md"),
    }
    hashes = {}
    for label, path in paths.items():
        text = path.read_text(encoding="utf-8")
        if "Status: APPROVED" not in text:
            raise RuntimeError(f"{label} is not approved; downstream execution is prohibited")
        hashes[label] = sha256_file(path)
    return hashes


def _assert_complete_partition() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    full = pd.read_csv(FEATURE_PATHS["full_blind_input"])
    development = pd.read_csv(FEATURE_PATHS["development_folds"])
    update = pd.read_csv(FEATURE_PATHS["update_groups"])
    for label, frame in [("full", full), ("development", development), ("update", update)]:
        ids = frame["drug_id"].astype(str)
        if ids.duplicated().any():
            raise AssertionError(f"{label} IDs are not unique")
    full_ids = set(full["drug_id"].astype(str))
    development_ids = set(development["drug_id"].astype(str))
    update_ids = set(update["drug_id"].astype(str))
    if development_ids & update_ids or development_ids | update_ids != full_ids:
        raise AssertionError("Development/update rows do not form an exact disjoint full-cohort partition")
    if set(development["release_group"]) != {"original-list"}:
        raise AssertionError("Development folds contain non-original-list rows")
    if set(update["release_group"]) != {"added-in-2.0"}:
        raise AssertionError("Update groups contain non-added rows")
    return full, development, update


def create_feature_fold_lock(output_path: str | Path = G3_PATH) -> dict:
    protocol = require_protocol_lock()
    amendments = _approved_amendments()
    missing = [str(path) for path in FEATURE_PATHS.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"G3 inputs are missing: {missing}")
    full, development, update = _assert_complete_partition()
    full_ids = full["drug_id"].astype(str).tolist()
    conventional_ids = _ids(FEATURE_PATHS["conventional"])
    mammal_ids = _ids(FEATURE_PATHS["mammal"])
    if conventional_ids != full_ids or mammal_ids != full_ids:
        raise AssertionError("G3 requires identical ordered 100% coverage in both feature families")
    validation = _load_json(FEATURE_PATHS["full_embedding_validation"])
    if not validation.get("passed") or validation.get("coverage") != 1.0:
        raise AssertionError("Full MAMMAL validation has not passed at exact 100% coverage")
    expected_sample_ids = pd.read_csv(FEATURE_PATHS["verification_sample"])["drug_id"].astype(str).tolist()
    repeat_ids = _ids(FEATURE_PATHS["mammal_verification_repeat"])
    expected_validation = {
        "full_output_sha256": sha256_file(FEATURE_PATHS["mammal"]),
        "repeat_output_sha256": sha256_file(FEATURE_PATHS["mammal_verification_repeat"]),
        "expected_sample_sha256": sha256_file(FEATURE_PATHS["verification_sample"]),
        "expected_sample_drug_ids": expected_sample_ids,
        "sampling_seed": int(validate_config("configs/seeds.yaml")["embedding_verification_sample"]),
    }
    for field, expected in expected_validation.items():
        if validation.get(field) != expected:
            raise AssertionError(f"Full embedding QC report is stale for {field}")
    if repeat_ids != expected_sample_ids:
        raise AssertionError("Repeat feature IDs/order do not match the frozen verification sample")
    conventional_manifest = _load_json(FEATURE_PATHS["conventional_manifest"])
    if (
        conventional_manifest.get("output_sha256") != sha256_file(FEATURE_PATHS["conventional"])
        or conventional_manifest.get("source_cohort_sha256") != sha256_file(FEATURE_PATHS["cohort"])
    ):
        raise AssertionError("Conventional feature manifest lineage is stale")
    mammal_manifest = _load_json(FEATURE_PATHS["mammal_manifest"])
    repeat_manifest = _load_json(FEATURE_PATHS["mammal_verification_repeat_manifest"])
    if (
        mammal_manifest.get("output_sha256") != sha256_file(FEATURE_PATHS["mammal"])
        or mammal_manifest.get("input_sha256") != sha256_file(FEATURE_PATHS["full_blind_input"])
        or repeat_manifest.get("output_sha256") != sha256_file(FEATURE_PATHS["mammal_verification_repeat"])
        or repeat_manifest.get("input_sha256") != sha256_file(FEATURE_PATHS["verification_sample"])
    ):
        raise AssertionError("MAMMAL feature manifest lineage is stale")
    precision = _load_json(FEATURE_PATHS["precision_summary"])
    if precision.get("observed_rows") != len(development):
        raise AssertionError("Precision simulation is not based on the final development population")
    if precision.get("folds_sha256") != sha256_file(FEATURE_PATHS["development_folds"]):
        raise AssertionError("Precision simulation fold hash is stale")
    assessment = FEATURE_PATHS["precision_assessment"].read_text(encoding="utf-8")
    assessment_terms = [
        f"{precision['observed_rows']}-row",
        f"{precision['observed_groups']}-group",
        f"largest {precision['observed_largest_group']}-drug",
        f"{precision['minimum_empirical_coverage']:.3f}",
        f"{precision['maximum_mean_ci_width']:.5f}",
        f"{precision['maximum_endpoint_shift_100_to_2000']:.5f}",
    ]
    if not all(term in assessment for term in assessment_terms):
        raise AssertionError("Precision assessment does not describe the current locked simulation")
    bundle, bundle_hash = validate_config_bundle("configs")
    if protocol["config_bundle_sha256"] != bundle_hash:
        raise AssertionError("Protocol/config mismatch at G3")
    payload = {
        "schema_version": 1,
        "gate": "G3",
        "status": "LOCKED_AWAITING_INDEPENDENT_VALIDATION",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "implementation_revision": _git_revision(),
        "protocol_lock_sha256": sha256_file(LOCK_PATH),
        "config_bundle_sha256": bundle_hash,
        "validated_config_sha256": sha256_json(bundle),
        "amendment_hashes": amendments,
        "counts": {
            "full_feature_rows": len(full),
            "development_rows": len(development),
            "development_groups": int(development["scaffold_id"].nunique()),
            "update_rows": len(update),
            "update_groups": int(update["scaffold_id"].nunique()),
        },
        "source_hashes": {name: sha256_file(path) for name, path in FEATURE_PATHS.items()},
        "ordered_feature_ids_sha256": sha256_json(full_ids),
        "precision_diagnostics": {
            key: precision[key]
            for key in [
                "minimum_empirical_coverage",
                "maximum_mean_ci_width",
                "maximum_endpoint_shift_100_to_2000",
            ]
        },
    }
    write_json(output_path, payload)
    return payload


def _require_independent_verdict(lock_path: Path, verdict_path: Path, gate: str) -> None:
    if not verdict_path.exists():
        raise RuntimeError(f"{gate} independent validator verdict is missing")
    text = verdict_path.read_text(encoding="utf-8")
    expected = sha256_file(lock_path)
    if "Status: PASS" not in text or f"Gate lock SHA-256: {expected}" not in text:
        raise RuntimeError(f"{gate} independent verdict is absent, failing, or bound to another lock")


def require_feature_fold_lock(require_validator: bool = True) -> dict:
    protocol = require_protocol_lock()
    if not G3_PATH.exists():
        raise RuntimeError("G3 feature/fold lock is missing")
    marker = _load_json(G3_PATH)
    if marker.get("gate") != "G3":
        raise RuntimeError("Invalid G3 marker")
    if marker.get("protocol_lock_sha256") != sha256_file(LOCK_PATH):
        raise RuntimeError("G3 was created against another protocol lock")
    if marker.get("config_bundle_sha256") != protocol["config_bundle_sha256"]:
        raise RuntimeError("G3 config lineage is stale")
    for name, path in FEATURE_PATHS.items():
        if marker["source_hashes"].get(name) != sha256_file(path):
            raise RuntimeError(f"G3 artifact drift detected: {name}")
    _assert_complete_partition()
    if require_validator:
        _require_independent_verdict(G3_PATH, G3_VERDICT_PATH, "G3")
    return marker


def _validate_prediction_frame(
    path: Path,
    expected_ids: set[str],
    models: set[str],
    repeats: int | None,
    release_group: str,
) -> dict:
    frame = pd.read_csv(path)
    required = {
        "drug_id", "outcome", "scaffold_id", "release_group", "model",
        "predicted_probability", "selected_c", "youden_threshold",
        "sensitivity_threshold", "convergence_warnings",
    }
    if not required.issubset(frame.columns):
        raise AssertionError(f"{path} lacks required columns: {sorted(required - set(frame.columns))}")
    if set(frame["drug_id"].astype(str)) != expected_ids:
        raise AssertionError(f"{path} has incorrect drug coverage")
    if set(frame["model"].astype(str)) != models or set(frame["release_group"]) != {release_group}:
        raise AssertionError(f"{path} has incorrect model or release-group coverage")
    numeric = frame[["predicted_probability", "selected_c", "youden_threshold", "sensitivity_threshold"]].to_numpy(float)
    if not np.isfinite(numeric).all() or not frame["predicted_probability"].between(0, 1).all():
        raise AssertionError(f"{path} contains invalid probabilities or tuning values")
    if not set(frame["outcome"].astype(int)).issubset({0, 1}):
        raise AssertionError(f"{path} has non-binary outcomes")
    key = ["drug_id", "model"] + (["repeat"] if repeats is not None else [])
    if frame.duplicated(key).any():
        raise AssertionError(f"{path} contains duplicate prediction keys")
    expected_rows = len(expected_ids) * len(models) * (repeats or 1)
    if len(frame) != expected_rows:
        raise AssertionError(f"{path} expected {expected_rows} rows, found {len(frame)}")
    if repeats is not None and set(frame["repeat"].astype(int)) != set(range(repeats)):
        raise AssertionError(f"{path} has incorrect repeat coverage")
    return {
        "rows": len(frame),
        "drugs": len(expected_ids),
        "models": sorted(models),
        "convergence_warnings": int(frame["convergence_warnings"].sum()),
    }


def create_prediction_lock(output_path: str | Path = G4_PATH) -> dict:
    require_feature_fold_lock()
    analysis_config = validate_config("configs/analysis.yaml")
    development = pd.read_csv(FEATURE_PATHS["development_folds"])
    update = pd.read_csv(FEATURE_PATHS["update_groups"])
    development_ids = set(development["drug_id"].astype(str))
    vmost_ids = set(
        development.loc[
            development["dili_category"].str.startswith("vMost")
            | development["dili_category"].str.startswith("vNo"),
            "drug_id",
        ].astype(str)
    )
    update_ids = set(update["drug_id"].astype(str))
    contracts = {
        "primary": (development_ids, {"A", "B", "C", "D"}, 5, "original-list"),
        "vmost_vs_vno": (vmost_ids, {"B", "D"}, 5, "original-list"),
        "stratified_random": (development_ids, {"B", "D"}, 5, "original-list"),
        "class_balanced": (development_ids, {"B", "D"}, 5, "original-list"),
        "update_transport": (update_ids, {"A", "B", "C", "D"}, None, "added-in-2.0"),
    }
    manifest_contracts = {
        "primary": ("primary", "scaffold_grouped", "primary"),
        "vmost_vs_vno": ("vmost_vs_vno", "scaffold_grouped", "primary"),
        "stratified_random": ("primary", "stratified_random", "primary"),
        "class_balanced": ("primary", "scaffold_grouped", "balanced_robustness"),
    }
    summaries = {}
    source_hashes = {}
    for name, path in PREDICTION_PATHS.items():
        if not path.exists():
            raise FileNotFoundError(f"G4 prediction is missing: {path}")
        summaries[name] = _validate_prediction_frame(path, *contracts[name])
        companions = [path, path.with_suffix(".manifest.json")]
        if name != "update_transport":
            companions.extend([path.with_suffix(".tuning.json"), path.with_suffix(".folds.csv")])
        for companion in companions:
            if not companion.exists():
                raise FileNotFoundError(f"G4 companion is missing: {companion}")
            source_hashes[str(companion)] = sha256_file(companion)
        manifest = _load_json(path.with_suffix(".manifest.json"))
        output_hash = manifest.get("output_sha256", manifest.get("prediction_sha256"))
        if output_hash != sha256_file(path):
            raise AssertionError(f"{name} manifest output hash is stale")
        if manifest.get("protocol_lock_sha256") != sha256_file(LOCK_PATH):
            raise AssertionError(f"{name} manifest protocol lineage is stale")
        if manifest.get("g3_feature_lock_sha256") != sha256_file(G3_PATH):
            raise AssertionError(f"{name} manifest G3 lineage is stale")
        if name != "update_transport":
            expected_population, expected_design, expected_weight = manifest_contracts[name]
            if (
                manifest.get("population") != expected_population
                or manifest.get("validation_design") != expected_design
                or manifest.get("class_weight_mode") != expected_weight
                or manifest.get("repeats") != 5
                or set(manifest.get("models", [])) != contracts[name][1]
            ):
                raise AssertionError(f"{name} manifest settings violate the frozen contract")
            if manifest.get("folds_sha256") != sha256_file(FEATURE_PATHS["development_folds"]):
                raise AssertionError(f"{name} does not use the G3 development folds")
            if manifest.get("conventional_features_sha256") != sha256_file(FEATURE_PATHS["conventional"]):
                raise AssertionError(f"{name} conventional feature lineage is stale")
            if manifest.get("mammal_features_sha256") != sha256_file(FEATURE_PATHS["mammal"]):
                raise AssertionError(f"{name} MAMMAL feature lineage is stale")
            tuning = _load_json(path.with_suffix(".tuning.json"))
            tuning_keys = [(row["model"], int(row["repeat"]), int(row["outer_fold"])) for row in tuning]
            expected_tuning_rows = len(contracts[name][1]) * int(analysis_config["required_outer_selection_count"])
            expected_tuning_keys = {
                (model, repeat, fold)
                for model in contracts[name][1]
                for repeat in range(5)
                for fold in range(5)
            }
            if (
                len(tuning) != expected_tuning_rows
                or set(tuning_keys) != expected_tuning_keys
                or len(set(tuning_keys)) != len(tuning_keys)
            ):
                raise AssertionError(f"{name} tuning coverage is incomplete or duplicated")
            if any(float(row["selected_c"]) not in analysis_config["regularization_grid"] for row in tuning):
                raise AssertionError(f"{name} tuning selected a C outside the locked grid")
            if manifest.get("tuning_sha256") != sha256_file(path.with_suffix(".tuning.json")):
                raise AssertionError(f"{name} tuning hash is stale")
            fold_path = path.with_suffix(".folds.csv")
            if manifest.get("analysis_folds_sha256") != sha256_file(fold_path):
                raise AssertionError(f"{name} analysis-fold hash is stale")
            fold_frame = pd.read_csv(fold_path)
            fold_columns = sorted(
                [column for column in fold_frame if "outer_fold_repeat_" in column],
                key=lambda column: int(column.rsplit("_", 1)[1]),
            )
            if len(fold_columns) != 5 or fold_frame["drug_id"].duplicated().any():
                raise AssertionError(f"{name} analysis-fold artifact has invalid coverage")
            expected_outer = {
                (str(row.drug_id), repeat): int(getattr(row, column))
                for row in fold_frame.itertuples(index=False)
                for repeat, column in enumerate(fold_columns)
            }
            prediction_frame = pd.read_csv(path)
            if any(
                expected_outer.get((str(row.drug_id), int(row.repeat))) != int(row.outer_fold)
                for row in prediction_frame.itertuples(index=False)
            ):
                raise AssertionError(f"{name} prediction outer-fold assignments disagree with manifest")
            chemical_group_map = development.set_index("drug_id")["scaffold_id"].astype(str).to_dict()
            if any(
                str(row.scaffold_id) != chemical_group_map[str(row.drug_id)]
                for row in prediction_frame.itertuples(index=False)
            ):
                raise AssertionError(f"{name} predictions do not preserve chemical scaffold IDs")
        else:
            primary_path = PREDICTION_PATHS["primary"]
            if manifest.get("development_predictions_sha256") != sha256_file(primary_path):
                raise AssertionError("Update predictions are not bound to the locked primary development run")
            if manifest.get("development_tuning_sha256") != sha256_file(primary_path.with_suffix(".tuning.json")):
                raise AssertionError("Update predictions are not bound to primary tuning")
            selected = manifest.get("selected_hyperparameters", {})
            if set(selected) != {"A", "B", "C", "D"} or any(
                item.get("rule") != analysis_config["final_hyperparameter_rule"]
                for item in selected.values()
            ):
                raise AssertionError("Update final-fit hyperparameter rule is not the locked rule")
            primary_tuning = _load_json(primary_path.with_suffix(".tuning.json"))
            for model in ["A", "B", "C", "D"]:
                model_rows = [row for row in primary_tuning if row["model"] == model]
                keys = {(int(row["repeat"]), int(row["outer_fold"])) for row in model_rows}
                if len(model_rows) != 25 or keys != {(repeat, fold) for repeat in range(5) for fold in range(5)}:
                    raise AssertionError(f"Primary tuning is not a unique 5x5 grid for {model}")
                counts = pd.Series([float(row["selected_c"]) for row in model_rows]).value_counts()
                modal = counts[counts == counts.max()].index.astype(float).tolist()
                expected_c = min(modal)
                expected_counts = {str(key): int(value) for key, value in counts.items()}
                if (
                    float(selected[model].get("C")) != expected_c
                    or selected[model].get("outer_selection_counts") != expected_counts
                ):
                    raise AssertionError(f"Update selected C/counts do not reproduce primary tuning for {model}")
    payload = {
        "schema_version": 1,
        "gate": "G4",
        "status": "LOCKED_AWAITING_INDEPENDENT_VALIDATION",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "implementation_revision": _git_revision(),
        "protocol_lock_sha256": sha256_file(LOCK_PATH),
        "g3_feature_lock_sha256": sha256_file(G3_PATH),
        "prediction_contracts": summaries,
        "source_hashes": source_hashes,
    }
    write_json(output_path, payload)
    return payload


def require_prediction_lock() -> dict:
    require_feature_fold_lock()
    if not G4_PATH.exists():
        raise RuntimeError("G4 prediction lock is missing")
    marker = _load_json(G4_PATH)
    if marker.get("g3_feature_lock_sha256") != sha256_file(G3_PATH):
        raise RuntimeError("G4 was created against another G3 lock")
    for path, expected in marker.get("source_hashes", {}).items():
        if sha256_file(path) != expected:
            raise RuntimeError(f"G4 prediction drift detected: {path}")
    _require_independent_verdict(G4_PATH, G4_VERDICT_PATH, "G4")
    return marker
