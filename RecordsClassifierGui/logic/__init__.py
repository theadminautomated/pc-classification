"""
Logic package for Records Classifier GUI.

This package contains the core business logic modules:
- classification_engine_fixed: Robust file classification engine
- file_scanner: File discovery and filtering logic
"""

from .classification_engine_fixed import (
    ClassificationEngine,
    ClassificationResult,
    process_file,
)
from .file_scanner import FileScanner, INCLUDE_EXT, EXCLUDE_EXT

__all__ = [
    'ClassificationEngine',
    'ClassificationResult', 
    'process_file',
    'FileScanner',
    'INCLUDE_EXT',
    'EXCLUDE_EXT'
]
