# build_installer.ps1 - Build standalone EXE and Windows installer
$ErrorActionPreference = 'Stop'

Write-Host 'Building Records Classifier executable...' -ForegroundColor Cyan

# Ensure PyInstaller is available
if (-not (Get-Command pyinstaller.exe -ErrorAction SilentlyContinue)) {
    Write-Host 'PyInstaller not found. Installing...' -ForegroundColor Yellow
    python -m pip install --upgrade pyinstaller | Out-Null
}

$spec = 'PC-RecordsClassifier.spec'
pyinstaller $spec

if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed.' }

# Path to built executable
$exePath = Join-Path 'dist' 'PC-RecordsClassifier.exe'
if (-not (Test-Path $exePath)) {
    throw "EXE not found at $exePath"
}

Write-Host 'Creating Windows installer...' -ForegroundColor Cyan
$iss = Join-Path 'installer' 'pcrc_installer.iss'
if (-not (Test-Path $iss)) { throw "Installer script not found: $iss" }

# Require Inno Setup's ISCC.exe to be installed and in PATH
if (-not (Get-Command iscc.exe -ErrorAction SilentlyContinue)) {
    throw 'iscc.exe not found. Install Inno Setup and ensure ISCC is in PATH.'
}

iscc $iss /DAppExe=$exePath /DOutputDir='release'
if ($LASTEXITCODE -ne 0) { throw 'Installer build failed.' }

Write-Host "Installer created in 'release' folder." -ForegroundColor Green
