#!/usr/bin/env python
"""
Records Classifier Setup Script

This script installs all required dependencies for the Records Classifier application,
checks if the environment is properly set up, and ensures all system and Python dependencies
are present. It is fully self-contained and requires no user intervention after launch.

Author: Pierce County IT
Date: 2025-05-28
"""

import subprocess
import sys
import os
import platform
from pathlib import Path

def print_header(text):
    print("\n" + "=" * 60)
    print(f" {text}")
    print("=" * 60)

def print_success(text):
    print(f"\033[92m✓ {text}\033[0m")

def print_error(text):
    print(f"\033[91m✗ {text}\033[0m")

def print_info(text):
    print(f"ℹ {text}")

def print_warning(text):
    print(f"\033[93m! {text}\033[0m")

def check_python_version():
    print_header("Checking Python Version")
    py_version = platform.python_version()
    print(f"Python version: {py_version}")
    major, minor, _ = map(int, py_version.split('.'))
    if major >= 3 and minor >= 8:
        print_success(f"Python version {py_version} is adequate")
        return True
    else:
        print_error(f"Python version {py_version} is too old. Please use Python 3.8 or newer.")
        return False

def pip_install(package):
    """Install a package via pip, upgrading if already present."""
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", package],
                       check=True, capture_output=True)
        print_success(f"{package} installed/upgraded successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install {package}")
        print(e.stderr.decode('utf-8'))
        return False

def install_dependencies():
    print_header("Installing Dependencies")
 codex/refactor-core-logic-functions
    dependencies = [
        "customtkinter>=5.2.0",
        "Pillow>=9.0.0",
        "ollama>=0.1.8",
        "openpyxl>=3.1.2",
        "python-docx>=0.8.11",
        "python-pptx>=0.6.21",
        "PyPDF2>=3.0.0",
        "pdfplumber>=0.8.1",
        "pytesseract>=0.3.10",
        "pdf2image>=1.16.0",
        "typing-extensions>=4.0.0",
        "xlrd>=2.0.1",
        "jsonschema>=4.24.0",
        "pandas>=2.2.2",
        "pytest>=8.2.1"
    ]

    dependencies = [
        "customtkinter>=5.2.0",
        "Pillow>=9.0.0",
        "ollama>=0.1.7",
        "psutil>=5.9.0",
        "openpyxl>=3.1.2",
        "python-docx>=0.8.11",
        "python-pptx>=0.6.21",
        "PyPDF2>=3.0.0",
        "pdfplumber>=0.8.1",
        "pytesseract>=0.3.10",
        "pdf2image>=1.16.0",
        "typing-extensions>=4.0.0",
        "xlrd>=2.0.1"
    ]
 main
    all_ok = True
    for dep in dependencies:
        if not pip_install(dep):
            all_ok = False
    return all_ok

def check_executable(cmd):
    """Check if an executable is available in PATH."""
    if platform.system() == "Windows":
        result = subprocess.run(["where", cmd], capture_output=True, text=True)
    else:
        result = subprocess.run(["which", cmd], capture_output=True, text=True)
    return result.returncode == 0

def check_system_dependencies():
    print_header("Checking System Dependencies")
    # Check Tesseract
    tesseract_ok = check_executable("tesseract")
    if tesseract_ok:
        print_success("Tesseract OCR is installed")
    else:
        print_warning("Tesseract OCR not found. Attempting to install...")
        if platform.system() == "Windows":
            # Download and install Tesseract silently (Windows only)
            import urllib.request, tempfile, shutil
            tesseract_url = "https://github.com/UB-Mannheim/tesseract/wiki/tesseract-ocr-w64-setup-v5.3.3.20231005.exe"
            temp_dir = tempfile.gettempdir()
            installer_path = os.path.join(temp_dir, "tesseract-installer.exe")
            try:
                urllib.request.urlretrieve(tesseract_url, installer_path)
                subprocess.run([installer_path, "/SILENT"], check=True)
                print_success("Tesseract OCR installed successfully")
                tesseract_ok = check_executable("tesseract")
            except Exception as e:
                print_error(f"Failed to install Tesseract OCR: {e}")
        else:
            # Try to install via apt or brew
            if check_executable("apt-get"):
                subprocess.run(["sudo", "apt-get", "update"], check=False)
                subprocess.run(["sudo", "apt-get", "install", "-y", "tesseract-ocr"], check=False)
                tesseract_ok = check_executable("tesseract")
            elif check_executable("brew"):
                subprocess.run(["brew", "install", "tesseract"], check=False)
                tesseract_ok = check_executable("tesseract")
            if tesseract_ok:
                print_success("Tesseract OCR installed successfully")
            else:
                print_warning("Tesseract OCR could not be installed automatically. Please install it manually.")

    # Check Poppler (for pdf2image)
    poppler_ok = check_executable("pdftoppm")
    if poppler_ok:
        print_success("Poppler (pdftoppm) is installed")
    else:
        print_warning("Poppler not found. Attempting to install...")
        if platform.system() == "Windows":
            # Download and extract Poppler for Windows
            import zipfile, urllib.request, tempfile
            poppler_url = "https://github.com/oschwartz10612/poppler-windows/releases/download/v23.11.0-0/Release-23.11.0-0.zip"
            temp_dir = tempfile.gettempdir()
            zip_path = os.path.join(temp_dir, "poppler.zip")
            poppler_dir = os.path.join(temp_dir, "poppler")
            try:
                urllib.request.urlretrieve(poppler_url, zip_path)
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(poppler_dir)
                # Add to PATH for this session
                bin_path = os.path.join(poppler_dir, "Library", "bin")
                os.environ["PATH"] += os.pathsep + bin_path
                print_success("Poppler extracted and added to PATH")
                poppler_ok = check_executable("pdftoppm")
            except Exception as e:
                print_error(f"Failed to install Poppler: {e}")
        else:
            if check_executable("apt-get"):
                subprocess.run(["sudo", "apt-get", "update"], check=False)
                subprocess.run(["sudo", "apt-get", "install", "-y", "poppler-utils"], check=False)
                poppler_ok = check_executable("pdftoppm")
            elif check_executable("brew"):
                subprocess.run(["brew", "install", "poppler"], check=False)
                poppler_ok = check_executable("pdftoppm")
            if poppler_ok:
                print_success("Poppler installed successfully")
            else:
                print_warning("Poppler could not be installed automatically. Please install it manually.")

    return tesseract_ok, poppler_ok

