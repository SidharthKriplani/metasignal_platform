# MetaSignal BI Layer — KPI Dictionary

Every metric displayed on the MetaSignal Executive Dashboard is defined here:
its calculation, acceptable range, owner, and the action triggered when it falls outside range.
This dictionary is the authoritative reference for dashboard consumers and reviewers.

---

## TAB 1 — Executive Overview

| KPI | Definition | Calculation | Green | Amber | Red | Action on Red |
|-----|-----------|-------------|-------|-------|-----|---------------|
| **Ship Rate %** | % of completed experiments that shipped | `shipped / total_experiments × 100` | ≥ 30% | 15–30% | < 15% | Review experiment quality and decision bottlenecks |
| **SRM Failure Rate %** | % of experiments invalidated by Sample Ratio Mismatch | `srm_fails / total × 100` | < 5% | 5–10% | > 10% | Audit assignment pipeline; review randomisation infrastructure |
| **Peeking Flag Rate %** | % of experiments called before 80% planned duration | `peeking_flagged / total × 100` | < 10% | 10–20% | > 20% | Enforce minimum duration policy; disable real-time result feeds |
| **Avg Lift % (Significant)** | Mean lift across statistically significant experiments | `AVG(lift_pct) WHERE is_significant = 1` | > 3% | 1–3% | < 1% | Review experiment hypothesis quality and targeting |
| **Guardrail Warn Rate %** | % of guardrail checks that triggered WARN | `guardrail_warns / total_checks × 100` | < 10% | 10–20% | > 20% | Engineering review of guardrail definitions and tolerance bands |
| **Team Health Score** | Composite 0–100 score per team (see SQL 05) | Weighted deductions for SRM, peeking, guardrail, power | ≥ 80 | 60–79 | < 60 | Team-level review; identify systemic issues |

---

## TAB 2 — Experiment Readout

| KPI | Definition | Calculation | Notes |
|-----|-----------|-------------|-------|
| **Lift %** | Relative conversion lift: treatment vs control | `(treatment_rate − control_rate) / control_rate × 100` | Positive = treatment better; negative = regression |
| **p-value** | Probability of observing this lift under the null hypothesis | Two-proportion z-test | Threshold: α = 0.05. Values < 0.05 = significant |
| **Confidence %** | Complement of p-value displayed as confidence | `(1 − p_value) × 100` | Display metric only; not a formal confidence interval |
| **SRM Status** | Whether assignment ratio matches planned split | Chi-squared test on `n_control / n_treatment` vs `planned_split` | FAIL invalidates all other checks |
| **Practical Significance** | Whether lift exceeds the business-meaningful threshold | `|lift_pct| ≥ practical_threshold_pct (1%)` | Statistical significance ≠ practical significance |
| **Peeking Risk** | Whether experiment was called before planned duration | `duration_ratio < 0.80` OR `interim_looks ≥ 3` | HIGH/LOW/NONE |
| **Recommended Action** | Derived decision guidance (not a ship decision) | See SQL 01 CASE logic | Human decision required; this is guidance only |
| **Experiment Health Score** | 0–100 experiment-level validity score | Deductions for SRM, peeking, power, novelty | 0 = invalid; 100 = clean |
| **Significance Label** | Plain-English significance classification | See SQL 01 CASE logic | Four values: Invalid — SRM / Significant & Meaningful / Significant but Negligible / Not Significant |

---

## TAB 3 — Guardrail Monitoring

| KPI | Definition | Calculation | Notes |
|-----|-----------|-------------|-------|
| **Delta %** | Relative change in guardrail metric: treatment vs control | `(treatment_val − control_val) / control_val × 100` | Sign depends on direction (lower_is_better vs higher_is_better) |
| **Delta % (Badness)** | Delta reoriented so positive = worse for all metrics | See SQL 02 `delta_pct_badness` | Enables single colour scale across mixed-direction guardrails |
| **Severity Band** | Breach classification | Healthy / Marginal / Warning / Critical | Critical = breach > 2× tolerance width |
| **Tolerance Multiples** | How far past the tolerance threshold the breach is | `|delta_pct| / tolerance_pct` | 1.0 = exactly at threshold; 2.0 = twice past |
| **Guardrail Status** | PASS / WARN per check | `bad_direction = 1 AND exceeded_tolerance = 1` | WARN requires human sign-off before shipping |

### Guardrail Definitions

| Guardrail | Direction | Tolerance | Rationale |
|-----------|-----------|-----------|-----------|
| `p99_latency_ms` | Lower is better | 2.0% | p99 latency degradation affects top users disproportionately |
| `error_rate_pct` | Lower is better | 5.0% | Error rate increases signal infrastructure instability |
| `revenue_per_user` | Higher is better | 1.5% | Revenue regression in non-revenue experiments = unacceptable side effect |
| `session_duration_s` | Higher is better | 3.0% | Engagement drop = user experience regression |

---

## TAB 4 — Metric Quality Panel

| KPI | Definition | Calculation | Green | Amber | Red |
|-----|-----------|-------------|-------|-------|-----|
| **Power at Observed Effect** | Statistical power given observed effect size and n | Approximate power formula (see SQL 03) | ≥ 0.80 | 0.60–0.79 | < 0.60 |
| **Max SMD** | Standardised Mean Difference across covariates (pre-period) | `(mean_t − mean_c) / pooled_std` per covariate | < 0.05 | 0.05–0.10 | ≥ 0.10 |
| **Sample Adequacy %** | Actual sample as % of minimum required sample | `actual_n / required_n × 100` | ≥ 100% | 80–99% | < 80% |
| **Quality Tier** | Composite quality classification | See SQL 03 | Clean | Minor Issues | Critical Issues / Invalidated |
| **Data Lag (hrs)** | Hours between event and pipeline availability | `data_lag_hours` | < 2h | 2–6h | > 6h |
| **Total Issue Count** | WARN + FAIL checks across all 7 audit checks | `SUM(status IN ('WARN','FAIL'))` | 0 | 1–2 | ≥ 3 |

---

## TAB 5 — Segment Deep Dive

| KPI | Definition | Calculation | Notes |
|-----|-----------|-------------|-------|
| **Segment Lift %** | Lift within a specific segment value | `(seg_treatment_rate − seg_control_rate) / seg_control_rate × 100` | Compare to experiment-level lift for heterogeneity |
| **Lift vs Experiment Avg** | Segment lift relative to overall experiment lift | `seg_lift_pct − experiment_lift_pct` | Positive = segment outperforms; negative = underperforms |
| **Heterogeneity Band** | Degree of treatment effect variation across segments | `MAX(lift_pct) − MIN(lift_pct)` within segment_col | High ≥ 10pp; Moderate ≥ 4pp; Homogeneous < 4pp |
| **Segment Performance Band** | Classification relative to experiment average | Outperformer / Inline / Underperformer / Negative Responder | See SQL 04 thresholds |
| **Segment Confidence Band** | Statistical confidence level at segment | p < 0.01 / p < 0.05 / p < 0.10 / Not Significant | Segment p-values have higher variance than experiment-level |

---

*MetaSignal BI Layer — KPI Dictionary v1.0*
*Owner: Data Science / Experimentation Platform*
*Review cadence: Quarterly or after significant metric definition changes*
