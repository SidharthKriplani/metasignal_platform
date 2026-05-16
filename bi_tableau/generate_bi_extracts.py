"""
generate_bi_extracts.py
MetaSignal BI Layer — Synthetic Data Generator

Produces five CSV files that power the MetaSignal Executive BI Dashboard.
Data is synthetic but structurally faithful to MetaSignal's actual audit output
schema. Includes realistic noise, edge cases, SRM failures, guardrail violations,
and borderline results — not a clean demo, a realistic experimentation program.

Run:
    python bi_tableau/generate_bi_extracts.py

Output (written to bi_tableau/data/):
    experiments.csv         — one row per experiment, core readout fields
    guardrails.csv          — one row per experiment × guardrail metric
    experiment_checks.csv   — one row per experiment × audit check
    segments.csv            — one row per experiment × segment × segment value
    metric_quality.csv      — one row per experiment, quality signal fields
"""

import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 42
random.seed(SEED)

OUT_DIR = Path(__file__).parent / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────

TEAMS = ["Growth", "Payments", "Onboarding", "Retention", "Search", "Monetisation"]

EXPERIMENT_NAMES = [
    "checkout_cta_color_v2",
    "homepage_hero_personalisation",
    "email_digest_frequency_test",
    "payment_page_trust_badges",
    "onboarding_step_reduction",
    "search_ranking_recency_boost",
    "retention_winback_offer_amount",
    "premium_upsell_modal_timing",
    "referral_incentive_structure",
    "cart_abandonment_nudge_delay",
    "notification_opt_in_prompt",
    "feed_algorithm_diversity_weight",
    "pricing_page_layout_b",
    "signup_form_field_reduction",
    "loyalty_points_display",
    "support_chat_proactive_trigger",
    "product_image_carousel_count",
    "coupon_visibility_placement",
    "social_proof_review_count",
    "dashboard_default_view",
    "cancellation_flow_pause_offer",
    "mobile_nav_bottom_bar_v3",
    "ai_recommendations_blend_ratio",
    "invoice_summary_format",
    "free_trial_duration_14d",
]

PRIMARY_METRICS = [
    "conversion_rate",
    "activation_rate",
    "click_through_rate",
    "signup_rate",
    "checkout_completion_rate",
]

GUARDRAIL_NAMES = ["p99_latency_ms", "error_rate_pct", "revenue_per_user", "session_duration_s"]

SEGMENT_COLS = ["device_type", "region", "user_cohort", "plan_type"]

SEGMENT_VALUES = {
    "device_type": ["mobile", "desktop", "tablet"],
    "region": ["IN", "US", "SEA", "EU", "LATAM"],
    "user_cohort": ["new", "returning", "power"],
    "plan_type": ["free", "pro", "enterprise"],
}

CHECK_NAMES = [
    "srm_check",
    "pre_period_balance",
    "primary_metric_significance",
    "continuous_metric_significance",
    "peeking_risk",
    "practical_significance",
    "guardrail_movement",
]

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def rnd(val, decimals=4):
    return round(val, decimals)

def clamp(val, lo, hi):
    return max(lo, min(hi, val))

def gauss(mu, sigma, lo=None, hi=None):
    v = random.gauss(mu, sigma)
    if lo is not None: v = max(lo, v)
    if hi is not None: v = min(hi, v)
    return v

def erfc_approx(x):
    """Approximate erfc for SRM p-value calculation."""
    t = 1.0 / (1.0 + 0.3275911 * abs(x))
    poly = t * (0.254829592 + t * (-0.284496736 + t * (1.421413741 + t * (-1.453152027 + t * 1.061405429))))
    return poly * math.exp(-x * x)

def srm_p_value(n_control, n_treatment, planned_split=0.5):
    n_total = n_control + n_treatment
    expected_c = n_total * planned_split
    expected_t = n_total * (1 - planned_split)
    chi2 = ((n_control - expected_c) ** 2 / expected_c +
            (n_treatment - expected_t) ** 2 / expected_t)
    return rnd(erfc_approx(math.sqrt(chi2 / 2)), 6)

def z_test_p_value(p1, p2, n1, n2):
    p_pool = (p1 * n1 + p2 * n2) / (n1 + n2)
    if p_pool <= 0 or p_pool >= 1:
        return 0.5
    se = math.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
    if se == 0:
        return 1.0
    z = abs(p2 - p1) / se
    return rnd(erfc_approx(z / math.sqrt(2)), 4)

