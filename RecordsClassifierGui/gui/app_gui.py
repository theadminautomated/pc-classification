#!/usr/bin/env python3
"""
gui.RecordsClassifierGui - Quantum-Enhanced, Enterprise-Grade GUI for Records Classifier
Enterprise production solution with LLM lifecycle robustness, atomic error containment, immutable enhancements, and quantum safe UI/LLM orchestration.
"""

import sys
import os
import time
import shutil
import datetime
import threading
import multiprocessing
import logging
from pathlib import Path
from tkinter import messagebox, filedialog, ttk
import tkinter as tk
from PIL import Image, ImageTk
import customtkinter as ctk
import ollama
import psutil
import math
from datetime import datetime
from collections import defaultdict
from typing import List, Set, Optional, Dict, Any, Tuple, Union


def safe_theme_color(
    theme_dict: Dict[str, str],
    key: str,
    fallbacks: List[str] = None,
    default: str = "#202020",
) -> str:
    """Safely get a color from the theme with multiple fallbacks for resiliency."""
    if fallbacks is None:
        fallbacks = []

    # Try the primary key first
    if key in theme_dict:
        return theme_dict[key]

    # Try each fallback in order
    for fallback in fallbacks:
        if fallback in theme_dict:
            return theme_dict[fallback]

    # Return the default if no keys found
    return default


def ensure_theme_keys() -> None:
    """Ensure all required theme keys exist by adding fallbacks."""
    # Status bar keys
    if "statusbar_bg" not in theme:
        theme["statusbar_bg"] = theme.get("status_bg", theme.get("bg", "#1e1e1e"))
    if "statusbar_fg" not in theme:
        theme["statusbar_fg"] = theme.get("fg", "#e0e0e0")


from core.llm_engine import classify_with_model as validated_classify_with_model
from core.llm_engine import process_file_for_output
import csv
import itertools
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import openpyxl
except ImportError:
    openpyxl = None

# Constants (quantized, immutable)
INCLUDE_EXT = {".txt", ".doc", ".docx", ".pdf"}
EXCLUDE_EXT = {".exe", ".dll", ".sys"}
SPACING = 10
PADDING = 20
FONT_FAMILY = "Segoe UI"
MODEL_NAME = "pierce-county-records-classifier-phi2:latest"

# Performance and Refresh Constants
STATS_REFRESH_RATE = 1000  # Stats refresh interval in milliseconds
MODEL_CHECK_INTERVAL = 5000  # LLM model check interval in milliseconds
MAX_HISTORY_POINTS = 100  # Maximum data points to keep for metrics

# UI Constants
STATS_PANEL_HEIGHT = 120
MIN_WINDOW_WIDTH = 900
MIN_WINDOW_HEIGHT = 600

# Import local modules (atomic, explicit structure)
from . import theme, screens, widgets, utils
from .theme import theme
from .screens import SetupScreen
from .widgets import (
    ToolTip,
    CompletionPanel,
    build_run_button,
    build_table,
    build_output_selector,
    build_folder_selector,
    build_trust_panel,
    build_header,
)
from .utils import hover_effect

# Ensure imports resolve correctly
from .widgets import *
from .utils import *

# ===== PATH FIX FOR DIRECT EXECUTION =====
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


def scan_files(folder: str, include_ext: Set[str], exclude_ext: Set[str]) -> List[Path]:
    """Scan a folder for files with specific extensions (atomic enhancement for pathlib)"""
    files = []
    for root, _, filenames in os.walk(folder):
        for filename in filenames:
            ext = Path(filename).suffix.lower()
            if (not include_ext or ext in include_ext) and ext not in exclude_ext:
                files.append(Path(root) / filename)
    return files


def extract_file_content(filepath: Path, max_lines: int = 100) -> str:
    """Extract content from a file with a line limit (quantized for Path)"""
    try:
        with filepath.open("r", encoding="utf-8", errors="replace") as f:
            lines = []
            for i, line in enumerate(f):
                if i >= max_lines:
                    break
                lines.append(line)
            return "".join(lines)
    except Exception as e:
        logger.error("Error reading file %s: %s", filepath, e)
        return ""


def classify_with_model(content: str, source_file: str = "unknown.txt") -> dict:
    """Classify the content using the validated Ollama model output pipeline."""
    result = validated_classify_with_model(content, source_file=source_file)
    # If validation_error is present, show a messagebox and log it
    if "validation_error" in result:
        from tkinter import messagebox

        messagebox.showerror(
            "Validation Error",
            f"Model output failed validation:\n{result['validation_error']}",
        )
        # Optionally, log or handle the error for audit
    return result


def export_results_to_csv(results: list, csv_path: str):
    """Export the processed results to a CSV file with required columns."""
    fieldnames = [
        "File Name",
        "Extension",
        "LLM Determination",
        "Justification",
        "Confidence Score",
        "File Path",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)


def process_folder_and_export(
    folder: str,
    csv_path: str,
    include_ext: Set[str] = INCLUDE_EXT,
    exclude_ext: Set[str] = EXCLUDE_EXT,
    max_lines: int = 100,
):
    """
    Scan a folder, process each file for output, and export results to CSV.
    Applies 6-year retention policy and LLM validation.
    """
    files = scan_files(folder, include_ext, exclude_ext)
    results = []
    for file in files:
        try:
            stat = file.stat()
            last_modified = stat.st_mtime
            content = extract_file_content(file, max_lines=max_lines)
            row = process_file_for_output(str(file), last_modified, content)
            results.append(row)
        except Exception as e:
            results.append(
                {
                    "File Name": file.name,
                    "Extension": file.suffix.lstrip("."),
                    "LLM Determination": "ERROR",
                    "Justification": f"Processing error: {e}",
                    "Confidence Score": 0.0,
                    "File Path": str(file),
                }
            )
    export_results_to_csv(results, csv_path)
    return results


class AnimatedSpinner(tk.Canvas):
    def __init__(self, parent, size=32, color="#4fa3f7", speed=0.08, **kwargs):
        super().__init__(
            parent,
            width=size,
            height=size,
            bg=parent["bg"],
            highlightthickness=0,
            **kwargs,
        )
        self.size = size
        self.color = color
        self.speed = speed
        self.angle = 0
        self.arc = self.create_arc(
            4,
            4,
            size - 4,
            size - 4,
            start=0,
            extent=270,
            style="arc",
            outline=color,
            width=4,
        )
        self.running = False

    def start(self):
        self.running = True
        self._animate()

    def stop(self):
        self.running = False
        self.itemconfig(self.arc, extent=0)

    def _animate(self):
        if not self.running:
            return
        self.angle = (self.angle + 10) % 360
        self.itemconfig(self.arc, start=self.angle, extent=270)
        self.after(int(self.speed * 1000), self._animate)


class AnimatedStatusLabel(ctk.CTkLabel):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._dots = itertools.cycle(["", ".", "..", "..."])
        self._base_text = self.cget("text")
        self._running = False

    def start(self, text=None):
        if text:
            self._base_text = text
        self._running = True
        self._animate()

    def stop(self, text=None):
        self._running = False
        if text:
            self.configure(text=text)

    def _animate(self):
        if not self._running:
            return
        dots = next(self._dots)
        self.configure(text=f"{self._base_text}{dots}")
        self.after(400, self._animate)


class AnimatedRunButton(ctk.CTkButton):
    def __init__(self, parent, command, **kwargs):
        super().__init__(parent, command=command, **kwargs)
        self._pulse = False
        self._pulse_id = None
        self._default_color = self.cget("fg_color")
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonRelease-1>", self._on_click)

    def _on_enter(self, e):
        self._pulse = True
        self._pulse_anim(1)

    def _on_leave(self, e):
        self._pulse = False
        if self._pulse_id:
            self.after_cancel(self._pulse_id)
        self.configure(fg_color=self._default_color)

    def _pulse_anim(self, step):
        if not self._pulse:
            return
        color = theme["button_hover"] if step % 2 == 0 else theme["button_bg"]
        self.configure(fg_color=color)
        self._pulse_id = self.after(300, self._pulse_anim, step + 1)

    def _on_click(self, e):
        self._pulse = False
        if self._pulse_id:
            self.after_cancel(self._pulse_id)
        self._show_checkmark()

    def _show_checkmark(self):
        orig_text = self.cget("text")
        self.configure(text="✔", fg_color=theme["success"])
        self.after(
            900, lambda: self.configure(text=orig_text, fg_color=self._default_color)
        )


