"""
core.model_output_validation - Model output validation logic for Records Classifier
Moved under core/ for modular architecture. Update all imports to use core.model_output_validation.
"""

from typing import Any, Dict, List, Callable, Optional, Tuple
# Attempt to import jsonschema, fallback to no-op validators
try:
    import jsonschema
except ImportError:
    import logging
    logging.warning("jsonschema not available, skipping JSON schema validation.")
    class jsonschema:
        class ValidationError(Exception):
            """Placeholder for jsonschema ValidationError."""
            pass
        @staticmethod
        def validate(instance, schema):
            """No-op validate when jsonschema is unavailable."""
            return None
    import logging
    logging.warning("jsonschema not available, skipping JSON schema validation.")
    class jsonschema:
        class ValidationError(Exception):
            """Placeholder for jsonschema ValidationError."""
            pass
        @staticmethod
        def validate(instance, schema):
            """No-op validate when jsonschema is unavailable."""
            return None
except ImportError:
    import logging
    logging.warning("jsonschema module not found, skipping JSON schema validation.")
    class jsonschema:
        class ValidationError(Exception):
            pass
        @staticmethod
        def validate(instance, schema):
            return None
except ImportError:
    import logging
    logging.warning("jsonschema module not found, JSON schema validation disabled.")
    class jsonschema:
        class ValidationError(Exception):
            pass
        @staticmethod
        def validate(instance, schema):
            return None
except ImportError:
    # jsonschema not installed; skip JSON schema validation
    import logging
    logging.warning("jsonschema module not found, skipping JSON schema validation.")
    class jsonschema:
        @staticmethod
        def validate(instance, schema):
            return None
        class ValidationError(Exception):
            pass

class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass

# Atomic validators

def validate_type(value: Any, expected_type: type) -> None:
    if not isinstance(value, expected_type):
        raise ValidationError(f"Expected type {expected_type.__name__}, got {type(value).__name__}")

def validate_required_fields(data: Dict, required_fields: List[str]) -> None:
    missing = [field for field in required_fields if field not in data]
    if missing:
        raise ValidationError(f"Missing required fields: {missing}")

def validate_range(value: Any, min_value: Optional[float] = None, max_value: Optional[float] = None) -> None:
    if min_value is not None and value < min_value:
        raise ValidationError(f"Value {value} below minimum {min_value}")
    if max_value is not None and value > max_value:
        raise ValidationError(f"Value {value} above maximum {max_value}")

# Composable validator

def validate_output(
    output: Any,
    validators: List[Tuple[Callable, Tuple, Dict]]
) -> None:
    """
    Run a sequence of validators on the output.
    Each validator is a tuple: (function, args, kwargs)
    """
    for func, args, kwargs in validators:
        func(output, *args, **kwargs)

# Washington State Schedule 6 classification keywords
SCHEDULE_6_KEYWORDS = {
    "TRANSITORY": ["transitory", "temporary", "short-term", "routine", "informal"],
    "OFFICIAL": ["official", "permanent", "record", "retention", "archival"],
    # Add more classes and keywords as needed
}

def compute_keyword_confidence(text: str, classification: str) -> float:
    """
    Compute a confidence score based on the presence of classification keywords in the text.
    Returns a float between 0.0 and 1.0.
    """
    keywords = SCHEDULE_6_KEYWORDS.get(classification.upper(), [])
    if not keywords:
        return 0.0
    text_lower = text.lower()
    matches = sum(1 for kw in keywords if kw in text_lower)
    return matches / len(keywords) if keywords else 0.0

def hybrid_confidence(model_confidence: float, text: str, classification: str, weight_model: float = 0.7) -> float:
    """
    Combine model confidence and keyword-based confidence using a weighted average.
    weight_model: weight for model confidence (0.0-1.0), rest is for keyword confidence.
    """
    keyword_score = compute_keyword_confidence(text, classification)
    return weight_model * model_confidence + (1 - weight_model) * keyword_score

