"""
gui.ui_components - Modular UI component builders for Records Classifier GUI
Moved under gui/ for modular architecture. All imports updated to new structure.
"""

from pathlib import Path
import logging
import tkinter as tk

try:
    import customtkinter as ctk
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logging.error(
        "customtkinter module not found. Please install it with: pip install customtkinter"
    )
    # Fallback to standard tkinter with similar interface
    import tkinter as tk

    class FallbackCTk:
        def __getattr__(self, name):
            if name in [
                "CTkFrame",
                "CTkLabel",
                "CTkEntry",
                "CTkButton",
                "CTkScrollbar",
            ]:
                # Return tkinter equivalent functions
                return getattr(tk, name.replace("CTk", ""))
            raise AttributeError(f"{name} is not implemented in fallback mode")

    ctk = FallbackCTk()
try:
    from PIL import Image
except ImportError:
    logging.warning("PIL module not found. Image loading will be disabled.")
    Image = None

import importlib.util
import sys
import os


def _import_local(name):
    here = os.path.dirname(__file__)
    file_path = os.path.join(here, f"{name}.py")
    spec = importlib.util.spec_from_file_location(name, file_path)
    if not spec:
        raise ImportError(f"Could not find module {name} at {file_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    if not spec.loader:
        raise ImportError(f"Module loader not found for {name}")
    spec.loader.exec_module(mod)
    return mod


theme_mod = _import_local("theme")
tooltip_mod = _import_local("tooltip")
utils_mod = _import_local("utils")

theme = theme_mod.theme
FONT_FAMILY = theme_mod.FONT_FAMILY
PADDING = theme_mod.PADDING
SPACING = theme_mod.SPACING
ToolTip = tooltip_mod.ToolTip
hover_effect = utils_mod.hover_effect


def build_header(parent):
    """Build the application header with logo and title.

    Improved with:
    - Better logo path resolution with multiple fallbacks
    - Enhanced error handling for image loading
    - Graceful degradation when resources are unavailable
    """
    frame = ctk.CTkFrame(
        parent, corner_radius=theme["radius"], fg_color=theme["header_bg"]
    )
    frame.grid(
        row=0,
        column=0,
        columnspan=4,
        sticky="ew",
        padx=PADDING + 8,
        pady=(PADDING + 6, SPACING + 6),
    )
    frame.grid_columnconfigure(1, weight=1)

    # Try multiple paths to find the logo with robust error handling
    logo_found = False
    logo_paths = [
        Path(__file__).parent / "PC_Logo_Round_white.png",  # Local to ui_components
        Path(__file__).parent.parent / "PC_Logo_Round_white.png",  # Parent directory
        Path(__file__).resolve().parent / "PC_Logo_Round_white.png",  # Absolute path
        Path.cwd() / "PC_Logo_Round_white.png",  # Working directory
    ]

    if Image:  # Only attempt to load image if PIL is available
        for logo_path in logo_paths:
            try:
                if logo_path.exists():
                    img = Image.open(logo_path).resize((48, 48))
                    ctk_img = ctk.CTkImage(
                        light_image=img, dark_image=img, size=(48, 48)
                    )
                    lbl = ctk.CTkLabel(
                        frame, image=ctk_img, text="", bg_color=theme["header_bg"]
                    )
                    # Store reference to prevent garbage collection
                    try:
                        # Changed from lbl.image to lbl._image to avoid conflicts with CTkLabel's image attribute
                        lbl._image = ctk_img
                    except:
                        # Create a backup reference to prevent garbage collection
                        if not hasattr(frame, "_image_refs"):
                            setattr(frame, "_image_refs", [])
                        getattr(frame, "_image_refs").append(ctk_img)
                    lbl.grid(
                        row=0, column=0, padx=(PADDING + 6, SPACING + 6), rowspan=2
                    )
                    logo_found = True
                    break
            except Exception as e:
                logging.warning("Failed to load logo from %s: %s", logo_path, e)
                continue

    # Fallback to emoji if no logo could be loaded
    if not logo_found:
        lbl = ctk.CTkLabel(
            frame, text="🗂️", font=(FONT_FAMILY, 32), bg_color=theme["header_bg"]
        )
        lbl.grid(row=0, column=0, padx=(PADDING + 6, SPACING + 6), rowspan=2)

    # Main header text
    title = ctk.CTkLabel(
        frame,
        text="Pierce County Electronic Records Classifier",
        font=(FONT_FAMILY, 22, "bold"),
        text_color=theme["fg"],
    )
    title.grid(row=0, column=1, sticky="w", pady=(0, 2))

    # Version with fallback to determine version from current date if needed
    try:
        # Try to get version from a version file if it exists
        version_file = Path(__file__).parent / "version.txt"
        if version_file.exists():
            version_text = version_file.read_text().strip()
        else:
            # Fallback to hardcoded version
            version_text = "v0.1.0"
    except Exception:
        # Further fallback using date-based versioning
        import datetime

        today = datetime.date.today()
        version_text = f"v{today.year}.{today.month}"

    version = ctk.CTkLabel(
        frame,
        text=version_text,
        font=(FONT_FAMILY, 12),
        text_color=theme["fg"],
        anchor="w",
    )
    version.grid(row=1, column=1, sticky="w", pady=(0, 2))

    return frame


def build_trust_panel(parent, show_how):
    frame = ctk.CTkFrame(
        parent, corner_radius=theme["radius"], fg_color=theme["panel_bg"]
    )
    # Ensure the frame spans the full width
    frame.grid(
        row=1,
        column=0,
        columnspan=4,
        sticky="ew",
        padx=(PADDING + 8, PADDING + 8),
        pady=(SPACING, SPACING),
    )
    frame.grid_columnconfigure(0, weight=1)
    lbl = ctk.CTkLabel(
        frame,
        text="🔒 Data never leaves your device or communicates outside of the Pierce County network. All LLM analysis is done offline and locally on your computer.",
        font=theme["font"],
        text_color=theme["accent"],
        wraplength=1200,
        anchor="w",
        justify="left",
    )
    lbl.grid(row=0, column=0, padx=(PADDING, SPACING), sticky="ew")
    link = ctk.CTkLabel(
        frame,
        text="[How it works]",
        font=(FONT_FAMILY, 11, "underline"),
        text_color=theme["fg"],
        cursor="hand2",
    )
    link.grid(row=0, column=1, sticky="e", padx=(0, PADDING))
    link.bind("<Button-1>", lambda _: show_how())
    frame.grid_columnconfigure(1, weight=0)
    return frame


def build_folder_selector(parent, folder_var, browse_cmd):
    """Build the folder selection UI components with improved validation.

    Args:
        parent: Parent widget
        folder_var: StringVar to bind the folder path
        browse_cmd: Callback function for the browse button

    Returns:
        Tuple of (entry widget, browse button)
    """
    # Create label
    lbl = ctk.CTkLabel(parent, text="Folder to analyze:", font=theme["font"])
    lbl.grid(row=2, column=0, sticky="e", padx=SPACING, pady=SPACING)

    # Create entry with validation
    entry = ctk.CTkEntry(
        parent,
        textvariable=folder_var,
        placeholder_text="Select folder…",
        width=500,
        corner_radius=theme["radius"],
        fg_color=theme["entry_bg"],
        text_color=theme["entry_fg"],
    )
    entry.grid(row=2, column=1, columnspan=2, sticky="ew", padx=SPACING)

    # Add validation callback for real-time folder validation
    def validate_folder_path(*args):
        path = folder_var.get().strip()
        if path:
            try:
                folder_path = Path(path)
                if not folder_path.exists():
                    entry.configure(border_color=theme["error"])
                    ToolTip(entry, "Folder does not exist")
                elif not folder_path.is_dir():
                    entry.configure(border_color=theme["error"])
                    ToolTip(entry, "Not a folder")
                else:
                    entry.configure(border_color=theme["success"])
                    ToolTip(entry, "Valid folder selected")
            except Exception:
                entry.configure(border_color=theme["error"])
                ToolTip(entry, "Invalid path")
        else:
            entry.configure(border_color="")  # Reset to default
            ToolTip(entry, "Select a folder containing files to classify")

    # Connect validation to the StringVar
    folder_var.trace("w", validate_folder_path)

    # Create browse button
    btn = ctk.CTkButton(
        parent,
        text="Browse...",
        command=browse_cmd,
        corner_radius=theme["radius"],
        fg_color=theme["button_bg"],
        text_color=theme["button_fg"],
        hover_color=theme["button_hover"],
    )
    btn.grid(row=2, column=3, padx=SPACING, pady=SPACING)

    return entry, btn


def build_output_selector(parent, output_var, browse_cmd):
    """Build the output file selection UI components with improved validation.

    Args:
        parent: Parent widget
        output_var: StringVar to bind the output file path
        browse_cmd: Callback function for the browse button

    Returns:
        Tuple of (entry widget, browse button)
    """
    # Create label
    lbl = ctk.CTkLabel(parent, text="Output file:", font=theme["font"])
    lbl.grid(row=3, column=0, sticky="e", padx=SPACING, pady=SPACING)

    # Create entry with validation
    entry = ctk.CTkEntry(
        parent,
        textvariable=output_var,
        placeholder_text="Select output file location…",
        width=500,
        corner_radius=theme["radius"],
        fg_color=theme["entry_bg"],
        text_color=theme["entry_fg"],
    )
    entry.grid(row=3, column=1, columnspan=2, sticky="ew", padx=SPACING)

    # Add validation callback for real-time output path validation
    def validate_output_path(*args):
        path = output_var.get().strip()
        if path:
            try:
                output_path = Path(path)
                output_dir = output_path.parent

                if not output_dir.exists():
                    entry.configure(border_color=theme["warning"])
                    ToolTip(entry, "Directory does not exist, will be created")
                else:
                    # Check if we can write to the directory
                    if os.access(output_dir, os.W_OK):
                        entry.configure(border_color=theme["success"])
                        ToolTip(entry, "Valid output location")
                    else:
                        entry.configure(border_color=theme["error"])
                        ToolTip(entry, "Cannot write to this location")
            except Exception:
                entry.configure(border_color=theme["error"])
                ToolTip(entry, "Invalid path")
        else:
            entry.configure(border_color="")  # Reset to default
            ToolTip(entry, "Select where to save the results (CSV file)")

    # Connect validation to the StringVar
    output_var.trace("w", validate_output_path)

    # Create browse button
    btn = ctk.CTkButton(
        parent,
        text="Browse...",
        command=browse_cmd,
        corner_radius=theme["radius"],
        fg_color=theme["button_bg"],
        text_color=theme["button_fg"],
        hover_color=theme["button_hover"],
    )
    btn.grid(row=3, column=3, padx=SPACING, pady=SPACING)

    return entry, btn


def build_model_controls(parent, model_var):
    """Build controls for selecting the LLM model.

    Args:
        parent: Parent widget
        model_var: StringVar to bind the selected model

    Returns:
        Frame containing the model selection controls
    """
    # Create container frame
    frame = ctk.CTkFrame(parent, fg_color="transparent")

    # Create label
    label = ctk.CTkLabel(
        frame, text="Model:", font=theme["font"], text_color=theme["fg"]
    )
    label.pack(side="left", padx=(0, 5))

    # Create dropdown/combobox
    # Use CTkComboBox if available, otherwise use ttk.Combobox
    try:
        model_dropdown = ctk.CTkComboBox(
            frame,
            values=[
                "pierce-county-records-classifier-phi2",
                "pierce-county-records-classifier-gemma3",
            ],
            variable=model_var,
            width=280,
            border_color=theme["accent"],
            button_color=theme["accent"],
            button_hover_color=theme["accent_hover"],
            dropdown_fg_color=theme["bg"],
            dropdown_hover_color=theme["hover_bg"],
        )
    except AttributeError:
        # Fallback if CTkComboBox is not available
        model_dropdown = tk.ttk.Combobox(
            frame,
            values=[
                "pierce-county-records-classifier-phi2",
                "pierce-county-records-classifier-gemma3",
            ],
            textvariable=model_var,
            width=25,
        )

    model_dropdown.pack(side="left", padx=5)

    # Add tooltip
    ToolTip(frame, "Select the model to use for classification")

    return frame


def build_search_bar(parent, search_var):
    """Build a search bar for filtering the data table.

    Args:
        parent: Parent widget
        search_var: StringVar for the search text

    Returns:
        The created search entry widget
    """
    # Create search entry
    entry = ctk.CTkEntry(
        parent,
        textvariable=search_var,
        font=(FONT_FAMILY, 13),
        width=320,
        corner_radius=theme["radius"],
        fg_color=theme["search_bg"],
        text_color=theme["search_fg"],
        placeholder_text="🔍 Search records by name, type, or result...",
    )

    # Add clear button functionality
    def on_focus_in(event):
        if entry.get() == "🔍 Search...":
            entry.delete(0, tk.END)

    def on_focus_out(event):
        if not entry.get():
            entry.insert(0, "🔍 Search...")

    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)

    # Add tooltip
    ToolTip(entry, "Search for files by name, type, or classification result")

    return entry


