# MetaSignal

**Production-simulated experimentation, metrics intelligence, and streaming observability platform.**

<p>
  <a href="https://sidharthkriplani.github.io/metasignal_platform/"><img alt="Live Dashboard" src="https://img.shields.io/badge/Live%20Dashboard-GitHub%20Pages-2ea44f?style=for-the-badge&logo=githubpages&logoColor=white"></a>
  <img alt="PRD Status" src="https://img.shields.io/badge/PRD%20Core-PASS-brightgreen?style=for-the-badge">
  <img alt="Experimentation" src="https://img.shields.io/badge/Experimentation-CUPED%20%2B%20Guardrails-2563eb?style=for-the-badge">
  <img alt="Decision System" src="https://img.shields.io/badge/Decision%20System-Auditable-7c3aed?style=for-the-badge">
  <img alt="Streaming" src="https://img.shields.io/badge/Streaming-Provisional%20Early%20Warning-f59e0b?style=for-the-badge">
</p>

<p>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11-3776ab?style=flat-square&logo=python&logoColor=white">
  <img alt="Postgres" src="https://img.shields.io/badge/Postgres-Alembic%20Migrations-4169e1?style=flat-square&logo=postgresql&logoColor=white">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-Evidence%20API-009688?style=flat-square&logo=fastapi&logoColor=white">
  <img alt="CUPED AA" src="https://img.shields.io/badge/CUPED%20A%2FA-1000%20Runs-brightgreen?style=flat-square">
  <img alt="FP Rate" src="https://img.shields.io/badge/A%2FA%20FP%20Rate-5.5%25-brightgreen?style=flat-square">
  <img alt="Golden Scenarios" src="https://img.shields.io/badge/Golden%20Scenarios-12%2F12%20Pass-blue?style=flat-square">
  <img alt="Streaming Checks" src="https://img.shields.io/badge/Streaming%20Checks-43%2F43%20Pass-purple?style=flat-square">
</p>

---

## Live Dashboard

**Open the visual showcase:**  
https://sidharthkriplani.github.io/metasignal_platform/

The dashboard summarizes MetaSignal's evidence artifacts, metrics intelligence flow, CUPED validation, guardrail-first decisioning, operational history, and streaming reconciliation layer.

## At a Glance

| Layer | What it proves |
|---|---|
| **Metric governance** | Versioned metric registry with explicit numerator, denominator, grain, owner, and config hash |
| **Denominator conflict detection** | Finds conversion-rate definitions that use inconsistent denominator logic |
| **Data quality gates** | Blocking quality failures prevent metric compute instead of producing bad metrics |
| **Experiment assignment** | Deterministic SHA-256 user assignment with SRM validation |
| **CUPED readout** | Variance-reduced experiment evaluation with A/A validation and edge-case handling |
| **Guardrail-first decisioning** | Statistically positive primary metric can still be blocked when guardrails violate |
| **Right-censoring** | Delayed guardrails are marked immature instead of being treated as final |
| **Anomaly detection** | DOW-adjusted anomaly detection with synthetic backtest evidence |
| **Decision audit trail** | Human overrides require written justification and are logged |
| **Streaming extension** | Provisional SRM, instrumentation, lag, DLQ, anomaly, and stream-batch reconciliation signals |

---

MetaSignal demonstrates experimentation systems thinking through metric governance, denominator conflict detection, data quality gates, deterministic assignment, SRM checks, CUPED readouts, CUPED A/A validation, guardrail-first decisioning, right-censoring, anomaly detection, golden scenario validation, FastAPI evidence retrieval, and a streaming early-warning extension.

## Key Results

| Area | Result |
|---|---:|
| Public event dataset | RetailRocket / 2,756,101 rows |
| Core metric definitions | 3 |
| Metric result rows | 417 |
| Experiment assignments | 20,000 |
| Treatment share | 50.47% |
| SRM p-value | 0.1837 |
| CUPED A/A runs | 1,000 |
| CUPED A/A false-positive rate | 5.5% |
| Synthetic CUPED variance reduction | 26.5% |
| CUPED edge cases | 5/5 pass |
| Golden scenarios | 12/12 pass |
| Streaming validation checks | 43/43 pass |
| Streaming scenarios | 10 implemented |
| API smoke tests | 8/8 pass |
| Operational history | 60 days simulated |
| Failure scenarios | 13 scripted scenarios |

