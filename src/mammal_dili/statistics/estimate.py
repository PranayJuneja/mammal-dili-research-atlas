from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)

from mammal_dili.config import validate_config
from mammal_dili.gates import G3_PATH, G4_PATH, PREDICTION_PATHS, require_prediction_lock
from mammal_dili.io import sha256_file, write_json
from mammal_dili.lock import LOCK_PATH, require_protocol_lock


def _calibration(y: np.ndarray, probabilities: np.ndarray) -> tuple[float, float]:
    clipped = np.clip(probabilities, 1e-6, 1 - 1e-6)
    logits = np.log(clipped / (1 - clipped)).reshape(-1, 1)
    model = LogisticRegression(C=1e6, solver="lbfgs").fit(logits, y)
    return float(model.intercept_[0]), float(model.coef_[0, 0])


def _metrics(frame: pd.DataFrame) -> dict:
    y = frame["outcome"].to_numpy(dtype=int)
    probabilities = frame["predicted_probability"].to_numpy(dtype=float)
    thresholds = frame["youden_threshold"].to_numpy(dtype=float)
    predictions = (probabilities >= thresholds).astype(int)
    intercept, slope = _calibration(y, probabilities)
    return {
        "auroc": float(roc_auc_score(y, probabilities)),
        "pr_auroc": float(average_precision_score(y, probabilities)),
        "brier": float(brier_score_loss(y, probabilities)),
        "sensitivity": float(recall_score(y, predictions)),
        "specificity": float(recall_score(1 - y, 1 - predictions)),
        "precision": float(precision_score(y, predictions, zero_division=0)),
        "balanced_accuracy": float(balanced_accuracy_score(y, predictions)),
        "calibration_intercept": intercept,
        "calibration_slope": slope,
    }


def _interpret(lower: float, upper: float, delta: float) -> tuple[str, str]:
    if lower > delta:
        return "meaningful_gain", "Practically important improvement supported."
    if lower > 0 and upper >= delta:
        return "some_gain", "Some improvement supported; practical importance remains uncertain."
    if lower <= 0 and upper >= delta:
        return "inconclusive", "Inconclusive for superiority and practical importance."
    if upper < 0:
        return "worse", "The expanded model performs worse under the locked procedure."
    if lower >= 0 and upper < delta:
        return "small_gain", "A small positive gain is supported; the pre-specified important gain is excluded."
    if upper < delta:
        return (
            "important_gain_excluded_without_superiority",
            "Superiority is not established; the pre-specified important gain is excluded.",
        )
    raise AssertionError("Unreachable interpretation interval")


def _validate_estimation_input(
    predictions_path: str | Path, analysis_key: str, update: bool = False
) -> tuple[pd.DataFrame, dict]:
    gate = require_prediction_lock()
    expected_path = PREDICTION_PATHS[analysis_key]
    if Path(predictions_path) != expected_path:
        raise AssertionError(f"Estimator requires the G4-locked {analysis_key} prediction path")
    expected_hash = gate["source_hashes"].get(str(expected_path))
    if expected_hash != sha256_file(predictions_path):
        raise AssertionError("Estimator prediction hash does not match G4")
    frame = pd.read_csv(predictions_path)
    key = ["drug_id", "model"] + ([] if update else ["repeat"])
    if frame.duplicated(key).any():
        raise AssertionError("Prediction keys are not unique")
    numeric = frame[["predicted_probability", "youden_threshold", "sensitivity_threshold"]].to_numpy(float)
    if not np.isfinite(numeric).all() or not frame["predicted_probability"].between(0, 1).all():
        raise AssertionError("Prediction values are non-finite or outside [0, 1]")
    pairing_key = ["drug_id"] + ([] if update else ["repeat"])
    paired = frame[frame["model"].isin(["B", "D"])]
    if not (paired.groupby(pairing_key)["model"].nunique() == 2).all():
        raise AssertionError("Models B and D are not exactly paired")
    consistency = paired.groupby(pairing_key).agg(
        outcomes=("outcome", "nunique"), scaffolds=("scaffold_id", "nunique")
    )
    if not ((consistency["outcomes"] == 1) & (consistency["scaffolds"] == 1)).all():
        raise AssertionError("Paired predictions disagree on outcome or scaffold")
    return frame, gate


