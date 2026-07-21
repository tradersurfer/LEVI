#!/usr/bin/env sh
set -eu
python3 scripts/install.py
python3 -m pip install -r requirements.txt
python3 scripts/validate_env.py
