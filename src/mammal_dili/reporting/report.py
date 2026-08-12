from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import precision_recall_curve, roc_curve

from mammal_dili.io import sha256_file, write_json


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


def _important_false_negatives(predictions: pd.DataFrame) -> pd.DataFrame:
    important = predictions[predictions["dili_category"].str.startswith("vMost")].copy()
    important["classified_negative"] = (
        important["predicted_probability"] < important["youden_threshold"]
    )
    summary = (
        important.groupby(
            ["drug_id", "compound_name_source", "scaffold_id", "model"], as_index=False
        )
        .agg(
            mean_probability=("predicted_probability", "mean"),
            minimum_probability=("predicted_probability", "min"),
            negative_repeats=("classified_negative", "sum"),
            repeats=("repeat", "nunique"),
        )
    )
    return summary[summary["negative_repeats"] > 0].sort_values(
        ["negative_repeats", "mean_probability"], ascending=[False, True]
    )


def _paper_markdown(summary: dict) -> str:
    primary = summary["primary"]
    lower, upper = primary["ci95"]
    model_rows = "\n".join(
        f"| {model} | {values['auroc']:.3f} | {values['pr_auroc']:.3f} | "
        f"{values['brier']:.3f} | {values['calibration_intercept']:.3f} | "
        f"{values['calibration_slope']:.3f} |"
        for model, values in summary["models"].items()
    )
    update = summary["update_transport"]["paired_delta_auroc"]
    update_lower, update_upper = update["ci95"]
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
- Chemical groups: {summary['flow']['scaffold_groups']:,}
- Development / untouched update drugs: {summary['flow']['development_drugs']:,} / {summary['flow']['update_drugs']:,}

### Model performance

| Model | AUROC | PR-AUROC | Brier | Calibration intercept | Calibration slope |
|---|---:|---:|---:|---:|---:|
{model_rows}

### Primary answer

The paired change was **{primary['delta_auroc']:+.3f}** (95% CI **{lower:+.3f} to {upper:+.3f}**) against the pre-specified practical benchmark of +{primary['practical_gain_benchmark']:.2f}. **{primary['interpretation']}** Repeat-specific differences were {', '.join(f'{value:+.3f}' for value in primary['repeat_deltas'])}.

### Transport and error review

The untouched added-drug cohort estimate was {update['estimate']:+.3f} (95% CI {update_lower:+.3f} to {update_upper:+.3f}). The machine-readable error table contains {summary['important_false_negative_rows']} model-drug rows in which a `vMost` drug fell below the training-derived Youden threshold in at least one repeat.

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
    predictions_path: str | Path,
    results_path: str | Path,
    update_results_path: str | Path,
    output_directory: str | Path,
) -> dict:
    cohort = pd.read_csv(cohort_path)
    folds = pd.read_csv(folds_path)
    predictions = pd.read_csv(predictions_path)
    results = _load_json(results_path)
    update_results = _load_json(update_results_path)
    target = Path(output_directory)
    target.mkdir(parents=True, exist_ok=True)

    model_table = pd.DataFrame(results["models"]).T.reset_index(names="model")
    model_table.to_csv(target / "model_performance.csv", index=False)
    roc_data, pr_data, calibration_data = _curve_data(predictions)
    roc_data.to_csv(target / "roc_curves.csv", index=False)
    pr_data.to_csv(target / "precision_recall_curves.csv", index=False)
    calibration_data.to_csv(target / "calibration.csv", index=False)
    errors = _important_false_negatives(predictions)
    errors.to_csv(target / "important_false_negatives.csv", index=False)
    (target / "primary_effect.svg").write_text(
        _primary_svg(results["primary"]), encoding="utf-8"
    )

    eligible = cohort[cohort["eligibility"]]
    flow = {
        "dilirank_records": 1336,
        "non_ambiguous_records_considered": len(cohort),
        "eligible_drugs": len(eligible),
        "excluded_drugs": int((~cohort["eligibility"]).sum()),
        "development_drugs": int((eligible["release_group"] == "original-list").sum()),
        "update_drugs": int((eligible["release_group"] == "added-in-2.0").sum()),
        "scaffold_groups": int(folds["scaffold_id"].nunique()),
        "outcome_counts": eligible["dili_category"].value_counts().to_dict(),
    }
    write_json(target / "study_flow.json", flow)

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
        "update_transport": update_results,
        "flow": flow,
        "important_false_negative_rows": len(errors),
        "scope": results["scope"],
        "source_hashes": {
            "cohort": sha256_file(cohort_path),
            "folds": sha256_file(folds_path),
            "predictions": sha256_file(predictions_path),
            "results": sha256_file(results_path),
            "update_results": sha256_file(update_results_path),
        },
    }
    write_json(target / "research_summary.json", summary)
    (target / "research_report.md").write_text(_paper_markdown(summary), encoding="utf-8")
    return summary
