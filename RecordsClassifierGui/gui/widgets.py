"""
widgets.py - Hardened, enterprise-grade custom widgets and UI components
for Records Classifier GUI using local LLM integration (Ollama) and production-grade practices.
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from PIL import Image, ImageTk
from pathlib import Path
import time
from typing import Callable, Optional, Any, Tuple, Dict, List
from .theme import theme, FONT_FAMILY  # Add FONT_FAMILY import

#################################################################################
# INTERNAL SAFE PARTITION: Enterprise LLM-ops and UI Robustness – Primary Author #
#################################################################################

def validate_theme(theme_dict: dict, required_keys: List[str]) -> None:
    """Runtime validation to guarantee theme dict integrity."""
    missing = [k for k in required_keys if k not in theme_dict]
    if missing:
        raise KeyError(f"Theme dictionary missing required keys: {missing}")

def get_resource_path(relative_path: str) -> Path:
    """Obtain absolute path for local resources, compatible in PyInstaller contexts."""
    import sys, os
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return Path(base_path) / relative_path

class ToolTip:
    """Create a tooltip for a given widget with improved lifecycle handling."""
    def __init__(self, widget: tk.Widget, text: str):
        self.widget = widget
        self.text = text
        self.tooltip: Optional[tk.Toplevel] = None
        self.widget.bind('<Enter>', self.enter, add='+')
        self.widget.bind('<Leave>', self.leave, add='+')
        self.widget.bind('<ButtonPress>', self.leave, add='+')  # Dismiss on click as well

    def enter(self, event=None) -> None:
        if self.tooltip:
            # Already open, don't open another
            return
        # Defensive: widget must be mapped (visible) to get bbox
        try:
            x, y, _, _ = self.widget.bbox("insert")
        except Exception:
            x = y = 0
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.tooltip, 
            text=self.text, 
            justify='left',
            background=theme['tooltip_bg'],
            foreground=theme['tooltip_fg'],
            relief='solid', 
            borderwidth=1,
            padx=5,
            pady=2
        )
        label.pack()

    def leave(self, event=None) -> None:
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

class CompletionPanel(ctk.CTkFrame):
    """Panel showing completion status and statistics."""
    def __init__(
        self,
        parent: tk.Widget,
        stats_vars: List[tk.StringVar],
        theme_dict: Dict[str, Any],
        font_family: str,
    ):
        validate_theme(theme_dict, ['panel_bg', 'completion_label_fg', 'stat_value_fg'])
        super().__init__(parent, fg_color=theme_dict['panel_bg'])
        self.stats_vars = stats_vars
        self.theme = theme_dict
        self.font_family = font_family
        self._widgets = []
        self._create_widgets()
        
    def _create_widgets(self) -> None:
        titles = ["Total Files", "Classified", "Unclassified", "Error Count"]
        for i, (label_txt, var) in enumerate(zip(titles, self.stats_vars)):
            label = ctk.CTkLabel(
                self, text=label_txt,
                font=(self.font_family, 12, "bold"),
                text_color=self.theme.get('completion_label_fg', "#000")
            )
            value = ctk.CTkLabel(
                self, textvariable=var,
                font=(self.font_family, 12),
                text_color=self.theme.get('stat_value_fg', "#008800")
            )
            label.grid(row=i, column=0, sticky="w", padx=10, pady=(7 if i==0 else 2,2))
            value.grid(row=i, column=1, sticky="e", padx=10)
            self._widgets.append((label, value))

def build_run_button(parent: tk.Widget, command: Callable) -> ctk.CTkButton:
    """Create the main run/process button."""
    validate_theme(theme, ['button_bg', 'button_hover', 'button_fg'])
    return ctk.CTkButton(
        parent,
        text="Process Files",
        command=command,
        fg_color=theme['button_bg'],
        hover_color=theme['button_hover'],
        text_color=theme['button_fg']
    )

def build_table(parent: tk.Widget, sort_command: Callable) -> ttk.Treeview:
    """Create the results table with robust event and data handling."""
    columns = ('File', 'Classification', 'Confidence', 'Date')
    style = ttk.Style()
    style.configure(
        "Treeview",
        rowheight=28,
        font=("Arial", 11),
        background=theme.get('table_bg', "#fff"),
        fieldbackground=theme.get('table_bg', "#fff"),
        foreground=theme.get('table_fg', "#181818"),
    )
    style.configure(
        "Treeview.Heading",
        font=("Arial", 11, "bold"),
        background=theme.get('header_bg', "#eff"),
        foreground=theme.get('fg', "#222"),
    )
    table = ttk.Treeview(parent, columns=columns, show='headings')
    for col in columns:
        table.heading(col, text=col, command=lambda c=col: sort_command(c))
        table.column(col, anchor='w', minwidth=80, width=140, stretch=True)
    return table

def build_output_selector(parent: tk.Widget, var: tk.StringVar, browse_command: Callable) -> Tuple[ctk.CTkEntry, ctk.CTkButton]:
    """Create the output file selector widgets with value validation."""
    validate_theme(theme, ['entry_bg', 'entry_fg', 'button_bg', 'button_hover', 'button_fg'])
    entry = ctk.CTkEntry(
        parent,
        textvariable=var,
        placeholder_text="Select output location...",
        fg_color=theme['entry_bg'],
        text_color=theme['entry_fg']
    )
    # Add right-click context clear option
    def clear_entry(event): var.set('')
    entry.bind("<Button-3>", clear_entry)
    button = ctk.CTkButton(
        parent,
        text="Browse",
        command=browse_command,
        fg_color=theme['button_bg'],
        hover_color=theme['button_hover'],
        text_color=theme['button_fg']
    )
    return entry, button

def build_folder_selector(parent: tk.Widget, var: tk.StringVar, browse_command: Callable) -> Tuple[ctk.CTkEntry, ctk.CTkButton]:
    """Create the folder selector widgets with value validation."""
    validate_theme(theme, ['entry_bg', 'entry_fg', 'button_bg', 'button_hover', 'button_fg'])
    entry = ctk.CTkEntry(
        parent,
        textvariable=var,
        placeholder_text="Select folder to scan...",
        fg_color=theme['entry_bg'],
        text_color=theme['entry_fg']
    )
    def clear_entry(event): var.set('')
    entry.bind("<Button-3>", clear_entry)
    button = ctk.CTkButton(
        parent,
        text="Browse",
        command=browse_command,
        fg_color=theme['button_bg'],
        hover_color=theme['button_hover'],
        text_color=theme['button_fg']
    )
    return entry, button

def build_trust_panel(parent: tk.Widget, how_command: Callable) -> ctk.CTkFrame:
    """Create the trust/help panel with robust dependency injection."""
    validate_theme(theme, ['panel_bg', 'fg', 'button_bg', 'button_hover', 'button_fg'])
    frame = ctk.CTkFrame(parent, fg_color=theme['panel_bg'])
    label = ctk.CTkLabel(
        frame,
        text="Trust & Security",
        font=("Arial", 14, "bold"),
        text_color=theme['fg']
    )
    how_button = ctk.CTkButton(
        frame,
        text="How it Works",
        command=how_command,
        fg_color=theme['button_bg'],
        hover_color=theme['button_hover'],
        text_color=theme['button_fg']
    )
    label.pack(pady=(10,3))
    how_button.pack(pady=(0,10))
    frame.pack(fill='x', pady=10)
    return frame

def build_header(parent: tk.Widget) -> ctk.CTkFrame:
    """Create the application header."""
    validate_theme(theme, ['header_bg', 'fg'])
    frame = ctk.CTkFrame(parent, fg_color=theme['header_bg'])
    title = ctk.CTkLabel(
        frame,
        text="Pierce County Records Classifier",
        font=("Arial", 18, "bold"),
        text_color=theme['fg']
    )
    subtitle = ctk.CTkLabel(
        frame,
        text="Automated Document Classification Tool",
        font=("Arial", 12),
        text_color=theme['fg']
    )
    title.pack(pady=5)
    subtitle.pack(pady=(0,7))
    frame.pack(fill='x', pady=10)
    return frame

"""Modern, animated widgets for Records Classifier GUI."""
import customtkinter as ctk
import tkinter as tk
import time
import threading
from .theme import theme

class AnimatedRunButton(ctk.CTkButton):
    """Button with loading animation and success state."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_loading = False
        self._original_text = kwargs.get('text', '')
        self._checkmark_shown = False
        self._pulse = False
        self._pulse_id = None
        self._default_color = self.cget('fg_color')
        self._configure_animation()
        
    def _configure_animation(self):
        """Set up button animation states."""
        self._dots = ["", ".", "..", "..."]
        self._dot_index = 0
        self._animation_after_id = None
        
    def _animate(self):
        """Animate loading dots."""
        if self._is_loading:
            self._dot_index = (self._dot_index + 1) % len(self._dots)
            self.configure(text=f"{self._original_text}{self._dots[self._dot_index]}")
            self._animation_after_id = self.after(500, self._animate)
            
    def start_loading(self):
        """Start loading animation."""
        self._is_loading = True
        self._pulse = False
        if self._pulse_id:
            self.after_cancel(self._pulse_id)
            self._pulse_id = None
        self.configure(state="disabled")
        self._animate()
        
    def stop_loading(self):
        """Stop loading animation."""
        self._is_loading = False
        if self._animation_after_id:
            self.after_cancel(self._animation_after_id)
        self.configure(text=self._original_text, state="normal")
        self._checkmark_shown = False
        
    def _show_checkmark(self):
        """Show success checkmark briefly."""
        if not self._checkmark_shown:
            self._checkmark_shown = True
            self.configure(text="✓ Done")
            self.after(2000, self.stop_loading)
            
    def _pulse_anim(self, step):
        """Animate button pulsing on hover."""
        if not self._pulse:
            return
        
        color = theme['button_hover'] if step % 2 == 0 else theme['button_bg']
        self.configure(fg_color=color)
        self._pulse_id = self.after(300, self._pulse_anim, step+1)
            
    def _on_enter(self, event=None):
        """Handle mouse enter with proper event handling and pulse animation."""
        if not self._is_loading and not self._checkmark_shown:
            super()._on_enter(event) if event else super()._on_enter()
            self._pulse = True
            self._pulse_anim(1)
            
    def _on_leave(self, event=None):
        """Handle mouse leave with proper cleanup."""
        if not self._is_loading and not self._checkmark_shown:
            self._pulse = False
            if self._pulse_id:
                self.after_cancel(self._pulse_id)
                self._pulse_id = None
            self.configure(fg_color=self._default_color)
            super()._on_leave(event) if event else super()._on_leave()
            
    def configure(self, **kwargs):
        """Override configure to handle special cases."""
        if "state" in kwargs:
            self._state = kwargs["state"]
        super().configure(**kwargs)

