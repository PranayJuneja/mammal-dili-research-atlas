import json

from mammal_dili.reporting.report import (
    SITE_DOWNLOAD_FILES,
    _kuhs_submission_protocol,
    _plain_language_summary,
    _presentation_outline,
    _publish_site_bundle,
    _tripod_ai_mapping,
)


def _summary() -> dict:
    return {
        "primary": {
            "delta_auroc": 0.012,
            "ci95": [-0.01, 0.035],
            "interpretation": "Inconclusive for superiority and practical importance.",
        },
        "flow": {
            "eligible_drugs": 809,
            "development_drugs": 675,
            "update_drugs": 134,
        },
        "update_transport": {
            "paired_delta_auroc": {
                "estimate": 0.004,
                "ci95": [-0.02, 0.03],
            }
        },
    }


def test_reporting_companions_are_complete_and_kuhs_limited() -> None:
    summary = _summary()
    protocol, counts = _kuhs_submission_protocol(summary)
    assert "## Methodology" in protocol
    assert all(value["words"] <= value["limit"] for value in counts.values())
    assert "drug-level research benchmark" in _plain_language_summary(summary)
    assert "TRIPOD+AI applicability map" in _tripod_ai_mapping()
    assert "Primary answer" in _presentation_outline(summary)


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
