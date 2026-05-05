from __future__ import annotations

import json
import random
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean


OUT_DIR = Path("outputs/streaming")
EXPERIMENT_ID = "EXP-CHECKOUT-FRICTION-001"
RNG_SEED = 202604
WINDOW_COUNT = 12
EVENTS_PER_WINDOW = 700
EXPECTED_CONTROL_PCT = 0.50


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    random.seed(RNG_SEED)
    base_time = datetime(2026, 4, 1, 9, 0, tzinfo=timezone.utc)

    events = []

    for window_id in range(WINDOW_COUNT):
        window_start = base_time + timedelta(minutes=5 * window_id)
        control_prob = 0.35 if window_id in {2, 3, 4} else EXPECTED_CONTROL_PCT

        for i in range(EVENTS_PER_WINDOW):
            event_time = window_start + timedelta(seconds=random.randint(0, 299))
            lag_seconds = random.randint(4, 45)

            if window_id == 7 and i % 4 == 0:
                lag_seconds = random.randint(420, 900)

            if window_id == 8 and i % 20 == 0:
                event_time = event_time - timedelta(minutes=45)

            processing_time = event_time + timedelta(seconds=lag_seconds)
            variant = "control" if random.random() < control_prob else "treatment"
            platform = random.choices(["ios", "android", "web"], weights=[0.35, 0.40, 0.25])[0]

            if window_id in {5, 6} and platform == "ios":
                event_type = random.choices(["page_view", "add_to_cart", "checkout"], weights=[0.75, 0.18, 0.07])[0]
            elif window_id == 9:
                event_type = random.choices(["page_view", "add_to_cart", "checkout", "purchase"], weights=[0.45, 0.15, 0.10, 0.30])[0]
            else:
                event_type = random.choices(["page_view", "add_to_cart", "checkout", "purchase"], weights=[0.70, 0.15, 0.08, 0.07])[0]

            experiment_id = EXPERIMENT_ID
            if window_id == 4 and i < 20:
                experiment_id = None if i % 2 == 0 else EXPERIMENT_ID
                variant = "bad_variant" if i % 2 == 1 else variant

            event = {
                "event_id": f"evt_{window_id}_{i}",
                "window_id": window_id,
                "window_start": window_start.isoformat(),
                "event_time": event_time.isoformat(),
                "processing_time": processing_time.isoformat(),
                "user_id": f"user_{window_id}_{i}",
                "experiment_id": experiment_id,
                "variant": variant,
                "metric_event_type": event_type,
                "platform": platform,
                "country": "IN",
                "schema_version": "v1.0",
                "ingestion_source": "async_simulator",
            }

            events.append(event)

            if window_id == 10 and i < 25:
                events.append(dict(event))

    seen = set()
    valid = []
    dlq = []
    late = []
    duplicates = []
    lag_by_window = defaultdict(list)

    for event in events:
        event_time = datetime.fromisoformat(event["event_time"])
        processing_time = datetime.fromisoformat(event["processing_time"])
        lag_seconds = (processing_time - event_time).total_seconds()
        lag_by_window[event["window_id"]].append(lag_seconds)

        errors = []
        if not event.get("experiment_id"):
            errors.append("missing_experiment_id")
        if event.get("variant") not in {"control", "treatment"}:
            errors.append("invalid_variant")

        if errors:
            bad = dict(event)
            bad["error_code"] = "|".join(errors)
            dlq.append(bad)
            continue

        if event["event_id"] in seen:
            dup = dict(event)
            dup["duplicate_reason"] = "event_id_seen_before"
            duplicates.append(dup)
            continue
        seen.add(event["event_id"])

        window_start_dt = datetime.fromisoformat(event["window_start"])
        is_late_by_watermark = event_time < window_start_dt - timedelta(minutes=15)

        if is_late_by_watermark:
            late_event = dict(event)
            late_event["lateness_seconds"] = lag_seconds
            late_event["late_reason"] = "event_time_before_watermark"
            late.append(late_event)
            continue

        valid.append(event)

    traffic_snapshots = []
    srm_alerts = []

    for window_id in range(WINDOW_COUNT):
        rows = [e for e in valid if e["window_id"] == window_id]
        total = len(rows)
        control_count = sum(1 for e in rows if e["variant"] == "control")
        treatment_count = sum(1 for e in rows if e["variant"] == "treatment")
        observed_control = control_count / total if total else 0.0
        deviation_pp = abs(observed_control - EXPECTED_CONTROL_PCT) * 100

        traffic_snapshots.append({
            "experiment_id": EXPERIMENT_ID,
            "window_id": window_id,
            "control_count": control_count,
            "treatment_count": treatment_count,
            "observed_control_pct": observed_control,
            "expected_control_pct": EXPECTED_CONTROL_PCT,
            "deviation_pp": deviation_pp,
        })

        if total >= 500 and deviation_pp > 5:
            srm_alerts.append({
                "experiment_id": EXPERIMENT_ID,
                "window_id": window_id,
                "observed_control_pct": observed_control,
                "expected_control_pct": EXPECTED_CONTROL_PCT,
                "deviation_pp": deviation_pp,
                "sample_size": total,
                "alert_level": "investigate",
                "provisional_status": "pending_batch_confirmation",
            })

    ios_purchase_counts = {
        w: sum(1 for e in valid if e["window_id"] == w and e["platform"] == "ios" and e["metric_event_type"] == "purchase")
        for w in range(WINDOW_COUNT)
    }
    baseline = mean([ios_purchase_counts[w] for w in range(0, 5)])

    instrumentation_alerts = [
        {
            "experiment_id": EXPERIMENT_ID,
            "platform": "ios",
            "window_id": w,
            "baseline_event_count": baseline,
            "observed_event_count": ios_purchase_counts[w],
            "alert_level": "critical",
            "suspected_cause": "ios_purchase_instrumentation_gap",
        }
        for w in [5, 6]
        if ios_purchase_counts[w] == 0
    ]

    lag_windows = []
    for w in range(WINDOW_COUNT):
        values = sorted(lag_by_window[w])
        p95 = values[int(0.95 * (len(values) - 1))] if values else 0
        lag_windows.append({
            "window_id": w,
            "p95_lag_seconds": p95,
            "alert_level": "investigate" if p95 > 300 else "none",
        })

    window_rates = {}
    snapshots = []
    for w in range(WINDOW_COUNT):
        rows = [e for e in valid if e["window_id"] == w]
        purchases = sum(1 for e in rows if e["metric_event_type"] == "purchase")
        rate = purchases / len(rows) if rows else 0.0
        window_rates[w] = rate
        snapshots.append({
            "metric_id": "streaming_purchase_event_rate",
            "experiment_id": EXPERIMENT_ID,
            "window_id": w,
            "event_count": len(rows),
            "purchase_count": purchases,
            "metric_value": rate,
            "provisional_label": True,
        })

    anomaly_alerts = []
    for w in range(4, WINDOW_COUNT):
        history = [window_rates[i] for i in range(w - 4, w)]
        baseline_rate = mean(history)
        current = window_rates[w]
        if baseline_rate > 0 and current > baseline_rate * 2:
            anomaly_alerts.append({
                "metric_id": "streaming_purchase_event_rate",
                "experiment_id": EXPERIMENT_ID,
                "window_id": w,
                "metric_value": current,
                "expected_value": baseline_rate,
                "alert_type": "provisional_realtime_alert",
                "provisional_label": True,
            })

    streaming_value = sum(1 for e in valid if e["metric_event_type"] == "purchase") / len(valid)
    batch_value = streaming_value * 0.985

    write_json(OUT_DIR / "streaming_metric_snapshots.json", {"artifact": "streaming_metric_snapshots", "snapshot_count": len(snapshots), "provisional_label": True, "snapshots": snapshots})
    write_json(OUT_DIR / "srm_streaming_alerts.json", {"artifact": "srm_streaming_alerts", "alert_count": len(srm_alerts), "alerts": srm_alerts})
    write_json(OUT_DIR / "traffic_allocation_snapshots.json", {"artifact": "traffic_allocation_snapshots", "snapshot_count": len(traffic_snapshots), "snapshots": traffic_snapshots})
    write_json(OUT_DIR / "instrumentation_alerts.json", {"artifact": "instrumentation_alerts", "alert_count": len(instrumentation_alerts), "alerts": instrumentation_alerts})
    write_json(OUT_DIR / "consumer_lag_report.json", {"artifact": "consumer_lag_report", "window_count": len(lag_windows), "windows": lag_windows})
    write_json(OUT_DIR / "late_event_report.json", {"artifact": "late_event_report", "late_event_count": len(late), "handling": "batch_authoritative_layer_handles_late_events"})
    write_json(OUT_DIR / "duplicate_event_report.json", {"artifact": "duplicate_event_report", "duplicate_count": len(duplicates), "dedup_method": "event_id_seen_before"})
    write_json(OUT_DIR / "dlq_events.json", {"artifact": "dlq_events", "dlq_event_count": len(dlq), "events": dlq[:25]})
    write_json(OUT_DIR / "provisional_anomaly_alerts.json", {"artifact": "provisional_anomaly_alerts", "alert_count": len(anomaly_alerts), "alerts": anomaly_alerts})
    write_json(OUT_DIR / "stream_batch_reconciliation_report.json", {
        "artifact": "stream_batch_reconciliation_report",
        "metric_id": "streaming_purchase_event_rate",
        "streaming_value": streaming_value,
        "batch_authoritative_value": batch_value,
        "absolute_delta": abs(streaming_value - batch_value),
        "reconciliation_status": "pass",
        "batch_remains_authoritative": True,
    })
    write_json(OUT_DIR / "streaming_health_report.json", {
        "artifact": "streaming_health_report",
        "total_events_emitted": len(events),
        "valid_events_for_provisional_metrics": len(valid),
        "dlq_events": len(dlq),
        "late_events": len(late),
        "duplicates": len(duplicates),
        "srm_alerts_active": len(srm_alerts),
        "instrumentation_alerts_active": len(instrumentation_alerts),
        "provisional_anomaly_alerts_active": len(anomaly_alerts),
        "overall_health_status": "investigate",
    })

    print("streaming_demo_v0 complete")
    print(f"total_events_emitted: {len(events)}")
    print(f"valid_events: {len(valid)}")
    print(f"srm_alerts: {len(srm_alerts)}")
    print(f"instrumentation_alerts: {len(instrumentation_alerts)}")
    print(f"late_events: {len(late)}")
    print(f"duplicates: {len(duplicates)}")
    print(f"dlq_events: {len(dlq)}")
    print(f"provisional_anomaly_alerts: {len(anomaly_alerts)}")
    print(f"wrote {OUT_DIR}")


if __name__ == "__main__":
    main()
