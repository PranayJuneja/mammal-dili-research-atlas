import numpy as np
import pandas as pd
import pytest

from mammal_dili.curation.structures import _resolve_duplicates
from mammal_dili.io import sha256_file
from mammal_dili.modelling import nested_cv
from mammal_dili.modelling.nested_cv import (
    FeatureSet,
    _pipeline,
    split_development_and_update,
    validation_group_vectors,
)


def _config() -> dict:
    return {
        "solver": "liblinear",
        "class_weight": None,
        "max_iterations": 100,
        "tolerance": 0.0001,
        "fit_intercept": True,
        "classifier_seed": 17,
    }


def test_test_only_extreme_cannot_change_training_scaler() -> None:
    training = np.array([[0.0], [2.0], [4.0], [6.0]])
    feature_set = FeatureSet(np.vstack([training, [[1_000_000.0]]]), [0])
    pipeline = _pipeline(feature_set, 1.0, _config())
    pipeline.fit(training, np.array([0, 0, 1, 1]))
    scaler = pipeline.named_steps["features"].named_transformers_["continuous"].named_steps["scale"]
    assert scaler.mean_.tolist() == [3.0]


def test_duplicate_parent_with_conflicting_labels_is_excluded_as_a_unit() -> None:
    frame = pd.DataFrame(
        {
            "parent_inchikey": ["SAME", "SAME"],
            "eligibility": [True, True],
            "outcome": [0, 1],
            "dilirank_id": ["LT1", "LT2"],
            "exclusion_code": [None, None],
        }
    )
    result = _resolve_duplicates(frame)
    assert not result["eligibility"].any()
    assert set(result["exclusion_code"]) == {"DUPLICATE_LABEL_CONFLICT"}


def test_update_cohort_never_enters_development_fit_object() -> None:
    frame = pd.DataFrame(
        {
            "drug_id": ["old-1", "old-2", "new-1"],
            "release_group": ["original-list", "original-list", "added-in-2.0"],
        }
    )
    development, update = split_development_and_update(frame)
    assert development["drug_id"].tolist() == ["old-1", "old-2"]
    assert update["drug_id"].tolist() == ["new-1"]


def test_random_split_preserves_chemical_groups_for_bootstrap() -> None:
    frame = pd.DataFrame(
        {"drug_id": ["a", "b"], "scaffold_id": ["shared", "shared"]}
    )
    chemical, split = validation_group_vectors(frame, "stratified_random")
    assert chemical.tolist() == ["shared", "shared"]
    assert split.tolist() == ["a", "b"]


def test_nested_cv_passes_only_original_list_to_feature_loading(tmp_path, monkeypatch) -> None:
    rows = []
    for index in range(20):
        rows.append(
            {
                "drug_id": f"old-{index}",
                "release_group": "original-list",
                "outcome": index % 2,
                "scaffold_id": f"group-{index}",
                "compound_name_source": f"old {index}",
                "dili_category": "vMost-DILI-concern" if index % 2 else "vNo-DILI-concern",
                **{f"outer_fold_repeat_{repeat}": index % 5 for repeat in range(5)},
            }
        )
    rows.append(
        {
            "drug_id": "new-never-fit",
            "release_group": "added-in-2.0",
            "outcome": 1,
            "scaffold_id": "new-group",
            "compound_name_source": "new",
            "dili_category": "vMost-DILI-concern",
            **{f"outer_fold_repeat_{repeat}": 0 for repeat in range(5)},
        }
    )
    folds = tmp_path / "folds.csv"
    pd.DataFrame(rows).to_csv(folds, index=False)
    ids = np.array([row["drug_id"] for row in rows])
    conventional = tmp_path / "conventional.npz"
    mammal = tmp_path / "mammal.npz"
    np.savez_compressed(
        conventional,
        drug_ids=ids,
        descriptors=np.zeros((len(ids), 1)),
        morgan=np.zeros((len(ids), 1)),
    )
    np.savez_compressed(mammal, drug_ids=ids, embeddings=np.zeros((len(ids), 1)))
    seen: list[list[str]] = []

    def stop_after_feature_load(model, drug_ids, conventional_path, mammal_path):
        seen.append(drug_ids)
        raise RuntimeError("stop")

    monkeypatch.setattr(nested_cv, "require_protocol_lock", lambda: {"config_bundle_sha256": "x"})
    monkeypatch.setattr(
        nested_cv,
        "require_feature_fold_lock",
        lambda: {
            "source_hashes": {
                "development_folds": sha256_file(folds),
                "conventional": sha256_file(conventional),
                "mammal": sha256_file(mammal),
            }
        },
    )
    monkeypatch.setattr(nested_cv, "load_feature_set", stop_after_feature_load)
    with pytest.raises(RuntimeError, match="stop"):
        nested_cv.run_nested_cv(
            folds,
            conventional,
            mammal,
            "configs/analysis.yaml",
            tmp_path / "predictions.csv",
        )

    assert seen
    assert "new-never-fit" not in seen[0]
    assert len(seen[0]) == 20
