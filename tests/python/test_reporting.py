import json

from mammal_dili.reporting.report import (
    SITE_DOWNLOAD_FILES,
    TRIPOD_AI_ITEM_IDS,
    _kuhs_submission_protocol,
    _paper_markdown,
    _plain_language_summary,
    _presentation_outline,
    _publish_site_bundle,
    _tripod_ai_mapping,
    _tripod_ai_rows,
)


def _summary() -> dict:
    return {
        "primary": {
            "delta_auroc": 0.012,
            "ci95": [-0.01, 0.035],
            "interpretation": "Inconclusive for superiority and practical importance.",
            "practical_gain_benchmark": 0.03,
            "repeat_deltas": [0.01, 0.02, 0.0, 0.015, 0.015],
        },
        "flow": {
            "eligible_drugs": 809,
            "excluded_drugs": 173,
            "dilirank_records": 1336,
            "non_ambiguous_records_considered": 982,
            "development_drugs": 675,
            "update_drugs": 134,
            "scaffold_groups": 568,
            "development_groups": 460,
            "update_groups": 125,
        },
        "update_transport": {
            "paired_delta_auroc": {
                "estimate": 0.004,
                "ci95": [-0.02, 0.03],
            }
        },
        "models": {},
        "model_repeat_uncertainty": {},
        "robustness": {},
        "precision_diagnostics": {
            "minimum_empirical_coverage": 0.825,
            "maximum_mean_ci_width": 0.05474,
            "maximum_endpoint_shift_100_to_2000": 0.00797,
        },
        "important_false_negative_rows": 0,
        "convergence": {"primary": {"warning_count": 0}},
    }


def test_reporting_companions_are_complete_and_kuhs_limited() -> None:
    summary = _summary()
    protocol, counts = _kuhs_submission_protocol(summary)
    assert "## Methodology" in protocol
    assert all(value["words"] <= value["limit"] for value in counts.values())
    assert "drug-level research benchmark" in _plain_language_summary(summary)
    assert "TRIPOD+AI applicability map" in _tripod_ai_mapping()
    assert "Primary answer" in _presentation_outline(summary)
    paper = _paper_markdown(summary)
    assert "## References" in paper
    assert "10.1016/j.drudis.2025.104485" in paper
    assert "10.1038/s44386-026-00047-4" in paper
    assert "10.1021/ci100050t" in paper
    assert "10.1021/jm9602928" in paper
    assert "10.1136/bmj-2023-078378" in paper


def test_tripod_ai_mapping_has_every_official_subitem_and_honest_states() -> None:
    rows = _tripod_ai_rows()
    assert len(rows) == 52
    assert tuple(row["item"] for row in rows) == TRIPOD_AI_ITEM_IDS
    assert {row["status"] for row in rows} >= {"Reported", "Pending", "Not applicable"}
    assert all(row["evidence_location"] for row in rows)
    mapping = _tripod_ai_mapping()
    assert "10.1136/bmj-2023-078378" in mapping
    assert "resolve every `Pending` row" in mapping


def test_publish_site_bundle_copies_complete_frozen_packet(tmp_path) -> None:
    report = tmp_path / "report"
    public = tmp_path / "public"
    report.mkdir()
    for filename in SITE_DOWNLOAD_FILES:
        (report / filename).write_text(f"contents of {filename}", encoding="utf-8")

    published = _publish_site_bundle(report, public)

    assert set(published) == set(SITE_DOWNLOAD_FILES)
    assert (public / "research_report.md").read_text(encoding="utf-8").startswith("contents")
    manifest = json.loads((public / "download_manifest.json").read_text(encoding="utf-8"))
    assert manifest["files"] == published
