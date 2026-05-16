# MetaSignal BI Layer — Tableau Build Specification

Step-by-step instructions for building the MetaSignal Executive Dashboard in Tableau Desktop.
Follow these exactly. Do not make design decisions — every choice is specified here.
After completing each tab, take a screenshot and save it to `tableau/screenshots/`.

---

## SETUP — Connect Data Sources

### Step 1: Open Tableau Desktop → New Workbook

### Step 2: Connect to Text File (CSV) — repeat for all 5 files

For each file: **Data → New Data Source → Text File** → navigate to `bi_tableau/data/`

Connect all five:
- `experiments.csv`
- `guardrails.csv`
- `experiment_checks.csv`
- `segments.csv`
- `metric_quality.csv`

### Step 3: Set Data Types

In the `experiments.csv` data source:
- `start_date`, `end_date` → Date (not String). Right-click column header → Change Data Type → Date
- `is_significant`, `is_practically_significant`, `min_sample_met` → Number (whole). Right-click → Change Data Type → Number (Whole)
- All rate fields (`control_rate`, `treatment_rate`, etc.) → Number (decimal)

Repeat for other CSVs where date/boolean columns appear.

### Step 4: Create Relationships (if using Tableau's logical layer)

If Tableau asks to create relationships between data sources when you start building:
- Primary: `experiments.csv`
- Link `guardrails.csv` → `experiments.csv` on `experiment_id`
- Link `experiment_checks.csv` → `experiments.csv` on `experiment_id`
- Link `segments.csv` → `experiments.csv` on `experiment_id`
- Link `metric_quality.csv` → `experiments.csv` on `experiment_id`

---

## CALCULATED FIELDS

Create these before building any sheets. In Tableau: **Analysis → Create Calculated Field**

### From experiments data source:

**Lift % (Relative)**
```
[lift_pct]
```
Format as: Number → Custom → `+0.00"%";-0.00"%";0.00"%"`

**Confidence %**
```
ROUND((1 - [p_value]) * 100, 1)
```

**Significance Label**
```
IF [srm_status] = "FAIL" THEN "Invalid — SRM"
ELSEIF [is_significant] = 1 AND [is_practically_significant] = 1 THEN "Significant & Meaningful"
ELSEIF [is_significant] = 1 AND [is_practically_significant] = 0 THEN "Significant but Negligible"
ELSE "Not Significant"
END
```

**Recommended Action**
```
IF [srm_status] = "FAIL" THEN "Invalidate & Re-run"
ELSEIF [peeking_risk] = "HIGH" THEN "Review Peeking — Hold Decision"
ELSEIF [overall_status] = "FAIL" THEN "Block Ship"
ELSEIF [is_significant] = 1 AND [is_practically_significant] = 1 AND [overall_status] = "PASS" THEN "Ready to Ship"
ELSEIF [is_significant] = 1 AND [is_practically_significant] = 0 THEN "Ship Only If Strategic"
ELSEIF [overall_status] = "WARN" THEN "Needs Review"
ELSE "Insufficient Evidence"
END
```

**Experiment Health Score**
```
IF [srm_status] = "FAIL" THEN 0
ELSE MAX(0,
  100
  - IF [srm_status] = "FAIL" THEN 40 ELSE 0 END
  - IF [peeking_risk] = "HIGH" THEN 20 ELSE 0 END
  - IF [peeking_risk] = "LOW" THEN 10 ELSE 0 END
  - IF [overall_status] = "WARN" THEN 10 ELSE 0 END
)
END
```

**Status Color**  *(used for color encoding — returns integer for color mapping)*
```
IF [overall_status] = "PASS" THEN 1
ELSEIF [overall_status] = "WARN" THEN 2
ELSE 3
END
```

### From guardrails data source:

**Delta Badness %**
```
IF [direction] = "lower_is_better" THEN [delta_pct]
ELSE -[delta_pct]
END
```

**Severity Band**
```
IF [status] = "PASS" THEN "Healthy"
ELSEIF [bad_direction] = 1 AND ABS([delta_pct]) <= [tolerance_pct] THEN "Marginal"
ELSEIF [bad_direction] = 1 AND ABS([delta_pct]) <= [tolerance_pct] * 2 THEN "Warning"
ELSEIF [bad_direction] = 1 AND ABS([delta_pct]) > [tolerance_pct] * 2 THEN "Critical"
ELSE "Healthy"
END
```

**Severity Color**
```
IF [Severity Band] = "Critical" THEN 4
ELSEIF [Severity Band] = "Warning" THEN 3
ELSEIF [Severity Band] = "Marginal" THEN 2
ELSE 1
END
```

### From segments data source:

