# install_ollama.ps1
# Production-ready installer for Ollama and model assets (offline, silent)

$ErrorActionPreference = 'Stop'

# Paths
$OllamaExeSource = Join-Path $PSScriptRoot 'ollama.exe'
$ModelSource = Join-Path $PSScriptRoot 'models'
$UserOllamaDir = Join-Path $env:USERPROFILE '.ollama'
$UserModelsDir = Join-Path $UserOllamaDir 'models'

# Ensure Ollama binary is present
if (-not (Test-Path $OllamaExeSource)) {
    Write-Error 'Ollama binary not found in installer directory.'
    exit 1
}

# Create Ollama directories if missing
New-Item -ItemType Directory -Force -Path $UserModelsDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $UserModelsDir 'manifests') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $UserModelsDir 'blobs') | Out-Null

# Copy Ollama binary to user profile (if not present)
$OllamaExeDest = Join-Path $env:USERPROFILE 'ollama.exe'
if (-not (Test-Path $OllamaExeDest)) {
    Copy-Item $OllamaExeSource $OllamaExeDest -Force
}

# Copy model files
Copy-Item (Join-Path $ModelSource 'manifests\*') (Join-Path $UserModelsDir 'manifests') -Force
Copy-Item (Join-Path $ModelSource 'blobs\*') (Join-Path $UserModelsDir 'blobs') -Force

# Set OLLAMA_MODELS for this user
[Environment]::SetEnvironmentVariable('OLLAMA_MODELS', $UserModelsDir, 'User')

Write-Host 'Ollama and model installed for offline use.'
