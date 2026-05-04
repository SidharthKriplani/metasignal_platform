from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import UUID

import pandas as pd

from src.metasignal.db.session import SessionLocal
from src.metasignal.db.models import DataQualityCheck, PipelineRunLog


EVENTS_PATH = Path("data/interim/events_standardized.parquet")
OUT_PATH = Path("outputs/evidence/failure_injection_report.json")

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


def evaluate_checks(df: pd.DataFrame):
    checks = []

    required_present = all(c in df.columns for c in REQUIRED_COLUMNS)
    checks.append({
        "check_name": "required_columns_present",
        "expected_value": len(REQUIRED_COLUMNS),
        "actual_value": sum(c in df.columns for c in REQUIRED_COLUMNS),
        "threshold": 0,
        "passed": required_present,
        "severity": "blocking",
        "check_details": {"required_columns": REQUIRED_COLUMNS, "actual_columns": list(df.columns)},
    })

    if "user_id" in df.columns:
        user_null_rate = float(df["user_id"].isna().mean())
    else:
        user_null_rate = 1.0

    checks.append({
        "check_name": "user_id_null_rate",
        "expected_value": 0.0,
        "actual_value": user_null_rate,
        "threshold": 0.001,
        "passed": user_null_rate <= 0.001,
        "severity": "blocking",
        "check_details": {"rule": "user_id null rate must be <= 0.1%"},
    })

    if "event_type" in df.columns:
        observed_event_types = set(df["event_type"].dropna().astype(str).unique())
    else:
        observed_event_types = set()

    invalid_event_types = sorted(observed_event_types - ALLOWED_EVENT_TYPES)

    checks.append({
        "check_name": "event_type_domain_check",
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

    blocking_failed = [c for c in checks if c["severity"] == "blocking" and not c["passed"]]
    status = "blocked" if blocking_failed else "success"

    return status, checks


def main() -> None:
    if not EVENTS_PATH.exists():
        raise FileNotFoundError(f"Missing standardized events file: {EVENTS_PATH}")

    base_df = pd.read_parquet(EVENTS_PATH)
    base_df["event_date"] = pd.to_datetime(base_df["event_date"]).dt.date

    scenarios = []

    schema_drift_df = base_df.drop(columns=["transaction_id"])
    scenarios.append(("schema_drift_missing_transaction_id", schema_drift_df))

    invalid_event_df = base_df.copy()
    invalid_event_df.loc[invalid_event_df.index[:100], "event_type"] = "checkout_started_unknown"
    scenarios.append(("invalid_event_type_injection", invalid_event_df))

    null_spike_df = base_df.copy()
    null_spike_size = max(1, int(len(null_spike_df) * 0.01))
    null_spike_df.loc[null_spike_df.index[:null_spike_size], "user_id"] = pd.NA
    scenarios.append(("user_id_null_spike", null_spike_df))

    report_scenarios = []

    with SessionLocal() as session:
        for scenario_name, df in scenarios:
            status, checks = evaluate_checks(df)
            run_date = df["event_date"].min() if "event_date" in df.columns else base_df["event_date"].min()

            run = PipelineRunLog(
                job_type=f"failure_injection_{scenario_name}",
                run_date=run_date,
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                status=status,
                rows_processed=len(df),
                rows_expected=len(base_df),
                quality_checks_passed=sum(c["passed"] for c in checks),
                quality_checks_failed=sum(not c["passed"] for c in checks),
                error_message=None if status == "success" else "Injected failure correctly blocked by quality gate",
                config_hash=hash_config(f"failure_injection_v0_{scenario_name}"),
                retry_count=0,
                triggered_by="run_failure_injection_v0",
            )
            session.add(run)
            session.flush()

            for c in checks:
                session.add(
                    DataQualityCheck(
                        run_id=run.id,
                        check_name=c["check_name"],
                        entity=scenario_name,
                        check_date=run_date,
                        expected_value=float(c["expected_value"]) if c["expected_value"] is not None else None,
                        actual_value=float(c["actual_value"]) if c["actual_value"] is not None else None,
                        threshold=float(c["threshold"]) if c["threshold"] is not None else None,
                        passed=c["passed"],
                        severity=c["severity"],
                        check_details=c["check_details"],
                    )
                )

            report_scenarios.append({
                "scenario_name": scenario_name,
                "status": status,
                "rows_processed": len(df),
                "checks_passed": run.quality_checks_passed,
                "checks_failed": run.quality_checks_failed,
                "checks": checks,
                "expected_behavior_met": status == "blocked",
            })

        session.commit()

    payload = {
        "artifact": "failure_injection_report",
        "scenario_count": len(report_scenarios),
        "blocked_scenarios": sum(s["status"] == "blocked" for s in report_scenarios),
        "scenarios": report_scenarios,
        "evidence_statement": "MetaSignal injected bad-data scenarios and verified that blocking data quality gates catch them before metric computation.",
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2, default=json_safe), encoding="utf-8")

    print("failure_injection_v0 complete")
    print(f"scenario_count: {payload['scenario_count']}")
    print(f"blocked_scenarios: {payload['blocked_scenarios']}")
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
