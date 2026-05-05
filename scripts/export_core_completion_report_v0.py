from __future__ import annotations

import json
import subprocess
from pathlib import Path


OUT_PATH = Path("outputs/reports/metasignal_core_completion_report.json")


def count_files(folder: str) -> int:
    path = Path(folder)
    if not path.exists():
        return 0
    return len([p for p in path.rglob("*") if p.is_file()])


def main() -> None:
    branch = subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()
    head = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()

    payload = {
        "artifact": "metasignal_core_completion_report",
        "status": "core_v1_complete_before_streaming_extension",
        "branch": branch,
        "head_commit_before_report": head,
        "evidence_file_count": count_files("outputs/evidence"),
        "validation_file_count": count_files("outputs/validation"),
        "report_file_count": count_files("outputs/reports"),
        "doc_file_count": count_files("docs"),
        "completed_core_capabilities": [
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
            "demo_narrative_docs",
            "architecture_docs",
            "interview_defense_docs",
            "resume_signal_summary",
        ],
        "next_phase": "streaming_extension",
        "claim_boundary": "Solo-built, non-production, production-simulated flagship project.",
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("core_completion_report_v0 complete")
    print(f"status: {payload['status']}")
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
