from __future__ import annotations

import json
from pathlib import Path


JSON_OUT = Path("outputs/reports/metasignal_demo_narrative.json")
MD_OUT = Path("docs/METASIGNAL_DEMO_NARRATIVE.md")


STEPS = [
    {
        "step": 1,
        "title": "Real event substrate",
        "proof": "RetailRocket events are standardized into a parquet substrate with 2.75M rows.",
        "artifact": "data/interim/events_standardized.parquet",
    },
    {
        "step": 2,
        "title": "Quality gates before compute",
        "proof": "Data quality checks run before metric computation and can block bad runs.",
        "artifact": "outputs/evidence/data_quality_service_report.json",
    },
    {
        "step": 3,
        "title": "Metric registry and denominator governance",
        "proof": "Metric definitions explicitly store numerator, denominator, grain, owner, version, and guardrail fields.",
        "artifact": "outputs/evidence/metric_registry.json",
    },
    {
        "step": 4,
        "title": "Metric conflict detection",
        "proof": "Conflicting conversion-rate denominators are detected and documented.",
        "artifact": "outputs/evidence/metric_conflict_report.json",
    },
    {
        "step": 5,
        "title": "Experiment assignment and SRM",
        "proof": "Deterministic assignment creates 20k users and validates treatment/control balance.",
        "artifact": "outputs/evidence/srm_check_report.json",
    },
    {
        "step": 6,
        "title": "CUPED readout plus A/A validation",
        "proof": "CUPED evaluation produces lift/p-value/variance reduction and A/A validation checks false-positive control.",
        "artifact": "outputs/evidence/cuped_experiment_readout.json",
    },
    {
        "step": 7,
        "title": "Guardrail-first decisioning",
        "proof": "A statistically positive primary metric is blocked because refund guardrail breaches tolerance.",
        "artifact": "outputs/evidence/guardrail_decision_report.json",
    },
    {
        "step": 8,
        "title": "Right-censoring and post-launch validation",
        "proof": "Delayed guardrails are marked immature/right-censored before final decisioning.",
        "artifact": "outputs/evidence/post_launch_validation_report.json",
    },
    {
        "step": 9,
        "title": "Anomaly detection",
        "proof": "DOW-adjusted rolling baseline detects a labeled synthetic metric anomaly.",
        "artifact": "outputs/evidence/anomaly_detection_report.json",
    },
    {
        "step": 10,
        "title": "API layer",
        "proof": "FastAPI exposes metrics, experiment readout, data quality, evidence, validation, and resume-signal endpoints.",
        "artifact": "outputs/validation/api_smoke_test_report.json",
    },
]


def main() -> None:
    payload = {
        "artifact": "metasignal_demo_narrative",
        "positioning": "MetaSignal is a production-simulated experimentation intelligence platform with concrete database rows, JSON evidence, validation reports, and API endpoints.",
        "demo_story": "The demo shows how an experiment moves from event ingestion to metric governance, quality checks, assignment validation, CUPED evaluation, guardrail-first decisioning, right-censoring, anomaly detection, and API-backed evidence retrieval.",
        "steps": STEPS,
    }

    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    MD_OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# MetaSignal Demo Narrative",
        "",
        "## Positioning",
        "",
        payload["positioning"],
        "",
        "## Demo Story",
        "",
        payload["demo_story"],
        "",
        "## Walkthrough",
        "",
    ]

    for item in STEPS:
        lines.extend([
            f"### {item['step']}. {item['title']}",
            "",
            f"**Proof:** {item['proof']}",
            "",
            f"**Artifact:** `{item['artifact']}`",
            "",
        ])

    MD_OUT.write_text("\n".join(lines), encoding="utf-8")

    print("demo_narrative_v0 complete")
    print(f"step_count: {len(STEPS)}")
    print(f"wrote {JSON_OUT}")
    print(f"wrote {MD_OUT}")


if __name__ == "__main__":
    main()
