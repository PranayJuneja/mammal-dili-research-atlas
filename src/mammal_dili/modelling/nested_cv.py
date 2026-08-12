from __future__ import annotations

import hashlib
import json
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
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from mammal_dili.config import validate_config
from mammal_dili.gates import G3_PATH, require_feature_fold_lock
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


def validation_group_vectors(
    frame: pd.DataFrame, validation_design: str
) -> tuple[np.ndarray, np.ndarray]:
    """Return (chemical groups for reporting/bootstrap, groups used for splitting)."""
    chemical_groups = frame["scaffold_id"].astype(str).to_numpy()
    if validation_design == "scaffold_grouped":
        return chemical_groups, chemical_groups
    if validation_design == "stratified_random":
        return chemical_groups, frame["drug_id"].astype(str).to_numpy()
    raise ValueError(f"Unknown validation design: {validation_design}")


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
                    tol=float(config["tolerance"]),
                    fit_intercept=bool(config["fit_intercept"]),
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
    population: str = "primary",
    model_names: tuple[str, ...] = ("A", "B", "C", "D"),
    validation_design: str = "scaffold_grouped",
    class_weight_mode: str = "primary",
) -> pd.DataFrame:
    protocol_lock = require_protocol_lock()
    g3 = require_feature_fold_lock()
    config = validate_config(config_path)
    expected_hashes = g3["source_hashes"]
    actual_inputs = {
        "development_folds": sha256_file(folds_path),
        "conventional": sha256_file(conventional_path),
        "mammal": sha256_file(mammal_path),
    }
    for name, actual in actual_inputs.items():
        if actual != expected_hashes[name]:
            raise AssertionError(f"Nested CV input is not the G3-locked {name} artifact")
    if class_weight_mode == "balanced_robustness":
        config["class_weight"] = config["robustness_class_weight"]
    elif class_weight_mode != "primary":
        raise ValueError(f"Unknown class-weight mode: {class_weight_mode}")
    folds_config = validate_config("configs/folds.yaml")
    seeds = validate_config("configs/seeds.yaml")
    config = {**config, "inner_folds": folds_config["inner_folds"], "classifier_seed": seeds["classifier"]}
    frame = pd.read_csv(folds_path)
    conventional_ids = set(np.load(conventional_path)["drug_ids"].astype(str))
    mammal_ids = set(np.load(mammal_path)["drug_ids"].astype(str))
    common = conventional_ids & mammal_ids
    frame = frame[frame["drug_id"].astype(str).isin(common)].copy().reset_index(drop=True)
    development, update = split_development_and_update(frame)
    frame = development.reset_index(drop=True)
    if population == "vmost_vs_vno":
        frame = frame[
            frame["dili_category"].str.startswith("vMost")
            | frame["dili_category"].str.startswith("vNo")
        ].reset_index(drop=True)
    elif population != "primary":
        raise ValueError(f"Unknown analysis population: {population}")
    drug_ids = frame["drug_id"].astype(str).tolist()
    y = frame["outcome"].astype(int).to_numpy()
    chemical_groups, split_groups = validation_group_vectors(frame, validation_design)
    if validation_design == "stratified_random":
        for repeat, seed in enumerate(folds_config["seeds"]):
            column = f"random_outer_fold_repeat_{repeat}"
            frame[column] = -1
            splitter = StratifiedKFold(
                n_splits=int(folds_config["outer_folds"]),
                shuffle=True,
                random_state=int(seed),
            )
            for fold, (_, test_indices) in enumerate(splitter.split(frame, y)):
                frame.loc[test_indices, column] = fold
    outputs = []
    tuning_log = []
    fold_prefix = (
        "outer_fold_repeat_"
        if validation_design == "scaffold_grouped"
        else "random_outer_fold_repeat_"
    )
    repeat_columns = sorted(
        (column for column in frame if column.startswith(fold_prefix)),
        key=lambda column: int(column.rsplit("_", 1)[1]),
    )
    for model_name in model_names:
        feature_set = load_feature_set(model_name, drug_ids, conventional_path, mammal_path)
        for repeat, fold_column in enumerate(repeat_columns):
            for outer_fold in sorted(frame[fold_column].unique()):
                test_indices = np.flatnonzero(frame[fold_column].to_numpy() == outer_fold)
                train_indices = np.flatnonzero(frame[fold_column].to_numpy() != outer_fold)
                best_c, inner_oof, candidates = _inner_tune(
                    feature_set,
                    train_indices,
                    y,
                    split_groups,
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
                            "scaffold_id": chemical_groups[index],
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
    expected = len(frame) * len(repeat_columns) * len(model_names)
    if len(result) != expected:
        raise AssertionError(f"Expected {expected} predictions, found {len(result)}")
    if {"B", "D"}.issubset(model_names):
        pairing = (
            result[result["model"].isin(["B", "D"])]
            .groupby(["drug_id", "repeat"])["model"]
            .nunique()
        )
        if not (pairing == 2).all():
            raise AssertionError("Models B and D do not have identical paired prediction coverage")
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(target, index=False)
    frame[["drug_id", *repeat_columns]].to_csv(target.with_suffix(".folds.csv"), index=False)
    write_json(target.with_suffix(".tuning.json"), tuning_log)
    write_json(
        target.with_suffix(".manifest.json"),
        {
            "prediction_rows": len(result),
            "drugs": len(frame),
            "analysis_population": "eligible original-list development cohort",
            "update_cohort_held_out_drugs": len(update),
            "update_cohort_drug_ids_sha256": hashlib.sha256(
                "\n".join(sorted(update["drug_id"].astype(str))).encode("utf-8")
            ).hexdigest(),
            "models": list(model_names),
            "population": population,
            "validation_design": validation_design,
            "class_weight_mode": class_weight_mode,
            "analysis_folds_sha256": sha256_file(target.with_suffix(".folds.csv")),
            "repeats": len(repeat_columns),
            "folds_sha256": sha256_file(folds_path),
            "conventional_features_sha256": sha256_file(conventional_path),
            "mammal_features_sha256": sha256_file(mammal_path),
            "prediction_sha256": sha256_file(target),
            "output_sha256": sha256_file(target),
            "tuning_sha256": sha256_file(target.with_suffix(".tuning.json")),
            "config_file_sha256": sha256_file(config_path),
            "g3_feature_lock_sha256": sha256_file(G3_PATH),
            "implementation_revision": protocol_lock["implementation_revision_at_lock"],
            "protocol_lock_sha256": sha256_file("audit/protocol_lock/execution_lock.json"),
            "protocol_config_bundle_sha256": protocol_lock["config_bundle_sha256"],
        },
    )
    return result


def run_update_transport(
    development_folds_path: str | Path,
    update_groups_path: str | Path,
    conventional_path: str | Path,
    mammal_path: str | Path,
    development_predictions_path: str | Path,
    config_path: str | Path,
    output_path: str | Path,
) -> pd.DataFrame:
    """Fit once on the original-list development cohort and evaluate the untouched update cohort."""
    protocol_lock = require_protocol_lock()
    g3 = require_feature_fold_lock()
    config = validate_config(config_path)
    expected_hashes = g3["source_hashes"]
    actual_inputs = {
        "development_folds": sha256_file(development_folds_path),
        "update_groups": sha256_file(update_groups_path),
        "conventional": sha256_file(conventional_path),
        "mammal": sha256_file(mammal_path),
    }
    for name, actual in actual_inputs.items():
        if actual != expected_hashes[name]:
            raise AssertionError(f"Update evaluation input is not the G3-locked {name} artifact")
    seeds = validate_config("configs/seeds.yaml")
    config = {**config, "classifier_seed": seeds["classifier"]}
    development = pd.read_csv(development_folds_path)
    if set(development["release_group"]) != {config["development_release_group"]}:
        raise AssertionError("Development fold artefact contains non-original rows")
    conventional_ids = set(np.load(conventional_path)["drug_ids"].astype(str))
    mammal_ids = set(np.load(mammal_path)["drug_ids"].astype(str))
    common = conventional_ids & mammal_ids
    development = development[development["drug_id"].astype(str).isin(common)].reset_index(drop=True)
    predictions = pd.read_csv(development_predictions_path)
    development_ids = development["drug_id"].astype(str).tolist()
    models = ["A", "B", "C", "D"]
    repeats = list(range(5))
    outer_folds = list(range(5))
    if set(predictions["drug_id"].astype(str)) != set(development_ids):
        raise AssertionError("Development OOF predictions do not exactly match original-list cohort")
    if set(predictions["release_group"]) != {"original-list"}:
        raise AssertionError("Update-cohort rows leaked into development predictions")
    prediction_keys = predictions[["drug_id", "model", "repeat"]]
    if (
        len(predictions) != len(development) * len(models) * len(repeats)
        or prediction_keys.duplicated().any()
        or set(predictions["model"]) != set(models)
        or set(predictions["repeat"].astype(int)) != set(repeats)
    ):
        raise AssertionError("Primary development prediction coverage is not exact 4-model x 5-repeat")
    tuning_path = Path(development_predictions_path).with_suffix(".tuning.json")
    development_manifest_path = Path(development_predictions_path).with_suffix(".manifest.json")
    development_manifest = json.loads(development_manifest_path.read_text(encoding="utf-8"))
    if development_manifest.get("prediction_sha256") != sha256_file(development_predictions_path):
        raise AssertionError("Development prediction manifest does not bind the current predictions")
    if development_manifest.get("tuning_sha256") != sha256_file(tuning_path):
        raise AssertionError("Development tuning artifact is stale or unrelated")
    if development_manifest.get("g3_feature_lock_sha256") != sha256_file(G3_PATH):
        raise AssertionError("Development predictions were not generated from the accepted G3 lock")
    tuning = json.loads(tuning_path.read_text(encoding="utf-8"))
    tuning_keys = {
        (str(row["model"]), int(row["repeat"]), int(row["outer_fold"]))
        for row in tuning
    }
    expected_tuning_keys = {
        (model, repeat, fold)
        for model in models
        for repeat in repeats
        for fold in outer_folds
    }
    if len(tuning) != len(expected_tuning_keys) or tuning_keys != expected_tuning_keys:
        raise AssertionError("Primary tuning must have unique complete 4-model x 5-repeat x 5-fold coverage")
    if any(float(row["selected_c"]) not in config["regularization_grid"] for row in tuning):
        raise AssertionError("Primary tuning selected C outside the locked grid")

    # Only after the complete development prediction/tuning contract passes may update outcomes load.
    update = pd.read_csv(update_groups_path)
    if set(update["release_group"]) != {config["update_release_group"]}:
        raise AssertionError("Update group artefact contains non-update rows")
    update = update[update["drug_id"].astype(str).isin(common)].reset_index(drop=True)
    outputs = []
    selected = {}
    for model_name in models:
        model_tuning = [row for row in tuning if row["model"] == model_name]
        if len(model_tuning) != int(config["required_outer_selection_count"]):
            raise AssertionError(f"Expected {config['required_outer_selection_count']} tuning selections for {model_name}")
        counts = pd.Series([float(row["selected_c"]) for row in model_tuning]).value_counts()
        most_frequent = counts[counts == counts.max()].index.astype(float).tolist()
        selected_c = min(most_frequent)
        selected[model_name] = {
            "rule": config["final_hyperparameter_rule"],
            "C": selected_c,
            "outer_selection_counts": {str(key): int(value) for key, value in counts.items()},
        }
        update_ids = update["drug_id"].astype(str).tolist()
        all_ids = development_ids + update_ids
        feature_set = load_feature_set(model_name, all_ids, conventional_path, mammal_path)
        development_indices = np.arange(len(development_ids))
        update_indices = np.arange(len(development_ids), len(all_ids))
        y_development = development["outcome"].astype(int).to_numpy()
        pipeline = _pipeline(feature_set, selected_c, config)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", ConvergenceWarning)
            pipeline.fit(feature_set.values[development_indices], y_development)
            convergence = sum(issubclass(item.category, ConvergenceWarning) for item in caught)
        model_oof = predictions[predictions["model"] == model_name]
        average_oof = (
            model_oof.groupby("drug_id", as_index=False)["predicted_probability"].mean()
        )
        ordered_oof = development[["drug_id", "outcome"]].merge(
            average_oof, on="drug_id", how="left", validate="one_to_one"
        )
        if ordered_oof["predicted_probability"].isna().any():
            raise AssertionError("Development OOF probabilities are incomplete")
        youden, sensitivity = _thresholds(
            ordered_oof["outcome"].to_numpy(dtype=int),
            ordered_oof["predicted_probability"].to_numpy(dtype=float),
            float(config["sensitivity_target"]),
        )
        probabilities = pipeline.predict_proba(feature_set.values[update_indices])[:, 1]
        for index, probability in enumerate(probabilities):
            outputs.append(
                {
                    "drug_id": update.loc[index, "drug_id"],
                    "compound_name_source": update.loc[index, "compound_name_source"],
                    "dili_category": update.loc[index, "dili_category"],
                    "outcome": int(update.loc[index, "outcome"]),
                    "scaffold_id": update.loc[index, "scaffold_id"],
                    "release_group": update.loc[index, "release_group"],
                    "model": model_name,
                    "predicted_probability": float(probability),
                    "selected_c": selected_c,
                    "youden_threshold": youden,
                    "sensitivity_threshold": sensitivity,
                    "convergence_warnings": convergence,
                }
            )
    result = pd.DataFrame(outputs)
    if len(result) != len(update) * 4:
        raise AssertionError("Update prediction coverage is incomplete")
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(target, index=False)
    write_json(
        target.with_suffix(".manifest.json"),
        {
            "design": "single untouched update-cohort transport after original-list development",
            "development_drugs": len(development),
            "update_drugs": len(update),
            "prediction_rows": len(result),
            "selected_hyperparameters": selected,
            "development_predictions_sha256": sha256_file(development_predictions_path),
            "development_tuning_sha256": sha256_file(tuning_path),
            "development_manifest_sha256": sha256_file(development_manifest_path),
            "development_folds_sha256": sha256_file(development_folds_path),
            "update_groups_sha256": sha256_file(update_groups_path),
            "conventional_features_sha256": sha256_file(conventional_path),
            "mammal_features_sha256": sha256_file(mammal_path),
            "output_sha256": sha256_file(target),
            "config_file_sha256": sha256_file(config_path),
            "g3_feature_lock_sha256": sha256_file(G3_PATH),
            "implementation_revision": protocol_lock["implementation_revision_at_lock"],
            "protocol_lock_sha256": sha256_file("audit/protocol_lock/execution_lock.json"),
            "protocol_config_bundle_sha256": protocol_lock["config_bundle_sha256"],
        },
    )
    return result
