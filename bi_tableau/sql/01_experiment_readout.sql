-- ============================================================
-- 01_experiment_readout.sql
-- MetaSignal BI Layer — Experiment Readout View
--
-- Purpose: Produces one row per experiment with all fields
--          needed for the Experiment Readout dashboard tab.
--          The central view that drives ship / no-ship decisions.
--
-- Source tables: experiments, metric_quality
-- Output:        experiment_readout_vw
-- ============================================================

WITH base AS (
    SELECT
        e.experiment_id,
        e.experiment_name,
        e.team,
        e.primary_metric,
        e.start_date,
        e.end_date,
        e.planned_duration_days,
        e.actual_duration_days,
        e.n_control,
        e.n_treatment,
        e.n_total,
        e.control_conversions,
        e.treatment_conversions,
        e.control_rate,
        e.treatment_rate,
        e.lift_pct,
        e.p_value,
        e.alpha,
        e.is_significant,
        e.srm_status,
        e.peeking_risk,
        e.interim_looks,
        e.duration_ratio,
        e.practical_threshold_pct,
        e.is_practically_significant,
        e.overall_status,
        e.ship_decision
    FROM experiments e
),

quality AS (
    SELECT
        experiment_id,
        power_at_observed_effect,
        min_sample_met,
        sample_adequacy_pct,
        novelty_effect_detected,
        data_lag_hours
    FROM metric_quality
),

enriched AS (
    SELECT
        b.*,
        q.power_at_observed_effect,
        q.min_sample_met,
        q.sample_adequacy_pct,
        q.novelty_effect_detected,
        q.data_lag_hours,

        -- Derived: absolute lift in percentage points
        ROUND((b.treatment_rate - b.control_rate) * 100, 4)
            AS lift_pp,

        -- Derived: confidence level (1 - p_value) as a display metric
        ROUND((1 - b.p_value) * 100, 1)
            AS confidence_pct,

        -- Derived: experiment health score (0–100)
        -- Penalise SRM (-40), peeking HIGH (-20), peeking LOW (-10),
        -- underpowered (-10), novelty effect (-5)
        CASE
            WHEN b.srm_status = 'FAIL' THEN 0
            ELSE GREATEST(0,
                100
                - CASE WHEN b.srm_status   = 'FAIL' THEN 40 ELSE 0 END
                - CASE WHEN b.peeking_risk = 'HIGH' THEN 20 ELSE 0 END
                - CASE WHEN b.peeking_risk = 'LOW'  THEN 10 ELSE 0 END
                - CASE WHEN q.min_sample_met = 0     THEN 10 ELSE 0 END
                - CASE WHEN q.novelty_effect_detected = 1 THEN 5 ELSE 0 END
                - CASE WHEN b.overall_status = 'WARN' THEN 10 ELSE 0 END
            )
        END AS experiment_health_score,

        -- Derived: readable significance label
        CASE
            WHEN b.srm_status = 'FAIL'       THEN 'Invalid — SRM'
            WHEN b.is_significant = 1
             AND b.is_practically_significant = 1 THEN 'Significant & Meaningful'
            WHEN b.is_significant = 1
             AND b.is_practically_significant = 0 THEN 'Significant but Negligible'
            WHEN b.is_significant = 0             THEN 'Not Significant'
        END AS significance_label,

        -- Derived: recommended action
        CASE
            WHEN b.srm_status   = 'FAIL'           THEN 'Invalidate & Re-run'
            WHEN b.peeking_risk = 'HIGH'            THEN 'Review Peeking — Hold Decision'
            WHEN b.overall_status = 'FAIL'          THEN 'Block Ship'
            WHEN b.is_significant = 1
             AND b.is_practically_significant = 1
             AND b.overall_status = 'PASS'          THEN 'Ready to Ship'
            WHEN b.is_significant = 1
             AND b.is_practically_significant = 0   THEN 'Ship Only If Strategic'
            WHEN b.overall_status = 'WARN'          THEN 'Needs Review'
            ELSE                                         'Insufficient Evidence'
        END AS recommended_action

    FROM base b
    LEFT JOIN quality q ON b.experiment_id = q.experiment_id
)

SELECT * FROM enriched
ORDER BY start_date DESC;
