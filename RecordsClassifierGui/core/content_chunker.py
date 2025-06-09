"""Utility for reading a limited chunk of text from files."""

from pathlib import Path
from typing import Union

MAX_CHARS = 4000


def read_chunk(file_path: Union[str, Path], max_chars: int = MAX_CHARS) -> str:
    """Return up to `max_chars` characters of cleaned text from a file."""
    path = Path(file_path)
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            content = f.read(max_chars)
        return " ".join(content.split())
    except Exception as exc:
        return f"[error reading {path.name}: {exc}]"
