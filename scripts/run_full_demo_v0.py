from __future__ import annotations

import subprocess
import sys


COMMANDS = [
    "PYTHONPATH=. python3 scripts/run_data_quality_v0.py",
    "PYTHONPATH=. python3 scripts/compute_metrics_v0.py",
    "PYTHONPATH=. python3 scripts/export_metric_results_summary.py",
    "PYTHONPATH=. python3 scripts/detect_metric_conflicts_v0.py",
    "PYTHONPATH=. python3 scripts/run_failure_injection_v0.py",
    "PYTHONPATH=. python3 scripts/generate_assignments_v0.py",
    "PYTHONPATH=. python3 scripts/run_srm_check_v0.py",
    "PYTHONPATH=. python3 scripts/run_cuped_v0.py",
    "PYTHONPATH=. python3 scripts/run_cuped_aa_validation_v0.py",
    "PYTHONPATH=. python3 scripts/run_guardrail_decision_v0.py",
    "PYTHONPATH=. python3 scripts/run_post_launch_validation_v0.py",
    "PYTHONPATH=. python3 scripts/run_anomaly_detector_v0.py",
    "PYTHONPATH=. python3 scripts/run_golden_scenarios_v0.py",
    "PYTHONPATH=. python3 scripts/export_core_artifacts.py",
    "PYTHONPATH=. python3 scripts/export_resume_signal_summary_v0.py",
    "PYTHONPATH=. python3 scripts/export_demo_narrative_v0.py",
    "PYTHONPATH=. python3 scripts/export_architecture_summary_v0.py",
    "PYTHONPATH=. python3 scripts/export_interview_defense_v0.py",
    "PYTHONPATH=. python3 scripts/smoke_test_api_v0.py",
    "PYTHONPATH=. python3 scripts/validate_evidence_artifacts_v0.py",
    "PYTHONPATH=. python3 scripts/show_core_report.py",
]


def main() -> None:
    print("\n=== MetaSignal Full Demo v0 ===\n")

    for i, cmd in enumerate(COMMANDS, start=1):
        print(f"\n[{i}/{len(COMMANDS)}] {cmd}")
        result = subprocess.run(cmd, shell=True)
        if result.returncode != 0:
            print(f"\nFAILED: {cmd}")
            sys.exit(result.returncode)

    print("\n=== MetaSignal Full Demo v0 completed successfully ===")
    print("Evidence folder: outputs/evidence")
    print("Validation folder: outputs/validation")
    print("Reports folder: outputs/reports")
    print("Docs folder: docs")


if __name__ == "__main__":
    main()
