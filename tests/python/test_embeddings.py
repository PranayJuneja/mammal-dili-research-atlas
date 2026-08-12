import numpy as np

from mammal_dili.embeddings.mammal import make_prompt, validate_pilot


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


def test_pilot_validation_separates_process_and_order_checks(tmp_path) -> None:
    ids = np.array([f"PILOT-{index:02d}" for index in range(1, 21)])
    vectors = np.arange(80, dtype=np.float32).reshape(20, 4)
    baseline = tmp_path / "baseline.npz"
    same = tmp_path / "same.npz"
    reversed_run = tmp_path / "reversed.npz"
    np.savez_compressed(baseline, drug_ids=ids, embeddings=vectors)
    np.savez_compressed(same, drug_ids=ids, embeddings=vectors.copy())
    np.savez_compressed(
        reversed_run, drug_ids=ids[::-1], embeddings=vectors[::-1].copy()
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
