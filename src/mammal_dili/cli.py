from __future__ import annotations

import argparse
import json

from mammal_dili.acquisition.dilirank import acquire_dilirank
from mammal_dili.acquisition.pubchem import resolve_pubchem
from mammal_dili.chemistry.features import build_conventional_features
from mammal_dili.curation.structures import create_review_packets, curate_cohort
from mammal_dili.embeddings.mammal import (
    extract_embeddings,
    preflight_pilot,
    prepare_full_blind_input,
    select_blind_pilot,
    select_embedding_verification_sample,
    validate_full_extraction,
    validate_pilot,
)
from mammal_dili.grouping.scaffolds import build_groups_and_folds
from mammal_dili.lock import create_protocol_lock
from mammal_dili.modelling.nested_cv import run_nested_cv, run_update_transport
from mammal_dili.reporting.report import generate_research_report
from mammal_dili.statistics.estimate import estimate_results, estimate_update_results
from mammal_dili.statistics.precision import simulate_precision


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="mammal-dili")
    commands = root.add_subparsers(dest="command", required=True)

    commands.add_parser("acquire")
    commands.add_parser("resolve-pubchem")
    commands.add_parser("curate")
    commands.add_parser("make-review-packets")
    commands.add_parser("build-features")
    commands.add_parser("build-folds")
    commands.add_parser("lock-protocol")
    pilot_select = commands.add_parser("select-pilot")
    pilot_select.add_argument("--total", type=int, default=20)
    commands.add_parser("preflight-pilot")
    commands.add_parser("prepare-mammal-input")
    commands.add_parser("select-embedding-qc-sample")
    mammal = commands.add_parser("extract-mammal")
    mammal.add_argument("--input", required=True)
    mammal.add_argument("--output", required=True)
    mammal.add_argument("--reverse-order", action="store_true")
    commands.add_parser("validate-pilot")
    commands.add_parser("validate-full-extraction")
    commands.add_parser("cross-validate")
    commands.add_parser("evaluate-update")
    commands.add_parser("estimate")
    commands.add_parser("estimate-update")
    commands.add_parser("simulate-precision")
    commands.add_parser("generate-report")
    return root


