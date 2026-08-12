from __future__ import annotations

import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from mammal_dili.config import validate_config
from mammal_dili.io import sha256_file, write_json
from mammal_dili.lock import require_protocol_lock


@dataclass(frozen=True)
class FeatureSet:
    values: np.ndarray
    continuous_indices: list[int]


def split_development_and_update(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Keep the 300-drug update cohort completely outside development fitting."""
    development = frame[frame["release_group"] == "original-list"].copy()
    update = frame[frame["release_group"] == "added-in-2.0"].copy()
    if set(development["drug_id"]) & set(update["drug_id"]):
        raise AssertionError("Development and update cohorts overlap")
    if len(development) + len(update) != len(frame):
        raise AssertionError("Unrecognised release-group value")
    return development, update


def _matrix_map(path: str | Path, key: str) -> dict[str, np.ndarray]:
    data = np.load(path)
    return dict(zip(data["drug_ids"].astype(str), data[key], strict=True))


def load_feature_set(
    model: str,
    drug_ids: list[str],
    conventional_path: str | Path,
    mammal_path: str | Path,
) -> FeatureSet:
    conventional = np.load(conventional_path)
    descriptor_map = dict(
        zip(conventional["drug_ids"].astype(str), conventional["descriptors"], strict=True)
    )
    morgan_map = dict(zip(conventional["drug_ids"].astype(str), conventional["morgan"], strict=True))
    mammal_map = _matrix_map(mammal_path, "embeddings")
    descriptor_dim = conventional["descriptors"].shape[1]
    mammal_dim = next(iter(mammal_map.values())).shape[0]
    if model == "A":
        values = np.vstack([descriptor_map[key] for key in drug_ids])
        return FeatureSet(values, list(range(descriptor_dim)))
    if model == "B":
        values = np.vstack([np.concatenate([descriptor_map[key], morgan_map[key]]) for key in drug_ids])
        return FeatureSet(values, list(range(descriptor_dim)))
    if model == "C":
        values = np.vstack([mammal_map[key] for key in drug_ids])
        return FeatureSet(values, list(range(mammal_dim)))
    if model == "D":
        values = np.vstack(
            [np.concatenate([descriptor_map[key], morgan_map[key], mammal_map[key]]) for key in drug_ids]
        )
        continuous = list(range(descriptor_dim)) + list(
            range(descriptor_dim + conventional["morgan"].shape[1], values.shape[1])
        )
        return FeatureSet(values, continuous)
    raise ValueError(f"Unknown model {model}")


def _pipeline(feature_set: FeatureSet, c_value: float, config: dict) -> Pipeline:
    all_indices = set(range(feature_set.values.shape[1]))
    continuous = sorted(feature_set.continuous_indices)
    binary = sorted(all_indices - set(continuous))
    transformers = []
    if continuous:
        transformers.append(
            (
                "continuous",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="median")),
                        ("scale", StandardScaler()),
                    ]
                ),
                continuous,
            )
        )
    if binary:
        transformers.append(("binary", "passthrough", binary))
    return Pipeline(
        [
            ("features", ColumnTransformer(transformers, sparse_threshold=0)),
            (
                "classifier",
                LogisticRegression(
                    penalty="l2",
                    solver=config["solver"],
                    C=float(c_value),
                    class_weight=config["class_weight"],
                    max_iter=int(config["max_iterations"]),
                    random_state=int(config["classifier_seed"]),
                ),
            ),
        ]
    )


def _thresholds(y_true: np.ndarray, probabilities: np.ndarray, sensitivity_target: float) -> tuple[float, float]:
    false_positive, true_positive, thresholds = roc_curve(y_true, probabilities)
    youden = thresholds[int(np.argmax(true_positive - false_positive))]
    feasible = np.where(true_positive >= sensitivity_target)[0]
    sensitivity_threshold = thresholds[feasible[np.argmin(false_positive[feasible])]] if len(feasible) else 0.0
    return float(youden), float(sensitivity_threshold)


def _inner_tune(
    feature_set: FeatureSet,
    train_indices: np.ndarray,
    y: np.ndarray,
    groups: np.ndarray,
    config: dict,
    seed: int,
) -> tuple[float, np.ndarray, list[dict]]:
    inner = StratifiedGroupKFold(n_splits=int(config["inner_folds"]), shuffle=True, random_state=seed)
    candidates = []
    best_score = -np.inf
    best_c = None
    best_oof = None
    for c_value in sorted(float(value) for value in config["regularization_grid"]):
        oof = np.full(len(train_indices), np.nan, dtype=float)
        convergence_warnings = 0
        local_y = y[train_indices]
        local_groups = groups[train_indices]
        for inner_train, inner_valid in inner.split(feature_set.values[train_indices], local_y, local_groups):
            pipeline = _pipeline(feature_set, c_value, config)
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", ConvergenceWarning)
                pipeline.fit(feature_set.values[train_indices[inner_train]], local_y[inner_train])
                convergence_warnings += sum(issubclass(item.category, ConvergenceWarning) for item in caught)
            oof[inner_valid] = pipeline.predict_proba(feature_set.values[train_indices[inner_valid]])[:, 1]
        if np.isnan(oof).any():
            raise AssertionError("Inner out-of-fold probabilities are incomplete")
        score = float(roc_auc_score(local_y, oof))
        candidates.append({"C": c_value, "inner_auroc": score, "convergence_warnings": convergence_warnings})
        if score > best_score + 1e-12:
            best_score = score
            best_c = c_value
            best_oof = oof
    assert best_c is not None and best_oof is not None
    return best_c, best_oof, candidates


def run_nested_cv(
    folds_path: str | Path,
    conventional_path: str | Path,
    mammal_path: str | Path,
    config_path: str | Path,
    output_path: str | Path,
) -> pd.DataFrame:
    protocol_lock = require_protocol_lock()
    config = validate_config(config_path)
    folds_config = validate_config("configs/folds.yaml")
    seeds = validate_config("configs/seeds.yaml")
    config = {**config, "inner_folds": folds_config["inner_folds"], "classifier_seed": seeds["classifier"]}
    frame = pd.read_csv(folds_path)
    conventional_ids = set(np.load(conventional_path)["drug_ids"].astype(str))
    mammal_ids = set(np.load(mammal_path)["drug_ids"].astype(str))
    common = conventional_ids & mammal_ids
    frame = frame[frame["drug_id"].astype(str).isin(common)].copy().reset_index(drop=True)
    drug_ids = frame["drug_id"].astype(str).tolist()
    y = frame["outcome"].astype(int).to_numpy()
    groups = frame["scaffold_id"].astype(str).to_numpy()
    outputs = []
    tuning_log = []
    repeat_columns = sorted(
        (column for column in frame if column.startswith("outer_fold_repeat_")),
        key=lambda column: int(column.rsplit("_", 1)[1]),
    )
    for model_name in ["A", "B", "C", "D"]:
        feature_set = load_feature_set(model_name, drug_ids, conventional_path, mammal_path)
        for repeat, fold_column in enumerate(repeat_columns):
            for outer_fold in sorted(frame[fold_column].unique()):
                test_indices = np.flatnonzero(frame[fold_column].to_numpy() == outer_fold)
                train_indices = np.flatnonzero(frame[fold_column].to_numpy() != outer_fold)
                best_c, inner_oof, candidates = _inner_tune(
                    feature_set,
                    train_indices,
                    y,
                    groups,
                    config,
                    seed=int(seeds["inner_cv_base"]) + repeat * 10 + int(outer_fold),
                )
                youden, sensitivity = _thresholds(
                    y[train_indices], inner_oof, float(config["sensitivity_target"])
                )
                pipeline = _pipeline(feature_set, best_c, config)
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter("always", ConvergenceWarning)
                    pipeline.fit(feature_set.values[train_indices], y[train_indices])
                    convergence = sum(issubclass(item.category, ConvergenceWarning) for item in caught)
                probabilities = pipeline.predict_proba(feature_set.values[test_indices])[:, 1]
                for index, probability in zip(test_indices, probabilities, strict=True):
                    outputs.append(
                        {
                            "drug_id": drug_ids[index],
                            "compound_name_source": frame.loc[index, "compound_name_source"],
                            "dili_category": frame.loc[index, "dili_category"],
                            "outcome": int(y[index]),
                            "scaffold_id": groups[index],
                            "release_group": frame.loc[index, "release_group"],
                            "model": model_name,
                            "repeat": repeat,
                            "outer_fold": int(outer_fold),
                            "predicted_probability": float(probability),
                            "selected_c": best_c,
                            "youden_threshold": youden,
                            "sensitivity_threshold": sensitivity,
                            "convergence_warnings": convergence,
                        }
                    )
                tuning_log.append(
                    {
                        "model": model_name,
                        "repeat": repeat,
                        "outer_fold": int(outer_fold),
                        "selected_c": best_c,
                        "candidates": candidates,
                    }
                )
    result = pd.DataFrame(outputs)
    expected = len(frame) * len(repeat_columns) * 4
    if len(result) != expected:
        raise AssertionError(f"Expected {expected} predictions, found {len(result)}")
    pairing = result[result["model"].isin(["B", "D"])].groupby(["drug_id", "repeat"])["model"].nunique()
    if not (pairing == 2).all():
        raise AssertionError("Models B and D do not have identical paired prediction coverage")
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(target, index=False)
    write_json(target.with_suffix(".tuning.json"), tuning_log)
    write_json(
        target.with_suffix(".manifest.json"),
        {
            "prediction_rows": len(result),
            "drugs": len(frame),
            "models": 4,
            "repeats": len(repeat_columns),
            "folds_sha256": sha256_file(folds_path),
            "conventional_features_sha256": sha256_file(conventional_path),
            "mammal_features_sha256": sha256_file(mammal_path),
            "prediction_sha256": sha256_file(target),
            "protocol_lock_sha256": sha256_file("audit/protocol_lock/execution_lock.json"),
            "protocol_config_bundle_sha256": protocol_lock["config_bundle_sha256"],
        },
    )
    return result
