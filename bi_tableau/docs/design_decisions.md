# MetaSignal BI Layer — Design Decisions

Documents every significant design choice in the dashboard architecture,
data model, and visual design. Each decision includes the alternative considered
and the reason it was rejected.

---

## D1 — Why Five Tabs, Not One

**Decision:** Five separate dashboard tabs (Executive Overview, Experiment Readout,
Guardrail Monitoring, Metric Quality, Segment Deep Dive) rather than a single
consolidated dashboard.

**Alternative considered:** A single scrollable dashboard with all KPIs visible at once.

**Reason rejected:** Different audiences consume different tabs. An engineering VP
needs the Executive Overview — total experiments, ship rate, SRM failures — without
wading through segment breakdowns. A DS reviewing a specific experiment needs the
full Readout tab. A platform engineer debugging a guardrail regression needs the
Guardrail tab in isolation. A single dashboard forces every viewer through every
piece of information regardless of relevance. Five tabs with a consistent navigation
header serve the actual audience structure of an experimentation program.

---

## D2 — Why Experiment_Health_Score Rather Than a Simple Status Flag

**Decision:** A continuous 0–100 health score per experiment, not just PASS/WARN/FAIL.

**Alternative considered:** Display only the overall_status field (PASS/WARN/FAIL).

**Reason rejected:** WARN is too broad. An experiment with one low-severity peeking
warning and an experiment with SRM + peeking + underpowering both produce overall_status = WARN,
but they are categorically different. The health score creates a continuous severity
ordering within WARN that enables the DS to triage which experiments need attention
first. Score 0 = invalid (SRM), score < 60 = multiple serious issues, score > 80 = clean.

---

## D3 — Why `delta_pct_badness` Instead of Raw `delta_pct` for Guardrail Color Scale

**Decision:** A derived field that reorients delta so positive always means worse,
regardless of whether the metric is lower_is_better or higher_is_better.

**Alternative considered:** Separate color scales per guardrail direction.

**Reason rejected:** The dashboard displays four guardrail metrics simultaneously:
p99_latency_ms (lower is better), error_rate_pct (lower is better),
revenue_per_user (higher is better), session_duration_s (higher is better).
A positive delta in p99_latency_ms (latency increased) is bad.
A positive delta in revenue_per_user (revenue increased) is good.
Using raw delta with a single color scale would encode "positive = good" everywhere,
which is incorrect for lower-is-better metrics. `delta_pct_badness` normalises this
so a single diverging color scale (green = good, red = bad) works across all four metrics.

---

## D4 — Why SRM-Failed Experiments Are Excluded From Segment Analysis

**Decision:** Segment rows are not generated for SRM-failed experiments.

**Alternative considered:** Include segment rows but label them "unreliable."

**Reason rejected:** Segment analysis on an SRM-failed experiment is meaningless —
if the overall assignment was biased, the segment-level assignments are also biased.
Displaying segment data with a warning label creates the risk that a viewer selects
only the segments they find favourable and ignores the SRM failure. Excluding the
rows entirely removes the temptation and makes the exclusion unambiguous.

---

## D5 — Why FAIL Is Reserved for SRM Only (in experiment_checks.csv)

**Decision:** Only `srm_check` and `peeking_risk` (when HIGH) produce FAIL-level
check status. All other checks produce at most WARN.

**Alternative considered:** Also FAIL for critical guardrail violations.

**Reason rejected:** Guardrail violations are contextually interpretable. A 3% p99
latency increase might be acceptable for a 5% conversion lift — that's a business
decision, not a statistical impossibility. SRM makes all other checks untrustworthy
in a structural sense — there's no business context that makes SRM acceptable because
the groups aren't comparable at all. FAIL should be reserved for conditions with
no legitimate explanation, not for conditions that require a judgment call.

---

## D6 — Why the SQL Layer Exists Between CSV and Tableau

**Decision:** Five SQL files define the analytical logic between raw CSVs and dashboard views.

**Alternative considered:** Apply all logic directly as Tableau calculated fields.

**Reason rejected:** Tableau calculated fields are not versionable, not testable, not
readable outside Tableau Desktop, and not reviewable in a PR. SQL is versionable,
readable in any text editor, and reviewable by anyone with SQL literacy. The SQL layer
documents exactly what each metric means and how it's computed — which is the function
of a data contract, not a UI detail. When the metric definition changes, the change
happens in a SQL file that goes through code review, not in a hidden Tableau calculated
field that requires the workbook to inspect.

In practice for this portfolio setup, Tableau connects directly to the CSVs
and the SQL files serve as analytical documentation and the specification
for any future database implementation.

---

## D7 — Why Synthetic Data With Injected Noise Rather Than Clean Round Numbers

**Decision:** All 25 experiments have realistic variance, non-round numbers,
edge cases (two SRM failures, 11 guardrail warnings, 10 shipped, 10 held/in-review).

**Alternative considered:** Clean synthetic data where all experiments PASS and
all metrics are round numbers.

**Reason rejected:** Clean data doesn't tell a story. A dashboard where everything
is green teaches the viewer nothing about what the dashboard is for. The data was
deliberately designed to include: 2 SRM failures (invalidated, rejected), experiments
with peeking risk, experiments that are statistically significant but not practically
significant, guardrail violations across different metrics and teams, heterogeneous
segment effects. A viewer using this dashboard can see a realistic experimentation
program health picture — some things working, some things flagged, clear actions
for each state.

---

## D8 — Why Practical Significance Threshold Is 1% Relative Lift

**Decision:** The practical significance threshold is set at 1% relative lift (configurable).

**Alternative considered:** 2% threshold (more conservative) or 0.5% threshold (less conservative).

**Reason rejected:** 1% relative lift is a commonly used minimum detectable effect in
consumer product experimentation at typical traffic volumes. It's large enough that
it excludes statistical noise while small enough that it catches meaningful but modest
improvements. The threshold is configurable per experiment — 1% is the default,
not a universal rule.

---

*MetaSignal BI Layer — Design Decisions v1.0*