# Define the comprehensive JSON schema for model output
MODEL_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "label": {"type": "string"},
        "score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "text": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
        "source_file": {"type": "string"},
        "classification_details": {
            "type": "object",
            "properties": {
                "schedule": {"type": "string"},
                "keywords_found": {"type": "array", "items": {"type": "string"}},
                "hybrid_confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "model_confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "keyword_confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "validation_passed": {"type": "boolean"},
                "notes": {"type": "string"}
            },
            "required": ["schedule", "keywords_found", "hybrid_confidence", "model_confidence", "keyword_confidence", "validation_passed"]
        }
    },
    "required": ["label", "score", "text", "timestamp", "source_file", "classification_details"]
}

def validate_json_schema(output: dict, schema: dict = MODEL_OUTPUT_SCHEMA) -> None:
    """
    Validate the output dict against the provided JSON schema.
    Raises ValidationError if validation fails.
    """
    try:
        jsonschema.validate(instance=output, schema=schema)
    except jsonschema.ValidationError as e:
        raise ValidationError(f"JSON schema validation error: {e.message}")

def fully_validate_model_output(output: dict) -> None:
    """
    Perform full, production-grade validation of model output for government workload.
    This includes:
    - JSON schema validation
    - Atomic field validation
    - Hybrid confidence computation
    - Domain-specific checks (e.g., label/classification compliance)
    Raises ValidationError on any failure.
    """
    # 1. JSON schema validation
    validate_json_schema(output)

    # 2. Atomic field validation
    validate_type(output["label"], str)
    validate_type(output["score"], float)
    validate_range(output["score"], 0.0, 1.0)
    validate_type(output["text"], str)
    validate_type(output["timestamp"], str)
    validate_type(output["source_file"], str)
    details = output["classification_details"]
    validate_type(details["schedule"], str)
    validate_type(details["keywords_found"], list)
    validate_type(details["hybrid_confidence"], float)
    validate_range(details["hybrid_confidence"], 0.0, 1.0)
    validate_type(details["model_confidence"], float)
    validate_range(details["model_confidence"], 0.0, 1.0)
    validate_type(details["keyword_confidence"], float)
    validate_range(details["keyword_confidence"], 0.0, 1.0)
    validate_type(details["validation_passed"], bool)
    if "notes" in details:
        validate_type(details["notes"], str)

    # 3. Hybrid confidence check (recompute and compare)
    recomputed_hybrid = hybrid_confidence(
        details["model_confidence"], output["text"], output["label"]
    )
    if abs(recomputed_hybrid - details["hybrid_confidence"]) > 0.01:
        raise ValidationError(f"Hybrid confidence mismatch: expected {recomputed_hybrid:.2f}, got {details['hybrid_confidence']:.2f}")

    # 4. Domain-specific: label must be in allowed classes
    allowed_labels = set(SCHEDULE_6_KEYWORDS.keys())
    if output["label"].upper() not in allowed_labels:
        raise ValidationError(f"Label '{output['label']}' not in allowed classes: {allowed_labels}")

    # 5. Domain-specific: keywords_found must be subset of class keywords
    class_keywords = set(SCHEDULE_6_KEYWORDS[output["label"].upper()])
    found_keywords = set(details["keywords_found"])
    if not found_keywords.issubset(class_keywords):
        raise ValidationError(f"keywords_found {found_keywords} not subset of class keywords {class_keywords}")

    # 6. Domain-specific: validation_passed must be True if hybrid_confidence >= 0.7
    if details["hybrid_confidence"] >= 0.7 and not details["validation_passed"]:
        raise ValidationError("validation_passed must be True if hybrid_confidence >= 0.7")

    # 7. (Optional) Add more government workload checks as needed in the future

# Additional domain-specific validators can be implemented here when
# expanded classification logic is required.  This placeholder block was
# previously used for demonstration purposes and has been removed for
# clarity.  Extend the `fully_validate_model_output` function with new
# checks as business rules evolve.
