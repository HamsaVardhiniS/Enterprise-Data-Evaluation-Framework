"""
Enterprise Data Evaluation & Trust Framework (EDET).

A pre-analytics evaluation system that measures structural reliability,
governance exposure, operational stability, logical integrity, statistical
utility, preparation effort, and strategic decision trust.

Positioned as a Data Trust Gate before ETL / BI / ML pipelines.
"""

__version__ = "1.0.0"

from edet.models.profile import DatasetProfile
from edet.models.scores import (
    StructuralResult,
    GovernanceResult,
    OperationalResult,
    LogicalResult,
    AnalyticalResult,
    TrustResult,
)
from edet.trust_engine import TrustEngine

__all__ = [
    "DatasetProfile",
    "StructuralResult",
    "GovernanceResult",
    "OperationalResult",
    "LogicalResult",
    "AnalyticalResult",
    "TrustResult",
    "TrustEngine",
]
