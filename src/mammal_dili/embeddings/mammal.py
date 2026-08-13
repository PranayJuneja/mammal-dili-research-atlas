from __future__ import annotations

import contextlib
import io
import json
import logging
import platform
import subprocess
import time
import warnings
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath, PureWindowsPath
from uuid import uuid4

import numpy as np
import pandas as pd

from mammal_dili.config import validate_config
from mammal_dili.io import sha256_file, sha256_json, write_json

PA03_FROZEN_PILOT_ARTIFACTS = {
    "mammal_pilot_baseline.npz": {
        "sha256": "28984f63fb19c200671095b3838926aac1a20d74e606a57a493ca776c4f34de3",
        "bytes": 57746,
    },
    "mammal_pilot_baseline.manifest.json": {
        "sha256": "874b8d6fe364823028570d21b21cd996aec2f85a603142a4447e416d80e696dd",
        "bytes": 16360,
    },
    "mammal_pilot_same_order.npz": {
        "sha256": "28984f63fb19c200671095b3838926aac1a20d74e606a57a493ca776c4f34de3",
        "bytes": 57746,
    },
    "mammal_pilot_same_order.manifest.json": {
        "sha256": "6dd06e130771b071533bc1523541206f861b3a8bbb9566a36be348536932952d",
        "bytes": 16360,
    },
    "mammal_pilot_reordered.npz": {
        "sha256": "9eff4e485b946c9fe52e743d3b295e78077b7cb13dffdfb8b172cdf99326b683",
        "bytes": 57746,
    },
    "mammal_pilot_reordered.manifest.json": {
        "sha256": "a74c98cdf298033752b8c42a96f9da4baa773ebfa4b1da3e56015974f96c7beb",
        "bytes": 16357,
    },
}
PA03_EXTRACTION_REVISION = "f6c35939f23ac27fa30c028589ef71888d316a26"


def _snapshot_relative_posix(path: Path, snapshot: Path) -> str:
    return path.relative_to(snapshot).as_posix()


