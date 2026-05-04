from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone

from sqlalchemy import delete, select, func

from src.metasignal.db.session import SessionLocal
from src.metasignal.db.models import (
    DataQualityCheck,
    DecisionLog,
    Experiment,
    ExperimentEvaluation,
    MetricDefinition,
    MetricResult,
    PipelineRunLog,
    SimulationEvent,
)


def hash_config(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def main() -> None:
    with SessionLocal() as session:
        # reset v0 seed data safely
        for model in [
            DecisionLog,
            ExperimentEvaluation,
            Experiment,
            MetricResult,
            DataQualityCheck,
            PipelineRunLog,
            SimulationEvent,
            MetricDefinition,
        ]:
            session.execute(delete(model))

        metric_cvr_user = MetricDefinition(
            name="purchase_conversion_rate_user",
            display_name="Purchase Conversion Rate - User Denominator",
            description="Share of active users who completed at least one purchase.",
            numerator_sql="COUNT(DISTINCT user_id) FILTER (WHERE event_type = 'transaction')",
            denominator_sql="COUNT(DISTINCT user_id)",
            denominator_type="distinct_users",
            filter_sql="event_type IN ('view', 'addtocart', 'transaction')",
            grain="daily",
            entity_type="user",
            direction="increase_good",
            is_guardrail=False,
            owner="growth_analytics",
            version=1,
            config_hash=hash_config("purchase_conversion_rate_user_v1"),
            change_notes="Initial authoritative conversion metric using distinct-user denominator.",
        )

        metric_cvr_event = MetricDefinition(
            name="purchase_conversion_rate_event",
            display_name="Purchase Conversion Rate - Event Denominator",
            description="Event-level conversion proxy. Kept active to demonstrate denominator conflict risk.",
            numerator_sql="COUNT(*) FILTER (WHERE event_type = 'transaction')",
            denominator_sql="COUNT(*) FILTER (WHERE event_type = 'view')",
            denominator_type="event_count",
            filter_sql="event_type IN ('view', 'transaction')",
            grain="daily",
            entity_type="event",
            direction="increase_good",
            is_guardrail=False,
            owner="growth_analytics",
            version=1,
            config_hash=hash_config("purchase_conversion_rate_event_v1"),
            change_notes="Non-authoritative conversion variant used to demonstrate denominator governance.",
        )

        metric_refund_guardrail = MetricDefinition(
            name="refund_rate_guardrail",
            display_name="Refund Rate Guardrail",
            description="Delayed guardrail metric tracking refund/return initiation risk.",
            numerator_sql="COUNT(*) FILTER (WHERE event_type = 'return_initiated')",
            denominator_sql="COUNT(*) FILTER (WHERE event_type = 'transaction')",
            denominator_type="purchase_events",
            filter_sql="event_type IN ('transaction', 'return_initiated')",
            grain="daily",
            entity_type="event",
            direction="decrease_good",
            is_guardrail=True,
            guardrail_tolerance_pct=2.0,
            guardrail_window_days=30,
            owner="marketplace_integrity",
            version=1,
            config_hash=hash_config("refund_rate_guardrail_v1"),
            change_notes="Delayed guardrail requires maturity window before final ship decision.",
        )

        session.add_all([metric_cvr_user, metric_cvr_event, metric_refund_guardrail])
        session.flush()

        scenarios = [
            SimulationEvent(
                scenario_id="SIM-001",
                scenario_name="Baseline successful daily pipeline",
                scenario_type="pipeline_success",
                simulation_day=1,
                event_date=date(2015, 5, 3),
                description="Daily metric pipeline completes with all quality checks passing.",
                injected=True,
                injection_payload={"source": "retailrocket_standardized", "expected_rows_min": 2500000},
                expected_system_behavior="pipeline_run_log.status = success; quality checks pass.",
            ),
            SimulationEvent(
                scenario_id="SIM-002",
                scenario_name="Schema drift blocked compute",
                scenario_type="schema_drift",
                simulation_day=7,
                event_date=date(2015, 5, 9),
                description="Unexpected event column drift should block metric computation.",
                injected=True,
                injection_payload={"missing_column": "transaction_id", "severity": "blocking"},
                expected_system_behavior="data_quality_checks.passed = false; pipeline run blocked.",
            ),
            SimulationEvent(
                scenario_id="SIM-003",
                scenario_name="Late-arriving partition recompute",
                scenario_type="late_arrival",
                simulation_day=14,
                event_date=date(2015, 5, 16),
                description="Late-arriving transaction events trigger partition recompute.",
                injected=True,
                injection_payload={"late_event_pct": 3.8, "affected_partition": "2015-05-15"},
                expected_system_behavior="metric_results.late_arrival_flag = true for recomputed rows.",
            ),
            SimulationEvent(
                scenario_id="SIM-004",
                scenario_name="Positive primary lift with guardrail breach",
                scenario_type="experiment_guardrail_breach",
                simulation_day=21,
                event_date=date(2015, 5, 23),
                description="Treatment improves conversion but breaches refund guardrail.",
                injected=True,
                injection_payload={"primary_lift_pct": 4.2, "refund_lift_pct": 3.1},
                expected_system_behavior="decision_recommendation = HOLD despite primary metric lift.",
            ),
            SimulationEvent(
                scenario_id="SIM-005",
                scenario_name="Human override with written justification",
                scenario_type="decision_override",
                simulation_day=30,
                event_date=date(2015, 6, 1),
                description="Reviewer overrides system HOLD recommendation with documented business rationale.",
                injected=True,
                injection_payload={"system_recommendation": "HOLD", "final_decision": "SHIP_WITH_MONITORING"},
                expected_system_behavior="decision_log.override_reason is populated.",
            ),
        ]

        session.add_all(scenarios)

        run = PipelineRunLog(
            job_type="daily_metric_compute",
            run_date=date(2015, 5, 3),
            started_at=datetime(2015, 5, 3, 6, 0, tzinfo=timezone.utc),
            completed_at=datetime(2015, 5, 3, 6, 11, tzinfo=timezone.utc),
            status="success",
            rows_processed=2756101,
            rows_expected=2756101,
            quality_checks_passed=3,
            quality_checks_failed=0,
            config_hash=hash_config("daily_metric_compute_2015_05_03_v1"),
            retry_count=0,
            triggered_by="seed_core",
        )
        session.add(run)
        session.flush()

        checks = [
            DataQualityCheck(
                run_id=run.id,
                check_name="row_count_parity",
                entity="events_standardized",
                check_date=date(2015, 5, 3),
                expected_value=2756101,
                actual_value=2756101,
                threshold=0,
                passed=True,
                severity="blocking",
                check_details={"rule": "actual rows must match generated standardized event count"},
            ),
            DataQualityCheck(
                run_id=run.id,
                check_name="required_columns_present",
                entity="events_standardized",
                check_date=date(2015, 5, 3),
                expected_value=6,
                actual_value=6,
                threshold=0,
                passed=True,
                severity="blocking",
                check_details={"columns": ["event_timestamp", "event_date", "user_id", "event_type", "item_id", "transaction_id"]},
            ),
            DataQualityCheck(
                run_id=run.id,
                check_name="event_type_domain_check",
                entity="events_standardized",
                check_date=date(2015, 5, 3),
                expected_value=3,
                actual_value=3,
                threshold=0,
                passed=True,
                severity="warning",
                check_details={"allowed_values": ["view", "addtocart", "transaction"]},
            ),
        ]
        session.add_all(checks)

        exp = Experiment(
            experiment_key="EXP-CHECKOUT-FRICTION-001",
            name="Checkout Friction Reduction",
            hypothesis="Reducing checkout friction should increase purchase conversion without increasing refund rate.",
            start_date=date(2015, 5, 10),
            end_date=date(2015, 5, 24),
            status="evaluated",
            primary_metric_id=metric_cvr_user.id,
            guardrail_metric_configs=[
                {
                    "metric_name": "refund_rate_guardrail",
                    "metric_id": str(metric_refund_guardrail.id),
                    "max_allowed_relative_increase_pct": 2.0,
                    "maturity_window_days": 30,
                }
            ],
            expected_mde=0.02,
            expected_duration_days=14,
            alpha=0.05,
            power=0.80,
            use_cuped=True,
            assignment_method="deterministic_hash",
            treatment_split_pct=0.50,
            notes="Seed experiment demonstrating guardrail-first decisioning.",
            created_by="seed_core",
        )
        session.add(exp)
        session.flush()

        evaluation = ExperimentEvaluation(
            experiment_id=exp.id,
            evaluation_day=14,
            sample_size_treatment=48520,
            sample_size_control=48610,
            primary_metric_lift=0.041,
            primary_metric_ci_lower=0.012,
            primary_metric_ci_upper=0.071,
            p_value=0.008,
            is_significant=True,
            cuped_applied=True,
            cuped_theta=0.37,
            variance_reduction_pct=18.4,
            guardrail_results=[
                {
                    "metric_name": "refund_rate_guardrail",
                    "status": "breached",
                    "observed_relative_increase_pct": 3.1,
                    "max_allowed_relative_increase_pct": 2.0,
                    "maturity_status": "immature_at_day_14",
                }
            ],
            guardrails_cleared=False,
            peeking_warning=False,
            simpsons_flag=False,
            segment_analysis={
                "top_segment": "returning_users_mobile",
                "note": "Lift concentrated in returning mobile users; refund risk also concentrated in same segment.",
            },
            novelty_flag=False,
            decision_recommendation="HOLD",
            recommendation_reason="Primary metric is statistically positive, but guardrail-first decisioning blocks shipment because refund-rate guardrail breached tolerance.",
            evaluator_version="eval_core_v0.1",
            is_aa_test=False,
        )
        session.add(evaluation)
        session.flush()

        decision = DecisionLog(
            experiment_id=exp.id,
            evaluation_id=evaluation.id,
            system_recommendation="HOLD",
            final_decision="HOLD",
            reviewer_name="Demo Reviewer",
            override_reason=None,
            decision_notes="System recommendation accepted. Treatment requires iteration before rollout.",
        )
        session.add(decision)

        session.commit()

        print("seed_core complete")
        for model in [
            MetricDefinition,
            SimulationEvent,
            PipelineRunLog,
            DataQualityCheck,
            Experiment,
            ExperimentEvaluation,
            DecisionLog,
        ]:
            count = session.scalar(select(func.count()).select_from(model))
            print(f"{model.__tablename__}: {count}")


if __name__ == "__main__":
    main()
