from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from src.metasignal.api.app import app


OUT_PATH = Path("outputs/validation/api_smoke_test_report.json")

client = TestClient(app)

ENDPOINTS = [
    "/health",
    "/metrics",
    "/experiments",
    "/experiments/EXP-CHECKOUT-FRICTION-001/readout",
    "/data-quality/latest",
    "/evidence/guardrail_decision_report",
    "/validation/cuped_aa_validation_report",
    "/resume-signal",
]


def main() -> None:
    results = []

    for endpoint in ENDPOINTS:
        response = client.get(endpoint)
        results.append(
            {
                "endpoint": endpoint,
                "status_code": response.status_code,
                "passed": response.status_code == 200,
            }
        )

    passed_count = sum(r["passed"] for r in results)
    status = "pass" if passed_count == len(results) else "review"

    payload = {
        "artifact": "api_smoke_test_report",
        "endpoint_count": len(results),
        "passed_count": passed_count,
        "failed_count": len(results) - passed_count,
        "status": status,
        "endpoints": results,
        "evidence_statement": "MetaSignal exposes core metrics, experiment readout, data quality, evidence artifacts, validation artifacts, and resume-signal summary through a FastAPI layer.",
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("api_smoke_test_v0 complete")
    for r in results:
        print(f"{r['status_code']} | {r['endpoint']}")

    print(f"passed_count: {passed_count}")
    print(f"endpoint_count: {len(results)}")
    print(f"status: {status}")
    print(f"wrote {OUT_PATH}")

    if status != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
