from __future__ import annotations

import json
from pathlib import Path


JSON_OUT = Path("outputs/reports/metasignal_architecture_summary.json")
MD_OUT = Path("docs/METASIGNAL_ARCHITECTURE.md")


LAYERS = [
    {
        "layer": "Event substrate",
        "components": ["RetailRocket standardized parquet", "event_date/user_id/event_type normalization"],
        "purpose": "Provides a real high-volume event base instead of toy CSV data.",
    },
    {
        "layer": "Storage and audit",
        "components": ["Postgres", "SQLAlchemy models", "Alembic migrations"],
        "purpose": "Stores metric definitions, results, pipeline runs, experiments, evaluations, decisions, and quality checks.",
    },
    {
        "layer": "Metric governance",
        "components": ["Metric registry", "denominator types", "metric conflict detector"],
        "purpose": "Prevents teams from using incompatible definitions of the same business metric.",
    },
    {
        "layer": "Data quality",
        "components": ["required-column checks", "row-count checks", "null checks", "domain checks", "failure injection"],
        "purpose": "Blocks compute when data quality is not trustworthy.",
    },
    {
        "layer": "Experiment evaluation",
        "components": ["deterministic assignment", "SRM check", "CUPED", "A/A validation"],
        "purpose": "Validates assignment quality and reduces variance before experiment decisions.",
    },
    {
        "layer": "Decisioning",
        "components": ["guardrail-first decision engine", "decision log", "human review fields"],
        "purpose": "Turns metric evidence into auditable ship/hold decisions.",
    },
    {
        "layer": "Reliability and validation",
        "components": ["right-censoring", "post-launch validation", "anomaly detection", "golden scenarios"],
        "purpose": "Shows operational maturity beyond a one-off notebook analysis.",
    },
    {
        "layer": "Serving",
        "components": ["FastAPI", "smoke-tested endpoints", "evidence/validation retrieval"],
        "purpose": "Exposes the system as a platform, not just terminal scripts.",
    },
]


def main() -> None:
    payload = {
        "artifact": "metasignal_architecture_summary",
        "architecture_style": "Batch-authoritative, production-simulated experimentation intelligence platform.",
        "non_goals": [
            "Not a production SaaS system",
            "Not a frontend-first dashboard",
            "Not a real-time decisioning engine",
            "Not claiming real production traffic or real users",
        ],
        "layers": LAYERS,
    }

    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    MD_OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# MetaSignal Architecture",
        "",
        "## Architecture Style",
        "",
        payload["architecture_style"],
        "",
        "## Non-Goals",
        "",
    ]

    for item in payload["non_goals"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Layers", ""])

    for layer in LAYERS:
        lines.extend([
            f"### {layer['layer']}",
            "",
            f"**Purpose:** {layer['purpose']}",
            "",
            "**Components:**",
        ])
        for component in layer["components"]:
            lines.append(f"- {component}")
        lines.append("")

    MD_OUT.write_text("\n".join(lines), encoding="utf-8")

    print("architecture_summary_v0 complete")
    print(f"layer_count: {len(LAYERS)}")
    print(f"wrote {JSON_OUT}")
    print(f"wrote {MD_OUT}")


if __name__ == "__main__":
    main()
