"""Pytest configuration for ensuring project modules are importable."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"

for path in (SRC_DIR, ROOT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
