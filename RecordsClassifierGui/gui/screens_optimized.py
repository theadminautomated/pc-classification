"""GUI screens module for Records Classifier application.

This module provides modular screen/flow management for the Records Classifier GUI,
including setup screens, main classification interface, and completion panels.
"""

import asyncio
import concurrent.futures
import csv
import json
import multiprocessing
import os
import socket
import sys
import threading
import tkinter as tk
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, Dict, Optional

import customtkinter as ctk
import importlib.util

# Dynamically load Electronic-Records-Classification.py
classification_spec = importlib.util.spec_from_file_location(
    "ElectronicRecordsClassification", 
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../Electronic-Records-Classification.py"))
)
ElectronicRecordsClassification = importlib.util.module_from_spec(classification_spec)
classification_spec.loader.exec_module(ElectronicRecordsClassification)

# Import required functions and constants
process_file = ElectronicRecordsClassification.process_file
INCLUDE_EXT = ElectronicRecordsClassification.INCLUDE_EXT
EXCLUDE_EXT = ElectronicRecordsClassification.EXCLUDE_EXT


def _make_http_request(url: str, method: str = 'GET', data: dict = None, timeout: int = 30) -> tuple[bool, Any]:
    """Make HTTP request using urllib (standard library).
    
    Args:
        url: The URL to make the request to
        method: HTTP method ('GET' or 'POST')
        data: Request data for POST requests
        timeout: Request timeout in seconds
        
    Returns:
        Tuple of (success: bool, response_data: Any)
    """
    try:
        if method == 'GET':
            with urllib.request.urlopen(url, timeout=timeout) as response:
                response_data = response.read().decode('utf-8')
                try:
                    return True, json.loads(response_data)
                except json.JSONDecodeError:
                    # Extract first valid JSON object
                    import re
                    json_pattern = r'({[\s\S]*?})'
                    matches = re.findall(json_pattern, response_data)
                    if matches:
                        return True, json.loads(matches[0])
                    return False, {"error": "Invalid JSON response", "data": response_data[:100]}
        else:  # POST
            request_data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(url, data=request_data, 
                                      headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                response_data = response.read().decode('utf-8')
                try:
                    return True, json.loads(response_data)
                except json.JSONDecodeError:
                    # Extract first valid JSON object
                    import re
                    json_pattern = r'({[\s\S]*?})'
                    matches = re.findall(json_pattern, response_data)
                    if matches:
                        return True, json.loads(matches[0])
                    return False, {"error": "Invalid JSON response", "data": response_data[:100]}
    except Exception as e:
        return False, {"error": str(e)}


def _import_local(name):
    """Import local module dynamically.
    
    Args:
        name: Module name to import
        
    Returns:
        Imported module object
    """
    here = os.path.dirname(__file__)
    spec = importlib.util.spec_from_file_location(name, os.path.join(here, f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# Import theme configuration
theme_mod = _import_local('theme')
theme = theme_mod.theme
FONT_FAMILY = theme_mod.FONT_FAMILY
PADDING = theme_mod.PADDING
SPACING = theme_mod.SPACING
CARD_RADIUS = theme_mod.CARD_RADIUS


class SetupScreen(ctk.CTkFrame):
    """Setup screen for application initialization.
    
    Provides visual feedback for startup tasks with progress indication
    and handles service validation and model verification.
    """

    def __init__(self, parent, on_complete=None, steps=None, task_name="Initializing", auto_run=False):
        """Initialize the setup screen.
        
        Args:
            parent: Parent widget
            on_complete: Callback function to execute when setup completes
            steps: List of setup steps with weights
            task_name: Display name for the setup task
            auto_run: Whether to automatically start setup
        """
        super().__init__(parent, fg_color=theme.get('bg', '#1e1e1e'))
        self.parent = parent
        self.on_complete = on_complete
        self.steps = steps if steps and len(steps) > 0 else [{'name': 'Initializing', 'weight': 1}]
        self.task_name = task_name
        self.current_step = -1
        self.current_progress = 0
        self.auto_run = auto_run
        self.running = False
        self.setup_thread = None
        self.total_weight = sum(step['weight'] for step in self.steps)
        self.ollama_port = 11434  # Default Ollama port
        
        if self.total_weight <= 0:
            raise ValueError("Total step weight must be greater than 0")

        # Center the content
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Create UI elements
        self._create_ui()

        # Set up task execution map
        self.task_map = {
            "Checking Ollama service": self._check_ollama_service,
            "Verifying model": self._verify_model,
            "Finalizing setup": self._finalize_setup
        }

        if auto_run:
            self.after(100, self.start)

    def _create_ui(self):
        """Create the UI elements for the setup screen."""
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=0, column=0, padx=20, pady=20)

        # Title
        title = ctk.CTkLabel(
            content_frame,
            text=self.task_name,
            font=(FONT_FAMILY, 24, "bold"),
            text_color=theme.get('fg', 'white')
        )
        title.pack(pady=(0, 20))

        # Progress container
        progress_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        progress_frame.pack(fill="x", padx=20)

        # Status message
        self.status_label = ctk.CTkLabel(
            progress_frame,
            text="Preparing...",
            font=(FONT_FAMILY, 14),
            text_color=theme.get('fg_secondary', '#cccccc'),
            justify="left"
        )
        self.status_label.pack(fill="x", pady=(0, 10))

        # Canvas for custom progress bar
        self.canvas = tk.Canvas(
            progress_frame,
            height=12,
            bd=0,
            highlightthickness=0,
            bg=theme.get('progress_bg', '#1e293b')
        )
        self.canvas.pack(fill="x", padx=2)

        # Create progress rectangle
        self.progress_rect = self.canvas.create_rectangle(
            0, 0, 0, 12,
            fill=theme.get('accent', '#0078d4'),
            width=0
        )

        # Progress label
        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="Starting...",
            font=(FONT_FAMILY, 12),
            text_color=theme.get('fg_secondary', '#94a3b8')
        )
        self.progress_label.pack(pady=(5, 0))

        # Step progress
        self.step_label = ctk.CTkLabel(
            progress_frame,
            text=f"Step 0/{len(self.steps)}",
            font=(FONT_FAMILY, 12),
            text_color=theme.get('fg_secondary', '#94a3b8')
        )
        self.step_label.pack(pady=(5, 0))

        # Configure canvas resize handling
        self.canvas.bind('<Configure>', self._on_canvas_resize)

    def _check_ollama_service(self) -> bool:
        """Check if Ollama service is running and accessible.
        
        Returns:
            True if service is accessible, False otherwise
        """
        try:
            # Try to connect to the Ollama service
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', self.ollama_port))
            sock.close()

            if result == 0:
                self.set_progress(0, 100, "Ollama service is running")
                return True
            else:
                self.set_progress(0, 50, "Ollama service not detected, attempting to start...")
                return self._start_ollama_service()

        except Exception as e:
            self.set_status(f"Error checking Ollama service: {str(e)[:100]}")
            return False

    def _start_ollama_service(self) -> bool:
        """Attempt to start the Ollama service.
        
        Returns:
            True if service started successfully, False otherwise
        """
        try:
            # Try starting ollama using the system's process manager
            if sys.platform == "win32":
                os.system("start ollama serve")
            else:
                os.system("ollama serve &")

            # Wait up to 30 seconds for the service to start
            attempts = 30
            while attempts > 0:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                if sock.connect_ex(('localhost', self.ollama_port)) == 0:
                    sock.close()
                    self.set_progress(0, 100, "Ollama service started successfully")
                    return True
                sock.close()
                attempts -= 1
                self.after(1000)  # Wait 1 second between attempts

            self.set_status("Timed out waiting for Ollama service to start")
            return False

        except Exception as e:
            self.set_status(f"Error starting Ollama service: {str(e)[:100]}")
            return False

    def _verify_model(self) -> bool:
        """Verify that the required model is available and properly set up.
        
        Returns:
            True if model is available, False otherwise
        """
        try:
            model_name = "phi2"  # Default model
            
            # Check if model exists in Ollama - use tags endpoint
            success, response = _make_http_request(
                f'http://localhost:{self.ollama_port}/api/tags',
                method='GET'
            )
            
            # Check if the model is in the list of available models
            if success and response and 'models' in response:
                model_exists = any(model.get('name') == model_name for model in response.get('models', []))
                if model_exists:
                    self.set_progress(1, 100, "Model verification complete")
                    return True
                
            # Model not found, attempt to pull it
            self.set_progress(1, 30, "Model not found, attempting to download...")
            success, response = _make_http_request(
                f'http://localhost:{self.ollama_port}/api/pull',
                method='POST',
                data={'name': model_name}
            )
            
            if success and response:
                self.set_progress(1, 100, "Model downloaded successfully")
                return True
            
            self.set_status("Failed to download model")
            return False

        except Exception as e:
            self.set_status(f"Error verifying model: {str(e)[:100]}")
            return False

    def _finalize_setup(self) -> bool:
        """Perform final setup tasks and verifications.
        
        Returns:
            True if setup completed successfully, False otherwise
        """
        try:
            # Verify working directory exists
            work_dir = os.path.expanduser("~/.recordsclassifier")
            if not os.path.exists(work_dir):
                os.makedirs(work_dir)
                
            # Create cache directory
            cache_dir = os.path.join(work_dir, 'cache')
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)
                
            # Create logs directory
            logs_dir = os.path.join(work_dir, 'logs')
            if not os.path.exists(logs_dir):
                os.makedirs(logs_dir)
                
            self.set_progress(2, 100, "Final setup complete")
            return True
            
        except Exception as e:
            self.set_status(f"Error in final setup: {str(e)[:100]}")
            return False

    def _execute_setup_tasks(self):
        """Execute all setup tasks in sequence."""
        try:
            for i, step in enumerate(self.steps):
                if not self.running:
                    break
                    
                step_name = step['name']
                self.current_step = i
                self.step_label.configure(text=f"Step {i+1}/{len(self.steps)}")
                
                if step_name in self.task_map:
                    task_func = self.task_map[step_name]
                    if not task_func():
                        self.complete(success=False)
                        return
                else:
                    self.set_status(f"Unknown step: {step_name}")
                    self.complete(success=False)
                    return
            
            if self.running:
                self.complete(success=True)
                
        except Exception as e:
            self.set_status(f"Setup error: {str(e)[:100]}")
            self.complete(success=False)

    def start(self):
        """Begin the setup process.
        
        Returns:
            True if setup started successfully, False otherwise
        """
        if not self.steps or self.running:
            return False
            
        self.running = True
        self.current_step = 0
        self.current_progress = 0
        
        # Update labels with initial state
        self.step_label.configure(text=f"Step 1/{len(self.steps)}")
        self.update_progress_display(0)
        
        # Start setup process in a separate thread
        self.setup_thread = threading.Thread(target=self._execute_setup_tasks)
        self.setup_thread.daemon = True
        self.setup_thread.start()
        
        return True

    def stop(self):
        """Stop the setup process."""
        self.running = False
        if self.setup_thread and self.setup_thread.is_alive():
            self.setup_thread.join(timeout=1.0)

    def set_status(self, message):
        """Update the status message.
        
        Args:
            message: Status message to display
        """
        # Use after() to ensure thread safety
        self.after(0, lambda: self.status_label.configure(text=message))

    def set_progress(self, step_index, progress_in_step, message=None):
        """Update the progress bar for the current step.
        
        Args:
            step_index: Index of current step
            progress_in_step: Progress percentage within current step
            message: Optional status message
        """
        if 0 <= step_index < len(self.steps):
            # Calculate overall progress
            prior_steps_weight = sum(self.steps[i]['weight'] for i in range(step_index))
            step_weight = self.steps[step_index]['weight']
            
            self.current_progress = (prior_steps_weight + 
                (step_weight * (progress_in_step / 100))) / self.total_weight
            
            # Update UI using after() for thread safety
            self.after(0, lambda: self._update_progress_ui(step_index, message))

    def _update_progress_ui(self, step_index, message=None):
        """Update all progress-related UI elements.
        
        Args:
            step_index: Index of current step
            message: Optional status message
        """
        self.update_progress_display(self.current_progress)
        if message:
            self.set_status(message)
        else:
            self.set_status(self.steps[step_index]['name'])
        
        self.step_label.configure(text=f"Step {step_index + 1}/{len(self.steps)}")
        self.progress_label.configure(text=f"{int(self.current_progress * 100)}% complete")
        self.update()

    def update_progress_display(self, progress):
        """Update the visual progress indicators.
        
        Args:
            progress: Progress value between 0 and 1
        """
        self.after(0, lambda: self._update_progress_bar(progress))
    
    def _update_progress_bar(self, progress):
        """Update the progress bar UI element.
        
        Args:
            progress: Progress value between 0 and 1
        """
        width = self.canvas.winfo_width()
        self.canvas.coords(self.progress_rect, 0, 0, width * progress, 12)
        
    def complete(self, success=True):
        """Mark setup as complete and trigger callback.
        
        Args:
            success: Whether setup completed successfully
        """
        self.running = False
        
        def _do_complete():
            if success:
                self.current_progress = 1.0
                self._update_progress_bar(1.0)
                self.set_status("Setup complete!")
                self.progress_label.configure(text="100% complete")
                if self.on_complete:
                    self.after(500, lambda: self.on_complete())
            else:
                self.canvas.itemconfig(self.progress_rect, fill=theme.get('error', '#dc2626'))
                self.set_status("Setup failed. Please check the logs and try again.")
                self.progress_label.configure(text="Setup failed")
                if self.on_complete:
                    self.after(500, lambda: self.on_complete(success))
                    
        self.after(0, _do_complete)
            
    def _on_canvas_resize(self, event):
        """Handle canvas resizing to keep progress bar properly scaled.
        
        Args:
            event: Tkinter resize event
        """
        self.canvas.coords(self.progress_rect, 0, 0, 
                         event.width * self.current_progress, event.height)
                         
    def destroy(self):
        """Override destroy to ensure cleanup."""
        self.stop()  # Stop any running tasks
        super().destroy()


