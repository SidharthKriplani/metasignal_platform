# MetaSignal BI Layer — Dashboard QA Checklist

Run this checklist before publishing any dashboard update or after a data refresh.
Every item must pass before the dashboard goes live. Document the reviewer and date.

---

## Pre-Publish QA Checklist

**Reviewer:** _______________  
**Date:** _______________  
**Dashboard version:** _______________  
**Data extract date:** _______________

---

### Section 1 — Data Integrity

| # | Check | Method | Pass? | Notes |
|---|-------|--------|-------|-------|
| 1.1 | Row counts in Tableau match CSV row counts | Compare Tableau data source row count vs CSV `wc -l` | ☐ | |
| 1.2 | No null experiment_id values in any data source | Filter on null experiment_id; expect 0 rows | ☐ | |
| 1.3 | `experiments.csv` has exactly 25 rows | Check dimensions panel in Tableau | ☐ | |
| 1.4 | SRM failure count = 2 (EXP-1004, EXP-1017) | Filter `srm_status = FAIL`; count | ☐ | |
| 1.5 | Ship rate on Executive Overview matches `shipped / total` from experiments.csv | Manually compute from raw data | ☐ | |
| 1.6 | Guardrail delta signs are correct for direction | Spot-check `p99_latency_ms` — positive delta = latency increased = worse | ☐ | |
| 1.7 | Segment rows: no SRM-failed experiments appear (2 experiments excluded) | Filter segments by SRM-failed experiment IDs; expect 0 rows | ☐ | |
| 1.8 | Experiment Health Score = 0 for all FAIL experiments | Filter overall_status = FAIL; check health score column | ☐ | |

---

### Section 2 — Calculated Fields

| # | Check | Method | Pass? | Notes |
|---|-------|--------|-------|-------|
| 2.1 | `Lift % (Relative)` matches manual calculation for 3 spot-check experiments | Cross-reference with experiments.csv directly | ☐ | |
| 2.2 | `Confidence %` = `(1 − p_value) × 100` for 3 experiments | Manual spot-check | ☐ | |
| 2.3 | `Significance Label` matches expected values: exactly 4 distinct values | Check values in Tableau dimension | ☐ | |
| 2.4 | `Severity Band` in guardrails tab: only values Healthy/Marginal/Warning/Critical | Check distinct values; no nulls | ☐ | |
| 2.5 | `Lift vs Experiment Avg` in segments: positive for outperformers | Spot-check 3 rows manually | ☐ | |
| 2.6 | `Team Health Score` is between 0 and 100 for all teams | Check min/max of calculated field | ☐ | |

---

### Section 3 — Filters and Interactivity

| # | Check | Method | Pass? | Notes |
|---|-------|--------|-------|-------|
| 3.1 | Team filter on Executive Overview updates all KPI tiles correctly | Select single team; verify all numbers change | ☐ | |
| 3.2 | Date range filter on Experiment Readout tab works | Set date range to Nov 2025 only; verify row count decreases | ☐ | |
| 3.3 | Clicking a bar on Experiment Readout filters Guardrail tab (if cross-filter enabled) | Test with one experiment | ☐ | |
| 3.4 | Segment dimension selector (device_type / region / cohort / plan_type) updates correctly | Toggle between dimensions; verify segment values update | ☐ | |
| 3.5 | Reset filters button clears all active filters | Click reset; verify all data returns | ☐ | |
| 3.6 | Null / edge case: what shows when only SRM-failed experiments are in view | Filter to srm_status = FAIL; check all tabs for errors | ☐ | |

---

### Section 4 — Visual and Layout

| # | Check | Method | Pass? | Notes |
|---|-------|--------|-------|-------|
| 4.1 | Color scale is consistent: PASS = green, WARN = amber, FAIL = red across all tabs | Visual check on all five tabs | ☐ | |
| 4.2 | No overlapping text or truncated labels on any tab at 1920×1080 | Full-screen preview | ☐ | |
| 4.3 | KPI tiles on Executive Overview are readable without zoom | 100% zoom visual check | ☐ | |
| 4.4 | Tooltips are enabled on all charts and show meaningful fields | Hover over at least 3 marks per tab | ☐ | |
| 4.5 | No default Tableau blue used for status-encoded colors (must use green/amber/red) | Visual scan | ☐ | |
| 4.6 | Axis labels include units (%, ms, hrs) where applicable | Spot-check p99_latency_ms axis | ☐ | |
| 4.7 | Reference lines (e.g., α = 0.05 line on p-value chart) are visible and labeled | Check Experiment Readout tab | ☐ | |
| 4.8 | Dashboard title matches tab name on all 5 tabs | Visual check | ☐ | |

---

### Section 5 — Executive Readout Tab Specific

| # | Check | Method | Pass? | Notes |
|---|-------|--------|-------|-------|
| 5.1 | Recommended Action field is never null | Filter on null recommended_action; expect 0 | ☐ | |
| 5.2 | Ship decision distribution sums to 25 experiments | Check bar total | ☐ | |
| 5.3 | The "Invalid — SRM" experiments are visually distinct (red row / icon) | Visual check | ☐ | |
| 5.4 | Lift % axis is centered at 0 with diverging color scale | Negative lifts should be red-toned | ☐ | |

---

### Sign-off

All items above must be checked before publishing.  
If any item fails, document the failure in the Notes column and create a fix ticket before publishing.

**Signed off by:** _______________  
**Date:** _______________

---

*MetaSignal BI Layer — Dashboard QA Checklist v1.0*
