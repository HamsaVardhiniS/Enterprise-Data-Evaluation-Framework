"""
Strategic Trust Engine: composite EDTI and trust tier.

Combines Structural, Governance, Operational, Logical, Analytical,
and Preparation Burden into the Enterprise Data Trust Index (EDTI).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from edet.models.scores import (
    TrustResult,
    TrustTier,
    StructuralResult,
    GovernanceResult,
    OperationalResult,
    LogicalResult,
    AnalyticalResult,
)

if TYPE_CHECKING:
    from edet.models.profile import DatasetProfile


@dataclass
class EvaluationBundle:
    """All layer outputs for a single dataset evaluation."""

    structural: StructuralResult
    governance: GovernanceResult
    operational: OperationalResult
    logical: LogicalResult
    analytical: AnalyticalResult
    trust: TrustResult | None = None


def _governance_to_trust_component(gr: GovernanceResult) -> float:
    """Convert governance risk (higher=worse) to trust component (higher=better)."""
    return max(0.0, 1.0 - gr.governance_risk_score)


def _prep_burden_to_component(prep_score: float) -> float:
    """Preparation complexity (higher=more effort) -> trust component (higher=better)."""
    return max(0.0, 1.0 - prep_score)


def compute_edti(
    structural: StructuralResult,
    governance: GovernanceResult,
    operational: OperationalResult,
    logical: LogicalResult,
    analytical: AnalyticalResult,
) -> TrustResult:
    """
    Compute Enterprise Data Trust Index from layer scores.

    Weights (configurable): structural, governance, operational, logical,
    utility, and inverse of preparation burden.
    """
    g_trust = _governance_to_trust_component(governance)
    prep_trust = _prep_burden_to_component(analytical.preparation_complexity_score)

    # Weighted composite; all components 0-1 (higher = better)
    weights = {
        "structural": 0.22,
        "governance": 0.20,
        "operational": 0.18,
        "logical": 0.18,
        "analytical_utility": 0.12,
        "preparation_readiness": 0.10,
    }
    edti = (
        weights["structural"] * structural.structural_integrity_score
        + weights["governance"] * g_trust
        + weights["operational"] * operational.temporal_reliability_score
        + weights["logical"] * logical.logical_integrity_score
        + weights["analytical_utility"] * analytical.analytics_utility_score
        + weights["preparation_readiness"] * prep_trust
    )
    edti = round(max(0.0, min(1.0, edti)), 4)

    if edti >= 0.80:
        tier = TrustTier.DECISION_READY
    elif edti >= 0.60:
        tier = TrustTier.REVIEW_RECOMMENDED
    elif edti >= 0.40:
        tier = TrustTier.RISK_PRESENT
    else:
        tier = TrustTier.NOT_TRUSTWORTHY

    component_scores = {
        "Structural Integrity": structural.structural_integrity_score,
        "Governance (1-risk)": g_trust,
        "Temporal Stability": operational.temporal_reliability_score,
        "Logical Consistency": logical.logical_integrity_score,
        "Analytics Utility": analytical.analytics_utility_score,
        "Preparation Readiness": prep_trust,
    }
    risk_heatmap = {
        "Structural": 1.0 - structural.structural_integrity_score,
        "Governance": governance.governance_risk_score,
        "Operational": 1.0 - operational.temporal_reliability_score,
        "Logical": 1.0 - logical.logical_integrity_score,
        "Analytical": 1.0 - analytical.analytics_utility_score,
        "Preparation Burden": analytical.preparation_complexity_score,
    }
    return TrustResult(
        edti_score=edti,
        trust_tier=tier,
        component_scores=component_scores,
        risk_heatmap=risk_heatmap,
    )


class TrustEngine:
    """
    Orchestrates full EDET pipeline: load -> profile -> evaluate all layers -> EDTI.
    """

    def __init__(self) -> None:
        pass

    def evaluate(self, profile: DatasetProfile) -> EvaluationBundle:
        """Run all layers and compute EDTI. Requires a DatasetProfile from input layer."""
        from edet.structural import evaluate_structural
        from edet.governance import evaluate_governance
        from edet.operational import evaluate_operational
        from edet.logical import evaluate_logical
        from edet.analytical import evaluate_analytical

        structural = evaluate_structural(profile)
        governance = evaluate_governance(profile)
        operational = evaluate_operational(profile)
        logical = evaluate_logical(profile)
        analytical = evaluate_analytical(profile)
        trust = compute_edti(structural, governance, operational, logical, analytical)
        return EvaluationBundle(
            structural=structural,
            governance=governance,
            operational=operational,
            logical=logical,
            analytical=analytical,
            trust=trust,
        )
