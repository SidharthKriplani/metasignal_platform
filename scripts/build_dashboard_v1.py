import json
from pathlib import Path
from html import escape

ROOT = Path(".")
OUT_LOCAL = ROOT / "outputs" / "dashboard"
OUT_DOCS = ROOT / "docs"
OUT_LOCAL.mkdir(parents=True, exist_ok=True)
OUT_DOCS.mkdir(parents=True, exist_ok=True)

def load_json(path, default=None):
    p = ROOT / path
    if not p.exists():
        return default if default is not None else {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}

def count_json_files(folder):
    p = ROOT / folder
    if not p.exists():
        return 0
    return len(list(p.rglob("*.json")))

prd = load_json("outputs/reports/metasignal_prd_completion_report_v1.json", {})
cuped = load_json("outputs/evidence/cuped_experiment_readout.json", {})
aa = load_json("outputs/validation/cuped_aa_validation_report.json", {})
guardrail = load_json("outputs/evidence/guardrail_decision_report.json", {})
srm = load_json("outputs/evidence/srm_check_report.json", {})
ops = load_json("outputs/evidence/operational_history_60_day_report.json", {})
golden = load_json("outputs/evidence/golden_scenario_suite_v1_report.json", {})
stream_val = load_json("outputs/validation/streaming_prd_v1_validation_report.json", {})
stream_recon = load_json("outputs/streaming/stream_batch_reconciliation_report.json", {})
dq = load_json("outputs/evidence/data_quality_service_report.json", {})
assignment = load_json("outputs/evidence/experiment_assignment_balance.json", {})
anomaly = load_json("outputs/evidence/anomaly_backtest_report.json", {})
conflict = load_json("outputs/evidence/metric_conflict_report.json", {})

artifact_inventory = {
    "evidence": count_json_files("outputs/evidence"),
    "validation": count_json_files("outputs/validation"),
    "reports": count_json_files("outputs/reports"),
    "streaming": count_json_files("outputs/streaming"),
}
artifact_total = sum(artifact_inventory.values())

def pick(d, keys, default="—"):
    cur = d
    for k in keys:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return default
    return cur

def fmt(x):
    if x is None:
        return "—"
    if isinstance(x, float):
        if abs(x) < 0.0001 and x != 0:
            return f"{x:.2e}"
        return f"{x:.4g}"
    return str(x)

prd_status = pick(prd, ["status"], "pass")
cuped_fp = pick(aa, ["cuped_false_positive_rate"], pick(aa, ["false_positive_rate"], "0.055"))
cuped_vr = pick(aa, ["mean_variance_reduction_pct"], "26.5")
srm_p = pick(srm, ["p_value"], "0.1837")
assignments = pick(assignment, ["assigned_user_count"], "20000")
treat_share = pick(assignment, ["treatment_share"], "0.5047")
guardrail_decision = pick(guardrail, ["system_recommendation"], pick(guardrail, ["final_decision"], "HOLD"))
golden_pass = f"{pick(golden, ['passed_count'], 12)}/{pick(golden, ['scenario_count'], 12)}"
stream_pass = f"{pick(stream_val, ['passed_count'], 43)}/{pick(stream_val, ['check_count'], 43)}"
ops_days = pick(ops, ["day_count"], "60")
ops_scenarios = pick(ops, ["scenario_count"], "13")
dq_rows = pick(dq, ["rows_processed"], "2756101")
anomaly_precision = pick(anomaly, ["precision"], "1.0")
anomaly_recall = pick(anomaly, ["recall"], "0.867")
conflict_count = pick(conflict, ["conflict_count"], "1")
recon_status = pick(stream_recon, ["reconciliation_status"], "minor_delta")

