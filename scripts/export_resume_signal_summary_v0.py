from __future__ import annotations

import json
from pathlib import Path


JSON_OUT = Path("outputs/reports/metasignal_resume_signal_summary.json")
MD_OUT = Path("outputs/reports/metasignal_resume_signal_summary.md")


SIGNALS = [
    {
        "capability": "Metric registry and denominator governance",
        "proof": "Versioned metric definitions with explicit numerator, denominator, grain, owner, and guardrail fields.",
        "artifact": "outputs/evidence/metric_registry.json",
        "interview_signal": "Can explain why conversion-rate denominator inconsistency breaks experimentation decisions.",
    },
    {
        "capability": "Data quality gates before compute",
        "proof": "Reusable quality service and failure-injection scenarios create blocked/warn/pass evidence.",
        "artifact": "outputs/evidence/data_quality_service_report.json",
        "interview_signal": "Understands that serving no metric is better than serving a metric computed on bad data.",
    },
    {
        "capability": "Metric conflict detection",
        "proof": "Detector identifies active metrics with conflicting denominator logic.",
        "artifact": "outputs/evidence/metric_conflict_report.json",
        "interview_signal": "Can reason about metric governance, not just dashboards.",
    },
    {
        "capability": "Deterministic experiment assignment and SRM",
        "proof": "Hash-based assignment creates 20k users and SRM check validates treatment/control balance.",
        "artifact": "outputs/evidence/srm_check_report.json",
        "interview_signal": "Can defend assignment validity and sample-ratio mismatch checks.",
    },
    {
        "capability": "CUPED experiment evaluation",
        "proof": "CUPED readout stores lift, p-value, variance reduction, and evaluation artifact.",
        "artifact": "outputs/evidence/cuped_experiment_readout.json",
        "interview_signal": "Can explain variance reduction and pre-period covariate adjustment.",
    },
    {
        "capability": "CUPED A/A validation",
        "proof": "1000 synthetic A/A runs validate false-positive control and p-value uniformity.",
        "artifact": "outputs/validation/cuped_aa_validation_report.json",
        "interview_signal": "Can show the statistical method was validated, not merely implemented.",
    },
    {
        "capability": "Guardrail-first decisioning",
        "proof": "Positive primary metric is blocked because refund guardrail breaches tolerance.",
        "artifact": "outputs/evidence/guardrail_decision_report.json",
        "interview_signal": "Can reason about asymmetric product harm and why guardrails are gates.",
    },
    {
        "capability": "Right-censoring and delayed guardrails",
        "proof": "Post-launch validation marks delayed refund guardrail as immature/right-censored.",
        "artifact": "outputs/evidence/post_launch_validation_report.json",
        "interview_signal": "Can explain why early readouts can be invalid for delayed metrics.",
    },
    {
        "capability": "Anomaly detection",
        "proof": "DOW-adjusted rolling baseline detects labeled synthetic metric anomaly.",
        "artifact": "outputs/evidence/anomaly_detection_report.json",
        "interview_signal": "Can distinguish metric movement from seasonality/noise/data-quality failure.",
    },
    {
        "capability": "Golden scenario suite",
        "proof": "Deterministic scenario suite validates registry, quality, assignment, CUPED, guardrail, and audit behavior.",
        "artifact": "outputs/evidence/golden_scenario_suite_report.json",
        "interview_signal": "Can prove system behavior through repeatable tests.",
    },
]


def main() -> None:
    payload = {
        "artifact": "metasignal_resume_signal_summary",
        "project_positioning": "Production-simulated experimentation, metrics intelligence, and decision-audit platform.",
        "resume_bullet_candidate": "Built MetaSignal, a production-simulated experimentation intelligence platform with versioned metric registry, denominator-conflict detection, data-quality gates, deterministic assignment, SRM checks, CUPED readouts, A/A validation, guardrail-first decisioning, right-censoring, anomaly detection, golden scenarios, and auditable evidence artifacts.",
        "signal_count": len(SIGNALS),
        "signals": SIGNALS,
    }

    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# MetaSignal Resume Signal Summary",
        "",
        "**Positioning:** Production-simulated experimentation, metrics intelligence, and decision-audit platform.",
        "",
        "## Resume Bullet Candidate",
        "",
        payload["resume_bullet_candidate"],
        "",
        "## Evidence Matrix",
        "",
        "| Capability | Proof | Artifact | Interview Signal |",
        "|---|---|---|---|",
    ]

    for s in SIGNALS:
        lines.append(
            f"| {s['capability']} | {s['proof']} | `{s['artifact']}` | {s['interview_signal']} |"
        )

    MD_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("resume_signal_summary_v0 complete")
    print(f"signal_count: {len(SIGNALS)}")
    print(f"wrote {JSON_OUT}")
    print(f"wrote {MD_OUT}")


if __name__ == "__main__":
    main()
