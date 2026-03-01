#!/usr/bin/env python3
"""Regression tests for ConfirmationAPI bootstrap behavior."""

from __future__ import annotations

from pathlib import Path

from lib.api import ConfirmationAPI


def test_confirmation_api_bootstraps_gep_store_when_missing(tmp_path: Path) -> None:
    memory_dir = tmp_path / ".openclaw_memory"

    api = ConfirmationAPI(memory_dir=memory_dir)

    assert api.gep_store is not None
    assert (memory_dir / "gep").exists()
    assert (memory_dir / "gep" / "genes.json").exists()
    assert (memory_dir / "gep" / "capsules.json").exists()
    assert (memory_dir / "gep" / "events.jsonl").exists()


def test_confirmation_api_records_feedback_on_first_run(tmp_path: Path) -> None:
    memory_dir = tmp_path / ".openclaw_memory"
    api = ConfirmationAPI(memory_dir=memory_dir)

    task = {
        "task_type": "T2",
        "task_description": "Run tests",
        "command": "python -m pytest tests/",
    }

    api.record_execution_result(task=task, success=True, auto_executed=True)
    history = api.get_confidence_history(task_type="T2")

    assert history["genes"], "Expected at least one learned gene after first execution."
