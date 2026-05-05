from __future__ import annotations

from fastapi.testclient import TestClient

from src.metasignal.api.app import app


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

    print("api_smoke_test_v0 complete")
    for r in results:
        print(f"{r['status_code']} | {r['endpoint']}")

    print(f"passed_count: {passed_count}")
    print(f"endpoint_count: {len(results)}")

    if passed_count != len(results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
