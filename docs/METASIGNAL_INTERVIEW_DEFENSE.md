# MetaSignal Interview Defense

Use this project to demonstrate experimentation systems thinking, not just statistical vocabulary.

## 1. What is MetaSignal?

A production-simulated experimentation intelligence platform that makes metrics explicit, experiment reads statistically disciplined, and product decisions auditable.

## 2. Why is this not just an A/B testing notebook?

Because it has registry, quality gates, assignment checks, CUPED validation, guardrail decisioning, anomaly evidence, API endpoints, and repeatable artifacts.

## 3. Why does denominator governance matter?

The same metric name can produce different business conclusions if teams use different denominators. MetaSignal makes that denominator explicit and detects conflicts.

## 4. Why use SRM?

SRM catches assignment or instrumentation problems before interpreting treatment effects. A broken split can invalidate the experiment.

## 5. Why use CUPED?

CUPED removes predictable pre-period variance from the post-period outcome, increasing sensitivity without changing assignment.

## 6. How did you validate CUPED?

The project runs 1000 synthetic A/A tests and checks false-positive rate plus p-value uniformity against Uniform(0,1).

## 7. Why are guardrails evaluated before primary metric decisions?

Because product harm is asymmetric. A positive primary lift should not ship if a pre-defined harm metric breaches tolerance.

## 8. What is right-censoring here?

Delayed metrics like refunds or returns may be immature at readout time, so MetaSignal marks them as right-censored rather than treating them as final.

## 9. What does anomaly detection prove?

It shows the system can distinguish metric movement from expected seasonality/noise using a DOW-adjusted rolling baseline.

## 10. What is production-simulated versus production?

Production-simulated means the system handles realistic operational failure modes and produces logs/artifacts, but it does not claim real users or live company deployment.

## 11. What would you improve next?

Streaming early-warning, stronger anomaly backtesting, CI, a small dashboard, and richer experiment scenario coverage.
