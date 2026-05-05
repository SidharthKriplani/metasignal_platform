# MetaSignal Resume Signal Summary

**Positioning:** Production-simulated experimentation, metrics intelligence, and decision-audit platform.

## Resume Bullet Candidate

Built MetaSignal, a production-simulated experimentation intelligence platform with versioned metric registry, denominator-conflict detection, data-quality gates, deterministic assignment, SRM checks, CUPED readouts, A/A validation, guardrail-first decisioning, right-censoring, anomaly detection, golden scenarios, and auditable evidence artifacts.

## Evidence Matrix

| Capability | Proof | Artifact | Interview Signal |
|---|---|---|---|
| Metric registry and denominator governance | Versioned metric definitions with explicit numerator, denominator, grain, owner, and guardrail fields. | `outputs/evidence/metric_registry.json` | Can explain why conversion-rate denominator inconsistency breaks experimentation decisions. |
| Data quality gates before compute | Reusable quality service and failure-injection scenarios create blocked/warn/pass evidence. | `outputs/evidence/data_quality_service_report.json` | Understands that serving no metric is better than serving a metric computed on bad data. |
| Metric conflict detection | Detector identifies active metrics with conflicting denominator logic. | `outputs/evidence/metric_conflict_report.json` | Can reason about metric governance, not just dashboards. |
| Deterministic experiment assignment and SRM | Hash-based assignment creates 20k users and SRM check validates treatment/control balance. | `outputs/evidence/srm_check_report.json` | Can defend assignment validity and sample-ratio mismatch checks. |
| CUPED experiment evaluation | CUPED readout stores lift, p-value, variance reduction, and evaluation artifact. | `outputs/evidence/cuped_experiment_readout.json` | Can explain variance reduction and pre-period covariate adjustment. |
| CUPED A/A validation | 1000 synthetic A/A runs validate false-positive control and p-value uniformity. | `outputs/validation/cuped_aa_validation_report.json` | Can show the statistical method was validated, not merely implemented. |
| Guardrail-first decisioning | Positive primary metric is blocked because refund guardrail breaches tolerance. | `outputs/evidence/guardrail_decision_report.json` | Can reason about asymmetric product harm and why guardrails are gates. |
| Right-censoring and delayed guardrails | Post-launch validation marks delayed refund guardrail as immature/right-censored. | `outputs/evidence/post_launch_validation_report.json` | Can explain why early readouts can be invalid for delayed metrics. |
| Anomaly detection | DOW-adjusted rolling baseline detects labeled synthetic metric anomaly. | `outputs/evidence/anomaly_detection_report.json` | Can distinguish metric movement from seasonality/noise/data-quality failure. |
| Golden scenario suite | Deterministic scenario suite validates registry, quality, assignment, CUPED, guardrail, and audit behavior. | `outputs/evidence/golden_scenario_suite_report.json` | Can prove system behavior through repeatable tests. |
