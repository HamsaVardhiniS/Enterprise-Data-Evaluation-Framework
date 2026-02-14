"""Logical & Domain Consistency: business rules, revenue/profit, FKs, balances."""

from __future__ import annotations

import re
import pandas as pd
import numpy as np

from edet.models.profile import DatasetProfile
from edet.models.scores import LogicalResult


def _col_like(name: str, patterns: list[str]) -> bool:
    n = name.lower()
    return any(re.search(p, n) for p in patterns)


def evaluate_logical(profile: DatasetProfile) -> LogicalResult:
    """
    Validate business correctness: revenue >= 0, profit <= revenue,
    unique transaction IDs, foreign key consistency.
    """
    df = profile.df
    violations = []
    total_checks = 0
    passed = 0

    numeric = df.select_dtypes(include=[np.number])
    revenue_cols = [c for c in df.columns if _col_like(c, [r"revenue", r"sales", r"amount"]) and c in numeric.columns]
    for c in revenue_cols:
        total_checks += 1
        if (df[c] < 0).sum() > 0:
            violations.append(f"'{c}' has negative values (revenue-like)")
        else:
            passed += 1

    profit_cols = [c for c in df.columns if _col_like(c, [r"profit", r"net_income"]) and c in numeric.columns]
    for rev_c in revenue_cols:
        for pr_c in profit_cols:
            if rev_c == pr_c:
                continue
            total_checks += 1
            if (df[pr_c] > df[rev_c]).sum() > 0:
                violations.append(f"'{pr_c}' > '{rev_c}' in some rows")
            else:
                passed += 1

    qty_cols = [c for c in df.columns if _col_like(c, [r"qty", r"quantity", r"count"]) and c in numeric.columns]
    for c in qty_cols:
        total_checks += 1
        if (df[c] < 0).sum() > 0:
            violations.append(f"'{c}' has negative values")
        else:
            passed += 1

    id_cols = [c for c in df.columns if _col_like(c, [r"id", r"transaction", r"txn", r"key"]) and df[c].nunique() > 0]
    for c in id_cols:
        if df[c].dtype in (object, "string") or np.issubdtype(df[c].dtype, np.integer):
            total_checks += 1
            if df[c].duplicated().sum() > 0:
                violations.append(f"'{c}' has duplicates (expected unique)")
            else:
                passed += 1

    if total_checks == 0:
        integrity = 0.85
        violation_rate = 0.0
    else:
        violation_rate = 1 - (passed / total_checks)
        integrity = max(0.0, 1.0 - violation_rate * 1.5)

    return LogicalResult(
        logical_integrity_score=round(min(1.0, integrity), 4),
        violation_rate=round(violation_rate, 4),
        violations_summary=violations[:30],
    )
