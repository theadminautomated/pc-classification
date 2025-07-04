#!/usr/bin/env python3
"""
Robust Electronic Records Classification Engine
-----------------------------------------------
A properly architected classification engine with robust error handling
and graceful fallback when LLM services are unavailable.
"""

# COPILOT AGENT: LLM MUST BE BYPASSED IF RUN MODE IS "Last Modified". IMPLEMENT THIS LOGIC HERE OR IN file_scanner.py

import json
import re
import datetime
import threading
from pathlib import Path
from typing import Dict, Any, List, Set, Optional, Union
from dataclasses import dataclass
import logging
import os
try:
    import requests  # type: ignore
except Exception:  # pragma: no cover - fallback for minimal environments
    import json as _json
    from urllib import request as _urlreq

    class _Resp:
        def __init__(self, text: str):
            self.text = text

        def json(self):
            return _json.loads(self.text)

        def raise_for_status(self):
            pass

    class requests:  # type: ignore
        class RequestException(Exception):
            pass

        @staticmethod
        def post(url, json=None, headers=None, timeout=10):
            data = _json.dumps(json or {}).encode()
            req = _urlreq.Request(url, data=data, headers=headers or {}, method="POST")
            try:
                with _urlreq.urlopen(req, timeout=timeout) as resp:
                    text = resp.read().decode()
            except Exception as exc:
                raise requests.RequestException(str(exc)) from exc
            return _Resp(text)

from RecordsClassifierGui.core import model_output_validation

# Force CPU mode unless user overrides
os.environ.setdefault("OLLAMA_LLAMA_ACCELERATE", "false")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File type constants - sync with file_scanner.py
INCLUDE_EXT: Set[str] = frozenset({
    '.txt', '.csv', '.docx', '.xlsx', '.pptx', '.pdf', '.html', '.htm', '.md',
    '.rtf', '.odt', '.xml', '.json', '.yaml', '.yml', '.log', '.tsv'
})

EXCLUDE_EXT: Set[str] = frozenset({
    '.tmp', '.bak', '.old', '.zip', '.rar', '.tar', '.gz', '.7z',
    '.exe', '.dll', '.sys', '.iso', '.dmg', '.apk', '.msi', '.ps1', '.psd1',
    '.psm1', '.db', '.mdb', '.accdb', '.sqlite', '.dbf', '.log', '.swp', '.swo'
})

@dataclass
class ClassificationResult:
    """Structured result from file classification."""

    file_name: str
    extension: str
    full_path: str
    last_modified: str
    size_kb: float
    model_determination: str
    confidence_score: int
    contextual_insights: str
    status: str = "success"
    processing_time_ms: int = 0
    error_message: str = ""

