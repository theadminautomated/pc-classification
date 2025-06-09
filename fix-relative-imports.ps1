# PowerShell script: fix-relative-imports.ps1
# Run from the root of your repo (where RecordsClassifierGui\ lives)

$Package = 'RecordsClassifierGui'

# Handle "from ..subpkg import foo" → "from RecordsClassifierGui.subpkg import foo"
Get-ChildItem -Path C:\Users\jtaylo7\Downloads\Pierce-County-Records-Classification-main\Pierce-County-Records-Classification-main\RecordsClassifierGui\ -Recurse -Filter *.py | ForEach-Object {
    (Get-Content $_.FullName) -replace 'from\s+\.\.([a-zA-Z0-9_\.]*)', "from $Package.`$1" | Set-Content $_.FullName
}

# Handle "from .subpkg import foo" → "from RecordsClassifierGui.subpkg import foo"
Get-ChildItem -Path C:\Users\jtaylo7\Downloads\Pierce-County-Records-Classification-main\Pierce-County-Records-Classification-main\RecordsClassifierGui\ -Recurse -Filter *.py | ForEach-Object {
    (Get-Content $_.FullName) -replace 'from\s+\.\b', "from $Package." | Set-Content $_.FullName
}

Write-Host "Relative imports replaced with absolute imports in all Python files under RecordsClassifierGui\"
