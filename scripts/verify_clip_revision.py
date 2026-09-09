#!/usr/bin/env python3
"""Verify the current public clip package without network or ASR calls."""

import runpy
import sys
from pathlib import Path


def main():
    if not __debug__:
        raise RuntimeError("Do not use -O: the retained input verifiers use assertions")
    root = Path(__file__).resolve().parents[1]
    runpy.run_path(str(root / "results/clip_revision_20260909/verify.py"),
                  run_name="__main__")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, KeyError, OSError, ValueError, RuntimeError) as exc:
        print(f"FAIL corrected clip verification: {exc}", file=sys.stderr)
        raise SystemExit(1)
