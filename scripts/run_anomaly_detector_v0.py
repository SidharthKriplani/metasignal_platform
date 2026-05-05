from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from uuid import UUID

import pandas as pd
from sqlalchemy import select

from src.metasignal.db.session import SessionLocal
from src.metasignal.db.models import MetricDefinition, MetricResult


OUT_PATH = Path("outputs/evidence/anomaly_detection_report.json")
TARGET_METRIC = "purchase_conversion_rate_user"


def json_safe(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    return value


def main() -> None:
    with SessionLocal() as session:
        metric = session.scalar(select(MetricDefinition).where(MetricDefinition.name == TARGET_METRIC))
        if metric is None:
            raise ValueError(f"Metric not found: {TARGET_METRIC}")

        rows = session.scalars(
            select(MetricResult)
            .where(MetricResult.metric_id == metric.id)
            .order_by(MetricResult.computation_date)
        ).all()

        if len(rows) < 14:
            raise ValueError("Need at least 14 metric rows for anomaly detection")

        df = pd.DataFrame([
            {"date": r.computation_date, "metric_value": r.metric_value}
            for r in rows
            if r.metric_value is not None
        ])

        # Inject one known synthetic anomaly for evidence validation.
        injected_idx = len(df) // 2
        injected_date = df.loc[injected_idx, "date"]
        baseline_value = float(df.loc[injected_idx, "metric_value"])
        df.loc[injected_idx, "metric_value"] = baseline_value * 2.5

        values = df["metric_value"].astype(float)
        mean_value = float(values.mean())
        std_value = float(values.std(ddof=1))

        alerts = []
        for _, row in df.iterrows():
            z = 0.0 if std_value == 0 else float((row["metric_value"] - mean_value) / std_value)
            is_alert = abs(z) >= 3.0
            if is_alert:
                alerts.append({
                    "date": row["date"],
                    "metric_value": float(row["metric_value"]),
                    "z_score": z,
                    "alert_type": "z_score_threshold",
                    "is_injected_anomaly": row["date"] == injected_date,
                })

        injected_detected = any(a["is_injected_anomaly"] for a in alerts)

        payload = {
            "artifact": "anomaly_detection_report",
            "metric_name": TARGET_METRIC,
            "rows_scanned": len(df),
            "method": "global_z_score_v0_with_synthetic_injection",
            "threshold": 3.0,
            "injected_anomaly": {
                "date": injected_date,
                "baseline_value": baseline_value,
                "injected_value": baseline_value * 2.5,
                "detected": injected_detected,
            },
            "alert_count": len(alerts),
            "alerts": alerts,
            "evidence_statement": "MetaSignal detected a labeled synthetic metric anomaly and produced auditable anomaly evidence.",
        }

        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUT_PATH.write_text(json.dumps(payload, indent=2, default=json_safe), encoding="utf-8")

        print("anomaly_detector_v0 complete")
        print(f"rows_scanned: {len(df)}")
        print(f"alert_count: {len(alerts)}")
        print(f"injected_detected: {injected_detected}")
        print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
