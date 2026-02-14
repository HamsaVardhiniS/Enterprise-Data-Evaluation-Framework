"""Score and result types for all EDET layers."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class SensitivityLevel(str, Enum):
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"


class TrustTier(str, Enum):
    DECISION_READY = "Decision-Ready"       # 0.80 – 1.00
    REVIEW_RECOMMENDED = "Review Recommended"  # 0.60 – 0.79
    RISK_PRESENT = "Risk Present"           # 0.40 – 0.59
    NOT_TRUSTWORTHY = "Not Trustworthy"     # < 0.40


@dataclass
class StructuralResult:
    """Output of Structural Reliability Layer."""

    structural_integrity_score: float  # 0–1
    structural_risk_flags: list[str] = field(default_factory=list)
    redundant_feature_list: list[str] = field(default_factory=list)
    candidate_primary_keys: list[str] = field(default_factory=list)


@dataclass
class GovernanceResult:
    """Output of Governance & Sensitivity Layer."""

    governance_risk_score: float  # higher = more risk
    sensitivity_classification: SensitivityLevel
    sensitive_column_map: dict[str, list[str]] = field(default_factory=dict)  # column -> [pattern types]
    risk_flags: list[str] = field(default_factory=list)


@dataclass
class OperationalResult:
    """Output of Operational & Temporal Stability Layer."""

    temporal_reliability_score: float  # 0–1
    operational_risk_flags: list[str] = field(default_factory=list)
    has_temporal_column: bool = False
    latest_update_lag_days: float | None = None


@dataclass
class LogicalResult:
    """Output of Logical & Domain Consistency Layer."""

    logical_integrity_score: float  # 0–1
    violation_rate: float
    violations_summary: list[str] = field(default_factory=list)


@dataclass
class AnalyticalResult:
    """Output of Analytical Utility & Preparation Layer."""

    analytics_utility_score: float  # 0–1
    preparation_complexity_score: float  # higher = more effort
    low_variance_columns: list[str] = field(default_factory=list)
    high_skew_columns: list[str] = field(default_factory=list)
    high_vif_columns: list[str] = field(default_factory=list)
    anomaly_density: float | None = None


@dataclass
class TrustResult:
    """Output of Strategic Trust Engine — EDTI."""

    edti_score: float  # Enterprise Data Trust Index 0–1
    trust_tier: TrustTier
    component_scores: dict[str, float] = field(default_factory=dict)
    risk_heatmap: dict[str, float] = field(default_factory=dict)  # category -> risk/score
