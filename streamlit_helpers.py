"""Helper utilities for the Streamlit UI."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import streamlit as st

logger = logging.getLogger(__name__)


def sanitize_filename(filename: str) -> str:
    """Return only the safe file name component of a path."""
    normalized = filename.replace("\\", "/")
    return Path(normalized).name


def load_file_content(uploaded_file) -> Optional[Path]:
    """Save uploaded file to a temporary directory and return the path.

    Parameters
    ----------
    uploaded_file: UploadedFile
        File object received from Streamlit's uploader.

    Returns
    -------
    Optional[Path]
        Path to the saved temporary file or ``None`` if an error occurred.
    """
    try:
        data = uploaded_file.read()
        temp_path = Path(st.session_state.get("temp_dir", "./tmp"))
        temp_path.mkdir(exist_ok=True)
        file_path = temp_path / sanitize_filename(uploaded_file.name)
        file_path.write_bytes(data)
        return file_path
    except Exception as exc:  # pragma: no cover - UI feedback only
        logger.exception("Error saving uploaded file")
        st.error(f"Failed to save file: {exc}")
        return None
