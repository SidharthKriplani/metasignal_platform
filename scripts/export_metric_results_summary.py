from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy import select

from src.metasignal.db.session import SessionLocal
from src.metasignal.db.models import MetricDefinition, MetricResult


OUT_PATH = Path("outputs/evidence/metric_results_summary.json")


def json_safe(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    return value


def main() -> None:
    with SessionLocal() as session:
        metrics = session.scalars(select(MetricDefinition)).all()
        metric_lookup = {m.id: m for m in metrics}

        rows = session.scalars(
            select(MetricResult).order_by(MetricResult.computation_date, MetricResult.metric_id)
        ).all()

        by_metric = {}
        for r in rows:
            metric = metric_lookup[r.metric_id]
            bucket = by_metric.setdefault(
                metric.name,
                {
                    "metric_name": metric.name,
                    "denominator_type": metric.denominator_type,
                    "grain": metric.grain,
                    "is_guardrail": metric.is_guardrail,
                    "row_count": 0,
                    "min_date": None,
                    "max_date": None,
                    "min_value": None,
                    "max_value": None,
                    "avg_value": None,
                    "sample_rows": [],
                    "_values": [],
                },
            )

            bucket["row_count"] += 1
            bucket["_values"].append(r.metric_value)

            d = r.computation_date
            bucket["min_date"] = d if bucket["min_date"] is None else min(bucket["min_date"], d)
            bucket["max_date"] = d if bucket["max_date"] is None else max(bucket["max_date"], d)

            if r.metric_value is not None:
                bucket["min_value"] = r.metric_value if bucket["min_value"] is None else min(bucket["min_value"], r.metric_value)
                bucket["max_value"] = r.metric_value if bucket["max_value"] is None else max(bucket["max_value"], r.metric_value)

            if len(bucket["sample_rows"]) < 5:
                bucket["sample_rows"].append(
                    {
                        "date": r.computation_date,
                        "numerator": r.numerator_value,
                        "denominator": r.denominator_value,
                        "metric_value": r.metric_value,
                        "quality_passed": r.quality_passed,
                    }
                )

        for bucket in by_metric.values():
            values = [v for v in bucket["_values"] if v is not None]
            bucket["avg_value"] = sum(values) / len(values) if values else None
            del bucket["_values"]

        payload = {
            "artifact": "metric_results_summary",
            "source": "metric_results table",
            "total_metric_result_rows": len(rows),
            "metric_count": len(by_metric),
            "metrics": list(by_metric.values()),
            "evidence_statement": "MetaSignal computed daily metric results from standardized RetailRocket parquet and inserted them into Postgres.",
        }

        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUT_PATH.write_text(json.dumps(payload, indent=2, default=json_safe), encoding="utf-8")

        print(f"wrote {OUT_PATH}")
        print(f"total_metric_result_rows: {len(rows)}")
        print(f"metric_count: {len(by_metric)}")


if __name__ == "__main__":
    main()
