"""
Deploy.ps1 - Automated deployment for Pierce County Electronic Records Classifier (Python)

This script is for deploying the Python-based Records Classifier solution.
It is NOT for .NET or Visual Studio projects. Ignore any .csproj or .sln errors.

Features:
- Ensures Ollama is installed and running
- Imports the custom LLM model for classification
- Verifies model availability

Usage:
    powershell.exe -ExecutionPolicy Bypass -File Deploy.ps1

Author: Pierce County IT
Date: 2025-05-28
"""

# Ensure Ollama is installed
if (-not (Get-Command "ollama" -ErrorAction SilentlyContinue)) {
    Write-Host "Ollama is not installed. Please install Ollama from https://ollama.com/download and ensure it is in your PATH." -ForegroundColor Red
    exit 1
}

# Ensure Ollama service is running
try {
    $ollamaStatus = ollama list
    Write-Host "Ollama service is running." -ForegroundColor Green
} catch {
    Write-Host "Ollama service is not running. Please start it with: ollama serve" -ForegroundColor Red
    exit 1
}

# Import the phi2 model if not present
$modelSource = "Modelfile-phi2"
$modelName = "pierce-county-records-classifier-phi2"

if (Test-Path $modelSource) {
    $models = ollama list | Select-String $modelName
    if (-not $models) {
        Write-Host "Importing custom phi2 model..." -ForegroundColor Yellow
        ollama create $modelName -f $modelSource
        Write-Host "Model imported successfully." -ForegroundColor Green
    } else {
        Write-Host "Model '$modelName' already available." -ForegroundColor Green
    }
} else {
    Write-Host "Model file '$modelSource' not found. Please ensure it is present in the root directory." -ForegroundColor Red
    exit 1
}

Write-Host "Deployment complete. You may now run the application using run_app.py or the packaged EXE." -ForegroundColor Green