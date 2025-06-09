"""Modern Streamlit UI for the Pierce County Records Classifier."""
from __future__ import annotations

import logging
from pathlib import Path

import streamlit as st

from RecordsClassifierGui.logic.classification_engine_fixed import (
    ClassificationEngine,
)
from config import CONFIG
from version import __version__
from streamlit_helpers import load_file_content

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def classify(file_path: Path, engine: ClassificationEngine, mode: str) -> None:
    """Classify a file and display results."""
    with st.spinner("Classifying..."):
        try:
            result = engine.classify_file(str(file_path), run_mode=mode)
        except Exception as exc:  # pragma: no cover - UI feedback only
            logger.exception("Classification failed")
            st.error(f"Classification failed: {exc}")
            return

    st.success("Classification complete")
    st.write(
        "**Determination:** "
        f"{result.model_determination} | "
        f"**Confidence:** {result.confidence_score}%"
    )
    with st.expander("Details"):
        st.json(
            {
                "file": result.file_name,
                "determination": result.model_determination,
                "confidence": result.confidence_score,
                "insights": result.contextual_insights,
            }
        )


def show_about() -> None:
    """Display about/help information."""
    st.sidebar.markdown(
        f"**Pierce County Records Classifier**\n\nVersion: {__version__}\n\n"
        "For help contact: records-support@example.com"
    )


def main() -> None:
    """Run the Streamlit UI."""
    st.set_page_config(page_title="Records Classifier", page_icon="📄", layout="wide")
    show_about()
    st.title("Pierce County Electronic Records Classifier")
    st.write(f"Model: {CONFIG.model_name}")

    engine = ClassificationEngine()

    mode = st.radio(
        "Mode",
        options=["Classification", "Last Modified"],
        horizontal=True,
    )

    uploaded_file = st.file_uploader("Upload a file for classification")
    if uploaded_file:
        st.info(f"Saving {uploaded_file.name}...")
        with st.spinner("Saving file..."):
            file_path = load_file_content(uploaded_file)
        if file_path:
            st.success("File saved")
            st.write(f"Name: {file_path.name} | Size: {file_path.stat().st_size} bytes")
            classify(file_path, engine, mode)


if __name__ == "__main__":
    main()
