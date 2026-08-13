import numpy as np
import pandas as pd
import pytest

from mammal_dili.embeddings import mammal
from mammal_dili.embeddings.mammal import (
    _canonicalize_manifest_file_map,
    _snapshot_relative_posix,
    _validate_pa03_lineage,
    _verify_manifest_snapshot_files,
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


def test_manifest_paths_write_posix_and_accept_legacy_windows_separator(tmp_path) -> None:
    snapshot = tmp_path / "snapshot"
    target = snapshot / "tokenizer" / "config.yaml"
    assert _snapshot_relative_posix(target, snapshot) == "tokenizer/config.yaml"
    result = _canonicalize_manifest_file_map(
        {r"tokenizer\config.yaml": {"sha256": "same"}}, "tokenizer_files"
    )
    assert result == {"tokenizer/config.yaml": {"sha256": "same"}}


@pytest.mark.parametrize(
    "key",
    [
        r"C:\\snapshot\\tokenizer\\config.yaml",
        r"\\\\server\\share\\config.yaml",
        "/snapshot/tokenizer/config.yaml",
        "tokenizer/../config.yaml",
        "tokenizer/./config.yaml",
        "tokenizer//config.yaml",
    ],
)
def test_manifest_path_canonicalization_rejects_unsafe_paths(key) -> None:
    with pytest.raises(AssertionError, match="unsafe path"):
        _canonicalize_manifest_file_map({key: {}}, "tokenizer_files")


def test_manifest_path_canonicalization_rejects_collision() -> None:
    with pytest.raises(AssertionError, match="collision"):
        _canonicalize_manifest_file_map(
            {"tokenizer/config.yaml": {}, r"tokenizer\config.yaml": {}},
            "tokenizer_files",
        )


def test_snapshot_verification_rejects_tokenizer_config_omission(tmp_path) -> None:
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    model = snapshot / "model.safetensors"
    model.write_bytes(b"model")
    manifest = {
        "checkpoint_snapshot": str(snapshot),
        "model_total_bytes": 5,
        "model_files": {
            "model.safetensors": {"sha256": sha256_file(model), "bytes": 5}
        },
        "tokenizer_files": {},
    }
    with pytest.raises(AssertionError, match="config.yaml"):
        _verify_manifest_snapshot_files(manifest)


def test_pa03_frozen_hash_refusal_occurs_before_npz_loading(tmp_path, monkeypatch) -> None:
    paths = []
    expected = {}
    for stem in ("mammal_pilot_baseline", "mammal_pilot_same_order", "mammal_pilot_reordered"):
        npz = tmp_path / f"{stem}.npz"
        manifest = tmp_path / f"{stem}.manifest.json"
        npz.write_bytes(b"frozen")
        manifest.write_bytes(b"{}")
        paths.append(npz)
        for path in (npz, manifest):
            expected[path.name] = {
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
    monkeypatch.setattr(mammal, "PA03_FROZEN_PILOT_ARTIFACTS", expected)
    paths[0].write_bytes(b"tampered")
    called = False

    def forbidden_load(*_args, **_kwargs):
        nonlocal called
        called = True
        raise AssertionError("Extraction loader must not be called")

    monkeypatch.setattr(mammal, "_load_and_validate_run", forbidden_load)
    with pytest.raises(AssertionError, match="artifact changed"):
        validate_pilot(
            paths[0],
            paths[1],
            paths[2],
            tmp_path / "unread-config.yaml",
            tmp_path / "unwritten-report.json",
            require_pa03_frozen_artifacts=True,
            validation_implementation_revision="validation-revision",
        )
    assert called is False


def test_pa03_lineage_rejects_extraction_revision_and_records_validation_revision() -> None:
    with pytest.raises(AssertionError, match="extraction revision"):
        _validate_pa03_lineage(
            [{"implementation_revision": "wrong"}], "validation-revision"
        )
    lineage = _validate_pa03_lineage(
        [{"implementation_revision": mammal.PA03_EXTRACTION_REVISION}],
        "validation-revision",
    )
    assert lineage == {
        "extraction_implementation_revision": mammal.PA03_EXTRACTION_REVISION,
        "validation_implementation_revision": "validation-revision",
    }


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
    snapshot = tmp_path / "snapshot"
    tokenizer = snapshot / "tokenizer" / "config.yaml"
    tokenizer.parent.mkdir(parents=True)
    model = snapshot / "model.safetensors"
    tokenizer.write_bytes(b"tokenizer")
    model.write_bytes(b"model")
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
        "checkpoint_snapshot": str(snapshot),
        "model_total_bytes": 5,
        "model_files": {
            "model.safetensors": {"sha256": sha256_file(model), "bytes": 5}
        },
        "tokenizer_files": {
            "tokenizer/config.yaml": {
                "sha256": sha256_file(tokenizer),
                "bytes": 9,
            }
        },
        "tokenizer_loader_warnings": [],
        "tokenizer_revision": "revision",
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