**Lift vs Experiment Avg**  *(requires blending with experiments — or pre-compute in Python)*
```
[lift_pct] - [experiment_lift_pct]
```
*(Note: `experiment_lift_pct` is already in segments.csv — use that column directly)*

**Segment Performance Band**
```
IF [lift_pct] > [experiment_lift_pct] + 2 THEN "Outperformer"
ELSEIF [lift_pct] >= [experiment_lift_pct] - 2 THEN "Inline"
ELSEIF [lift_pct] < [experiment_lift_pct] - 2 AND [lift_pct] >= 0 THEN "Underperformer"
ELSE "Negative Responder"
END
```

---

## TAB 1 — Executive Overview

**Sheet name:** `Exec_Overview`  
**Dashboard name:** `Executive Overview`

### KPI Tiles (use BANs — Big Ass Numbers)

Create 6 separate sheets, each showing one KPI as a text mark:

**Sheet: KPI_ShipRate**
- Mark type: Text
- Text: `COUNTD(IF [ship_decision] = "SHIPPED" THEN [experiment_id] END) / COUNTD([experiment_id]) * 100`
- Format: `0.0"%"`
- Label above: "Ship Rate"

**Sheet: KPI_SRMRate**
- Text: `COUNTD(IF [srm_status] = "FAIL" THEN [experiment_id] END) / COUNTD([experiment_id]) * 100`
- Format: `0.0"%"`
- Label: "SRM Failure Rate"
- Color: If > 10% → Red; else if > 5% → Amber; else Green (use calculated field)

**Sheet: KPI_PeekingRate**
- Text: `COUNTD(IF [peeking_risk] != "NONE" THEN [experiment_id] END) / COUNTD([experiment_id]) * 100`
- Label: "Peeking Flag Rate"

**Sheet: KPI_AvgLift**
- Text: `AVG(IF [is_significant] = 1 AND [srm_status] = "PASS" THEN [lift_pct] END)`
- Format: `+0.00"%";-0.00"%";0.00"%"`
- Label: "Avg Lift % (Significant Experiments)"

**Sheet: KPI_GuardrailWarn**
- Data source: guardrails.csv
- Text: `COUNTD(IF [status] = "WARN" THEN [experiment_id] + [guardrail_name] END) / COUNT([guardrail_name]) * 100`
- Format: `0.0"%"`
- Label: "Guardrail Warn Rate"

**Sheet: KPI_TotalExperiments**
- Text: `COUNTD([experiment_id])`
- Label: "Total Experiments"

### Ship Decision Bar Chart

