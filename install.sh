#!/usr/bin/env sh
set -eu
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .
echo "Installed. Run: .venv/bin/pealang examples/hello.pea"
