from __future__ import annotations

import subprocess
import sys
from pathlib import Path


COMMANDS = [
    "PYTHONPATH=. python3 scripts/run_data_quality_v0.py",
    "PYTHONPATH=. python3 scripts/compute_metrics_v0.py",
    "PYTHONPATH=. python3 scripts/export_metric_results_summary.py",
    "PYTHONPATH=. python3 scripts/detect_metric_conflicts_v0.py",
    "PYTHONPATH=. python3 scripts/run_failure_injection_v0.py",
    "PYTHONPATH=. python3 scripts/generate_assignments_v0.py",
    "PYTHONPATH=. python3 scripts/run_srm_check_v0.py",
    "PYTHONPATH=. python3 scripts/run_cuped_v0.py",
    "PYTHONPATH=. python3 scripts/run_guardrail_decision_v0.py",
    "PYTHONPATH=. python3 scripts/run_post_launch_validation_v0.py",
    "PYTHONPATH=. python3 scripts/run_anomaly_detector_v0.py",
    "PYTHONPATH=. python3 scripts/run_golden_scenarios_v0.py",
    "PYTHONPATH=. python3 scripts/export_core_artifacts.py",
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


if __name__ == "__main__":
    main()
