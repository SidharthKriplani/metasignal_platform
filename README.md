# MetaSignal

Production-simulated experimentation, metrics intelligence, and streaming observability platform.

MetaSignal demonstrates experimentation systems thinking through metric governance, denominator conflict detection, data quality gates, deterministic assignment, SRM checks, CUPED readouts, CUPED A/A validation, guardrail-first decisioning, right-censoring, anomaly detection, golden scenario validation, FastAPI evidence retrieval, and a streaming early-warning extension.

## Run the full demo

PYTHONPATH=. python3 scripts/run_full_demo_v0.py

## Core experimentation capabilities

- Versioned metric registry with explicit denominator logic
- Metric conflict detection
- Data quality gates before compute
- Failure injection and blocked pipeline evidence
- Deterministic experiment assignment
- SRM validation
- CUPED experiment evaluation
- CUPED A/A validation over 1000 synthetic runs
- Guardrail-first ship/hold decisioning
- Right-censoring for delayed guardrails
- DOW-adjusted anomaly detection
- Golden scenario suite
- FastAPI readout and evidence layer
- Resume, architecture, demo, and interview-defense artifacts

## Streaming extension capabilities

- Provisional SRM early warning
- Traffic allocation drift monitoring
- Instrumentation gap detection
- Consumer lag monitoring
- Late-event detection
- Duplicate detection
- DLQ quarantine
- Provisional anomaly alerts
- Stream-batch reconciliation

## Claim boundary

This is a solo-built, non-production, production-simulated project. It does not claim real production deployment or real company users. Streaming alerts are provisional investigation signals; batch remains authoritative.


## PRD Completion Evidence

MetaSignal now includes executable repo evidence for both the Core PRD and Streaming Extension PRD.

Run the complete local validation bundle:

```bash
PYTHONPATH=. python3 scripts/run_metasignal_prd_complete_v1.py
