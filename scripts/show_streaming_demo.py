from __future__ import annotations

from src.metasignal.streaming.streaming_prd_v1 import run_sync


def main() -> None:
    result = run_sync()

    print("=== MetaSignal Streaming Extension PRD v1 Demo ===")
    print(f"raw_events: {result['raw_events']}")
    print(f"valid_events: {result['valid_events']}")
    print(f"dlq_count: {result['dlq_count']}")
    print(f"duplicate_count: {result['duplicate_count']}")
    print(f"late_count: {result['late_count']}")
    print(f"srm_alerts: {result['srm_alerts']}")
    print(f"instrumentation_alerts: {result['instrumentation_alerts']}")
    print(f"anomaly_alerts: {result['anomaly_alerts']}")
    print(f"stream_quality_checks: {result['stream_quality_checks']}")
    print(f"dlq_parquet_written: {result['dlq_parquet_written']}")
    print(f"scenario_status: {result['scenario_status']}")
    print("Streaming gives speed. Batch gives authority. Reconciliation gives trust.")


if __name__ == "__main__":
    main()
