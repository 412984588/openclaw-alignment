#!/usr/bin/env python3
"""Cross-platform installer for OpenClaw Alignment."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Install OpenClaw Alignment")
    parser.add_argument("--phase3", action="store_true", help="Install optional phase3 dependencies")
    parser.add_argument("--dev", action="store_true", help="Install development dependencies")
    parser.add_argument("--editable", action="store_true", help="Install package in editable mode")
    args = parser.parse_args()

    run([sys.executable, "-m", "pip", "install", "-r", str(PROJECT_ROOT / "requirements.txt")])
    if args.phase3:
        run([sys.executable, "-m", "pip", "install", "-r", str(PROJECT_ROOT / "requirements-full.txt")])
    if args.dev:
        run([sys.executable, "-m", "pip", "install", "-r", str(PROJECT_ROOT / "requirements-dev.txt")])

    if args.editable:
        run([sys.executable, "-m", "pip", "install", "-e", str(PROJECT_ROOT)])
    else:
        run([sys.executable, "-m", "pip", "install", str(PROJECT_ROOT)])

    print("Installation complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