## Run the Full Demo

    PYTHONPATH=. python3 scripts/run_full_demo_v0.py

Run the complete PRD validation bundle:

    PYTHONPATH=. python3 scripts/run_metasignal_prd_complete_v1.py

Run the streaming extension demo:

    PYTHONPATH=. python3 scripts/show_streaming_demo.py
    PYTHONPATH=. python3 scripts/validate_streaming_prd_v1.py

## Core Experimentation Capabilities

- Versioned metric registry with explicit denominator logic
- Metric conflict detection
- Data quality gates before compute
- Failure injection and blocked pipeline evidence
- Deterministic experiment assignment
- SRM validation
- CUPED experiment evaluation
- CUPED A/A validation over 1,000 synthetic runs
- Guardrail-first ship/hold decisioning
- Right-censoring for delayed guardrails
- DOW-adjusted anomaly detection
- Golden scenario suite
- FastAPI readout and evidence layer
- Resume, architecture, demo, and interview-defense artifacts

## Streaming Extension Capabilities

- Provisional SRM early warning
- Traffic allocation drift monitoring
- Instrumentation gap detection
- Consumer lag monitoring
- Late-event detection
- Duplicate detection
- DLQ quarantine
- Provisional anomaly alerts
- Stream-batch reconciliation

## Important Artifacts

| Artifact | Path |
|---|---|
| PRD completion report | `outputs/reports/metasignal_prd_completion_report_v1.json` |
| CUPED readout | `outputs/evidence/cuped_experiment_readout.json` |
| CUPED A/A validation | `outputs/validation/cuped_aa_validation_report.json` |
| CUPED edge-case validation | `outputs/validation/cuped_edge_case_validation_report.json` |
| Guardrail decision report | `outputs/evidence/guardrail_decision_report.json` |
| SRM check report | `outputs/evidence/srm_check_report.json` |
| Operational history report | `outputs/evidence/operational_history_60_day_report.json` |
| Golden scenario suite | `outputs/evidence/golden_scenario_suite_v1_report.json` |
| Streaming validation report | `outputs/validation/streaming_prd_v1_validation_report.json` |
| Stream-batch reconciliation | `outputs/streaming/stream_batch_reconciliation_report.json` |
| Defense pack / PRDs | `docs/prd/` |

## Claim Boundary

MetaSignal is a **solo-built, non-production, production-simulated project**.

It does **not** claim:

- real production deployment
- real company users
- real production traffic
- real analyst decisions
- Kafka/Flink production infrastructure
- production streaming decisioning
- real guardrail breach data
- real A/B treatment effect from RetailRocket

Streaming alerts are provisional investigation signals. **Batch remains authoritative.**

## Resume-Safe Claim

Built MetaSignal, a production-simulated experimentation intelligence platform with versioned metric governance, denominator conflict detection, blocking data-quality gates, deterministic assignment, SRM checks, CUPED readouts with 1,000-run A/A validation, guardrail-first decisioning, right-censoring, anomaly detection, decision audit logs, FastAPI evidence retrieval, and a provisional streaming early-warning extension.

## Repository Structure

    alembic/                 database migrations
    config/                  configuration files
    data/                    raw/interim/processed local data folders
    docs/                    architecture, PRD, and defense documentation
    outputs/evidence/        core evidence artifacts
    outputs/reports/         completion and resume-signal reports
    outputs/streaming/       streaming extension artifacts
    outputs/validation/      validation artifacts
    scripts/                 demo, validation, seeding, and export scripts
    src/metasignal/          application source code
    tests/                   test scaffolding

## Status

MetaSignal is complete at the production-simulated repo-evidence level. The next public-showcase layer is a GitHub Pages evidence dashboard.
