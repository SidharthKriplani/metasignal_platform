from __future__ import annotations

import json
import subprocess
from pathlib import Path


OUT_PATH = Path("outputs/reports/metasignal_final_completion_report.json")


def count_files(folder: str) -> int:
    path = Path(folder)
    if not path.exists():
        return 0
    return len([p for p in path.rglob("*") if p.is_file()])


def main() -> None:
    branch = subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()
    head = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    status_short = subprocess.check_output(["git", "status", "--short"], text=True).strip()

    payload = {
        "artifact": "metasignal_final_completion_report",
        "status": "core_v1_plus_streaming_extension_complete",
        "branch": branch,
        "head_commit_before_report": head,
        "working_tree_clean_before_report": status_short == "",
        "evidence_file_count": count_files("outputs/evidence"),
        "validation_file_count": count_files("outputs/validation"),
        "report_file_count": count_files("outputs/reports"),
        "streaming_file_count": count_files("outputs/streaming"),
        "doc_file_count": count_files("docs"),
        "completed_capabilities": [
            "metric_registry",
            "denominator_governance",
            "data_quality_gates",
            "failure_injection",
            "metric_conflict_detection",
            "deterministic_assignment",
            "srm_check",
            "cuped_readout",
            "cuped_aa_validation",
            "guardrail_first_decisioning",
            "right_censoring",
            "post_launch_validation",
            "anomaly_detection",
            "golden_scenarios",
            "fastapi_readout_layer",
            "api_smoke_test",
            "demo_narrative_docs",
            "architecture_docs",
            "interview_defense_docs",
            "resume_signal_summary",
            "streaming_srm_early_warning",
            "streaming_traffic_allocation_drift",
            "streaming_instrumentation_gap_detection",
            "streaming_consumer_lag_monitoring",
            "streaming_late_event_detection",
            "streaming_duplicate_detection",
            "streaming_dlq_quarantine",
            "streaming_provisional_anomaly_alerts",
            "stream_batch_reconciliation",
        ],
        "claim_boundary": "Solo-built, non-production, production-simulated flagship project. Streaming is provisional; batch remains authoritative.",
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("final_completion_report_v0 complete")
    print(f"status: {payload['status']}")
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
