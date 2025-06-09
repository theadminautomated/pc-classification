#!/usr/bin/env python3
"""
Simple demo script to showcase the enhanced MainScreen implementation.
This script launches the MainScreen directly for testing and demonstration.
"""

import sys
import os
import logging
import tkinter as tk

# Add the RecordsClassifierGui directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'RecordsClassifierGui'))

try:
    import customtkinter as ctk
    from gui.screens import MainScreen
    from gui.theme import theme

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logger = logging.getLogger(__name__)

    logger.info("🚀 Launching Enhanced Records Classifier MainScreen Demo...")
    logger.info("=" * 60)
    
    # Configure CustomTkinter
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # Create main window
    root = ctk.CTk()
    root.title("Pierce County Records Classifier - Enhanced UI Demo")
    root.geometry("1400x900")
    root.configure(fg_color=theme['bg'])
    
    logger.info("✓ Main window created")
    
    # Create and display MainScreen
    main_screen = MainScreen(root)
    main_screen.pack(fill="both", expand=True)
    
    logger.info("✓ MainScreen initialized with enhanced features:")
    logger.info("  • Modern header with branding and quick stats")
    logger.info("  • Enhanced path selection with real-time validation")
    logger.info("  • Advanced controls with parallel jobs slider")
    logger.info("  • Sophisticated results table with bulk operations")
    logger.info("  • Modern status bar with real-time statistics")
    logger.info("  • Comprehensive keyboard shortcuts")
    logger.info("  • Focus handlers and enhanced UX")
    logger.info("  • Mock processing simulation")
    logger.info("  • Table sorting and context menus")
    logger.info("  • Bulk operations (RERUN, EXPORT, DESTROY)")
    
    logger.info("\n📋 Available Keyboard Shortcuts:")
    logger.info("  • Ctrl+O: Browse input folder")
    logger.info("  • Ctrl+S: Browse output file")
    logger.info("  • Ctrl+R: Start/Stop classification")
    logger.info("  • Ctrl+A: Select/Deselect all")
    logger.info("  • Delete: Remove selected items")
    logger.info("  • Ctrl+E: Export selected items")
    logger.info("  • Ctrl+T: Toggle theme")
    logger.info("  • F5: Refresh table")
    logger.info("  • Escape: Clear selection")
    
    logger.info("\n🎯 UI Features Demonstrated:")
    logger.info("  • Modern glassmorphism design")
    logger.info("  • Responsive layout with proper grid management")
    logger.info("  • Real-time path validation with visual feedback")
    logger.info("  • Advanced table with extended columns and color-coding")
    logger.info("  • Parallel processing controls")
    logger.info("  • Comprehensive error handling")
    logger.info("  • Accessibility features and tooltips")
    
    logger.info("\n🌟 The enhanced UI is now ready for use!")
    logger.info("=" * 60)
    
    # Start the application
    root.mainloop()
    
except ImportError as e:
    logging.error("❌ Import error: %s", e)
    logging.error("Please ensure all required dependencies are installed.")
except Exception as e:
    logging.exception("❌ Error launching demo: %s", e)