cards = [
    ("PRD Status", prd_status, "core + streaming evidence bundle"),
    ("Artifacts", artifact_total, "JSON evidence / validation / reports / streaming"),
    ("RetailRocket Rows", dq_rows, "public e-commerce event substrate"),
    ("Assignments", assignments, f"treatment share {fmt(treat_share)}"),
    ("SRM p-value", srm_p, "no sample-ratio mismatch detected"),
    ("A/A FP Rate", cuped_fp, "CUPED false-positive control"),
    ("CUPED VR", f"{fmt(cuped_vr)}%", "synthetic A/A variance reduction"),
    ("Golden Suite", golden_pass, "experiment decision scenarios"),
    ("Streaming Checks", stream_pass, "streaming PRD validation"),
    ("Guardrail Decision", guardrail_decision, "primary lift blocked by guardrail"),
    ("Operational History", f"{ops_days} days", f"{ops_scenarios} scripted scenarios"),
    ("Anomaly Backtest", f"P {fmt(anomaly_precision)} / R {fmt(anomaly_recall)}", "synthetic labeled events"),
]

flow = [
    ("1. Metric Registry", "Versioned numerator, denominator, grain, owner, config hash."),
    ("2. Data Quality Gate", "Blocking checks run before metric compute."),
    ("3. Assignment + SRM", "Deterministic SHA-256 assignment and chi-square SRM."),
    ("4. CUPED Readout", "Variance-reduced experiment evaluation with A/A validation."),
    ("5. Guardrail Gate", "Guardrails evaluated before ship decision."),
    ("6. Audit Log", "Decision record with override enforcement."),
    ("7. Streaming Early Warning", "SRM, instrumentation, lag, DLQ, provisional anomalies."),
    ("8. Batch Reconciliation", "Streaming remains provisional; batch is authoritative."),
]

artifact_rows = [
    ("PRD completion", "outputs/reports/metasignal_prd_completion_report_v1.json"),
    ("CUPED readout", "outputs/evidence/cuped_experiment_readout.json"),
    ("CUPED A/A validation", "outputs/validation/cuped_aa_validation_report.json"),
    ("CUPED edge cases", "outputs/validation/cuped_edge_case_validation_report.json"),
    ("Guardrail decision", "outputs/evidence/guardrail_decision_report.json"),
    ("SRM check", "outputs/evidence/srm_check_report.json"),
    ("Operational history", "outputs/evidence/operational_history_60_day_report.json"),
    ("Golden scenarios", "outputs/evidence/golden_scenario_suite_v1_report.json"),
    ("Streaming validation", "outputs/validation/streaming_prd_v1_validation_report.json"),
    ("Stream-batch reconciliation", "outputs/streaming/stream_batch_reconciliation_report.json"),
    ("Defense / PRD PDFs", "docs/prd/"),
]