class LLMEngine:
    """LLM interaction layer using Ollama's HTTP API."""

    def __init__(self, timeout_seconds: int = 60):
        """Initialize the LLM engine.

        Args:
            timeout_seconds: Maximum time to wait for LLM responses.
        """
        self.timeout_seconds = timeout_seconds
        self.ollama_available = False
        self._initialize_ollama()

    def _initialize_ollama(self) -> None:
        """Verify that the Ollama service is reachable."""
        from config import CONFIG
        url = f"{CONFIG.ollama_url.rstrip('/')}/api/generate"
        try:
            resp = requests.post(
                url,
                json={"model": CONFIG.model_name, "prompt": "ping", "stream": False},
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            resp.raise_for_status()
            self.ollama_available = True
            logger.info("Ollama service detected and available")
        except Exception as exc:  # pragma: no cover - service missing
            logger.warning("Ollama unavailable: %s", exc)
            self.ollama_available = False

    def classify_with_llm(
        self,
        model: str,
        system_instructions: str,
        content: str,
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        """Call the LLM and return validated output."""

        logger.debug("LLM prompt: %s", system_instructions)

        used_fallback = False
        prompt = system_instructions

        try:
            from config import CONFIG
            url = f"{CONFIG.ollama_url.rstrip('/')}/api/generate"

            payload = {"model": model, "prompt": prompt, "stream": False}
            logger.debug("POST %s payload=%s", url, payload)

            resp = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=15,
            )

            if not resp.ok:
                logger.error("LLM HTTP %s: %s", resp.status_code, resp.text)
                resp.raise_for_status()

            raw = resp.json().get("response", resp.text)
            logger.debug("LLM raw response: %s", raw)

            json_match = re.search(r"\{[^{}]*\}", raw, re.DOTALL)
            if not json_match:
                raise ValueError(f"No valid JSON in response: {raw[:200]}")

            result = json.loads(json_match.group(0))

            if result.get("classification") not in {"TRANSITORY", "DESTROY", "ARCHIVE", "KEEP"}:
                raise ValueError(f"Invalid classification: {result.get('classification')}")

            conf = result.get("confidence")
            if not isinstance(conf, (int, float)) or not (0 <= conf <= 1):
                raise ValueError(f"Invalid confidence: {conf}")

            rationale = result.get("rationale", "")
            if not isinstance(rationale, str) or not rationale.strip():
                raise ValueError("Rationale missing")

            result_dict = {
                "modelDetermination": result["classification"],
                "confidenceScore": int(conf * 100),
                "contextualInsights": rationale,
                "used_fallback": used_fallback,
            }
            logger.debug("Parsed LLM result: %s", result_dict)
            return result_dict

        except requests.RequestException as exc:
            used_fallback = True
            err_text = getattr(getattr(exc, "response", None), "text", str(exc))
            logger.error("LLM request failed: %s", err_text)
        except Exception as exc:  # pragma: no cover - unexpected failures
            used_fallback = True
            logger.error("LLM classification failed: %s", exc)

        fallback = self._heuristic_classify(content)
        fallback["used_fallback"] = used_fallback
        return fallback

    def _heuristic_classify(self, content: str) -> Dict[str, Any]:
        """Minimal heuristic fallback used when LLM cannot be reached."""
        text = content.lower()
        keyword_counts = {
            label: sum(text.count(kw) for kw in model_output_validation.SCHEDULE_6_KEYWORDS.get(label, []))
            for label in model_output_validation.SCHEDULE_6_KEYWORDS
        }

        if keyword_counts:
            best_label = max(keyword_counts, key=keyword_counts.get)
            first_match = next(
                (kw for kw in model_output_validation.SCHEDULE_6_KEYWORDS[best_label] if kw in text),
                "",
            )
            determination = "KEEP" if best_label == "OFFICIAL" else best_label
            base_conf = 50 + min(keyword_counts[best_label] * 10, 40)
            return {
                "modelDetermination": determination,
                "confidenceScore": base_conf,
                "contextualInsights": f"Matched keyword '{first_match}'" if first_match else "Heuristic fallback",
            }

        snippet = text[:50]
        return {
            "modelDetermination": "TRANSITORY",
            "confidenceScore": 50,
            "contextualInsights": f"No keywords found. Sample: '{snippet}'",
        }
class ClassificationEngine:
    """Main classification engine with hybrid scoring.
    
    Combines LLM-based classification with rule-based logic for optimal
    accuracy. Automatically destroys files older than 6 years and applies
    confidence adjustments based on file characteristics.
    """
    
    def __init__(self, timeout_seconds: int = 60):
        """Initialize the classification engine.
        
        Args:
            timeout_seconds: Maximum time to wait for LLM responses.
        """
        self.llm_engine = LLMEngine(timeout_seconds)
    def _hybrid_confidence(
        self, 
        llm_score: int, 
        file_path: Path, 
        content: str, 
        determination: str
    ) -> int:
        """Calculate hybrid confidence score combining LLM and rule-based logic.
        
        Args:
            llm_score: Confidence score from LLM (1-100).
            file_path: Path to the file being classified.
            content: File content that was classified.
            determination: Classification result from LLM.
            
        Returns:
            Adjusted confidence score (1-100) based on hybrid logic:
            - DESTROY for >6 years old: always 100
            - Empty files: always 0
            - DESTROY for newer files: capped at 80
            - Other classifications: use LLM score with bounds checking
        """
        try:
            if determination == "DESTROY":
                mtime = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
                threshold = datetime.datetime.now() - datetime.timedelta(days=6 * 365)
                if mtime < threshold:
                    return 100
                else:
                    return min(80, max(1, int(llm_score)))
            elif not content.strip():
                return 0
            else:
                return min(100, max(1, int(llm_score)))
        except Exception:
            return min(100, max(1, int(llm_score)))
    
    def _read_file_content(self, file_path: Path, min_words: int = 300) -> str:
        """Read the entire file and return the text."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            if len(text.split()) < min_words:
                logger.warning("Content under %d words for %s", min_words, file_path.name)
            return text
        except Exception as e:
            logger.warning("Could not read file %s: %s", file_path, e)
            return ""
    
    def classify_file(
        self,
        file_path: Union[str, Path],
        model: str = 'llama2',
        instructions: str = '',
        temperature: float = 0.1,
        max_lines: int = 100,
        run_mode: str = 'Classification'
    ) -> ClassificationResult:
        """
        Classify a single file with comprehensive error handling.
        
        Args:
            file_path: Path to the file to classify
            model: LLM model name
            instructions: System instructions for classification
            temperature: LLM temperature
            max_lines: Deprecated. Context extraction now uses up to 500 words
            run_mode: Classification mode ('Classification' or 'Last Modified')
            
        Returns:
            ClassificationResult with all metadata and classification
        """
        start_time = datetime.datetime.now()
        file_path = Path(file_path)
        
        try:
            # Get file metadata
            stat_info = file_path.stat()
            mtime = datetime.datetime.fromtimestamp(stat_info.st_mtime)
            size_kb = round(stat_info.st_size / 1024, 2)
            
            # Check for excluded file extensions
            extension = file_path.suffix.lower()
            if extension in EXCLUDE_EXT:
                processing_time = (datetime.datetime.now() - start_time).total_seconds() * 1000
                return ClassificationResult(
                    file_name=file_path.name,
                    extension=extension,
                    full_path=str(file_path.resolve()),
                    last_modified=mtime.isoformat(),
                    size_kb=size_kb,
                    model_determination="SKIP",
                    confidence_score=100,
                    contextual_insights=f"Excluded file type: {extension}",
                    status="skipped",
                    processing_time_ms=int(processing_time)
                )
            
            # Check if file extension is not in include list
            if extension not in INCLUDE_EXT:
                processing_time = (datetime.datetime.now() - start_time).total_seconds() * 1000
                return ClassificationResult(
                    file_name=file_path.name,
                    extension=extension,
                    full_path=str(file_path.resolve()),
                    last_modified=mtime.isoformat(),
                    size_kb=size_kb,
                    model_determination="SKIP",
                    confidence_score=100,
                    contextual_insights=f"Unsupported file type: {extension}",
                    status="skipped",
                    processing_time_ms=int(processing_time)
                )
            
            # Read full file content for classification
            content = self._read_file_content(file_path, min_words=300)
            
            threshold = datetime.datetime.now() - datetime.timedelta(days=6 * 365)

            if run_mode == "Last Modified":
                processing_time = (datetime.datetime.now() - start_time).total_seconds() * 1000
                if mtime < threshold:
                    return ClassificationResult(
                        file_name=file_path.name,
                        extension=extension,
                        full_path=str(file_path.resolve()),
                        last_modified=mtime.isoformat(),
                        size_kb=size_kb,
                        model_determination="DESTROY",
                        confidence_score=100,
                        contextual_insights="Last Modified date > 6 years",
                        status="Marked for Destruction",
                        processing_time_ms=int(processing_time),
                    )
                return ClassificationResult(
                    file_name=file_path.name,
                    extension=extension,
                    full_path=str(file_path.resolve()),
                    last_modified=mtime.isoformat(),
                    size_kb=size_kb,
                    model_determination="SKIP",
                    confidence_score=100,
                    contextual_insights="File newer than 6 years",
                    status="skipped",
                    processing_time_ms=int(processing_time),
                )

            # Automatic DESTROY for old files in normal mode
            if mtime < threshold:
                processing_time = (datetime.datetime.now() - start_time).total_seconds() * 1000
                return ClassificationResult(
                    file_name=file_path.name,
                    extension=file_path.suffix,
                    full_path=str(file_path.resolve()),
                    last_modified=mtime.isoformat(),
                    size_kb=size_kb,
                    model_determination="DESTROY",
                    confidence_score=100,
                    contextual_insights="Older than 6 years - automatic destroy",
                    status="success",
                    processing_time_ms=int(processing_time),
                )
            
            # Build prompt for the LLM per cleanup policy
            prompt = (
                "You are classifying electronic records for cleanup based on these rules:\n\n"
                "- TRANSITORY: notes, drafts, brainstorms, tasks, etc.\n"
                "- DESTROY: no longer needed and past retention.\n"
                "- ARCHIVE: no longer needed but still in retention.\n"
                "- KEEP: active or business-critical.\n\n"
                f"File: {file_path.name}\n"
                f"Type: {extension}\n"
                f"Modified: {mtime.isoformat()}\n"
                "Content:\n"
                f"{content}\n\n"
                "Respond in JSON:\n{\n  \"classification\": \"...\",\n  \"confidence\": 0-1,\n  \"rationale\": \"...\"\n}"
            )

            logger.debug("LLM prompt: %s", prompt)

            llm_result = self.llm_engine.classify_with_llm(
                model=model,
                system_instructions=prompt,
                content=content,
                temperature=temperature,
            )
            used_fallback = llm_result.pop("used_fallback", False)
            
            # Apply hybrid confidence scoring
            confidence_score = self._hybrid_confidence(
                llm_result.get('confidenceScore', 0),
                file_path,
                content,
                llm_result.get('modelDetermination', 'ERROR')
            )
            
            processing_time = (datetime.datetime.now() - start_time).total_seconds() * 1000

            return ClassificationResult(
                file_name=file_path.name,
                extension=file_path.suffix,
                full_path=str(file_path.resolve()),
                last_modified=mtime.isoformat(),
                size_kb=size_kb,
                model_determination=llm_result.get('modelDetermination', 'ERROR'),
                confidence_score=confidence_score,
                contextual_insights=llm_result.get('contextualInsights', ''),
                status="fallback" if used_fallback else "success",
                processing_time_ms=int(processing_time)
            )
            
        except Exception as e:
            processing_time = (
                datetime.datetime.now() - start_time
            ).total_seconds() * 1000
            logger.error("Failed to classify %s: %s", file_path, e)
            msg = str(e)
            if "await" in msg and "expression" in msg:
                msg += " - asynchronous call failed"
            
            # Return error result with as much metadata as possible
            try:
                stat_info = file_path.stat()
                mtime = datetime.datetime.fromtimestamp(stat_info.st_mtime)
                size_kb = round(stat_info.st_size / 1024, 2)
            except:
                mtime = datetime.datetime.now()
                size_kb = 0
            
            return ClassificationResult(
                file_name=file_path.name,
                extension=file_path.suffix,
                full_path=str(file_path.resolve()),
                last_modified=mtime.isoformat(),
                size_kb=size_kb,
                model_determination="ERROR",
                confidence_score=0,
                contextual_insights=f"Processing error: {msg[:200]}",
                status="error",
                processing_time_ms=int(processing_time),
                error_message=msg
            )

# Create a global instance for backward compatibility
_classification_engine = ClassificationEngine()

def process_file(
    file_path: Path,
    model: str,
    instructions: str,
    temperature: float,
    lines: int,
    run_mode: str = 'Classification'
) -> Dict[str, Any]:
    """
    Legacy compatibility function that matches the original interface.
    
    Args:
        file_path: Path to the file to classify
        model: LLM model name
        instructions: System instructions for classification
        temperature: LLM temperature
        lines: Maximum lines to read from file
        run_mode: Classification mode ('Classification' or 'Last Modified')
    
    Returns:
        Dictionary with classification results in the original format
    """
    result = _classification_engine.classify_file(
        file_path=file_path,
        model=model,
        instructions=instructions,
        temperature=temperature,
        max_lines=lines,
        run_mode=run_mode
    )
    
    # Convert to original format
    return {
        'FileName': result.file_name,
        'Extension': result.extension,
        'FullPath': result.full_path,
        'LastModified': result.last_modified,
        'SizeKB': result.size_kb,
        'ModelDetermination': result.model_determination,
        'ConfidenceScore': result.confidence_score,
        'ContextualInsights': result.contextual_insights,
        'Status': result.status
    }
