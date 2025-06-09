"""
core.llm_engine - LLM engine logic for Records Classifier
"""

import ollama
import os
import sys
import time
import datetime
import logging
from pathlib import Path
from core import model_output_validation
from core.import_model import verify_model, import_model

# Constants
MODEL_NAME = "pierce-county-records-classifier-phi2:latest"
MODEL_PARAMS = {
    "temperature": 0.15,
    "top_k": 2,
    "top_p": 0.95,
    "num_ctx": 2048,
    "num_thread": 2,
    "num_batch": 2,
    "stop": "<end_of_turn>",
}

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ensure_model_available():
    """Ensure the model is available for use, initializing it if needed."""
    logger.info(f"Verifying model availability: {MODEL_NAME}")
    success, message = verify_model(MODEL_NAME)

    if not success:
        logger.warning(f"Model verification failed: {message}")
        logger.info("Attempting to import model...")
        if not import_model(MODEL_NAME):
            logger.error("Failed to import model")
            return False
        logger.info("Model imported successfully")

    return True


def classify_with_model(content, lines_per_file=100, source_file="unknown.txt"):
    """Classify file content using the Ollama model (offline, robust), with output validation."""
    try:
        # Ensure model is available
        if not ensure_model_available():
            raise Exception("Model not available")

        # Log parameters for reproducibility
        logger.info(f"Classification request for: {source_file}")
        logger.info(f"Model parameters: {MODEL_PARAMS}")

        # Use ollama.generate with configured parameters
        response = ollama.generate(model=MODEL_NAME, prompt=content, **MODEL_PARAMS)

        # Parse model output with robust error handling
        if isinstance(response, dict) and "label" in response and "score" in response:
            label = response.get("label", "TRANSITORY")
            score = float(response.get("score", 0.0))
            notes = response.get("contextualInsights", "")
        else:
            # Fallback: parse from response text
            raw = (
                response.get("response", "")
                if isinstance(response, dict)
                else str(response)
            )
            label = "TRANSITORY"
            score = 0.0
            notes = raw

        text = content
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"

        # Gather classification details
        keywords_found = [
            kw
            for kw in model_output_validation.SCHEDULE_6_KEYWORDS.get(label.upper(), [])
            if kw.lower() in text.lower()
        ]
        model_confidence = score
        keyword_confidence = model_output_validation.compute_keyword_confidence(
            text, label
        )
        hybrid_conf = model_output_validation.hybrid_confidence(
            model_confidence, text, label
        )
        validation_passed = hybrid_conf >= 0.7

        # Build result object
        classification_details = {
            "schedule": "Schedule 6",
            "keywords_found": keywords_found,
            "hybrid_confidence": hybrid_conf,
            "model_confidence": model_confidence,
            "keyword_confidence": keyword_confidence,
            "validation_passed": validation_passed,
            "notes": notes,
        }

        result = {
            "label": label,
            "score": score,
            "text": text,
            "timestamp": timestamp,
            "source_file": source_file,
            "classification_details": classification_details,
        }

        # Validate model output
        try:
            model_output_validation.fully_validate_model_output(result)
        except model_output_validation.ValidationError as ve:
            result["validation_error"] = str(ve)
            logger.warning(f"Validation error for {source_file}: {str(ve)}")

        logger.info(f"Classification complete for {source_file}")
        return result

    except Exception as e:
        logger.error(f"Classification error for {source_file}: {str(e)}")
        return {
            "label": "ERROR",
            "score": 0,
            "text": content,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "source_file": source_file,
            "classification_details": {},
            "validation_error": str(e),
        }


def process_file_for_output(file_path: str, last_modified: float, content: str) -> dict:
    """Process a file and prepare it for classification output."""
    try:
        # Files > 6 years old are pre-classified as DESTROY
        if last_modified < time.time() - (6 * 365 * 24 * 60 * 60):
            return {
                "label": "DESTROY",
                "score": 1.0,
                "text": content,
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                "source_file": file_path,
                "classification_details": {
                    "schedule": "Schedule 6",
                    "reason": "File older than 6 years",
                },
            }

        # Otherwise classify normally
        return classify_with_model(content, source_file=file_path)

    except Exception as e:
        logger.error(f"File processing error for {file_path}: {str(e)}")
        return {
            "label": "ERROR",
            "score": 0,
            "text": content,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "source_file": file_path,
            "classification_details": {},
            "error": str(e),
        }
