from __future__ import annotations

import platform
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from mammal_dili.config import validate_config_bundle
from mammal_dili.io import sha256_file, write_json

LOCK_PATH = Path("audit/protocol_lock/execution_lock.json")
CLEARANCE_PATH = Path("audit/governance/2026-08-12-user-reported-clearance.md")


def _git_revision() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def create_protocol_lock(path: str | Path = LOCK_PATH) -> dict:
    if not CLEARANCE_PATH.exists():
        raise RuntimeError(f"Missing required governance evidence: {CLEARANCE_PATH}")
    bundle, bundle_hash = validate_config_bundle("configs")
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
    return marker
