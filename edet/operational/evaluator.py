"""Operational and temporal stability evaluation."""

import pandas as pd
from edet.models.profile import DatasetProfile
from edet.models.scores import OperationalResult


def _find_temporal_column(df):
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            return df[col].dropna()
        try:
            s = df[col].dropna().astype(str)
            if s.str.match(r"^\d{4}-\d{2}-\d{2}").any():
                parsed = pd.to_datetime(df[col], errors="coerce")
                return parsed.dropna()
        except Exception:
            pass
    return None


def evaluate_operational(profile: DatasetProfile) -> OperationalResult:
    df = profile.df
    flags = []
    score = 1.0
    latest_lag_days = None
    ts = _find_temporal_column(df)

    if ts is None or len(ts) == 0:
        return OperationalResult(
            temporal_reliability_score=0.5,
            operational_risk_flags=["No temporal column detected"],
            has_temporal_column=False,
            latest_update_lag_days=None,
        )

    ts = pd.Series(ts).sort_values()
    latest = ts.max()
    now = pd.Timestamp.now()
    latest_lag_days = (now - latest).total_seconds() / 86400
    if latest_lag_days > 365:
        flags.append("Data very stale: over 1 year old")
        score -= 0.4
    elif latest_lag_days > 90:
        flags.append("Data may be stale: over 90 days")
        score -= 0.2
    elif latest_lag_days > 30:
        flags.append("Moderate lag: over 30 days")
        score -= 0.1

    if len(ts) >= 2:
        diffs = ts.diff().dropna()
        if len(diffs) > 0 and diffs.median().total_seconds() > 0:
            gaps = (diffs > 2 * diffs.median()).sum()
            if gaps > 0:
                flags.append("Time gaps detected")
                score -= min(0.2, 0.05 * min(gaps, 4))

    score = max(0.0, min(1.0, score))
    return OperationalResult(
        temporal_reliability_score=round(score, 4),
        operational_risk_flags=flags,
        has_temporal_column=True,
        latest_update_lag_days=round(latest_lag_days, 2) if latest_lag_days is not None else None,
    )
