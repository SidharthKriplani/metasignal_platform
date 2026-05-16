-- ============================================================
-- 05_kpi_summary.sql
-- MetaSignal BI Layer — Executive KPI Summary View
--
-- Purpose: Aggregates experiment program health into executive
--          KPIs used on the Executive Overview tab.
--          One-row-per-team + one program-level totals row.
--
-- Source tables: experiments, guardrails, experiment_checks, metric_quality
-- Output:        kpi_summary_vw
-- ============================================================

WITH experiment_counts AS (
    SELECT
        team,
        COUNT(*)                                                    AS total_experiments,
        SUM(CASE WHEN overall_status = 'PASS'      THEN 1 ELSE 0 END) AS pass_count,
        SUM(CASE WHEN overall_status = 'WARN'      THEN 1 ELSE 0 END) AS warn_count,
        SUM(CASE WHEN overall_status = 'FAIL'      THEN 1 ELSE 0 END) AS fail_count,
        SUM(CASE WHEN srm_status = 'FAIL'          THEN 1 ELSE 0 END) AS srm_fail_count,
        SUM(CASE WHEN ship_decision = 'SHIPPED'    THEN 1 ELSE 0 END) AS shipped_count,
        SUM(CASE WHEN ship_decision = 'REJECTED'   THEN 1 ELSE 0 END) AS rejected_count,
        SUM(CASE WHEN ship_decision = 'HELD'       THEN 1 ELSE 0 END) AS held_count,
        SUM(CASE WHEN peeking_risk IN ('LOW','HIGH') THEN 1 ELSE 0 END) AS peeking_flagged,
        ROUND(AVG(CASE WHEN is_significant = 1 AND srm_status = 'PASS'
                       THEN lift_pct END), 2)                      AS avg_lift_pct_significant,
        ROUND(AVG(duration_ratio), 3)                              AS avg_duration_ratio,
        ROUND(
            100.0 * SUM(CASE WHEN ship_decision = 'SHIPPED' THEN 1 ELSE 0 END)
            / NULLIF(COUNT(*), 0), 1
        )                                                           AS ship_rate_pct,
        ROUND(
            100.0 * SUM(CASE WHEN is_significant = 1 AND srm_status = 'PASS' THEN 1 ELSE 0 END)
            / NULLIF(SUM(CASE WHEN srm_status = 'PASS' THEN 1 ELSE 0 END), 0), 1
        )                                                           AS significance_rate_pct
    FROM experiments
    GROUP BY team
),

guardrail_counts AS (
    SELECT
        team,
        COUNT(*)                                                    AS total_guardrail_checks,
        SUM(CASE WHEN status = 'WARN' THEN 1 ELSE 0 END)           AS guardrail_warn_count,
        ROUND(
            100.0 * SUM(CASE WHEN status = 'WARN' THEN 1 ELSE 0 END)
            / NULLIF(COUNT(*), 0), 1
        )                                                           AS guardrail_warn_rate_pct,
        ROUND(AVG(ABS(delta_pct)), 3)                              AS avg_guardrail_delta_pct
    FROM guardrails
    GROUP BY team
),

quality_counts AS (
    SELECT
        e.team,
        ROUND(AVG(mq.power_at_observed_effect), 3)                 AS avg_power,
        SUM(mq.novelty_effect_detected)                            AS novelty_count,
        ROUND(AVG(mq.data_lag_hours), 1)                           AS avg_data_lag_hours,
        SUM(CASE WHEN mq.min_sample_met = 0 THEN 1 ELSE 0 END)    AS underpowered_count
    FROM metric_quality mq
    JOIN experiments e ON mq.experiment_id = e.experiment_id
    GROUP BY e.team
),

team_summary AS (
    SELECT
        ec.team,
        ec.total_experiments,
        ec.pass_count,
        ec.warn_count,
        ec.fail_count,
        ec.srm_fail_count,
        ec.shipped_count,
        ec.rejected_count,
        ec.held_count,
        ec.peeking_flagged,
        ec.avg_lift_pct_significant,
        ec.avg_duration_ratio,
        ec.ship_rate_pct,
        ec.significance_rate_pct,
        gc.total_guardrail_checks,
        gc.guardrail_warn_count,
        gc.guardrail_warn_rate_pct,
        gc.avg_guardrail_delta_pct,
        qc.avg_power,
        qc.novelty_count,
        qc.avg_data_lag_hours,
        qc.underpowered_count,

        -- Program health score per team (0–100)
        GREATEST(0,
            100
            - ROUND(10.0 * ec.srm_fail_count / NULLIF(ec.total_experiments, 0), 1) * 4
            - ROUND(10.0 * ec.peeking_flagged / NULLIF(ec.total_experiments, 0), 1) * 2
            - ROUND(gc.guardrail_warn_rate_pct * 0.3, 1)
            - CASE WHEN qc.avg_power < 0.70 THEN 10 ELSE 0 END
        )                                                           AS team_health_score

    FROM experiment_counts ec
    LEFT JOIN guardrail_counts gc ON ec.team = gc.team
    LEFT JOIN quality_counts qc   ON ec.team = qc.team
)

-- Team-level rows
SELECT 'team' AS row_type, * FROM team_summary

UNION ALL

-- Program totals row
SELECT
    'program_total'             AS row_type,
    'ALL TEAMS'                 AS team,
    SUM(total_experiments),
    SUM(pass_count),
    SUM(warn_count),
    SUM(fail_count),
    SUM(srm_fail_count),
    SUM(shipped_count),
    SUM(rejected_count),
    SUM(held_count),
    SUM(peeking_flagged),
    ROUND(AVG(avg_lift_pct_significant), 2),
    ROUND(AVG(avg_duration_ratio), 3),
    ROUND(100.0 * SUM(shipped_count) / NULLIF(SUM(total_experiments), 0), 1),
    ROUND(AVG(significance_rate_pct), 1),
    SUM(total_guardrail_checks),
    SUM(guardrail_warn_count),
    ROUND(100.0 * SUM(guardrail_warn_count) / NULLIF(SUM(total_guardrail_checks), 0), 1),
    ROUND(AVG(avg_guardrail_delta_pct), 3),
    ROUND(AVG(avg_power), 3),
    SUM(novelty_count),
    ROUND(AVG(avg_data_lag_hours), 1),
    SUM(underpowered_count),
    ROUND(AVG(team_health_score), 1)
FROM team_summary

ORDER BY row_type DESC, total_experiments DESC;