class AnimatedSpinner(ctk.CTkFrame):
    """Smooth spinning loading indicator."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configure(width=20, height=20, fg_color='transparent')
        
        # Create canvas for drawing
        self.canvas = tk.Canvas(
            self,
            width=20,
            height=20,
            bg=theme['bg'],
            highlightthickness=0
        )
        self.canvas.pack(fill='both', expand=True)
        
        # Initialize spinner properties
        self._angle = 0
        self._is_spinning = False
        self._animation_event = threading.Event()
        
        # Draw initial spinner
        self._draw_spinner()

    def start(self):
        """Start the spinning animation."""
        self._is_spinning = True
        threading.Thread(target=self._spin, daemon=True).start()

    def stop(self):
        """Stop the spinning animation."""
        self._is_spinning = False
        self._animation_event.set()

    def _draw_spinner(self):
        """Draw the spinner at current angle."""
        self.canvas.delete('spinner')
        
        # Draw arc with gradient effect
        for i in range(8):
            angle = (self._angle + i * 45) % 360
            start = angle
            extent = 30
            
            # Calculate color opacity
            opacity = hex(int(255 * (8 - i) / 8))[2:].zfill(2)
            color = f"{theme['spinner_color']}{opacity}"
            
            self.canvas.create_arc(
                4, 4, 16, 16,
                start=start,
                extent=extent,
                width=2,
                outline=color,
                tags='spinner'
            )

    def _spin(self):
        """Animate the spinner rotation."""
        while self._is_spinning:
            if not self._is_spinning:
                break
            self._angle = (self._angle + 10) % 360
            self._draw_spinner()
            time.sleep(0.05)
        self._animation_event.clear()

class AnimatedStatusLabel(ctk.CTkLabel):
    """Status label with smooth text transitions."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_text = kwargs.get('text', '')
        self._target_text = self._current_text
        self._animation_event = threading.Event()

    def set(self, text):
        """Set status text with animation."""
        self._target_text = text
        threading.Thread(target=self._animate_text, daemon=True).start()

    def _animate_text(self):
        """Animate text change with fade effect."""
        # Fade out
        for alpha in range(100, 0, -10):
            if self._current_text != self._target_text:
                self.configure(text_color=f"{theme['fg']}{hex(alpha)[2:].zfill(2)}")
                time.sleep(0.02)

        # Update text
        self._current_text = self._target_text
        self.configure(text=self._current_text)

        # Fade in
        for alpha in range(0, 100, 10):
            if self._current_text == self._target_text:
                self.configure(text_color=f"{theme['fg']}{hex(alpha)[2:].zfill(2)}")
                time.sleep(0.02)

        # Ensure full opacity
        self.configure(text_color=theme['fg'])

