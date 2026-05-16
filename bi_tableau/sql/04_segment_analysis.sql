-- ============================================================
-- 04_segment_analysis.sql
-- MetaSignal BI Layer — Segment Deep Dive View
--
-- Purpose: Surfaces heterogeneous treatment effects across
--          device, region, cohort, and plan segments.
--          Identifies which segments drive lift and which lag.
--          Drives the Segment Deep Dive dashboard tab.
--
-- Source tables: segments, experiments
-- Output:        segment_analysis_vw
-- ============================================================

WITH segment_enriched AS (
    SELECT
        s.experiment_id,
        s.experiment_name,
        s.team,
        s.segment_col,
        s.segment_value,
        s.n_control,
        s.n_treatment,
        s.control_rate,
        s.treatment_rate,
        s.lift_pct,
        s.p_value,
        s.is_significant,

        e.overall_status     AS experiment_overall_status,
        e.lift_pct           AS experiment_lift_pct,
        e.is_significant     AS experiment_is_significant,
        e.ship_decision,
        e.start_date,

        -- Relative performance vs experiment-level lift
        ROUND(s.lift_pct - e.lift_pct, 3)          AS lift_vs_experiment_avg,

        -- Segment direction classification
        CASE
            WHEN s.lift_pct >  e.lift_pct + 2.0    THEN 'Outperformer'
            WHEN s.lift_pct >= e.lift_pct - 2.0    THEN 'Inline'
            WHEN s.lift_pct <  e.lift_pct - 2.0
             AND s.lift_pct >= 0                   THEN 'Underperformer'
            ELSE                                        'Negative Responder'
        END AS segment_performance_band,

        -- Statistical confidence at segment level
        CASE
            WHEN s.p_value < 0.01  THEN 'High Confidence'
            WHEN s.p_value < 0.05  THEN 'Significant'
            WHEN s.p_value < 0.10  THEN 'Marginal'
            ELSE                        'Not Significant'
        END AS segment_confidence_band,

        -- Sample size adequacy per segment
        CASE
            WHEN (s.n_control + s.n_treatment) >= 1000 THEN 'Adequate'
            WHEN (s.n_control + s.n_treatment) >= 300  THEN 'Marginal'
            ELSE                                            'Insufficient'
        END AS segment_sample_band

    FROM segments s
    LEFT JOIN experiments e ON s.experiment_id = e.experiment_id
),

-- Within each experiment × segment_col: rank segments by lift
ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY experiment_id, segment_col
            ORDER BY lift_pct DESC
        ) AS lift_rank_within_segment_col
    FROM segment_enriched
),

-- Experiment-level segment summary: heterogeneity flag
het_summary AS (
    SELECT
        experiment_id,
        segment_col,
        MAX(lift_pct) - MIN(lift_pct)   AS lift_range_pct,
        STDDEV(lift_pct)                AS lift_stddev,
        COUNT(DISTINCT segment_value)   AS segment_count,
        SUM(is_significant)             AS significant_segments
    FROM segments
    GROUP BY experiment_id, segment_col
)

SELECT
    r.*,
    h.lift_range_pct,
    h.lift_stddev,
    h.segment_count,
    h.significant_segments,

    -- Heterogeneity flag: is segment effect meaningfully different across groups?
    CASE
        WHEN h.lift_range_pct >= 10.0   THEN 'High Heterogeneity'
        WHEN h.lift_range_pct >= 4.0    THEN 'Moderate Heterogeneity'
        ELSE                                 'Homogeneous'
    END AS heterogeneity_band

FROM ranked r
LEFT JOIN het_summary h
       ON r.experiment_id = h.experiment_id
      AND r.segment_col   = h.segment_col
ORDER BY
    r.experiment_id,
    r.segment_col,
    r.lift_pct DESC;
