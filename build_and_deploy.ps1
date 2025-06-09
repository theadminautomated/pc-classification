# build_and_deploy.ps1 - One-and-done build/deploy script for Pierce County Records Classifier
# Author: Jacob Taylor | Team: Microsoft 365 Service | Unit: Client Technology Services (CTS) | Division: Information Technology | Org: Pierce County

<# TODO: Unable to launch built exe. error:
Traceback (most recent call last):
  File "\\ad\pcfiles\IT\IT Ops\Product_Support_Documentation\M365 Administration\Records\RecordsClassifierGui\RecordsClassifierGui.py", line 21, in <module>
    import shutil
                ^^
  File "\\ad\pcfiles\IT\IT Ops\Product_Support_Documentation\M365 Administration\Records\RecordsClassifierGui\RecordsClassifierGui.py", line 19, in _import_local
    import multiprocessing
        ^^^^^^^^^^^^^^^^^^^
  File "<frozen importlib._bootstrap_external>", line 991, in exec_module
  File "<frozen importlib._bootstrap_external>", line 1128, in get_code
  File "<frozen importlib._bootstrap_external>", line 1186, in get_data
FileNotFoundError: [Errno 2] No such file or directory: 'C:\\Users\\jtaylo7\\AppData\\Local\\Temp\\_MEI202442\\theme.py'
#>
# This script automates the build and deployment process for the Pierce County Records Classifier application.
$ErrorActionPreference = 'Stop'
Write-Host "Pierce County Records Classifier - Automated Build & Deploy" -ForegroundColor Cyan
Write-Host "Author: Jacob Taylor | Team: Microsoft 365 Service | CTS | IT | Pierce County" -ForegroundColor Yellow

# Immediately determine and set script directory as working directory
# Use multiple fallback methods to ensure we get the correct path
if ($PSScriptRoot) {
    $scriptRoot = $PSScriptRoot
    Write-Host "Using PSScriptRoot path: $scriptRoot" -ForegroundColor DarkGray
} elseif ($MyInvocation.MyCommand.Path) {
    $scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
    Write-Host "Using MyInvocation path: $scriptRoot" -ForegroundColor DarkGray
} else {
    $scriptRoot = (Get-Location).Path
    Write-Host "Using current directory path: $scriptRoot" -ForegroundColor DarkGray
}

# Hardcoded fallback if all else fails (remove or modify as needed)
if (-not (Test-Path (Join-Path $scriptRoot "RecordsClassifierGui"))) {
    Write-Host "Could not find RecordsClassifierGui directory in $scriptRoot" -ForegroundColor Yellow
    $fallbackPath = "n:\IT Ops\Product_Support_Documentation\M365 Administration\Records"
    if (Test-Path $fallbackPath) {
        $scriptRoot = $fallbackPath
        Write-Host "Using fallback path: $scriptRoot" -ForegroundColor Yellow
    }
}

Set-Location $scriptRoot
Write-Host "Working directory set to: $scriptRoot" -ForegroundColor Green

# 1. Check Python
Write-Host "Checking Python..."
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw 'Python is not installed.' }

# 2. Check pip
Write-Host "Checking pip..."
if (-not (Get-Command pip -ErrorAction SilentlyContinue)) { throw 'pip is not installed.' }

# 3. Install dependencies
Write-Host "Installing/upgrading dependencies..."
python -m pip install --upgrade pip
python -m pip install customtkinter pillow openpyxl ollama pyinstaller

# 4. Skip external Deploy.ps1 - include model folder in EXE
Write-Host "Including LLM model in EXE package..."

# 5. Build EXE with PyInstaller (include model folder)
Write-Host "Building EXE with PyInstaller..."

# Verify all required paths exist
$guiDir = Join-Path $scriptRoot "RecordsClassifierGui"
$iconPath = Join-Path $guiDir "app.ico"
$mainScript = Join-Path $guiDir "gui\app_gui.py"
$modelDir = Join-Path $scriptRoot "pierce-county-records-classifier-phi2"

# Path existence checks
$allPathsExist = $true
if (-not (Test-Path $guiDir -PathType Container)) {
    Write-Host "ERROR: RecordsClassifierGui directory not found at: $guiDir" -ForegroundColor Red
    $allPathsExist = $false
}
if (-not (Test-Path $iconPath -PathType Leaf)) {
    Write-Host "ERROR: Icon file not found at: $iconPath" -ForegroundColor Red
    $allPathsExist = $false
}
if (-not (Test-Path $mainScript -PathType Leaf)) {
    Write-Host "ERROR: Main script not found at: $mainScript" -ForegroundColor Red
    $allPathsExist = $false
}
if (-not (Test-Path $modelDir -PathType Container)) {
    Write-Host "WARN: Model directory not found at: $modelDir" -ForegroundColor Yellow
    Write-Host "The model directory will not be included in the build." -ForegroundColor Yellow
    $includeModel = $false
} else {
    $includeModel = $true
}

