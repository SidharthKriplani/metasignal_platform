# MetaSignal Demo Narrative

## Positioning

MetaSignal is a production-simulated experimentation intelligence platform with concrete database rows, JSON evidence, validation reports, and API endpoints.

## Demo Story

The demo shows how an experiment moves from event ingestion to metric governance, quality checks, assignment validation, CUPED evaluation, guardrail-first decisioning, right-censoring, anomaly detection, and API-backed evidence retrieval.

## Walkthrough

### 1. Real event substrate

**Proof:** RetailRocket events are standardized into a parquet substrate with 2.75M rows.

**Artifact:** `data/interim/events_standardized.parquet`

### 2. Quality gates before compute

**Proof:** Data quality checks run before metric computation and can block bad runs.

**Artifact:** `outputs/evidence/data_quality_service_report.json`

### 3. Metric registry and denominator governance

**Proof:** Metric definitions explicitly store numerator, denominator, grain, owner, version, and guardrail fields.

**Artifact:** `outputs/evidence/metric_registry.json`

### 4. Metric conflict detection

**Proof:** Conflicting conversion-rate denominators are detected and documented.

**Artifact:** `outputs/evidence/metric_conflict_report.json`

### 5. Experiment assignment and SRM

**Proof:** Deterministic assignment creates 20k users and validates treatment/control balance.

**Artifact:** `outputs/evidence/srm_check_report.json`

### 6. CUPED readout plus A/A validation

**Proof:** CUPED evaluation produces lift/p-value/variance reduction and A/A validation checks false-positive control.

**Artifact:** `outputs/evidence/cuped_experiment_readout.json`

### 7. Guardrail-first decisioning

**Proof:** A statistically positive primary metric is blocked because refund guardrail breaches tolerance.

**Artifact:** `outputs/evidence/guardrail_decision_report.json`

### 8. Right-censoring and post-launch validation

**Proof:** Delayed guardrails are marked immature/right-censored before final decisioning.

**Artifact:** `outputs/evidence/post_launch_validation_report.json`

### 9. Anomaly detection

**Proof:** DOW-adjusted rolling baseline detects a labeled synthetic metric anomaly.

**Artifact:** `outputs/evidence/anomaly_detection_report.json`

### 10. API layer

**Proof:** FastAPI exposes metrics, experiment readout, data quality, evidence, validation, and resume-signal endpoints.

**Artifact:** `outputs/validation/api_smoke_test_report.json`
