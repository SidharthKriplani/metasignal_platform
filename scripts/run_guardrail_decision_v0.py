from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy import delete, select

from src.metasignal.db.session import SessionLocal
from src.metasignal.db.models import DecisionLog, Experiment, ExperimentEvaluation


OUT_PATH = Path("outputs/evidence/guardrail_decision_report.json")
EXPERIMENT_KEY = "EXP-CHECKOUT-FRICTION-001"


def json_safe(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    return value


def main() -> None:
    with SessionLocal() as session:
        experiment = session.scalar(
            select(Experiment).where(Experiment.experiment_key == EXPERIMENT_KEY)
        )

        if experiment is None:
            raise ValueError(f"Experiment not found: {EXPERIMENT_KEY}")

        evaluation = session.scalar(
            select(ExperimentEvaluation)
            .where(
                ExperimentEvaluation.experiment_id == experiment.id,
                ExperimentEvaluation.evaluator_version == "cuped_v0",
            )
            .order_by(ExperimentEvaluation.created_at.desc())
        )

        if evaluation is None:
            raise ValueError("CUPED evaluation not found. Run run_cuped_v0.py first.")

        # v0 simulated delayed guardrail readout:
        # Primary metric is positive, but refund guardrail breaches allowed tolerance.
        guardrail_results = [
            {
                "metric_name": "refund_rate_guardrail",
                "guardrail_type": "delayed_refund_rate",
                "max_allowed_relative_increase_pct": 2.0,
                "observed_relative_increase_pct": 3.1,
                "maturity_status": "immature_at_day_14",
                "status": "breached",
                "decision_effect": "blocks_ship",
            }
        ]

        primary_positive = bool(evaluation.is_significant and evaluation.primary_metric_lift and evaluation.primary_metric_lift > 0)
        guardrails_cleared = all(g["status"] == "pass" for g in guardrail_results)

        if not guardrails_cleared:
            system_recommendation = "HOLD"
            reason = (
                "Primary metric is positive, but guardrail-first decisioning blocks shipment because "
                "refund-rate guardrail breached tolerance."
            )
        elif primary_positive:
            system_recommendation = "SHIP"
            reason = "Primary metric is positive and all guardrails cleared."
        else:
            system_recommendation = "INVESTIGATE"
            reason = "Primary metric evidence is insufficient for ship decision."

        evaluation.guardrail_results = guardrail_results
        evaluation.guardrails_cleared = guardrails_cleared
        evaluation.decision_recommendation = system_recommendation
        evaluation.recommendation_reason = reason

        session.execute(
            delete(DecisionLog).where(
                DecisionLog.experiment_id == experiment.id,
                DecisionLog.evaluation_id == evaluation.id,
            )
        )

        decision = DecisionLog(
            experiment_id=experiment.id,
            evaluation_id=evaluation.id,
            system_recommendation=system_recommendation,
            final_decision=system_recommendation,
            reviewer_name="Guardrail Engine v0",
            override_reason=None,
            decision_notes="Automated v0 decision accepted for demo evidence.",
        )

        session.add(decision)
        session.commit()

        payload = {
            "artifact": "guardrail_decision_report",
            "experiment_key": experiment.experiment_key,
            "primary_metric": {
                "cuped_relative_lift": evaluation.primary_metric_lift,
                "p_value": evaluation.p_value,
                "is_significant": evaluation.is_significant,
                "primary_positive": primary_positive,
            },
            "guardrails": guardrail_results,
            "guardrails_cleared": guardrails_cleared,
            "system_recommendation": system_recommendation,
            "final_decision": decision.final_decision,
            "decision_reason": reason,
            "db_evaluation_id": evaluation.id,
            "db_decision_id": decision.id,
            "evidence_statement": "MetaSignal applied guardrail-first decisioning: a statistically positive CUPED readout is blocked when a guardrail breaches tolerance.",
        }

        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUT_PATH.write_text(json.dumps(payload, indent=2, default=json_safe), encoding="utf-8")

        print("guardrail_decision_v0 complete")
        print(f"primary_positive: {primary_positive}")
        print(f"guardrails_cleared: {guardrails_cleared}")
        print(f"system_recommendation: {system_recommendation}")
        print(f"final_decision: {decision.final_decision}")
        print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
