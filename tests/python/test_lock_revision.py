import subprocess

import pytest

from mammal_dili import lock


def test_protocol_lock_rejects_committed_implementation_drift(tmp_path, monkeypatch) -> None:
    marker = {
        "status": "LOCKED_FOR_EXECUTION",
        "config_bundle_sha256": "same",
        "implementation_revision_at_lock": "locked",
        "approved_amendment_hashes": {"PA": "same"},
    }
    marker_path = tmp_path / "lock.json"
    marker_path.write_text(__import__("json").dumps(marker), encoding="utf-8")
    monkeypatch.setattr(lock, "validate_config_bundle", lambda _: ({}, "same"))
    monkeypatch.setattr(lock, "_validate_amendments", lambda: {"PA": "same"})
    monkeypatch.setattr(subprocess, "check_call", lambda *args, **kwargs: 0)

    def output(command, **kwargs):
        if command[1] == "diff":
            return "src/mammal_dili/modelling/nested_cv.py\n"
        return ""

    monkeypatch.setattr(subprocess, "check_output", output)
    with pytest.raises(RuntimeError, match="implementation changed"):
        lock.require_protocol_lock(marker_path)
