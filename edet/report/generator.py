"""Executive summary and downloadable report generation."""

from __future__ import annotations

from io import StringIO

from edet.models.profile import DatasetProfile
from edet.trust_engine import EvaluationBundle


def generate_executive_summary(
    profile: DatasetProfile,
    bundle: EvaluationBundle,
    title: str = "EDET Executive Summary",
) -> str:
    """Produce a text executive summary suitable for download."""
    out = StringIO()
    m = profile.metadata
    t = bundle.trust
    if not t:
        return "No trust result available."
    out.write(f"{title}\n")
    out.write("=" * 60 + "\n\n")
    out.write("1. Dataset Overview\n")
    out.write(f"   Rows: {m.record_count}, Columns: {m.column_count}\n")
    out.write(f"   File type: {m.file_type}\n")
    out.write(f"   Numeric density: {m.numeric_density:.1%}\n")
    out.write(f"   Has timestamp: {m.has_timestamp}, Has text: {m.has_text}\n\n")
    out.write("2. Enterprise Data Trust Index (EDTI)\n")
    out.write(f"   Score: {t.edti_score:.2f}\n")
    out.write(f"   Tier: {t.trust_tier.value}\n\n")
    out.write("3. Component Scores\n")
    for k, v in t.component_scores.items():
        out.write(f"   {k}: {v:.2f}\n")
    out.write("\n4. Risk Heatmap (higher = more risk)\n")
    for k, v in t.risk_heatmap.items():
        out.write(f"   {k}: {v:.2f}\n")
    out.write("\n5. Structural Reliability\n")
    out.write(f"   Score: {bundle.structural.structural_integrity_score:.2f}\n")
    for f in bundle.structural.structural_risk_flags[:10]:
        out.write(f"   - {f}\n")
    out.write("\n6. Governance & Sensitivity\n")
    out.write(f"   Classification: {bundle.governance.sensitivity_classification.value}\n")
    for f in bundle.governance.risk_flags[:10]:
        out.write(f"   - {f}\n")
    out.write("\n7. Operational Stability\n")
    out.write(f"   Score: {bundle.operational.temporal_reliability_score:.2f}\n")
    for f in bundle.operational.operational_risk_flags[:5]:
        out.write(f"   - {f}\n")
    out.write("\n8. Logical Integrity\n")
    out.write(f"   Score: {bundle.logical.logical_integrity_score:.2f}, Violation rate: {bundle.logical.violation_rate:.2%}\n")
    for v in bundle.logical.violations_summary[:5]:
        out.write(f"   - {v}\n")
    out.write("\n9. Preparation & Analytical Utility\n")
    out.write(f"   Utility: {bundle.analytical.analytics_utility_score:.2f}, Preparation complexity: {bundle.analytical.preparation_complexity_score:.2f}\n")
    out.write("\n--- End of Executive Summary ---\n")
    return out.getvalue()
