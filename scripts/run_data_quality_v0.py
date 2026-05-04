from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import UUID

import pandas as pd
from sqlalchemy import select

from src.metasignal.db.session import SessionLocal
from src.metasignal.db.models import DataQualityCheck, PipelineRunLog


EVENTS_PATH = Path("data/interim/events_standardized.parquet")
OUT_PATH = Path("outputs/evidence/data_quality_service_report.json")

REQUIRED_COLUMNS = [
    "event_timestamp",
    "event_date",
    "user_id",
    "event_type",
    "item_id",
    "transaction_id",
]

ALLOWED_EVENT_TYPES = {"view", "addtocart", "transaction"}


def hash_config(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def json_safe(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    return value


def main() -> None:
    if not EVENTS_PATH.exists():
        raise FileNotFoundError(f"Missing standardized events file: {EVENTS_PATH}")

    df = pd.read_parquet(EVENTS_PATH)
    df["event_date"] = pd.to_datetime(df["event_date"]).dt.date
    df["event_type"] = df["event_type"].astype(str)

    run_date = df["event_date"].min()
    checks_payload = []

    required_present = all(c in df.columns for c in REQUIRED_COLUMNS)
    checks_payload.append({
        "check_name": "required_columns_present",
        "entity": "events_standardized",
        "expected_value": len(REQUIRED_COLUMNS),
        "actual_value": sum(c in df.columns for c in REQUIRED_COLUMNS),
        "threshold": 0,
        "passed": required_present,
        "severity": "blocking",
        "check_details": {"required_columns": REQUIRED_COLUMNS, "actual_columns": list(df.columns)},
    })

    row_count_passed = len(df) > 0
    checks_payload.append({
        "check_name": "row_count_nonzero",
        "entity": "events_standardized",
        "expected_value": 1,
        "actual_value": len(df),
        "threshold": 0,
        "passed": row_count_passed,
        "severity": "blocking",
        "check_details": {"rule": "standardized event table must not be empty"},
    })

    user_null_rate = float(df["user_id"].isna().mean())
    checks_payload.append({
        "check_name": "user_id_null_rate",
        "entity": "events_standardized",
        "expected_value": 0.0,
        "actual_value": user_null_rate,
        "threshold": 0.001,
        "passed": user_null_rate <= 0.001,
        "severity": "blocking",
        "check_details": {"rule": "user_id null rate must be <= 0.1%"},
    })

    observed_event_types = set(df["event_type"].dropna().unique())
    invalid_event_types = sorted(observed_event_types - ALLOWED_EVENT_TYPES)
    checks_payload.append({
        "check_name": "event_type_domain_check",
        "entity": "events_standardized",
        "expected_value": len(ALLOWED_EVENT_TYPES),
        "actual_value": len(observed_event_types),
        "threshold": 0,
        "passed": len(invalid_event_types) == 0,
        "severity": "blocking",
        "check_details": {
            "allowed_event_types": sorted(ALLOWED_EVENT_TYPES),
            "observed_event_types": sorted(observed_event_types),
            "invalid_event_types": invalid_event_types,
        },
    })

    date_span_days = df["event_date"].nunique()
    checks_payload.append({
        "check_name": "date_coverage_check",
        "entity": "events_standardized",
        "expected_value": 30,
        "actual_value": date_span_days,
        "threshold": 30,
        "passed": date_span_days >= 30,
        "severity": "warning",
        "check_details": {"rule": "dataset should contain at least 30 event dates for demo usefulness"},
    })

    blocking_failed = [c for c in checks_payload if c["severity"] == "blocking" and not c["passed"]]
    status = "blocked" if blocking_failed else "success"

    with SessionLocal() as session:
        run = PipelineRunLog(
            job_type="data_quality_v0",
            run_date=run_date,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            status=status,
            rows_processed=len(df),
            rows_expected=len(df),
            quality_checks_passed=sum(c["passed"] for c in checks_payload),
            quality_checks_failed=sum(not c["passed"] for c in checks_payload),
            error_message=None if status == "success" else "Blocking data quality check failed",
            config_hash=hash_config("data_quality_v0_events_standardized"),
            retry_count=0,
            triggered_by="run_data_quality_v0",
        )
        session.add(run)
        session.flush()

        db_checks = [
            DataQualityCheck(
                run_id=run.id,
                check_name=c["check_name"],
                entity=c["entity"],
                check_date=run_date,
                expected_value=float(c["expected_value"]) if c["expected_value"] is not None else None,
                actual_value=float(c["actual_value"]) if c["actual_value"] is not None else None,
                threshold=float(c["threshold"]) if c["threshold"] is not None else None,
                passed=c["passed"],
                severity=c["severity"],
                check_details=c["check_details"],
            )
            for c in checks_payload
        ]

        session.add_all(db_checks)
        session.commit()

        report = {
            "artifact": "data_quality_service_report",
            "source_file": str(EVENTS_PATH),
            "run_id": run.id,
            "status": status,
            "rows_processed": len(df),
            "checks_passed": run.quality_checks_passed,
            "checks_failed": run.quality_checks_failed,
            "checks": checks_payload,
            "evidence_statement": "MetaSignal validated standardized event data before metric computation using reusable quality checks.",
        }

        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUT_PATH.write_text(json.dumps(report, indent=2, default=json_safe), encoding="utf-8")

        print("data_quality_v0 complete")
        print(f"status: {status}")
        print(f"rows_processed: {len(df)}")
        print(f"checks_passed: {run.quality_checks_passed}")
        print(f"checks_failed: {run.quality_checks_failed}")
        print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
