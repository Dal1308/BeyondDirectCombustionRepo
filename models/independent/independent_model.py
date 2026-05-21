"""
models/independent/independent_model.py

Entry-point script — delegates to the benchmark-driven package.
Replaces the old Brayton+HP cycle model with a pure benchmark exploration.

Usage:
    .venv/bin/python models/independent/independent_model.py
    # or
    .venv/bin/python -c "from models.independent import run_model; run_model()"
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from models.independent import run_model

if __name__ == "__main__":
    run_model()
