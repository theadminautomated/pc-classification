"""
gui.theme - Theming and color palette for Records Classifier GUI
Defines professional enterprise theme with accessibility considerations
"""

import sys

# Modern system font stack with fallbacks
FONT_FAMILY = "Segoe UI Variable" if sys.platform == "win32" else "SF Pro Display" if sys.platform == "darwin" else "Inter"

# Spacing and layout constants
PADDING = 20  # Outer padding/margin
SPACING = 12  # Inner component spacing
CARD_RADIUS = 18  # Card corner radius

# Typography details
typography = {
    "default": (FONT_FAMILY, 14),
    "small": (FONT_FAMILY, 12),
    "large": (FONT_FAMILY, 16),
    "heading": (FONT_FAMILY, 18, "bold"),
    "title": (FONT_FAMILY, 24, "bold"),
    "mono": ("JetBrains Mono", 12),
}

# Colors palette
colors = {
    "navy": "#0a0e1a",
    "white": "#e8f4fd",
    "cyan": "#00d4ff",
    "purple": "#7c3aed",
    "blue": "#0078D7",
    "green": "#28A745",
    "yellow": "#FFC107",
    "red": "#DC3545",
    "gray": "#CED4DA",
}

# Layout presets
layout = {
    "padding": PADDING,
    "spacing": SPACING,
    "card_radius": CARD_RADIUS,
    "content_width": 1200,
    "form_width": 680,
}

theme = {  
    # ===== TYPOGRAPHY =====  
    "font": (FONT_FAMILY, 14),
    "font_small": (FONT_FAMILY, 12),
    "font_large": (FONT_FAMILY, 16),
    "font_mono": ("JetBrains Mono", 12),
    "font_heading": (FONT_FAMILY, 18, "bold"),
    "font_title": (FONT_FAMILY, 24, "bold"),
    
    # ===== ADVANCED INNOVATION THEME =====  
    "bg": "#0a0e1a",            # Deep tech navy
    "fg": "#e8f4fd",            # Bright ice white  
    "accent": "#00d4ff",        # Electric cyan
    "accent_soft": "#4db8ff",   # Softer accent for hover states
    "accent_hover": "#33e0ff",  # Brighter electric cyan
    "accent_secondary": "#7c3aed", # Innovation purple    # ===== SURFACE LAYERS =====  
    "panel_bg": "#162032",      # Tech panel surface
    "card_bg": "#1a2332",       # Innovation card background
    "header_bg": "#0f1724",     # Advanced header surface
    "status_bg": "#0f1724",     # Status bar
    "statusbar_bg": "#0f1724",  # Status bar (alias)
    "statusbar_fg": "#e8f4fd",  # Status bar text (alias)
    "subtle_fg": "#7dd3fc",     # Electric subdued text
      # ===== INTERACTION =====  
    "button_bg": "#0078D7",
    "button_fg": "#FFFFFF",
    "button_hover": "#005A9E",
    "button_active": "#004A8F",
    "button_disabled": "#CCCCCC",
    "button_success": "#28A745",
    "button_success_hover": "#218838",
    "button_warning": "#FFC107",
    "button_warning_hover": "#e0a800",
    "button_danger": "#DC3545",
    "input_bg": "#F8F9FA",
    "input_border": "#CED4DA",
    "input_focus": "#80BDFF",
    "disabled_bg": "#E9ECEF",
    "disabled_fg": "#6C757D",
    
    # ===== INDICATORS =====  
    "success": "#28A745",       # Success green
    "warning": "#FFC107",       # Warning amber
    "error": "#DC3545",         # Error red
    "info": "#17A2B8",          # Info blue
    "processing": "#6F42C1",    # Processing purple
      # ===== TABLE & DATA =====
    "table_header_bg": "#1e1e1e",
    "table_row_bg": "#2b2b2b",
    "table_row_alt_bg": "#333333",
    "table_border": "#3A3B40",
    "table_highlight": "#0078d422",
    "select_bg": "#0078d4",  # Selection background
    "select_fg": "#ffffff",  # Selection foreground text
    "bg_alt": "#333333",     # Alternate row background
    "data_viz": ["#00C4D8", "#FF5E7D", "#9D5CFF", "#00D7A0", "#FFB83D"],
    
    # ===== PROGRESS =====
    "progress_bg": "#333333",
    "progress_fill": "#0078d4",
    "progress_text": "#ffffff",
    "spinner_color": "#0078d4",
      # ===== ENHANCED LAYOUT =====
    "card_padding": 24,
    "section_spacing": 20,
    "element_spacing": 12,
    "button_height": 36,
    "input_height": 40,
    "header_height": 60,
    "statusbar_height": 32,
    
    # ===== ANIMATIONS =====
    "animation_duration": 200,
    "hover_scale": 1.02,
    "click_scale": 0.98,
      
    # ===== OVERLAY & EFFECTS =====
    "tooltip_bg": "#1e1e1e",
    "tooltip_fg": "#ffffff",
    "overlay_bg": "#000000CC",
    "shadow_sm": "0 2px 8px rgba(0,0,0,0.12)",
    "shadow_md": "0 4px 16px rgba(0,0,0,0.2)",
    "shadow_lg": "0 8px 32px rgba(0,0,0,0.3)",
    "frost": "rgba(120, 130, 150, 0.15)",
    "glow": "0 0 12px rgba(0, 196, 216, 0.3)",
    
    # ===== TRUST & SECURITY =====
    "trust_badge": "#00D7A0",   # Security elements
    "verified": "#00B4FF",      # Verification marks
    "encryption": "#9D5CFF",    # Privacy indicators
    
    # ===== CORE PROPERTIES =====
    "radius": CARD_RADIUS,      # Global corner radius
    "border_radius": 16,        # Alternative radius
    "transition": "all 0.25s cubic-bezier(0.65, 0, 0.35, 1)"
}

# Helper functions for better theme access
def get_color(key, default=None):
    """Get a color from the theme by key with an optional default."""
    return theme.get(key, default)

def get_font(key=None, size=None):
    """Get a font from the theme by key with an optional size override."""
    if key is None:
        # Return the default font
        base_font = theme.get("font", (FONT_FAMILY, 14))
    else:
        # Try to get a specific font by key (e.g., 'heading', 'title', etc.)
        font_key = f"font_{key}" if not key.startswith("font_") else key
        base_font = theme.get(font_key, theme.get("font", (FONT_FAMILY, 14)))
    
    # If size is specified, apply it
    if size is not None and isinstance(base_font, tuple) and len(base_font) >= 2:
        if len(base_font) > 2:
            # Font with weight/style
            return (base_font[0], size, *base_font[2:])
        else:
            # Simple font tuple
            return (base_font[0], size)
    
    return base_font

def get_color(key: str):
    """Retrieve a color from the theme by key."""
    return theme.get(key)

def get_font(key: str):
    """Retrieve a font tuple from the theme by key."""
    return theme.get(key)
