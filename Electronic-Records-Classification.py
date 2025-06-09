#!/usr/bin/env python3
"""
Optimized Electronic Records Classification System
-------------------------------------------------
- Hybrid LLM + deterministic scoring for Pierce County Schedule 6
- Strict schema validation and type checking
- Memory-efficient, parallel-safe, robust error handling
- Confidence score is hybrid: LLM + deterministic policy
"""

import argparse
import os
import sys
import csv
import datetime
import json
import re
import concurrent.futures
import multiprocessing
from pathlib import Path
from typing import Dict, Any, List, Set, Optional

try:
    import ollama
except ImportError:
    ollama = None

INCLUDE_EXT: Set[str] = frozenset({
    '.txt', '.csv', '.docx', '.xlsx', '.pptx', '.pdf', '.html', '.htm', '.md',
    '.rtf', '.odt', '.xml', '.json', '.yaml', '.yml', '.log', '.tsv'
})
EXCLUDE_EXT: Set[str] = frozenset({
    '.tmp', '.bak', '.old', '.zip', '.rar', '.tar', '.gz', '.7z',
    '.exe', '.dll', '.sys', '.iso', '.dmg', '.apk', '.msi', '.ps1', '.psd1',
    '.psm1', '.db', '.mdb', '.accdb'
})

