from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import precision_recall_curve, roc_curve

from mammal_dili.gates import (
    G3_PATH,
    G4_PATH,
    PREDICTION_PATHS,
    require_feature_fold_lock,
    require_prediction_lock,
)
from mammal_dili.io import sha256_file, write_json
from mammal_dili.lock import LOCK_PATH

RESULT_PATHS = {
    "primary": Path("artifacts/results/results.json"),
    "update_transport": Path("artifacts/results/update_results.json"),
    "vmost_vs_vno": Path("artifacts/results/vmost_vno_results.json"),
    "stratified_random": Path("artifacts/results/random_split_results.json"),
    "class_balanced": Path("artifacts/results/balanced_results.json"),
}


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _primary_svg(primary: dict) -> str:
    estimate = float(primary["delta_auroc"])
    lower, upper = (float(value) for value in primary["ci95"])
    x_min = min(-0.10, lower - 0.01)
    x_max = max(0.10, upper + 0.01)

    def x(value: float) -> float:
        return 90 + (value - x_min) / (x_max - x_min) * 760

    ticks = np.linspace(x_min, x_max, 9)
    tick_markup = "".join(
        f'<line x1="{x(value):.2f}" y1="172" x2="{x(value):.2f}" y2="180" />'
        f'<text x="{x(value):.2f}" y="202" text-anchor="middle">{value:+.2f}</text>'
        for value in ticks
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="940" height="270" viewBox="0 0 940 270" role="img" aria-labelledby="title desc">
<title id="title">Primary paired change in AUROC</title>
<desc id="desc">Estimate {estimate:+.4f}, 95 percent confidence interval {lower:+.4f} to {upper:+.4f}, practical benchmark plus 0.03.</desc>
<rect width="940" height="270" rx="24" fill="#f4f8f7" />
<text x="54" y="52" fill="#102b35" font-family="sans-serif" font-size="20" font-weight="700">Incremental value of frozen MAMMAL</text>
<text x="54" y="80" fill="#587078" font-family="sans-serif" font-size="14">Paired Model D minus Model B AUROC · repeated scaffold-grouped validation</text>
<g stroke="#9db2b6" fill="#587078" font-family="monospace" font-size="12">
<line x1="90" y1="172" x2="850" y2="172" />{tick_markup}</g>
<line x1="{x(0):.2f}" y1="108" x2="{x(0):.2f}" y2="172" stroke="#36505a" stroke-width="2" />
<line x1="{x(0.03):.2f}" y1="102" x2="{x(0.03):.2f}" y2="172" stroke="#d18b28" stroke-width="2" stroke-dasharray="5 5" />
<text x="{x(0.03):.2f}" y="94" text-anchor="middle" fill="#9a6118" font-family="sans-serif" font-size="12">+0.03 benchmark</text>
<line x1="{x(lower):.2f}" y1="136" x2="{x(upper):.2f}" y2="136" stroke="#167f87" stroke-width="8" stroke-linecap="round" />
<line x1="{x(lower):.2f}" y1="124" x2="{x(lower):.2f}" y2="148" stroke="#167f87" stroke-width="3" />
<line x1="{x(upper):.2f}" y1="124" x2="{x(upper):.2f}" y2="148" stroke="#167f87" stroke-width="3" />
<circle cx="{x(estimate):.2f}" cy="136" r="10" fill="#ef7e65" stroke="#fff" stroke-width="3" />
<text x="470" y="242" text-anchor="middle" fill="#102b35" font-family="sans-serif" font-size="14" font-weight="700">ΔAUROC {estimate:+.3f} (95% CI {lower:+.3f} to {upper:+.3f})</text>
</svg>"""


def _curve_data(predictions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    roc_rows = []
    pr_rows = []
    calibration_rows = []
    for (model, repeat), frame in predictions.groupby(["model", "repeat"]):
        y = frame["outcome"].to_numpy(dtype=int)
        probability = frame["predicted_probability"].to_numpy(dtype=float)
        false_positive, true_positive, _ = roc_curve(y, probability)
        precision, recall, _ = precision_recall_curve(y, probability)
        for index, (fpr, tpr) in enumerate(zip(false_positive, true_positive, strict=True)):
            roc_rows.append(
                {"model": model, "repeat": repeat, "point": index, "fpr": fpr, "tpr": tpr}
            )
        for index, (precision_value, recall_value) in enumerate(
            zip(precision, recall, strict=True)
        ):
            pr_rows.append(
                {
                    "model": model,
                    "repeat": repeat,
                    "point": index,
                    "precision": precision_value,
                    "recall": recall_value,
                }
            )
        observed, predicted = calibration_curve(y, probability, n_bins=10, strategy="quantile")
        for index, (observed_value, predicted_value) in enumerate(
            zip(observed, predicted, strict=True)
        ):
            calibration_rows.append(
                {
                    "model": model,
                    "repeat": repeat,
                    "bin": index,
                    "mean_predicted": predicted_value,
                    "observed_fraction": observed_value,
                }
            )
    return pd.DataFrame(roc_rows), pd.DataFrame(pr_rows), pd.DataFrame(calibration_rows)


def _important_false_negatives(predictions: pd.DataFrame, cohort: pd.DataFrame) -> pd.DataFrame:
    important = predictions[predictions["dili_category"].str.startswith("vMost")].copy()
    important["classified_negative"] = (
        important["predicted_probability"] < important["youden_threshold"]
    )
    important["below_sensitivity_threshold"] = (
        important["predicted_probability"] < important["sensitivity_threshold"]
    )
    summary = (
        important.groupby(
            ["drug_id", "compound_name_source", "dili_category", "scaffold_id", "model"], as_index=False
        )
        .agg(
            mean_probability=("predicted_probability", "mean"),
            minimum_probability=("predicted_probability", "min"),
            negative_repeats=("classified_negative", "sum"),
            sensitivity_negative_repeats=("below_sensitivity_threshold", "sum"),
            repeats=("repeat", "nunique"),
            mean_youden_threshold=("youden_threshold", "mean"),
            mean_sensitivity_threshold=("sensitivity_threshold", "mean"),
            convergence_warnings=("convergence_warnings", "sum"),
        )
    )
    summary["youden_false_negative_persistence"] = summary["negative_repeats"] / summary["repeats"]
    summary["sensitivity_false_negative_persistence"] = summary["sensitivity_negative_repeats"] / summary["repeats"]
    curation_columns = [
        "drug_id", "curation_flags", "review_status", "resolution_method",
        "identity_adjudication", "active_moiety_adjudication",
    ]
    summary = summary.merge(cohort[curation_columns], on="drug_id", how="left", validate="many_to_one")
    summary["training_context"] = (
        "Outer-fold out-of-fold prediction; molecule and its chemical group were absent from that fit."
    )
    summary["therapeutic_class"] = (
        "Not available in the locked DILIrank source; no post hoc class was inferred."
    )
    return summary[summary["negative_repeats"] > 0].sort_values(
        ["negative_repeats", "mean_probability"], ascending=[False, True]
    )


def _repeat_stability_svg(repeat_metrics: pd.DataFrame) -> str:
    rows = repeat_metrics[repeat_metrics["model"].isin(["B", "D"])]
    values = rows["auroc"].to_numpy(float)
    low, high = min(values) - 0.02, max(values) + 0.02
    def x(value: float) -> float:
        return 110 + (value - low) / max(high - low, 1e-9) * 710
    marks = []
    for model, y, colour in [("B", 95, "#365f91"), ("D", 155, "#e77961")]:
        subset = rows[rows["model"] == model].sort_values("repeat")
        marks.append(f'<text x="55" y="{y + 5}" font-family="sans-serif" font-weight="700">{model}</text>')
        marks.extend(
            f'<circle cx="{x(float(row.auroc)):.2f}" cy="{y}" r="7" fill="{colour}"><title>Repeat {int(row.repeat) + 1}: {float(row.auroc):.4f}</title></circle>'
            for row in subset.itertuples()
        )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="880" height="230" viewBox="0 0 880 230" role="img" aria-label="Repeat-level AUROC stability for models B and D">
<rect width="880" height="230" rx="22" fill="#f4f8f7"/><text x="44" y="42" font-family="sans-serif" font-size="18" font-weight="700" fill="#102b35">Repeat-level AUROC stability</text>
<line x1="110" y1="190" x2="820" y2="190" stroke="#9db2b6"/><text x="110" y="215" font-family="monospace" font-size="11">{low:.3f}</text><text x="820" y="215" text-anchor="end" font-family="monospace" font-size="11">{high:.3f}</text>{''.join(marks)}</svg>'''


def _validate_result_lineage(result_path: str | Path, prediction_key: str) -> dict:
    target = Path(result_path)
    if target != RESULT_PATHS[prediction_key]:
        raise AssertionError(f"Report requires the frozen {prediction_key} result path")
    manifest_path = target.with_suffix(".manifest.json")
    manifest = _load_json(manifest_path)
    if manifest.get("output_sha256") != sha256_file(target):
        raise AssertionError(f"Stale result manifest: {target}")
    if manifest.get("prediction_sha256") != sha256_file(PREDICTION_PATHS[prediction_key]):
        raise AssertionError(f"Result is not bound to current {prediction_key} predictions")
    if manifest.get("g4_prediction_lock_sha256") != sha256_file(G4_PATH):
        raise AssertionError(f"Result was not produced from the accepted G4 lock: {target}")
    bootstrap_path = target.with_name(f"{target.stem}.bootstrap_delta_auroc.npy")
    if manifest.get("bootstrap_sha256") != sha256_file(bootstrap_path):
        raise AssertionError(f"Result bootstrap companion is stale: {target}")
    if prediction_key != "update_transport":
        repeat_metrics_path = target.with_name(f"{target.stem}.repeat_metrics.csv")
        if manifest.get("repeat_metrics_sha256") != sha256_file(repeat_metrics_path):
            raise AssertionError(f"Result repeat-metrics companion is stale: {target}")
    return _load_json(target)


def _paper_markdown(summary: dict) -> str:
    primary = summary["primary"]
    lower, upper = primary["ci95"]
    model_rows = "\n".join(
        f"| {model} | {values['auroc']:.3f} ({summary['model_repeat_uncertainty'][model]['auroc']['repeat_sd']:.3f}) | {values['pr_auroc']:.3f} | "
        f"{values['brier']:.3f} | {values['calibration_intercept']:.3f} | "
        f"{values['calibration_slope']:.3f} |"
        for model, values in summary["models"].items()
    )
    update = summary["update_transport"]["paired_delta_auroc"]
    update_lower, update_upper = update["ci95"]
    robustness_rows = "\n".join(
        f"| {name.replace('_', ' ')} | {result['primary']['delta_auroc']:+.3f} | "
        f"{result['primary']['ci95'][0]:+.3f} to {result['primary']['ci95'][1]:+.3f} |"
        for name, result in summary["robustness"].items()
    )
    return f"""# Frozen MAMMAL representations for drug-level DILI concern: a paired scaffold-grouped benchmark

## Abstract

**Objective.** To determine whether a pre-specified frozen MAMMAL molecular embedding adds discrimination beyond physicochemical descriptors and a chirality-aware Morgan fingerprint for drug-level DILIrank 2.0 concern classification.

**Design.** Repeated nested scaffold-grouped validation with a common L2-regularised logistic-regression learner. Model B used descriptors plus Morgan bits; Model D added the frozen 768-dimensional MAMMAL vector. The primary estimand was mean repeat-level `AUROC(D) - AUROC(B)`, with a 95% interval from 2,000 complete-scaffold bootstrap resamples and a pre-specified +0.03 practical benchmark.

**Data.** Of {summary['flow']['dilirank_records']:,} DILIrank 2.0 records, {summary['flow']['non_ambiguous_records_considered']:,} non-ambiguous records underwent structural review; {summary['flow']['eligible_drugs']:,} were eligible. The primary development cohort contained {summary['flow']['development_drugs']:,} original-list drugs and the untouched transport cohort contained {summary['flow']['update_drugs']:,} added drugs.

**Results.** Adding MAMMAL changed AUROC by **{primary['delta_auroc']:+.3f}** (95% CI **{lower:+.3f} to {upper:+.3f}**). {primary['interpretation']} In the untouched update cohort, the paired AUROC change was {update['estimate']:+.3f} (95% CI {update_lower:+.3f} to {update_upper:+.3f}); this is exploratory transport evidence.

**Conclusion.** {primary['interpretation']} This conclusion applies only to the frozen checkpoint, prompt, pooling rule, eligible drug-level cohort, conventional comparator, learner, and validation procedure studied here. It is not a patient-risk estimate or clinical recommendation.

## Research question and estimand

The study asks an incremental question: does one frozen MAMMAL representation improve ranking performance when added to a strong conventional molecular baseline? Models B and D used identical drugs, folds, preprocessing, hyperparameter opportunities, thresholds, and classifiers. The only intended difference was the MAMMAL block. The primary point estimate is the arithmetic mean of five paired repeat-level AUROC differences.

## Methods

### Cohort and outcome

DILIrank 2.0 categories `vMost` and `vLess` were coded positive and `vNo` negative. Ambiguous labels were excluded before structural review. Names were mapped to PubChem candidates, active moieties were adjudicated, parent structures were standardised while preserving justified stereochemistry, unsupported biologics/complexes/mixtures were excluded, and duplicate parents were resolved before grouping.

### Representations

- Model A: pre-specified physicochemical descriptors.
- Model B: descriptors plus 2,048 radius-2 chirality-aware Morgan bits.
- Model C: frozen MAMMAL embedding alone.
- Model D: descriptors, Morgan bits, and frozen MAMMAL embedding.

MAMMAL weights were never updated using DILI labels. The checkpoint, revision, tokenizer bytes, checkpoint-native molecule syntax, final encoder state, attention-mask-aware mean pooling, L2 normalisation, maximum length, failure rules, and CPU execution were frozen after an outcome-blind 20-structure pilot.

### Validation and analysis

Bemis-Murcko scaffolds defined groups for ring-containing structures; acyclic structures were similarity-clustered. Five outer folds were repeated five times. Preprocessing and regularisation selection occurred only inside training partitions. The 300-drug update-era source cohort was excluded from development and evaluated once after the development pipeline was fixed. The primary interval resampled complete scaffold groups, preserving model pairing and chemical clustering.

## Results

### Study flow

- DILIrank 2.0 records: {summary['flow']['dilirank_records']:,}
- Non-ambiguous records structurally considered: {summary['flow']['non_ambiguous_records_considered']:,}
- Eligible / excluded: {summary['flow']['eligible_drugs']:,} / {summary['flow']['excluded_drugs']:,}
- Chemical groups: {summary['flow']['scaffold_groups']:,} across all eligible drugs; {summary['flow']['development_groups']:,} constructed independently in development and {summary['flow']['update_groups']:,} constructed separately in the update cohort
- Development / untouched update drugs: {summary['flow']['development_drugs']:,} / {summary['flow']['update_drugs']:,}

### Model performance

| Model | AUROC mean (repeat SD) | PR-AUROC | Brier | Calibration intercept | Calibration slope |
|---|---:|---:|---:|---:|---:|
{model_rows}

### Primary answer

The paired change was **{primary['delta_auroc']:+.3f}** (95% CI **{lower:+.3f} to {upper:+.3f}**) against the pre-specified practical benchmark of +{primary['practical_gain_benchmark']:.2f}. **{primary['interpretation']}** Repeat-specific differences were {', '.join(f'{value:+.3f}' for value in primary['repeat_deltas'])}.

The pre-performance precision simulation on the final development group vector had minimum empirical coverage {summary['precision_diagnostics']['minimum_empirical_coverage']:.3f}, maximum mean interval width {summary['precision_diagnostics']['maximum_mean_ci_width']:.3f}, and maximum 100-versus-2,000-resample endpoint shift {summary['precision_diagnostics']['maximum_endpoint_shift_100_to_2000']:.3f}. These diagnostics motivate cautious interval interpretation and do not alter the frozen estimator.

### Transport and error review

The untouched added-drug cohort estimate was {update['estimate']:+.3f} (95% CI {update_lower:+.3f} to {update_upper:+.3f}). The machine-readable error table contains {summary['important_false_negative_rows']} model-drug rows in which a `vMost` drug fell below the training-derived Youden threshold in at least one repeat.

### Pre-specified robustness analyses

| Analysis | D-minus-B AUROC | 95% CI |
|---|---:|---:|
{robustness_rows}

The random-split analysis is explicitly optimistic and cannot replace scaffold-grouped validation. The `vMost`-versus-`vNo` and class-balanced analyses are sensitivity checks; none redefines the primary estimand.

Across the primary fits, {summary['convergence']['primary']['warning_count']} convergence warnings were recorded. All are retained and disclosed; no prediction is silently removed. Repeat-level metric ranges and standard deviations, the cohort/scaffold table, sensitivity table, and both false-negative persistence definitions are provided as machine-readable companion files.

## Interpretation

{primary['interpretation']} The result should be interpreted jointly with precision-recall performance, probability error, calibration, sensitivity/specificity, transport behavior, and important false negatives. A positive AUROC difference does not establish clinical utility; an interval crossing zero does not prove equivalence; and an upper interval below +0.03 addresses only the pre-specified size of improvement under this design.

## Limitations

The outcome is a curated drug-level concern category, not individual patient injury. Molecular structure omits dose, exposure, metabolism, immune mechanisms, genetics, comorbidity, and co-medication. Labels are imperfect regulatory/evidentiary constructs. Scaffold separation limits downstream analogue leakage but cannot establish whether a pretrained foundation model encountered study molecules. Results concern one frozen representation recipe and one conventional learner, not the full MAMMAL family.

## Scope statement

This study evaluates drug-level prediction of curated DILI concern within DILIrank 2.0. It does not estimate an individual patient's probability of liver injury, establish drug-specific causality, recommend prescribing decisions, or replace laboratory, clinical, pharmacovigilance, or regulatory assessment.
"""


def generate_research_report(
    cohort_path: str | Path,
    folds_path: str | Path,
    all_folds_path: str | Path,
    update_groups_path: str | Path,
    predictions_path: str | Path,
    results_path: str | Path,
    update_results_path: str | Path,
    vmost_results_path: str | Path,
    random_results_path: str | Path,
    balanced_results_path: str | Path,
    output_directory: str | Path,
    site_data_path: str | Path | None = None,
) -> dict:
    g3 = require_feature_fold_lock()
    g4 = require_prediction_lock()
    expected_inputs = {
        "cohort": (Path(cohort_path), Path("data/processed/cohort_audit.csv")),
        "folds": (Path(folds_path), Path("artifacts/folds/development_folds.csv")),
        "all_folds": (Path(all_folds_path), Path("artifacts/folds/outer_folds.csv")),
        "update_groups": (Path(update_groups_path), Path("artifacts/folds/update_groups.csv")),
        "predictions": (Path(predictions_path), PREDICTION_PATHS["primary"]),
    }
    for label, (actual_path, expected_path) in expected_inputs.items():
        if actual_path != expected_path:
            raise AssertionError(f"Report requires the frozen {label} path: {expected_path}")
    if g4["source_hashes"][str(PREDICTION_PATHS["primary"])] != sha256_file(predictions_path):
        raise AssertionError("Report primary prediction input does not match G4")
    g3_hash_contract = {
        "cohort": cohort_path,
        "development_folds": folds_path,
        "all_cohort_folds": all_folds_path,
        "update_groups": update_groups_path,
    }
    for key, path in g3_hash_contract.items():
        if g3["source_hashes"].get(key) != sha256_file(path):
            raise AssertionError(f"Report {key} input does not match G3")
    cohort = pd.read_csv(cohort_path)
    folds = pd.read_csv(folds_path)
    all_folds = pd.read_csv(all_folds_path)
    update_groups = pd.read_csv(update_groups_path)
    predictions = pd.read_csv(predictions_path)
    results = _validate_result_lineage(results_path, "primary")
    update_results = _validate_result_lineage(update_results_path, "update_transport")
    robustness = {
        "vmost_vs_vno": _validate_result_lineage(vmost_results_path, "vmost_vs_vno"),
        "stratified_random": _validate_result_lineage(random_results_path, "stratified_random"),
        "class_balanced": _validate_result_lineage(balanced_results_path, "class_balanced"),
    }
    target = Path(output_directory)
    target.mkdir(parents=True, exist_ok=True)

    model_table = pd.DataFrame(results["models"]).T.reset_index(names="model")
    model_table.to_csv(target / "model_performance.csv", index=False)
    roc_data, pr_data, calibration_data = _curve_data(predictions)
    roc_data.to_csv(target / "roc_curves.csv", index=False)
    pr_data.to_csv(target / "precision_recall_curves.csv", index=False)
    calibration_data.to_csv(target / "calibration.csv", index=False)
    errors = _important_false_negatives(predictions, cohort)
    errors.to_csv(target / "important_false_negatives.csv", index=False)
    (target / "primary_effect.svg").write_text(
        _primary_svg(results["primary"]), encoding="utf-8"
    )
    primary_repeat_metrics = pd.read_csv(
        Path(results_path).with_name(f"{Path(results_path).stem}.repeat_metrics.csv")
    )
    primary_repeat_metrics.to_csv(target / "repeat_stability.csv", index=False)
    (target / "repeat_stability.svg").write_text(
        _repeat_stability_svg(primary_repeat_metrics), encoding="utf-8"
    )
    uncertainty_rows = []
    for model, metrics in results["model_repeat_uncertainty"].items():
        for metric, values in metrics.items():
            uncertainty_rows.append({"model": model, "metric": metric, **values})
    pd.DataFrame(uncertainty_rows).to_csv(target / "model_metric_uncertainty.csv", index=False)
    sensitivity_rows = []
    for name, value in robustness.items():
        sensitivity_rows.append(
            {
                "analysis": name,
                "delta_auroc": value["primary"]["delta_auroc"],
                "ci95_lower": value["primary"]["ci95"][0],
                "ci95_upper": value["primary"]["ci95"][1],
                "interpretation": value["primary"]["interpretation"],
                "convergence_warnings": value["convergence"]["warning_count"],
            }
        )
    pd.DataFrame(sensitivity_rows).to_csv(target / "sensitivity_analyses.csv", index=False)

    eligible = cohort[cohort["eligibility"]]
    flow = {
        "dilirank_records": 1336,
        "non_ambiguous_records_considered": len(cohort),
        "eligible_drugs": len(eligible),
        "excluded_drugs": int((~cohort["eligibility"]).sum()),
        "development_drugs": int((eligible["release_group"] == "original-list").sum()),
        "update_drugs": int((eligible["release_group"] == "added-in-2.0").sum()),
        "scaffold_groups": int(all_folds["scaffold_id"].nunique()),
        "development_groups": int(folds["scaffold_id"].nunique()),
        "update_groups": int(update_groups["scaffold_id"].nunique()),
        "outcome_counts": eligible["dili_category"].value_counts().to_dict(),
    }
    write_json(target / "study_flow.json", flow)
    scaffold_summary = pd.DataFrame(
        [
            {
                "population": "all structurally eligible",
                "drugs": len(all_folds),
                "groups": int(all_folds["scaffold_id"].nunique()),
                "largest_group": int(all_folds["scaffold_id"].value_counts().max()),
                "singleton_groups": int((all_folds["scaffold_id"].value_counts() == 1).sum()),
            },
            {
                "population": "original-list development",
                "drugs": len(folds),
                "groups": int(folds["scaffold_id"].nunique()),
                "largest_group": int(folds["scaffold_id"].value_counts().max()),
                "singleton_groups": int((folds["scaffold_id"].value_counts() == 1).sum()),
            },
            {
                "population": "added-in-2.0 untouched update",
                "drugs": len(update_groups),
                "groups": int(update_groups["scaffold_id"].nunique()),
                "largest_group": int(update_groups["scaffold_id"].value_counts().max()),
                "singleton_groups": int((update_groups["scaffold_id"].value_counts() == 1).sum()),
            },
        ]
    )
    scaffold_summary.to_csv(target / "cohort_scaffold_summary.csv", index=False)

    primary = results["primary"]
    summary = {
        "status": "complete",
        "research_question": (
            "Does adding one frozen MAMMAL molecular embedding improve drug-level DILI "
            "concern discrimination beyond descriptors and a Morgan fingerprint?"
        ),
        "answer": primary["interpretation"],
        "primary": primary,
        "models": results["models"],
        "model_repeat_uncertainty": results["model_repeat_uncertainty"],
        "update_transport": update_results,
        "robustness": robustness,
        "flow": flow,
        "important_false_negative_rows": len(errors),
        "precision_diagnostics": _load_json("audit/qc/precision_simulation.summary.json"),
        "uncertainty_note": "Per-model uncertainty tables describe variation across five repeats; the primary inferential interval is the complete-scaffold paired bootstrap.",
        "convergence": {
            "primary": results["convergence"],
            "robustness": {name: value["convergence"] for name, value in robustness.items()},
            "update": update_results["convergence"],
        },
        "provenance": {
            "protocol_lock_sha256": sha256_file(LOCK_PATH),
            "g3_feature_lock_sha256": sha256_file(G3_PATH),
            "g4_prediction_lock_sha256": sha256_file(G4_PATH),
            "g4_contracts": g4["prediction_contracts"],
            "primary_result": results["provenance"],
        },
        "scope": results["scope"],
        "source_hashes": {
            "cohort": sha256_file(cohort_path),
            "folds": sha256_file(folds_path),
            "all_folds": sha256_file(all_folds_path),
            "update_groups": sha256_file(update_groups_path),
            "predictions": sha256_file(predictions_path),
            "results": sha256_file(results_path),
            "update_results": sha256_file(update_results_path),
            "vmost_results": sha256_file(vmost_results_path),
            "random_results": sha256_file(random_results_path),
            "balanced_results": sha256_file(balanced_results_path),
        },
    }
    write_json(target / "research_summary.json", summary)
    if site_data_path is not None:
        write_json(site_data_path, summary)
    (target / "research_report.md").write_text(_paper_markdown(summary), encoding="utf-8")
    write_json(
        target / "report_manifest.json",
        {
            "g4_prediction_lock_sha256": sha256_file(G4_PATH),
            "research_summary_sha256": sha256_file(target / "research_summary.json"),
            "research_report_sha256": sha256_file(target / "research_report.md"),
            "site_data_sha256": sha256_file(site_data_path) if site_data_path is not None else None,
            "generated_files": {
                str(path.relative_to(target)): sha256_file(path)
                for path in sorted(target.iterdir())
                if path.is_file() and path.name != "report_manifest.json"
            },
        },
    )
    return summary
