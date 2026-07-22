$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$CurrentDirectory = (Get-Location).Path
if (-not [string]::Equals($CurrentDirectory, $RepoRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Run this installer from the LEVI repository root. Expected: cd `"$RepoRoot`""
}

foreach ($RequiredPath in @("requirements.txt", ".env.example", "scripts\install.py", "scripts\validate_env.py")) {
    if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot $RequiredPath))) {
        throw "This does not look like the LEVI repository root; missing $RequiredPath"
    }
}

$VenvRoot = Join-Path $RepoRoot ".venv"
$VenvPython = Join-Path $VenvRoot "Scripts\python.exe"
$ActivateScript = Join-Path $VenvRoot "Scripts\Activate.ps1"

if (-not (Test-Path -LiteralPath $VenvPython)) {
    Write-Host "Creating repository-local virtual environment at $VenvRoot"
    $PythonLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($PythonLauncher) {
        & $PythonLauncher.Name -3.11 -m venv $VenvRoot
    } else {
        if ($env:VIRTUAL_ENV -and -not [string]::Equals($env:VIRTUAL_ENV, $VenvRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Another virtual environment is active at $env:VIRTUAL_ENV. Deactivate it, then run this installer again from the LEVI repository root."
        }
        $Python = Get-Command python -ErrorAction SilentlyContinue
        if (-not $Python) { throw "Python 3.11 or newer is required to create .venv" }
        & $Python.Name -m venv $VenvRoot
    }
}

if (-not (Test-Path -LiteralPath $ActivateScript)) {
    throw "Virtual environment creation failed: $ActivateScript was not created"
}

& $ActivateScript
if (-not [string]::Equals($env:VIRTUAL_ENV, $VenvRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Failed to activate the repository-local virtual environment at $VenvRoot"
}

& $VenvPython scripts/install.py
& $VenvPython -m pip install -r requirements.txt
& $VenvPython scripts/validate_env.py

Write-Host "LEVI is installed in $VenvRoot"
Write-Host "For future PowerShell sessions run: .\.venv\Scripts\Activate.ps1"
