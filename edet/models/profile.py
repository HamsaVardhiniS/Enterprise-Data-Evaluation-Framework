"""Input Layer: Dataset profile and metadata models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass
class InputMetadata:
    """Metadata captured at ingestion (Dataset Profile Object)."""

    file_type: str
    record_count: int
    column_count: int
    data_types: dict[str, str]  # column -> dtype name
    has_timestamp: bool
    has_text: bool
    numeric_density: float  # proportion of numeric columns
    column_names: list[str] = field(default_factory=list)


def build_input_metadata(df: pd.DataFrame, file_type: str = "unknown") -> InputMetadata:
    """Build InputMetadata from a DataFrame."""
    record_count = len(df)
    column_count = len(df.columns)
    data_types = {c: str(df[c].dtype) for c in df.columns}
    numeric_cols = df.select_dtypes(include=["number"]).columns
    numeric_density = len(numeric_cols) / column_count if column_count else 0.0

    def _has_timestamp() -> bool:
        for c in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[c]):
                return True
            s = df[c].dropna().astype(str)
            if s.str.match(r"^\d{4}-\d{2}-\d{2}").any():
                return True
        return False

    def _has_text() -> bool:
        for c in df.columns:
            if df[c].dtype == object or (df[c].dtype.name == "string"):
                return True
        return False

    return InputMetadata(
        file_type=file_type,
        record_count=record_count,
        column_count=column_count,
        data_types=data_types,
        has_timestamp=_has_timestamp(),
        has_text=_has_text(),
        numeric_density=numeric_density,
        column_names=list(df.columns),
    )


@dataclass
class DatasetProfile:
    """Full dataset profile after input layer processing."""

    raw: pd.DataFrame
    metadata: InputMetadata
    # Optional: normalized view for downstream (e.g. parsed dates)
    working_df: pd.DataFrame | None = None

    @property
    def df(self) -> pd.DataFrame:
        return self.working_df if self.working_df is not None else self.raw