def estimate_results(
    predictions_path: str | Path,
    config_path: str | Path,
    output_path: str | Path,
    analysis_label: str = "primary vMost/vLess versus vNo development analysis",
    analysis_key: str = "primary",
) -> dict:
    protocol = require_protocol_lock()
    config = validate_config(config_path)
    predictions, gate = _validate_estimation_input(predictions_path, analysis_key)
    repeat_metrics = []
    for (model, repeat), frame in predictions.groupby(["model", "repeat"]):
        repeat_metrics.append({"model": model, "repeat": int(repeat), **_metrics(frame)})
    repeat_frame = pd.DataFrame(repeat_metrics)
    summary = repeat_frame.groupby("model").mean(numeric_only=True).drop(columns=["repeat"]).to_dict(orient="index")
    metric_columns = [column for column in repeat_frame.columns if column not in {"model", "repeat"}]
    repeat_uncertainty = {
        str(model): {
            metric: {
                "mean": float(values[metric].mean()),
                "repeat_sd": float(values[metric].std(ddof=1)),
                "repeat_min": float(values[metric].min()),
                "repeat_max": float(values[metric].max()),
                "interpretation": "Descriptive variation across five repeated outer validations; not an independent-sample confidence interval.",
            }
            for metric in metric_columns
        }
        for model, values in repeat_frame.groupby("model")
    }
    paired = repeat_frame.pivot(index="repeat", columns="model", values="auroc")
    repeat_deltas = (paired["D"] - paired["B"]).to_numpy()
    point = float(repeat_deltas.mean())

    bd = predictions[predictions["model"].isin(["B", "D"])].copy()
    group_ids = bd["scaffold_id"].unique()
    rng = np.random.default_rng(int(config["bootstrap_seed"]))
    bootstrap = []
    for _ in range(int(config["bootstrap_resamples"])):
        sampled = rng.choice(group_ids, size=len(group_ids), replace=True)
        deltas = []
        for repeat in sorted(bd["repeat"].unique()):
            repeated_chunks = []
            repeat_data = bd[bd["repeat"] == repeat]
            for draw, group in enumerate(sampled):
                chunk = repeat_data[repeat_data["scaffold_id"] == group].copy()
                chunk["bootstrap_group"] = draw
                repeated_chunks.append(chunk)
            sample = pd.concat(repeated_chunks, ignore_index=True)
            values = {}
            for model in ["B", "D"]:
                model_sample = sample[sample["model"] == model]
                if model_sample["outcome"].nunique() < 2:
                    continue
                values[model] = roc_auc_score(model_sample["outcome"], model_sample["predicted_probability"])
            if len(values) == 2:
                deltas.append(values["D"] - values["B"])
        if deltas:
            bootstrap.append(float(np.mean(deltas)))
    lower, upper = np.percentile(bootstrap, [2.5, 97.5])
    region, wording = _interpret(float(lower), float(upper), float(config["practical_gain"]))
    result = {
        "analysis_label": analysis_label,
        "primary": {
            "estimand": "mean repeat AUROC(D) - AUROC(B)",
            "delta_auroc": point,
            "ci95": [float(lower), float(upper)],
            "practical_gain_benchmark": float(config["practical_gain"]),
            "interpretation_region": region,
            "interpretation": wording,
            "repeat_deltas": repeat_deltas.tolist(),
            "bootstrap_successful_resamples": len(bootstrap),
        },
        "models": summary,
        "model_repeat_uncertainty": repeat_uncertainty,
        "convergence": {
            "warning_count": int(predictions["convergence_warnings"].sum()),
            "fits_with_warnings": int((predictions["convergence_warnings"] > 0).sum()),
            "disposition": "All convergence warnings are disclosed; no fit is silently removed.",
        },
        "provenance": {
            "bootstrap_seed": int(config["bootstrap_seed"]),
            "classifier_seed": int(validate_config("configs/seeds.yaml")["classifier"]),
            "config_file_sha256": sha256_file(config_path),
            "protocol_lock_sha256": sha256_file(LOCK_PATH),
            "g3_feature_lock_sha256": sha256_file(G3_PATH),
            "g4_prediction_lock_sha256": sha256_file(G4_PATH),
            "prediction_sha256": sha256_file(predictions_path),
            "prediction_manifest_sha256": sha256_file(Path(predictions_path).with_suffix(".manifest.json")),
            "implementation_revision": protocol["implementation_revision_at_lock"],
        },
        "scope": "Drug-level DILIrank 2.0 concern classification; not patient-level risk or clinical validation.",
    }
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    write_json(target, result)
    repeat_metrics_path = target.with_name(f"{target.stem}.repeat_metrics.csv")
    bootstrap_path = target.with_name(f"{target.stem}.bootstrap_delta_auroc.npy")
    repeat_frame.to_csv(repeat_metrics_path, index=False)
    np.save(bootstrap_path, np.asarray(bootstrap, dtype=np.float64))
    write_json(
        target.with_suffix(".manifest.json"),
        {
            "analysis_key": analysis_key,
            "output_sha256": sha256_file(target),
            "prediction_sha256": sha256_file(predictions_path),
            "g4_prediction_lock_sha256": sha256_file(G4_PATH),
            "repeat_metrics_sha256": sha256_file(repeat_metrics_path),
            "bootstrap_sha256": sha256_file(bootstrap_path),
            "g4_source_hash_verified": gate["source_hashes"][str(PREDICTION_PATHS[analysis_key])],
        },
    )
    return result


