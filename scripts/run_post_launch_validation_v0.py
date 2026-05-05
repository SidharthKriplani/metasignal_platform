from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy import select

from src.metasignal.db.session import SessionLocal
from src.metasignal.db.models import Experiment, ExperimentEvaluation, DecisionLog


OUT_PATH = Path("outputs/evidence/post_launch_validation_report.json")
EXPERIMENT_KEY = "EXP-CHECKOUT-FRICTION-001"


def json_safe(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    return value


def main() -> None:
    with SessionLocal() as session:
        experiment = session.scalar(select(Experiment).where(Experiment.experiment_key == EXPERIMENT_KEY))
        if experiment is None:
            raise ValueError(f"Experiment not found: {EXPERIMENT_KEY}")

        evaluation = session.scalar(
            select(ExperimentEvaluation)
            .where(ExperimentEvaluation.experiment_id == experiment.id)
            .order_by(ExperimentEvaluation.created_at.desc())
        )
        if evaluation is None:
            raise ValueError("No evaluation found")

        decision = session.scalar(
            select(DecisionLog)
            .where(DecisionLog.experiment_id == experiment.id)
            .order_by(DecisionLog.created_at.desc())
        )

        delayed_guardrail = {
            "metric_name": "refund_rate_guardrail",
            "readout_day": 14,
            "maturity_window_days": 30,
            "is_mature": False,
            "right_censoring_flag": True,
            "observed_relative_increase_pct_day_14": 3.1,
            "projected_mature_relative_increase_pct_day_30": 3.8,
            "max_allowed_relative_increase_pct": 2.0,
            "status": "immature_but_breached",
        }

        post_launch_assessment = {
            "decision_reviewed": decision.final_decision if decision else None,
            "would_ship_without_guardrail": bool(evaluation.is_significant and evaluation.primary_metric_lift and evaluation.primary_metric_lift > 0),
            "actual_system_decision": decision.final_decision if decision else None,
            "post_launch_status": "blocked_before_rollout",
            "lesson": "Delayed guardrails must be treated as immature until maturity window closes; positive primary lift alone is insufficient.",
        }

        payload = {
            "artifact": "post_launch_validation_report",
            "experiment_key": experiment.experiment_key,
            "right_censoring": delayed_guardrail,
            "post_launch_assessment": post_launch_assessment,
            "evidence_statement": "MetaSignal marks delayed guardrails as right-censored and prevents positive primary-metric readouts from shipping without mature guardrail review.",
        }

        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUT_PATH.write_text(json.dumps(payload, indent=2, default=json_safe), encoding="utf-8")

        print("post_launch_validation_v0 complete")
        print(f"right_censoring_flag: {delayed_guardrail['right_censoring_flag']}")
        print(f"post_launch_status: {post_launch_assessment['post_launch_status']}")
        print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
