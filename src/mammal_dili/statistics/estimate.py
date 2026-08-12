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
from mammal_dili.io import write_json


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
    if upper < delta:
        return "important_gain_excluded", "The pre-specified important gain is excluded."
    return "small_gain", "A positive gain is supported but remains below the practical benchmark."


def estimate_results(predictions_path: str | Path, config_path: str | Path, output_path: str | Path) -> dict:
    config = validate_config(config_path)
    predictions = pd.read_csv(predictions_path)
    repeat_metrics = []
    for (model, repeat), frame in predictions.groupby(["model", "repeat"]):
        repeat_metrics.append({"model": model, "repeat": int(repeat), **_metrics(frame)})
    repeat_frame = pd.DataFrame(repeat_metrics)
    summary = repeat_frame.groupby("model").mean(numeric_only=True).drop(columns=["repeat"]).to_dict(orient="index")
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
        "scope": "Drug-level DILIrank 2.0 concern classification; not patient-level risk or clinical validation.",
    }
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    write_json(target, result)
    repeat_frame.to_csv(target.with_name("repeat_metrics.csv"), index=False)
    np.save(target.with_name("bootstrap_delta_auroc.npy"), np.asarray(bootstrap, dtype=np.float64))
    return result