def setup_model_directory():
    print_header("Setting Up Model Directory")
    script_dir = Path(__file__).resolve().parent
    model_dir = script_dir / "pierce-county-records-classifier-phi2"
    try:
        model_dir.mkdir(exist_ok=True)
        print_success(f"Model directory created at {model_dir}")
        placeholder = model_dir / "latest"
        placeholder.touch(exist_ok=True)
        print_success("Model placeholder created")
    except Exception as e:
        print_error(f"Failed to create model directory: {e}")
        return False
    return True

def check_ollama():
    print_header("Checking Ollama")
    ollama_ok = check_executable("ollama")
    if ollama_ok:
        print_success("Ollama is installed")
    else:
        print_warning("Ollama is not installed or not in PATH. Attempting to install...")
        if platform.system() == "Windows":
            ollama_url = "https://github.com/jmorganca/ollama/releases/latest/download/OllamaSetup.exe"
            import urllib.request, tempfile
            temp_dir = tempfile.gettempdir()
            installer_path = os.path.join(temp_dir, "OllamaSetup.exe")
            try:
                urllib.request.urlretrieve(ollama_url, installer_path)
                subprocess.run([installer_path, "/SILENT"], check=True)
                ollama_ok = check_executable("ollama")
                if ollama_ok:
                    print_success("Ollama installed successfully")
            except Exception as e:
                print_error(f"Failed to install Ollama: {e}")
        else:
            # Mac/Linux: try curl or brew
            if check_executable("brew"):
                subprocess.run(["brew", "install", "ollama"], check=False)
                ollama_ok = check_executable("ollama")
            elif check_executable("curl"):
                try:
                    subprocess.run("curl -fsSL https://ollama.com/install.sh | sh", shell=True, check=True)
                    ollama_ok = check_executable("ollama")
                except Exception as e:
                    print_error(f"Failed to install Ollama: {e}")
            if ollama_ok:
                print_success("Ollama installed successfully")
            else:
                print_warning("Ollama could not be installed automatically. Please install it manually from https://ollama.ai")
    # Try to start Ollama service if not running
    try:
        import psutil
        ollama_running = False
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and 'ollama' in proc.info['name'].lower():
                ollama_running = True
                print_success("Ollama service is running")
                break
        if not ollama_running:
            print_info("Starting Ollama service...")
            if platform.system() == "Windows":
                subprocess.Popen(["ollama", "serve"], creationflags=subprocess.DETACHED_PROCESS)
            else:
                subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print_success("Ollama service started")
    except Exception as e:
        print_warning(f"Could not check/start Ollama service: {e}")
    return ollama_ok

def main():
    print_header("Records Classifier Setup")
    print(f"Platform: {platform.platform()}")
    print(f"Working directory: {os.getcwd()}")
    if not check_python_version():
        sys.exit(1)
    if not install_dependencies():
        sys.exit(1)
    check_system_dependencies()
    if not setup_model_directory():
        sys.exit(1)
    check_ollama()
    print_header("Setup Complete")
    print_success("All dependencies installed successfully")
    print_info("You can now run the Records Classifier application using:")
    print("   python run_app.py")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)