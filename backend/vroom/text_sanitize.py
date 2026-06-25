from __future__ import annotations

import html
import re

_SCRIPT_PATTERN = re.compile(r"<script[\s\S]*?</script>", re.IGNORECASE)
_TAG_PATTERN = re.compile(r"<[^>]+>")
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def sanitize_display_text(value: str, *, max_length: int = 150) -> str:
    """Strip HTML/control chars from user-facing text fields."""
    cleaned = html.unescape(value.strip())
    cleaned = _SCRIPT_PATTERN.sub("", cleaned)
    cleaned = _TAG_PATTERN.sub("", cleaned)
    cleaned = cleaned.replace("<", "").replace(">", "")
    cleaned = _CONTROL_CHARS.sub("", cleaned)
    cleaned = cleaned.strip()
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length].strip()
    return cleaned
