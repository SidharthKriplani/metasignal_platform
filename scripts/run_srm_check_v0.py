from __future__ import annotations

import json
import math
from datetime import date, datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy import select, func

from src.metasignal.db.session import SessionLocal
from src.metasignal.db.models import Experiment, ExperimentAssignment


OUT_PATH = Path("outputs/evidence/srm_check_report.json")
EXPERIMENT_KEY = "EXP-CHECKOUT-FRICTION-001"


def json_safe(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    return value


def chi_square_p_value_df1(chi_square_stat: float) -> float:
    return math.erfc(math.sqrt(chi_square_stat / 2.0))


def main() -> None:
    with SessionLocal() as session:
        experiment = session.scalar(
            select(Experiment).where(Experiment.experiment_key == EXPERIMENT_KEY)
        )

        if experiment is None:
            raise ValueError(f"Experiment not found: {EXPERIMENT_KEY}")

        rows = session.execute(
            select(
                ExperimentAssignment.variant,
                func.count(ExperimentAssignment.id),
            )
            .where(ExperimentAssignment.experiment_id == experiment.id)
            .group_by(ExperimentAssignment.variant)
        ).all()

        counts = {variant: count for variant, count in rows}
        treatment_count = counts.get("treatment", 0)
        control_count = counts.get("control", 0)
        total = treatment_count + control_count

        expected_treatment = total * experiment.treatment_split_pct
        expected_control = total * (1.0 - experiment.treatment_split_pct)

        chi_square = 0.0
        if expected_treatment > 0:
            chi_square += ((treatment_count - expected_treatment) ** 2) / expected_treatment
        if expected_control > 0:
            chi_square += ((control_count - expected_control) ** 2) / expected_control

        p_value = chi_square_p_value_df1(chi_square)
        srm_detected = p_value < 0.001

        payload = {
            "artifact": "srm_check_report",
            "experiment_key": experiment.experiment_key,
            "assignment_method": experiment.assignment_method,
            "expected_treatment_share": experiment.treatment_split_pct,
            "observed": {
                "treatment_count": treatment_count,
                "control_count": control_count,
                "total": total,
                "treatment_share": treatment_count / total if total else None,
                "control_share": control_count / total if total else None,
            },
            "srm_test": {
                "test": "chi_square_goodness_of_fit_df1",
                "chi_square_stat": chi_square,
                "p_value": p_value,
                "alpha": 0.001,
                "srm_detected": srm_detected,
                "status": "fail" if srm_detected else "pass",
            },
            "evidence_statement": "MetaSignal checked sample ratio mismatch on deterministic experiment assignments before experiment readout.",
        }

        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUT_PATH.write_text(json.dumps(payload, indent=2, default=json_safe), encoding="utf-8")

        print("srm_check_v0 complete")
        print(f"total_assignments: {total}")
        print(f"treatment_count: {treatment_count}")
        print(f"control_count: {control_count}")
        print(f"chi_square_stat: {chi_square}")
        print(f"p_value: {p_value}")
        print(f"srm_status: {payload['srm_test']['status']}")
        print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
