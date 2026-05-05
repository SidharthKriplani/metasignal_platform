from __future__ import annotations

import json
from pathlib import Path


JSON_OUT = Path("outputs/reports/metasignal_streaming_extension_summary.json")
MD_OUT = Path("docs/METASIGNAL_STREAMING_EXTENSION.md")


CAPABILITIES = [
    ["SRM early warning", "outputs/streaming/srm_streaming_alerts.json", "Detect split issues early, but batch confirms validity."],
    ["Traffic allocation drift", "outputs/streaming/traffic_allocation_snapshots.json", "Track rolling control/treatment allocation drift."],
    ["Instrumentation gap detection", "outputs/streaming/instrumentation_alerts.json", "Detect platform-specific event drops before daily batch readout."],
    ["Consumer lag monitoring", "outputs/streaming/consumer_lag_report.json", "Surface processing delay and prevent false realtime confidence."],
    ["Late event handling", "outputs/streaming/late_event_report.json", "Count late arrivals while preserving batch authority."],
    ["Duplicate detection", "outputs/streaming/duplicate_event_report.json", "Detect duplicate event IDs before provisional metric use."],
    ["DLQ quarantine", "outputs/streaming/dlq_events.json", "Quarantine malformed events instead of silently including them."],
    ["Provisional anomaly detection", "outputs/streaming/provisional_anomaly_alerts.json", "Realtime anomaly alerts trigger investigation only."],
    ["Stream-batch reconciliation", "outputs/streaming/stream_batch_reconciliation_report.json", "Streaming gives speed, batch gives authority, reconciliation gives trust."],
]


def main() -> None:
    payload = {
        "artifact": "metasignal_streaming_extension_summary",
        "positioning": "A provisional streaming early-warning layer on top of the batch-authoritative MetaSignal core.",
        "hard_rule": "Streaming alerts may trigger investigation or pause-for-review, but never final experiment decisions.",
        "capability_count": len(CAPABILITIES),
        "capabilities": [
            {"capability": c, "artifact": a, "principle": p}
            for c, a, p in CAPABILITIES
        ],
    }

    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    MD_OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# MetaSignal Streaming Extension",
        "",
        "## Positioning",
        payload["positioning"],
        "",
        "## Hard Rule",
        payload["hard_rule"],
        "",
        "## Capabilities",
        "",
    ]

    for cap, artifact, principle in CAPABILITIES:
        lines.extend([
            f"### {cap}",
            f"- Artifact: `{artifact}`",
            f"- Principle: {principle}",
            "",
        ])

    MD_OUT.write_text("\n".join(lines), encoding="utf-8")

    print("streaming_extension_summary_v0 complete")
    print(f"capability_count: {len(CAPABILITIES)}")
    print(f"wrote {JSON_OUT}")
    print(f"wrote {MD_OUT}")


if __name__ == "__main__":
    main()
