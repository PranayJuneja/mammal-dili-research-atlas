from collections import Counter

from mammal_dili.acquisition.dilirank import parse_fda_snapshot
from mammal_dili.acquisition.pubchem import candidate_names


def test_fda_snapshot_has_locked_counts() -> None:
    frame = parse_fda_snapshot("data/raw/dilirank_2_0_fda_page.md")
    assert len(frame) == 1336
    assert Counter(frame["dili_category"]) == {
        "vMost-DILI-concern": 217,
        "vLess-DILI-concern": 351,
        "vNo-DILI-concern": 414,
        "Ambiguous-DILI-concern": 354,
    }
    assert frame["release_group"].value_counts().to_dict() == {
        "original-list": 1036,
        "added-in-2.0": 300,
    }


def test_pubchem_candidate_names_make_salt_fallback_explicit() -> None:
    assert candidate_names("Fluoxetine hydrochloride") == [
        ("Fluoxetine hydrochloride", "exact-name"),
        ("Fluoxetine", "salt-suffix-fallback"),
    ]
    assert candidate_names("Aspirin") == [("Aspirin", "exact-name")]

