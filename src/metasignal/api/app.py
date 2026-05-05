from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from sqlalchemy import select

from src.metasignal.db.models import (
    DataQualityCheck,
    DecisionLog,
    Experiment,
    ExperimentEvaluation,
    MetricDefinition,
    MetricResult,
    PipelineRunLog,
)
from src.metasignal.db.session import SessionLocal


app = FastAPI(
    title="MetaSignal API",
    version="0.1.0",
    description="Production-simulated experimentation, metrics intelligence, and decision audit API.",
)


EVIDENCE_DIR = Path("outputs/evidence")
VALIDATION_DIR = Path("outputs/validation")
REPORTS_DIR = Path("outputs/reports")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Artifact not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/health")
def health() -> dict[str, Any]:
    with SessionLocal() as session:
        metric_count = len(session.scalars(select(MetricDefinition)).all())
        experiment_count = len(session.scalars(select(Experiment)).all())
        run_count = len(session.scalars(select(PipelineRunLog)).all())

    return {
        "status": "ok",
        "service": "metasignal-api",
        "metric_definitions": metric_count,
        "experiments": experiment_count,
        "pipeline_runs": run_count,
    }


@app.get("/metrics")
def list_metrics() -> list[dict[str, Any]]:
    with SessionLocal() as session:
        metrics = session.scalars(select(MetricDefinition).order_by(MetricDefinition.name)).all()

    return [
        {
            "name": m.name,
            "display_name": m.display_name,
            "denominator_type": m.denominator_type,
            "grain": m.grain,
            "entity_type": m.entity_type,
            "is_guardrail": m.is_guardrail,
            "version": m.version,
            "is_active": m.is_active,
        }
        for m in metrics
    ]


@app.get("/metrics/{metric_name}/timeseries")
def metric_timeseries(metric_name: str) -> dict[str, Any]:
    with SessionLocal() as session:
        metric = session.scalar(select(MetricDefinition).where(MetricDefinition.name == metric_name))
        if metric is None:
            raise HTTPException(status_code=404, detail=f"Metric not found: {metric_name}")

        rows = session.scalars(
            select(MetricResult)
            .where(MetricResult.metric_id == metric.id)
            .where(MetricResult.segment_key == "ALL")
            .order_by(MetricResult.computation_date)
        ).all()

    return {
        "metric_name": metric_name,
        "row_count": len(rows),
        "timeseries": [
            {
                "date": r.computation_date.isoformat(),
                "metric_value": r.metric_value,
                "numerator_value": r.numerator_value,
                "denominator_value": r.denominator_value,
                "quality_passed": r.quality_passed,
                "late_arrival_flag": r.late_arrival_flag,
            }
            for r in rows
        ],
    }


@app.get("/experiments")
def list_experiments() -> list[dict[str, Any]]:
    with SessionLocal() as session:
        experiments = session.scalars(select(Experiment).order_by(Experiment.created_at)).all()

    return [
        {
            "experiment_key": e.experiment_key,
            "name": e.name,
            "hypothesis": e.hypothesis,
            "status": e.status,
            "start_date": e.start_date.isoformat(),
            "end_date": e.end_date.isoformat() if e.end_date else None,
            "use_cuped": e.use_cuped,
            "assignment_method": e.assignment_method,
        }
        for e in experiments
    ]


@app.get("/experiments/{experiment_key}/readout")
def experiment_readout(experiment_key: str) -> dict[str, Any]:
    with SessionLocal() as session:
        experiment = session.scalar(select(Experiment).where(Experiment.experiment_key == experiment_key))
        if experiment is None:
            raise HTTPException(status_code=404, detail=f"Experiment not found: {experiment_key}")

        evaluation = session.scalar(
            select(ExperimentEvaluation)
            .where(ExperimentEvaluation.experiment_id == experiment.id)
            .order_by(ExperimentEvaluation.evaluated_at.desc())
        )

        decision = session.scalar(
            select(DecisionLog)
            .where(DecisionLog.experiment_id == experiment.id)
            .order_by(DecisionLog.created_at.desc())
        )

    return {
        "experiment_key": experiment.experiment_key,
        "name": experiment.name,
        "hypothesis": experiment.hypothesis,
        "latest_evaluation": None if evaluation is None else {
            "primary_metric_lift": evaluation.primary_metric_lift,
            "p_value": evaluation.p_value,
            "is_significant": evaluation.is_significant,
            "cuped_applied": evaluation.cuped_applied,
            "variance_reduction_pct": evaluation.variance_reduction_pct,
            "guardrails_cleared": evaluation.guardrails_cleared,
            "system_recommendation": evaluation.system_recommendation,
        },
        "latest_decision": None if decision is None else {
            "system_recommendation": decision.system_recommendation,
            "final_decision": decision.final_decision,
            "decision_reason": decision.decision_reason,
            "reviewer": decision.reviewer,
            "override_reason": decision.override_reason,
        },
    }


@app.get("/data-quality/latest")
def latest_data_quality() -> dict[str, Any]:
    with SessionLocal() as session:
        run = session.scalar(select(PipelineRunLog).order_by(PipelineRunLog.created_at.desc()))
        if run is None:
            raise HTTPException(status_code=404, detail="No pipeline runs found")

        checks = session.scalars(
            select(DataQualityCheck)
            .where(DataQualityCheck.run_id == run.id)
            .order_by(DataQualityCheck.check_name)
        ).all()

    return {
        "run_date": run.run_date.isoformat(),
        "status": run.status,
        "rows_processed": run.rows_processed,
        "checks_passed": run.quality_checks_passed,
        "checks_failed": run.quality_checks_failed,
        "checks": [
            {
                "check_name": c.check_name,
                "entity": c.entity,
                "passed": c.passed,
                "severity": c.severity,
                "expected_value": c.expected_value,
                "actual_value": c.actual_value,
                "threshold": c.threshold,
            }
            for c in checks
        ],
    }


@app.get("/evidence/{artifact_name}")
def get_evidence_artifact(artifact_name: str) -> dict[str, Any]:
    safe_name = artifact_name.replace("/", "").replace("..", "")
    return load_json(EVIDENCE_DIR / f"{safe_name}.json")


@app.get("/validation/{artifact_name}")
def get_validation_artifact(artifact_name: str) -> dict[str, Any]:
    safe_name = artifact_name.replace("/", "").replace("..", "")
    return load_json(VALIDATION_DIR / f"{safe_name}.json")


@app.get("/resume-signal")
def resume_signal() -> dict[str, Any]:
    return load_json(REPORTS_DIR / "metasignal_resume_signal_summary.json")
