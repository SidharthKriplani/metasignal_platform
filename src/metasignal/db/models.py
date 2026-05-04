from __future__ import annotations

import uuid
from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class PipelineRunLog(Base):
    __tablename__ = "pipeline_run_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_type: Mapped[str] = mapped_column(String(64), nullable=False)
    run_date: Mapped[date] = mapped_column(Date, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    rows_processed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rows_expected: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quality_checks_passed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quality_checks_failed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    config_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    triggered_by: Mapped[str] = mapped_column(String(64), nullable=False, default="manual")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())


class MetricDefinition(Base):
    __tablename__ = "metric_definitions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    numerator_sql: Mapped[str] = mapped_column(Text, nullable=False)
    denominator_sql: Mapped[str] = mapped_column(Text, nullable=False)
    denominator_type: Mapped[str] = mapped_column(String(64), nullable=False)
    filter_sql: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    grain: Mapped[str] = mapped_column(String(32), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    direction: Mapped[str] = mapped_column(String(32), nullable=False)
    is_guardrail: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    guardrail_tolerance_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    guardrail_window_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    owner: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    deprecated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    parent_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("metric_definitions.id"), nullable=True)
    change_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    config_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())

    parent_version = relationship("MetricDefinition", remote_side=[id])


class MetricResult(Base):
    __tablename__ = "metric_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("metric_definitions.id"), nullable=False)
    metric_version: Mapped[int] = mapped_column(Integer, nullable=False)
    computation_date: Mapped[date] = mapped_column(Date, nullable=False)
    grain_period: Mapped[str] = mapped_column(String(64), nullable=False)
    numerator_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    denominator_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    metric_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    segment_key: Mapped[str] = mapped_column(String(256), nullable=False, default="ALL")
    run_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("pipeline_run_log.id"), nullable=True)
    quality_passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    late_arrival_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())

    metric = relationship("MetricDefinition")
    run = relationship("PipelineRunLog")

    __table_args__ = (
        UniqueConstraint("metric_id", "metric_version", "grain_period", "segment_key", name="uq_metric_result_grain_segment"),
    )


class DataQualityCheck(Base):
    __tablename__ = "data_quality_checks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("pipeline_run_log.id"), nullable=False)
    check_name: Mapped[str] = mapped_column(String(128), nullable=False)
    entity: Mapped[str] = mapped_column(String(128), nullable=False)
    check_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    threshold: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    check_details: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())

    run = relationship("PipelineRunLog")


class SimulationEvent(Base):
    __tablename__ = "simulation_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    scenario_name: Mapped[str] = mapped_column(String(256), nullable=False)
    scenario_type: Mapped[str] = mapped_column(String(128), nullable=False)
    simulation_day: Mapped[int] = mapped_column(Integer, nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    injected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    injection_payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    expected_system_behavior: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    primary_metric_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("metric_definitions.id"), nullable=True)
    guardrail_metric_configs: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    expected_mde: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    expected_duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    alpha: Mapped[float] = mapped_column(Float, nullable=False, default=0.05)
    power: Mapped[float] = mapped_column(Float, nullable=False, default=0.80)
    use_cuped: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    assignment_method: Mapped[str] = mapped_column(String(64), nullable=False, default="deterministic_hash")
    treatment_split_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.50)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())

    primary_metric = relationship("MetricDefinition")


class ExperimentEvaluation(Base):
    __tablename__ = "experiment_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("experiments.id"), nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    evaluation_day: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sample_size_treatment: Mapped[int] = mapped_column(Integer, nullable=False)
    sample_size_control: Mapped[int] = mapped_column(Integer, nullable=False)
    primary_metric_lift: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    primary_metric_ci_lower: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    primary_metric_ci_upper: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    p_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_significant: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    cuped_applied: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cuped_theta: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    variance_reduction_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cuped_edge_case: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    cuped_fallback: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    guardrail_results: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    guardrails_cleared: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    peeking_warning: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    simpsons_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    segment_analysis: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    novelty_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    decision_recommendation: Mapped[str] = mapped_column(String(64), nullable=False)
    recommendation_reason: Mapped[str] = mapped_column(Text, nullable=False)
    evaluator_version: Mapped[str] = mapped_column(String(64), nullable=False)
    is_aa_test: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())

    experiment = relationship("Experiment")


class DecisionLog(Base):
    __tablename__ = "decision_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("experiments.id"), nullable=False)
    evaluation_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("experiment_evaluations.id"), nullable=True)
    system_recommendation: Mapped[str] = mapped_column(String(64), nullable=False)
    final_decision: Mapped[str] = mapped_column(String(64), nullable=False)
    reviewer_name: Mapped[str] = mapped_column(String(128), nullable=False)
    override_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decision_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())

    experiment = relationship("Experiment")
    evaluation = relationship("ExperimentEvaluation")