def _canonicalize_manifest_file_map(value: object, field: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise TypeError(f"Manifest {field} must be an object")
    canonical: dict[str, object] = {}
    for raw_key, metadata in value.items():
        if not isinstance(raw_key, str) or not raw_key:
            raise AssertionError(f"Manifest {field} contains an empty or non-string path")
        windows_path = PureWindowsPath(raw_key)
        normalized = raw_key.replace("\\", "/")
        posix_path = PurePosixPath(normalized)
        parts = normalized.split("/")
        if (
            windows_path.is_absolute()
            or bool(windows_path.drive)
            or posix_path.is_absolute()
            or any(part in {"", ".", ".."} for part in parts)
        ):
            raise AssertionError(f"Manifest {field} contains an unsafe path: {raw_key!r}")
        key = "/".join(parts)
        if key in canonical:
            raise AssertionError(f"Manifest {field} path normalization collision: {key}")
        canonical[key] = metadata
    return canonical


def _verify_pa03_frozen_pilot_artifacts(paths: list[str | Path]) -> dict[str, dict]:
    artifacts: dict[str, Path] = {}
    for value in paths:
        target = Path(value)
        for path in (target, target.with_suffix(".manifest.json")):
            if path.name in artifacts:
                raise AssertionError(f"Duplicate frozen pilot artifact: {path.name}")
            artifacts[path.name] = path
    if set(artifacts) != set(PA03_FROZEN_PILOT_ARTIFACTS):
        raise AssertionError("PA-03 frozen pilot artifact names do not match the approved bundle")
    verified: dict[str, dict] = {}
    for name, expected in PA03_FROZEN_PILOT_ARTIFACTS.items():
        path = artifacts[name]
        if not path.is_file():
            raise AssertionError(f"Missing PA-03 frozen pilot artifact: {path}")
        actual = {"sha256": sha256_file(path), "bytes": path.stat().st_size}
        if actual != expected:
            raise AssertionError(f"PA-03 frozen pilot artifact changed: {name}")
        verified[name] = actual
    return verified


def _verify_manifest_snapshot_files(manifest: dict) -> None:
    snapshot_value = manifest.get("checkpoint_snapshot")
    if not isinstance(snapshot_value, str) or not snapshot_value:
        raise AssertionError("Manifest checkpoint snapshot is missing")
    snapshot = Path(snapshot_value)
    if not snapshot.is_dir():
        raise AssertionError(f"Pinned checkpoint snapshot is unavailable: {snapshot}")
    verified_bytes: dict[str, int] = {}
    for field in ("model_files", "tokenizer_files"):
        records = manifest[field]
        verified_bytes[field] = 0
        for key, expected in records.items():
            if not isinstance(expected, dict) or set(expected) != {"sha256", "bytes"}:
                raise AssertionError(f"Manifest {field} metadata is incomplete: {key}")
            path = snapshot.joinpath(*PurePosixPath(key).parts)
            if not path.is_file():
                raise AssertionError(f"Pinned snapshot file is missing: {key}")
            actual = {"sha256": sha256_file(path), "bytes": path.stat().st_size}
            if actual != expected:
                raise AssertionError(f"Pinned snapshot file changed: {key}")
            verified_bytes[field] += actual["bytes"]
    if manifest.get("model_total_bytes") != verified_bytes["model_files"]:
        raise AssertionError("Manifest model byte total does not match pinned snapshot")
    if "tokenizer/config.yaml" not in manifest["tokenizer_files"]:
        raise AssertionError("Tokenizer manifest omits tokenizer/config.yaml")


def _validate_pa03_lineage(
    manifests: list[dict], validation_implementation_revision: str | None
) -> dict[str, str]:
    if not validation_implementation_revision:
        raise AssertionError("PA-03 validation implementation revision is required")
    if any(
        manifest["implementation_revision"] != PA03_EXTRACTION_REVISION
        for manifest in manifests
    ):
        raise AssertionError("Frozen pilot extraction revision does not match PA-03")
    return {
        "extraction_implementation_revision": PA03_EXTRACTION_REVISION,
        "validation_implementation_revision": validation_implementation_revision,
    }


def make_prompt(smiles: str, config: dict) -> str:
    return f"{config['prompt_prefix']}{smiles}{config['prompt_suffix']}"


def masked_mean_l2(hidden, attention_mask, torch):
    """Pool non-padding encoder states and L2-normalise each row."""
    expanded_mask = attention_mask.unsqueeze(-1).to(dtype=hidden.dtype)
    denominator = expanded_mask.sum(dim=1).clamp_min(1.0)
    pooled = (hidden * expanded_mask).sum(dim=1) / denominator
    return torch.nn.functional.normalize(pooled, p=2, dim=1)


def _construct_tokenizer(snapshot: Path):
    from fuse.data.tokenizers.modular_tokenizer.op import ModularTokenizerOp

    captured_logs: list[str] = []

    class _Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            captured_logs.append(self.format(record))

    handler = _Capture()
    root_logger = logging.getLogger()
    transformers_logger = logging.getLogger("transformers")
    root_logger.addHandler(handler)
    transformers_logger.addHandler(handler)
    stream = io.StringIO()
    try:
        with (
            warnings.catch_warnings(record=True) as caught,
            contextlib.redirect_stdout(stream),
            contextlib.redirect_stderr(stream),
        ):
            warnings.simplefilter("always")
            tokenizer = ModularTokenizerOp.from_pretrained(snapshot / "tokenizer")
    finally:
        root_logger.removeHandler(handler)
        transformers_logger.removeHandler(handler)
    warning_messages = [str(item.message) for item in caught]
    stream_messages = [line.strip() for line in stream.getvalue().splitlines() if line.strip()]
    messages = sorted(set(warning_messages + captured_logs + stream_messages))
    return tokenizer, messages


def _compress_integer_ranges(values: list[int]) -> list[list[int]]:
    if not values:
        return []
    ranges: list[list[int]] = []
    start = previous = values[0]
    for value in values[1:]:
        if value == previous + 1:
            previous = value
            continue
        ranges.append([start, previous])
        start = previous = value
    ranges.append([start, previous])
    return ranges


def _tokenizer_vocabulary_diagnostics(tokenizer_root: Path) -> list[dict]:
    """Record the non-contiguous ID condition reported by the native tokenizer loader."""
    diagnostics = []
    for path in sorted(tokenizer_root.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        vocab = payload.get("model", {}).get("vocab", {})
        if not isinstance(vocab, dict) or not vocab:
            continue
        ids = sorted({int(value) for value in vocab.values()})
        holes = sorted(set(range(ids[0], ids[-1] + 1)) - set(ids))
        diagnostics.append(
            {
                "file": path.name,
                "model_type": payload.get("model", {}).get("type"),
                "vocab_entries": len(ids),
                "minimum_id": ids[0],
                "maximum_id": ids[-1],
                "hole_count": len(holes),
                "hole_ranges": _compress_integer_ranges(holes),
                "interpretation": (
                    "Non-contiguous reserved ID ranges; observed native loader emits "
                    "OrderedVocab-hole warnings. IDs are preserved and hashed, not rewritten."
                ),
            }
        )
    return diagnostics


def select_blind_pilot(cohort_path: str | Path, output_path: str | Path, total: int = 20) -> pd.DataFrame:
    del cohort_path
    fixtures = [
        ("PILOT-01", "CCO", "small neutral acyclic"),
        ("PILOT-02", "CC(=O)Oc1ccccc1C(=O)O", "ordinary aromatic drug-like"),
        ("PILOT-03", "O=C([O-])c1ccccc1", "negative formal charge"),
        ("PILOT-04", "C[N+](C)(C)CCO", "positive formal charge"),
        ("PILOT-05", "N[C@@H](C)C(=O)O", "defined stereocentre"),
        ("PILOT-06", "N[C@H](C)C(=O)O", "stereoisomer pair"),
        ("PILOT-07", "C1CCCCCCCCCCC1", "macrocycle"),
        ("PILOT-08", "c1ccc2cc3ccccc3cc2c1", "fused aromatic rings"),
        ("PILOT-09", "Ic1ccccc1Br", "uncommon supported halogens"),
        ("PILOT-10", "COP(=O)(O)O", "phosphorus-containing molecule"),
        ("PILOT-11", "C[Se]C", "selenium-containing molecule"),
        ("PILOT-12", "C1=CC=[N+](C=C1)[O-]", "zwitterionic charge pattern"),
        ("PILOT-13", "CC(C)(C)C(=O)O", "branched acyclic molecule"),
        ("PILOT-14", "C1CC2CCC1C2", "bridged ring system"),
        ("PILOT-15", "O=C1NCC(=O)N1", "small cyclic amide"),
        ("PILOT-16", "CC(=O)O", "parent selected from a salt source"),
        ("PILOT-17", "C[C@H](O)[C@@H](O)CO", "multiple stereocentres"),
        ("PILOT-18", "C1=CC=C(C=C1)S(=O)(=O)N", "sulfur-containing aromatic"),
        ("PILOT-19", "N#CC1=NC=CC=C1", "heteroaromatic nitrile"),
        (
            "PILOT-20",
            "[13CH3]" + "[13CH2]" * 330 + "[13CH3]",
            "valid isotope-explicit structure measured near configured tokenizer length limit",
        ),
    ]
    if total != 20:
        raise ValueError("The frozen pilot contract requires exactly 20 structures")
    pilot = pd.DataFrame(fixtures, columns=["drug_id", "standardised_isomeric_smiles", "selection_rationale"])
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    pilot.to_csv(target, index=False)
    return pilot


def prepare_full_blind_input(
    cohort_path: str | Path, output_path: str | Path
) -> pd.DataFrame:
    cohort = pd.read_csv(cohort_path)
    frame = (
        cohort[cohort["eligibility"]][["drug_id", "standardised_isomeric_smiles"]]
        .sort_values("drug_id")
        .reset_index(drop=True)
    )
    if frame["drug_id"].duplicated().any() or frame.isna().any().any():
        raise AssertionError("Full label-blind input requires unique complete drug/SMILES rows")
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(target, index=False)
    return frame


def select_embedding_verification_sample(
    input_path: str | Path,
    output_path: str | Path,
    fraction: float = 0.05,
    seed: int | None = None,
) -> pd.DataFrame:
    if seed is None:
        seed = int(validate_config("configs/seeds.yaml")["embedding_verification_sample"])
    frame = pd.read_csv(input_path)
    size = max(1, int(np.ceil(len(frame) * fraction)))
    sample = frame.sample(n=size, random_state=seed).sort_values("drug_id").reset_index(drop=True)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    sample.to_csv(target, index=False)
    return sample


def _load_runtime(config: dict):
    import torch
    from huggingface_hub import snapshot_download
    from mammal.model import Mammal

    snapshot = Path(
        snapshot_download(
            repo_id=config["checkpoint"],
            revision=config["checkpoint_revision"],
        )
    )
    model = Mammal.from_pretrained(
        pretrained_model_name_or_path=snapshot,
        allow_config_mismatch=True,
        strict=False,
    )
    model.eval()
    model = model.to(device=torch.device(config["device"]), dtype=torch.float32)
    tokenizer, tokenizer_loader_warnings = _construct_tokenizer(snapshot)
    return torch, model, tokenizer, snapshot, tokenizer_loader_warnings


def preflight_pilot(
    input_path: str | Path, config_path: str | Path, report_path: str | Path
) -> dict:
    """Validate chemistry and pinned-tokenizer behavior without loading model weights."""
    from huggingface_hub import snapshot_download
    from rdkit import Chem

    config = validate_config(config_path)
    frame = pd.read_csv(input_path)
    snapshot = Path(
        snapshot_download(
            repo_id=config["checkpoint"], revision=config["checkpoint_revision"]
        )
    )
    tokenizer, tokenizer_loader_warnings = _construct_tokenizer(snapshot)
    tokenizer_vocabulary_diagnostics = _tokenizer_vocabulary_diagnostics(snapshot / "tokenizer")
    diagnostics: list[dict] = []
    for row in frame.to_dict(orient="records"):
        smiles = row["standardised_isomeric_smiles"]
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            tokenized = tokenizer(
                {"text": make_prompt(smiles, config)},
                key_in="text",
                key_out_tokens_ids="input_ids",
                key_out_attention_mask="attention_mask",
            )
        ids = tokenized["input_ids"]
        mask = tokenized["attention_mask"]
        ids = ids.tolist() if hasattr(ids, "tolist") else list(ids)
        mask = mask.tolist() if hasattr(mask, "tolist") else list(mask)
        warning_messages = sorted({str(item.message) for item in caught})
        diagnostics.append(
            {
                "drug_id": row["drug_id"],
                "rdkit_valid": Chem.MolFromSmiles(smiles) is not None,
                "smiles_characters": len(smiles),
                "attended_tokens": int(sum(mask)),
                "sequence_length": len(ids),
                "unknown_token_count": ids.count(int(config["unknown_token_id"])),
                "warnings": warning_messages,
            }
        )
    passed = len(diagnostics) == int(config["pilot_total"]) and all(
        row["rdkit_valid"]
        and row["sequence_length"] <= int(config["max_sequence_length"])
        and row["unknown_token_count"] == 0
        and not any("unknown token" in item.casefold() for item in row["warnings"])
        for row in diagnostics
    )
    report = {
        "passed": passed,
        "rows": len(diagnostics),
        "input_sha256": sha256_file(input_path),
        "config_file_sha256": sha256_file(config_path),
        "checkpoint_revision": config["checkpoint_revision"],
        "prompt_prefix": config["prompt_prefix"],
        "prompt_suffix": config["prompt_suffix"],
        "max_sequence_length": config["max_sequence_length"],
        "unknown_token_rule": config["unknown_token_rule"],
        "tokenizer_loader_warnings": tokenizer_loader_warnings,
        "tokenizer_vocabulary_diagnostics": tokenizer_vocabulary_diagnostics,
        "diagnostics": diagnostics,
    }
    write_json(report_path, report)
    return report


def extract_embeddings(
    input_path: str | Path,
    config_path: str | Path,
    output_path: str | Path,
    reverse_order: bool = False,
) -> Path:
    config = validate_config(config_path)
    frame = pd.read_csv(input_path)
    required = {"drug_id", "standardised_isomeric_smiles"}
    if not required.issubset(frame.columns):
        raise ValueError(f"Input must include {sorted(required)}")
    if reverse_order:
        frame = frame.iloc[::-1].reset_index(drop=True)
    input_sha256 = sha256_file(input_path)
    config_file_sha256 = sha256_file(config_path)
    implementation_revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip()
    run_id = str(uuid4())
    process_id = __import__("os").getpid()
    started_at_utc = datetime.now(UTC).isoformat()
    torch, model, tokenizer, snapshot, tokenizer_loader_warnings = _load_runtime(config)
    tokenizer_vocabulary_diagnostics = _tokenizer_vocabulary_diagnostics(snapshot / "tokenizer")
    embeddings: list[np.ndarray] = []
    token_counts: list[int] = []
    failures: list[dict] = []
    token_diagnostics: list[dict] = []
    started = time.perf_counter()
    try:
        import psutil

        process = psutil.Process()
        peak_rss = process.memory_info().rss
    except ImportError:
        process = None
        peak_rss = None
    batch_size = int(config["batch_size"])
    with torch.inference_mode():
        for start in range(0, len(frame), batch_size):
            batch = frame.iloc[start : start + batch_size]
            token_ids: list[list[int]] = []
            masks: list[list[int]] = []
            valid_indices: list[int] = []
            for local_index, row in enumerate(batch.to_dict(orient="records")):
                prompt = make_prompt(row["standardised_isomeric_smiles"], config)
                try:
                    with warnings.catch_warnings(record=True) as caught:
                        warnings.simplefilter("always")
                        tokenized = tokenizer(
                            {"text": prompt},
                            key_in="text",
                            key_out_tokens_ids="input_ids",
                            key_out_attention_mask="attention_mask",
                        )
                except Exception as error:  # noqa: BLE001 - third-party tokenizer has no stable exception base
                    failures.append(
                        {
                            "drug_id": row["drug_id"],
                            "reason": "TOKENIZATION_FAILURE",
                            "detail": f"{type(error).__name__}: {error}",
                        }
                    )
                    continue
                ids = tokenized["input_ids"]
                mask = tokenized["attention_mask"]
                ids = ids.tolist() if hasattr(ids, "tolist") else list(ids)
                mask = mask.tolist() if hasattr(mask, "tolist") else list(mask)
                warning_messages = sorted({str(item.message) for item in caught})
                unknown_count = ids.count(int(config["unknown_token_id"]))
                if unknown_count or any("unknown token" in item.casefold() for item in warning_messages):
                    failures.append(
                        {
                            "drug_id": row["drug_id"],
                            "reason": "TOKENIZATION_FAILURE",
                            "detail": "unknown token rejected",
                            "unknown_token_id": int(config["unknown_token_id"]),
                            "unknown_token_count": unknown_count,
                            "warnings": warning_messages,
                        }
                    )
                    continue
                if len(ids) > int(config["max_sequence_length"]):
                    failures.append({"drug_id": row["drug_id"], "reason": "OVERLENGTH", "tokens": len(ids)})
                    continue
                token_diagnostics.append(
                    {
                        "drug_id": row["drug_id"],
                        "token_count": int(sum(mask)),
                        "sequence_length": len(ids),
                        "max_sequence_length": int(config["max_sequence_length"]),
                        "truncated": False,
                        "token_id_prefix": ids[:4],
                        "token_id_suffix": ids[-3:],
                        "special_token_layout": config["special_tokens"],
                        "unknown_token_id": int(config["unknown_token_id"]),
                        "unknown_token_count": unknown_count,
                        "warnings": warning_messages,
                    }
                )
                token_ids.append(ids)
                masks.append(mask)
                valid_indices.append(local_index)
            if not token_ids:
                continue
            max_len = max(map(len, token_ids))
            padded_ids = [ids + [0] * (max_len - len(ids)) for ids in token_ids]
            padded_masks = [mask + [0] * (max_len - len(mask)) for mask in masks]
            ids_tensor = torch.tensor(padded_ids, dtype=torch.long, device=config["device"])
            mask_tensor = torch.tensor(padded_masks, dtype=torch.long, device=config["device"])
            inputs = model._calculate_inputs_embeddings(
                {
                    "data.encoder_input_token_ids": ids_tensor,
                    "data.encoder_input_attention_mask": mask_tensor,
                }
            )
            encoded = model.t5_model.encoder(inputs_embeds=inputs, attention_mask=mask_tensor)
            hidden = encoded.last_hidden_state
            pooled = masked_mean_l2(hidden, mask_tensor, torch)
            embeddings.extend(pooled.cpu().numpy().astype(np.float32))
            token_counts.extend([sum(mask) for mask in masks])
            if process is not None:
                peak_rss = max(int(peak_rss or 0), process.memory_info().rss)
    elapsed = time.perf_counter() - started
    if failures:
        failed_ids = {failure["drug_id"] for failure in failures}
        frame = frame[~frame["drug_id"].isin(failed_ids)].reset_index(drop=True)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        target,
        drug_ids=frame["drug_id"].to_numpy(dtype=str),
        embeddings=np.asarray(embeddings, dtype=np.float32),
        token_counts=np.asarray(token_counts, dtype=np.int32),
    )
    model_files = sorted(snapshot.rglob("*.safetensors"))
    tokenizer_root = snapshot / "tokenizer"
    tokenizer_files = sorted(path for path in tokenizer_root.rglob("*") if path.is_file())
    embedding_array = np.asarray(embeddings, dtype=np.float32)
    embedding_norms = (
        np.linalg.norm(embedding_array, axis=1) if embedding_array.size else np.asarray([])
    )
    environment_locks = [Path("environment/mammal-lock.txt"), Path("environment/chemistry-lock.txt")]
    write_json(
        target.with_suffix(".manifest.json"),
        {
            "checkpoint": config["checkpoint"],
            "checkpoint_revision": config["checkpoint_revision"],
            "checkpoint_snapshot": str(snapshot),
            "model_files": {
                _snapshot_relative_posix(path, snapshot): {
                    "sha256": sha256_file(path),
                    "bytes": path.stat().st_size,
                }
                for path in model_files
            },
            "model_total_bytes": sum(path.stat().st_size for path in model_files),
            "tokenizer_files": {
                _snapshot_relative_posix(path, snapshot): {
                    "sha256": sha256_file(path),
                    "bytes": path.stat().st_size,
                }
                for path in tokenizer_files
            },
            "tokenizer_loader_warnings": tokenizer_loader_warnings,
            "tokenizer_vocabulary_diagnostics": tokenizer_vocabulary_diagnostics,
            "tokenizer_native_warning_disposition": (
                "Known non-contiguous reserved vocabulary IDs independently diagnosed from "
                "the pinned JSON files; tokenizer bytes and ID assignments are unchanged."
            ),
            "tokenizer_revision": config["checkpoint_revision"],
            "code_revision": config["code_revision"],
            "implementation_revision": implementation_revision,
            "input_path": str(input_path),
            "input_sha256": input_sha256,
            "config_path": str(config_path),
            "config_file_sha256": config_file_sha256,
            "validated_config_sha256": sha256_json(config),
            "batch_order": "reversed" if reverse_order else "input_order",
            "run_id": run_id,
            "process_id": process_id,
            "started_at_utc": started_at_utc,
            "completed_at_utc": datetime.now(UTC).isoformat(),
            "prompt_prefix": config["prompt_prefix"],
            "prompt_suffix": config["prompt_suffix"],
            "hidden_state": config["hidden_state"],
            "pooling": config["pooling"],
            "special_tokens": config["special_tokens"],
            "max_sequence_length": config["max_sequence_length"],
            "overlength_rule": config["overlength_rule"],
            "unknown_token_id": config["unknown_token_id"],
            "unknown_token_rule": config["unknown_token_rule"],
            "dtype": config["dtype"],
            "device": config["device"],
            "batch_size": batch_size,
            "cpu_model": platform.processor() or platform.machine(),
            "observed_peak_process_rss_bytes": peak_rss,
            "python": platform.python_version(),
            "torch": torch.__version__,
            "environment_locks": {
                str(path): sha256_file(path) for path in environment_locks if path.exists()
            },
            "rows_requested": len(pd.read_csv(input_path)),
            "rows_successful": len(frame),
            "requested_drug_ids": pd.read_csv(input_path)["drug_id"].astype(str).tolist(),
            "successful_drug_ids": frame["drug_id"].astype(str).tolist(),
            "embedding_dimension": int(embedding_array.shape[1]),
            "embedding_norm_min": float(embedding_norms.min()) if embedding_norms.size else None,
            "embedding_norm_max": float(embedding_norms.max()) if embedding_norms.size else None,
            "elapsed_seconds": elapsed,
            "token_count_min": min(token_counts, default=None),
            "token_count_max": max(token_counts, default=None),
            "configured_failure_codes": config["failure_codes"],
            "token_diagnostics": token_diagnostics,
            "failures": failures,
            "output_sha256": sha256_file(target),
        },
    )
    return target


def _compare_embedding_runs(reference, candidate, config: dict) -> dict:
    reference_map = dict(zip(reference["drug_ids"], reference["embeddings"], strict=True))
    candidate_map = dict(zip(candidate["drug_ids"], candidate["embeddings"], strict=True))
    common = sorted(set(reference_map) & set(candidate_map))
    differences = [
        float(np.max(np.abs(reference_map[key] - candidate_map[key]))) for key in common
    ]
    finite = all(
        np.isfinite(reference_map[key]).all() and np.isfinite(candidate_map[key]).all()
        for key in common
    )
    repeatable = all(
        np.allclose(
            reference_map[key],
            candidate_map[key],
            atol=float(config["repeatability_atol"]),
            rtol=float(config["repeatability_rtol"]),
        )
        for key in common
    )
    return {
        "same_successful_ids": set(reference_map) == set(candidate_map),
        "successful_in_both": len(common),
        "finite": finite,
        "within_tolerance": repeatable,
        "maximum_absolute_difference": max(differences, default=None),
    }


def _load_and_validate_run(path: str | Path, expected_order: str) -> tuple[object, dict]:
    target = Path(path)
    manifest_path = target.with_suffix(".manifest.json")
    if not manifest_path.exists():
        raise AssertionError(f"Missing extraction manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["model_files"] = _canonicalize_manifest_file_map(
        manifest.get("model_files"), "model_files"
    )
    manifest["tokenizer_files"] = _canonicalize_manifest_file_map(
        manifest.get("tokenizer_files"), "tokenizer_files"
    )
    _verify_manifest_snapshot_files(manifest)
    run = np.load(target)
    ids = run["drug_ids"].astype(str).tolist()
    token_counts = run["token_counts"].tolist()
    embeddings = run["embeddings"]
    if manifest["batch_order"] != expected_order:
        raise AssertionError(f"Expected {expected_order}, found {manifest['batch_order']}")
    if manifest["output_sha256"] != sha256_file(target):
        raise AssertionError("Manifest output hash does not match NPZ")
    if manifest["rows_successful"] != len(ids) or manifest["successful_drug_ids"] != ids:
        raise AssertionError("Manifest success rows/IDs do not match NPZ")
    requested_ids = manifest["requested_drug_ids"]
    failures = manifest["failures"]
    if manifest["rows_requested"] != len(requested_ids):
        raise AssertionError("Manifest requested row count does not match requested IDs")
    if manifest["rows_successful"] + len(failures) != manifest["rows_requested"]:
        raise AssertionError("Manifest successes and failures do not reconcile")
    if len(requested_ids) != len(set(requested_ids)):
        raise AssertionError("Requested drug IDs are not unique")
    failure_ids = [str(failure.get("drug_id")) for failure in failures]
    if len(failure_ids) != len(set(failure_ids)):
        raise AssertionError("A requested drug has multiple failure records")
    if set(ids) & set(failure_ids):
        raise AssertionError("A drug is recorded as both successful and failed")
    if set(ids) | set(failure_ids) != set(requested_ids):
        raise AssertionError("Successful and failed IDs do not partition requested IDs")
    if not manifest.get("tokenizer_vocabulary_diagnostics"):
        raise AssertionError("Tokenizer vocabulary-hole diagnostics were not recorded")
    diagnostics = manifest["token_diagnostics"]
    diagnostic_ids = [str(item["drug_id"]) for item in diagnostics]
    if diagnostic_ids != ids or len(token_counts) != len(ids):
        raise AssertionError("Token counts/diagnostics do not align with successful NPZ IDs")
    for item, token_count in zip(diagnostics, token_counts, strict=True):
        if item["token_count"] != token_count:
            raise AssertionError("NPZ token count disagrees with manifest diagnostic")
        if item["unknown_token_count"] != 0 or item["truncated"]:
            raise AssertionError("A successful row has unknown tokens or truncation")
        if any("unknown token" in warning.casefold() for warning in item["warnings"]):
            raise AssertionError("A successful row has an unknown-token warning")
    if embeddings.ndim != 2 or embeddings.shape[1] != 768:
        raise AssertionError("Expected 768-dimensional MAMMAL vectors")
    if manifest["embedding_dimension"] != embeddings.shape[1]:
        raise AssertionError("Manifest embedding dimension does not match NPZ")
    if not np.isfinite(embeddings).all():
        raise AssertionError("Embedding run contains non-finite values")
    norms = np.linalg.norm(embeddings, axis=1)
    if not np.allclose(norms, 1.0, atol=1e-5, rtol=1e-5):
        raise AssertionError("Embedding run contains non-unit vectors")
    if not np.isclose(manifest["embedding_norm_min"], norms.min(), atol=1e-7):
        raise AssertionError("Manifest minimum norm does not match NPZ")
    if not np.isclose(manifest["embedding_norm_max"], norms.max(), atol=1e-7):
        raise AssertionError("Manifest maximum norm does not match NPZ")
    return run, manifest


def validate_pilot(
    baseline_path: str | Path,
    same_order_path: str | Path,
    reordered_path: str | Path,
    config_path: str | Path,
    report_path: str | Path,
    *,
    require_pa03_frozen_artifacts: bool = False,
    validation_implementation_revision: str | None = None,
) -> dict:
    frozen_artifacts = None
    if require_pa03_frozen_artifacts:
        frozen_artifacts = _verify_pa03_frozen_pilot_artifacts(
            [baseline_path, same_order_path, reordered_path]
        )
        if not validation_implementation_revision:
            raise AssertionError("PA-03 validation implementation revision is required")
    config = validate_config(config_path)
    baseline, baseline_manifest = _load_and_validate_run(baseline_path, "input_order")
    same_order, same_manifest = _load_and_validate_run(same_order_path, "input_order")
    reordered, reordered_manifest = _load_and_validate_run(reordered_path, "reversed")
    manifests = [baseline_manifest, same_manifest, reordered_manifest]
    pa03_lineage = None
    if require_pa03_frozen_artifacts:
        pa03_lineage = _validate_pa03_lineage(
            manifests, validation_implementation_revision
        )
        expected_input = Path("audit/pilot/frozen_pilot_v2.csv")
        if not expected_input.is_file():
            raise AssertionError("PA-03 frozen pilot input is missing")
        if any(manifest["input_sha256"] != sha256_file(expected_input) for manifest in manifests):
            raise AssertionError("Frozen pilot input hash does not match PA-03 manifests")
        if any(manifest["config_file_sha256"] != sha256_file(config_path) for manifest in manifests):
            raise AssertionError("Current embedding config does not match PA-03 manifests")
        if any(manifest["validated_config_sha256"] != sha256_json(config) for manifest in manifests):
            raise AssertionError("Validated embedding config does not match PA-03 manifests")
    invariant_fields = [
        "input_sha256",
        "config_file_sha256",
        "validated_config_sha256",
        "code_revision",
        "implementation_revision",
        "checkpoint",
        "checkpoint_revision",
        "checkpoint_snapshot",
        "model_files",
        "model_total_bytes",
        "tokenizer_files",
        "tokenizer_loader_warnings",
        "tokenizer_revision",
        "prompt_prefix",
        "prompt_suffix",
        "hidden_state",
        "pooling",
        "dtype",
        "device",
        "batch_size",
        "max_sequence_length",
        "unknown_token_rule",
        "unknown_token_id",
        "overlength_rule",
        "special_tokens",
        "environment_locks",
        "tokenizer_vocabulary_diagnostics",
    ]
    for field in invariant_fields:
        if any(manifest[field] != manifests[0][field] for manifest in manifests[1:]):
            raise AssertionError(f"Pilot manifests disagree on {field}")
    run_ids = [manifest["run_id"] for manifest in manifests]
    process_ids = [manifest["process_id"] for manifest in manifests]
    if len(set(run_ids)) != 3 or len(set(process_ids)) != 3:
        raise AssertionError("Pilot outputs are not from three distinct fresh processes")
    timestamps = [datetime.fromisoformat(manifest["started_at_utc"]) for manifest in manifests]
    if any(value.tzinfo is None for value in timestamps) or len(set(timestamps)) != 3:
        raise AssertionError("Pilot start timestamps are not distinct timezone-aware values")
    process_repeatability = _compare_embedding_runs(baseline, same_order, config)
    batch_order_invariance = _compare_embedding_runs(baseline, reordered, config)
    required = int(config["pilot_required_successes"])
    passed = all(
        comparison["successful_in_both"] >= required
        and comparison["same_successful_ids"]
        and comparison["finite"]
        and comparison["within_tolerance"]
        for comparison in (process_repeatability, batch_order_invariance)
    )
    report = {
        "passed": passed,
        "required_successes": required,
        "process_repeatability": process_repeatability,
        "batch_order_invariance": batch_order_invariance,
        "outputs": {
            "baseline_sha256": sha256_file(baseline_path),
            "same_order_sha256": sha256_file(same_order_path),
            "reordered_sha256": sha256_file(reordered_path),
        },
        "fresh_process_evidence": {
            "distinct_run_ids": run_ids,
            "distinct_process_ids": process_ids,
            "started_at_utc": [manifest["started_at_utc"] for manifest in manifests],
        },
        "manifest_invariants_verified": invariant_fields,
        "pa03_validation_only_reuse": require_pa03_frozen_artifacts,
        "frozen_artifacts": frozen_artifacts,
        "pa03_revision_lineage": pa03_lineage,
    }
    write_json(report_path, report)
    return report


def validate_full_extraction(
    input_path: str | Path,
    expected_sample_path: str | Path,
    full_path: str | Path,
    repeat_sample_path: str | Path,
    config_path: str | Path,
    report_path: str | Path,
) -> dict:
    config = validate_config(config_path)
    requested = pd.read_csv(input_path)["drug_id"].astype(str).tolist()
    expected_repeat_ids = pd.read_csv(expected_sample_path)["drug_id"].astype(str).tolist()
    full, full_manifest = _load_and_validate_run(full_path, "input_order")
    repeat, repeat_manifest = _load_and_validate_run(repeat_sample_path, "input_order")
    full_ids = full["drug_ids"].astype(str).tolist()
    repeat_ids = repeat["drug_ids"].astype(str).tolist()
    if full_manifest["input_sha256"] != sha256_file(input_path):
        raise AssertionError("Full extraction manifest input hash does not match frozen input")
    if repeat_manifest["input_sha256"] != sha256_file(expected_sample_path):
        raise AssertionError("Repeat manifest input hash does not match deterministic sample")
    if repeat_manifest["requested_drug_ids"] != expected_repeat_ids or repeat_ids != expected_repeat_ids:
        raise AssertionError("Repeat extraction IDs/order do not exactly match deterministic sample")
    if not set(repeat_ids).issubset(full_ids):
        raise AssertionError("Verification sample contains IDs absent from full extraction")
    if full_manifest["run_id"] == repeat_manifest["run_id"] or full_manifest["process_id"] == repeat_manifest["process_id"]:
        raise AssertionError("Verification extraction is not from a distinct clean process")
    timestamps = [
        datetime.fromisoformat(full_manifest["started_at_utc"]),
        datetime.fromisoformat(repeat_manifest["started_at_utc"]),
    ]
    if any(timestamp.tzinfo is None for timestamp in timestamps) or timestamps[0] == timestamps[1]:
        raise AssertionError("Extraction timestamps must be distinct and timezone-aware")
    invariant_fields = [
        "config_file_sha256",
        "validated_config_sha256",
        "code_revision",
        "implementation_revision",
        "checkpoint",
        "checkpoint_revision",
        "checkpoint_snapshot",
        "model_files",
        "model_total_bytes",
        "tokenizer_files",
        "tokenizer_loader_warnings",
        "tokenizer_revision",
        "prompt_prefix",
        "prompt_suffix",
        "hidden_state",
        "pooling",
        "dtype",
        "device",
        "batch_size",
        "max_sequence_length",
        "overlength_rule",
        "unknown_token_id",
        "unknown_token_rule",
        "special_tokens",
        "environment_locks",
        "tokenizer_vocabulary_diagnostics",
    ]
    for field in invariant_fields:
        if full_manifest[field] != repeat_manifest[field]:
            raise AssertionError(f"Full and repeat manifests disagree on {field}")
    full_map = dict(zip(full_ids, full["embeddings"], strict=True))
    repeat_map = dict(zip(repeat_ids, repeat["embeddings"], strict=True))
    differences = [
        float(np.max(np.abs(full_map[drug_id] - repeat_map[drug_id])))
        for drug_id in repeat_ids
    ]
    repeatable = all(
        np.allclose(
            full_map[drug_id],
            repeat_map[drug_id],
            atol=float(config["repeatability_atol"]),
            rtol=float(config["repeatability_rtol"]),
        )
        for drug_id in repeat_ids
    )
    coverage = len(full_ids) / len(requested)
    passed = (
        full_ids == requested
        and coverage == 1.0
        and coverage >= float(config["full_cohort_minimum_coverage"])
        and repeatable
        and len(repeat_ids) == len(set(repeat_ids))
        and len(repeat_ids) == max(1, int(np.ceil(len(requested) * 0.05)))
    )
    report = {
        "passed": passed,
        "requested": len(requested),
        "successful": len(full_ids),
        "coverage": coverage,
        "minimum_coverage": float(config["full_cohort_minimum_coverage"]),
        "verification_sample_size": len(repeat_ids),
        "verification_fraction_of_requested": len(repeat_ids) / len(requested),
        "repeatable": repeatable,
        "distinct_processes": True,
        "maximum_absolute_difference": max(differences, default=None),
        "full_output_sha256": sha256_file(full_path),
        "repeat_output_sha256": sha256_file(repeat_sample_path),
        "expected_sample_sha256": sha256_file(expected_sample_path),
        "expected_sample_drug_ids": expected_repeat_ids,
        "sampling_seed": int(validate_config("configs/seeds.yaml")["embedding_verification_sample"]),
        "started_at_utc": [manifest["started_at_utc"] for manifest in [full_manifest, repeat_manifest]],
        "manifest_invariants_verified": invariant_fields,
    }
    write_json(report_path, report)
    return report
