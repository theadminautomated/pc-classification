"""
gui.tooltip - Tooltip helpers for Records Classifier GUI
Moved under gui/ for modular architecture. All imports updated to new structure.

Author: Pierce County IT
Date: 2025-05-27
"""
import tkinter as tk
import importlib.util
import sys
import os
def _import_local(name):
    here = os.path.dirname(__file__)
    spec = importlib.util.spec_from_file_location(name, os.path.join(here, f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

from .theme import theme

# Get the font family from theme module directly
FONT_FAMILY = "Segoe UI Variable" if sys.platform == "win32" else "SF Pro Display" if sys.platform == "darwin" else "Inter"

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind('<Enter>', self.show)
        widget.bind('<Leave>', self.hide)

    def show(self, event=None):
        if self.tip or not self.text:
            return
        x, y = self.widget.winfo_rootx() + 20, self.widget.winfo_rooty() + 20
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f'+{x}+{y}')
        lbl = tk.Label(self.tip, text=self.text, bg=theme.get('tooltip_bg', '#222C3A'), fg=theme.get('tooltip_fg', '#F3F6FA'), relief='solid', bd=1, font=(FONT_FAMILY, 9))
        lbl.pack(ipadx=8, ipady=3)

    def hide(self, event=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None
