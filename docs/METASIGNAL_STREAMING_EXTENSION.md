# MetaSignal Streaming Extension

## Positioning
A provisional streaming early-warning layer on top of the batch-authoritative MetaSignal core.

## Hard Rule
Streaming alerts may trigger investigation or pause-for-review, but never final experiment decisions.

## Capabilities

### SRM early warning
- Artifact: `outputs/streaming/srm_streaming_alerts.json`
- Principle: Detect split issues early, but batch confirms validity.

### Traffic allocation drift
- Artifact: `outputs/streaming/traffic_allocation_snapshots.json`
- Principle: Track rolling control/treatment allocation drift.

### Instrumentation gap detection
- Artifact: `outputs/streaming/instrumentation_alerts.json`
- Principle: Detect platform-specific event drops before daily batch readout.

### Consumer lag monitoring
- Artifact: `outputs/streaming/consumer_lag_report.json`
- Principle: Surface processing delay and prevent false realtime confidence.

### Late event handling
- Artifact: `outputs/streaming/late_event_report.json`
- Principle: Count late arrivals while preserving batch authority.

### Duplicate detection
- Artifact: `outputs/streaming/duplicate_event_report.json`
- Principle: Detect duplicate event IDs before provisional metric use.

### DLQ quarantine
- Artifact: `outputs/streaming/dlq_events.json`
- Principle: Quarantine malformed events instead of silently including them.

### Provisional anomaly detection
- Artifact: `outputs/streaming/provisional_anomaly_alerts.json`
- Principle: Realtime anomaly alerts trigger investigation only.

### Stream-batch reconciliation
- Artifact: `outputs/streaming/stream_batch_reconciliation_report.json`
- Principle: Streaming gives speed, batch gives authority, reconciliation gives trust.
