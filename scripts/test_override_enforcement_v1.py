from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from src.metasignal.api.app import app


OUT_PATH = Path("outputs/validation/override_reason_enforcement_report.json")


def main() -> None:
    client = TestClient(app)

    invalid = client.post(
        "/decisions/validate-override",
        json={
            "system_recommendation": "hold",
            "human_decision": "override_ship",
            "override_reason": None,
        },
    )

    valid = client.post(
        "/decisions/validate-override",
        json={
            "system_recommendation": "hold",
            "human_decision": "override_ship",
            "override_reason": "PM accepted risk after leadership review.",
        },
    )

    checks = [
        {
            "check": "invalid_override_without_reason_returns_422",
            "passed": invalid.status_code == 422,
            "status_code": invalid.status_code,
        },
        {
            "check": "valid_override_with_reason_returns_200",
            "passed": valid.status_code == 200,
            "status_code": valid.status_code,
        },
    ]

    payload = {
        "artifact": "override_reason_enforcement_report",
        "status": "pass" if all(c["passed"] for c in checks) else "review",
        "checks": checks,
        "evidence_statement": "MetaSignal API enforces override_reason when a human decision overrides the system recommendation.",
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("override_enforcement_v1 complete")
    print(f"status: {payload['status']}")
    print(f"invalid_status_code: {invalid.status_code}")
    print(f"valid_status_code: {valid.status_code}")
    print(f"wrote {OUT_PATH}")

    if payload["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