def build_table(parent, on_sort):
    """Build the data table for displaying file classifications.

    Args:
        parent: Parent widget
        on_sort: Callback function for column header clicks

    Returns:
        Frame containing the Treeview widget
    """
    import tkinter.ttk as ttk

    frame = ctk.CTkFrame(
        parent,
        fg_color=theme["panel_bg"],
        corner_radius=theme["radius"],
        border_width=0,
    )
    frame.grid_propagate(False)

    # Column definitions
    cols = [
        "FileName",
        "Extension",
        "FullPath",
        "LastModified",
        "SizeKB",
        "ModelDetermination",
        "ConfidenceScore",
        "ContextualInsights",
    ]

    # TTK Style Configuration with error handling
    style = ttk.Style()

    # Try the preferred theme first, fall back to default if not available
    try:
        style.theme_use("clam")  # use clam theme for full styling support
    except tk.TclError:
        logging.warning("'clam' theme not available, using default theme")
        # No need to explicitly set theme, will use default

    # Configure the basic treeview style with error handling for each property
    style_props = {
        "background": theme["panel_bg"],
        "fieldbackground": theme["panel_bg"],
        "foreground": theme["fg"],
        "borderwidth": 0,
        "highlightthickness": 0,
        "rowheight": 30,
        "font": theme["font"],
        "relief": "flat",
    }

    # Apply style properties individually so one failure doesn't affect others
    for prop, value in style_props.items():
        try:
            style.configure("Treeview", **{prop: value})
        except tk.TclError as e:
            logging.warning("Could not configure Treeview %s: %s", prop, e)

    # Configure the heading style
    heading_props = {
        "background": theme["accent"],
        "foreground": "white",
        "font": (FONT_FAMILY, 13, "bold"),
        "borderwidth": 0,
        "relief": "flat",
        "padding": (8, 4, 8, 4),
    }

    for prop, value in heading_props.items():
        try:
            style.configure("Treeview.Heading", **{prop: value})
        except tk.TclError as e:
            logging.warning("Could not configure Treeview.Heading %s: %s", prop, e)

    # Configure style maps
    try:
        style.map("Treeview.Heading", background=[("active", theme["accent_hover"])])
    except tk.TclError as e:
        logging.warning("Could not map Treeview.Heading background: %s", e)

    try:
        style.map("Treeview", background=[("selected", theme["accent_hover"])])
    except tk.TclError as e:
        logging.warning("Could not map Treeview background: %s", e)

    # Configure alternating row styles
    try:
        style.configure("OddRow", background=theme["panel_bg"])
        style.configure("EvenRow", background=theme["table_alt"])
    except tk.TclError as e:
        logging.warning("Could not configure alternating row styles: %s", e)

    # Remove the borders if possible
    try:
        style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
    except tk.TclError as e:
        logging.warning("Could not modify Treeview layout: %s", e)

    # Create the treeview
    try:
        tree = ttk.Treeview(
            frame, columns=cols, show="headings", selectmode="browse", style="Treeview"
        )
    except tk.TclError:
        # Fallback without style if it failed
        tree = ttk.Treeview(frame, columns=cols, show="headings", selectmode="browse")

    # Configure row tagging for alternating colors
    try:
        tree.tag_configure("oddrow", background=theme["panel_bg"])
        tree.tag_configure("evenrow", background=theme["table_alt"])

        # Store the original insert method
        orig_insert = tree.insert

        # Define a new insert method that adds alternating row tags
        def insert_with_tags(parent, index, **kwargs):
            try:
                count = len(tree.get_children())
                tag = "evenrow" if count % 2 == 0 else "oddrow"
                tags = kwargs.get("tags", ())
                kwargs["tags"] = (*tags, tag)
                return orig_insert(parent, index, **kwargs)
            except Exception as e:
                logging.warning("Error in custom insert method: %s", e)
                # Fall back to original insert if our custom logic fails
                return orig_insert(parent, index, **kwargs)

        # Instead of replacing the method, we'll create a utility function
        # that will be accessible via the frame
        def insert_row(parent, index, **kwargs):
            return insert_with_tags(parent, index, **kwargs)

        try:
            setattr(frame, "insert_row", insert_row)
        except Exception as e:
            logging.warning("Could not set insert_row attribute: %s", e)
    except Exception as e:
        logging.warning("Could not configure row tagging: %s", e)

    # Configure tooltips for column headers
    col_tooltips = {
        "FileName": "Original file name",
        "Extension": "File extension/type",
        "FullPath": "Full file path",
        "LastModified": "Last modified date",
        "SizeKB": "File size (KB)",
        "ModelDetermination": "LLM classification",
        "ConfidenceScore": "Model confidence (0-100)",
        "ContextualInsights": "Extra context from LLM",
    }

    # Set up column headings with sort commands and reasonable defaults
    for c in cols:
        tree.heading(c, text=c, command=lambda _c=c: on_sort(_c))

        # Use different default widths based on column type
        if c == "FileName":
            width = 180
        elif c == "Extension":
            width = 80
        elif c == "FullPath":
            width = 300
        elif c == "ContextualInsights":
            width = 300
        elif c == "ConfidenceScore":
            width = 80
        else:
            width = 120

        tree.column(c, width=width, anchor="w", minwidth=80, stretch=True)

    # Create scrollbars with error handling
    try:
        vsb = ctk.CTkScrollbar(frame, orientation="vertical", command=tree.yview)
    except Exception as e:
        logging.warning("Could not create vertical scrollbar: %s", e)
        # Fallback to standard Tkinter scrollbar
        vsb = tk.Scrollbar(frame, orient="vertical", command=tree.yview)

    try:
        hsb = ctk.CTkScrollbar(frame, orientation="horizontal", command=tree.xview)
    except Exception as e:
        logging.warning("Could not create horizontal scrollbar: %s", e)
        # Fallback to standard Tkinter scrollbar
        hsb = tk.Scrollbar(frame, orient="horizontal", command=tree.xview)

    # Configure the scrollbar connections
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    # Layout using grid for proper resizing
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    tree.grid(row=0, column=0, sticky="nswe", padx=6, pady=6)
    vsb.grid(row=0, column=1, sticky="ns", pady=6)
    hsb.grid(row=1, column=0, sticky="ew", padx=6)

    # Performance optimization for large datasets
    tree["displaycolumns"] = [
        "FileName",
        "Extension",
        "LastModified",
        "SizeKB",
        "ModelDetermination",
        "ConfidenceScore",
    ]
    # Attach the tree widget to the frame for access in the main app
    try:
        # Use a safer way to store attributes on the frame
        setattr(frame, "tree", tree)

        # Store the original column configuration for view switching
        setattr(frame, "all_columns", cols)
        setattr(
            frame,
            "default_columns",
            [
                "FileName",
                "Extension",
                "LastModified",
                "SizeKB",
                "ModelDetermination",
                "ConfidenceScore",
            ],
        )
        setattr(frame, "detailed_columns", cols)
    except Exception as e:
        logging.warning("Could not set frame attributes: %s", e)

    # Add method to switch between simple and detailed views
    def toggle_detail_view(show_details=None):
        """Toggle between simple and detailed table views"""
        try:
            default_cols = getattr(
                frame,
                "default_columns",
                [
                    "FileName",
                    "Extension",
                    "LastModified",
                    "SizeKB",
                    "ModelDetermination",
                    "ConfidenceScore",
                ],
            )
            detailed_cols = getattr(frame, "detailed_columns", cols)

            if show_details is None:
                # If current view is default, switch to detailed
                show_details = tree["displaycolumns"] == default_cols

            if show_details:
                tree["displaycolumns"] = detailed_cols
            else:
                tree["displaycolumns"] = default_cols
        except Exception as e:
            logging.warning("Could not toggle detail view: %s", e)

    # Attach the method to the frame
    try:
        setattr(frame, "toggle_detail_view", toggle_detail_view)
    except Exception as e:
        logging.warning("Could not set toggle_detail_view attribute: %s", e)

    return frame