def norm_cdf_approx(z):
    return 0.5 * erfc_approx(-z / math.sqrt(2))

# ─────────────────────────────────────────────────────────────
# GENERATE EXPERIMENTS
# ─────────────────────────────────────────────────────────────

def generate_experiments():
    rows = []
    base_date = date(2025, 11, 1)

    for i, name in enumerate(EXPERIMENT_NAMES):
        team = TEAMS[i % len(TEAMS)]
        metric = PRIMARY_METRICS[i % len(PRIMARY_METRICS)]
        planned_duration = random.choice([7, 10, 14, 21, 28])
        start_offset = random.randint(0, 120)
        start_date = base_date + timedelta(days=start_offset)

        # Introduce peeking for ~25% of experiments
        peeking = random.random() < 0.25
        if peeking:
            actual_duration = int(planned_duration * gauss(0.6, 0.1, 0.4, 0.79))
        else:
            actual_duration = int(planned_duration * gauss(1.02, 0.08, 0.80, 1.25))

        end_date = start_date + timedelta(days=actual_duration)

        # Sample sizes — realistic scale
        base_n = random.randint(8000, 80000)
        planned_split = 0.5

        # SRM for exactly 2 experiments (indices 4 and 17)
        srm_fail = i in (4, 17)
        if srm_fail:
            # Inject split imbalance
            split_skew = gauss(0.0, 0.06)
            n_control = int(base_n * (planned_split + split_skew))
            n_treatment = base_n - n_control
        else:
            noise = random.randint(-int(base_n * 0.01), int(base_n * 0.01))
            n_control = base_n // 2 + noise
            n_treatment = base_n - n_control

        srm_p = srm_p_value(n_control, n_treatment, planned_split)
        # srm_status is authoritative from the injection flag, not the p-value
        srm_status = "FAIL" if srm_fail else "PASS"

        # Control rate
        control_rate = gauss(0.045, 0.025, 0.005, 0.25)

        # Lift: mix of null, small positive, large positive, negative
        lift_scenario = random.choices(
            ["null", "small_pos", "meaningful_pos", "large_pos", "negative"],
            weights=[0.20, 0.25, 0.30, 0.10, 0.15]
        )[0]

        if lift_scenario == "null":
            true_lift = gauss(0.0, 0.003)
        elif lift_scenario == "small_pos":
            true_lift = gauss(0.005, 0.002, 0.001, 0.009)
        elif lift_scenario == "meaningful_pos":
            true_lift = gauss(0.018, 0.006, 0.010, 0.040)
        elif lift_scenario == "large_pos":
            true_lift = gauss(0.055, 0.015, 0.035, 0.090)
        else:  # negative
            true_lift = gauss(-0.012, 0.005, -0.030, -0.001)

        treatment_rate = clamp(control_rate + true_lift, 0.001, 0.50)
        control_conversions = int(n_control * control_rate)
        treatment_conversions = int(n_treatment * treatment_rate)

        # Observed rates with sampling noise
        obs_control_rate = control_conversions / n_control
        obs_treatment_rate = treatment_conversions / n_treatment
        obs_lift_pct = rnd((obs_treatment_rate - obs_control_rate) / obs_control_rate * 100, 2)

        p_value = z_test_p_value(obs_control_rate, obs_treatment_rate, n_control, n_treatment)
        alpha = 0.05
        is_significant = p_value < alpha and srm_status == "PASS"

        practical_threshold_pct = 1.0  # 1% relative lift
        is_practically_significant = abs(obs_lift_pct) >= practical_threshold_pct

        # Peeking risk level
        duration_ratio = actual_duration / planned_duration
        interim_looks = random.randint(0, 2) if not peeking else random.randint(3, 7)
        if duration_ratio < 0.80 or interim_looks >= 3:
            peeking_risk = "HIGH" if (duration_ratio < 0.65 or interim_looks >= 5) else "LOW"
        else:
            peeking_risk = "NONE"

        # Overall status
        if srm_status == "FAIL":
            overall_status = "FAIL"
        elif peeking_risk == "HIGH" or (is_significant and not is_practically_significant):
            overall_status = "WARN"
        elif not is_significant and lift_scenario not in ["null"]:
            overall_status = "WARN"
        else:
            overall_status = "PASS" if is_significant else "WARN"

        # Ship decision
        if overall_status == "FAIL":
            ship_decision = "REJECTED"
        elif overall_status == "WARN":
            ship_decision = random.choice(["HELD", "IN_REVIEW", "SHIPPED_WITH_NOTE"])
        elif is_significant and is_practically_significant and obs_lift_pct > 0:
            ship_decision = "SHIPPED"
        else:
            ship_decision = random.choice(["HELD", "IN_REVIEW"])

        rows.append({
            "experiment_id": f"EXP-{1000 + i:04d}",
            "experiment_name": name,
            "team": team,
            "primary_metric": metric,
            "planned_duration_days": planned_duration,
            "actual_duration_days": actual_duration,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "planned_split": planned_split,
            "n_control": n_control,
            "n_treatment": n_treatment,
            "n_total": n_control + n_treatment,
            "control_conversions": control_conversions,
            "treatment_conversions": treatment_conversions,
            "control_rate": rnd(obs_control_rate, 5),
            "treatment_rate": rnd(obs_treatment_rate, 5),
            "lift_pct": obs_lift_pct,
            "p_value": p_value,
            "alpha": alpha,
            "is_significant": int(is_significant),
            "srm_p_value": srm_p,
            "srm_status": srm_status,
            "peeking_risk": peeking_risk,
            "interim_looks": interim_looks,
            "duration_ratio": rnd(duration_ratio, 3),
            "practical_threshold_pct": practical_threshold_pct,
            "is_practically_significant": int(is_practically_significant),
            "overall_status": overall_status,
            "ship_decision": ship_decision,
        })

    return rows


