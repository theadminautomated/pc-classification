# Build and deploy script for Records Classification Tool
#
# This script:
# 1. Builds the Records Classification Tool as a self-contained executable
# 2. Creates an optional ZIP package for distribution
# 3. Provides options for copying to a network share
#
# Requirements: .NET SDK 8.0 or newer
param([switch]$CreateZip,[string]$NetworkSharePath,[switch]$ImportModelOnly,[string]$ModelName="pierce-county-records-classifier-phi2")  
  
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path  
$projectPath = Join-Path $scriptDir "RecordsClassifierGui.csproj"  
$originalLocation = Get-Location  
Push-Location $scriptDir  
  


# Find project file  
if (-not (Test-Path $projectPath)) {  
    $parentDir = Split-Path -Parent $scriptDir  
    $projectPath = Join-Path $parentDir "RecordsClassifierGui\RecordsClassifierGui.csproj"  
    if (-not (Test-Path $projectPath)) {  
        $possibleProjectDir = Get-ChildItem -Path $parentDir -Directory -Filter "RecordsClassifierGui" -Recurse -Depth 2 | Select-Object -First 1  
        if ($possibleProjectDir) { $projectPath = Join-Path $possibleProjectDir.FullName "RecordsClassifierGui.csproj" }  
        if (-not (Test-Path $projectPath)) { Write-Error "Cannot find RecordsClassifierGui.csproj"; Pop-Location; exit 1 }  
    }  
}  
  
# Model import only mode  
if ($ImportModelOnly) {  
    $modelfilePath = @(  
        (Join-Path $scriptDir "Modelfile"),  
        (Join-Path (Split-Path -Parent $scriptDir) "Modelfile"),  
        (Join-Path (Split-Path -Parent $scriptDir) "Modelfile-phi2"),  
        (Join-Path (Split-Path -Parent (Split-Path -Parent $scriptDir)) "Modelfile")  
    ) | Where-Object { Test-Path $_ } | Select-Object -First 1  
      
    if (-not $modelfilePath) { Write-Error "Modelfile not found"; Pop-Location; exit 1 }  
    if (-not (Get-Command ollama -EA SilentlyContinue)) { Write-Error "Ollama not found"; Pop-Location; exit 1 }  
      
    try {  
        ollama import $ModelName $modelfilePath | Out-Null  
        if ($LASTEXITCODE -ne 0) { throw "Ollama import failed" }  
        if (-not (ollama list | Where-Object { $_ -like "*$ModelName*" })) { Write-Warning "Model may not be properly imported" }  
    } catch { Write-Error "Failed to import model: $_"; Pop-Location; exit 1 }  
    Pop-Location; exit 0  
}  
  
# Check requirements  
try { $dotnetVersion = dotnet --version } catch { Write-Error ".NET SDK not found"; exit 1 }  
if (-not (Get-Command python -EA SilentlyContinue)) { winget install -e --id Python.Python.3 }  
if (-not (Get-Command ollama -EA SilentlyContinue)) { winget install -e --id Ollama.Ollama }  
if (-not (Get-Process -Name "ollama" -EA SilentlyContinue)) { Start-Process ollama -ArgumentList "serve" -WindowStyle Hidden; Start-Sleep 5 }  
  
# Build application  
dotnet publish -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true  
$publishPath = ".\bin\Release\net8.0-windows\win-x64\publish"  
$exePath = "$publishPath\RecordsClassifierGui.exe"  
if (-not (Test-Path $exePath)) { Write-Error "Build failed"; exit 1 }  
  
# Copy models  
@(  
    @("..\models\gemma3:1b", "$publishPath\models\gemma3:1b"),  
    @("..\pierce-county-records-classifier-gemma3", "$publishPath\pierce-county-records-classifier-gemma3")  
) | ForEach-Object { if (Test-Path $_[0]) { Copy-Item -Path $_[0] -Destination $_[1] -Recurse -Force } }  
  
# Create ZIP if requested  
if ($CreateZip) {  
    $zipPath = ".\RecordsClassifierTool.zip"  
    if (Test-Path $zipPath) { Remove-Item $zipPath -Force }  
    Add-Type -AssemblyName System.IO.Compression.FileSystem  
    [System.IO.Compression.ZipFile]::CreateFromDirectory($publishPath, $zipPath)  
}  
  
# Network copy if specified  
if ($NetworkSharePath -and (Test-Path $NetworkSharePath)) { Copy-Item $exePath -Destination $NetworkSharePath }  
  
# Launch application  
if (Test-Path $exePath) { Start-Process -FilePath $exePath } else { Write-Error "Cannot find executable" }  
  
