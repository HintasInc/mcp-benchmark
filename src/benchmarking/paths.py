"""Repository path constants used by the harness.

The package ships under ``src/benchmarking/`` in an editable install, so the
repo root is two parents above this file. Harness data that lives outside the
package (platform manifests, per-platform scripts, prompts JSON, run output)
lives under ``PLATFORMS_DIR`` — each platform owns the directory
``PLATFORMS_DIR / <name>/`` containing its ``<name>.toml`` and scripts.
Analysis assets (grading prompts, platform notes, renderers) are package data
and rooted at ``ANALYSIS_DIR``.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
PLATFORMS_DIR: Path = REPO_ROOT / "platforms"
ANALYSIS_DIR: Path = Path(__file__).resolve().parent / "analysis"
