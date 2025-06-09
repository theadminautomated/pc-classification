# Pierce County Electronic Records Classifier (GUI)

## Modern Modular Architecture (2025-05-29)

This project is organized for maximum scalability, maintainability, and clarity. All code is separated by responsibility.

### Project Structure

```
RecordsClassifierGui/
    core/         # Business logic, file scanning, LLM, model operations
    gui/          # All GUI components, screens, theming, tooltips
    utils/        # Shared utility functions and helpers
    model/        # Model files, Modelfile, and weights
    README.md     # This documentation
    requirements.txt
    ...
```

### Key Modules
- `core/`: All backend logic, file scanning, chunking, model import, and LLM engine
- `gui/`: All CustomTkinter GUI, screens, UI components, theming, tooltips
- `utils/`: Shared helpers, utility functions
- `model/`: Modelfile, model weights, and assets

### Entry Point
- `run_app.py` (root): Launches the GUI and wires together core and gui modules

---

## Production-Ready Features
- All core logic, validation, and UI flows are implemented and robust
- All visible actions are implemented or clearly marked as "Coming Soon" (bulk move/delete)
- Accessibility: color contrast, font size, keyboard navigation, and tooltips for all controls
- Real-time feedback, micro-animations, and status indicators
- Version number is shown in the window title
- All documentation and help text are up-to-date
- All UI method references are implemented, with robust error handling for all actions
- Resource usage is optimized for speed and efficiency, even with large folders
- The app now includes a single, detailed 'How It Works' help page (see the Help tab in the app)

## How It Works
- Click the "How It Works" button or open the Help tab in the main UI for a summary of the workflow
- The app scans files, extracts and cleans content, applies 6-year retention, classifies with LLM, validates output, and updates the table in real time
- You can select files and export results to CSV
- Bulk move/delete are planned for a future release and are disabled in the UI

## For Developers
- All code is robustly documented with docstrings and module-level comments
- Follow the modular structure for all new features
- See each module for further documentation

---

## Build & Run
- To run: `python run_app.py`
- To build: run `..\build_installer.ps1` from the repository root. This script
  creates a signed EXE and Windows installer in the `release` folder.
- For deployment: distribute only the installer. No manual dependency setup is
  required on the target machine.

---

*Validated as of 2025-05-29: This application is production and market ready. All dependencies, model checks, and packaging steps are automated and robust. Bulk move/delete are planned for a future release.*

Pierce County IT | 2025