# ─────────────────────────────────────────────────────────────
# GENERATE GUARDRAILS
# ─────────────────────────────────────────────────────────────

def generate_guardrails(experiments):
    rows = []
    guardrail_configs = {
        "p99_latency_ms": {"direction": "lower_is_better", "base": 220, "sigma": 30, "tolerance_pct": 2.0},
        "error_rate_pct":  {"direction": "lower_is_better", "base": 0.8,  "sigma": 0.15, "tolerance_pct": 5.0},
        "revenue_per_user": {"direction": "higher_is_better", "base": 4.20, "sigma": 0.60, "tolerance_pct": 1.5},
        "session_duration_s": {"direction": "higher_is_better", "base": 185, "sigma": 20, "tolerance_pct": 3.0},
    }

    for exp in experiments:
        # Each experiment gets 2-3 guardrails
        selected = random.sample(GUARDRAIL_NAMES, random.randint(2, 3))
        for gname in selected:
            cfg = guardrail_configs[gname]
            control_val = gauss(cfg["base"], cfg["sigma"] * 0.3)
            # ~15% chance of guardrail violation
            violated = random.random() < 0.15
            if violated:
                # Move in bad direction beyond tolerance
                bad_delta_pct = gauss(cfg["tolerance_pct"] * 1.8, cfg["tolerance_pct"] * 0.5,
                                      cfg["tolerance_pct"] * 1.1, cfg["tolerance_pct"] * 4.0)
                if cfg["direction"] == "lower_is_better":
                    treatment_val = control_val * (1 + bad_delta_pct / 100)
                else:
                    treatment_val = control_val * (1 - bad_delta_pct / 100)
            else:
                noise_pct = gauss(0, cfg["tolerance_pct"] * 0.3,
                                  -cfg["tolerance_pct"] * 0.9, cfg["tolerance_pct"] * 0.9)
                treatment_val = control_val * (1 + noise_pct / 100)

            delta_pct = rnd((treatment_val - control_val) / control_val * 100, 3)

            if cfg["direction"] == "lower_is_better":
                bad_direction = delta_pct > 0
                exceeded_tolerance = delta_pct > cfg["tolerance_pct"]
            else:
                bad_direction = delta_pct < 0
                exceeded_tolerance = delta_pct < -cfg["tolerance_pct"]

            status = "WARN" if (bad_direction and exceeded_tolerance) else "PASS"

            rows.append({
                "experiment_id": exp["experiment_id"],
                "experiment_name": exp["experiment_name"],
                "team": exp["team"],
                "guardrail_name": gname,
                "direction": cfg["direction"],
                "tolerance_pct": cfg["tolerance_pct"],
                "control_val": rnd(control_val, 3),
                "treatment_val": rnd(treatment_val, 3),
                "delta_pct": delta_pct,
                "bad_direction": int(bad_direction),
                "exceeded_tolerance": int(exceeded_tolerance),
                "status": status,
            })
    return rows


