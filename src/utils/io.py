"""I/O helpers for reading/writing AnnData, CSVs, JSON, and figures."""

import json
import shutil
from pathlib import Path
from typing import Any, Dict, Optional, Union

import anndata as ann
import numpy as np
import pandas as pd
import scanpy as sc


def read_anndata(path: Union[str, Path]) -> ann.AnnData:
    """Read AnnData from h5ad, h5, or loom formats."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in {".h5ad", ".h5"}:
        return sc.read_h5ad(path)
    elif suffix == ".loom":
        return sc.read_loom(path)
    else:
        raise ValueError(f"Unsupported AnnData format: {suffix}")

def write_anndata(adata: ann.AnnData, path: Union[str, Path]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    adata.write_h5ad(path)

def read_csv(path: Union[str, Path], **kwargs) -> pd.DataFrame:
    return pd.read_csv(path, **kwargs)

def write_csv(df: pd.DataFrame, path: Union[str, Path], **kwargs) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=kwargs.pop("index", False), **kwargs)

def read_json(path: Union[str, Path]) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_json(data: Dict[str, Any], path: Union[str, Path]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)

def ensure_dir(path: Union[str, Path]) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p

def copy_file(src: Union[str, Path], dst: Union[str, Path]) -> None:
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

def make_path(*parts: str) -> Path:
    return Path(*parts)
