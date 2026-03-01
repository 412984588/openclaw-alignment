#!/usr/bin/env python3
"""
跨平台路径工具。

优先使用 XDG / AppData 目录，兼容 legacy OpenClaw 路径。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional


APP_NAME = "openclaw-alignment"
LEGACY_ROOT = Path("~/.openclaw/extensions/intent-alignment").expanduser()


def _home() -> Path:
    return Path.home()


def get_config_dir() -> Path:
    if sys.platform.startswith("win"):
        base = Path(os.environ.get("APPDATA", _home() / "AppData/Roaming"))
        return base / APP_NAME
    base = Path(os.environ.get("XDG_CONFIG_HOME", _home() / ".config"))
    return base / APP_NAME


def get_cache_dir() -> Path:
    if sys.platform.startswith("win"):
        base = Path(os.environ.get("LOCALAPPDATA", _home() / "AppData/Local"))
        return base / APP_NAME / "cache"
    base = Path(os.environ.get("XDG_CACHE_HOME", _home() / ".cache"))
    return base / APP_NAME


def get_state_dir() -> Path:
    if sys.platform.startswith("win"):
        base = Path(os.environ.get("LOCALAPPDATA", _home() / "AppData/Local"))
        return base / APP_NAME / "state"
    base = Path(os.environ.get("XDG_STATE_HOME", _home() / ".local/state"))
    return base / APP_NAME


def get_default_config_path() -> Path:
    return get_config_dir() / "config.json"


def get_default_model_dir() -> Path:
    return get_cache_dir() / "models" / "rl"


def get_legacy_config_path() -> Path:
    return LEGACY_ROOT / "config" / "config.json"


def get_legacy_model_dir() -> Path:
    return LEGACY_ROOT / "models" / "rl"


def resolve_config_path(config_path: Optional[str] = None) -> Path:
    if config_path:
        return Path(config_path).expanduser()

    default_path = get_default_config_path()
    legacy_path = get_legacy_config_path()

    if default_path.exists():
        return default_path
    if legacy_path.exists():
        return legacy_path
    return default_path


def resolve_model_dir(model_path: Optional[str] = None) -> Path:
    if model_path:
        return Path(model_path).expanduser()

    default_dir = get_default_model_dir()
    legacy_dir = get_legacy_model_dir()

    if default_dir.exists():
        return default_dir
    if legacy_dir.exists():
        return legacy_dir
    return default_dir
