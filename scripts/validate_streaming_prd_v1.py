from __future__ import annotations

import importlib
import json
from pathlib import Path


OUT_DIR = Path("outputs/streaming")
OUT_PATH = Path("outputs/validation/streaming_prd_v1_validation_report.json")

EXPECTED_ARTIFACTS = [
    "srm_streaming_alerts.json",
    "traffic_allocation_snapshots.json",
    "instrumentation_alerts.json",
    "consumer_lag_report.json",
    "late_event_report.json",
    "duplicate_event_report.json",
    "dlq_events.json",
    "streaming_metric_snapshots.json",
    "provisional_anomaly_alerts.json",
    "stream_quality_checks.json",
    "stream_batch_reconciliation_report.json",
    "streaming_health_report.json",
    "replay_run_log.json",
    "streaming_prd_scenario_report.json",
]


def load(name: str) -> dict:
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def main() -> None:
    checks = []
    module = importlib.import_module("src.metasignal.streaming.streaming_prd_v1")

    for class_name in [
        "EventSource",
        "AsyncSimulatorEventSource",
        "AsyncEventQueue",
        "StreamEventConsumer",
        "StreamValidator",
        "DeadLetterQueueWriter",
        "SRMDetector",
        "TrafficAllocationMonitor",
        "InstrumentationHealthMonitor",
        "ConsumerLagMonitor",
        "RealtimeMetricSnapshotter",
        "ProvisionalAnomalyDetector",
        "StreamBatchReconciler",
        "ReplayManager",
        "StreamQualityChecker",
    ]:
        checks.append({"check": f"class_exists_{class_name}", "passed": hasattr(module, class_name)})

    for name in EXPECTED_ARTIFACTS:
        path = OUT_DIR / name
        checks.append({"check": f"artifact_exists_{name}", "passed": path.exists() and path.stat().st_size > 0})

    srm = load("srm_streaming_alerts.json")
    instrumentation = load("instrumentation_alerts.json")
    lag = load("consumer_lag_report.json")
    late = load("late_event_report.json")
    duplicate = load("duplicate_event_report.json")
    dlq = load("dlq_events.json")
    snapshots = load("streaming_metric_snapshots.json")
    anomaly = load("provisional_anomaly_alerts.json")
    quality = load("stream_quality_checks.json")
    recon = load("stream_batch_reconciliation_report.json")
    replay = load("replay_run_log.json")
    scenario = load("streaming_prd_scenario_report.json")

    checks.extend([
        {"check": "srm_alerts_present", "passed": srm.get("alert_count", 0) > 0},
        {"check": "srm_batch_confirmation_status_present", "passed": all("batch_confirmation_status" in a for a in srm.get("alerts", []))},
        {"check": "instrumentation_alerts_present", "passed": instrumentation.get("alert_count", 0) > 0},
        {"check": "consumer_lag_spike_detected", "passed": any(w.get("alert_level") == "investigate" for w in lag.get("windows", []))},
        {"check": "late_events_detected", "passed": late.get("late_event_count", 0) > 0},
        {"check": "duplicates_detected", "passed": duplicate.get("duplicate_count", 0) > 0},
        {"check": "dlq_events_present", "passed": dlq.get("dlq_event_count", 0) > 0},
        {"check": "all_snapshots_provisional", "passed": snapshots.get("provisional_label") is True and all(s.get("provisional_label") is True for s in snapshots.get("snapshots", []))},
        {"check": "provisional_anomaly_present", "passed": anomaly.get("alert_count", 0) > 0},
        {"check": "stream_quality_checks_present", "passed": quality.get("check_count", 0) >= 50},
        {"check": "reconciliation_has_relative_delta", "passed": "relative_delta" in recon and "suspected_cause" in recon and recon.get("batch_remains_authoritative") is True},
        {"check": "replay_log_present", "passed": replay.get("batch_truth_unchanged") is True},
        {"check": "ten_streaming_scenarios_implemented", "passed": scenario.get("scenario_count") == 10 and scenario.get("implemented_count") == 10},
    ])

    checks.append({
        "check": "dlq_parquet_written_or_json_fallback_available",
        "passed": (OUT_DIR / "dlq_events.parquet").exists() or (OUT_DIR / "dlq_events_parquet_fallback.json").exists(),
    })

    passed_count = sum(c["passed"] for c in checks)
    status = "pass" if passed_count == len(checks) else "review"

    payload = {
        "artifact": "streaming_prd_v1_validation_report",
        "check_count": len(checks),
        "passed_count": passed_count,
        "failed_count": len(checks) - passed_count,
        "status": status,
        "checks": checks,
        "evidence_statement": "Streaming PRD v1 validation confirms modular EventSource/consumer/validator/monitor architecture, 10 failure scenarios, stream quality checks, replay, DLQ, provisional-only snapshots, and stream-batch reconciliation.",
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("streaming_prd_v1_validation complete")
    print(f"check_count: {len(checks)}")
    print(f"passed_count: {passed_count}")
    print(f"status: {status}")
    print(f"wrote {OUT_PATH}")

    if status != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
