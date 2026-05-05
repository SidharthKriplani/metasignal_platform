from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy import select

from src.metasignal.db.session import SessionLocal
from src.metasignal.db.models import MetricDefinition


OUT_PATH = Path("outputs/evidence/metric_conflict_report.json")


def json_safe(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    return value


def metric_family(metric_name: str) -> str:
    name = metric_name.lower()

    if "conversion_rate" in name:
        return "conversion_rate"

    if "refund_rate" in name:
        return "refund_rate"

    return name


def main() -> None:
    with SessionLocal() as session:
        metrics = session.scalars(
            select(MetricDefinition).where(MetricDefinition.is_active == True)
        ).all()

        grouped = {}
        for metric in metrics:
            family = metric_family(metric.name)
            grouped.setdefault(family, []).append(metric)

        conflicts = []

        for family, family_metrics in grouped.items():
            denominator_types = sorted({m.denominator_type for m in family_metrics})
            grains = sorted({m.grain for m in family_metrics})
            entity_types = sorted({m.entity_type for m in family_metrics})

            has_conflict = (
                len(family_metrics) > 1
                and (
                    len(denominator_types) > 1
                    or len(grains) > 1
                    or len(entity_types) > 1
                )
            )

            if has_conflict:
                conflicts.append(
                    {
                        "metric_family": family,
                        "conflict_type": "active_metric_semantic_conflict",
                        "reason": "Multiple active metrics appear to describe the same business concept but use different denominator/grain/entity logic.",
                        "denominator_types": denominator_types,
                        "grains": grains,
                        "entity_types": entity_types,
                        "affected_metrics": [
                            {
                                "id": m.id,
                                "name": m.name,
                                "display_name": m.display_name,
                                "denominator_type": m.denominator_type,
                                "denominator_sql": m.denominator_sql,
                                "grain": m.grain,
                                "entity_type": m.entity_type,
                                "owner": m.owner,
                                "version": m.version,
                                "config_hash": m.config_hash,
                            }
                            for m in family_metrics
                        ],
                        "recommended_action": "Require owner review and mark one metric as authoritative before using this metric family in experiment decisions.",
                    }
                )

        payload = {
            "artifact": "metric_conflict_report",
            "active_metric_count": len(metrics),
            "families_scanned": len(grouped),
            "conflict_count": len(conflicts),
            "conflicts": conflicts,
            "evidence_statement": "MetaSignal scanned active metric definitions and detected denominator/grain conflicts across semantically similar metric families.",
        }

        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUT_PATH.write_text(json.dumps(payload, indent=2, default=json_safe), encoding="utf-8")

        print("metric_conflict_detector_v0 complete")
        print(f"active_metric_count: {len(metrics)}")
        print(f"families_scanned: {len(grouped)}")
        print(f"conflict_count: {len(conflicts)}")
        print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
