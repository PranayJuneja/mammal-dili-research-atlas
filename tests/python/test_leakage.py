import numpy as np
import pandas as pd

from mammal_dili.curation.structures import _resolve_duplicates
from mammal_dili.modelling.nested_cv import FeatureSet, _pipeline, split_development_and_update


def _config() -> dict:
    return {
        "solver": "liblinear",
        "class_weight": None,
        "max_iterations": 100,
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
