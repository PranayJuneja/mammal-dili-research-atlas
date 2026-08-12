from __future__ import annotations

from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import ndtri
from scipy.stats import rankdata

from mammal_dili.config import validate_config
from mammal_dili.io import sha256_file, write_json


def _repeated_paired_scores(
    rng: np.random.Generator,
    n: int,
    prevalence: float,
    baseline_auc: float,
    delta_auc: float,
    correlation: float,
    repeats: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    y = rng.binomial(1, prevalence, n)
    if y.min() == y.max():
        return _repeated_paired_scores(
            rng, n, prevalence, baseline_auc, delta_auc, correlation, repeats
        )
    separation_b = np.sqrt(2.0) * ndtri(baseline_auc)
    separation_d = np.sqrt(2.0) * ndtri(baseline_auc + delta_auc)
    stable_latent = rng.normal(size=n)
    scores_b = []
    scores_d = []
    for _ in range(repeats):
        repeat_noise = rng.normal(scale=0.15, size=n)
        shared = stable_latent + repeat_noise
        independent = rng.normal(size=n)
        scores_b.append(separation_b * y + shared)
        scores_d.append(
            separation_d * y
            + correlation * shared
            + np.sqrt(1 - correlation**2) * independent
        )
    return y, np.asarray(scores_b), np.asarray(scores_d)


def _mean_repeat_delta(y: np.ndarray, score_b: np.ndarray, score_d: np.ndarray) -> float:
    def auc(values: np.ndarray) -> float:
        positives = y == 1
        n_positive = int(positives.sum())
        n_negative = len(y) - n_positive
        ranks = rankdata(values)
        return float(
            (ranks[positives].sum() - n_positive * (n_positive + 1) / 2)
            / (n_positive * n_negative)
        )

    return float(
        np.mean(
            [
                auc(values_d) - auc(values_b)
                for values_b, values_d in zip(score_b, score_d, strict=True)
            ]
        )
    )


def _group_bootstrap(
    rng: np.random.Generator,
    y: np.ndarray,
    score_b: np.ndarray,
    score_d: np.ndarray,
    groups: np.ndarray,
    resamples: int,
) -> np.ndarray:
    unique = np.unique(groups)
    group_rows = {group: np.flatnonzero(groups == group) for group in unique}
    deltas = []
    for _ in range(resamples):
        selected = rng.choice(unique, size=len(unique), replace=True)
        indices = np.concatenate([group_rows[group] for group in selected])
        if np.unique(y[indices]).size == 2:
            deltas.append(_mean_repeat_delta(y[indices], score_b[:, indices], score_d[:, indices]))
    return np.asarray(deltas, dtype=np.float64)


def _observed_group_vectors(folds: pd.DataFrame, rng: np.random.Generator) -> dict[str, np.ndarray]:
    full = folds["scaffold_id"].astype(str).to_numpy()
    unique = np.unique(full)
    selected = rng.permutation(unique)
    chosen = []
    rows = 0
    target = len(full) // 2
    sizes = pd.Series(full).value_counts()
    for group in selected:
        chosen.append(group)
        rows += int(sizes[group])
        if rows >= target:
            break
    reduced = folds[folds["scaffold_id"].astype(str).isin(chosen)]["scaffold_id"].astype(str).to_numpy()
    return {"observed_full": full, "observed_half_groups": reduced}


def simulate_precision(
    output_path: str | Path,
    folds_path: str | Path = "artifacts/folds/outer_folds.csv",
) -> dict:
    seeds = validate_config("configs/seeds.yaml")
    analysis = validate_config("configs/analysis.yaml")
    fold_config = validate_config("configs/folds.yaml")
    rng = np.random.default_rng(int(seeds["negative_control"]))
    folds = pd.read_csv(folds_path)
    group_vectors = _observed_group_vectors(folds, rng)
    observed_prevalence = float(folds["outcome"].mean())
    coverage_resamples = 100
    full_resamples = int(analysis["bootstrap_resamples"])
    experiments = 40
    repeats = int(fold_config["repeats"])
    rows = []
    for (size_scenario, groups), prevalence, correlation, true_delta in product(
        group_vectors.items(),
        [0.50, observed_prevalence],
        [0.70, 0.90],
        [0.00, float(analysis["practical_gain"])],
    ):
        intervals = []
        estimates = []
        representative = None
        for experiment in range(experiments):
            y, score_b, score_d = _repeated_paired_scores(
                rng, len(groups), prevalence, 0.75, true_delta, correlation, repeats
            )
            estimates.append(_mean_repeat_delta(y, score_b, score_d))
            draws = _group_bootstrap(
                rng, y, score_b, score_d, groups, coverage_resamples
            )
            intervals.append(tuple(np.percentile(draws, [2.5, 97.5])))
            if experiment == 0:
                representative = (y, score_b, score_d)
        assert representative is not None
        full_draws = _group_bootstrap(rng, *representative, groups, full_resamples)
        full_ci = np.percentile(full_draws, [2.5, 97.5])
        prefix_ci = np.percentile(full_draws[:coverage_resamples], [2.5, 97.5])
        group_sizes = pd.Series(groups).value_counts()
        rows.append(
            {
                "size_scenario": size_scenario,
                "n": len(groups),
                "groups": int(group_sizes.size),
                "largest_group": int(group_sizes.max()),
                "median_group_size": float(group_sizes.median()),
                "prevalence": prevalence,
                "baseline_auc": 0.75,
                "score_correlation": correlation,
                "true_delta_auc": true_delta,
                "repeated_cv_prediction_sets": repeats,
                "mean_estimated_delta": float(np.mean(estimates)),
                "mean_ci_width": float(np.mean([upper - lower for lower, upper in intervals])),
                "empirical_coverage": float(
                    np.mean([lower <= true_delta <= upper for lower, upper in intervals])
                ),
                "coverage_experiments": experiments,
                "coverage_resamples_per_experiment": coverage_resamples,
                "full_bootstrap_resamples": full_resamples,
                "full_bootstrap_ci_lower": float(full_ci[0]),
                "full_bootstrap_ci_upper": float(full_ci[1]),
                "max_endpoint_shift_100_to_2000": float(np.max(np.abs(full_ci - prefix_ci))),
            }
        )
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(target, index=False)
    result = {
        "status": "COMPLETED_BEFORE_MODEL_PERFORMANCE_INSPECTION",
        "seed": int(seeds["negative_control"]),
        "folds_sha256": sha256_file(folds_path),
        "observed_rows": len(folds),
        "observed_groups": int(folds["scaffold_id"].nunique()),
        "observed_largest_group": int(folds["scaffold_id"].value_counts().max()),
        "repeated_cv_prediction_sets": repeats,
        "scenarios": len(rows),
        "coverage_experiments_per_scenario": experiments,
        "coverage_bootstrap_resamples": coverage_resamples,
        "locked_full_bootstrap_resamples": full_resamples,
        "minimum_empirical_coverage": min(row["empirical_coverage"] for row in rows),
        "maximum_mean_ci_width": max(row["mean_ci_width"] for row in rows),
        "maximum_endpoint_shift_100_to_2000": max(
            row["max_endpoint_shift_100_to_2000"] for row in rows
        ),
        "note": (
            "Planning simulation only. It uses the observed group-size distribution and five paired "
            "prediction repeats but no empirical model predictions. Coverage screening uses 100 "
            "resamples across 40 experiments; every scenario also receives the locked 2,000-resample "
            "bootstrap to assess Monte Carlo endpoint stability. No analysis setting was changed."
        ),
    }
    write_json(target.with_suffix(".summary.json"), result)
    return result
