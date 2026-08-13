from __future__ import annotations

import platform
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from mammal_dili.config import validate_config_bundle
from mammal_dili.io import sha256_file, write_json

LOCK_PATH = Path("audit/protocol_lock/execution_lock.json")
CLEARANCE_PATH = Path("audit/governance/2026-08-12-user-reported-clearance.md")
AMENDMENT_PATHS = {
    "PA-01": Path("audit/pilot/protocol-amendment-pa-01.md"),
    "PA-02": Path("audit/protocol_lock/protocol-amendment-pa-02.md"),
    "PA-03": Path("audit/protocol_lock/protocol-amendment-pa-03.md"),
}
LOCKED_IMPLEMENTATION_PATHS = [
    "configs",
    "environment",
    "pyproject.toml",
    "scripts",
    "src/mammal_dili",
    "tests/python",
]


def _git_revision() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def _validate_amendments() -> dict[str, str]:
    hashes = {}
    for label, path in AMENDMENT_PATHS.items():
        if not path.exists():
            raise RuntimeError(f"Missing required protocol amendment: {path}")
        text = path.read_text(encoding="utf-8")
        approvals = text.split("## Required approvals", 1)[-1]
        if "Status: APPROVED" not in text or "| Pending" in approvals:
            raise RuntimeError(f"{label} is not fully approved; execution lock refused")
        hashes[label] = sha256_file(path)
    return hashes


def create_protocol_lock(path: str | Path = LOCK_PATH) -> dict:
    if not CLEARANCE_PATH.exists():
        raise RuntimeError(f"Missing required governance evidence: {CLEARANCE_PATH}")
    bundle, bundle_hash = validate_config_bundle("configs")
    amendment_hashes = _validate_amendments()
    marker = {
        "schema_version": 1,
        "status": "LOCKED_FOR_EXECUTION",
        "locked_at_utc": datetime.now(UTC).isoformat(),
        "protocol_baseline_revision": "0b16bd9c903dfaf1088dca8ad198c351db7fa1b7",
        "implementation_revision_at_lock": _git_revision(),
        "config_bundle_sha256": bundle_hash,
        "config_files": sorted(bundle),
        "governance_evidence": str(CLEARANCE_PATH),
        "governance_evidence_sha256": sha256_file(CLEARANCE_PATH),
        "approved_amendment_hashes": amendment_hashes,
        "python": platform.python_version(),
        "platform": platform.platform(),
    }
    write_json(path, marker)
    return marker


def require_protocol_lock(path: str | Path = LOCK_PATH) -> dict:
    target = Path(path)
    if not target.exists():
        raise RuntimeError("Outcome modelling refused: protocol execution lock is missing")
    import json

    marker = json.loads(target.read_text(encoding="utf-8"))
    _, current_hash = validate_config_bundle("configs")
    if marker.get("status") != "LOCKED_FOR_EXECUTION":
        raise RuntimeError("Outcome modelling refused: protocol lock is not active")
    if marker.get("config_bundle_sha256") != current_hash:
        raise RuntimeError("Outcome modelling refused: configuration changed after protocol lock")
    current_amendments = _validate_amendments()
    if marker.get("approved_amendment_hashes") != current_amendments:
        raise RuntimeError("Outcome modelling refused: approved amendment changed after protocol lock")
    locked_revision = marker.get("implementation_revision_at_lock")
    if not locked_revision:
        raise RuntimeError("Outcome modelling refused: implementation revision is absent")
    subprocess.check_call(["git", "merge-base", "--is-ancestor", locked_revision, "HEAD"])
    committed_drift = subprocess.check_output(
        ["git", "diff", "--name-only", f"{locked_revision}..HEAD", "--", *LOCKED_IMPLEMENTATION_PATHS],
        text=True,
    ).strip()
    dirty_drift = subprocess.check_output(
        ["git", "status", "--porcelain", "--", *LOCKED_IMPLEMENTATION_PATHS], text=True
    ).strip()
    if committed_drift or dirty_drift:
        raise RuntimeError(
            "Outcome modelling refused: implementation changed after protocol lock"
        )
    return marker
