"""
EDET Framework — Enterprise Data Evaluation & Trust Dashboard.

A Data Trust Gate before ETL / BI / ML pipelines.
Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO

from edet.input_layer import load_dataset, create_profile
from edet.trust_engine import TrustEngine, EvaluationBundle
from edet.report import generate_executive_summary
from edet.models.scores import TrustTier

st.set_page_config(
    page_title="EDET — Data Trust Framework",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom styling for professional look
st.markdown("""
<style>
    .main-header { font-size: 1.8rem; font-weight: 700; color: #1e3a5f; margin-bottom: 0.5rem; }
    .sub-header { color: #5a7a9a; font-size: 0.95rem; margin-bottom: 1.5rem; }
    .metric-card { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); padding: 1rem 1.25rem; border-radius: 8px; border-left: 4px solid #3b82f6; margin: 0.5rem 0; }
    .tier-ready { color: #059669; font-weight: 600; }
    .tier-review { color: #d97706; font-weight: 600; }
    .tier-risk { color: #dc2626; font-weight: 600; }
    .tier-not { color: #7f1d1d; font-weight: 700; }
    section { margin-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🛡️ Enterprise Data Evaluation & Trust Framework</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Pre-analytics Data Trust Gate — Structural, Governance, Operational, Logical & Analytical Readiness</p>', unsafe_allow_html=True)

# Sidebar: data input
with st.sidebar:
    st.header("Data Input")
    uploaded = st.file_uploader(
        "Upload dataset (CSV, Excel, JSON)",
        type=["csv", "xlsx", "xls", "json", "txt", "tsv"],
    )
    if uploaded:
        try:
            df, file_type = load_dataset(uploaded, file_type=None)
            st.success(f"Loaded: {len(df):,} rows × {len(df.columns)} columns ({file_type})")
        except Exception as e:
            st.error(str(e))
            df = None
            file_type = None
    else:
        df = None
        file_type = None

if df is None:
    st.info("Upload a file from the sidebar to run the EDET evaluation.")
    st.stop()

# Run pipeline
@st.cache_data(show_spinner="Running EDET evaluation...")
def run_edet(_df: pd.DataFrame, _file_type: str):
    profile = create_profile(_df, _file_type)
    engine = TrustEngine()
    return profile, engine.evaluate(profile)

with st.spinner("Evaluating dataset..."):
    profile, bundle = run_edet(df, file_type or "unknown")

t = bundle.trust
if not t:
    st.error("Trust result not available.")
    st.stop()

# Section 1 — Dataset Overview
st.header("1. Dataset Overview")
meta = profile.metadata
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Rows", f"{meta.record_count:,}")
c2.metric("Columns", meta.column_count)
c3.metric("File type", meta.file_type)
c4.metric("Numeric density", f"{meta.numeric_density:.0%}")
c5.metric("Timestamp / Text", f"{meta.has_timestamp} / {meta.has_text}")
with st.expander("Column types"):
    st.dataframe(pd.DataFrame(list(meta.data_types.items()), columns=["Column", "Dtype"]), use_container_width=True)

# Section 8 — Enterprise Trust Index (prominent)
st.header("8. Enterprise Data Trust Index (EDTI)")
tier_class = {
    TrustTier.DECISION_READY: "tier-ready",
    TrustTier.REVIEW_RECOMMENDED: "tier-review",
    TrustTier.RISK_PRESENT: "tier-risk",
    TrustTier.NOT_TRUSTWORTHY: "tier-not",
}.get(t.trust_tier, "")
st.markdown(f'<div class="metric-card"><span style="font-size: 2rem;">{t.edti_score:.2f}</span> — <span class="{tier_class}">{t.trust_tier.value}</span></div>', unsafe_allow_html=True)
st.caption("0.80–1.00 Decision-Ready | 0.60–0.79 Review Recommended | 0.40–0.59 Risk Present | &lt;0.40 Not Trustworthy")

# Risk heatmap
st.subheader("Risk heatmap by category")
fig_heat = go.Figure(data=go.Bar(
    x=list(t.risk_heatmap.keys()),
    y=list(t.risk_heatmap.values()),
    marker_color=px.colors.sequential.Reds[::-1][:6],
))
fig_heat.update_layout(
    xaxis_title="Category",
    yaxis_title="Risk (0–1)",
    template="plotly_white",
    height=320,
    margin=dict(t=20, b=40),
)
st.plotly_chart(fig_heat, use_container_width=True)

# Section 2 — Structural Reliability
st.header("2. Structural Reliability")
sr = bundle.structural
st.metric("Structural Integrity Score", f"{sr.structural_integrity_score:.2f}")
col1, col2 = st.columns(2)
with col1:
    st.write("**Risk flags**")
    for f in sr.structural_risk_flags[:15]:
        st.write(f"• {f}")
with col2:
    st.write("**Redundant features**")
    st.write(", ".join(sr.redundant_feature_list[:15]) or "—")
    st.write("**Candidate primary keys**")
    st.write(", ".join(sr.candidate_primary_keys[:10]) or "—")

# Section 3 — Governance & Sensitivity
st.header("3. Governance & Sensitivity")
gr = bundle.governance
st.metric("Governance Risk Score", f"{gr.governance_risk_score:.2f}")
st.metric("Sensitivity Classification", gr.sensitivity_classification.value)
if gr.sensitive_column_map:
    st.write("**Sensitive column map**")
    st.json(gr.sensitive_column_map)
st.write("**Risk flags**")
for f in gr.risk_flags[:15]:
    st.write(f"• {f}")

# Section 4 — Operational Stability
st.header("4. Operational & Temporal Stability")
op = bundle.operational
st.metric("Temporal Reliability Score", f"{op.temporal_reliability_score:.2f}")
st.write("Has temporal column:", op.has_temporal_column)
if op.latest_update_lag_days is not None:
    st.write("Latest update lag (days):", op.latest_update_lag_days)
for f in op.operational_risk_flags:
    st.write(f"• {f}")

# Section 5 — Logical Integrity
st.header("5. Logical & Domain Consistency")
lr = bundle.logical
st.metric("Logical Integrity Score", f"{lr.logical_integrity_score:.2f}")
st.metric("Violation rate", f"{lr.violation_rate:.1%}")
for v in lr.violations_summary[:15]:
    st.write(f"• {v}")

# Section 6 — Preparation Complexity
st.header("6. Preparation Complexity")
ar = bundle.analytical
st.metric("Preparation Complexity Score", f"{ar.preparation_complexity_score:.2f}")
st.write("Low variance columns:", ", ".join(ar.low_variance_columns[:10]) or "—")
st.write("High skew:", ", ".join(ar.high_skew_columns[:10]) or "—")
st.write("High VIF (multicollinearity):", ", ".join(ar.high_vif_columns[:10]) or "—")
if ar.anomaly_density is not None:
    st.write("Anomaly density (Isolation Forest):", f"{ar.anomaly_density:.2%}")

# Section 7 — Analytical Utility
st.header("7. Analytical Utility")
st.metric("Analytics Utility Score", f"{ar.analytics_utility_score:.2f}")

# Component scores chart
st.subheader("Component scores (trust breakdown)")
fig_comp = go.Figure(data=go.Bar(
    x=list(t.component_scores.keys()),
    y=list(t.component_scores.values()),
    marker_color="#3b82f6",
))
fig_comp.update_layout(
    xaxis_tickangle=-45,
    yaxis_range=[0, 1.05],
    template="plotly_white",
    height=320,
    margin=dict(t=20, b=80),
)
st.plotly_chart(fig_comp, use_container_width=True)

# Downloadable Executive Summary
st.header("Download Executive Summary")
summary_text = generate_executive_summary(profile, bundle)
st.download_button(
    label="Download Executive Summary (TXT)",
    data=summary_text,
    file_name="edet_executive_summary.txt",
    mime="text/plain",
)
