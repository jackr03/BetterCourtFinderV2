#!/bin/bash

set -e

if [ ! -d ".venv" ]; then
  echo "Virtual environment not found. Creating a new one..."
  python3 -m venv .venv
  source .venv/bin/activate

  if command -v uv &> /dev/null; then
    echo "Installing dependencies using uv..."
    uv pip install -r pyproject.toml
  else
    echo "Installing dependencies using pip..."
    pip install .
  fi

  echo "Done. Launching the program..."
fi

source .venv/bin/activate
PYTHONPATH=. python src/main.py