**Sheet: ShipDecision_Bar**
- Rows: `COUNTD([experiment_id])`
- Columns: `[ship_decision]`
- Mark type: Bar
- Color: SHIPPED=green (#2ECC71), HELD=amber (#F39C12), REJECTED=red (#E74C3C), IN_REVIEW=grey (#95A5A6), SHIPPED_WITH_NOTE=light green
- Sort: Descending by count
- Label: Show count on bars

### Team Health Heatmap

**Sheet: TeamHealth_Heatmap**
- Rows: `[team]`
- Columns: `Measure Names` (Ship Rate, SRM Rate, Guardrail Rate)
- Mark type: Square
- Color: Use sequential green→red
- Text: Show value in each cell

### Dashboard Layout — Executive Overview

Place in this order, top to bottom:
1. Row 1: 6 KPI tiles in a horizontal strip (equal width)
2. Row 2: ShipDecision_Bar (left 60%) + TeamHealth_Heatmap (right 40%)
3. Add filter: Team (dropdown, allow All)
4. Add filter: Date range on start_date (slider)
5. Title: "MetaSignal — Experimentation Program Overview"

---

## TAB 2 — Experiment Readout

**Sheet name:** `Experiment_Readout`  
**Dashboard name:** `Experiment Readout`

### Main Table

**Sheet: Readout_Table**
- Mark type: Text (as a table/crosstab)
- Rows: `[experiment_name]`, sorted by `start_date` descending
- Columns (in order):
  - `[team]`
  - `[primary_metric]`
  - `[Lift % (Relative)]` — color encoded: positive=green, negative=red, 0=grey (diverging, center at 0)
  - `[p_value]` — color: < 0.05 = green, 0.05-0.10 = amber, > 0.10 = grey
  - `[Significance Label]`
  - `[srm_status]` — FAIL=red, PASS=green
  - `[peeking_risk]` — HIGH=red, LOW=amber, NONE=green
  - `[Recommended Action]`
  - `[Experiment Health Score]` — color: 80-100=green, 60-79=amber, <60=red
  - `[ship_decision]`

### Lift Distribution

**Sheet: Lift_Distribution**
- Mark type: Bar (histogram)
- Columns: `[lift_pct]` (create bins: width 2.0)
- Rows: `COUNT([experiment_id])`
- Color: Positive bins=green (#27AE60), negative bins=red (#E74C3C)
- Add reference line at 0 (solid black, label: "No Effect")
- Add reference line at 1.0 and -1.0 (dashed grey, label: "±1% Practical Threshold")

### p-value Distribution

**Sheet: PValue_Distribution**
- Mark type: Bar (histogram)
- Columns: `[p_value]` (bins: width 0.05)
- Rows: `COUNT([experiment_id])`
- Add reference line at 0.05 (red dashed, label: "α = 0.05")
- Color: Bars left of reference line = green, right = grey

### Dashboard Layout — Experiment Readout

1. Row 1: Readout_Table (full width — this is the primary view)
2. Row 2 (below fold): Lift_Distribution (left 50%) + PValue_Distribution (right 50%)
3. Filter: Team (dropdown)
4. Filter: overall_status (checkbox: PASS / WARN / FAIL)
5. Filter: ship_decision (checkbox)
6. Filter: Date range on start_date

---

## TAB 3 — Guardrail Monitoring

**Sheet name:** `Guardrail_Monitoring`  
**Dashboard name:** `Guardrail Monitoring`

### Guardrail Delta Heatmap

**Sheet: Guardrail_Heatmap**
- Rows: `[guardrail_name]`
- Columns: `[experiment_name]`
- Mark type: Square
- Color: `[Delta Badness %]` — diverging palette: green (negative, good) → white (0) → red (positive, bad)
- Size: Fixed (equal squares)
- Tooltip: experiment_name, guardrail_name, delta_pct, status, severity_band
- Sort columns: by experiment start_date ascending

### Severity Bar Chart

**Sheet: Severity_Bar**
- Rows: `COUNT([experiment_id] + [guardrail_name])`  *(one row per check)*
- Columns: `[Severity Band]`
- Mark type: Bar
- Color: Critical=red (#C0392B), Warning=orange (#E67E22), Marginal=amber (#F39C12), Healthy=green (#27AE60)
- Sort: Critical → Warning → Marginal → Healthy

### Guardrail WARN Table

**Sheet: Guardrail_WarnTable**
- Filter: `[status] = "WARN"` (fixed filter, not user-selectable)
- Rows: `[experiment_name]`
- Columns: `[guardrail_name]`, `[delta_pct]`, `[tolerance_pct]`, `[Severity Band]`, `[ship_decision]`
- Sort: by `[Delta Badness %]` descending (worst breaches first)

### Dashboard Layout — Guardrail Monitoring

1. Row 1: Guardrail_Heatmap (full width — this gives at-a-glance view)
2. Row 2: Severity_Bar (left 40%) + Guardrail_WarnTable (right 60%)
3. Filter: Team
4. Filter: guardrail_name (checkbox)
5. Filter: Severity Band (checkbox)

---

## TAB 4 — Metric Quality Panel

**Sheet name:** `Metric_Quality`  
**Dashboard name:** `Metric Quality Panel`

### Quality Tier Bar Chart

**Sheet: QualityTier_Bar**
- Rows: `COUNTD([experiment_id])`
- Columns: `[quality_tier]` (use metric_quality.csv field or create calculated field)
- Mark type: Bar
- Color: Clean=green, Minor Issues=amber, Multiple Warnings=orange, Critical Issues=red, Invalidated=dark red
- Order: Invalidated → Critical → Multiple → Minor → Clean (left to right)

**Note:** Create `Quality Tier` as a calculated field if not already in metric_quality.csv:
```
IF [srm_status] = "FAIL" THEN "Invalidated"
ELSEIF [overall_status] = "FAIL" THEN "Critical Issues"
ELSE "Minor Issues"
END
```
*(Simplify as needed — use overall_status and srm_status from metric_quality.csv)*

### Power vs Sample Size Scatter

**Sheet: Power_Scatter**
- Columns: `[actual_sample_size]`
- Rows: `[power_at_observed_effect]`
- Mark type: Circle
- Color: `[power_at_observed_effect]` — sequential: red (<0.6) → amber (0.6-0.8) → green (>0.8)
- Size: fixed medium
- Label: `[experiment_name]` (show on hover tooltip, not on mark)
- Add reference line at y=0.80 (dashed grey, label: "Minimum Power (0.80)")
- Add reference line at y=0.60 (dashed grey, label: "Marginal Power (0.60)")

### Issue Count per Team (stacked bar)

**Sheet: IssueCount_Team**
- Rows: `[team]`
- Columns: `SUM([total_issue_count])` (from metric_quality.csv)
- Mark type: Bar
- Color: encode by average issue count per experiment (sequential: green=0 → red=5+)

### Pre-Period Balance Table

**Sheet: Balance_Table**
- Filter: `[pre_period_balance_status] = "WARN"` (show only imbalanced experiments)
- Rows: `[experiment_name]`, `[team]`, `[max_smd_covariate]`, `[pre_period_balance_status]`
- Color: `[max_smd_covariate]` — white (0.0) → amber (0.10) → red (0.20+)

### Dashboard Layout — Metric Quality Panel

1. Row 1: QualityTier_Bar (left 40%) + Power_Scatter (right 60%)
2. Row 2: IssueCount_Team (left 40%) + Balance_Table (right 60%)
3. Filter: Team

---

## TAB 5 — Segment Deep Dive

**Sheet name:** `Segment_DeepDive`  
**Dashboard name:** `Segment Deep Dive`

### Segment Lift Bar Chart (main chart)

**Sheet: Segment_Lift_Bar**
- Rows: `[segment_value]`
- Columns: `[lift_pct]`
- Mark type: Bar
- Color: Positive=green (#27AE60), Negative=red (#E74C3C) — use conditional: `IF [lift_pct] >= 0 THEN 1 ELSE 0 END`
- Add reference line at 0 (solid black)
- Add reference line at `AVG([experiment_lift_pct])` per experiment (dashed blue, label: "Experiment Avg")
- Label: show `[lift_pct]` value on each bar
- Filter: `[experiment_name]` (user-selectable — this is the primary filter on this tab)
- Filter: `[segment_col]` (radio button: device_type / region / user_cohort / plan_type)

### Segment Confidence Table

**Sheet: Segment_Confidence_Table**
- Rows: `[segment_value]`, `[n_control]`, `[n_treatment]`, `[lift_pct]`, `[p_value]`, `[is_significant]`
- Color `[is_significant]` column: 1=green, 0=grey
- Sort: by `[lift_pct]` descending

### Heterogeneity Summary

**Sheet: Heterogeneity_Bar**
- Rows: `[experiment_name]`
- Columns: `[lift_range_pct]` (max−min lift across segments — compute as MAX(lift_pct)−MIN(lift_pct) using LOD)
  - LOD formula: `{FIXED [experiment_id], [segment_col] : MAX([lift_pct]) - MIN([lift_pct])}`
- Mark type: Bar
- Color: > 10pp = red (High Heterogeneity), 4-10pp = amber, < 4pp = green
- Filter: segment_col

### Dashboard Layout — Segment Deep Dive

1. Row 1: Segment_Lift_Bar (full width — primary chart)
2. Row 2: Segment_Confidence_Table (left 55%) + Heterogeneity_Bar (right 45%)
3. Primary filter: Experiment Name (dropdown — this drives the whole tab)
4. Secondary filter: Segment Dimension (radio: device_type / region / user_cohort / plan_type)
5. Note at bottom: "Segment p-values have higher variance than experiment-level. Treat with caution for n < 500."

---

## FORMATTING — Apply to All Tabs

### Colors (use these exact hex codes):
- PASS / positive / healthy: `#27AE60` (green)
- WARN / marginal: `#F39C12` (amber)
- FAIL / critical / negative: `#E74C3C` (red)
- Neutral / not significant: `#95A5A6` (grey)
- Reference lines: `#2C3E50` (dark grey, solid) or `#BDC3C7` (light grey, dashed)
- Background: White (`#FFFFFF`)
- Header background: `#2C3E50` (dark slate)
- Header text: `#FFFFFF`

### Typography:
- Dashboard title: Tableau Semibold, 18pt, `#2C3E50`
- Section labels: Tableau Medium, 11pt, `#2C3E50`
- KPI tiles: Tableau Bold, 36pt (number), 11pt (label)
- Table text: Tableau Regular, 9pt

### Tooltips — add to all marks:
- Always show: experiment_name, team, the primary metric on that chart
- Never show raw IDs (experiment_id) in tooltips

### Navigation header (optional, adds polish):
Create a horizontal strip at the top of each dashboard with tab names.
Use Text + Action (navigate to sheet) to create tab links.
Active tab: background `#2C3E50`, text white.
Inactive tabs: background `#ECF0F1`, text `#2C3E50`.

---

## EXPORT

1. Save workbook as: `bi_tableau/tableau/MetaSignal_BI_Dashboard.twbx`
2. Publish to Tableau Public: `File → Save to Tableau Public` (requires free account)
3. Copy the Tableau Public URL — add it to `bi_tableau/README.md`
4. Screenshots: After each tab is complete, take a full-screen screenshot (Cmd+Shift+4 → space → click window) and save to `bi_tableau/tableau/screenshots/tab1_exec_overview.png`, `tab2_experiment_readout.png`, etc.

---

*MetaSignal BI Layer — Tableau Build Specification v1.0*
*Follow exactly. Ask for clarification before deviating.*
