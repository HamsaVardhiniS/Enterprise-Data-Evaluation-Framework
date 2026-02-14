"""Load structured/semi-structured data into DataFrames."""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

import pandas as pd

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".json", ".txt", ".tsv"}


def load_dataset(
    source: str | Path | BinaryIO,
    file_type: str | None = None,
) -> tuple[pd.DataFrame, str]:
    """
    Load dataset from file path or file-like object.

    Returns:
        (DataFrame, detected_or_given file_type)
    """
    if hasattr(source, "read"):
        return _load_from_fileobj(source, file_type or "unknown")
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS and file_type is None:
        raise ValueError(
            f"Unsupported extension '{ext}'. Supported: {SUPPORTED_EXTENSIONS}"
        )
    ft = file_type or ext.lstrip(".")
    if ext == ".csv" or ft == "csv":
        df = pd.read_csv(path)
    elif ext in (".xlsx", ".xls"):
        df = pd.read_excel(path, engine="openpyxl")
    elif ext == ".json":
        df = pd.read_json(path)
        if df.ndim == 1 or (isinstance(df, pd.DataFrame) and len(df.columns) == 1 and df.iloc[:, 0].apply(lambda x: isinstance(x, dict)).all()):
            df = pd.json_normalize(df.iloc[:, 0].tolist() if len(df.columns) == 1 else df.tolist())
    elif ext in (".txt", ".tsv"):
        df = pd.read_csv(path, sep="\t", on_bad_lines="skip")
    else:
        df = pd.read_csv(path)
    return df, ft


def _load_from_fileobj(fp: BinaryIO, file_type: str) -> tuple[pd.DataFrame, str]:
    """Load from file-like object (e.g. Streamlit upload)."""
    ext = (getattr(fp, "name", "") or "").lower()
    if ext.endswith(".csv"):
        df = pd.read_csv(fp)
        return df, "csv"
    if ext.endswith(".xlsx") or ext.endswith(".xls"):
        df = pd.read_excel(fp, engine="openpyxl")
        return df, "xlsx"
    if ext.endswith(".json"):
        df = pd.read_json(fp)
        if isinstance(df, pd.DataFrame) and len(df.columns) == 1 and df.iloc[:, 0].apply(lambda x: isinstance(x, dict)).any():
            df = pd.json_normalize(df.iloc[:, 0].tolist())
        return df, "json"
    if file_type == "csv":
        df = pd.read_csv(fp)
        return df, "csv"
    if file_type == "json":
        df = pd.read_json(fp)
        return df, "json"
    df = pd.read_csv(fp)
    return df, file_type or "unknown"