def estimate_update_results(
    predictions_path: str | Path, config_path: str | Path, output_path: str | Path
) -> dict:
    """Estimate untouched update-cohort performance with complete-scaffold uncertainty."""
    protocol = require_protocol_lock()
    config = validate_config(config_path)
    predictions, _ = _validate_estimation_input(predictions_path, "update_transport", update=True)
    if set(predictions["release_group"]) != {"added-in-2.0"}:
        raise AssertionError("External transport estimates require only added-in-2.0 rows")
    models = {model: _metrics(frame) for model, frame in predictions.groupby("model")}
    by_id = {
        model: frame.set_index("drug_id") for model, frame in predictions.groupby("model")
    }
    if set(by_id["B"].index) != set(by_id["D"].index):
        raise AssertionError("Update-cohort B and D predictions are not paired")
    point = float(models["D"]["auroc"] - models["B"]["auroc"])
    groups = predictions["scaffold_id"].unique()
    rng = np.random.default_rng(int(config["bootstrap_seed"]) + 1)
    bootstrap = []
    paired = predictions[predictions["model"].isin(["B", "D"])]
    for _ in range(int(config["bootstrap_resamples"])):
        sampled = rng.choice(groups, size=len(groups), replace=True)
        chunks = []
        for draw, group in enumerate(sampled):
            chunk = paired[paired["scaffold_id"] == group].copy()
            chunk["bootstrap_group"] = draw
            chunks.append(chunk)
        sample = pd.concat(chunks, ignore_index=True)
        if sample["outcome"].nunique() < 2:
            continue
        values = {
            model: roc_auc_score(frame["outcome"], frame["predicted_probability"])
            for model, frame in sample.groupby("model")
        }
        if set(values) == {"B", "D"}:
            bootstrap.append(float(values["D"] - values["B"]))
    lower, upper = np.percentile(bootstrap, [2.5, 97.5])
    result = {
        "design": "untouched DILIrank 2.0 added-drug transport cohort",
        "drugs": int(predictions["drug_id"].nunique()),
        "models": models,
        "paired_delta_auroc": {
            "estimate": point,
            "ci95": [float(lower), float(upper)],
            "bootstrap_successful_resamples": len(bootstrap),
            "interpretation": "Exploratory transport evidence; it does not replace the primary result.",
        },
        "convergence": {
            "warning_count": int(predictions["convergence_warnings"].sum()),
            "fits_with_warnings": int((predictions["convergence_warnings"] > 0).sum()),
        },
        "provenance": {
            "bootstrap_seed": int(config["bootstrap_seed"]) + 1,
            "config_file_sha256": sha256_file(config_path),
            "protocol_lock_sha256": sha256_file(LOCK_PATH),
            "g3_feature_lock_sha256": sha256_file(G3_PATH),
            "g4_prediction_lock_sha256": sha256_file(G4_PATH),
            "prediction_sha256": sha256_file(predictions_path),
            "prediction_manifest_sha256": sha256_file(Path(predictions_path).with_suffix(".manifest.json")),
            "implementation_revision": protocol["implementation_revision_at_lock"],
        },
    }
    target = Path(output_path)
    write_json(target, result)
    bootstrap_path = target.with_name(f"{target.stem}.bootstrap_delta_auroc.npy")
    np.save(
        bootstrap_path,
        np.asarray(bootstrap, dtype=np.float64),
    )
    write_json(
        target.with_suffix(".manifest.json"),
        {
            "analysis_key": "update_transport",
            "output_sha256": sha256_file(target),
            "prediction_sha256": sha256_file(predictions_path),
            "g4_prediction_lock_sha256": sha256_file(G4_PATH),
            "bootstrap_sha256": sha256_file(bootstrap_path),
        },
    )
    return result
