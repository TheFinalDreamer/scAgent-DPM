"""System-level utilities: GPU check, disk space, environment validation."""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple


def check_gpu() -> Dict[str, str]:
    """Check GPU availability via nvidia-smi and PyTorch."""
    info: Dict[str, str] = {}
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            info["nvidia_smi"] = result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        info["nvidia_smi"] = "nvidia-smi not available"

    try:
        import torch
        info["torch_cuda_available"] = str(torch.cuda.is_available())
        if torch.cuda.is_available():
            info["torch_cuda_device_count"] = str(torch.cuda.device_count())
            info["torch_cuda_device_name"] = torch.cuda.get_device_name(0)
    except ImportError:
        info["torch_cuda_available"] = "torch not installed"

    return info


def check_disk_space(path: Union[str, Path]) -> Dict[str, str]:
    """Check available disk space."""
    p = Path(path)
    while not p.exists():
        p = p.parent
    usage = shutil.disk_usage(p)
    gb = 1024 ** 3
    return {
        "path": str(p),
        "total_gb": f"{usage.total / gb:.1f}",
        "used_gb": f"{usage.used / gb:.1f}",
        "free_gb": f"{usage.free / gb:.1f}",
    }


def check_conda() -> Optional[str]:
    """Check if conda is available."""
    try:
        result = subprocess.run(["conda", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except FileNotFoundError:
        pass
    return None


def check_python_packages(required: list) -> Dict[str, bool]:
    """Check which packages from a list are importable."""
    status = {}
    for pkg in required:
        try:
            __import__(pkg)
            status[pkg] = True
        except ImportError:
            status[pkg] = False
    return status


def get_python_version() -> str:
    return sys.version


def get_platform() -> str:
    return sys.platform