def build_run_button(parent, run_cmd):
    """Build a large, prominent run button for starting the classification.

    Args:
        parent: Parent widget
        run_cmd: Callback function for when the button is clicked

    Returns:
        The created button widget
    """
    btn = ctk.CTkButton(
        parent,
        text="Run Classification",
        command=run_cmd,
        corner_radius=theme["radius"],
        fg_color=theme["accent"],
        text_color="white",
        hover_color=theme["accent_hover"],
        height=40,
        font=(FONT_FAMILY, 14, "bold"),
    )
    # Add hover effect
    hover_effect(btn, theme["accent_hover"], theme["accent"])

    return btn


def build_stats_bar(parent, stats_vars):
    """Build the statistics bar for the bottom of the application.

    Args:
        parent: Parent widget
        stats_vars: List of StringVar instances for showing statistics

    Returns:
        The created frame containing the statistics widgets
    """
    # Create frame with dark background
    frame = ctk.CTkFrame(parent, fg_color=theme["panel_bg"], corner_radius=0, height=30)

    # Set up statistics labels and values
    labels = ["Total:", "Processed:", "Skipped:", "Errors:", "Speed:", "Time:"]

    # Ensure we have enough variables
    while len(stats_vars) < len(labels):
        stats_vars.append(tk.StringVar(value="0"))

    # Create and position stats widgets
    for i, (label_text, var) in enumerate(zip(labels, stats_vars)):
        # Even columns for labels, odd columns for values
        col_label = i * 2
        col_value = i * 2 + 1

        # Create label with light text
        label = ctk.CTkLabel(
            frame,
            text=label_text,
            font=theme["font"],
            text_color=theme["subtle_fg"],
            anchor="e",
        )
        label.grid(row=0, column=col_label, padx=(10 if i == 0 else 5, 0), sticky="e")

        # Create value with brighter text
        value = ctk.CTkLabel(
            frame,
            textvariable=stats_vars[i],
            font=theme["font"],
            text_color=theme["fg"],
            anchor="w",
        )
        value.grid(row=0, column=col_value, padx=(0, 15), sticky="w")

    return frame


def build_parallel_slider(parent, var, max_jobs):
    """Build a slider for controlling parallel job count."""
    frame = ctk.CTkFrame(parent, fg_color="transparent")

    label = ctk.CTkLabel(
        frame, text="Parallel Jobs:", font=theme["font"], text_color=theme["fg"]
    )
    label.pack(side="left", padx=(0, 8))

    slider = ctk.CTkSlider(
        frame,
        from_=1,
        to=max_jobs,
        number_of_steps=max_jobs - 1,
        variable=var,
        width=150,
        height=16,
        fg_color=theme["panel_bg"],
        progress_color=theme["accent"],
        button_color=theme["accent"],
        button_hover_color=theme["accent_hover"],
    )
    slider.pack(side="left", padx=(0, 4))

    value_label = ctk.CTkLabel(
        frame, textvariable=var, font=theme["font"], text_color=theme["fg"], width=30
    )
    value_label.pack(side="left")

    return frame
