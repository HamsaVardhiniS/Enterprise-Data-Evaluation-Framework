"""Structural Reliability Layer: schema, missing, duplicates, redundancy."""

from __future__ import annotations

import pandas as pd
import numpy as np

from edet.models.profile import DatasetProfile
from edet.models.scores import StructuralResult


def evaluate_structural(profile: DatasetProfile) -> StructuralResult:
    """
    Evaluate structural reliability: completeness, missing density,
    duplicates, identifier uniqueness, constant columns, correlation redundancy,
    type inconsistency.
    """
    df = profile.df
    n_rows, n_cols = df.shape
    flags: list[str] = []
    redundant: list[str] = []
    candidate_pks: list[str] = []

    # --- Schema completeness ---
    empty_cols = [c for c in df.columns if df[c].isna().all()]
    if empty_cols:
        flags.append(f"Empty columns: {len(empty_cols)} ({', '.join(empty_cols[:5])}{'...' if len(empty_cols) > 5 else ''})")

    # --- Missing value density (per column then overall) ---
    missing_ratio = df.isna().sum().sum() / (n_rows * n_cols) if (n_rows * n_cols) > 0 else 0.0
    if missing_ratio > 0.3:
        flags.append(f"High missing value density: {missing_ratio:.1%}")
    elif missing_ratio > 0.1:
        flags.append(f"Moderate missing value density: {missing_ratio:.1%}")

    # --- Duplicate rows ---
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        pct = dup_count / n_rows if n_rows else 0
        flags.append(f"Duplicate rows: {dup_count} ({pct:.1%})")

    # --- Identifier uniqueness & candidate primary keys ---
    for col in df.columns:
        if df[col].dtype in ("object", "string", "int64", "int32") or "int" in str(df[col].dtype):
            uniq = df[col].nunique()
            if uniq == n_rows and n_rows > 0 and df[col].notna().all():
                candidate_pks.append(col)
            if uniq == 1 and n_rows > 1:
                redundant.append(col)
                flags.append(f"Constant column: {col}")

    # --- Near-constant (e.g. >95% one value) ---
    for col in df.columns:
        if col in redundant:
            continue
        vc = df[col].value_counts(dropna=False)
        if len(vc) > 0 and vc.iloc[0] / n_rows >= 0.95 and n_rows > 10:
            redundant.append(col)
            flags.append(f"Near-constant column: {col} ({vc.index[0]})")

    # --- Correlation redundancy (highly correlated numeric pairs) ---
    num_df = df.select_dtypes(include=[np.number])
    if num_df.shape[1] >= 2:
        corr = num_df.corr().abs()
        np.fill_diagonal(corr.values, 0)
        for i, c1 in enumerate(num_df.columns):
            for j, c2 in enumerate(num_df.columns):
                if i < j and corr.iloc[i, j] > 0.95:
                    redundant.append(c1)
                    redundant.append(c2)
                    flags.append(f"High correlation redundancy: {c1} ~ {c2} (r={corr.iloc[i, j]:.2f})")
    redundant = list(dict.fromkeys(redundant))  # deduplicate while preserving order

    # --- Type inconsistency (mixed types in object columns) ---
    for col in df.select_dtypes(include=["object"]).columns:
        non_null = df[col].dropna().astype(str)
        if len(non_null) == 0:
            continue
        # Check if column has mixed numeric/non-numeric
        def looks_numeric(s):
            try:
                float(s.replace(",", ""))
                return True
            except (ValueError, TypeError):
                return False
        num_like = non_null.apply(looks_numeric)
        if 0 < num_like.sum() < len(non_null):
            flags.append(f"Type inconsistency in column: {col} (mixed numeric/text)")

    # --- Structural Integrity Score (0–1) ---
    score = 1.0
    if missing_ratio > 0.5:
        score -= 0.35
    elif missing_ratio > 0.2:
        score -= 0.2
    elif missing_ratio > 0.05:
        score -= 0.1
    if dup_count / max(n_rows, 1) > 0.1:
        score -= 0.2
    elif dup_count > 0:
        score -= 0.1
    if len(empty_cols) > 0:
        score -= 0.1 * min(len(empty_cols), 3)
    if len(redundant) > n_cols * 0.3:
        score -= 0.15
    score = max(0.0, min(1.0, score))

    return StructuralResult(
        structural_integrity_score=round(score, 4),
        structural_risk_flags=flags,
        redundant_feature_list=redundant,
        candidate_primary_keys=candidate_pks,
    )
