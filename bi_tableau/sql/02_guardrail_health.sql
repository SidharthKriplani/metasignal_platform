-- ============================================================
-- 02_guardrail_health.sql
-- MetaSignal BI Layer — Guardrail Health View
--
-- Purpose: Produces one row per experiment × guardrail with
--          delta, breach classification, and severity band.
--          Drives the Guardrail Monitoring dashboard tab.
--
-- Source tables: guardrails, experiments
-- Output:        guardrail_health_vw
-- ============================================================

WITH guardrail_enriched AS (
    SELECT
        g.experiment_id,
        g.experiment_name,
        g.team,
        g.guardrail_name,
        g.direction,
        g.tolerance_pct,
        g.control_val,
        g.treatment_val,
        g.delta_pct,
        g.bad_direction,
        g.exceeded_tolerance,
        g.status,

        -- Severity band: how far past tolerance is the breach?
        CASE
            WHEN g.status = 'PASS'                             THEN 'Healthy'
            WHEN g.bad_direction = 1
             AND ABS(g.delta_pct) <= g.tolerance_pct           THEN 'Marginal'
            WHEN g.bad_direction = 1
             AND ABS(g.delta_pct) <= g.tolerance_pct * 2.0     THEN 'Warning'
            WHEN g.bad_direction = 1
             AND ABS(g.delta_pct) > g.tolerance_pct * 2.0      THEN 'Critical'
            ELSE                                                     'Healthy'
        END AS severity_band,

        -- How many tolerance widths past the threshold?
        CASE
            WHEN g.tolerance_pct = 0 THEN NULL
            ELSE ROUND(ABS(g.delta_pct) / g.tolerance_pct, 2)
        END AS tolerance_multiples,

        -- Directional delta: positive always = "worse" direction for display
        CASE
            WHEN g.direction = 'lower_is_better' THEN g.delta_pct
            ELSE -g.delta_pct
        END AS delta_pct_badness,

        e.overall_status     AS experiment_overall_status,
        e.ship_decision,
        e.start_date,
        e.end_date

    FROM guardrails g
    LEFT JOIN experiments e ON g.experiment_id = e.experiment_id
),

-- Rollup: guardrail health by team
team_guardrail_summary AS (
    SELECT
        team,
        guardrail_name,
        COUNT(*)                                   AS total_checks,
        SUM(CASE WHEN status = 'WARN' THEN 1 ELSE 0 END) AS warn_count,
        ROUND(
            100.0 * SUM(CASE WHEN status = 'WARN' THEN 1 ELSE 0 END) / COUNT(*),
            1
        )                                          AS warn_rate_pct,
        ROUND(AVG(ABS(delta_pct)), 3)              AS avg_abs_delta_pct,
        ROUND(MAX(ABS(delta_pct)), 3)              AS max_abs_delta_pct
    FROM guardrails
    GROUP BY team, guardrail_name
)

SELECT
    ge.*,
    ts.total_checks           AS team_guardrail_total,
    ts.warn_count             AS team_guardrail_warns,
    ts.warn_rate_pct          AS team_guardrail_warn_rate_pct,
    ts.avg_abs_delta_pct      AS team_avg_abs_delta_pct
FROM guardrail_enriched ge
LEFT JOIN team_guardrail_summary ts
       ON ge.team = ts.team
      AND ge.guardrail_name = ts.guardrail_name
ORDER BY
    CASE ge.severity_band
        WHEN 'Critical' THEN 1
        WHEN 'Warning'  THEN 2
        WHEN 'Marginal' THEN 3
        ELSE 4
    END,
    ABS(ge.delta_pct) DESC;
