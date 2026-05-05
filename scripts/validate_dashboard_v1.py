import json
from pathlib import Path

checks = []

def add(name, passed, observed):
    checks.append({"name": name, "passed": bool(passed), "observed": observed})

docs_index = Path("docs/index.html")
local_index = Path("outputs/dashboard/index.html")
manifest_path = Path("outputs/dashboard/dashboard_manifest.json")

add("docs_index_exists", docs_index.exists(), str(docs_index))
add("local_index_exists", local_index.exists(), str(local_index))
add("manifest_exists", manifest_path.exists(), str(manifest_path))

html = docs_index.read_text(encoding="utf-8") if docs_index.exists() else ""
for phrase in [
    "MetaSignal Evidence Dashboard",
    "CUPED + Guardrails",
    "Streaming Provisional",
    "Batch Authoritative",
    "System Flow",
    "Evidence Summary",
    "Claim Boundary",
    "Run Locally",
]:
    add(f"html_contains_{phrase.replace(' ', '_')}", phrase in html, phrase)

manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
artifact_total = manifest.get("artifact_inventory_total", 0)
add("artifact_inventory_total_positive", artifact_total > 0, artifact_total)
add("manifest_status_pass", manifest.get("status") == "pass", manifest.get("status"))

status = "pass" if all(c["passed"] for c in checks) else "fail"
payload = {
    "artifact": "metasignal_dashboard_validation_v1",
    "status": status,
    "check_count": len(checks),
    "passed_count": sum(c["passed"] for c in checks),
    "checks": checks,
    "evidence_statement": "Validates MetaSignal static evidence dashboard and GitHub Pages entrypoint."
}

out = Path("outputs/validation/dashboard_validation_v1.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

print("metasignal_dashboard_validation_v1 complete")
print(f"status: {status}")
print(f"passed_count: {payload['passed_count']}/{payload['check_count']}")
print(f"wrote {out}")

if status != "pass":
    raise SystemExit(1)
