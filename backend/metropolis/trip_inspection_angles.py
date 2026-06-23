"""Trip inspection angle manifest (single JSON source)."""

from __future__ import annotations

import json
from pathlib import Path

_MANIFEST_PATH = Path(__file__).resolve().parent / "data" / "tripInspectionAngles.json"

with _MANIFEST_PATH.open(encoding="utf-8") as _fh:
    ANGLE_MANIFEST: list[dict] = json.load(_fh)

STANDARD_ANGLE_KEYS: frozenset[str] = frozenset(entry["key"] for entry in ANGLE_MANIFEST)
RECOMMENDED_ANGLE_COUNT: int = sum(1 for entry in ANGLE_MANIFEST if entry.get("recommendedFirst"))
STANDARD_ANGLE_COUNT: int = len(ANGLE_MANIFEST)
MAX_EXTRA_PHOTOS_PER_PHASE: int = 20
