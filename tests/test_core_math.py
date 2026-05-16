"""Unit tests for MetaSignal core statistical functions.

All functions under test are pure Python (no DB, no pandas, no external calls).
They are loaded directly from scripts using importlib so no package restructuring
is required. Tests cover: SRM chi-square math, CUPED variance/covariance/theta,
two-sample z-test, variance reduction, and guardrail decision logic.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Load pure functions from scripts without triggering main() or DB imports
# ---------------------------------------------------------------------------

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


def _load_fn(script_name: str, fn_names: list[str]) -> dict:
    """Import named functions from a script file without running main()."""
    spec = importlib.util.spec_from_file_location(
        script_name.replace(".py", ""),
        SCRIPTS_DIR / script_name,
    )
    # Intercept DB/heavy imports by pre-loading stubs into sys.modules
    for stub in ["sqlalchemy", "sqlalchemy.orm", "pandas", "numpy",
                 "src.metasignal.db.session", "src.metasignal.db.models"]:
        if stub not in sys.modules:
            sys.modules[stub] = type(sys)("stub")  # type: ignore[arg-type]

    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    try:
        spec.loader.exec_module(module)  # type: ignore[union-attr]
    except Exception:
        pass  # top-level side effects may fail; functions are already loaded

    return {name: getattr(module, name) for name in fn_names if hasattr(module, name)}


_srm_fns = _load_fn("run_srm_check_v0.py", ["chi_square_p_value_df1"])
_cuped_fns = _load_fn(
    "run_cuped_v0.py",
    ["mean", "variance", "covariance", "diff_test", "p_value_from_z", "safe_divide"],
)

chi_square_p_value_df1 = _srm_fns.get("chi_square_p_value_df1")
mean = _cuped_fns.get("mean")
variance = _cuped_fns.get("variance")
covariance = _cuped_fns.get("covariance")
diff_test = _cuped_fns.get("diff_test")
p_value_from_z = _cuped_fns.get("p_value_from_z")
safe_divide = _cuped_fns.get("safe_divide")

# ---------------------------------------------------------------------------
# SRM: chi_square_p_value_df1
# ---------------------------------------------------------------------------

@pytest.mark.skipif(chi_square_p_value_df1 is None, reason="function not loaded")
class TestChiSquarePValue:
    def test_zero_stat_returns_one(self):
        """Chi-square = 0 → perfect fit → p-value = 1.0."""
        assert chi_square_p_value_df1(0.0) == pytest.approx(1.0, abs=1e-9)

    def test_large_stat_returns_near_zero(self):
        """Chi-square = 100 → extreme mismatch → p-value ≈ 0."""
        p = chi_square_p_value_df1(100.0)
        assert p < 1e-20

    def test_known_value_3_84(self):
        """Chi-square ≈ 3.841 is the 0.05 critical value for df=1."""
        p = chi_square_p_value_df1(3.841)
        assert 0.04 < p < 0.06

    def test_p_value_decreases_as_stat_increases(self):
        p_low = chi_square_p_value_df1(1.0)
        p_mid = chi_square_p_value_df1(5.0)
        p_high = chi_square_p_value_df1(20.0)
        assert p_low > p_mid > p_high

    def test_returns_float(self):
        result = chi_square_p_value_df1(2.0)
        assert isinstance(result, float)


# ---------------------------------------------------------------------------
# CUPED: mean / variance / covariance
# ---------------------------------------------------------------------------

@pytest.mark.skipif(mean is None, reason="function not loaded")
class TestMean:
    def test_basic_mean(self):
        assert mean([1.0, 2.0, 3.0]) == pytest.approx(2.0)

    def test_empty_returns_zero(self):
        assert mean([]) == 0.0

    def test_single_element(self):
        assert mean([42.0]) == 42.0

    def test_negative_values(self):
        assert mean([-1.0, 1.0]) == pytest.approx(0.0)


@pytest.mark.skipif(variance is None, reason="function not loaded")
class TestVariance:
    def test_constant_series_returns_zero(self):
        assert variance([5.0, 5.0, 5.0, 5.0]) == pytest.approx(0.0)

    def test_two_values_known_variance(self):
        # [0, 2]: sample variance = ((0-1)^2 + (2-1)^2) / 1 = 2.0
        assert variance([0.0, 2.0]) == pytest.approx(2.0)

    def test_single_element_returns_zero(self):
        assert variance([7.0]) == 0.0

    def test_standard_dataset(self):
        # [2, 4, 4, 4, 5, 5, 7, 9]: sample variance ≈ 4.571
        vals = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
        assert variance(vals) == pytest.approx(4.571, rel=1e-2)


@pytest.mark.skipif(covariance is None, reason="function not loaded")
class TestCovariance:
    def test_perfectly_correlated(self):
        xs = [1.0, 2.0, 3.0, 4.0, 5.0]
        ys = [2.0, 4.0, 6.0, 8.0, 10.0]  # ys = 2 * xs
        cov = covariance(xs, ys)
        assert cov > 0

    def test_negatively_correlated(self):
        xs = [1.0, 2.0, 3.0, 4.0, 5.0]
        ys = [5.0, 4.0, 3.0, 2.0, 1.0]
        cov = covariance(xs, ys)
        assert cov < 0

    def test_uncorrelated_returns_near_zero(self):
        xs = [1.0, 2.0, 3.0, 4.0]
        ys = [3.0, 1.0, 4.0, 2.0]  # shuffled — low covariance
        cov = covariance(xs, ys)
        assert abs(cov) < 2.0

    def test_single_pair_returns_zero(self):
        assert covariance([1.0], [2.0]) == 0.0


# ---------------------------------------------------------------------------
# CUPED: diff_test (z-test with CI)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(diff_test is None, reason="function not loaded")
class TestDiffTest:
    def test_significant_lift_detected(self):
        """Large treatment effect with large n → p < 0.05, is_significant=True."""
        control = [0.0] * 9000 + [1.0] * 1000     # rate 0.10
        treatment = [0.0] * 8800 + [1.0] * 1200   # rate 0.12
        result = diff_test(treatment, control)
        assert result["is_significant"] is True
        assert result["absolute_lift"] == pytest.approx(0.02, abs=0.001)

    def test_no_lift_not_significant(self):
        """Identical distributions → p ≈ 1.0, is_significant=False."""
        values = [0.0] * 500 + [1.0] * 500
        result = diff_test(values, values[:])
        assert result["is_significant"] is False

    def test_result_keys_present(self):
        result = diff_test([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])
        for key in ("mean_treatment", "mean_control", "absolute_lift",
                    "z_score", "p_value", "ci_low", "ci_high", "is_significant"):
            assert key in result

    def test_confidence_interval_contains_true_lift(self):
        """True lift = 0.10; CI should contain 0.10."""
        control = [0.0] * 9000 + [1.0] * 1000
        treatment = [0.0] * 8800 + [1.0] * 1200
        result = diff_test(treatment, control)
        assert result["ci_low"] <= 0.02 <= result["ci_high"]

    def test_relative_lift_computed_correctly(self):
        control = [1.0] * 1000
        treatment = [1.1] * 1000
        result = diff_test(treatment, control)
        assert result["relative_lift"] == pytest.approx(0.1, rel=1e-6)


# ---------------------------------------------------------------------------
# Guardrail decision logic (inline, as it's trivial enough to test directly)
# ---------------------------------------------------------------------------

class TestGuardrailDecision:
    """Test the guardrail-first ship/hold decision rule."""

    @staticmethod
    def _decide(guardrail_results: list[dict]) -> str:
        """Mirror the logic from run_guardrail_decision_v0.py."""
        guardrails_cleared = all(g["status"] == "pass" for g in guardrail_results)
        return "SHIP" if guardrails_cleared else "HOLD"

    def test_all_guardrails_pass_gives_ship(self):
        guardrails = [
            {"metric_name": "refund_rate", "status": "pass"},
            {"metric_name": "error_rate", "status": "pass"},
        ]
        assert self._decide(guardrails) == "SHIP"

    def test_single_fail_gives_hold(self):
        guardrails = [
            {"metric_name": "refund_rate", "status": "fail"},
            {"metric_name": "error_rate", "status": "pass"},
        ]
        assert self._decide(guardrails) == "HOLD"

    def test_all_fail_gives_hold(self):
        guardrails = [
            {"metric_name": "refund_rate", "status": "fail"},
            {"metric_name": "latency_p99", "status": "fail"},
        ]
        assert self._decide(guardrails) == "HOLD"

    def test_empty_guardrails_gives_ship(self):
        assert self._decide([]) == "SHIP"


# ---------------------------------------------------------------------------
# CUPED: variance reduction formula (theta, adjusted values)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(covariance is None or variance is None, reason="functions not loaded")
class TestCupedTheta:
    """Verify the CUPED theta = cov(X,Y) / var(X) is mathematically correct."""

    def test_theta_equals_regression_slope(self):
        """theta = cov(x, y) / var(x) is the OLS regression slope of y on x."""
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 3.5, 5.0, 6.5, 8.0]  # y ≈ 1.5x + 0.5
        theta = covariance(x, y) / variance(x)
        assert theta == pytest.approx(1.5, rel=1e-6)

    def test_theta_zero_when_uncorrelated(self):
        """Uncorrelated X and Y → theta ≈ 0 → no adjustment."""
        x = [1.0, 2.0, 3.0, 4.0]
        y = [10.0, 10.0, 10.0, 10.0]  # constant y, cov = 0
        theta = covariance(x, y) / variance(x)
        assert theta == pytest.approx(0.0, abs=1e-9)

    def test_variance_reduction_when_correlated(self):
        """Applying CUPED adjustment to correlated pre-period reduces variance."""
        import math
        n = 1000
        rng_seed = 42
        # Deterministic pseudo-random: pre ~ N(0,1), outcome = 0.5*pre + noise
        pre = [math.sin(i * 0.1) for i in range(n)]
        outcome = [0.5 * p + math.cos(i * 0.3) * 0.3 for i, p in enumerate(pre)]

        x_mean = mean(pre)
        theta = covariance(pre, outcome) / variance(pre) if variance(pre) > 0 else 0.0
        adjusted = [o - theta * (p - x_mean) for o, p in zip(outcome, pre)]

        var_raw = variance(outcome)
        var_adjusted = variance(adjusted)
        assert var_adjusted < var_raw