class MainScreen(ctk.CTkFrame):
    """Main application screen for Records Classification.
    
    Provides the primary interface for file selection, classification, 
    and results viewing with optimized async processing.
    """

    def __init__(self, parent, **kwargs):
        """Initialize the main screen.
        
        Args:
            parent: Parent widget
            **kwargs: Additional keyword arguments for CTkFrame
        """
        super().__init__(parent, fg_color=theme.get('bg', '#1e1e1e'))
        self.parent = parent
        
        # Initialize core state variables
        self.model = "pierce-county-records-classifier-phi2:latest"
        self.input_folder = ""
        self.results_data = []
        self.selected_items = set()
        self.processing = False
        self.sort_reverse = {}
        self.classification_complete = False
        
        # Footer stats state
        self.success_count = 0
        self.skipped_count = 0
        self.error_count = 0
        
        # StringVars for dynamic footer stats
        self.success_var = tk.StringVar(value='0')
        self.skipped_var = tk.StringVar(value='0')
        self.error_var = tk.StringVar(value='0')
        
        # Initialize additional state variables
        self._sim_items_processed = 0
        self._classification_task = None
        self._toggle_lock = threading.Lock()

        # Configure grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Create main UI
        self._setup_ui()
        
        # Setup keyboard shortcuts
        self._setup_keyboard_shortcuts()
        
        # Ensure inline action buttons are hidden initially
        self._update_action_buttons_visibility()

    def _setup_ui(self):
        """Setup the main user interface."""
        # Main container
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_container.grid_rowconfigure(2, weight=1)  # Results table expands
        main_container.grid_columnconfigure(0, weight=1)
        
        # Header section
        self._setup_header(main_container)
        
        # Path selection and controls
        self._setup_controls(main_container)
        
        # Results table
        self._setup_results_table(main_container)
        
        # Status bar
        self._setup_status_bar(main_container)
        
    def _setup_header(self, parent):
        """Setup the header section with title and quick stats.
        
        Args:
            parent: Parent widget
        """
        header_frame = ctk.CTkFrame(parent, fg_color=theme.get('header_bg', '#2d3748'))
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Title section
        title_label = ctk.CTkLabel(
            header_frame,
            text="Pierce County Records Classifier",
            font=(FONT_FAMILY, 24, "bold"),
            text_color=theme.get('fg', 'white')
        )
        title_label.grid(row=0, column=0, sticky="w", padx=20, pady=(15, 5))
        
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Analyze and classify documents based on Washington State Record Retention policies",
            font=(FONT_FAMILY, 12),
            text_color=theme.get('fg_secondary', '#94a3b8')
        )
        subtitle_label.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 15))
        
    def _setup_controls(self, parent):
        """Setup the path selection and control buttons.
        
        Args:
            parent: Parent widget
        """
        controls_frame = ctk.CTkFrame(parent, fg_color=theme.get('card_bg', '#374151'))
        controls_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        controls_frame.grid_columnconfigure(1, weight=1)
        
        # Input folder selection
        ctk.CTkLabel(
            controls_frame,
            text="Input Folder:",
            font=(FONT_FAMILY, 12, "bold")
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(15, 5))
        
        folder_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        folder_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 10))
        folder_frame.grid_columnconfigure(0, weight=1)
        
        self.folder_entry = ctk.CTkEntry(
            folder_frame,
            placeholder_text="Select a folder containing files to classify...",
            font=(FONT_FAMILY, 11),
            height=32
        )
        self.folder_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.folder_entry.bind('<KeyRelease>', self._on_folder_change)
        
        folder_browse_btn = ctk.CTkButton(
            folder_frame,
            text="Browse",
            width=80,
            height=32,
            command=self._browse_folder
        )        
        folder_browse_btn.grid(row=0, column=1)
        
        # Action buttons
        button_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        button_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=(10, 15))
        
        self.run_button = ctk.CTkButton(
            button_frame,
            text="Start Classification",
            font=(FONT_FAMILY, 12, "bold"),
            height=36,
            command=self._toggle_classification
        )
        self.run_button.pack(side="left", padx=(0, 10), anchor="center")
        
        # Lines-per-file slider for controlling the amount of text analyzed
        
        # Add dropdown for classification mode
        self.mode_var = tk.StringVar(value="Classification")
        mode_dropdown = ctk.CTkComboBox(
            controls_frame,
            values=["Classification", "Last Modified"],
            variable=self.mode_var,
            font=(FONT_FAMILY, 11),
            width=150
        )
        mode_dropdown.grid(row=0, column=1, sticky="e", padx=(0, 20))

        
    def _setup_results_table(self, parent):
        """Setup the results table with headers and data display.
        
        Args:
            parent: Parent widget
        """
        table_frame = ctk.CTkFrame(parent, fg_color=theme.get('card_bg', '#374151'))
        table_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        table_frame.grid_rowconfigure(1, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Table header with inline actions
        header_row = ctk.CTkFrame(table_frame, fg_color="transparent")
        header_row.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 10))
        header_row.grid_columnconfigure(0, weight=1)

        header_label = ctk.CTkLabel(
            header_row,
            text="Classification Results",
            font=(FONT_FAMILY, 16, "bold"),
            text_color=theme.get('fg', 'white')
        )
        header_label.grid(row=0, column=0, sticky="w")

        # Inline RERUN and EXPORT buttons (initially hidden)
        self.rerun_btn = ctk.CTkButton(
            header_row,
            text="RERUN",
            font=(FONT_FAMILY, 11, "bold"),
            height=28,
            width=80,
            fg_color=theme.get('button_warning', '#FFC107'),
            text_color=theme.get('button_fg', 'white'),
            hover_color=theme.get('button_warning_hover', '#e0a800'),
            command=self._toggle_classification
        )
        self.rerun_btn.grid(row=0, column=1, padx=(10, 0))
        self.rerun_btn.grid_remove()

        self.export_btn = ctk.CTkButton(
            header_row,
            text="EXPORT",
            font=(FONT_FAMILY, 11, "bold"),
            height=28,
            width=80,
            fg_color=theme.get('button_success', '#28A745'),
            text_color=theme.get('button_fg', 'white'),
            hover_color=theme.get('button_success_hover', '#218838'),
            command=self.export_results
        )
        self.export_btn.grid(row=0, column=2, padx=(10, 0))
        self.export_btn.grid_remove()
        
        # Create table container with scrollbars
        table_container = ctk.CTkFrame(table_frame, fg_color="transparent")
        table_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 15))
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)
        
        # Style the treeview for dark theme
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", 
                       background=theme.get('table_bg', '#2d3748'),
                       foreground=theme.get('fg', 'white'),
                       fieldbackground=theme.get('table_bg', '#2d3748'),
                       borderwidth=0)
        style.configure("Treeview.Heading",
                       background=theme.get('header_bg', '#1a202c'),
                       foreground=theme.get('fg', 'white'),
                       borderwidth=1,
                       font=(FONT_FAMILY, 10, "bold"))
          # Create treeview
        columns = ('File', 'Size', 'Modified', 'Classification', 'Confidence', 'Status', 'Contextual Insights')
        self.tree = ttk.Treeview(table_container, columns=columns, show='headings', height=10)
        
        # Configure columns
        col_widths = {'File': 200, 'Size': 80, 'Modified': 120, 'Classification': 150, 'Confidence': 80, 'Status': 100, 'Contextual Insights': 250}
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self._sort_table(c))
            self.tree.column(col, width=col_widths.get(col, 100), minwidth=50)
        
        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(table_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Bind selection events
        self.tree.bind('<<TreeviewSelect>>', self._on_table_select)
        self.tree.bind('<Button-3>', self._on_table_right_click)

    def _update_action_buttons_visibility(self):
        """Show RERUN and EXPORT only if not processing and table has items."""
        has_items = len(self.tree.get_children()) > 0
        if not self.processing and has_items:
            self.rerun_btn.grid()
            self.export_btn.grid()
        else:
            self.rerun_btn.grid_remove()
            self.export_btn.grid_remove()
    
    def update_ui_sync(self, file_result, total_files):
        """Thread-safe UI update for file processing.
        
        Args:
            file_result: Processing result for a single file
            total_files: Total number of files being processed
        """
        def _update():
            try:                # Insert file result into the table
                self.tree.insert('', 'end', values=(
                    file_result.get('FileName', ''),
                    f"{file_result.get('SizeKB', 0)} KB",
                    file_result.get('LastModified', ''),
                    file_result.get('ModelDetermination', ''),
                    file_result.get('ConfidenceScore', ''),
                    file_result.get('Status', 'Unknown'),
                    file_result.get('ContextualInsights', '')
                ))
                
                # Update progress stats
                self._sim_items_processed += 1
                self.progress_text.configure(text=f"{self._sim_items_processed} files processed")
                
                # Show current file name in status
                current_file = file_result.get('FileName', 'Unknown')
                self.status_text.configure(text=f"Processed: {current_file} ({self._sim_items_processed}/{total_files})")
                
                # Update footer statistics
                status = file_result.get('Status')
                if status == 'success':
                    self.success_count += 1
                    self.success_var.set(str(self.success_count))
                elif status == 'skipped':
                    self.skipped_count += 1
                    self.skipped_var.set(str(self.skipped_count))
                else:
                    self.error_count += 1
                    self.error_var.set(str(self.error_count))
                
                self.run_button.configure(state="normal", text="Stop Classification")
                
            except Exception as e:
                print(f"Error updating UI: {e}")
        
        # Schedule UI update on main thread
        self.after(0, _update)

    async def _process_file(self, file_path):
        """Process a single file asynchronously.
        
        Args:
            file_path: Path to the file to process
              Returns:
            Dictionary containing file processing results
        """
        try:
            # Run the blocking file processing in a thread pool
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                # Construct the proper instructions based on the PowerShell version pattern
                instructions = f"""You are "{self.model}" – a highly specialized Washington State Records Classification Assistant 
specializing in government content for Pierce County. Your primary function is to generate a single, precise JSON 
object adhering to the defined schema.

**Output Format:** Produce *only* this JSON object.
```json
{{
  "modelDetermination": "TRANSITORY" | "DESTROY" | "KEEP",
  "confidenceScore": integer (1–100),
  "contextualInsights": string
}}
```

**Core Requirements:**

1.  **Confidence Assessment:** Estimate a confidence score (1-100) for your classification based 
    *exclusively* on the text within the provided file. Justify this score with *direct textual 
    references* to the relevant passages.

2.  **Contextual Justification:** When generating contextual insights, you *must* cite key text 
    snippets directly supporting your classification decision, avoiding interpretive commentary.

3. **JSON Schema Adherence:** Strictly adhere to the defined JSON schema.

4.  **Prioritize Accuracy & Compliance:** Ensure your output directly addresses the legal 
    requirements of WA Schedule 6.

**Instructions:**

*   Analyze up to 500 words from the input file.
*   Identify the most relevant legal classification (e.g., 'KEEP', 'DESTROY', 'TRANSITORY').
*   Assign a confidence score (1-100) justifying your determination.
*   Quote *exactly* one relevant text snippet to support your classification.

**Example:**  '[Quote relevant text]' and '[Quote relevant text]'"""
                
                # Use the imported process_file function from Electronic-Records-Classification with all required parameters
                result = await loop.run_in_executor(
                    executor, 
                    process_file, 
                    str(file_path),  # file_path
                    self.model,      # model
                    instructions,    # instructions
                    0.1,            # temperature (default from CLI version)
                    0  # deprecated max_lines parameter
                )
                
                # Convert result to expected format with all required columns
                file_stats = file_path.stat() if file_path.exists() else None
                file_result = {
                    'FileName': file_path.name,
                    'Extension': file_path.suffix,
                    'FullPath': str(file_path),
                    'LastModified': datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S') if file_stats else 'Unknown',
                    'SizeKB': round(file_stats.st_size / 1024, 2) if file_stats else 0,
                    'ModelDetermination': 'Unknown',
                    'ConfidenceScore': 'N/A',
                    'ContextualInsights': 'No insights available',
                    'Status': 'error'
                }
                if result:
                    file_result.update({
                        'ModelDetermination': result.get('ModelDetermination', 'Unknown'),
                        'ConfidenceScore': result.get('ConfidenceScore', 'N/A'),
                        'ContextualInsights': result.get('ContextualInsights', 'No insights available'),
                        'Status': 'success'
                })
                else:
                    file_result.update({
                        'ModelDetermination': 'Error',
                        'ContextualInsights': 'Processing failed',
                        'Status': 'error'
                })
                    
                return file_result
                
        except Exception as e:
            return {
                'FileName': file_path.name,
                'Extension': file_path.suffix if hasattr(file_path, 'suffix') else '',
                'FullPath': str(file_path),
                'LastModified': 'Unknown',
                'SizeKB': 0,
                'ModelDetermination': 'Error',
                'ConfidenceScore': 'N/A',
                'ContextualInsights': f'Error: {str(e)}',
                'Status': 'error'
            }

    def _stop_classification(self):
        """Stop the classification process gracefully."""
        self.processing = False
        
        if hasattr(self, '_classification_task') and self._classification_task and not self._classification_task.done():
            try:
                self._classification_task.cancel()
                # Give the task a moment to clean up
                def finalize_stop():
                    self.run_button.configure(text="Start Classification")
                    self.status_text.configure(text="Classification stopped")
                    self._update_action_buttons_visibility()
                self.after(100, finalize_stop)  # Delay to allow cleanup
            except Exception as e:
                print(f"Error stopping classification: {e}")
                self.run_button.configure(text="Start Classification")
                self.status_text.configure(text="Classification stopped")
                self._update_action_buttons_visibility()
        else:
            # Update UI immediately if no task to cancel
            self.run_button.configure(text="Start Classification")
            self.status_text.configure(text="Classification stopped")
            self._update_action_buttons_visibility()

    def export_results(self):
        """Export classification results to user's Documents folder with auto-naming."""
        # Determine root folder name
        root_folder = os.path.basename(os.path.normpath(self.input_folder)) or "Records"
        # Date string
        date_str = datetime.now().strftime("%Y%m%d")
        # Documents path
        documents_path = os.path.join(os.path.expanduser("~"), "Documents")
        # Output filename
        filename = f"RecordsClassification_{root_folder}_{date_str}.csv"
        file_path = os.path.join(documents_path, filename)
        
        # Write CSV
        with open(file_path, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["File Name", "Size", "Modified Date", "Classification", "Confidence", "Status"])
            for item in self.tree.get_children():
                writer.writerow(self.tree.item(item, "values"))
        
        # Visual cue: update status bar and transient button state
        self.status_text.configure(text=f"Export complete: {file_path}")
        original_text = self.export_btn.cget('text')
        original_color = theme.get('button_success')
        
        # Change button to indicate success
        self.export_btn.configure(text="Exported", fg_color=theme.get('button_success', '#28A745'))
        
        # Reset after delay
        def _reset_export_button():
            self.export_btn.configure(text=original_text, fg_color=theme.get('button_success', original_color))
            self.status_text.configure(text="Ready")
        
        self.after(3000, _reset_export_button)

    def _on_table_select(self, event):
        """Handle table row selection events.
        
        Args:
            event: Tkinter selection event
        """
        self._update_action_buttons_visibility()
    
    def _on_table_right_click(self, event):
        """Handle right-click events on the table.
        
        Args:
            event: Tkinter right-click event
        """
        self._update_action_buttons_visibility()
        
    def _on_folder_change(self, event=None):
        """Handle folder path changes from entry widget.
        
        Args:
            event: Optional tkinter event
        """
        self.input_folder = self.folder_entry.get()
        self._validate_inputs()
        
    def _browse_folder(self):
        """Browse for input folder and update entry."""
        folder = filedialog.askdirectory(title="Select folder containing files to classify")
        if folder:
            self.input_folder = folder
            self.folder_entry.delete(0, 'end')
            self.folder_entry.insert(0, folder)
            self._validate_inputs()

    def _toggle_classification(self):
        """Toggle between starting and stopping classification."""
        if not self._toggle_lock.acquire(blocking=False):
            return
        
        try:
            if self.processing:
                self._stop_classification() 
            else:
                # Ensure button remains enabled during processing
                self.run_button.configure(state="normal", text="Stop Classification")
                
                if self.mode_var.get() == "Last Modified":
                    self._last_modified_classification()
                else:
                    self._start_classification()
        finally:
            self._toggle_lock.release()

    def _setup_status_bar(self, parent):
        """Create a modern status bar with real-time statistics and progress.
        
        Args:
            parent: Parent widget
        """
        status_bar = ctk.CTkFrame(parent, fg_color=theme.get('statusbar_bg', '#0f1724'), height=theme.get('statusbar_height', 32))
        status_bar.grid(row=3, column=0, sticky="ew", padx=0, pady=(0, 0))
        
        # Configure columns for status, progress, and stats
        for i in range(8):
            status_bar.grid_columnconfigure(i, weight=1 if i == 0 else 0)
        status_bar.grid_propagate(False)

        # Status text (left)
        self.status_text = ctk.CTkLabel(
            status_bar,
            text="Ready",
            text_color=theme.get('statusbar_fg', '#e8f4fd'),
            font=(FONT_FAMILY, 11)
        )
        self.status_text.grid(row=0, column=0, sticky="w", padx=10)

        # Progress text
        self.progress_text = ctk.CTkLabel(
            status_bar,
            text="",
            text_color=theme.get('statusbar_fg', '#e8f4fd'),
            font=(FONT_FAMILY, 11)
        )
        self.progress_text.grid(row=0, column=1, sticky="w", padx=10)

        # Success count
        ctk.CTkLabel(status_bar, text="Success:", text_color=theme.get('subtle_fg', '#7dd3fc'), font=(FONT_FAMILY, 11)).grid(row=0, column=2, sticky="e")
        ctk.CTkLabel(status_bar, textvariable=self.success_var, text_color=theme.get('success', '#28A745'), font=(FONT_FAMILY, 11, 'bold')).grid(row=0, column=3, sticky="w", padx=(2,10))
        
        # Skipped count
        ctk.CTkLabel(status_bar, text="Skipped:", text_color=theme.get('subtle_fg', '#7dd3fc'), font=(FONT_FAMILY, 11)).grid(row=0, column=4, sticky="e")
        ctk.CTkLabel(status_bar, textvariable=self.skipped_var, text_color=theme.get('warning', '#FFC107'), font=(FONT_FAMILY, 11, 'bold')).grid(row=0, column=5, sticky="w", padx=(2,10))
        
        # Error count
        ctk.CTkLabel(status_bar, text="Error:", text_color=theme.get('subtle_fg', '#7dd3fc'), font=(FONT_FAMILY, 11)).grid(row=0, column=6, sticky="e")
        ctk.CTkLabel(status_bar, textvariable=self.error_var, text_color=theme.get('error', '#DC3545'), font=(FONT_FAMILY, 11, 'bold')).grid(row=0, column=7, sticky="w", padx=(2,10))

        self._status_bar = status_bar

    def _setup_keyboard_shortcuts(self):
        """Bind keyboard shortcuts for accessibility and productivity."""
        toplevel = self.winfo_toplevel()
        toplevel.bind('<Control-o>', lambda e: self._browse_folder())
        toplevel.bind('<Control-r>', lambda e: self._toggle_classification())

    async def classify_files(self):
        """Classify files asynchronously with real-time updates."""
        files_to_process = []
        
        try:
            self._sim_items_processed = 0  # Reset counter
            folder = Path(self.input_folder)
            
            # Update initial status
            def update_initial_status():
                self.status_text.configure(text="Enumerating files...")
            self.after(0, update_initial_status)
            
            # Collect all files first to get accurate count
            async for file in self.enumerate_files(folder):
                if not self.processing:  # Check if stopped
                    return
                files_to_process.append(file)

            if files_to_process and self.processing:
                # Update status with file count
                total_count = len(files_to_process)
                def update_count_status():
                    self.status_text.configure(text=f"Found {total_count} files. Starting classification...")
                self.after(0, update_count_status)
                
                await self.process_files_in_chunks(files_to_process)

            if self.processing:  # Only update if not stopped
                self.processing = False
                def update_complete_status():
                    self.run_button.configure(state="normal", text="Start Classification")
                    self.status_text.configure(text="Classification complete")
                    self._update_action_buttons_visibility()
                self.after(0, update_complete_status)
                
        except asyncio.CancelledError:
            def update_cancelled_status():
                self.processing = False
                self.run_button.configure(state="normal", text="Start Classification")
                self.status_text.configure(text="Classification cancelled")
                self._update_action_buttons_visibility()
            self.after(0, update_cancelled_status)
            raise  # Re-raise to properly handle cancellation
        except Exception as e:
            def update_error_status():
                self.processing = False
                self.run_button.configure(state="normal", text="Start Classification")
                self.status_text.configure(text=f"Classification error: {str(e)}")
                self._update_action_buttons_visibility()
            self.after(0, update_error_status)
        finally:
            # Ensure processing flag is reset
            self.processing = False
            self._update_action_buttons_visibility()

    async def enumerate_files(self, folder):
        """Enumerate files in folder with async yield.
        
        Args:
            folder: Path object to enumerate
            
        Yields:
            File paths found in the folder
        """
        try:
            for file in folder.rglob('*'):
                if not self.processing:
                    return  # Use return instead of break for proper generator cleanup
                if file.is_file():  # Only yield actual files
                    yield file
                    await asyncio.sleep(0.001)  # Yield control
        except asyncio.CancelledError:
            # Handle cancellation gracefully
            return
        except Exception as e:
            print(f"Error during file enumeration: {e}")
            return

    async def process_files_in_chunks(self, files_to_process, chunk_size=10):
        """Process files in chunks to provide real-time feedback and manage memory.
        
        Args:
            files_to_process: List of file paths to process
            chunk_size: Number of files to process in each chunk
        """
        total_files = len(files_to_process)
        processed_count = 0
        
        try:
            # Process files in chunks
            for i in range(0, len(files_to_process), chunk_size):
                if not self.processing:
                    break
                    
                chunk = files_to_process[i:i + chunk_size]
                
                # Process each file in the current chunk
                for file_path in chunk:
                    if not self.processing:
                        break
                        
                    try:
                        # Process the file using the existing _process_file method
                        file_result = await self._process_file(file_path)
                        
                        # Update UI with the result
                        self.update_ui_sync(file_result, total_files)
                        processed_count += 1
                        
                        # Update status with real-time progress
                        current_file_name = file_path.name
                        current_count = processed_count
                        
                        def update_status_text():
                            self.status_text.configure(
                                text=f"Processing: {current_file_name} ({current_count}/{total_files})"
                            )
                        self.after(0, update_status_text)
                        
                        # Small delay to yield control and allow UI updates
                        await asyncio.sleep(0.01)
                        
                    except Exception as e:
                        # Create error result for failed file
                        error_result = {
                            'FileName': file_path.name if hasattr(file_path, 'name') else str(file_path),
                            'Extension': file_path.suffix if hasattr(file_path, 'suffix') else '',
                            'FullPath': str(file_path),
                            'LastModified': 'Unknown',
                            'SizeKB': 0,
                            'ModelDetermination': 'ERROR',
                            'ConfidenceScore': '0',
                            'ContextualInsights': f'Processing error: {str(e)}',
                            'Status': 'error'
                        }
                        self.update_ui_sync(error_result, total_files)
                        processed_count += 1
                
                # Brief pause between chunks to allow UI responsiveness
                await asyncio.sleep(0.05)
                
        except Exception as e:
            error_message = f"Error during processing: {e}"
            def update_error_status():
                self.status_text.configure(text=error_message)
            self.after(0, update_error_status)
        finally:
            # Update final status
            final_count = processed_count
            def update_final_status():
                self.status_text.configure(text=f"Processing complete: {final_count} files processed")
            self.after(0, update_final_status)

    def _start_classification(self):
        """Start the classification process using asyncio for non-blocking operations."""
        try:
            if not self.input_folder or not os.path.exists(self.input_folder):
                messagebox.showerror("Error", "Please select a valid input folder.")
                return

            # Cancel any existing task
            if hasattr(self, '_classification_task') and self._classification_task and not self._classification_task.done():
                self._classification_task.cancel()

            self.processing = True
            self.run_button.configure(text="Stop Classification")
            self.status_text.configure(text="Classification starting...")
            self.progress_text.configure(text="0 files processed")
            self.tree.delete(*self.tree.get_children())  # Clear previous results
            
            # Reset counters
            self.success_count = 0
            self.skipped_count = 0
            self.error_count = 0
            self.success_var.set('0')
            self.skipped_var.set('0')
            self.error_var.set('0')
            self._sim_items_processed = 0
            
            self._update_action_buttons_visibility()

            # Create and start the classification task
            loop = asyncio.get_event_loop()
            self._classification_task = loop.create_task(self.classify_files())
            
            # Add callback to handle task completion
            def on_task_complete(task):
                try:
                    if not task.cancelled():
                        task.result()  # Get result to trigger any exceptions
                except asyncio.CancelledError:
                    pass  # Expected when cancelled
                except Exception as e:
                    def show_error():
                        self.status_text.configure(text=f"Classification error: {str(e)}")
                        self.processing = False
                        self.run_button.configure(text="Start Classification")
                        self._update_action_buttons_visibility()
                    self.after(0, show_error)
            
            self._classification_task.add_done_callback(on_task_complete)
            
        except Exception as e:
            self.processing = False
            self.run_button.configure(text="Start Classification")
            self.status_text.configure(text=f"Error starting classification: {str(e)}")
            self._update_action_buttons_visibility()
    
    def _validate_inputs(self):
        """Validate the input folder and other required parameters."""
        # Basic validation - can be extended as needed
        pass
    def _last_modified_classification(self):
        """Handle classification based on last modified date with real-time UI updates."""
        if not self.input_folder or not os.path.exists(self.input_folder):
            self.status_text.configure(text="Please select a valid input folder")
            return
            
        # Use the same logic as _start_classification for consistency
        self._start_classification()

    def _sort_table(self, column):
        """Sort table by the specified column.
        
        Args:
            column: Column name to sort by
        """
        # Toggle sort direction
        reverse = not self.sort_reverse.get(column, False)
        self.sort_reverse[column] = reverse
        
        # Get all items and sort them
        items = [(self.tree.set(child, column), child) for child in self.tree.get_children()]
        items.sort(reverse=reverse)
        
        # Rearrange items in sorted positions
        for index, (val, child) in enumerate(items):
            self.tree.move(child, '', index)
