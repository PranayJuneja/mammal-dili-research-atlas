from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests

from mammal_dili.config import validate_config
from mammal_dili.io import sha256_file, write_json

LABEL_NORMALIZATION = {
    "vMOST-DILI-concern": "vMost-DILI-concern",
    "vNo-DILI-Concern": "vNo-DILI-concern",
}


def parse_fda_snapshot(snapshot_path: str | Path) -> pd.DataFrame:
    path = Path(snapshot_path)
    rows: list[list[str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split("\t")
        if len(fields) == 6 and fields[0].startswith("LT") and fields[0][2:].isdigit():
            rows.append(fields)
    frame = pd.DataFrame(
        rows,
        columns=[
            "dilirank_id",
            "compound_name_source",
            "severity_class",
            "label_section",
            "dili_category",
            "release_comment",
        ],
    )
    frame["dili_category"] = frame["dili_category"].replace(LABEL_NORMALIZATION)
    frame["severity_class"] = pd.to_numeric(frame["severity_class"], errors="coerce").astype("Int64")
    frame["release_group"] = frame["release_comment"].map(
        lambda value: "added-in-2.0" if value == "New" else "original-list"
    )
    frame["outcome"] = frame["dili_category"].map(
        {"vMost-DILI-concern": 1, "vLess-DILI-concern": 1, "vNo-DILI-concern": 0}
    )
    return frame


def acquire_dilirank(config_path: str | Path, output_path: str | Path) -> pd.DataFrame:
    config = validate_config(config_path)["dilirank"]
    snapshot = Path(config["snapshot_path"])
    if not snapshot.exists():
        response = requests.get(
            config["snapshot_transport"],
            timeout=60,
            headers={"User-Agent": "mammal-dili-research/0.1"},
        )
        response.raise_for_status()
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_bytes(response.content)
    frame = parse_fda_snapshot(config["snapshot_path"])
    counts = Counter(frame["dili_category"])
    expected_counts = config["expected_labels"]
    if len(frame) != config["expected_records"]:
        raise ValueError(f"Expected {config['expected_records']} rows, found {len(frame)}")
    if dict(counts) != expected_counts:
        raise ValueError(f"Label counts differ: expected {expected_counts}, found {dict(counts)}")
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(target, index=False)
    write_json(
        target.with_suffix(".manifest.json"),
        {
            "created_at_utc": datetime.now(UTC).isoformat(),
            "canonical_url": config["canonical_url"],
            "transport_url": config["snapshot_transport"],
            "licence": config["licence"],
            "snapshot_path": config["snapshot_path"],
            "snapshot_sha256": sha256_file(config["snapshot_path"]),
            "output_sha256": sha256_file(target),
            "record_count": len(frame),
            "label_counts": dict(counts),
            "release_counts": frame["release_group"].value_counts().to_dict(),
        },
    )
    return frame
