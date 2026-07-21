$ErrorActionPreference = "Stop"
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw "Python 3.11 or newer is required" }
python scripts/install.py
python -m pip install -r requirements.txt
python scripts/validate_env.py
