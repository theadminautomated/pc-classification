# Enhanced PowerShell launcher script for Records Classifier
# Author: Pierce County IT
# Date: 2025-05-28

# Get script directory and navigate to it
$scriptPath = $PSScriptRoot
Set-Location -Path $scriptPath
$env:PYTHONPATH = $scriptPath

# Check if Python is installed
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Python is not installed or not in PATH!" -ForegroundColor Red
    Write-Host "Please install Python from https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host -Prompt "Press Enter to exit"
    exit
}

# Check if required packages are installed
$requiredPackages = @("customtkinter", "PIL", "ollama", "psutil")
$missingPackages = @()

foreach ($package in $requiredPackages) {
    $checkCmd = "python -c 'import $package' 2>&1"
    $result = Invoke-Expression $checkCmd
    if ($LASTEXITCODE -ne 0) {
        $missingPackages += $package
    }
}

# Install missing packages if needed
if ($missingPackages.Count -gt 0) {
    Write-Host "Installing missing packages: $($missingPackages -join ', ')" -ForegroundColor Yellow
    foreach ($package in $missingPackages) {
        # Convert PIL to Pillow for pip install
        $pipPackage = if ($package -eq "PIL") { "Pillow" } else { $package }
        Write-Host "Installing $pipPackage..." -ForegroundColor Cyan
        python -m pip install $pipPackage
    }
}

# Create model directory if it doesn't exist
$modelDir = Join-Path $scriptPath "pierce-county-records-classifier-phi2"
if (-not (Test-Path $modelDir)) {
    Write-Host "Creating model directory: $modelDir" -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $modelDir | Out-Null
    New-Item -ItemType File -Path (Join-Path $modelDir "latest") | Out-Null
}

# Check if Ollama is running
$ollamaRunning = $false
try {
    $processes = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
    if ($processes) {
        $ollamaRunning = $true
        Write-Host "Ollama service is running" -ForegroundColor Green
    } else {
        Write-Host "Ollama service is not running!" -ForegroundColor Red
        Write-Host "You may need to start it manually with 'ollama serve' in a separate terminal" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Could not check Ollama status: $_" -ForegroundColor Red
}

# Run the application
Write-Host "Starting Records Classifier..." -ForegroundColor Green
python run_app.py