def main() -> None:
    args = parser().parse_args()
    if args.command == "acquire":
        result = acquire_dilirank("configs/sources.yaml", "data/interim/dilirank.csv")
        print(f"Validated {len(result)} DILIrank records")
    elif args.command == "resolve-pubchem":
        result = resolve_pubchem(
            "data/interim/dilirank.csv",
            "configs/sources.yaml",
            "data/interim/identity_resolution.csv",
            "data/interim/pubchem_cache_v3.json",
        )
        print(result["identity_status"].value_counts().to_string())
    elif args.command == "curate":
        result = curate_cohort(
            "data/interim/identity_resolution.csv",
            "configs/curation.yaml",
            "data/processed/cohort_audit.csv",
        )
        print(result["eligibility"].value_counts().to_string())
    elif args.command == "make-review-packets":
        result = create_review_packets(
            "data/processed/cohort_audit.csv",
            "configs/curation.yaml",
            "configs/seeds.yaml",
            "audit/reviews/phase-1",
        )
        print(json.dumps(result, indent=2))
    elif args.command == "build-features":
        print(
            build_conventional_features(
                "data/processed/cohort_audit.csv",
                "configs/features.yaml",
                "artifacts/features/conventional.npz",
            )
        )
    elif args.command == "build-folds":
        result = build_groups_and_folds(
            "data/processed/cohort_audit.csv", "configs/folds.yaml", "artifacts/folds/outer_folds.csv"
        )
        print(f"Locked {len(result)} drugs across {result['scaffold_id'].nunique()} groups")
    elif args.command == "lock-protocol":
        print(json.dumps(create_protocol_lock(), indent=2))
    elif args.command == "select-pilot":
        result = select_blind_pilot(
            "data/processed/cohort_audit.csv", "audit/pilot/frozen_pilot_v2.csv", args.total
        )
        print(f"Selected {len(result)} label-blind pilot molecules")
    elif args.command == "preflight-pilot":
        report = preflight_pilot(
            "audit/pilot/frozen_pilot_v2.csv",
            "configs/mammal_embedding.yaml",
            "audit/pilot/tokenizer_preflight.json",
        )
        print(json.dumps(report, indent=2))
        if not report["passed"]:
            raise SystemExit(2)
    elif args.command == "prepare-mammal-input":
        result = prepare_full_blind_input(
            "data/processed/cohort_audit.csv", "data/processed/mammal_full_blind.csv"
        )
        print(f"Prepared {len(result)} label-blind full-cohort structures")
    elif args.command == "select-embedding-qc-sample":
        result = select_embedding_verification_sample(
            "data/processed/mammal_full_blind.csv",
            "data/processed/mammal_verification_sample.csv",
        )
        print(f"Selected {len(result)} deterministic verification structures")
    elif args.command == "extract-mammal":
        print(
            extract_embeddings(
                args.input,
                "configs/mammal_embedding.yaml",
                args.output,
                reverse_order=args.reverse_order,
            )
        )
    elif args.command == "validate-pilot":
        report = validate_pilot(
            "artifacts/pilot/mammal_pilot_baseline.npz",
            "artifacts/pilot/mammal_pilot_same_order.npz",
            "artifacts/pilot/mammal_pilot_reordered.npz",
            "configs/mammal_embedding.yaml",
            "artifacts/pilot/pilot_report.json",
        )
        print(json.dumps(report, indent=2))
        if not report["passed"]:
            raise SystemExit(2)
    elif args.command == "validate-full-extraction":
        report = validate_full_extraction(
            "data/processed/mammal_full_blind.csv",
            "artifacts/features/mammal.npz",
            "artifacts/features/mammal_verification_repeat.npz",
            "configs/mammal_embedding.yaml",
            "audit/qc/full_embedding_validation.json",
        )
        print(json.dumps(report, indent=2))
        if not report["passed"]:
            raise SystemExit(2)
    elif args.command == "cross-validate":
        result = run_nested_cv(
            "artifacts/folds/outer_folds.csv",
            "artifacts/features/conventional.npz",
            "artifacts/features/mammal.npz",
            "configs/analysis.yaml",
            "artifacts/predictions/oof_predictions.csv",
        )
        print(f"Generated {len(result)} out-of-fold predictions")
    elif args.command == "estimate":
        result = estimate_results(
            "artifacts/predictions/oof_predictions.csv",
            "configs/analysis.yaml",
            "artifacts/results/results.json",
        )
        print(json.dumps(result["primary"], indent=2))
    elif args.command == "evaluate-update":
        result = run_update_transport(
            "artifacts/folds/outer_folds.csv",
            "artifacts/features/conventional.npz",
            "artifacts/features/mammal.npz",
            "artifacts/predictions/oof_predictions.csv",
            "configs/analysis.yaml",
            "artifacts/predictions/update_predictions.csv",
        )
        print(f"Generated {len(result)} untouched update-cohort predictions")
    elif args.command == "estimate-update":
        result = estimate_update_results(
            "artifacts/predictions/update_predictions.csv",
            "configs/analysis.yaml",
            "artifacts/results/update_results.json",
        )
        print(json.dumps(result["paired_delta_auroc"], indent=2))
    elif args.command == "simulate-precision":
        print(json.dumps(simulate_precision("audit/qc/precision_simulation.csv"), indent=2))
    elif args.command == "generate-report":
        result = generate_research_report(
            "data/processed/cohort_audit.csv",
            "artifacts/folds/outer_folds.csv",
            "artifacts/predictions/oof_predictions.csv",
            "artifacts/results/results.json",
            "artifacts/results/update_results.json",
            "artifacts/report",
        )
        print(json.dumps(result["primary"], indent=2))


if __name__ == "__main__":
    main()
