from __future__ import annotations

import json
import subprocess
from pathlib import Path


OUT_PATH = Path("outputs/reports/metasignal_prd_completion_report_v1.json")


COMMANDS = [
    ["PYTHONPATH=.", "python3", "scripts/seed_operational_history_v1.py"],
    ["PYTHONPATH=.", "python3", "scripts/run_prd_core_validation_suite_v1.py"],
    ["PYTHONPATH=.", "python3", "scripts/test_override_enforcement_v1.py"],
    ["PYTHONPATH=.", "python3", "scripts/show_streaming_demo.py"],
    ["PYTHONPATH=.", "python3", "scripts/validate_streaming_prd_v1.py"],
]


REQUIRED_ARTIFACTS = [
    "outputs/evidence/operational_history_60_day_report.json",
    "outputs/evidence/golden_scenario_suite_v1_report.json",
    "outputs/evidence/causal_trap_detection_report.json",
    "outputs/evidence/anomaly_backtest_report.json",
    "outputs/validation/cuped_edge_case_validation_report.json",
    "outputs/validation/prd_core_validation_suite_v1_summary.json",
    "outputs/validation/override_reason_enforcement_report.json",
    "outputs/streaming/srm_streaming_alerts.json",
    "outputs/streaming/traffic_allocation_snapshots.json",
    "outputs/streaming/instrumentation_alerts.json",
    "outputs/streaming/consumer_lag_report.json",
    "outputs/streaming/late_event_report.json",
    "outputs/streaming/duplicate_event_report.json",
    "outputs/streaming/dlq_events.json",
    "outputs/streaming/dlq_events.parquet",
    "outputs/streaming/streaming_metric_snapshots.json",
    "outputs/streaming/provisional_anomaly_alerts.json",
    "outputs/streaming/stream_quality_checks.json",
    "outputs/streaming/stream_batch_reconciliation_report.json",
    "outputs/streaming/streaming_health_report.json",
    "outputs/streaming/replay_run_log.json",
    "outputs/streaming/streaming_prd_scenario_report.json",
    "outputs/validation/streaming_prd_v1_validation_report.json",
]


def run_command(command: list[str]) -> dict:
    env = None
    cmd = command

    if command[0].startswith("PYTHONPATH="):
        env = {"PYTHONPATH": command[0].split("=", 1)[1]}
        cmd = command[1:]

    result = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        env={**dict(__import__("os").environ), **(env or {})},
    )

    return {
        "command": " ".join(command),
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-2000:],
        "stderr_tail": result.stderr[-2000:],
        "passed": result.returncode == 0,
    }


def main() -> None:
    command_results = []

    for command in COMMANDS:
        print("RUN:", " ".join(command))
        result = run_command(command)
        command_results.append(result)
        print("returncode:", result["returncode"])
        if result["returncode"] != 0:
            print(result["stdout_tail"])
            print(result["stderr_tail"])
            raise SystemExit(1)

    artifact_checks = []
    for artifact in REQUIRED_ARTIFACTS:
        p = Path(artifact)
        artifact_checks.append({
            "artifact": artifact,
            "exists": p.exists(),
            "non_empty": p.exists() and p.stat().st_size > 0,
        })

    completed_core_prd_items = [
        "60_day_operational_history",
        "13_failure_simulation_scenarios",
        "7_prd_metric_registry_entries",
        "metric_conflicts",
        "backfill_jobs",
        "system_health_reports",
        "cuped_edge_cases",
        "12_golden_scenarios",
        "peeking_warning",
        "novelty_flag",
        "simpsons_segment_reversal_flag",
        "20_event_synthetic_anomaly_backtest",
        "override_reason_api_enforcement",
    ]

    completed_streaming_prd_items = [
        "EventSource_interface",
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
        "10_streaming_failure_scenarios",
        "dlq_events_parquet",
        "stream_quality_checks",
        "replay_run_log",
        "stream_batch_reconciliation",
        "provisional_only_streaming_artifacts",
    ]

    status = (
        "pass"
        if all(r["passed"] for r in command_results)
        and all(c["exists"] and c["non_empty"] for c in artifact_checks)
        else "review"
    )

    payload = {
        "artifact": "metasignal_prd_completion_report_v1",
        "status": status,
        "core_prd_completion_status": "implemented_at_repo_v1_evidence_level",
        "streaming_prd_completion_status": "implemented_at_repo_v1_evidence_level",
        "completed_core_prd_items": completed_core_prd_items,
        "completed_streaming_prd_items": completed_streaming_prd_items,
        "command_results": command_results,
        "artifact_checks": artifact_checks,
        "claim_boundary": "This remains solo-built, non-production, production-simulated. PRD completion here means implemented as executable repo evidence and artifacts, not real production deployment.",
        "evidence_statement": "MetaSignal now has executable evidence for the Core PRD and Streaming Extension PRD: operational history, core validation, override enforcement, modular streaming, scenarios, stream quality, replay, and reconciliation.",
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("metasignal_prd_complete_v1 complete")
    print(f"status: {status}")
    print(f"core_items: {len(completed_core_prd_items)}")
    print(f"streaming_items: {len(completed_streaming_prd_items)}")
    print(f"artifact_checks: {len(artifact_checks)}")
    print(f"wrote {OUT_PATH}")

    if status != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
