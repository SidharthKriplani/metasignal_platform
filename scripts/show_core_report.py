from __future__ import annotations

from sqlalchemy import select, func

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


def main() -> None:
    with SessionLocal() as session:
        print("\n=== MetaSignal Core Evidence Report v0 ===\n")

        counts = [
            ("Metric definitions", MetricDefinition),
            ("Simulation events", SimulationEvent),
            ("Pipeline runs", PipelineRunLog),
            ("Data quality checks", DataQualityCheck),
            ("Experiments", Experiment),
            ("Experiment evaluations", ExperimentEvaluation),
            ("Decision log entries", DecisionLog),
        ]

        print("Object counts")
        print("-------------")
        for label, model in counts:
            count = session.scalar(select(func.count()).select_from(model))
            print(f"{label}: {count}")

        print("\nMetric registry")
        print("---------------")
        metrics = session.scalars(select(MetricDefinition).order_by(MetricDefinition.name)).all()
        for m in metrics:
            guardrail = "yes" if m.is_guardrail else "no"
            print(f"- {m.name} | denominator={m.denominator_type} | grain={m.grain} | guardrail={guardrail}")

        print("\nSimulation scenarios")
        print("--------------------")
        scenarios = session.scalars(select(SimulationEvent).order_by(SimulationEvent.simulation_day)).all()
        for s in scenarios:
            print(f"- Day {s.simulation_day}: {s.scenario_id} | {s.scenario_type} | {s.scenario_name}")

        print("\nPipeline quality")
        print("----------------")
        run = session.scalars(select(PipelineRunLog).order_by(PipelineRunLog.started_at.desc())).first()
        if run:
            print(f"Run date: {run.run_date}")
            print(f"Status: {run.status}")
            print(f"Rows processed: {run.rows_processed}")
            print(f"Quality checks passed: {run.quality_checks_passed}")
            print(f"Quality checks failed: {run.quality_checks_failed}")

        print("\nExperiment readout")
        print("------------------")
        exp = session.scalars(select(Experiment)).first()
        eval_row = session.scalars(select(ExperimentEvaluation)).first()
        decision = session.scalars(select(DecisionLog)).first()

        if exp and eval_row and decision:
            print(f"Experiment: {exp.experiment_key} — {exp.name}")
            print(f"Hypothesis: {exp.hypothesis}")
            print(f"Primary lift: {eval_row.primary_metric_lift}")
            print(f"p-value: {eval_row.p_value}")
            print(f"CUPED applied: {eval_row.cuped_applied}")
            print(f"Variance reduction pct: {eval_row.variance_reduction_pct}")
            print(f"Guardrails cleared: {eval_row.guardrails_cleared}")
            print(f"System recommendation: {decision.system_recommendation}")
            print(f"Final decision: {decision.final_decision}")
            print(f"Reason: {eval_row.recommendation_reason}")

        print("\nEvidence status")
        print("---------------")
        print("PASS: Core registry, quality, experiment, and decision evidence exists.")
        print("NEXT: Add file output artifacts under outputs/evidence/.")


if __name__ == "__main__":
    main()
