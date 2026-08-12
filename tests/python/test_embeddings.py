import numpy as np
import pandas as pd
import pytest

from mammal_dili.embeddings import mammal
from mammal_dili.embeddings.mammal import (
    make_prompt,
    prepare_full_blind_input,
    validate_full_extraction,
    validate_pilot,
)
from mammal_dili.io import sha256_file, write_json


def test_prompt_contract_is_byte_explicit() -> None:
    config = {
        "prompt_prefix": (
            "<@TOKENIZER-TYPE=SMILES><MOLECULAR_ENTITY>"
            "<MOLECULAR_ENTITY_SMALL_MOLECULE><SEQUENCE_NATURAL_START>"
        ),
        "prompt_suffix": "<SEQUENCE_NATURAL_END><EOS>",
    }
    assert make_prompt("CCO", config) == (
        "<@TOKENIZER-TYPE=SMILES><MOLECULAR_ENTITY>"
        "<MOLECULAR_ENTITY_SMALL_MOLECULE><SEQUENCE_NATURAL_START>"
        "CCO<SEQUENCE_NATURAL_END><EOS>"
    )


def test_full_mammal_input_is_label_blind_and_eligible_only(tmp_path) -> None:
    cohort = tmp_path / "cohort.csv"
    output = tmp_path / "blind.csv"
    pd.DataFrame(
        {
            "drug_id": ["eligible", "excluded"],
            "standardised_isomeric_smiles": ["CCO", "CC"],
            "eligibility": [True, False],
            "outcome": [1, 0],
            "dili_category": ["vMost", "vNo"],
        }
    ).to_csv(cohort, index=False)

    result = prepare_full_blind_input(cohort, output)

    assert result.to_dict(orient="records") == [
        {"drug_id": "eligible", "standardised_isomeric_smiles": "CCO"}
    ]
    assert list(pd.read_csv(output)) == ["drug_id", "standardised_isomeric_smiles"]


def test_pilot_validation_separates_process_and_order_checks(tmp_path) -> None:
    ids = np.array([f"PILOT-{index:02d}" for index in range(1, 21)])
    vectors = np.arange(20 * 768, dtype=np.float32).reshape(20, 768) + 1
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
    baseline = tmp_path / "baseline.npz"
    same = tmp_path / "same.npz"
    reversed_run = tmp_path / "reversed.npz"
    token_counts = np.full(20, 6, dtype=np.int32)
    np.savez_compressed(baseline, drug_ids=ids, embeddings=vectors, token_counts=token_counts)
    np.savez_compressed(same, drug_ids=ids, embeddings=vectors.copy(), token_counts=token_counts)
    np.savez_compressed(
        reversed_run,
        drug_ids=ids[::-1],
        embeddings=vectors[::-1].copy(),
        token_counts=token_counts[::-1],
    )
    invariant = {
        "input_sha256": "input",
        "config_file_sha256": "config",
        "validated_config_sha256": "validated",
        "code_revision": "pinned-code",
        "implementation_revision": "analysis-code",
        "checkpoint": "checkpoint",
        "checkpoint_revision": "revision",
        "model_files": {"model.safetensors": {"sha256": "model"}},
        "tokenizer_files": {"tokenizer/config.yaml": {"sha256": "tokenizer"}},
        "prompt_prefix": "prefix",
        "prompt_suffix": "suffix",
        "hidden_state": "state",
        "pooling": "pooling",
        "dtype": "float32",
        "device": "cpu",
        "batch_size": 8,
        "max_sequence_length": 2100,
        "unknown_token_rule": "reject",
        "unknown_token_id": 0,
        "overlength_rule": "reject",
        "special_tokens": "included",
        "environment_locks": {"environment/mammal-lock.txt": "lock"},
        "tokenizer_vocabulary_diagnostics": [{"file": "tokenizer.json", "hole_count": 1}],
    }
    for index, (path, order, run_ids) in enumerate(
        [
            (baseline, "input_order", ids),
            (same, "input_order", ids),
            (reversed_run, "reversed", ids[::-1]),
        ],
        start=1,
    ):
        write_json(
            path.with_suffix(".manifest.json"),
            {
                **invariant,
                "batch_order": order,
                "run_id": f"run-{index}",
                "process_id": index,
                "started_at_utc": f"2026-08-13T00:00:0{index}+00:00",
                "rows_successful": 20,
                "rows_requested": 20,
                "requested_drug_ids": ids.tolist(),
                "successful_drug_ids": run_ids.tolist(),
                "failures": [],
                "tokenizer_loader_warnings": [],
                "token_diagnostics": [
                    {
                        "drug_id": drug_id,
                        "token_count": 6,
                        "unknown_token_count": 0,
                        "truncated": False,
                        "warnings": [],
                    }
                    for drug_id in run_ids
                ],
                "embedding_dimension": 768,
                "embedding_norm_min": float(
                    np.linalg.norm(vectors if order == "input_order" else vectors[::-1], axis=1).min()
                ),
                "embedding_norm_max": float(
                    np.linalg.norm(vectors if order == "input_order" else vectors[::-1], axis=1).max()
                ),
                "output_sha256": sha256_file(path),
            },
        )

    report = validate_pilot(
        baseline,
        same,
        reversed_run,
        "configs/mammal_embedding.yaml",
        tmp_path / "report.json",
    )

    assert report["passed"] is True
    assert report["process_repeatability"]["within_tolerance"] is True
    assert report["batch_order_invariance"]["within_tolerance"] is True


def test_full_validation_binds_repeat_to_exact_sample_hash(tmp_path, monkeypatch) -> None:
    full_input = tmp_path / "full.csv"
    sample = tmp_path / "sample.csv"
    pd.DataFrame({"drug_id": ["a", "b"]}).to_csv(full_input, index=False)
    pd.DataFrame({"drug_id": ["a"]}).to_csv(sample, index=False)
    arrays = [
        {"drug_ids": np.array(["a", "b"]), "embeddings": np.ones((2, 768))},
        {"drug_ids": np.array(["a"]), "embeddings": np.ones((1, 768))},
    ]
    manifests = [
        {"input_sha256": sha256_file(full_input)},
        {"input_sha256": "stale-sample-hash"},
    ]
    calls = iter(zip(arrays, manifests, strict=True))
    monkeypatch.setattr(mammal, "_load_and_validate_run", lambda *_: next(calls))
    with pytest.raises(AssertionError, match="deterministic sample"):
        validate_full_extraction(
            full_input,
            sample,
            tmp_path / "full.npz",
            tmp_path / "repeat.npz",
            "configs/mammal_embedding.yaml",
            tmp_path / "report.json",
        )
