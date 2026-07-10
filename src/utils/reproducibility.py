"""Reproducibility utilities: seed setting, session info, and checksums."""

import hashlib
import json
import os
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np


def set_seed(seed: int = 42) -> None:
    """Set random seed across numpy, random, and environment."""
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    except ImportError:
        pass


def get_session_info() -> Dict[str, Any]:
    """Collect Python and package version information."""
    info = {
        "timestamp": datetime.now().isoformat(),
        "python_version": sys.version,
        "platform": sys.platform,
    }
    try:
        import session_info
        info["packages"] = session_info.get_session_info()
    except ImportError:
        info["packages"] = "session_info not installed"
    return info


def compute_file_checksum(filepath: Union[str, Path], algorithm: str = "sha256") -> str:
    """Compute checksum of a file."""
    h = hashlib.new(algorithm)
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def save_reproducibility_metadata(
    output_dir: Union[str, Path],
    seed: int,
    config: Optional[Dict[str, Any]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Path:
    """Save reproducibility metadata to a JSON file."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "seed": seed,
        "session_info": get_session_info(),
        "config": config,
        "extra": extra or {},
    }
    path = output_dir / "reproducibility_metadata.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False, default=str)
    return path
