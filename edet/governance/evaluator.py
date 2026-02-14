"""Governance & Sensitivity Layer: PII, sensitive patterns, risk classification."""

from __future__ import annotations

import re
import pandas as pd

from edet.models.profile import DatasetProfile
from edet.models.scores import GovernanceResult, SensitivityLevel


# Regex patterns for PII and sensitive data
PII_PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "phone_us": re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "credit_card": re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),
    "iban": re.compile(r"\b[A-Z]{2}\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{0,4}\b"),
    "ip_address": re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
}

# Column name hints for high-risk attributes
SENSITIVE_NAME_PATTERNS = [
    r"password", r"passwd", r"pwd", r"secret", r"token", r"api_key",
    r"ssn", r"social", r"tax_id", r"nin", r"dob", r"birth_date",
    r"salary", r"income", r"bank_account", r"credit_card", r"cvv",
    r"email", r"phone", r"address", r"name", r"first_name", r"last_name",
]


def _column_name_risk(col: str) -> list[str]:
    hits = []
    col_lower = col.lower()
    for pat in SENSITIVE_NAME_PATTERNS:
        if re.search(pat, col_lower):
            hits.append(f"name:{pat}")
    return hits


def _detect_patterns_in_series(s: pd.Series) -> list[str]:
    found = []
    sample = s.dropna().astype(str).head(1000)
    for name, pattern in PII_PATTERNS.items():
        if sample.str.contains(pattern, regex=True).any():
            found.append(name)
    return found


def evaluate_governance(profile: DatasetProfile) -> GovernanceResult:
    """
    Assess governance and sensitivity: PII detection, sensitive patterns,
    identifier exposure, high-risk attribute classification.
    """
    df = profile.df
    sensitive_map: dict[str, list[str]] = {}
    risk_flags: list[str] = []
    max_risk = 0.0
    n_cols = len(df.columns)
    n_rows = len(df)

    for col in df.columns:
        reasons: list[str] = []
        # Name-based
        name_risks = _column_name_risk(col)
        reasons.extend(name_risks)
        # Pattern-based (sample for speed)
        if df[col].dtype == object or str(df[col].dtype) == "string":
            pattern_risks = _detect_patterns_in_series(df[col])
            reasons.extend(pattern_risks)
        if reasons:
            sensitive_map[col] = list(set(reasons))
            if any("password" in r or "secret" in r or "token" in r for r in reasons):
                max_risk = max(max_risk, 1.0)
            elif any("ssn" in r or "credit_card" in r or "salary" in r for r in reasons):
                max_risk = max(max_risk, 0.9)
            elif any("email" in r or "phone" in r for r in reasons):
                max_risk = max(max_risk, 0.7)

    # Absence of unique key (from structural we could pass candidate PKs; here we just note)
    if n_rows > 0:
        has_unique = any(df[c].nunique() == n_rows for c in df.columns)
        if not has_unique and n_cols > 0:
            risk_flags.append("No obvious unique identifier; re-identification risk")

    # Governance risk score: higher = more risk (invert for "good" interpretation in heatmap we use 1 - x)
    num_sensitive = len(sensitive_map)
    if num_sensitive > 0:
        governance_risk = min(1.0, 0.3 + 0.2 * num_sensitive + max_risk * 0.5)
    else:
        governance_risk = 0.1  # baseline low risk
    governance_risk = min(1.0, governance_risk)

    # Sensitivity classification
    if max_risk >= 0.9 or num_sensitive >= 5:
        sensitivity_classification = SensitivityLevel.HIGH
    elif max_risk >= 0.5 or num_sensitive >= 2:
        sensitivity_classification = SensitivityLevel.MODERATE
    else:
        sensitivity_classification = SensitivityLevel.LOW

    for col, reasons in sensitive_map.items():
        risk_flags.append(f"Sensitive column '{col}': {', '.join(set(reasons))}")

    return GovernanceResult(
        governance_risk_score=round(governance_risk, 4),
        sensitivity_classification=sensitivity_classification,
        sensitive_column_map=sensitive_map,
        risk_flags=risk_flags[:50],
    )