Write-Host "Deployment completed!" -ForegroundColor Green  
# TODO: unsure if file is needed since this is not .net. error: C:\Program Files\dotnet\sdk\8.0.408\NuGet.targets(465,5): error MSB3202: The project file "N:\IT Ops\Product_Support_Documentation\M365 Administration\Records\RecordsClassifierGui\RecordsClassifierGui.csproj" was not found. [N:\IT Ops\Product_Support_Documentation\M365 Administration\Records\Records.sln]

param(
    # invalid syntax: param([switch]$CreateZip = $false, [string]$NetworkSharePath = $null, [switch]$ImportModelOnly = $false, [string]$ModelName = "pierce-county-records-classifier-phi2")
    # This doesnt seem to be a function, so it should be fine to use param() instead of function param()
    [switch]$CreateZip = $false,
    [string]$NetworkSharePath = $null,
    [switch]$ImportModelOnly = $false,
    [string]$ModelName = "pierce-county-records-classifier-phi2"
)

# Get the directory where this script is located - more reliable than relying on current directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectPath = Join-Path $scriptDir "RecordsClassifierGui.csproj"

# Save original location so we can return to it
$originalLocation = Get-Location
Push-Location $scriptDir

# Verify we're in the right directory or have the right path
if (-not (Test-Path $projectPath)) {
    # Try to find it in parent directory for model import scenario
    $parentDir = Split-Path -Parent $scriptDir
    $projectPath = Join-Path $parentDir "RecordsClassifierGui\RecordsClassifierGui.csproj"
    
    # If still not found, try looking in parent folders
    if (-not (Test-Path $projectPath)) {
        # Try to find RecordsClassifierGui folder anywhere in parent path
        $parentDir = Split-Path -Parent $scriptDir
        $possibleProjectDir = Get-ChildItem -Path $parentDir -Directory -Filter "RecordsClassifierGui" -Recurse -Depth 2 | Select-Object -First 1
        
        if ($possibleProjectDir) {
            $projectPath = Join-Path $possibleProjectDir.FullName "RecordsClassifierGui.csproj"
        }
        
        if (-not (Test-Path $projectPath)) {
            Write-Error "Cannot find RecordsClassifierGui.csproj. Script cannot continue."
            Pop-Location
            exit 1
        }
    }
}

# If we're only importing the model, do that and exit
if ($ImportModelOnly) {
    Write-Output "Starting model import process for $ModelName..."
    
    # Look for Modelfile in multiple locations with absolute paths
    $possiblePaths = @(
        (Join-Path $scriptDir "Modelfile"),                                      # Same directory
        (Join-Path (Split-Path -Parent $scriptDir) "Modelfile"),                 # Parent directory
        (Join-Path (Split-Path -Parent $scriptDir) "Modelfile-phi2"),            # Parent directory with variant name
        (Join-Path (Split-Path -Parent (Split-Path -Parent $scriptDir)) "Modelfile") # Grandparent directory
    )
    
    $modelfilePath = $null
    foreach ($path in $possiblePaths) {
        if (Test-Path $path) {
            $modelfilePath = $path
            break
        }
    }
    
    if (-not $modelfilePath) {
        Write-Error "Modelfile not found in any of the expected locations"
        Pop-Location # Return to original directory
        exit 1
    }
    
    Write-Output "Found Modelfile at: $modelfilePath"
    
    # Check if ollama is installed
    if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
        Write-Error "Ollama not found. Please install Ollama first."
        Pop-Location # Return to original directory
        exit 1
    }
    
    # Import the model using ollama with absolute path
    Write-Output "Importing $ModelName model..."
    try {
        $result = ollama import $ModelName $modelfilePath
        if ($LASTEXITCODE -ne 0) {
            throw "Ollama import failed with exit code $LASTEXITCODE"
        }
        
        Write-Output "Model import complete."
        
        # Verify model is available
        $modelCheck = ollama list | Where-Object { $_ -like "*$ModelName*" }
        if ($modelCheck) {
            Write-Output "Model $ModelName successfully verified in Ollama."
        } else {
            Write-Warning "Model may not have been properly imported. Please check 'ollama list' output."
        }
    }
    catch {
        Write-Error "Failed to import model: $_"
        Pop-Location # Return to original directory
        exit 1
    }
    
    Pop-Location # Return to original directory
    exit 0
}

# Check for .NET SDK
try {
    $dotnetVersion = dotnet --version
    Write-Host "Using .NET SDK version: $dotnetVersion" -ForegroundColor Cyan
}
catch {
    Write-Error ".NET SDK not found. Please install .NET SDK 8.0 or newer."
    exit 1
}

