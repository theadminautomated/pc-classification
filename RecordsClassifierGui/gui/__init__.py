"""
GUI package for Records Classifier.

This package contains the user interface components:
- screens: Main GUI application screens and logic  
- screens_optimized: Optimized version of the GUI screens
- theme: Application theming and styling
"""

# Re-export only core modules for gui package
from .theme import *
from .screens import *

__all__ = ['screens', 'screens_optimized', 'theme']
