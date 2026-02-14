# Enterprise Data Evaluation & Trust Framework (EDET)

A **pre-analytics evaluation system** that systematically measures structural reliability, governance and sensitivity exposure, operational stability, logical integrity, statistical utility, preparation effort, and strategic decision trust. Positioned as a **Data Trust Gate** before ETL / BI / ML pipelines.

## Core philosophy

Most analytics failures happen *before* modeling, due to unstable schemas, sensitive data leakage, inconsistent logic, poor coverage, high preprocessing burden, and hidden structural risks. This framework answers:

> **Can this dataset be trusted for enterprise decision-making?**

## Capabilities

| Layer | Purpose | Outputs |
|-------|--------|--------|
| **Input** | Ingestion & profiling | Dataset Profile (rows, columns, types, timestamp/text, numeric density) |
| **Structural** | Engineering stability | Structural Integrity Score, risk flags, redundant features, candidate keys |
| **Governance** | Compliance exposure | Governance Risk Score, Sensitivity (Low/Moderate/High), sensitive column map |
| **Operational** | Temporal reliability | Temporal Reliability Score, lag, gaps, volume stability flags |
| **Logical** | Business correctness | Logical Integrity Score, violation rate, domain rule violations |
| **Analytical** | Modeling readiness | Analytics Utility Score, Preparation Complexity, VIF, skew, anomaly density |
| **Trust Engine** | Composite gate | **Enterprise Data Trust Index (EDTI)** and tier |

### EDTI tiers

| EDTI Score | Interpretation |
|------------|----------------|
| 0.80 – 1.00 | **Decision-Ready** |
| 0.60 – 0.79 | **Review Recommended** |
| 0.40 – 0.59 | **Risk Present** |
| < 0.40 | **Not Trustworthy** |

## Quick start

```bash
# Create virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Run the dashboard
streamlit run app.py
```

Upload a CSV, Excel, or JSON file in the sidebar. The dashboard will show:

1. Dataset Overview  
2. Structural Reliability  
3. Governance & Sensitivity  
4. Operational & Temporal Stability  
5. Logical Integrity  
6. Preparation Complexity  
7. Analytical Utility  
8. Enterprise Data Trust Index (EDTI)  
9. Downloadable Executive Summary  

## Project structure

```
edet/
  models/          # DatasetProfile, InputMetadata, score result types
  input_layer/     # Loaders (CSV, Excel, JSON), profiler
  structural/      # Schema, missing, duplicates, redundancy
  governance/      # PII/sensitive patterns, risk classification
  operational/    # Temporal column, lag, gaps, volume
  logical/        # Domain rules (revenue, profit, IDs)
  analytical/     # Variance, skew, VIF, anomaly density
  trust_engine/   # EDTI composite and tier
  report/         # Executive summary generator
app.py            # Streamlit dashboard
requirements.txt
```

## Programmatic use

```python
from edet.input_layer import load_dataset, create_profile
from edet.trust_engine import TrustEngine

df, file_type = load_dataset("path/to/data.csv")
profile = create_profile(df, file_type)
engine = TrustEngine()
bundle = engine.evaluate(profile)

print("EDTI:", bundle.trust.edti_score)
print("Tier:", bundle.trust.trust_tier.value)
```

## Extensibility

The layered design allows future extension to:

- Spark-based distributed profiling  
- Real-time schema drift detection  
- Airflow orchestration  
- Data catalog integration  
- ML-based sensitivity classification  
- Continuous monitoring and data contract enforcement  

## License

Use as needed for enterprise data governance and evaluation.