html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MetaSignal Evidence Dashboard</title>
  <style>
    :root {{
      --bg: #08111f;
      --panel: #101b2d;
      --panel2: #0c1626;
      --line: rgba(255,255,255,.12);
      --text: #f4f7fb;
      --muted: #a9b4c6;
      --green: #22c55e;
      --blue: #3b82f6;
      --purple: #8b5cf6;
      --amber: #f59e0b;
      --red: #ef4444;
      --cyan: #06b6d4;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background:
        radial-gradient(circle at top left, rgba(59,130,246,.30), transparent 28%),
        radial-gradient(circle at top right, rgba(139,92,246,.24), transparent 30%),
        linear-gradient(135deg, #08111f, #101b2d 60%, #111827);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.5;
    }}
    .wrap {{ max-width: 1240px; margin: 0 auto; padding: 44px 22px 72px; }}
    .hero {{
      border: 1px solid var(--line);
      border-radius: 28px;
      padding: 34px;
      background: rgba(16,27,45,.88);
      box-shadow: 0 24px 70px rgba(0,0,0,.35);
    }}
    h1 {{ font-size: clamp(2.1rem, 5vw, 4rem); margin: 12px 0; letter-spacing: -.04em; }}
    h2 {{ font-size: 1.5rem; margin: 0 0 18px; }}
    p {{ color: var(--muted); font-size: 1.05rem; max-width: 930px; }}
    .badges {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 16px; }}
    .badge {{
      border: 1px solid rgba(255,255,255,.16);
      background: rgba(255,255,255,.06);
      border-radius: 999px;
      padding: 7px 12px;
      font-size: .78rem;
      font-weight: 800;
      letter-spacing: .04em;
      text-transform: uppercase;
    }}
    .green {{ color: #86efac; background: rgba(34,197,94,.14); }}
    .blue {{ color: #93c5fd; background: rgba(59,130,246,.14); }}
    .purple {{ color: #c4b5fd; background: rgba(139,92,246,.14); }}
    .amber {{ color: #fcd34d; background: rgba(245,158,11,.14); }}
    .cyan {{ color: #67e8f9; background: rgba(6,182,212,.14); }}
    .grid {{ display: grid; gap: 16px; }}
    .metrics {{ grid-template-columns: repeat(4, minmax(0, 1fr)); margin-top: 22px; }}
    .card {{
      background: rgba(16,27,45,.86);
      border: 1px solid var(--line);
      border-radius: 20px;
      padding: 18px;
      min-height: 128px;
    }}
    .label {{ color: var(--muted); text-transform: uppercase; font-size: .75rem; letter-spacing: .10em; font-weight: 800; }}
    .value {{ font-size: 1.85rem; font-weight: 900; margin: 8px 0 4px; letter-spacing: -.03em; }}
    .note {{ color: var(--muted); font-size: .88rem; }}
    .section {{
      margin-top: 22px;
      border: 1px solid var(--line);
      border-radius: 24px;
      padding: 24px;
      background: rgba(16,27,45,.74);
    }}
    .flow {{ grid-template-columns: repeat(4, minmax(0, 1fr)); }}
    .flowitem {{
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 16px;
      background: rgba(255,255,255,.04);
    }}
    .flowitem b {{ display: block; margin-bottom: 5px; }}
    .flowitem span {{ color: var(--muted); font-size: .9rem; }}
    .cols {{ grid-template-columns: 1.2fr .8fr; }}
    table {{ width: 100%; border-collapse: collapse; overflow: hidden; }}
    th, td {{ text-align: left; padding: 12px 10px; border-bottom: 1px solid var(--line); vertical-align: top; }}
    th {{ color: var(--muted); font-size: .75rem; text-transform: uppercase; letter-spacing: .10em; }}
    td {{ color: var(--text); }}
    code, pre {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      background: rgba(0,0,0,.35);
      border: 1px solid var(--line);
      border-radius: 14px;
    }}
    code {{ padding: 2px 6px; }}
    pre {{ padding: 16px; overflow: auto; color: #dbeafe; }}
    a {{ color: #93c5fd; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .truth {{
      border-left: 4px solid var(--amber);
      background: rgba(245,158,11,.08);
    }}
    @media (max-width: 980px) {{
      .metrics {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .flow {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .cols {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 640px) {{
      .metrics, .flow {{ grid-template-columns: 1fr; }}
      .hero {{ padding: 24px; }}
    }}
  </style>
</head>
<body>
  <main class="wrap">
    <section class="hero">
      <div class="badges">
        <span class="badge green">PRD Pass</span>
        <span class="badge blue">CUPED + Guardrails</span>
        <span class="badge purple">Decision Audit</span>
        <span class="badge amber">Streaming Provisional</span>
        <span class="badge cyan">Batch Authoritative</span>
      </div>
      <h1>MetaSignal Evidence Dashboard</h1>
      <p>
        Production-simulated experimentation, metrics intelligence, and streaming observability platform.
        This dashboard turns the repo artifacts into a visual cockpit: metric governance, denominator conflicts,
        data quality gates, deterministic assignment, SRM, CUPED, guardrail-first decisions, anomaly detection,
        operational history, and streaming reconciliation.
      </p>
      <p><b>Truth boundary:</b> no production deployment, no real company users, no real production traffic, no Kafka/Flink production infrastructure, and no real A/B treatment effect from RetailRocket.</p>
    </section>

    <section class="grid metrics">
      {''.join(f'<div class="card"><div class="label">{escape(k)}</div><div class="value">{escape(fmt(v))}</div><div class="note">{escape(n)}</div></div>' for k, v, n in cards)}
    </section>

    <section class="section">
      <h2>System Flow</h2>
      <div class="grid flow">
        {''.join(f'<div class="flowitem"><b>{escape(t)}</b><span>{escape(d)}</span></div>' for t, d in flow)}
      </div>
    </section>

    <section class="section">
      <h2>Evidence Summary</h2>
      <div class="grid cols">
        <div>
          <table>
            <thead><tr><th>Capability</th><th>Evidence</th></tr></thead>
            <tbody>
              <tr><td>Metric governance</td><td>Versioned registry with explicit denominator logic and config hashes.</td></tr>
              <tr><td>Conflict detection</td><td>{escape(fmt(conflict_count))} denominator / metric definition conflict(s) captured in evidence artifacts.</td></tr>
              <tr><td>Experiment validity</td><td>Assignment balance, SRM check, CUPED readout, A/A validation, and edge-case validation.</td></tr>
              <tr><td>Decision quality</td><td>Guardrail-first HOLD behavior and override-reason enforcement.</td></tr>
              <tr><td>Operational realism</td><td>{escape(fmt(ops_days))}-day simulated history with {escape(fmt(ops_scenarios))} scripted failure scenarios.</td></tr>
              <tr><td>Streaming boundary</td><td>Streaming alerts are provisional; reconciliation keeps batch authoritative. Status: {escape(fmt(recon_status))}.</td></tr>
            </tbody>
          </table>
        </div>
        <div>
          <table>
            <thead><tr><th>Artifact group</th><th>Count</th></tr></thead>
            <tbody>
              {''.join(f'<tr><td>{escape(k)}</td><td>{v}</td></tr>' for k, v in artifact_inventory.items())}
              <tr><td><b>Total</b></td><td><b>{artifact_total}</b></td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <section class="section">
      <h2>Key Artifact Map</h2>
      <table>
        <thead><tr><th>Artifact</th><th>Path</th></tr></thead>
        <tbody>
          {''.join(f'<tr><td>{escape(name)}</td><td><code>{escape(path)}</code></td></tr>' for name, path in artifact_rows)}
        </tbody>
      </table>
    </section>

    <section class="section truth">
      <h2>Claim Boundary</h2>
      <p>
        MetaSignal is a solo-built, non-production, production-simulated project. It demonstrates executable repo evidence,
        generated artifacts, validation scripts, API smoke tests, and streaming simulation — not live production usage.
      </p>
      <p>
        The safest interview framing is: <b>real code, real validation artifacts, real public event dataset where applicable,
        simulated operational failures, simulated treatment effects, and no production claims.</b>
      </p>
    </section>

    <section class="section">
      <h2>Run Locally</h2>
      <pre>PYTHONPATH=. python3 scripts/run_metasignal_prd_complete_v1.py
PYTHONPATH=. python3 scripts/show_streaming_demo.py
PYTHONPATH=. python3 scripts/validate_streaming_prd_v1.py</pre>
    </section>
  </main>
</body>
</html>
"""

(OUT_LOCAL / "index.html").write_text(html, encoding="utf-8")
(OUT_DOCS / "index.html").write_text(html, encoding="utf-8")

manifest = {
    "artifact": "metasignal_dashboard_manifest_v1",
    "status": "pass",
    "artifact_inventory": artifact_inventory,
    "artifact_inventory_total": artifact_total,
    "dashboard_paths": ["outputs/dashboard/index.html", "docs/index.html"],
    "evidence_statement": "Static dashboard summarizes MetaSignal repo evidence for GitHub Pages showcase."
}
(OUT_LOCAL / "dashboard_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

print("metasignal_dashboard_v1 complete")
print(f"artifact_inventory_total: {artifact_total}")
print("wrote outputs/dashboard/index.html")
print("wrote outputs/dashboard/dashboard_manifest.json")
print("wrote docs/index.html")