if (-not $allPathsExist) {
    throw "Critical files missing. Cannot continue with build. Please check paths."
}

# Locate pyinstaller
$pyinstallerPath = (Get-Command pyinstaller.exe -ErrorAction SilentlyContinue).Source
if (-not $pyinstallerPath) { throw 'PyInstaller not found in PATH.' }

# Build pyinstaller command
$addData = @(
    "$(Join-Path $scriptRoot 'RecordsClassifierGui');RecordsClassifierGui"
)
if ($includeModel) {
    $addData += "$(Join-Path $scriptRoot 'pierce-county-records-classifier-phi2');pierce-county-records-classifier-phi2"
}

Write-Host "Using icon path: $iconPath" -ForegroundColor DarkGray
Write-Host "Using main script: $mainScript" -ForegroundColor DarkGray
foreach ($data in $addData) {
    Write-Host "Adding data: $data" -ForegroundColor DarkGray
}

# Build command with properly escaped arguments
$pyinstallerArgs = @(
    "--noconfirm",
    "--onefile",
    "--windowed",
    "--name", "PC-RecordsClassifier",
    "--icon", $iconPath
)

foreach ($data in $addData) {
    $pyinstallerArgs += "--add-data"
    $pyinstallerArgs += $data
}

$pyinstallerArgs += $mainScript

# Show the command that will be executed
$cmdDisplay = "$pyinstallerPath " + ($pyinstallerArgs -join " ")
Write-Host "Executing: $cmdDisplay" -ForegroundColor DarkGray

# Execute pyinstaller with the arguments
Write-Host "Starting PyInstaller build process..." -ForegroundColor Green
& $pyinstallerPath $pyinstallerArgs

# 6. Copy the generated EXE to a 'release' folder in the workspace
$distDir = Join-Path $scriptRoot "dist"
$releaseDir = Join-Path $scriptRoot "release"
$exeSource = Join-Path $distDir "PC-RecordsClassifier.exe"

# Check if build succeeded by confirming EXE exists
if (-not (Test-Path $exeSource -PathType Leaf)) {
    Write-Host "ERROR: Build failed! EXE not found at: $exeSource" -ForegroundColor Red
    Write-Host "Check the PyInstaller output above for errors." -ForegroundColor Yellow
    throw "Build failed - EXE file not found"
}

# Create release directory if it doesn't exist
if (-not (Test-Path $releaseDir -PathType Container)) { 
    Write-Host "Creating release directory: $releaseDir" -ForegroundColor DarkGray
    New-Item -ItemType Directory -Path $releaseDir | Out-Null
}

# Copy the EXE to the release folder
$exeDest = Join-Path $releaseDir "PC-RecordsClassifier.exe"
Write-Host "Copying EXE to release folder..." -ForegroundColor Green
Copy-Item -Path $exeSource -Destination $exeDest -Force
Write-Host "Executable successfully saved to: $exeDest" -ForegroundColor Green

# 7. Final instructions
Write-Host "`nBuild and copy complete!" -ForegroundColor Green
Write-Host "Release folder: $releaseDir" -ForegroundColor Cyan
Write-Host "`nTo distribute the application:" -ForegroundColor Yellow
Write-Host "1. Copy $exeDest to the target machine" -ForegroundColor White
if ($includeModel) {
    Write-Host "2. The model is already included in the EXE" -ForegroundColor White
} else {
    Write-Host "2. Copy the model folder 'pierce-county-records-classifier-phi2' to the target machine" -ForegroundColor White
}
Write-Host "3. Run the EXE to launch the Records Classifier application" -ForegroundColor White

Write-Host '=== [1/4] Ensure Ollama model files are present ==='
if (-not (Test-Path 'installer/models/manifests')) {
    Write-Error 'Missing model manifests. Copy from your .ollama/models/manifests directory.'
    exit 1
}
if (-not (Test-Path 'installer/models/blobs')) {
    Write-Error 'Missing model blobs. Copy from your .ollama/models/blobs directory.'
    exit 1
}

Write-Host '=== [2/4] Ensure Ollama binary is present ==='
if (-not (Test-Path 'installer/ollama.exe')) {
    Write-Error 'Missing installer/ollama.exe. Download from https://ollama.com/download.'
    exit 1
}

Write-Host '=== [3/4] Run PyInstaller build ==='
pyinstaller PC-RecordsClassifier.spec

Write-Host '=== [4/4] Copy installer assets to release directory ==='
$releaseDir = 'release'
if (-not (Test-Path $releaseDir)) { New-Item -ItemType Directory -Path $releaseDir | Out-Null }
Copy-Item -Recurse -Force installer $releaseDir
Write-Host 'Build and packaging complete. Distribute release/PC-RecordsClassifier.exe and release/installer/'
