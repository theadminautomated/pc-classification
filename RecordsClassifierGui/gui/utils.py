"""
utils.py - Enterprise-grade Utility functions for the Records Classifier GUI
Includes robust, type-safe, and extensible widget hover effect management.
"""

"""
app_gui.utils - Enterprise-grade Utility functions for the Records Classifier GUI
Includes robust, type-safe, and extensible widget hover effect management.
"""

# This file is part of the app_gui package
from typing import Optional, Any
import tkinter as tk
import sys
from pathlib import Path

def hover_effect(widget: Any, enter_bg: Optional[str] = None, leave_bg: Optional[str] = None) -> None:
    """
    Add hover background change effect to a widget with robust error handling.
    
    Parameters:
        widget (tk.Widget): The widget to add the effect to.
        enter_bg (str, optional): Background color when mouse enters. If None, no change.
        leave_bg (str, optional): Background color when mouse leaves. If None, no change.
    """
    original_bg = getattr(widget, "_original_bg", None)
    if original_bg is None and hasattr(widget, "cget"):
        try:
            original_bg = widget.cget("bg")
        except Exception:
            original_bg = None
        setattr(widget, "_original_bg", original_bg)

    def on_enter(event):
        bg = enter_bg if enter_bg is not None else original_bg
        if bg is not None:
            try:
                widget.configure(bg=bg)
            except Exception:
                pass

    def on_leave(event):
        bg = leave_bg
        if bg is None:
            # Revert to original
            bg = getattr(widget, "_original_bg", None)
        if bg is not None:
            try:
                widget.configure(bg=bg)
            except Exception:
                pass

    # Defensive: prevent multiple bindings of same function object
    widget.unbind('<Enter>')
    widget.unbind('<Leave>')
    widget.bind('<Enter>', on_enter, add='+')
    widget.bind('<Leave>', on_leave, add='+')
