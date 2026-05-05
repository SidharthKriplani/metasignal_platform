from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np


OUT_PATH = Path("outputs/validation/cuped_aa_validation_report.json")
N_RUNS = 1000
N_USERS = 4000
ALPHA = 0.05
RNG_SEED = 42


def two_sided_normal_pvalue(z: float) -> float:
    return math.erfc(abs(z) / math.sqrt(2.0))


def ks_uniform_statistic(p_values: list[float]) -> float:
    values = sorted(p_values)
    n = len(values)
    return max(
        max((i + 1) / n - p for i, p in enumerate(values)),
        max(p - i / n for i, p in enumerate(values)),
    )


def main() -> None:
    rng = np.random.default_rng(RNG_SEED)

    raw_p_values = []
    cuped_p_values = []
    variance_reductions = []

    for _ in range(N_RUNS):
        x_pre = rng.normal(loc=0.0, scale=1.0, size=N_USERS)
        y_post = 0.6 * x_pre + rng.normal(loc=0.0, scale=1.0, size=N_USERS)

        assignment = rng.integers(0, 2, size=N_USERS)
        control = assignment == 0
        treatment = assignment == 1

        raw_diff = y_post[treatment].mean() - y_post[control].mean()
        raw_se = math.sqrt(
            y_post[treatment].var(ddof=1) / treatment.sum()
            + y_post[control].var(ddof=1) / control.sum()
        )
        raw_z = raw_diff / raw_se
        raw_p_values.append(two_sided_normal_pvalue(raw_z))

        theta = np.cov(y_post, x_pre, ddof=1)[0, 1] / np.var(x_pre, ddof=1)
        y_cuped = y_post - theta * (x_pre - x_pre.mean())

        cuped_diff = y_cuped[treatment].mean() - y_cuped[control].mean()
        cuped_se = math.sqrt(
            y_cuped[treatment].var(ddof=1) / treatment.sum()
            + y_cuped[control].var(ddof=1) / control.sum()
        )
        cuped_z = cuped_diff / cuped_se
        cuped_p_values.append(two_sided_normal_pvalue(cuped_z))

        raw_var = float(np.var(y_post, ddof=1))
        cuped_var = float(np.var(y_cuped, ddof=1))
        variance_reductions.append((1 - cuped_var / raw_var) * 100)

    raw_false_positive_rate = float(np.mean(np.array(raw_p_values) < ALPHA))
    cuped_false_positive_rate = float(np.mean(np.array(cuped_p_values) < ALPHA))

    ks_stat = ks_uniform_statistic(cuped_p_values)
    ks_critical_5pct = 1.36 / math.sqrt(N_RUNS)
    ks_pass = ks_stat < ks_critical_5pct

    payload = {
        "artifact": "cuped_aa_validation_report",
        "validation_type": "synthetic_aa_test",
        "runs": N_RUNS,
        "users_per_run": N_USERS,
        "alpha": ALPHA,
        "raw_false_positive_rate": raw_false_positive_rate,
        "cuped_false_positive_rate": cuped_false_positive_rate,
        "mean_variance_reduction_pct": float(np.mean(variance_reductions)),
        "median_variance_reduction_pct": float(np.median(variance_reductions)),
        "cuped_p_value_uniformity": {
            "ks_statistic": ks_stat,
            "ks_critical_5pct": ks_critical_5pct,
            "passed": ks_pass,
        },
        "status": "pass" if ks_pass and 0.035 <= cuped_false_positive_rate <= 0.065 else "review",
        "evidence_statement": "MetaSignal validates CUPED on 1000 synthetic A/A runs: false positive rate remains controlled and CUPED p-values are checked against a Uniform(0,1) distribution.",
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("cuped_aa_validation_v0 complete")
    print(f"runs: {N_RUNS}")
    print(f"raw_false_positive_rate: {raw_false_positive_rate:.4f}")
    print(f"cuped_false_positive_rate: {cuped_false_positive_rate:.4f}")
    print(f"mean_variance_reduction_pct: {payload['mean_variance_reduction_pct']:.2f}")
    print(f"ks_statistic: {ks_stat:.4f}")
    print(f"ks_critical_5pct: {ks_critical_5pct:.4f}")
    print(f"status: {payload['status']}")
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
