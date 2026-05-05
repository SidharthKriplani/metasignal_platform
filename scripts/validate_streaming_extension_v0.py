from __future__ import annotations

import json
from pathlib import Path


OUT_DIR = Path("outputs/streaming")
OUT_PATH = Path("outputs/validation/streaming_extension_validation_report.json")

EXPECTED_FILES = [
    "streaming_metric_snapshots.json",
    "srm_streaming_alerts.json",
    "traffic_allocation_snapshots.json",
    "instrumentation_alerts.json",
    "consumer_lag_report.json",
    "late_event_report.json",
    "duplicate_event_report.json",
    "dlq_events.json",
    "provisional_anomaly_alerts.json",
    "stream_batch_reconciliation_report.json",
    "streaming_health_report.json",
]


def load_json(name: str) -> dict:
    path = OUT_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing streaming artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    checks = []

    for name in EXPECTED_FILES:
        path = OUT_DIR / name
        checks.append({
            "check": f"{name}_exists",
            "passed": path.exists() and path.stat().st_size > 0,
            "path": str(path),
        })

    srm = load_json("srm_streaming_alerts.json")
    instrumentation = load_json("instrumentation_alerts.json")
    late = load_json("late_event_report.json")
    duplicate = load_json("duplicate_event_report.json")
    dlq = load_json("dlq_events.json")
    anomaly = load_json("provisional_anomaly_alerts.json")
    reconciliation = load_json("stream_batch_reconciliation_report.json")
    health = load_json("streaming_health_report.json")
    snapshots = load_json("streaming_metric_snapshots.json")

    checks.extend([
        {
            "check": "srm_early_warning_detected",
            "passed": srm.get("alert_count", 0) > 0,
            "observed": srm.get("alert_count", 0),
        },
        {
            "check": "instrumentation_gap_detected",
            "passed": instrumentation.get("alert_count", 0) > 0,
            "observed": instrumentation.get("alert_count", 0),
        },
        {
            "check": "late_events_detected",
            "passed": late.get("late_event_count", 0) > 0,
            "observed": late.get("late_event_count", 0),
        },
        {
            "check": "duplicates_detected",
            "passed": duplicate.get("duplicate_count", 0) > 0,
            "observed": duplicate.get("duplicate_count", 0),
        },
        {
            "check": "dlq_events_quarantined",
            "passed": dlq.get("dlq_event_count", 0) > 0,
            "observed": dlq.get("dlq_event_count", 0),
        },
        {
            "check": "provisional_anomaly_detected",
            "passed": anomaly.get("alert_count", 0) > 0,
            "observed": anomaly.get("alert_count", 0),
        },
        {
            "check": "stream_batch_reconciliation_passed",
            "passed": reconciliation.get("reconciliation_status") == "pass" and reconciliation.get("batch_remains_authoritative") is True,
            "observed": reconciliation.get("reconciliation_status"),
        },
        {
            "check": "streaming_snapshots_are_provisional",
            "passed": snapshots.get("provisional_label") is True and all(s.get("provisional_label") is True for s in snapshots.get("snapshots", [])),
            "observed": snapshots.get("snapshot_count", 0),
        },
        {
            "check": "streaming_health_requires_investigation",
            "passed": health.get("overall_health_status") == "investigate",
            "observed": health.get("overall_health_status"),
        },
    ])

    passed_count = sum(c["passed"] for c in checks)
    status = "pass" if passed_count == len(checks) else "review"

    payload = {
        "artifact": "streaming_extension_validation_report",
        "check_count": len(checks),
        "passed_count": passed_count,
        "failed_count": len(checks) - passed_count,
        "status": status,
        "checks": checks,
        "evidence_statement": "MetaSignal streaming extension validates provisional SRM, traffic allocation drift, instrumentation gap, consumer lag, late-event, duplicate, DLQ, provisional anomaly, and stream-batch reconciliation behavior.",
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("streaming_extension_validation_v0 complete")
    print(f"check_count: {len(checks)}")
    print(f"passed_count: {passed_count}")
    print(f"status: {status}")
    print(f"wrote {OUT_PATH}")

    if status != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
