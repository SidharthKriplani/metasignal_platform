from __future__ import annotations

import json
from pathlib import Path


JSON_OUT = Path("outputs/reports/metasignal_interview_defense.json")
MD_OUT = Path("docs/METASIGNAL_INTERVIEW_DEFENSE.md")


QUESTIONS = [
    {
        "question": "What is MetaSignal?",
        "answer": "A production-simulated experimentation intelligence platform that makes metrics explicit, experiment reads statistically disciplined, and product decisions auditable.",
    },
    {
        "question": "Why is this not just an A/B testing notebook?",
        "answer": "Because it has registry, quality gates, assignment checks, CUPED validation, guardrail decisioning, anomaly evidence, API endpoints, and repeatable artifacts.",
    },
    {
        "question": "Why does denominator governance matter?",
        "answer": "The same metric name can produce different business conclusions if teams use different denominators. MetaSignal makes that denominator explicit and detects conflicts.",
    },
    {
        "question": "Why use SRM?",
        "answer": "SRM catches assignment or instrumentation problems before interpreting treatment effects. A broken split can invalidate the experiment.",
    },
    {
        "question": "Why use CUPED?",
        "answer": "CUPED removes predictable pre-period variance from the post-period outcome, increasing sensitivity without changing assignment.",
    },
    {
        "question": "How did you validate CUPED?",
        "answer": "The project runs 1000 synthetic A/A tests and checks false-positive rate plus p-value uniformity against Uniform(0,1).",
    },
    {
        "question": "Why are guardrails evaluated before primary metric decisions?",
        "answer": "Because product harm is asymmetric. A positive primary lift should not ship if a pre-defined harm metric breaches tolerance.",
    },
    {
        "question": "What is right-censoring here?",
        "answer": "Delayed metrics like refunds or returns may be immature at readout time, so MetaSignal marks them as right-censored rather than treating them as final.",
    },
    {
        "question": "What does anomaly detection prove?",
        "answer": "It shows the system can distinguish metric movement from expected seasonality/noise using a DOW-adjusted rolling baseline.",
    },
    {
        "question": "What is production-simulated versus production?",
        "answer": "Production-simulated means the system handles realistic operational failure modes and produces logs/artifacts, but it does not claim real users or live company deployment.",
    },
    {
        "question": "What would you improve next?",
        "answer": "Streaming early-warning, stronger anomaly backtesting, CI, a small dashboard, and richer experiment scenario coverage.",
    },
]


def main() -> None:
    payload = {
        "artifact": "metasignal_interview_defense",
        "defense_positioning": "Use this project to demonstrate experimentation systems thinking, not just statistical vocabulary.",
        "question_count": len(QUESTIONS),
        "questions": QUESTIONS,
    }

    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    MD_OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# MetaSignal Interview Defense",
        "",
        payload["defense_positioning"],
        "",
    ]

    for i, qa in enumerate(QUESTIONS, start=1):
        lines.extend([
            f"## {i}. {qa['question']}",
            "",
            qa["answer"],
            "",
        ])

    MD_OUT.write_text("\n".join(lines), encoding="utf-8")

    print("interview_defense_v0 complete")
    print(f"question_count: {len(QUESTIONS)}")
    print(f"wrote {JSON_OUT}")
    print(f"wrote {MD_OUT}")


if __name__ == "__main__":
    main()
