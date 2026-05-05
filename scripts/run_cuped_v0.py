from __future__ import annotations

import hashlib
import json
import math
from datetime import date, datetime
from pathlib import Path
from uuid import UUID

import pandas as pd
from sqlalchemy import delete, select

from src.metasignal.db.session import SessionLocal
from src.metasignal.db.models import Experiment, ExperimentAssignment, ExperimentEvaluation, DecisionLog


EVENTS_PATH = Path("data/interim/events_standardized.parquet")
OUT_PATH = Path("outputs/evidence/cuped_experiment_readout.json")
EXPERIMENT_KEY = "EXP-CHECKOUT-FRICTION-001"


def json_safe(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    return value


def p_value_from_z(z: float) -> float:
    return math.erfc(abs(z) / math.sqrt(2.0))


def safe_divide(num: float, den: float):
    if den == 0:
        return None
    return num / den


def deterministic_uplift(experiment_key: str, user_id: str, threshold: float = 0.025) -> bool:
    raw = f"{experiment_key}:uplift:{user_id}"
    h = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    bucket = int(h[:12], 16) / float(16 ** 12)
    return bucket < threshold


def mean(values):
    return sum(values) / len(values) if values else 0.0


def variance(values):
    if len(values) <= 1:
        return 0.0
    m = mean(values)
    return sum((x - m) ** 2 for x in values) / (len(values) - 1)


def covariance(xs, ys):
    if len(xs) <= 1:
        return 0.0
    mx = mean(xs)
    my = mean(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (len(xs) - 1)


def diff_test(treatment_values, control_values):
    n_t = len(treatment_values)
    n_c = len(control_values)

    mean_t = mean(treatment_values)
    mean_c = mean(control_values)
    diff = mean_t - mean_c

    var_t = variance(treatment_values)
    var_c = variance(control_values)

    se = math.sqrt((var_t / n_t) + (var_c / n_c)) if n_t > 0 and n_c > 0 else 0.0
    z = diff / se if se > 0 else 0.0
    p_value = p_value_from_z(z) if se > 0 else None

    ci_low = diff - 1.96 * se
    ci_high = diff + 1.96 * se

    return {
        "n_treatment": n_t,
        "n_control": n_c,
        "mean_treatment": mean_t,
        "mean_control": mean_c,
        "absolute_lift": diff,
        "relative_lift": safe_divide(diff, mean_c),
        "standard_error": se,
        "z_score": z,
        "p_value": p_value,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "is_significant": bool(p_value is not None and p_value < 0.05),
    }


def main() -> None:
    if not EVENTS_PATH.exists():
        raise FileNotFoundError(f"Missing standardized events file: {EVENTS_PATH}")

    with SessionLocal() as session:
        experiment = session.scalar(
            select(Experiment).where(Experiment.experiment_key == EXPERIMENT_KEY)
        )
        if experiment is None:
            raise ValueError(f"Experiment not found: {EXPERIMENT_KEY}")

        assignments = session.scalars(
            select(ExperimentAssignment).where(ExperimentAssignment.experiment_id == experiment.id)
        ).all()

        if not assignments:
            raise ValueError("No experiment assignments found. Run generate_assignments_v0.py first.")

        assignment_df = pd.DataFrame(
            [
                {
                    "user_id": a.user_id,
                    "variant": a.variant,
                    "assignment_bucket": a.assignment_bucket,
                }
                for a in assignments
            ]
        )

        df = pd.read_parquet(EVENTS_PATH, columns=["user_id", "event_date", "event_type"])
        df["user_id"] = df["user_id"].astype(str)
        df["event_date"] = pd.to_datetime(df["event_date"]).dt.date
        df["event_type"] = df["event_type"].astype(str)

        start = experiment.start_date
        end = experiment.end_date

        pre_df = df[df["event_date"] < start]
        exp_df = df[(df["event_date"] >= start) & (df["event_date"] <= end)]

        pre_features = (
            pre_df.groupby("user_id")
            .agg(
                pre_event_count=("event_type", "count"),
                pre_purchase_count=("event_type", lambda s: int((s == "transaction").sum())),
            )
            .reset_index()
        )

        outcome = (
            exp_df.groupby("user_id")
            .agg(
                exp_event_count=("event_type", "count"),
                purchase_count=("event_type", lambda s: int((s == "transaction").sum())),
            )
            .reset_index()
        )

        user_df = assignment_df.merge(pre_features, on="user_id", how="left").merge(outcome, on="user_id", how="left")
        user_df[["pre_event_count", "pre_purchase_count", "exp_event_count", "purchase_count"]] = (
            user_df[["pre_event_count", "pre_purchase_count", "exp_event_count", "purchase_count"]].fillna(0)
        )

        user_df["raw_conversion"] = (user_df["purchase_count"] > 0).astype(float)

        # Controlled synthetic treatment effect for portfolio simulation:
        # Some treatment users with experiment-period activity are converted deterministically.
        user_df["uplift_injected"] = user_df.apply(
            lambda r: (
                r["variant"] == "treatment"
                and r["raw_conversion"] == 0
                and r["exp_event_count"] > 0
                and deterministic_uplift(EXPERIMENT_KEY, r["user_id"])
            ),
            axis=1,
        )

        user_df["conversion"] = user_df["raw_conversion"]
        user_df.loc[user_df["uplift_injected"], "conversion"] = 1.0

        x = user_df["pre_event_count"].astype(float).tolist()
        y = user_df["conversion"].astype(float).tolist()

        var_x = variance(x)
        cov_xy = covariance(x, y)
        theta = cov_xy / var_x if var_x > 0 else 0.0
        x_mean = mean(x)

        user_df["cuped_conversion"] = user_df["conversion"] - theta * (user_df["pre_event_count"] - x_mean)

        treatment_raw = user_df.loc[user_df["variant"] == "treatment", "conversion"].astype(float).tolist()
        control_raw = user_df.loc[user_df["variant"] == "control", "conversion"].astype(float).tolist()

        treatment_cuped = user_df.loc[user_df["variant"] == "treatment", "cuped_conversion"].astype(float).tolist()
        control_cuped = user_df.loc[user_df["variant"] == "control", "cuped_conversion"].astype(float).tolist()

        raw_result = diff_test(treatment_raw, control_raw)
        cuped_result = diff_test(treatment_cuped, control_cuped)

        raw_var = variance(y)
        cuped_var = variance(user_df["cuped_conversion"].astype(float).tolist())
        variance_reduction_pct = (1.0 - (cuped_var / raw_var)) * 100.0 if raw_var > 0 else 0.0

        old_evals = session.scalars(
            select(ExperimentEvaluation).where(
                ExperimentEvaluation.experiment_id == experiment.id,
                ExperimentEvaluation.evaluator_version == "cuped_v0",
            )
        ).all()

        for old_eval in old_evals:
            session.execute(
                delete(DecisionLog).where(DecisionLog.evaluation_id == old_eval.id)
            )

        session.execute(
            delete(ExperimentEvaluation).where(
                ExperimentEvaluation.experiment_id == experiment.id,
                ExperimentEvaluation.evaluator_version == "cuped_v0",
            )
        )

        eval_row = ExperimentEvaluation(
            experiment_id=experiment.id,
            evaluation_day=(end - start).days + 1,
            sample_size_treatment=raw_result["n_treatment"],
            sample_size_control=raw_result["n_control"],
            primary_metric_lift=cuped_result["relative_lift"],
            primary_metric_ci_lower=cuped_result["ci_low"],
            primary_metric_ci_upper=cuped_result["ci_high"],
            p_value=cuped_result["p_value"],
            is_significant=cuped_result["is_significant"],
            cuped_applied=True,
            cuped_theta=theta,
            variance_reduction_pct=variance_reduction_pct,
            cuped_edge_case=None,
            cuped_fallback=None,
            guardrail_results=[],
            guardrails_cleared=None,
            peeking_warning=False,
            simpsons_flag=False,
            segment_analysis={
                "covariate": "pre_event_count",
                "synthetic_uplift_users": int(user_df["uplift_injected"].sum()),
                "note": "CUPED v0 uses pre-period engagement as covariate and controlled synthetic treatment uplift for demo readout.",
            },
            novelty_flag=False,
            decision_recommendation="INVESTIGATE",
            recommendation_reason="CUPED-adjusted readout complete; guardrail-first decision engine has not yet been applied.",
            evaluator_version="cuped_v0",
            is_aa_test=False,
        )
        session.add(eval_row)
        session.commit()

        payload = {
            "artifact": "cuped_experiment_readout",
            "experiment_key": experiment.experiment_key,
            "period": {
                "pre_period_end_before": start,
                "experiment_start": start,
                "experiment_end": end,
            },
            "sample": {
                "assigned_users": len(user_df),
                "treatment_users": raw_result["n_treatment"],
                "control_users": raw_result["n_control"],
                "synthetic_uplift_users": int(user_df["uplift_injected"].sum()),
            },
            "raw_readout": raw_result,
            "cuped_readout": cuped_result,
            "cuped": {
                "covariate": "pre_event_count",
                "theta": theta,
                "raw_variance": raw_var,
                "cuped_variance": cuped_var,
                "variance_reduction_pct": variance_reduction_pct,
            },
            "db_evaluation_id": eval_row.id,
            "evidence_statement": "MetaSignal computed an experiment readout with CUPED variance adjustment using deterministic user assignments and pre-period behavior.",
        }

        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUT_PATH.write_text(json.dumps(payload, indent=2, default=json_safe), encoding="utf-8")

        print("cuped_v0 complete")
        print(f"assigned_users: {len(user_df)}")
        print(f"synthetic_uplift_users: {int(user_df['uplift_injected'].sum())}")
        print(f"raw_relative_lift: {raw_result['relative_lift']}")
        print(f"raw_p_value: {raw_result['p_value']}")
        print(f"cuped_relative_lift: {cuped_result['relative_lift']}")
        print(f"cuped_p_value: {cuped_result['p_value']}")
        print(f"variance_reduction_pct: {variance_reduction_pct}")
        print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
