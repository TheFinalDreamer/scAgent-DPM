#!/usr/bin/env python
"""Check Python environment and dependencies for scAgent-DPM."""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.system import (
    check_gpu, check_disk_space, check_conda,
    check_python_packages, get_python_version, get_platform,
)


def main():
    print("=" * 60)
    print("  scAgent-DPM Environment Check")
    print("=" * 60)

    print(f"\nPython: {get_python_version()}")
    print(f"Platform: {get_platform()}")

    print("\n--- GPU ---")
    for k, v in check_gpu().items():
        print(f"  {k}: {v}")

    print("\n--- Disk Space ---")
    for k, v in check_disk_space(PROJECT_ROOT).items():
        print(f"  {k}: {v}")

    conda_ver = check_conda()
    print(f"\nConda: {conda_ver or 'not found'}")

    print("\n--- Required Packages ---")
    required = [
        "numpy", "scipy", "pandas", "anndata", "scanpy",
        "sklearn", "matplotlib", "seaborn", "yaml", "h5py",
    ]
    for pkg, ok in check_python_packages(required).items():
        print(f"  {pkg}: {'OK' if ok else 'MISSING'}")

    print("\n--- Optional Packages ---")
    optional = ["torch", "celltypist", "gseapy", "scrublet", "scgpt", "session_info"]
    for pkg, ok in check_python_packages(optional).items():
        print(f"  {pkg}: {'OK' if ok else 'not installed'}")

    print("\nDone.")


if __name__ == "__main__":
    main()
