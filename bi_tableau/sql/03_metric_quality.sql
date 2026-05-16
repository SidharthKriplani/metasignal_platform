-- ============================================================
-- 03_metric_quality.sql
-- MetaSignal BI Layer — Metric Quality Panel View
--
-- Purpose: Surfaces data quality signals per experiment:
--          pre-period balance, sample adequacy, novelty effect,
--          peeking risk, and power at observed effect.
--          Drives the Metric Quality Panel dashboard tab.
--
-- Source tables: metric_quality, experiments, experiment_checks
-- Output:        metric_quality_vw
-- ============================================================

WITH check_status_pivot AS (
    -- Pivot check results to one row per experiment
    SELECT
        experiment_id,
        MAX(CASE WHEN check_name = 'srm_check'
            THEN status END)                         AS srm_check_status,
        MAX(CASE WHEN check_name = 'pre_period_balance'
            THEN status END)                         AS pre_period_balance_status,
        MAX(CASE WHEN check_name = 'peeking_risk'
            THEN status END)                         AS peeking_check_status,
        MAX(CASE WHEN check_name = 'practical_significance'
            THEN status END)                         AS practical_sig_status,
        MAX(CASE WHEN check_name = 'guardrail_movement'
            THEN status END)                         AS guardrail_check_status,

        -- Count of WARN/FAIL checks per experiment
        SUM(CASE WHEN status IN ('WARN', 'FAIL') THEN 1 ELSE 0 END)
                                                     AS total_issue_count,
        SUM(CASE WHEN status = 'FAIL' THEN 1 ELSE 0 END)
                                                     AS fail_count
    FROM experiment_checks
    GROUP BY experiment_id
),

quality_enriched AS (
    SELECT
        mq.experiment_id,
        mq.experiment_name,
        mq.team,
        mq.max_smd_covariate,
        mq.pre_period_balance_status,
        mq.min_sample_size_required,
        mq.actual_sample_size,
        mq.sample_adequacy_pct,
        mq.min_sample_met,
        mq.novelty_effect_detected,
        mq.power_at_observed_effect,
        mq.data_lag_hours,
        mq.srm_status,
        mq.overall_status,

        e.peeking_risk,
        e.interim_looks,
        e.duration_ratio,
        e.lift_pct,
        e.p_value,
        e.ship_decision,
        e.start_date,
        e.end_date,

        cp.total_issue_count,
        cp.fail_count,
        cp.peeking_check_status,
        cp.practical_sig_status,
        cp.guardrail_check_status,

        -- Quality tier: composite signal
        CASE
            WHEN mq.srm_status = 'FAIL'                     THEN 'Invalidated'
            WHEN cp.fail_count > 0                          THEN 'Critical Issues'
            WHEN cp.total_issue_count >= 3                  THEN 'Multiple Warnings'
            WHEN cp.total_issue_count IN (1, 2)             THEN 'Minor Issues'
            ELSE                                                 'Clean'
        END AS quality_tier,

        -- Power band for visualisation
        CASE
            WHEN mq.power_at_observed_effect >= 0.80        THEN 'Adequately Powered'
            WHEN mq.power_at_observed_effect >= 0.60        THEN 'Marginally Powered'
            ELSE                                                 'Underpowered'
        END AS power_band,

        -- SMD severity
        CASE
            WHEN mq.max_smd_covariate < 0.05               THEN 'Balanced'
            WHEN mq.max_smd_covariate < 0.10               THEN 'Minor Imbalance'
            ELSE                                                 'Significant Imbalance'
        END AS balance_band

    FROM metric_quality mq
    LEFT JOIN experiments e   ON mq.experiment_id = e.experiment_id
    LEFT JOIN check_status_pivot cp ON mq.experiment_id = cp.experiment_id
)

SELECT * FROM quality_enriched
ORDER BY
    CASE quality_tier
        WHEN 'Invalidated'       THEN 1
        WHEN 'Critical Issues'   THEN 2
        WHEN 'Multiple Warnings' THEN 3
        WHEN 'Minor Issues'      THEN 4
        ELSE 5
    END,
    total_issue_count DESC;
