from __future__ import annotations

import platform
import subprocess
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from mammal_dili.config import validate_config
from mammal_dili.io import sha256_file, sha256_json, write_json


def make_prompt(smiles: str, config: dict) -> str:
    return f"{config['prompt_prefix']}{smiles}{config['prompt_suffix']}"


def masked_mean_l2(hidden, attention_mask, torch):
    """Pool non-padding encoder states and L2-normalise each row."""
    expanded_mask = attention_mask.unsqueeze(-1).to(dtype=hidden.dtype)
    denominator = expanded_mask.sum(dim=1).clamp_min(1.0)
    pooled = (hidden * expanded_mask).sum(dim=1) / denominator
    return torch.nn.functional.normalize(pooled, p=2, dim=1)


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


def _load_runtime(config: dict):
    import torch
    from fuse.data.tokenizers.modular_tokenizer.op import ModularTokenizerOp
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
    tokenizer = ModularTokenizerOp.from_pretrained(snapshot / "tokenizer")
    return torch, model, tokenizer, snapshot


def preflight_pilot(
    input_path: str | Path, config_path: str | Path, report_path: str | Path
) -> dict:
    """Validate chemistry and pinned-tokenizer behavior without loading model weights."""
    from fuse.data.tokenizers.modular_tokenizer.op import ModularTokenizerOp
    from huggingface_hub import snapshot_download
    from rdkit import Chem

    config = validate_config(config_path)
    frame = pd.read_csv(input_path)
    snapshot = Path(
        snapshot_download(
            repo_id=config["checkpoint"], revision=config["checkpoint_revision"]
        )
    )
    tokenizer = ModularTokenizerOp.from_pretrained(snapshot / "tokenizer")
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
    torch, model, tokenizer, snapshot = _load_runtime(config)
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
    tokenizer_files = sorted(
        path
        for path in snapshot.rglob("*")
        if path.is_file() and any(term in path.name.casefold() for term in ("token", "vocab", "merges"))
    )
    environment_locks = [Path("environment/mammal-lock.txt"), Path("environment/chemistry-lock.txt")]
    write_json(
        target.with_suffix(".manifest.json"),
        {
            "checkpoint": config["checkpoint"],
            "checkpoint_revision": config["checkpoint_revision"],
            "checkpoint_snapshot": str(snapshot),
            "model_files": {
                str(path.relative_to(snapshot)): {"sha256": sha256_file(path), "bytes": path.stat().st_size}
                for path in model_files
            },
            "model_total_bytes": sum(path.stat().st_size for path in model_files),
            "tokenizer_files": {
                str(path.relative_to(snapshot)): {"sha256": sha256_file(path), "bytes": path.stat().st_size}
                for path in tokenizer_files
            },
            "tokenizer_revision": config["checkpoint_revision"],
            "code_revision": config["code_revision"],
            "implementation_revision": implementation_revision,
            "input_path": str(input_path),
            "input_sha256": input_sha256,
            "config_path": str(config_path),
            "config_file_sha256": config_file_sha256,
            "validated_config_sha256": sha256_json(config),
            "batch_order": "reversed" if reverse_order else "input_order",
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
            "embedding_dimension": int(np.asarray(embeddings).shape[1]),
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


def validate_pilot(
    baseline_path: str | Path,
    same_order_path: str | Path,
    reordered_path: str | Path,
    config_path: str | Path,
    report_path: str | Path,
) -> dict:
    config = validate_config(config_path)
    baseline = np.load(baseline_path)
    same_order = np.load(same_order_path)
    reordered = np.load(reordered_path)
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
    }
    write_json(report_path, report)
    return report