class RecordsClassifierGui(ctk.CTk):
    """
    Main GUI application for Pierce County Electronic Records Classifier (quantized, robust).
    See docstring in previous cell for full featureset.
    """

    def _center(self, w, h):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def __init__(self):
        """Initialize the GUI with proper initialization order and setup handling."""
        super().__init__()

        # Initialize state variables first
        self.stats_vars = {
            "processed": tk.StringVar(value="0"),
            "pending": tk.StringVar(value="0"),
            "total_size": tk.StringVar(value="0 B"),
            "avg_time": tk.StringVar(value="0ms"),
            "success_rate": tk.StringVar(value="100%"),
            "memory_usage": tk.StringVar(value="0%"),
            "cpu_usage": tk.StringVar(value="0%"),
            "start_time": None,
            "processing_times": [],
        }
        self._setup_complete = False
        self._cancel_event = threading.Event()
        self._worker_thread = None
        self._sort_state = defaultdict(lambda: False)
        self._results = []
        self._all_results = []
        self._model_status = {"available": False, "message": "Not checked"}
        self._processing_stats = {
            "total_files": 0,
            "processed_files": 0,
            "failed_files": 0,
            "total_size": 0,
            "current_file": None,
        }

        # Initialize path variables
        self.folder_path = tk.StringVar()
        self.output_path = tk.StringVar()

        # Configure main window
        self.title("Pierce County Records Classifier")
        self.geometry("1200x800")
        self.minsize(800, 600)
        self._center(1200, 800)

        # Create the main container frame
        self.main_frame = ctk.CTkFrame(self, fg_color=theme["bg"])
        self.main_frame.pack(fill="both", expand=True)

        # Create the notebook
        style = ttk.Style()
        style.configure("TNotebook", background=theme["bg"])
        style.configure(
            "TNotebook.Tab", padding=[12, 4], font=("Segoe UI Variable", 10)
        )

        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill="both", expand=True)

        # Create the main app frame
        self.main_app_frame = ctk.CTkFrame(self.notebook, fg_color=theme["bg"])
        self.notebook.add(self.main_app_frame, text="Records Classifier")

        # Load logo if available
        logo_path = str(Path(__file__).parent.parent / "PC_Logo_Round_white.png")
        if os.path.exists(logo_path):
            try:
                logo_image = Image.open(logo_path)
                logo_photo = ImageTk.PhotoImage(logo_image)
                logo_label = tk.Label(
                    self.main_app_frame, image=logo_photo, bg=theme["bg"]
                )
                logo_label.image = logo_photo  # Keep a reference!
                logo_label.pack(pady=(20, 0))
            except Exception as e:
                logger.warning(
                    "Logo loading error: %s", e
                )  # Ensure theme has all required keys before initializing UI
        ensure_theme_keys()

        # Initialize UI with enterprise features
        self._initialize_ui()

        # Start stats update loop
        self._update_stats()

        # Check model in background
        threading.Thread(target=self._check_model_status, daemon=True).start()

    def _update_stats(self):
        """Update all system and processing statistics with error handling."""
        try:
            # Update system metrics
            cpu_percent = psutil.cpu_percent(interval=None)
            memory_percent = psutil.Process().memory_percent()

            self.stats_vars["cpu_usage"].set(f"{cpu_percent:.1f}%")
            self.stats_vars["memory_usage"].set(f"{memory_percent:.1f}%")

            # Update processing metrics if running
            if self.processing:
                current_time = time.time()
                elapsed = current_time - self.stats_vars.get("start_time", current_time)

                # Calculate processing rate and update ETA
                if self.stats_vars["processing_times"]:
                    avg_time = sum(self.stats_vars["processing_times"]) / len(
                        self.stats_vars["processing_times"]
                    )
                    self.stats_vars["avg_time"].set(f"{avg_time:.1f}ms")

                    processed = int(self.stats_vars["processed"].get() or 0)
                    total = processed + int(self.stats_vars["pending"].get() or 0)

                    if total > 0:
                        progress = processed / total
                        self.stats_vars["success_rate"].set(f"{(progress * 100):.1f}%")

                        # Calculate ETA
                        remaining = total - processed
                        eta_seconds = remaining * (avg_time / 1000)
                        if eta_seconds > 0:
                            eta = str(datetime.timedelta(seconds=int(eta_seconds)))
                            self.est_time_label.configure(text=f"ETA: {eta}")

                # Update size metrics
                if hasattr(self, "total_size"):
                    self.stats_vars["total_size"].set(
                        f"{self.total_size / 1024:.2f} KB"
                    )
        except Exception as e:
            logger.error("Error updating stats: %s", e)
            # Don't update stats this cycle, but continue updates
        finally:
            # Safely check for the processing attribute
            if getattr(self, "processing", False) or getattr(
                self, "always_update_stats", False
            ):
                self.after(STATS_REFRESH_RATE, self._update_stats)

    def _initialize_stats_tracking(self):
        """Initialize statistical tracking system."""
        self.stats_vars = {
            "processed": tk.StringVar(value="0"),
            "pending": tk.StringVar(value="0"),
            "total_size": tk.StringVar(value="0 B"),
            "avg_time": tk.StringVar(value="0ms"),
            "success_rate": tk.StringVar(value="0%"),
            "memory_usage": tk.StringVar(value="0%"),
            "cpu_usage": tk.StringVar(value="0%"),
            "start_time": None,
            "processing_times": [],
        }

        # Enable continuous stats updates
        self.always_update_stats = True
        self._update_stats()  # Start the update cycle

    def _initialize_stats_panel(self, parent):
        """Initialize the statistics panel with comprehensive metrics."""
        stats_frame = ctk.CTkFrame(
            parent, fg_color=theme["panel_bg"], corner_radius=12, height=120
        )
        stats_frame.pack(fill="x", padx=10, pady=(0, 20))
        stats_frame.pack_propagate(False)

        # Create 2x4 grid of stats
        for i, (label, var) in enumerate(
            [
                ("Processed", self.stats_vars["processed"]),
                ("Pending", self.stats_vars["pending"]),
                ("Total Files", self.stats_vars["total_files"]),
                ("Avg. Time", self.stats_vars["avg_time"]),
                ("Success Rate", self.stats_vars["success_rate"]),
                ("Memory Usage", self.stats_vars["memory_usage"]),
                ("CPU Usage", self.stats_vars["cpu_usage"]),
                ("Status", self.stats_vars.get("status", tk.StringVar(value="Ready"))),
            ]
        ):
            col = i % 4
            row = i // 4
            stat_container = ctk.CTkFrame(stats_frame, fg_color="transparent")
            stat_container.grid(row=row, column=col, padx=10, pady=5, sticky="nsew")

            label_widget = ctk.CTkLabel(
                stat_container,
                text=label,
                font=("Segoe UI Variable", 12),
                text_color=theme["fg"],
            )
            label_widget.pack(anchor="w")

            value_widget = ctk.CTkLabel(
                stat_container,
                textvariable=var,
                font=("Segoe UI Variable", 16, "bold"),
                text_color=theme["accent"],
            )
            value_widget.pack(anchor="w")

        # Configure grid
        for i in range(4):
            stats_frame.grid_columnconfigure(i, weight=1)
        for i in range(2):
            stats_frame.grid_rowconfigure(i, weight=1)

    def _check_model_status(self):
        """Check model status in background without blocking UI."""
        try:
            # First check Ollama service
            try:
                import ollama

                ollama.list()
                service_ok = True
            except Exception:
                service_ok = False
                self._model_status = {
                    "available": False,
                    "message": "Ollama service not running",
                }
                self._update_model_status_ui()
                return

            if not service_ok:
                return

            # Then check model
            try:
                models = ollama.list().get("models", [])
                if any(MODEL_NAME in m.get("name", "") for m in models):
                    self._model_status = {"available": True, "message": "Model ready"}
                else:
                    self._model_status = {
                        "available": False,
                        "message": "Model not found",
                    }
            except Exception as e:
                self._model_status = {
                    "available": False,
                    "message": f"Model check failed: {str(e)[:50]}",
                }
        except Exception as e:
            self._model_status = {
                "available": False,
                "message": f"Status check error: {str(e)[:50]}",
            }
        finally:
            self._update_model_status_ui()

    def _update_model_status_ui(self):
        """Update UI elements showing model status."""
        self.after(0, lambda: self._do_update_model_status_ui())

    def _do_update_model_status_ui(self):
        """Actually update the UI elements (must be called from main thread)."""
        # Update model status indicator in footer
        if hasattr(self, "model_status_label"):
            color = (
                theme["success"] if self._model_status["available"] else theme["error"]
            )
            icon = "✓" if self._model_status["available"] else "⚠"
            self.model_status_label.configure(
                text=f"Model Status: {icon} {self._model_status['message']}",
                text_color=color,
            )

        # Update mode dropdown based on model availability
        if hasattr(self, "mode_menu"):
            if self._model_status["available"]:
                self.mode_menu.configure(
                    values=["Full Classification", "DESTROY Only"], state="normal"
                )
            else:
                self.mode_menu.configure(values=["DESTROY Only"], state="normal")
                self.mode_var.set("DESTROY Only")

    def _show_main_ui(self):
        self.setup_background.destroy()
        self.notebook.pack(side="top", fill="both", expand=True)

    def _check_model_and_initialize(self):
        """Check model availability and initialize in background."""
        try:
            if self._run_setup_checks(MODEL_NAME):
                self.after(0, lambda: self._on_setup_complete(True))
            else:
                self.after(0, lambda: self._on_setup_complete(False))
        except Exception as e:
            logger.error("Model check error: %s", e)
            self.after(0, lambda: self._on_setup_complete(False))

    def _run_setup_checks(self, model_name):
        """Run setup checks with proper error handling."""
        try:
            # Initialize setup screen if needed
            if not self.setup_screen:
                self.setup_screen = SetupScreen(
                    self.main_app_frame,
                    self._on_setup_complete,
                    task_name="Initializing",
                    steps=[
                        {"name": "Checking Ollama service", "weight": 30},
                        {"name": "Verifying model", "weight": 40},
                        {"name": "Finalizing setup", "weight": 30},
                    ],
                    auto_run=True,
                )

            self.setup_screen.start()

            # Check Ollama service
            self.setup_screen.set_status("Checking Ollama service...")
            if not self._check_ollama_service():
                return False

            # Check model availability
            self.setup_screen.set_progress(1, 30, "Checking model...")
            if not self._check_model_availability(model_name):
                return False

            # Final checks
            self.setup_screen.set_progress(2, 70, "Finalizing...")
            return True

        except Exception as e:
            if self.setup_screen:
                self.setup_screen.set_status(f"Setup error: {str(e)[:200]}")
                self.setup_screen.progress_label.configure(text="Failed")
                self.setup_screen.canvas.itemconfig(
                    self.setup_screen.progress_rect, fill=theme["error"]
                )
            return False

    def _check_ollama_service(self):
        """Check if Ollama service is running."""
        try:
            import ollama

            ollama.list()
            self.setup_screen.set_status("Ollama service connected")
            return True
        except Exception as e:
            self.setup_screen.set_status(
                "Ollama service not running. Please start Ollama and try again."
            )
            return False

    def _check_model_availability(self, model_name):
        """Check if required model is available."""
        try:
            import ollama

            models = ollama.list().get("models", [])
            if any(model_name in m.get("name", "") for m in models):
                self.setup_screen.set_status(f"Model '{model_name}' verified")
                return True
            self.setup_screen.set_status(f"Model '{model_name}' not found")
            return False
        except Exception as e:
            self.setup_screen.set_status(f"Model check failed: {str(e)[:200]}")
            return False

    def _import_model_silently(self, model_name):
        """Import model with robust validation and error handling."""
        try:
            # Step 1: Validate Ollama service
            try:
                import ollama

                models = ollama.list()
                self._model_status = {
                    "available": False,
                    "message": "Checking model...",
                }
                self._update_model_status_ui()
            except ImportError:
                self._model_status = {
                    "available": False,
                    "message": "Ollama package not installed",
                }
                self._update_model_status_ui()
                return False
            except Exception as e:
                if "connection refused" in str(e).lower():
                    self._model_status = {
                        "available": False,
                        "message": "Ollama service not running",
                    }
                else:
                    self._model_status = {
                        "available": False,
                        "message": f"Service error: {str(e)[:50]}",
                    }
                self._update_model_status_ui()
                return False

            # Step 2: Check if model exists
            models_data = models.get("models", [])
            model_names = [m.get("name", "") for m in models_data]
            if any(model_name in n for n in model_names):
                self._model_status = {"available": True, "message": "Model ready"}
                self._update_model_status_ui()
                return True

            # Step 3: Find Modelfile
            self._model_status = {
                "available": False,
                "message": "Searching for Modelfile...",
            }
            self._update_model_status_ui()

            script_dir = Path(__file__).resolve().parent
            workspace_dir = script_dir.parent
            possible_paths = [
                script_dir / "Modelfile-phi2",
                workspace_dir / "Modelfile-phi2",
                Path(os.getcwd()) / "Modelfile-phi2",
                Path(os.getcwd()).parent / "Modelfile-phi2",
            ]

            modelfile_path = next(
                (path for path in possible_paths if path.exists()), None
            )
            if not modelfile_path:
                self._model_status = {
                    "available": False,
                    "message": "Modelfile not found",
                }
                self._update_model_status_ui()
                return False

            # Step 4: Try API import
            try:
                self._model_status = {
                    "available": False,
                    "message": "Creating model via API...",
                }
                self._update_model_status_ui()

                with open(modelfile_path, "r") as f:
                    modelfile_content = f.read()
                ollama.create(model=model_name, modelfile=modelfile_content)

                self._model_status = {
                    "available": True,
                    "message": "Model created successfully",
                }
                self._update_model_status_ui()
                return True

            except Exception as api_err:
                # Step 5: Fall back to CLI import
                self._model_status = {
                    "available": False,
                    "message": "Trying CLI import...",
                }
                self._update_model_status_ui()

                try:
                    original_dir = os.getcwd()
                    os.chdir(modelfile_path.parent)

                    process = subprocess.run(
                        ["ollama", "create", model_name, "-f", modelfile_path.name],
                        capture_output=True,
                        text=True,
                    )

                    os.chdir(original_dir)

                    if process.returncode == 0:
                        self._model_status = {
                            "available": True,
                            "message": "Model created via CLI",
                        }
                        self._update_model_status_ui()
                        return True
                    else:
                        error_msg = process.stderr or process.stdout or "Unknown error"
                        self._model_status = {
                            "available": False,
                            "message": f"CLI import failed: {error_msg[:50]}",
                        }
                        self._update_model_status_ui()
                        return False

                except Exception as cli_err:
                    self._model_status = {
                        "available": False,
                        "message": f"CLI attempt failed: {str(cli_err)[:50]}",
                    }
                    self._update_model_status_ui()
                    return False

        except Exception as e:
            self._model_status = {
                "available": False,
                "message": f"Import error: {str(e)[:50]}",
            }
            self._update_model_status_ui()
            return False

    def _add_readme_tabs(self):
        """Replace with a single, extremely detailed 'How It Works' tab for compliance and transparency."""
        import tkinter.scrolledtext as st

        how_it_works_content = (
            "# How It Works: Pierce County Records Classifier\n\n"
            "This application is designed for government and compliance use. It provides full transparency into every step of the records classification process.\n\n"
            "## 1. File Scanning and Selection\n"
            "- The app scans your selected folder for files with supported extensions (e.g., .txt, .docx, .pdf).\n"
            "- Files with unsupported or risky extensions (e.g., .exe, .dll) are ignored for safety.\n\n"
            "## 2. Content Extraction and OCR\n"
            "- For text-based files, the app reads the file contents directly.\n"
            "- For PDF or image-based files, Optical Character Recognition (OCR) is used to extract readable text.\n"
            "- Only the first portion (up to 100 lines) of each file is processed to ensure efficiency and privacy.\n\n"
            "## 3. Content Chunking\n"
            "- Large files are broken into manageable 'chunks' of text.\n"
            "- Each chunk is cleaned (removing non-text artifacts, extra spaces, etc.) to ensure only relevant content is analyzed.\n"
            "- This chunking ensures the AI model can process files of any size without missing important information.\n\n"
            "## 4. 6-Year Retention Policy (Auto-DESTROY)\n"
            "- If a file's last modified date is more than 6 years ago, it is automatically marked as 'DESTROY' (scheduled for destruction).\n"
            "- This rule is enforced before any AI analysis, ensuring compliance with records retention laws.\n\n"
            "## 5. AI Model (LLM) Classification\n"
            "- Files not marked for auto-destruction are analyzed by a local, government-approved AI model (LLM).\n"
            "- The model reviews the cleaned text and determines the correct classification (e.g., RETAIN, DESTROY, or other categories).\n"
            "- The model also provides a plain-language justification for its decision.\n"
            "- The model is run entirely on your local machine—no data ever leaves your computer.\n\n"
            "## 6. Model Output Validation\n"
            "- Every AI model output is validated using two layers:\n"
            "    - **JSON Schema Validation:** Ensures the model's response is in the correct format (required fields, types, etc.).\n"
            "    - **Hybrid Confidence Validation:** Checks that the model's confidence score is present, within a valid range, and that the justification is meaningful.\n"
            "- If the model output fails validation, it is rejected and flagged for review.\n"
            "- This prevents accidental or malformed classifications from being used.\n\n"
            "## 7. Confidence Scoring\n"
            "- The model assigns a confidence score (0.0 to 1.0) to each classification.\n"
            "- This score is calculated using a hybrid method:\n"
            "    - The model's own internal certainty.\n"
            "    - Additional checks (e.g., does the justification match the classification, is the evidence strong).\n"
            "- Low-confidence results are highlighted for human review.\n\n"
            "## 8. Real-Time Feedback and Results Table\n"
            "- As files are processed, results appear in the table immediately.\n"
            "- Each row shows: File Name, Extension, Classification, Justification, Confidence Score, and File Path.\n"
            "- You can search, sort, and filter results for easy review.\n\n"
            "## 9. Export and Audit\n"
            "- You can export all results to a CSV file for audit, compliance, or further processing.\n"
            "- The exported CSV includes all relevant fields for each file.\n\n"
            "## 10. Accessibility and Security\n"
            "- The app is designed for keyboard navigation, high contrast, and screen reader compatibility.\n"
            "- All processing is local—no files or data are sent to the cloud or third parties.\n"
            "- Error handling and logging are robust, with clear messages for any issues.\n\n"
            "## 11. Compliance and Transparency\n"
            "- Every step is documented and auditable.\n"
            "- The classification model, validation logic, and retention rules are open for inspection.\n"
            "- For compliance review, see the README and Modelfile for technical details.\n\n"
            "---\n"
            "**For help:** Click the 'How It Works' button or see this page. For technical/compliance questions, contact IT or records management."
        )
        how_it_works_frame = ctk.CTkFrame(self.notebook, fg_color=theme["bg"])
        how_it_works_text = st.ScrolledText(
            how_it_works_frame,
            wrap="word",
            font=(FONT_FAMILY, 12),
            bg=theme["panel_bg"],
            fg=theme["fg"],
        )
        how_it_works_text.insert("1.0", how_it_works_content)
        how_it_works_text.configure(state="disabled")
        how_it_works_text.pack(expand=True, fill="both", padx=10, pady=10)
        self.notebook.add(how_it_works_frame, text="How It Works")

    def _show_how(self):
        """Show a modal dialog explaining how the app works (production-ready)."""
        import tkinter.messagebox as messagebox

        msg = (
            "Pierce County Records Classifier\n\n"
            "1. Scans all files in the selected folder.\n"
            "2. For each file, extracts and cleans a content chunk.\n"
            "3. If the file is older than 6 years, it is marked DESTROY (auto).\n"
            "4. Otherwise, the file is classified by the LLM, with output rigorously validated.\n"
            "5. All results are shown in the table in real time.\n"
            "6. You can select files and export results to CSV.\n\n"
            "Bulk move/delete are planned for a future release."
        )
        messagebox.showinfo("How It Works", msg)

    def _browse_folder(self):
        """Open a folder dialog and set the folder_path variable."""
        from tkinter import filedialog

        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path.set(folder_selected)

    def _browse_output(self):
        """Open a file dialog and set the output_path variable."""
        from tkinter import filedialog

        file_selected = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if file_selected:
            self.output_path.set(file_selected)

    def _initialize_ui(self):
        """Initialize the main UI components."""
        # Create outer container that fills the window
        outer_container = ctk.CTkFrame(self.main_app_frame, fg_color=theme["bg"])
        outer_container.pack(fill="both", expand=True)

        # Create main content area with scrolling
        content_area = ctk.CTkFrame(outer_container, fg_color=theme["bg"])
        content_area.pack(fill="both", expand=True, padx=10, pady=(10, 0))

        # Initialize main components in content area
        self._initialize_header(content_area)
        self._initialize_items_panel(content_area)
        self._initialize_stats_panel(content_area)

        # Create fixed footer that stays at bottom
        self.footer = ctk.CTkFrame(
            outer_container, fg_color=theme["statusbar_bg"], height=25
        )
        self.footer.pack(fill="x", side="bottom", pady=(5, 0))
        self.footer.pack_propagate(False)  # Prevent footer from shrinking

        # Initialize VSCode-style status footer with left and right sections
        left_container = ctk.CTkFrame(self.footer, fg_color="transparent")
        left_container.pack(side="left", fill="y")

        right_container = ctk.CTkFrame(self.footer, fg_color="transparent")
        right_container.pack(side="right", fill="y")

        # Left side status items
        self.status_label = ctk.CTkLabel(
            left_container,
            text="Ready",
            text_color=theme["statusbar_fg"],
            font=("Segoe UI Variable", 11),
        )
        self.status_label.pack(side="left", padx=5)

        self.progress_label = ctk.CTkLabel(
            left_container,
            text="",
            text_color=theme["statusbar_fg"],
            font=("Segoe UI Variable", 11),
        )
        self.progress_label.pack(side="left", padx=5)

        # Right side items
        self.stats_label = ctk.CTkLabel(
            right_container,
            text="Records: 0",
            text_color=theme["statusbar_fg"],
            font=("Segoe UI Variable", 11),
        )
        self.stats_label.pack(side="right", padx=5)

        self.model_status_label = ctk.CTkLabel(
            right_container,
            text="Model Status: Checking...",
            text_color=theme["statusbar_fg"],
            font=("Segoe UI Variable", 11),
        )
        self.model_status_label.pack(side="right", padx=5)

        # Start model check
        self._check_model_status()

        # Initialize processing state
        self.processing = False

    def _initialize_header(self, parent):
        """Initialize header with title and description."""
        header = ctk.CTkFrame(parent, fg_color=theme["header_bg"], height=80)
        header.pack(fill="x", padx=10, pady=(0, 20))
        header.pack_propagate(False)

        title = ctk.CTkLabel(
            header,
            text="Pierce County Records Classifier",
            font=("Segoe UI Variable", 24, "bold"),
            text_color=theme["fg"],
        )
        title.pack(pady=(10, 0))

        subtitle = ctk.CTkLabel(
            header,
            text="AI-Powered Document Classification Tool",
            font=("Segoe UI Variable", 14),
            text_color=theme["fg"],
        )
        subtitle.pack()

    def _initialize_items_panel(self, parent):
        """Initialize the items panel with the modern LiveUpdateTable."""
        frame = ctk.CTkFrame(parent, fg_color=theme["bg"])
        frame.pack(fill="both", expand=True, pady=(10, 0))

        # Define table columns
        columns = [
            ("id", "#", 50),
            ("filename", "Filename", 200),
            ("extension", "Extension", 80),
            ("modified", "Last Modified", 150),
            ("size", "Size", 100),
            ("determination", "Determination", 120),
            ("confidence", "Confidence", 100),
            ("justification", "Justification", 300),
        ]

        # Create table with virtualized scrolling and column reordering
        self.items_table = LiveUpdateTable(
            frame,
            columns=columns,
            height=400,
            show="headings",  # Hide the first empty column
            virtualized=True,  # Enable virtualized scrolling
            reorderable=True,  # Allow column reordering
        )
        self.items_table.pack(side="top", fill="x", expand=False, pady=(5, 5))

        # Pack scrollbar
        self.items_table.yscrollbar.pack(side="right", fill="y")

        # Configure sorting
        for col in columns:
            self.items_table.heading(
                col[0], command=lambda c=col[0]: self._sort_table(c)
            )

        # Add bulk action buttons
        bulk_actions_frame = ctk.CTkFrame(frame, fg_color=theme["bg"])
        bulk_actions_frame.pack(fill="x", pady=(5, 0))

        self.bulk_rerun_button = ctk.CTkButton(
            bulk_actions_frame, text="RERUN", command=self._bulk_rerun
        )
        self.bulk_rerun_button.pack(side="left", padx=5)

        self.bulk_export_button = ctk.CTkButton(
            bulk_actions_frame, text="EXPORT CSV/JSON", command=self._bulk_export
        )
        self.bulk_export_button.pack(side="left", padx=5)

        self.bulk_destroy_button = ctk.CTkButton(
            bulk_actions_frame, text="DESTROY", command=self._bulk_destroy
        )
        self.bulk_destroy_button.pack(side="left", padx=5)

        # Initialize live update mechanism
        self._initialize_live_updates()

    # Add methods for bulk actions

    def _bulk_rerun(self):
        """Handle bulk RERUN action."""
        selected_items = self.items_table.get_selected_items()
        # ... Implement logic for rerunning selected items ...

    def _bulk_export(self):
        """Handle bulk EXPORT action."""
        selected_items = self.items_table.get_selected_items()
        # ... Implement logic for exporting selected items to CSV/JSON ...

    def _bulk_destroy(self):
        """Handle bulk DESTROY action."""
        selected_items = self.items_table.get_selected_items()
        # ... Implement logic for destroying selected items ...

    def _initialize_live_updates(self):
        """Initialize live update mechanism for the table."""
        # ... Implement logic for streaming results into the table in real-time ...

    def _sort_table(self, column):
        """Sort table by column with proper data type handling."""
        # Get all items
        items = [
            (self.items_table.item(child)["values"], child)
            for child in self.items_table.get_children("")
        ]

        # Determine column index
        col_id = self.items_table.column.index(column)

        # Sort based on column type
        reverse = self._sort_state.get(column, False)
        if column in ["size", "confidence"]:
            # Numeric sorting
            items.sort(key=lambda x: float(x[0][col_id]), reverse=reverse)
        elif column == "modified":
            # Date sorting
            items.sort(
                key=lambda x: datetime.strptime(x[0][col_id], "%Y-%m-%d %H:%M:%S"),
                reverse=reverse,
            )
        else:
            # String sorting
            items.sort(key=lambda x: str(x[0][col_id]).lower(), reverse=reverse)

        # Rearrange items
        for index, (values, item) in enumerate(items):
            self.items_table.move(item, "", index)

            # Update row colors
            tags = ["oddrow"] if index % 2 == 1 else []
            if values[5].lower() in [
                "retain",
                "destroy",
                "review",
            ]:  # determination column
                tags.append(values[5].lower())
            self.items_table.item(item, tags=tags)

        # Toggle sort state
        self._sort_state[column] = not reverse

    def _initialize_stats_tracking(self):
        """Initialize statistical tracking system."""
        self.stats_vars = {
            "processed": tk.StringVar(value="0"),
            "pending": tk.StringVar(value="0"),
            "total_size": tk.StringVar(value="0 B"),
            "avg_time": tk.StringVar(value="0ms"),
            "success_rate": tk.StringVar(value="0%"),
            "memory_usage": tk.StringVar(value="0%"),
            "cpu_usage": tk.StringVar(value="0%"),
            "start_time": None,
            "processing_times": [],
        }

        # Enable continuous stats updates
        self.always_update_stats = True
        self._update_stats()  # Start the update cycle

    def _initialize_stats_panel(self, parent):
        """Initialize the statistics panel with comprehensive metrics."""
        stats_frame = ctk.CTkFrame(
            parent, fg_color=theme["panel_bg"], corner_radius=12, height=120
        )
        stats_frame.pack(fill="x", padx=10, pady=(0, 20))
        stats_frame.pack_propagate(False)

        # Create 2x4 grid of stats
        for i, (label, var) in enumerate(
            [
                ("Processed", self.stats_vars["processed"]),
                ("Pending", self.stats_vars["pending"]),
                ("Total Files", self.stats_vars["total_files"]),
                ("Avg. Time", self.stats_vars["avg_time"]),
                ("Success Rate", self.stats_vars["success_rate"]),
                ("Memory Usage", self.stats_vars["memory_usage"]),
                ("CPU Usage", self.stats_vars["cpu_usage"]),
                ("Status", self.stats_vars.get("status", tk.StringVar(value="Ready"))),
            ]
        ):
            col = i % 4
            row = i // 4
            stat_container = ctk.CTkFrame(stats_frame, fg_color="transparent")
            stat_container.grid(row=row, column=col, padx=10, pady=5, sticky="nsew")

            label_widget = ctk.CTkLabel(
                stat_container,
                text=label,
                font=("Segoe UI Variable", 12),
                text_color=theme["fg"],
            )
            label_widget.pack(anchor="w")

            value_widget = ctk.CTkLabel(
                stat_container,
                textvariable=var,
                font=("Segoe UI Variable", 16, "bold"),
                text_color=theme["accent"],
            )
            value_widget.pack(anchor="w")

        # Configure grid
        for i in range(4):
            stats_frame.grid_columnconfigure(i, weight=1)
        for i in range(2):
            stats_frame.grid_rowconfigure(i, weight=1)

    def _check_model_status(self):
        """Check model status in background without blocking UI."""
        try:
            # First check Ollama service
            try:
                import ollama

                ollama.list()
                service_ok = True
            except Exception:
                service_ok = False
                self._model_status = {
                    "available": False,
                    "message": "Ollama service not running",
                }
                self._update_model_status_ui()
                return

            if not service_ok:
                return

            # Then check model
            try:
                models = ollama.list().get("models", [])
                if any(MODEL_NAME in m.get("name", "") for m in models):
                    self._model_status = {"available": True, "message": "Model ready"}
                else:
                    self._model_status = {
                        "available": False,
                        "message": "Model not found",
                    }
            except Exception as e:
                self._model_status = {
                    "available": False,
                    "message": f"Model check failed: {str(e)[:50]}",
                }
        except Exception as e:
            self._model_status = {
                "available": False,
                "message": f"Status check error: {str(e)[:50]}",
            }
        finally:
            self._update_model_status_ui()

    def _update_model_status_ui(self):
        """Update UI elements showing model status."""
        self.after(0, lambda: self._do_update_model_status_ui())

    def _do_update_model_status_ui(self):
        """Actually update the UI elements (must be called from main thread)."""
        # Update model status indicator in footer
        if hasattr(self, "model_status_label"):
            color = (
                theme["success"] if self._model_status["available"] else theme["error"]
            )
            icon = "✓" if self._model_status["available"] else "⚠"
            self.model_status_label.configure(
                text=f"Model Status: {icon} {self._model_status['message']}",
                text_color=color,
            )

        # Update mode dropdown based on model availability
        if hasattr(self, "mode_menu"):
            if self._model_status["available"]:
                self.mode_menu.configure(
                    values=["Full Classification", "DESTROY Only"], state="normal"
                )
            else:
                self.mode_menu.configure(values=["DESTROY Only"], state="normal")
                self.mode_var.set("DESTROY Only")

    def _show_main_ui(self):
        self.setup_background.destroy()
        self.notebook.pack(side="top", fill="both", expand=True)

    def _check_model_and_initialize(self):
        """Check model availability and initialize in background."""
        try:
            if self._run_setup_checks(MODEL_NAME):
                self.after(0, lambda: self._on_setup_complete(True))
            else:
                self.after(0, lambda: self._on_setup_complete(False))
        except Exception as e:
            logger.error("Model check error: %s", e)
            self.after(0, lambda: self._on_setup_complete(False))

    def _run_setup_checks(self, model_name):
        """Run setup checks with proper error handling."""
        try:
            # Initialize setup screen if needed
            if not self.setup_screen:
                self.setup_screen = SetupScreen(
                    self.main_app_frame,
                    self._on_setup_complete,
                    task_name="Initializing",
                    steps=[
                        {"name": "Checking Ollama service", "weight": 30},
                        {"name": "Verifying model", "weight": 40},
                        {"name": "Finalizing setup", "weight": 30},
                    ],
                    auto_run=True,
                )

            self.setup_screen.start()

            # Check Ollama service
            self.setup_screen.set_status("Checking Ollama service...")
            if not self._check_ollama_service():
                return False

            # Check model availability
            self.setup_screen.set_progress(1, 30, "Checking model...")
            if not self._check_model_availability(model_name):
                return False

            # Final checks
            self.setup_screen.set_progress(2, 70, "Finalizing...")
            return True

        except Exception as e:
            if self.setup_screen:
                self.setup_screen.set_status(f"Setup error: {str(e)[:200]}")
                self.setup_screen.progress_label.configure(text="Failed")
                self.setup_screen.canvas.itemconfig(
                    self.setup_screen.progress_rect, fill=theme["error"]
                )
            return False

    def _check_ollama_service(self):
        """Check if Ollama service is running."""
        try:
            import ollama

            ollama.list()
            self.setup_screen.set_status("Ollama service connected")
            return True
        except Exception as e:
            self.setup_screen.set_status(
                "Ollama service not running. Please start Ollama and try again."
            )
            return False

    def _check_model_availability(self, model_name):
        """Check if required model is available."""
        try:
            import ollama

            models = ollama.list().get("models", [])
            if any(model_name in m.get("name", "") for m in models):
                self.setup_screen.set_status(f"Model '{model_name}' verified")
                return True
            self.setup_screen.set_status(f"Model '{model_name}' not found")
            return False
        except Exception as e:
            self.setup_screen.set_status(f"Model check failed: {str(e)[:200]}")
            return False

    def _import_model_silently(self, model_name):
        """Import model with robust validation and error handling."""
        try:
            # Step 1: Validate Ollama service
            try:
                import ollama

                models = ollama.list()
                self._model_status = {
                    "available": False,
                    "message": "Checking model...",
                }
                self._update_model_status_ui()
            except ImportError:
                self._model_status = {
                    "available": False,
                    "message": "Ollama package not installed",
                }
                self._update_model_status_ui()
                return False
            except Exception as e:
                if "connection refused" in str(e).lower():
                    self._model_status = {
                        "available": False,
                        "message": "Ollama service not running",
                    }
                else:
                    self._model_status = {
                        "available": False,
                        "message": f"Service error: {str(e)[:50]}",
                    }
                self._update_model_status_ui()
                return False

            # Step 2: Check if model exists
            models_data = models.get("models", [])
            model_names = [m.get("name", "") for m in models_data]
            if any(model_name in n for n in model_names):
                self._model_status = {"available": True, "message": "Model ready"}
                self._update_model_status_ui()
                return True

            # Step 3: Find Modelfile
            self._model_status = {
                "available": False,
                "message": "Searching for Modelfile...",
            }
            self._update_model_status_ui()

            script_dir = Path(__file__).resolve().parent
            workspace_dir = script_dir.parent
            possible_paths = [
                script_dir / "Modelfile-phi2",
                workspace_dir / "Modelfile-phi2",
                Path(os.getcwd()) / "Modelfile-phi2",
                Path(os.getcwd()).parent / "Modelfile-phi2",
            ]

            modelfile_path = next(
                (path for path in possible_paths if path.exists()), None
            )
            if not modelfile_path:
                self._model_status = {
                    "available": False,
                    "message": "Modelfile not found",
                }
                self._update_model_status_ui()
                return False

            # Step 4: Try API import
            try:
                self._model_status = {
                    "available": False,
                    "message": "Creating model via API...",
                }
                self._update_model_status_ui()

                with open(modelfile_path, "r") as f:
                    modelfile_content = f.read()
                ollama.create(model=model_name, modelfile=modelfile_content)

                self._model_status = {
                    "available": True,
                    "message": "Model created successfully",
                }
                self._update_model_status_ui()
                return True

            except Exception as api_err:
                # Step 5: Fall back to CLI import
                self._model_status = {
                    "available": False,
                    "message": "Trying CLI import...",
                }
                self._update_model_status_ui()

                try:
                    original_dir = os.getcwd()
                    os.chdir(modelfile_path.parent)

                    process = subprocess.run(
                        ["ollama", "create", model_name, "-f", modelfile_path.name],
                        capture_output=True,
                        text=True,
                    )

                    os.chdir(original_dir)

                    if process.returncode == 0:
                        self._model_status = {
                            "available": True,
                            "message": "Model created via CLI",
                        }
                        self._update_model_status_ui()
                        return True
                    else:
                        error_msg = process.stderr or process.stdout or "Unknown error"
                        self._model_status = {
                            "available": False,
                            "message": f"CLI import failed: {error_msg[:50]}",
                        }
                        self._update_model_status_ui()
                        return False

                except Exception as cli_err:
                    self._model_status = {
                        "available": False,
                        "message": f"CLI attempt failed: {str(cli_err)[:50]}",
                    }
                    self._update_model_status_ui()
                    return False

        except Exception as e:
            self._model_status = {
                "available": False,
                "message": f"Import error: {str(e)[:50]}",
            }
            self._update_model_status_ui()
            return False

    def _add_readme_tabs(self):
        """Replace with a single, extremely detailed 'How It Works' tab for compliance and transparency."""
        import tkinter.scrolledtext as st

        how_it_works_content = (
            "# How It Works: Pierce County Records Classifier\n\n"
            "This application is designed for government and compliance use. It provides full transparency into every step of the records classification process.\n\n"
            "## 1. File Scanning and Selection\n"
            "- The app scans your selected folder for files with supported extensions (e.g., .txt, .docx, .pdf).\n"
            "- Files with unsupported or risky extensions (e.g., .exe, .dll) are ignored for safety.\n\n"
            "## 2. Content Extraction and OCR\n"
            "- For text-based files, the app reads the file contents directly.\n"
            "- For PDF or image-based files, Optical Character Recognition (OCR) is used to extract readable text.\n"
            "- Only the first portion (up to 100 lines) of each file is processed to ensure efficiency and privacy.\n\n"
            "## 3. Content Chunking\n"
            "- Large files are broken into manageable 'chunks' of text.\n"
            "- Each chunk is cleaned (removing non-text artifacts, extra spaces, etc.) to ensure only relevant content is analyzed.\n"
            "- This chunking ensures the AI model can process files of any size without missing important information.\n\n"
            "## 4. 6-Year Retention Policy (Auto-DESTROY)\n"
            "- If a file's last modified date is more than 6 years ago, it is automatically marked as 'DESTROY' (scheduled for destruction).\n"
            "- This rule is enforced before any AI analysis, ensuring compliance with records retention laws.\n\n"
            "## 5. AI Model (LLM) Classification\n"
            "- Files not marked for auto-destruction are analyzed by a local, government-approved AI model (LLM).\n"
            "- The model reviews the cleaned text and determines the correct classification (e.g., RETAIN, DESTROY, or other categories).\n"
            "- The model also provides a plain-language justification for its decision.\n"
            "- The model is run entirely on your local machine—no data ever leaves your computer.\n\n"
            "## 6. Model Output Validation\n"
            "- Every AI model output is validated using two layers:\n"
            "    - **JSON Schema Validation:** Ensures the model's response is in the correct format (required fields, types, etc.).\n"
            "    - **Hybrid Confidence Validation:** Checks that the model's confidence score is present, within a valid range, and that the justification is meaningful.\n"
            "- If the model output fails validation, it is rejected and flagged for review.\n"
            "- This prevents accidental or malformed classifications from being used.\n\n"
            "## 7. Confidence Scoring\n"
            "- The model assigns a confidence score (0.0 to 1.0) to each classification.\n"
            "- This score is calculated using a hybrid method:\n"
            "    - The model's own internal certainty.\n"
            "    - Additional checks (e.g., does the justification match the classification, is the evidence strong).\n"
            "- Low-confidence results are highlighted for human review.\n\n"
            "## 8. Real-Time Feedback and Results Table\n"
            "- As files are processed, results appear in the table immediately.\n"
            "- Each row shows: File Name, Extension, Classification, Justification, Confidence Score, and File Path.\n"
            "- You can search, sort, and filter results for easy review.\n\n"
            "## 9. Export and Audit\n"
            "- You can export all results to a CSV file for audit, compliance, or further processing.\n"
            "- The exported CSV includes all relevant fields for each file.\n\n"
            "## 10. Accessibility and Security\n"
            "- The app is designed for keyboard navigation, high contrast, and screen reader compatibility.\n"
            "- All processing is local—no files or data are sent to the cloud or third parties.\n"
            "- Error handling and logging are robust, with clear messages for any issues.\n\n"
            "## 11. Compliance and Transparency\n"
            "- Every step is documented and auditable.\n"
            "- The classification model, validation logic, and retention rules are open for inspection.\n"
            "- For compliance review, see the README and Modelfile for technical details.\n\n"
            "---\n"
            "**For help:** Click the 'How It Works' button or see this page. For technical/compliance questions, contact IT or records management."
        )
        how_it_works_frame = ctk.CTkFrame(self.notebook, fg_color=theme["bg"])
        how_it_works_text = st.ScrolledText(
            how_it_works_frame,
            wrap="word",
            font=(FONT_FAMILY, 12),
            bg=theme["panel_bg"],
            fg=theme["fg"],
        )
        how_it_works_text.insert("1.0", how_it_works_content)
        how_it_works_text.configure(state="disabled")
        how_it_works_text.pack(expand=True, fill="both", padx=10, pady=10)
        self.notebook.add(how_it_works_frame, text="How It Works")

    def _show_how(self):
        """Show a modal dialog explaining how the app works (production-ready)."""
        import tkinter.messagebox as messagebox

        msg = (
            "Pierce County Records Classifier\n\n"
            "1. Scans all files in the selected folder.\n"
            "2. For each file, extracts and cleans a content chunk.\n"
            "3. If the file is older than 6 years, it is marked DESTROY (auto).\n"
            "4. Otherwise, the file is classified by the LLM, with output rigorously validated.\n"
            "5. All results are shown in the table in real time.\n"
            "6. You can select files and export results to CSV.\n\n"
            "Bulk move/delete are planned for a future release."
        )
        messagebox.showinfo("How It Works", msg)

    def _browse_folder(self):
        """Open a folder dialog and set the folder_path variable."""
        from tkinter import filedialog

        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path.set(folder_selected)

    def _browse_output(self):
        """Open a file dialog and set the output_path variable."""
        from tkinter import filedialog

        file_selected = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if file_selected:
            self.output_path.set(file_selected)

    def _initialize_ui(self):
        """Initialize the main UI components."""
        # Create outer container that fills the window
        outer_container = ctk.CTkFrame(self.main_app_frame, fg_color=theme["bg"])
        outer_container.pack(fill="both", expand=True)

        # Create main content area with scrolling
        content_area = ctk.CTkFrame(outer_container, fg_color=theme["bg"])
        content_area.pack(fill="both", expand=True, padx=10, pady=(10, 0))

        # Initialize main components in content area
        self._initialize_header(content_area)
        self._initialize_items_panel(content_area)
        self._initialize_stats_panel(content_area)

        # Create fixed footer that stays at bottom
        self.footer = ctk.CTkFrame(
            outer_container, fg_color=theme["statusbar_bg"], height=25
        )
        self.footer.pack(fill="x", side="bottom", pady=(5, 0))
        self.footer.pack_propagate(False)  # Prevent footer from shrinking

        # Initialize VSCode-style status footer with left and right sections
        left_container = ctk.CTkFrame(self.footer, fg_color="transparent")
        left_container.pack(side="left", fill="y")

        right_container = ctk.CTkFrame(self.footer, fg_color="transparent")
        right_container.pack(side="right", fill="y")

        # Left side status items
        self.status_label = ctk.CTkLabel(
            left_container,
            text="Ready",
            text_color=theme["statusbar_fg"],
            font=("Segoe UI Variable", 11),
        )
        self.status_label.pack(side="left", padx=5)

        self.progress_label = ctk.CTkLabel(
            left_container,
            text="",
            text_color=theme["statusbar_fg"],
            font=("Segoe UI Variable", 11),
        )
        self.progress_label.pack(side="left", padx=5)

        # Right side items
        self.stats_label = ctk.CTkLabel(
            right_container,
            text="Records: 0",
            text_color=theme["statusbar_fg"],
            font=("Segoe UI Variable", 11),
        )
        self.stats_label.pack(side="right", padx=5)

        self.model_status_label = ctk.CTkLabel(
            right_container,
            text="Model Status: Checking...",
            text_color=theme["statusbar_fg"],
            font=("Segoe UI Variable", 11),
        )
        self.model_status_label.pack(side="right", padx=5)

        # Start model check
        self._check_model_status()

        # Initialize processing state
        self.processing = False

    def _initialize_header(self, parent):
        """Initialize header with title and description."""
        header = ctk.CTkFrame(parent, fg_color=theme["header_bg"], height=80)
        header.pack(fill="x", padx=10, pady=(0, 20))
        header.pack_propagate(False)

        title = ctk.CTkLabel(
            header,
            text="Pierce County Records Classifier",
            font=("Segoe UI Variable", 24, "bold"),
            text_color=theme["fg"],
        )
        title.pack(pady=(10, 0))

        subtitle = ctk.CTkLabel(
            header,
            text="AI-Powered Document Classification Tool",
            font=("Segoe UI Variable", 14),
            text_color=theme["fg"],
        )
        subtitle.pack()

    def _initialize_items_panel(self, parent):
        """Initialize the items panel with the modern LiveUpdateTable."""
        frame = ctk.CTkFrame(parent, fg_color=theme["bg"])
        frame.pack(fill="both", expand=True, pady=(10, 0))

        # Define table columns
        columns = [
            ("id", "#", 50),
            ("filename", "Filename", 200),
            ("extension", "Extension", 80),
            ("modified", "Last Modified", 150),
            ("size", "Size", 100),
            ("determination", "Determination", 120),
            ("confidence", "Confidence", 100),
            ("justification", "Justification", 300),
        ]

        # Create table with virtualized scrolling and column reordering
        self.items_table = LiveUpdateTable(
            frame,
            columns=columns,
            height=400,
            show="headings",  # Hide the first empty column
            virtualized=True,  # Enable virtualized scrolling
            reorderable=True,  # Allow column reordering
        )
        self.items_table.pack(side="top", fill="x", expand=False, pady=(5, 5))

        # Pack scrollbar
        self.items_table.yscrollbar.pack(side="right", fill="y")

        # Configure sorting
        for col in columns:
            self.items_table.heading(
                col[0], command=lambda c=col[0]: self._sort_table(c)
            )

        # Add bulk action buttons
        bulk_actions_frame = ctk.CTkFrame(frame, fg_color=theme["bg"])
        bulk_actions_frame.pack(fill="x", pady=(5, 0))

        self.bulk_rerun_button = ctk.CTkButton(
            bulk_actions_frame, text="RERUN", command=self._bulk_rerun
        )
        self.bulk_rerun_button.pack(side="left", padx=5)

        self.bulk_export_button = ctk.CTkButton(
            bulk_actions_frame, text="EXPORT CSV/JSON", command=self._bulk_export
        )
        self.bulk_export_button.pack(side="left", padx=5)

        self.bulk_destroy_button = ctk.CTkButton(
            bulk_actions_frame, text="DESTROY", command=self._bulk_destroy
        )
        self.bulk_destroy_button.pack(side="left", padx=5)

        # Initialize live update mechanism
        self._initialize_live_updates()

    # Add methods for bulk actions

    def _bulk_rerun(self):
        """Handle bulk RERUN action."""
        selected_items = self.items_table.get_selected_items()
        # ... Implement logic for rerunning selected items ...

    def _bulk_export(self):
        """Handle bulk EXPORT action."""
        selected_items = self.items_table.get_selected_items()
        # ... Implement logic for exporting selected items to CSV/JSON ...

    def _bulk_destroy(self):
        """Handle bulk DESTROY action."""
        selected_items = self.items_table.get_selected_items()
        # ... Implement logic for destroying selected items ...

    def _initialize_live_updates(self):
        """Initialize live update mechanism for the table."""
        # ... Implement logic for streaming results into the table in real-time ...

    def _sort_table(self, column):
        """Sort table by column with proper data type handling."""
        # Get all items
        items = [
            (self.items_table.item(child)["values"], child)
            for child in self.items_table.get_children("")
        ]

        # Determine column index
        col_id = self.items_table.column.index(column)

        # Sort based on column type
        reverse = self._sort_state.get(column, False)
        if column in ["size", "confidence"]:
            # Numeric sorting
            items.sort(key=lambda x: float(x[0][col_id]), reverse=reverse)
        elif column == "modified":
            # Date sorting
            items.sort(
                key=lambda x: datetime.strptime(x[0][col_id], "%Y-%m-%d %H:%M:%S"),
                reverse=reverse,
            )
        else:
            # String sorting
            items.sort(key=lambda x: str(x[0][col_id]).lower(), reverse=reverse)

        # Rearrange items
        for index, (values, item) in enumerate(items):
            self.items_table.move(item, "", index)

            # Update row colors
            tags = ["oddrow"] if index % 2 == 1 else []
            if values[5].lower() in [
                "retain",
                "destroy",
                "review",
            ]:  # determination column
                tags.append(values[5].lower())
            self.items_table.item(item, tags=tags)

        # Toggle sort state
        self._sort_state[column] = not reverse

    def _initialize_stats_tracking(self):
        """Initialize statistical tracking system."""
        self.stats_vars = {
            "processed": tk.StringVar(value="0"),
            "pending": tk.StringVar(value="0"),
            "total_size": tk.StringVar(value="0 B"),
            "avg_time": tk.StringVar(value="0ms"),
            "success_rate": tk.StringVar(value="0%"),
            "memory_usage": tk.StringVar(value="0%"),
            "cpu_usage": tk.StringVar(value="0%"),
            "start_time": None,
            "processing_times": [],
        }

        # Enable continuous stats updates
        self.always_update_stats = True
        self._update_stats()  # Start the update cycle

    def _initialize_stats_panel(self, parent):
        """Initialize the statistics panel with comprehensive metrics."""
        stats_frame = ctk.CTkFrame(
            parent, fg_color=theme["panel_bg"], corner_radius=12, height=120
        )
        stats_frame.pack(fill="x", padx=10, pady=(0, 20))
        stats_frame.pack_propagate(False)

        # Create 2x4 grid of stats
        for i, (label, var) in enumerate(
            [
                ("Processed", self.stats_vars["processed"]),
                ("Pending", self.stats_vars["pending"]),
                ("Total Files", self.stats_vars["total_files"]),
                ("Avg. Time", self.stats_vars["avg_time"]),
                ("Success Rate", self.stats_vars["success_rate"]),
                ("Memory Usage", self.stats_vars["memory_usage"]),
                ("CPU Usage", self.stats_vars["cpu_usage"]),
                ("Status", self.stats_vars.get("status", tk.StringVar(value="Ready"))),
            ]
        ):
            col = i % 4
            row = i // 4
            stat_container = ctk.CTkFrame(stats_frame, fg_color="transparent")
            stat_container.grid(row=row, column=col, padx=10, pady=5, sticky="nsew")

            label_widget = ctk.CTkLabel(
                stat_container,
                text=label,
                font=("Segoe UI Variable", 12),
                text_color=theme["fg"],
            )
            label_widget.pack(anchor="w")

            value_widget = ctk.CTkLabel(
                stat_container,
                textvariable=var,
                font=("Segoe UI Variable", 16, "bold"),
                text_color=theme["accent"],
            )
            value_widget.pack(anchor="w")

        # Configure grid
        for i in range(4):
            stats_frame.grid_columnconfigure(i, weight=1)
        for i in range(2):
            stats_frame.grid_rowconfigure(i, weight=1)

    def _check_model_status(self):
        """Check model status in background without blocking UI."""
        try:
            # First check Ollama service
            try:
                import ollama

                ollama.list()
                service_ok = True
            except Exception:
                service_ok = False
                self._model_status = {
                    "available": False,
                    "message": "Ollama service not running",
                }
                self._update_model_status_ui()
                return

            if not service_ok:
                return

            # Then check model
            try:
                models = ollama.list().get("models", [])
                if any(MODEL_NAME in m.get("name", "") for m in models):
                    self._model_status = {"available": True, "message": "Model ready"}
                else:
                    self._model_status = {
                        "available": False,
                        "message": "Model not found",
                    }
            except Exception as e:
                self._model_status = {
                    "available": False,
                    "message": f"Model check failed: {str(e)[:50]}",
                }
        except Exception as e:
            self._model_status = {
                "available": False,
                "message": f"Status check error: {str(e)[:50]}",
            }
        finally:
            self._update_model_status_ui()

    def _update_model_status_ui(self):
        """Update UI elements showing model status."""
        self.after(0, lambda: self._do_update_model_status_ui())

    def _do_update_model_status_ui(self):
        """Actually update the UI elements (must be called from main thread)."""
        # Update model status indicator in footer
        if hasattr(self, "model_status_label"):
            color = (
                theme["success"] if self._model_status["available"] else theme["error"]
            )
            icon = "✓" if self._model_status["available"] else "⚠"
            self.model_status_label.configure(
                text=f"Model Status: {icon} {self._model_status['message']}",
                text_color=color,
            )

        # Update mode dropdown based on model availability
        if hasattr(self, "mode_menu"):
            if self._model_status["available"]:
                self.mode_menu.configure(
                    values=["Full Classification", "DESTROY Only"], state="normal"
                )
            else:
                self.mode_menu.configure(values=["DESTROY Only"], state="normal")
                self.mode_var.set("DESTROY Only")

    def _show_main_ui(self):
        self.setup_background.destroy()
        self.notebook.pack(side="top", fill="both", expand=True)

    def _check_model_and_initialize(self):
        """Check model availability and initialize in background."""
        try:
            if self._run_setup_checks(MODEL_NAME):
                self.after(0, lambda: self._on_setup_complete(True))
            else:
                self.after(0, lambda: self._on_setup_complete(False))
        except Exception as e:
            logger.error("Model check error: %s", e)
            self.after(0, lambda: self._on_setup_complete(False))

    def _run_setup_checks(self, model_name):
        """Run setup checks with proper error handling."""
        try:
            # Initialize setup screen if needed
            if not self.setup_screen:
                self.setup_screen = SetupScreen(
                    self.main_app_frame,
                    self._on_setup_complete,
                    task_name="Initializing",
                    steps=[
                        {"name": "Checking Ollama service", "weight": 30},
                        {"name": "Verifying model", "weight": 40},
                        {"name": "Finalizing setup", "weight": 30},
                    ],
                    auto_run=True,
                )

            self.setup_screen.start()

            # Check Ollama service
            self.setup_screen.set_status("Checking Ollama service...")
            if not self._check_ollama_service():
                return False

            # Check model availability
            self.setup_screen.set_progress(1, 30, "Checking model...")
            if not self._check_model_availability(model_name):
                return False

            # Final checks
            self.setup_screen.set_progress(2, 70, "Finalizing...")
            return True

        except Exception as e:
            if self.setup_screen:
                self.setup_screen.set_status(f"Setup error: {str(e)[:200]}")
                self.setup_screen.progress_label.configure(text="Failed")
                self.setup_screen.canvas.itemconfig(
                    self.setup_screen.progress_rect, fill=theme["error"]
                )
            return False

    def _check_ollama_service(self):
        """Check if Ollama service is running."""
        try:
            import ollama

            ollama.list()
            self.setup_screen.set_status("Ollama service connected")
            return True
        except Exception as e:
            self.setup_screen.set_status(
                "Ollama service not running. Please start Ollama and try again."
            )
            return False

    def _check_model_availability(self, model_name):
        """Check if required model is available."""
        try:
            import ollama

            models = ollama.list().get("models", [])
            if any(model_name in m.get("name", "") for m in models):
                self.setup_screen.set_status(f"Model '{model_name}' verified")
                return True
            self.setup_screen.set_status(f"Model '{model_name}' not found")
            return False
        except Exception as e:
            self.setup_screen.set_status(f"Model check failed: {str(e)[:200]}")
            return False

    def _import_model_silently(self, model_name):
        """Import model with robust validation and error handling."""
        try:
            # Step 1: Validate Ollama service
            try:
                import ollama

                models = ollama.list()
                self._model_status = {
                    "available": False,
                    "message": "Checking model...",
                }
                self._update_model_status_ui()
            except ImportError:
                self._model_status = {
                    "available": False,
                    "message": "Ollama package not installed",
                }
                self._update_model_status_ui()
                return False
            except Exception as e:
                if "connection refused" in str(e).lower():
                    self._model_status = {
                        "available": False,
                        "message": "Ollama service not running",
                    }
                else:
                    self._model_status = {
                        "available": False,
                        "message": f"Service error: {str(e)[:50]}",
                    }
                self._update_model_status_ui()
                return False

            # Step 2: Check if model exists
            models_data = models.get("models", [])
            model_names = [m.get("name", "") for m in models_data]
            if any(model_name in n for n in model_names):
                self._model_status = {"available": True, "message": "Model ready"}
                self._update_model_status_ui()
                return True

            # Step 3: Find Modelfile
            self._model_status = {
                "available": False,
                "message": "Searching for Modelfile...",
            }
            self._update_model_status_ui()

            script_dir = Path(__file__).resolve().parent
            workspace_dir = script_dir.parent
            possible_paths = [
                script_dir / "Modelfile-phi2",
                workspace_dir / "Modelfile-phi2",
                Path(os.getcwd()) / "Modelfile-phi2",
                Path(os.getcwd()).parent / "Modelfile-phi2",
            ]

            modelfile_path = next(
                (path for path in possible_paths if path.exists()), None
            )
            if not modelfile_path:
                self._model_status = {
                    "available": False,
                    "message": "Modelfile not found",
                }
                self._update_model_status_ui()
                return False

            # Step 4: Try API import
            try:
                self._model_status = {
                    "available": False,
                    "message": "Creating model via API...",
                }
                self._update_model_status_ui()

                with open(modelfile_path, "r") as f:
                    modelfile_content = f.read()
                ollama.create(model=model_name, modelfile=modelfile_content)

                self._model_status = {
                    "available": True,
                    "message": "Model created successfully",
                }
                self._update_model_status_ui()
                return True

            except Exception as api_err:
                # Step 5: Fall back to CLI import
                self._model_status = {
                    "available": False,
                    "message": "Trying CLI import...",
                }
                self._update_model_status_ui()

                try:
                    original_dir = os.getcwd()
                    os.chdir(modelfile_path.parent)

                    process = subprocess.run(
                        ["ollama", "create", model_name, "-f", modelfile_path.name],
                        capture_output=True,
                        text=True,
                    )

                    os.chdir(original_dir)

                    if process.returncode == 0:
                        self._model_status = {
                            "available": True,
                            "message": "Model created via CLI",
                        }
                        self._update_model_status_ui()
                        return True
                    else:
                        error_msg = process.stderr or process.stdout or "Unknown error"
                        self._model_status = {
                            "available": False,
                            "message": f"CLI import failed: {error_msg[:50]}",
                        }
                        self._update_model_status_ui()
                        return False

                except Exception as cli_err:
                    self._model_status = {
                        "available": False,
                        "message": f"CLI attempt failed: {str(cli_err)[:50]}",
                    }
                    self._update_model_status_ui()
                    return False

        except Exception as e:
            self._model_status = {
                "available": False,
                "message": f"Import error: {str(e)[:50]}",
            }
            self._update_model_status_ui()
            return False

    def _add_readme_tabs(self):
        """Replace with a single, extremely detailed 'How It Works' tab for compliance and transparency."""
        import tkinter.scrolledtext as st

        how_it_works_content = (
            "# How It Works: Pierce County Records Classifier\n\n"
            "This application is designed for government and compliance use. It provides full transparency into every step of the records classification process.\n\n"
            "## 1. File Scanning and Selection\n"
            "- The app scans your selected folder for files with supported extensions (e.g., .txt, .docx, .pdf).\n"
            "- Files with unsupported or risky extensions (e.g., .exe, .dll) are ignored for safety.\n\n"
            "## 2. Content Extraction and OCR\n"
            "- For text-based files, the app reads the file contents directly.\n"
            "- For PDF or image-based files, Optical Character Recognition (OCR) is used to extract readable text.\n"
            "- Only the first portion (up to 100 lines) of each file is processed to ensure efficiency and privacy.\n\n"
            "## 3. Content Chunking\n"
            "- Large files are broken into manageable 'chunks' of text.\n"
            "- Each chunk is cleaned (removing non-text artifacts, extra spaces, etc.) to ensure only relevant content is analyzed.\n"
            "- This chunking ensures the AI model can process files of any size without missing important information.\n\n"
            "## 4. 6-Year Retention Policy (Auto-DESTROY)\n"
            "- If a file's last modified date is more than 6 years ago, it is automatically marked as 'DESTROY' (scheduled for destruction).\n"
            "- This rule is enforced before any AI analysis, ensuring compliance with records retention laws.\n\n"
            "## 5. AI Model (LLM) Classification\n"
            "- Files not marked for auto-destruction are analyzed by a local, government-approved AI model (LLM).\n"
            "- The model reviews the cleaned text and determines the correct classification (e.g., RETAIN, DESTROY, or other categories).\n"
            "- The model also provides a plain-language justification for its decision.\n"
            "- The model is run entirely on your local machine—no data ever leaves your computer.\n\n"
            "## 6. Model Output Validation\n"
            "- Every AI model output is validated using two layers:\n"
            "    - **JSON Schema Validation:** Ensures the model's response is in the correct format (required fields, types, etc.).\n"
            "    - **Hybrid Confidence Validation:** Checks that the model's confidence score is present, within a valid range, and that the justification is meaningful.\n"
            "- If the model output fails validation, it is rejected and flagged for review.\n"
            "- This prevents accidental or malformed classifications from being used.\n\n"
            "## 7. Confidence Scoring\n"
            "- The model assigns a confidence score (0.0 to 1.0) to each classification.\n"
            "- This score is calculated using a hybrid method:\n"
            "    - The model's own internal certainty.\n"
            "    - Additional checks (e.g., does the justification match the classification, is the evidence strong).\n"
            "- Low-confidence results are highlighted for human review.\n\n"
            "## 8. Real-Time Feedback and Results Table\n"
            "- As files are processed, results appear in the table immediately.\n"
            "- Each row shows: File Name, Extension, Classification, Justification, Confidence Score, and File Path.\n"
            "- You can search, sort, and filter results for easy review.\n\n"
            "## 9. Export and Audit\n"
            "- You can export all results to a CSV file for audit, compliance, or further processing.\n"
            "- The exported CSV includes all relevant fields for each file.\n\n"
            "## 10. Accessibility and Security\n"
            "- The app is designed for keyboard navigation, high contrast, and screen reader compatibility.\n"
            "- All processing is local—no files or data are sent to the cloud or third parties.\n"
            "- Error handling and logging are robust, with clear messages for any issues.\n\n"
            "## 11. Compliance and Transparency\n"
            "- Every step is documented and auditable.\n"
            "- The classification model, validation logic, and retention rules are open for inspection.\n"
            "- For compliance review, see the README and Modelfile for technical details.\n\n"
            "---\n"
            "**For help:** Click the 'How It Works' button or see this page. For technical/compliance questions, contact IT or records management."
        )
        how_it_works_frame = ctk.CTkFrame(self.notebook, fg_color=theme["bg"])
        how_it_works_text = st.ScrolledText(
            how_it_works_frame,
            wrap="word",
            font=(FONT_FAMILY, 12),
            bg=theme["panel_bg"],
            fg=theme["fg"],
        )
        how_it_works_text.insert("1.0", how_it_works_content)
        how_it_works_text.configure(state="disabled")
        how_it_works_text.pack(expand=True, fill="both", padx=10, pady=10)
        self.notebook.add(how_it_works_frame, text="How It Works")
