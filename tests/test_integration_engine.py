#!/usr/bin/env python3
"""
IntentAlignmentEngine行为测试
"""

import json

from lib.integration import IntentAlignmentEngine


def test_update_preferences_preserves_config_wrapper(tmp_path):
    config_path = tmp_path / "cfg" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(
            {
                "version": "1.0.0",
                "learned_preferences": {"existing": 1},
                "last_updated": "2026-03-01",
            }
        ),
        encoding="utf-8",
    )

    engine = IntentAlignmentEngine(repo_path=".", config_path=str(config_path))
    engine.update_preferences({"new_key": 2})

    updated = json.loads(config_path.read_text(encoding="utf-8"))
    assert updated["version"] == "1.0.0"
    assert updated["learned_preferences"]["existing"] == 1
    assert updated["learned_preferences"]["new_key"] == 2


def test_update_preferences_creates_config_parent_dir(tmp_path):
    config_path = tmp_path / "nested" / "config" / "config.json"
    engine = IntentAlignmentEngine(repo_path=".", config_path=str(config_path))
    engine.update_preferences({"first": "value"})

    updated = json.loads(config_path.read_text(encoding="utf-8"))
    assert updated["learned_preferences"]["first"] == "value"