# ─────────────────────────────────────────────────────────────
# GENERATE EXPERIMENT CHECKS
# ─────────────────────────────────────────────────────────────

def generate_checks(experiments):
    rows = []
    for exp in experiments:
        srm_status = exp["srm_status"]
        peeking_risk = exp["peeking_risk"]
        is_sig = bool(exp["is_significant"])
        is_prac = bool(exp["is_practically_significant"])

        check_results = {
            "srm_check": (srm_status, f"SRM p={exp['srm_p_value']}; split {exp['n_control']}/{exp['n_treatment']}"),
            "pre_period_balance": ("PASS" if random.random() > 0.15 else "WARN",
                                   "Max SMD across covariates"),
            "primary_metric_significance": (
                "PASS" if is_sig else "WARN",
                f"p={exp['p_value']}; lift={exp['lift_pct']}%"
            ),
            "continuous_metric_significance": (
                "PASS" if random.random() > 0.2 else "WARN",
                "Welch t-test on revenue_per_session"
            ),
            "peeking_risk": (
                "FAIL" if peeking_risk == "HIGH" else ("WARN" if peeking_risk == "LOW" else "PASS"),
                f"duration_ratio={exp['duration_ratio']}; interim_looks={exp['interim_looks']}"
            ),
            "practical_significance": (
                "PASS" if (is_sig and is_prac) else ("WARN" if is_sig else "PASS"),
                f"observed_lift={exp['lift_pct']}%; threshold={exp['practical_threshold_pct']}%"
            ),
            "guardrail_movement": (
                "WARN" if random.random() < 0.15 else "PASS",
                "Guardrail delta vs tolerance band"
            ),
        }

        # Override: if SRM FAIL, most checks are unreliable
        if srm_status == "FAIL":
            for k in ["pre_period_balance", "primary_metric_significance",
                      "continuous_metric_significance", "practical_significance"]:
                check_results[k] = ("WARN", "Unreliable — SRM detected")

        for check_name, (status, finding) in check_results.items():
            rows.append({
                "experiment_id": exp["experiment_id"],
                "experiment_name": exp["experiment_name"],
                "team": exp["team"],
                "check_name": check_name,
                "status": status,
                "finding": finding,
            })
    return rows


# ─────────────────────────────────────────────────────────────
# GENERATE SEGMENTS
# ─────────────────────────────────────────────────────────────

def generate_segments(experiments):
    rows = []
    for exp in experiments:
        if exp["srm_status"] == "FAIL":
            continue  # No segment analysis for SRM-failed experiments
        # Pick 1-2 segment dimensions per experiment
        seg_cols = random.sample(SEGMENT_COLS, random.randint(1, 2))
        for seg_col in seg_cols:
            values = SEGMENT_VALUES[seg_col]
            for seg_val in values:
                # Segment-level sizes (sum won't be exact but that's realistic)
                seg_n_control = int(exp["n_control"] / len(values) * gauss(1.0, 0.15, 0.5, 1.8))
                seg_n_treatment = int(exp["n_treatment"] / len(values) * gauss(1.0, 0.15, 0.5, 1.8))
                seg_n_control = max(seg_n_control, 50)
                seg_n_treatment = max(seg_n_treatment, 50)

                seg_control_rate = clamp(exp["control_rate"] * gauss(1.0, 0.25, 0.3, 2.5), 0.001, 0.5)
                # Heterogeneous treatment effects
                het_multiplier = gauss(1.0, 0.3, 0.2, 2.0)
                true_seg_lift_pct = exp["lift_pct"] * het_multiplier
                seg_treatment_rate = clamp(seg_control_rate * (1 + true_seg_lift_pct / 100), 0.001, 0.5)

                seg_lift_pct = rnd((seg_treatment_rate - seg_control_rate) / seg_control_rate * 100, 2)
                seg_p = z_test_p_value(seg_control_rate, seg_treatment_rate, seg_n_control, seg_n_treatment)

                rows.append({
                    "experiment_id": exp["experiment_id"],
                    "experiment_name": exp["experiment_name"],
                    "team": exp["team"],
                    "segment_col": seg_col,
                    "segment_value": seg_val,
                    "n_control": seg_n_control,
                    "n_treatment": seg_n_treatment,
                    "control_rate": rnd(seg_control_rate, 5),
                    "treatment_rate": rnd(seg_treatment_rate, 5),
                    "lift_pct": seg_lift_pct,
                    "p_value": seg_p,
                    "is_significant": int(seg_p < 0.05),
                })
    return rows


