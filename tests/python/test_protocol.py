from copy import deepcopy

import numpy as np
import pytest
import yaml

from mammal_dili.config import validate_config
from mammal_dili.embeddings.mammal import select_blind_pilot
from mammal_dili.lock import require_protocol_lock


def test_unknown_configuration_key_is_rejected(tmp_path) -> None:
    with open("configs/features.yaml", encoding="utf-8") as handle:
        source = yaml.safe_load(handle)
    altered = deepcopy(source)
    altered["surprise"] = True
    target = tmp_path / "features.yaml"
    target.write_text(yaml.safe_dump(altered), encoding="utf-8")
    with pytest.raises(ValueError, match="surprise"):
        validate_config(target)


def test_missing_protocol_lock_refuses_outcome_modelling(tmp_path) -> None:
    with pytest.raises(RuntimeError, match="lock is missing"):
        require_protocol_lock(tmp_path / "missing.json")


def test_frozen_pilot_is_label_blind_and_covers_technical_extremes(tmp_path) -> None:
    frame = select_blind_pilot("unused.csv", tmp_path / "pilot.csv")
    assert list(frame.columns) == ["drug_id", "standardised_isomeric_smiles", "selection_rationale"]
    assert len(frame) == 20
    assert frame["standardised_isomeric_smiles"].str.contains(r"\[O-\]").any()
    assert frame["selection_rationale"].str.contains("macrocycle").any()
    assert frame["standardised_isomeric_smiles"].str.len().max() >= 1800
    assert not any("dili" in column.casefold() or "outcome" in column.casefold() for column in frame)


def test_complete_group_resample_never_splits_a_group() -> None:
    groups = np.array(["a", "a", "b", "c", "c"])
    rng = np.random.default_rng(7)
    sampled = rng.choice(np.unique(groups), size=3, replace=True)
    rows = np.concatenate([np.flatnonzero(groups == group) for group in sampled])
    for group in sampled:
        assert set(np.flatnonzero(groups == group)).issubset(set(rows))
