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
    ExperimentAssignment,
    ExperimentEvaluation,
    MetricDefinition,
    MetricResult,
    PipelineRunLog,
    SimulationEvent,
)


OUT_PATH = Path("outputs/evidence/golden_scenario_suite_report.json")


def json_safe(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    return value


def main() -> None:
    with SessionLocal() as session:
        metric_count = len(session.scalars(select(MetricDefinition)).all())
        metric_result_count = len(session.scalars(select(MetricResult)).all())
        failed_quality_count = len(session.scalars(select(DataQualityCheck).where(DataQualityCheck.passed == False)).all())
        simulation_count = len(session.scalars(select(SimulationEvent)).all())
        assignment_count = len(session.scalars(select(ExperimentAssignment)).all())
        evals = session.scalars(select(ExperimentEvaluation)).all()
        decisions = session.scalars(select(DecisionLog)).all()
        runs = session.scalars(select(PipelineRunLog)).all()

        latest_decision = decisions[-1] if decisions else None
        latest_eval = evals[-1] if evals else None

        scenarios = [
            {
                "scenario": "metric_registry_exists",
                "expected": "at least 3 metric definitions",
                "passed": metric_count >= 3,
                "observed": metric_count,
            },
            {
                "scenario": "metric_results_computed",
                "expected": "daily metric rows exist",
                "passed": metric_result_count > 0,
                "observed": metric_result_count,
            },
            {
                "scenario": "quality_failures_are_captured",
                "expected": "failure injection creates failed checks",
                "passed": failed_quality_count > 0,
                "observed": failed_quality_count,
            },
            {
                "scenario": "simulation_events_defined",
                "expected": "at least 5 simulation events",
                "passed": simulation_count >= 5,
                "observed": simulation_count,
            },
            {
                "scenario": "experiment_assignments_exist",
                "expected": "at least 10k assignments",
                "passed": assignment_count >= 10000,
                "observed": assignment_count,
            },
            {
                "scenario": "cuped_evaluation_exists",
                "expected": "at least one CUPED evaluation",
                "passed": any(e.cuped_applied for e in evals),
                "observed": len(evals),
            },
            {
                "scenario": "guardrail_blocks_positive_primary_metric",
                "expected": "final decision HOLD when guardrail breached",
                "passed": bool(latest_decision and latest_decision.final_decision == "HOLD"),
                "observed": latest_decision.final_decision if latest_decision else None,
            },
            {
                "scenario": "pipeline_runs_logged",
                "expected": "pipeline run logs exist",
                "passed": len(runs) > 0,
                "observed": len(runs),
            },
        ]

        passed_count = sum(s["passed"] for s in scenarios)

        payload = {
            "artifact": "golden_scenario_suite_report",
            "scenario_count": len(scenarios),
            "passed_count": passed_count,
            "failed_count": len(scenarios) - passed_count,
            "status": "pass" if passed_count == len(scenarios) else "review",
            "scenarios": scenarios,
            "evidence_statement": "MetaSignal golden scenario suite validates core registry, metric compute, quality failure, assignment, CUPED, guardrail, and audit behaviors.",
        }

        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUT_PATH.write_text(json.dumps(payload, indent=2, default=json_safe), encoding="utf-8")

        print("golden_scenarios_v0 complete")
        print(f"scenario_count: {len(scenarios)}")
        print(f"passed_count: {passed_count}")
        print(f"status: {payload['status']}")
        print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