# ─────────────────────────────────────────────────────────────
# GENERATE METRIC QUALITY
# ─────────────────────────────────────────────────────────────

def generate_metric_quality(experiments):
    rows = []
    for exp in experiments:
        # Pre-period balance: SMD across 3 covariates
        max_smd = rnd(abs(gauss(0.04, 0.04, 0.0, 0.25)), 4)
        balance_status = "WARN" if max_smd >= 0.10 else "PASS"

        # Sample size adequacy
        required_n = int(gauss(exp["n_total"] * 0.85, exp["n_total"] * 0.2, 1000, exp["n_total"] * 2))
        sample_adequacy_pct = rnd(exp["n_total"] / required_n * 100, 1)
        min_sample_met = int(exp["n_total"] >= required_n)

        # Novelty effect: elevated early lift that decays
        novelty_detected = int(random.random() < 0.18)

        # Power at observed effect
        obs_lift_abs = abs(exp["lift_pct"]) / 100 * exp["control_rate"]
        if obs_lift_abs > 0:
            # Approximate power
            z_alpha = 1.6449  # one-sided 0.05
            se = math.sqrt(exp["control_rate"] * (1 - exp["control_rate"]) * 2 / (exp["n_total"] / 2))
            z_power = obs_lift_abs / se - z_alpha if se > 0 else 0
            power = rnd(clamp(norm_cdf_approx(z_power), 0.05, 0.999), 3)
        else:
            power = rnd(gauss(0.5, 0.15, 0.05, 0.95), 3)

        # Data freshness lag (hours between event and availability in pipeline)
        data_lag_hours = rnd(gauss(3.2, 1.8, 0.5, 12.0), 1)

        rows.append({
            "experiment_id": exp["experiment_id"],
            "experiment_name": exp["experiment_name"],
            "team": exp["team"],
            "max_smd_covariate": max_smd,
            "pre_period_balance_status": balance_status,
            "min_sample_size_required": required_n,
            "actual_sample_size": exp["n_total"],
            "sample_adequacy_pct": sample_adequacy_pct,
            "min_sample_met": min_sample_met,
            "novelty_effect_detected": novelty_detected,
            "power_at_observed_effect": power,
            "data_lag_hours": data_lag_hours,
            "srm_status": exp["srm_status"],
            "overall_status": exp["overall_status"],
        })
    return rows


# ─────────────────────────────────────────────────────────────
# WRITE CSVs
# ─────────────────────────────────────────────────────────────

def write_csv(path, rows):
    if not rows:
        print(f"  [WARN] No rows for {path.name}")
        return
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Written: {path.name}  ({len(rows)} rows)")


def main():
    print("MetaSignal BI Extract Generator")
    print("=" * 40)

    experiments = generate_experiments()
    guardrails = generate_guardrails(experiments)
    checks = generate_checks(experiments)
    segments = generate_segments(experiments)
    metric_quality = generate_metric_quality(experiments)

    write_csv(OUT_DIR / "experiments.csv", experiments)
    write_csv(OUT_DIR / "guardrails.csv", guardrails)
    write_csv(OUT_DIR / "experiment_checks.csv", checks)
    write_csv(OUT_DIR / "segments.csv", segments)
    write_csv(OUT_DIR / "metric_quality.csv", metric_quality)

    print()
    print("Summary:")
    print(f"  Experiments:       {len(experiments)}")
    print(f"  Guardrail rows:    {len(guardrails)}")
    print(f"  Check rows:        {len(checks)}")
    print(f"  Segment rows:      {len(segments)}")
    print(f"  Metric quality:    {len(metric_quality)}")
    print()
    srm_fails = sum(1 for e in experiments if e["srm_status"] == "FAIL")
    shipped = sum(1 for e in experiments if e["ship_decision"] == "SHIPPED")
    guardrail_warns = sum(1 for g in guardrails if g["status"] == "WARN")
    print(f"  SRM failures:      {srm_fails} / {len(experiments)}")
    print(f"  Shipped:           {shipped} / {len(experiments)}")
    print(f"  Guardrail WARNs:   {guardrail_warns} / {len(guardrails)}")
    print()
    print(f"Output directory: {OUT_DIR.resolve()}")
    print("Done.")


if __name__ == "__main__":
    main()
