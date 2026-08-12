from __future__ import annotations

from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import ndtri
from sklearn.metrics import roc_auc_score

from mammal_dili.config import validate_config
from mammal_dili.io import write_json


def _paired_scores(
    rng: np.random.Generator,
    n: int,
    prevalence: float,
    baseline_auc: float,
    delta_auc: float,
    correlation: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    y = rng.binomial(1, prevalence, n)
    if y.min() == y.max():
        return _paired_scores(rng, n, prevalence, baseline_auc, delta_auc, correlation)
    separation_b = np.sqrt(2.0) * ndtri(baseline_auc)
    separation_d = np.sqrt(2.0) * ndtri(baseline_auc + delta_auc)
    shared = rng.normal(size=n)
    independent = rng.normal(size=n)
    score_b = separation_b * y + shared
    score_d = separation_d * y + correlation * shared + np.sqrt(1 - correlation**2) * independent
    return y, score_b, score_d


def _group_bootstrap_ci(
    rng: np.random.Generator,
    y: np.ndarray,
    score_b: np.ndarray,
    score_d: np.ndarray,
    groups: np.ndarray,
    resamples: int,
) -> tuple[float, float]:
    unique = np.unique(groups)
    deltas = []
    for _ in range(resamples):
        selected = rng.choice(unique, size=len(unique), replace=True)
        indices = np.concatenate([np.flatnonzero(groups == group) for group in selected])
        if np.unique(y[indices]).size == 2:
            deltas.append(
                roc_auc_score(y[indices], score_d[indices])
                - roc_auc_score(y[indices], score_b[indices])
            )
    return tuple(float(value) for value in np.percentile(deltas, [2.5, 97.5]))


def simulate_precision(output_path: str | Path) -> dict:
    seeds = validate_config("configs/seeds.yaml")
    rng = np.random.default_rng(int(seeds["negative_control"]))
    rows = []
    for n, prevalence, correlation, true_delta in product(
        [400, 820], [0.50, 0.63], [0.70, 0.90], [0.00, 0.03]
    ):
        intervals = []
        estimates = []
        group_count = round(n * 572 / 820)
        groups = np.arange(n) % group_count
        for _ in range(50):
            y, score_b, score_d = _paired_scores(
                rng, n, prevalence, 0.75, true_delta, correlation
            )
            estimates.append(roc_auc_score(y, score_d) - roc_auc_score(y, score_b))
            intervals.append(_group_bootstrap_ci(rng, y, score_b, score_d, groups, 50))
        rows.append(
            {
                "n": n,
                "groups": group_count,
                "prevalence": prevalence,
                "baseline_auc": 0.75,
                "score_correlation": correlation,
                "true_delta_auc": true_delta,
                "mean_estimated_delta": float(np.mean(estimates)),
                "mean_ci_width": float(np.mean([upper - lower for lower, upper in intervals])),
                "empirical_coverage": float(
                    np.mean([lower <= true_delta <= upper for lower, upper in intervals])
                ),
                "experiments": 50,
                "group_bootstrap_resamples_per_experiment": 50,
            }
        )
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(target, index=False)
    result = {
        "status": "COMPLETED_BEFORE_MODEL_PERFORMANCE_INSPECTION",
        "seed": int(seeds["negative_control"]),
        "scenarios": len(rows),
        "minimum_empirical_coverage": min(row["empirical_coverage"] for row in rows),
        "maximum_mean_ci_width": max(row["mean_ci_width"] for row in rows),
        "note": (
            "Planning simulation only. It did not use empirical model predictions and did not alter "
            "the locked five-repeat, five-fold, 2,000-resample analysis."
        ),
    }
    write_json(target.with_suffix(".summary.json"), result)
    return result
