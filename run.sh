#!/bin/bash

set -e

#if [ ! -d ".venv" ]; then
#  echo "Virtual environment not found. Creating a new one..."
#  python3 -m venv .venv
#  source .venv/bin/activate
#  pip install -r requirements.txt
#  echo "Done. Launching the program..."
#fi

source .venv/bin/activate
PYTHONPATH=. python src/main.py