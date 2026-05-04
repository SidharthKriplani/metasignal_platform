from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy import select

from src.metasignal.db.session import SessionLocal
from src.metasignal.db.models import (
    DataQualityCheck,
    DecisionLog,
    Experiment,
    ExperimentEvaluation,
    MetricDefinition,
    PipelineRunLog,
    SimulationEvent,
)


OUT_DIR = Path("outputs/evidence")


def json_safe(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    return value


def write_json(filename: str, payload) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / filename
    path.write_text(json.dumps(payload, indent=2, default=json_safe), encoding="utf-8")
    print(f"wrote {path}")


def main() -> None:
    with SessionLocal() as session:
        metrics = session.scalars(select(MetricDefinition).order_by(MetricDefinition.name)).all()
        scenarios = session.scalars(select(SimulationEvent).order_by(SimulationEvent.simulation_day)).all()
        runs = session.scalars(select(PipelineRunLog).order_by(PipelineRunLog.run_date)).all()
        checks = session.scalars(select(DataQualityCheck).order_by(DataQualityCheck.check_name)).all()
        experiments = session.scalars(select(Experiment)).all()
        evaluations = session.scalars(select(ExperimentEvaluation)).all()
        decisions = session.scalars(select(DecisionLog)).all()

        metric_registry = [
            {
                "id": m.id,
                "name": m.name,
                "display_name": m.display_name,
                "description": m.description,
                "numerator_sql": m.numerator_sql,
                "denominator_sql": m.denominator_sql,
                "denominator_type": m.denominator_type,
                "grain": m.grain,
                "entity_type": m.entity_type,
                "direction": m.direction,
                "is_guardrail": m.is_guardrail,
                "guardrail_tolerance_pct": m.guardrail_tolerance_pct,
                "owner": m.owner,
                "version": m.version,
                "is_active": m.is_active,
                "config_hash": m.config_hash,
                "change_notes": m.change_notes,
            }
            for m in metrics
        ]

        simulation_scenarios = [
            {
                "scenario_id": s.scenario_id,
                "scenario_name": s.scenario_name,
                "scenario_type": s.scenario_type,
                "simulation_day": s.simulation_day,
                "event_date": s.event_date,
                "description": s.description,
                "injected": s.injected,
                "injection_payload": s.injection_payload,
                "expected_system_behavior": s.expected_system_behavior,
            }
            for s in scenarios
        ]

        pipeline_quality_report = {
            "pipeline_runs": [
                {
                    "id": r.id,
                    "job_type": r.job_type,
                    "run_date": r.run_date,
                    "status": r.status,
                    "rows_processed": r.rows_processed,
                    "rows_expected": r.rows_expected,
                    "quality_checks_passed": r.quality_checks_passed,
                    "quality_checks_failed": r.quality_checks_failed,
                    "config_hash": r.config_hash,
                    "retry_count": r.retry_count,
                    "triggered_by": r.triggered_by,
                }
                for r in runs
            ],
            "data_quality_checks": [
                {
                    "id": c.id,
                    "run_id": c.run_id,
                    "check_name": c.check_name,
                    "entity": c.entity,
                    "check_date": c.check_date,
                    "expected_value": c.expected_value,
                    "actual_value": c.actual_value,
                    "threshold": c.threshold,
                    "passed": c.passed,
                    "severity": c.severity,
                    "check_details": c.check_details,
                }
                for c in checks
            ],
        }

        experiment_readout = {
            "experiments": [
                {
                    "id": e.id,
                    "experiment_key": e.experiment_key,
                    "name": e.name,
                    "hypothesis": e.hypothesis,
                    "start_date": e.start_date,
                    "end_date": e.end_date,
                    "status": e.status,
                    "expected_mde": e.expected_mde,
                    "expected_duration_days": e.expected_duration_days,
                    "alpha": e.alpha,
                    "power": e.power,
                    "use_cuped": e.use_cuped,
                    "assignment_method": e.assignment_method,
                    "treatment_split_pct": e.treatment_split_pct,
                    "guardrail_metric_configs": e.guardrail_metric_configs,
                }
                for e in experiments
            ],
            "evaluations": [
                {
                    "id": ev.id,
                    "experiment_id": ev.experiment_id,
                    "evaluation_day": ev.evaluation_day,
                    "sample_size_treatment": ev.sample_size_treatment,
                    "sample_size_control": ev.sample_size_control,
                    "primary_metric_lift": ev.primary_metric_lift,
                    "primary_metric_ci_lower": ev.primary_metric_ci_lower,
                    "primary_metric_ci_upper": ev.primary_metric_ci_upper,
                    "p_value": ev.p_value,
                    "is_significant": ev.is_significant,
                    "cuped_applied": ev.cuped_applied,
                    "cuped_theta": ev.cuped_theta,
                    "variance_reduction_pct": ev.variance_reduction_pct,
                    "guardrail_results": ev.guardrail_results,
                    "guardrails_cleared": ev.guardrails_cleared,
                    "decision_recommendation": ev.decision_recommendation,
                    "recommendation_reason": ev.recommendation_reason,
                    "evaluator_version": ev.evaluator_version,
                }
                for ev in evaluations
            ],
        }

        decision_audit_log = [
            {
                "id": d.id,
                "experiment_id": d.experiment_id,
                "evaluation_id": d.evaluation_id,
                "system_recommendation": d.system_recommendation,
                "final_decision": d.final_decision,
                "reviewer_name": d.reviewer_name,
                "override_reason": d.override_reason,
                "decision_notes": d.decision_notes,
                "created_at": d.created_at,
            }
            for d in decisions
        ]

        manifest = {
            "artifact_set": "MetaSignal Core Evidence v0",
            "generated_files": [
                "metric_registry.json",
                "simulation_scenarios.json",
                "pipeline_quality_report.json",
                "experiment_readout.json",
                "decision_audit_log.json",
            ],
            "evidence_status": "core_seed_complete",
            "notes": "These artifacts prove the first production-simulated MetaSignal registry, quality, experiment, and decision evidence objects exist.",
        }

        write_json("metric_registry.json", metric_registry)
        write_json("simulation_scenarios.json", simulation_scenarios)
        write_json("pipeline_quality_report.json", pipeline_quality_report)
        write_json("experiment_readout.json", experiment_readout)
        write_json("decision_audit_log.json", decision_audit_log)
        write_json("core_evidence_manifest.json", manifest)

        print("export_core_artifacts complete")


if __name__ == "__main__":
    main()
