from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from pathlib import Path
from uuid import UUID

import pandas as pd
from sqlalchemy import delete, insert, select

from src.metasignal.db.session import SessionLocal
from src.metasignal.db.models import Experiment, ExperimentAssignment


EVENTS_PATH = Path("data/interim/events_standardized.parquet")
OUT_PATH = Path("outputs/evidence/experiment_assignment_balance.json")
EXPERIMENT_KEY = "EXP-CHECKOUT-FRICTION-001"
MAX_USERS_FOR_V0 = 20000


def json_safe(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    return value


def assign_bucket(experiment_key: str, user_id: str) -> tuple[str, float]:
    raw = f"{experiment_key}:{user_id}"
    h = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    bucket = int(h[:12], 16) / float(16 ** 12)
    return h, bucket


def main() -> None:
    if not EVENTS_PATH.exists():
        raise FileNotFoundError(f"Missing standardized events file: {EVENTS_PATH}")

    df = pd.read_parquet(EVENTS_PATH, columns=['user_id', 'event_date'])
    df["event_date"] = pd.to_datetime(df["event_date"]).dt.date

    with SessionLocal() as session:
        experiment = session.scalar(
            select(Experiment).where(Experiment.experiment_key == EXPERIMENT_KEY)
        )

        if experiment is None:
            raise ValueError(f"Experiment not found: {EXPERIMENT_KEY}")

        eligible = df[
            (df["event_date"] >= experiment.start_date)
            & (df["event_date"] <= experiment.end_date)
        ][["user_id"]].dropna().drop_duplicates()

        eligible["user_id"] = eligible["user_id"].astype(str)
        eligible = eligible.sort_values("user_id").head(MAX_USERS_FOR_V0)

        session.execute(
            delete(ExperimentAssignment).where(
                ExperimentAssignment.experiment_id == experiment.id
            )
        )

        rows = []
        treatment_count = 0
        control_count = 0

        for user_id in eligible["user_id"].tolist():
            h, bucket = assign_bucket(experiment.experiment_key, user_id)
            variant = "treatment" if bucket < experiment.treatment_split_pct else "control"

            if variant == "treatment":
                treatment_count += 1
            else:
                control_count += 1

            rows.append(
                {
                    "experiment_id": experiment.id,
                    "user_id": user_id,
                    "variant": variant,
                    "assignment_hash": h,
                    "assignment_bucket": bucket,
                    "assignment_method": experiment.assignment_method,
                }
            )

        batch_size = 5000
        for i in range(0, len(rows), batch_size):
            session.execute(insert(ExperimentAssignment), rows[i:i + batch_size])

        session.commit()

        total = len(rows)
        treatment_share = treatment_count / total if total else None
        control_share = control_count / total if total else None
        expected = experiment.treatment_split_pct
        absolute_imbalance = abs(treatment_share - expected) if treatment_share is not None else None

        payload = {
            "artifact": "experiment_assignment_balance",
            "experiment_key": experiment.experiment_key,
            "assignment_method": experiment.assignment_method,
            "eligible_users_source": str(EVENTS_PATH),
            "assigned_user_count": total,
            "max_users_for_v0": MAX_USERS_FOR_V0,
            "expected_treatment_share": expected,
            "treatment_count": treatment_count,
            "control_count": control_count,
            "treatment_share": treatment_share,
            "control_share": control_share,
            "absolute_treatment_share_imbalance": absolute_imbalance,
            "balance_status": "pass" if absolute_imbalance is not None and absolute_imbalance <= 0.01 else "review",
            "evidence_statement": "MetaSignal generated deterministic user-level experiment assignments and verified treatment/control balance.",
        }

        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUT_PATH.write_text(json.dumps(payload, indent=2, default=json_safe), encoding="utf-8")

        print("generate_assignments_v0 complete")
        print(f"assigned_user_count: {total}")
        print(f"treatment_count: {treatment_count}")
        print(f"control_count: {control_count}")
        print(f"treatment_share: {treatment_share}")
        print(f"balance_status: {payload['balance_status']}")
        print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