def hybrid_confidence(llm_score: int, file_path: Path, content: str, determination: str) -> int:
    """
    Hybrid confidence: deterministic policy + LLM.
    - DESTROY for >6 years old always 100.
    - If file is empty, always 0.
    - If LLM says DESTROY but file is not >6 years, cap at 80.
    - If LLM says KEEP or TRANSITORY, trust LLM but clamp 1-100.
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

def classify_with_ollama(
    model: str,
    system_instructions: str,
    content: str,
    temperature: float,
    lines_per_file: int,
    file_path: Optional[Path] = None
) -> Dict[str, Any]:
    """Optimized classification engine with hybrid confidence scoring."""
    if not ollama:
        return {
            "modelDetermination": "ERROR",
            "confidenceScore": 0,
            "contextualInsights": "ollama not installed"
        }

    GENERATION_CONFIG = {
        "temperature": max(0.0, min(1.0, temperature)),
        "top_p": 0.9,
        "top_k": 40,
        "num_ctx": 8192,
        "repeat_penalty": 1.2,
        "stop": ["<end_of_turn>", "```", "\n\n"],
        "system": system_instructions
    }

    prompt = f"Classify this content per instructions:\n{content[:5000]}\nOutput JSON only:"

    try:
        response = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": system_instructions or ""},
                {"role": "user", "content": prompt}
            ],
            options=GENERATION_CONFIG,
            stream=False
        )

        raw = response.get('message', {}).get('content', '') if isinstance(response, dict) else str(response)
        json_match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
        if not json_match:
            raise ValueError(f'No valid JSON found in: {raw[:200]}')

        try:
            result = json.loads(json_match.group(0))
        except json.JSONDecodeError as e:
            raise ValueError(f'JSON decode error: {e}\nExtracted: {json_match.group(0)[:200]}')

        validation_rules = {
            'modelDetermination': (
                lambda x: x in ("TRANSITORY", "DESTROY", "KEEP"),
                "must be TRANSITORY, DESTROY, or KEEP"
            ),
            'confidenceScore': (
                lambda x: isinstance(x, (int, float)) and 1 <= x <= 100,
                "must be number 1-100"
            ),
            'contextualInsights': (
                lambda x: isinstance(x, str),
                "must be string"
            )
        }

        for key, (validator, msg) in validation_rules.items():
            if key not in result:
                raise ValueError(f'Missing required key: {key}')
            if not validator(result[key]):
                raise ValueError(f'Invalid {key}: {result[key]} ({msg})')

        # Hybrid confidence normalization
        result['confidenceScore'] = hybrid_confidence(
            result['confidenceScore'],
            file_path if file_path else Path(),
            content,
            result['modelDetermination']
        )

        return result

    except Exception as e:
        return {
            "modelDetermination": "ERROR",
            "confidenceScore": 0,
            "contextualInsights": f"Classification error: {str(e)[:200]}"
        }

def process_file(
    file_path: Path,
    model: str,
    instructions: str,
    temperature: float,
    lines: int
) -> Dict[str, Any]:
    """Atomic file processor with hybrid scoring and error handling."""
    try:
        with open(file_path, 'r', errors='ignore') as f:
            content = ''.join([next(f) for _ in range(lines)])
    except Exception:
        content = ''

    result = classify_with_ollama(
        model=model,
        system_instructions=instructions,
        content=content,
        temperature=temperature,
        lines_per_file=lines,
        file_path=file_path
    )

    mtime = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
    return {
        'FileName': file_path.name,
        'Extension': file_path.suffix,
        'FullPath': str(file_path.resolve()),
        'LastModified': mtime.isoformat(),
        'SizeKB': round(file_path.stat().st_size / 1024, 2),
        'ModelDetermination': result.get('modelDetermination', 'ERROR'),
        'ConfidenceScore': result.get('confidenceScore', 0),
        'ContextualInsights': result.get('contextualInsights', '')
    }

def parse_args():
    parser = argparse.ArgumentParser(description='Electronic Records Classification System')
    parser.add_argument('FolderPath', type=str, help='Path to the folder with documents to classify')
    parser.add_argument('OutputPath', type=str, help='Path for the output CSV file')
    parser.add_argument('--Model', type=str, default='llama2', help='Ollama model to use')
    parser.add_argument('--LinesPerFile', type=int, default=100, help='Number of lines to analyze per file')
    parser.add_argument('--Temperature', type=float, default=0.1, help='Model temperature (0.0-1.0)')
    parser.add_argument('--MaxParallelJobs', type=int, default=None, help='Maximum parallel classification jobs')
    parser.add_argument('--SkipAnalysis', action='store_true', help='Skip LLM analysis of files')
    return parser.parse_args()

def main():
    args = parse_args()
    folder = Path(args.FolderPath)
    fieldnames = ['FileName', 'Extension', 'FullPath', 'LastModified', 'SizeKB',
                  'ModelDetermination', 'ConfidenceScore', 'ContextualInsights']

    threshold = datetime.datetime.now() - datetime.timedelta(days=6 * 365)
    all_files = list(folder.rglob('*'))
    destroy_files = [f for f in all_files if f.is_file() and
                     datetime.datetime.fromtimestamp(f.stat().st_mtime) < threshold]
    remaining = [f for f in all_files if f.is_file() and
                 datetime.datetime.fromtimestamp(f.stat().st_mtime) >= threshold]
    skipped_files = [f for f in remaining if f.suffix.lower() not in INCLUDE_EXT or
                     f.suffix.lower() in EXCLUDE_EXT]
    supported = [f for f in remaining if f.suffix.lower() in INCLUDE_EXT and
                 f.suffix.lower() not in EXCLUDE_EXT]

    with open(args.OutputPath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        def write_batch(files, determination, insights):
            for f in files:
                writer.writerow({
                    'FileName': f.name,
                    'Extension': f.suffix,
                    'FullPath': str(f.resolve()),
                    'LastModified': datetime.datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                    'SizeKB': round(f.stat().st_size / 1024, 2),
                    'ModelDetermination': determination,
                    'ConfidenceScore': 100 if determination == 'DESTROY' else 0,
                    'ContextualInsights': insights
                })
                csvfile.flush()

        write_batch(destroy_files, 'DESTROY', 'Older than 6 years')
        write_batch(skipped_files, 'SKIPPED', 'Unsupported type')

        if not args.SkipAnalysis and ollama:
            instructions = (
                f'You are "{args.Model}" - Pierce County Records Classifier.\n'
                f'Analyze first {args.LinesPerFile} lines. Output JSON with: '
                'KEEP/DESTROY/TRANSITORY, confidenceScore, contextualInsights.'
            )

            with concurrent.futures.ThreadPoolExecutor(
                max_workers=args.MaxParallelJobs or multiprocessing.cpu_count()
            ) as executor:
                futures = {
                    executor.submit(
                        process_file,
                        f,
                        args.Model,
                        instructions,
                        args.Temperature,
                        args.LinesPerFile
                    ): f for f in supported
                }

                for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
                    writer.writerow(future.result())
                    csvfile.flush()
                    print(f"PROGRESS: {i}/{len(supported)}", end='\r', file=sys.stderr)

        elif supported:
            write_batch(supported, 'Not Analyzed',
                        'Analysis skipped' if args.SkipAnalysis else 'ollama not installed')

if __name__ == '__main__':
    main()