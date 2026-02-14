"""Build DatasetProfile from loaded DataFrame."""

from __future__ import annotations

import pandas as pd

from edet.models.profile import DatasetProfile, InputMetadata, build_input_metadata


def create_profile(df: pd.DataFrame, file_type: str = "unknown") -> DatasetProfile:
    """Create a DatasetProfile (Input Layer output)."""
    metadata = build_input_metadata(df, file_type)
    return DatasetProfile(raw=df, metadata=metadata, working_df=None)
