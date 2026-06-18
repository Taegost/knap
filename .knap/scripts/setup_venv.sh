#!/bin/bash
# One-time setup: create venv and install dependencies
set -e
cd "$(dirname "$0")"
python3 -m venv ../.venv
source ../.venv/bin/activate
pip install -r requirements.txt
echo "Done. Activate with: source .knap/.venv/bin/activate"