class LiveUpdateTable(ttk.Treeview):
    """Modern enterprise-grade table widget with live updates and flexible styling."""
    
    def __init__(self, master, columns, **kwargs):
        # Extract custom options to avoid passing them to ttk.Treeview
        virtualized = kwargs.pop('virtualized', False)
        reorderable = kwargs.pop('reorderable', False)
        # Initialize base Treeview with proper columns
        super().__init__(master, columns=[col[0] for col in columns], show=kwargs.get('show', 'headings'), **{k: v for k, v in kwargs.items() if k not in ['show']})
        # Store column definitions for internal use
        self._column_defs = columns
        # Configure headings and column widths
        for col_id, col_title, col_width in columns:
            self.heading(col_id, text=col_title)
            self.column(col_id, width=col_width, anchor='w')
        # Optionally configure virtualized scrolling or reordering
        if virtualized:
            # Placeholder: integrate virtual scrolling support library or custom logic
            pass
        if reorderable:
            # Placeholder: enable column drag-reordering if implemented
            pass
        
        # Configure tags for alternating rows and status highlighting
        self.tag_configure("oddrow", background=theme["bg_alt"])
        self.tag_configure("retain", foreground=theme["success"])
        self.tag_configure("destroy", foreground=theme["error"])
        self.tag_configure("review", foreground=theme["warning"])
        
        # Configure selection
        self.configure(selectmode="browse")
        
        # Configure scrollbar
        self.yscrollbar = ttk.Scrollbar(master, orient="vertical", command=self.yview)
        self.configure(yscrollcommand=self.yscrollbar.set)
        
        # Bind events
        self.bind("<<TreeviewSelect>>", self._on_select)
        self.bind("<Motion>", self._on_motion)
        
        # Performance optimizations
        self._item_cache = {}  # Cache for rendered items
        self._update_queue = []  # Queue for batched updates
        self._last_update = 0  # Timestamp of last update
        self._update_scheduled = False
        
    def _on_motion(self, event):
        """Handle mouse motion for hover effects."""
        row = self.identify_row(event.y)
        if row and not self.selection():
            self.selection_set(row)
    
    def _on_select(self, event):
        """Handle row selection."""
        selected = self.selection()
        if selected:
            self.event_generate("<<RowSelected>>")
    
    def update_item(self, item_id, values):
        """Update a single item with optimized rendering."""
        if not self._update_scheduled:
            self._update_scheduled = True
            self.after(50, self._process_updates)  # Batch updates every 50ms
        
        self._update_queue.append((item_id, values))
        
    def _process_updates(self):
        """Process batched updates for better performance."""
        self._update_scheduled = False
        
        for item_id, values in self._update_queue:
            try:
                self.item(item_id, values=values)
            except tk.TclError:
                # Item doesn't exist, insert it
                self.insert("", "end", iid=item_id, values=values)
            
            # Update alternating row colors
            odd = len(self.get_children()) % 2 == 1
            self.item(item_id, tags=("oddrow",) if odd else ())
            
            # Add status tag if applicable
            if values[-1].lower() == "retain":
                self.item(item_id, tags=("retain",))
            elif values[-1].lower() == "destroy":
                self.item(item_id, tags=("destroy",))
            elif values[-1].lower() == "review":
                self.item(item_id, tags=("review",))
        
        self._update_queue.clear()
    
    def set_items(self, items):
        """Set all items at once with optimized rendering."""
        # Clear existing items
        self.delete(*self.get_children())
        
        # Insert all items at once
        for i, (item_id, values) in enumerate(items):
            tags = ["oddrow"] if i % 2 == 1 else []
            if values[-1].lower() in ["retain", "destroy", "review"]:
                tags.append(values[-1].lower())
            self.insert("", "end", iid=item_id, values=values, tags=tags)
            
        self._item_cache.clear()  # Clear the cache
