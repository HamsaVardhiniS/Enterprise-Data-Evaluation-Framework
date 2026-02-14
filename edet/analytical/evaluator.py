"""Analytical Utility & Preparation: variance, entropy, skew, VIF, anomaly density."""

from __future__ import annotations

import pandas as pd
import numpy as np
from scipy import stats

from edet.models.profile import DatasetProfile
from edet.models.scores import AnalyticalResult

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


def _vif(df: pd.DataFrame) -> dict[str, float]:
    """Variance inflation factor for numeric columns."""
    num = df.select_dtypes(include=[np.number]).dropna(axis=1, how="all")
    if num.shape[1] < 2:
        return {}
    from numpy.linalg import LinAlgError
    vifs = {}
    for i, col in enumerate(num.columns):
        try:
            y = num.iloc[:, i]
            X = num.drop(columns=[col])
            X = X.loc[:, X.std() > 0]
            if X.shape[1] == 0:
                continue
            from sklearn.linear_model import LinearRegression
            r2 = LinearRegression().fit(X, y).score(X, y)
            vif = 1 / (1 - r2) if r2 < 1 else np.inf
            vifs[col] = vif
        except (LinAlgError, ValueError):
            continue
    return vifs


def evaluate_analytical(profile: DatasetProfile) -> AnalyticalResult:
    """
    Evaluate modeling readiness: variance, entropy, skewness, outliers,
    multicollinearity (VIF), optional anomaly density, missing burden.
    """
    df = profile.df
    n_rows, n_cols = df.shape
    low_var: list[str] = []
    high_skew: list[str] = []
    high_vif: list[str] = []
    utility_score = 1.0
    prep_complexity = 0.0
    anomaly_density: float | None = None

    numeric = df.select_dtypes(include=[np.number])
    if numeric.empty:
        return AnalyticalResult(
            analytics_utility_score=0.5,
            preparation_complexity_score=0.5,
            low_variance_columns=[],
            high_skew_columns=[],
            high_vif_columns=[],
            anomaly_density=None,
        )

    # Variance sufficiency
    for c in numeric.columns:
        std = numeric[c].std()
        if std == 0 or (std < 1e-10 and numeric[c].abs().max() > 1e-10):
            low_var.append(c)
        elif numeric[c].std() < numeric[c].mean() * 0.01 and numeric[c].mean() != 0:
            low_var.append(c)
    if low_var:
        utility_score -= 0.1 * min(len(low_var), 5)
        prep_complexity += 0.1 * len(low_var)

    # Skewness
    for c in numeric.columns:
        if c in low_var:
            continue
        sk = stats.skew(numeric[c].dropna())
        if abs(sk) > 2:
            high_skew.append(c)
    if high_skew:
        utility_score -= 0.05 * min(len(high_skew), 4)
        prep_complexity += 0.05 * len(high_skew)

    # Categorical entropy (diversity)
    obj = df.select_dtypes(include=["object", "string"])
    for c in obj.columns:
        vc = df[c].value_counts(normalize=True)
        ent = -np.sum(vc * np.log2(vc + 1e-10))
        max_ent = np.log2(len(vc)) if len(vc) > 1 else 1
        if max_ent > 0 and ent / max_ent < 0.1:
            prep_complexity += 0.05  # low diversity

    # Multicollinearity (VIF)
    try:
        vifs = _vif(df)
        for col, v in vifs.items():
            if v > 10:
                high_vif.append(col)
        if high_vif:
            utility_score -= 0.1 * min(len(high_vif), 3)
            prep_complexity += 0.1 * len(high_vif)
    except Exception:
        pass

    # Missing burden
    missing_ratio = df.isna().sum().sum() / (n_rows * n_cols) if (n_rows * n_cols) > 0 else 0
    prep_complexity += missing_ratio * 0.5

    # Optional: Isolation Forest anomaly density
    if HAS_SKLEARN and numeric.shape[0] > 10 and numeric.shape[1] >= 1:
        try:
            X = numeric.fillna(numeric.median())
            X = StandardScaler().fit_transform(X)
            iso = IsolationForest(random_state=42, contamination=0.1).fit(X)
            pred = iso.predict(X)
            anomaly_density = (pred == -1).sum() / len(pred)
        except Exception:
            pass

    utility_score = max(0.0, min(1.0, utility_score))
    prep_complexity = min(1.0, prep_complexity)
    return AnalyticalResult(
        analytics_utility_score=round(utility_score, 4),
        preparation_complexity_score=round(prep_complexity, 4),
        low_variance_columns=low_var,
        high_skew_columns=high_skew,
        high_vif_columns=high_vif,
        anomaly_density=round(anomaly_density, 4) if anomaly_density is not None else None,
    )
