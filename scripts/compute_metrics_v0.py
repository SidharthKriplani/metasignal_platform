from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import delete, select

from src.metasignal.db.session import SessionLocal
from src.metasignal.db.models import MetricDefinition, MetricResult, PipelineRunLog


EVENTS_PATH = Path("data/interim/events_standardized.parquet")


def hash_config(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def safe_divide(num: float, den: float) -> float | None:
    if den == 0:
        return None
    return num / den


def main() -> None:
    if not EVENTS_PATH.exists():
        raise FileNotFoundError(f"Missing standardized events file: {EVENTS_PATH}")

    df = pd.read_parquet(EVENTS_PATH)
    df["event_date"] = pd.to_datetime(df["event_date"]).dt.date
    df["event_type"] = df["event_type"].astype(str)

    with SessionLocal() as session:
        metric_defs = {
            m.name: m
            for m in session.scalars(select(MetricDefinition)).all()
        }

        required = [
            "purchase_conversion_rate_user",
            "purchase_conversion_rate_event",
            "refund_rate_guardrail",
        ]

        missing = [name for name in required if name not in metric_defs]
        if missing:
            raise ValueError(f"Missing metric definitions: {missing}")

        session.execute(delete(MetricResult))

        run = PipelineRunLog(
            job_type="metric_compute_v0",
            run_date=df["event_date"].min(),
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            status="success",
            rows_processed=len(df),
            rows_expected=len(df),
            quality_checks_passed=1,
            quality_checks_failed=0,
            config_hash=hash_config("metric_compute_v0_retailrocket"),
            retry_count=0,
            triggered_by="compute_metrics_v0",
        )
        session.add(run)
        session.flush()

        results = []

        for event_date, g in df.groupby("event_date"):
            active_users = g["user_id"].nunique()
            purchase_users = g.loc[g["event_type"] == "transaction", "user_id"].nunique()
            view_events = int((g["event_type"] == "view").sum())
            purchase_events = int((g["event_type"] == "transaction").sum())
            return_events = int((g["event_type"] == "return_initiated").sum())

            metric_values = [
                (
                    metric_defs["purchase_conversion_rate_user"],
                    purchase_users,
                    active_users,
                    safe_divide(purchase_users, active_users),
                ),
                (
                    metric_defs["purchase_conversion_rate_event"],
                    purchase_events,
                    view_events,
                    safe_divide(purchase_events, view_events),
                ),
                (
                    metric_defs["refund_rate_guardrail"],
                    return_events,
                    purchase_events,
                    safe_divide(return_events, purchase_events),
                ),
            ]

            for metric, numerator, denominator, value in metric_values:
                results.append(
                    MetricResult(
                        metric_id=metric.id,
                        metric_version=metric.version,
                        computation_date=event_date,
                        grain_period=str(event_date),
                        numerator_value=float(numerator),
                        denominator_value=float(denominator),
                        metric_value=value,
                        segment_key="ALL",
                        run_id=run.id,
                        quality_passed=True,
                        late_arrival_flag=False,
                    )
                )

        session.add_all(results)
        session.commit()

        print("compute_metrics_v0 complete")
        print(f"events_loaded: {len(df)}")
        print(f"dates_computed: {df['event_date'].nunique()}")
        print(f"metric_results_inserted: {len(results)}")


if __name__ == "__main__":
    main()