# Ensure Python 3 is installed
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python not found. Installing Python 3..." -ForegroundColor Yellow
    winget install -e --id Python.Python.3
}

# Ensure Ollama CLI is installed
#TODO host model on internall server so local host connection can be established
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    Write-Host "Ollama CLI not found. Installing Ollama..." -ForegroundColor Yellow
    winget install -e --id Ollama.Ollama
}

# --- Ollama model import automation for seamless deployment ---
# Add this to your Deploy.ps1 to ensure the model is available automatically

# Ensure Ollama is installed and running
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    Write-Error 'Ollama is not installed. Please install Ollama before running this deployment.'
    exit 1
}

# Start Ollama service if not running
if (-not (Get-Process -Name "ollama" -ErrorAction SilentlyContinue)) {
    Start-Process ollama -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 5
}

# Import the custom model (adjust path if needed)
$ModelPath = Join-Path $PSScriptRoot '..\pierce-county-records-classifier-gemma3\4b'
ollama run import $ModelPath

# Optionally verify model is available
ollama list | Select-String "pierce-county-records-classifier-gemma3:4b"

# Build the application
Write-Host "Building Records Classification Tool..." -ForegroundColor Green
dotnet publish -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true

# Check if build succeeded
$publishPath = ".\bin\Release\net8.0-windows\win-x64\publish"
$exePath = "$publishPath\RecordsClassifierGui.exe"

if (-not (Test-Path $exePath)) {
    Write-Error "Build failed. Executable not found."
    exit 1
}

$fileInfo = Get-Item $exePath
Write-Host "Build successful! Created: $exePath ($([Math]::Round($fileInfo.Length / 1MB, 2)) MB)" -ForegroundColor Green

# Bundle local gemma3:1b model files to avoid external downloads
$localModelSource = "..\models\gemma3:1b"
$destModelPath = "$publishPath\models\gemma3:1b"
if (Test-Path $localModelSource) {
    Write-Host "Copying local gemma3:1b model to distribution package..." -ForegroundColor Green
    Copy-Item -Path $localModelSource -Destination $destModelPath -Recurse -Force
}

# Bundle local pierce-county-records-classifier-gemma3:4b model files for distribution
$localModelSource = "..\pierce-county-records-classifier-gemma3"
$destModelPath = "$publishPath\pierce-county-records-classifier-gemma3"
if (Test-Path $localModelSource) {
    Write-Host "Copying local pierce-county-records-classifier-gemma3 model to distribution package..." -ForegroundColor Green
    Copy-Item -Path $localModelSource -Destination $destModelPath -Recurse -Force
}

# Create ZIP package if requested
if ($CreateZip) {
    Write-Host "Creating ZIP package..." -ForegroundColor Green
    $zipPath = ".\RecordsClassifierTool.zip"
    
    if (Test-Path $zipPath) {
        Remove-Item $zipPath -Force
    }
    
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::CreateFromDirectory($publishPath, $zipPath)
    
    Write-Host "ZIP package created: $zipPath" -ForegroundColor Green
}

# Copy to network share if specified
if ($NetworkSharePath) {
    if (Test-Path $NetworkSharePath) {
        Write-Host "Copying to network share: $NetworkSharePath" -ForegroundColor Green
        Copy-Item $exePath -Destination $NetworkSharePath
        Write-Host "Copy completed successfully!" -ForegroundColor Green
    }
    else {
        Write-Error "Network share not found: $NetworkSharePath"
    }
}

# Uninstall logic: Remove model directory on uninstall
function Uninstall-RecordsClassifier {
    $exePath = "$publishPath\RecordsClassifierGui.exe"
    $modelPath = "$publishPath\pierce-county-records-classifier-gemma3"
    if (Test-Path $exePath) {
        Remove-Item $exePath -Force
        Write-Host "Removed executable."
    }
    if (Test-Path $modelPath) {
        Remove-Item $modelPath -Recurse -Force
        Write-Host "Removed model files."
    }
    Write-Host "Uninstall complete."
}

# Automatically launch the executable after deployment
$exePath = "$publishPath\RecordsClassifierGui.exe"
if (Test-Path $exePath) {
    Write-Host "Launching application..." -ForegroundColor Green
    Start-Process -FilePath $exePath
} else {
    Write-Error "Cannot find executable to run: $exePath"
}

Write-Host "`nDeployment completed!" -ForegroundColor Green
Write-Host "You can now distribute RecordsClassifierGui.exe to users."
