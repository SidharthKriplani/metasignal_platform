from __future__ import annotations

import json
from pathlib import Path


OUT_PATH = Path("outputs/validation/evidence_artifact_validation_report.json")

EXPECTED_ARTIFACTS = [
    "outputs/evidence/core_evidence_manifest.json",
    "outputs/evidence/decision_audit_log.json",
    "outputs/evidence/experiment_readout.json",
    "outputs/evidence/metric_registry.json",
    "outputs/evidence/metric_results_summary.json",
    "outputs/evidence/pipeline_quality_report.json",
    "outputs/evidence/simulation_scenarios.json",
    "outputs/evidence/data_quality_service_report.json",
    "outputs/evidence/metric_conflict_report.json",
    "outputs/evidence/failure_injection_report.json",
    "outputs/evidence/experiment_assignment_balance.json",
    "outputs/evidence/srm_check_report.json",
    "outputs/evidence/cuped_experiment_readout.json",
    "outputs/evidence/guardrail_decision_report.json",
    "outputs/evidence/post_launch_validation_report.json",
    "outputs/evidence/anomaly_detection_report.json",
    "outputs/evidence/golden_scenario_suite_report.json",
    "outputs/validation/cuped_aa_validation_report.json",
    "outputs/validation/api_smoke_test_report.json",
    "outputs/validation/streaming_extension_validation_report.json",
    "outputs/reports/metasignal_resume_signal_summary.json",
    "outputs/reports/metasignal_demo_narrative.json",
    "outputs/reports/metasignal_architecture_summary.json",
    "outputs/reports/metasignal_interview_defense.json",
    "outputs/reports/metasignal_core_completion_report.json",
    "outputs/reports/metasignal_streaming_extension_summary.json",
    "outputs/streaming/streaming_metric_snapshots.json",
    "outputs/streaming/srm_streaming_alerts.json",
    "outputs/streaming/traffic_allocation_snapshots.json",
    "outputs/streaming/instrumentation_alerts.json",
    "outputs/streaming/consumer_lag_report.json",
    "outputs/streaming/late_event_report.json",
    "outputs/streaming/duplicate_event_report.json",
    "outputs/streaming/dlq_events.json",
    "outputs/streaming/provisional_anomaly_alerts.json",
    "outputs/streaming/stream_batch_reconciliation_report.json",
    "outputs/streaming/streaming_health_report.json",
]


def load_json_status(path: Path) -> dict:
    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "valid_json": False,
            "size_bytes": 0,
            "artifact": None,
        }

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        valid_json = True
        artifact = data.get("artifact")
    except Exception:
        valid_json = False
        artifact = None

    return {
        "path": str(path),
        "exists": True,
        "valid_json": valid_json,
        "size_bytes": path.stat().st_size,
        "artifact": artifact,
    }


def main() -> None:
    checks = [load_json_status(Path(p)) for p in EXPECTED_ARTIFACTS]

    missing = [c for c in checks if not c["exists"]]
    invalid = [c for c in checks if c["exists"] and not c["valid_json"]]
    empty = [c for c in checks if c["exists"] and c["size_bytes"] == 0]

    status = "pass" if not missing and not invalid and not empty else "review"

    payload = {
        "artifact": "evidence_artifact_validation_report",
        "expected_artifact_count": len(EXPECTED_ARTIFACTS),
        "present_artifact_count": sum(c["exists"] for c in checks),
        "valid_json_count": sum(c["valid_json"] for c in checks),
        "missing_count": len(missing),
        "invalid_json_count": len(invalid),
        "empty_file_count": len(empty),
        "status": status,
        "checks": checks,
        "evidence_statement": "MetaSignal validates that core evidence, experiment evidence, anomaly evidence, and CUPED validation artifacts exist as concrete files.",
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("evidence_artifact_validation_v0 complete")
    print(f"expected_artifact_count: {payload['expected_artifact_count']}")
    print(f"present_artifact_count: {payload['present_artifact_count']}")
    print(f"valid_json_count: {payload['valid_json_count']}")
    print(f"status: {status}")
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
