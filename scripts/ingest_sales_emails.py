#!/usr/bin/env python3
"""CLI wrapper for the T817_2 sales email intake PoC."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from sales_email_ingest import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
