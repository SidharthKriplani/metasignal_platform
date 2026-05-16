# MetaSignal — Executive Experiment Readout Template

**Use this template** for presenting completed experiment results to senior stakeholders.
Fill in the bracketed fields. Keep it to one page. The audience is VP/Director level —
they need a ship/hold recommendation with enough context to ask one good question,
not a statistics lecture.

---

## Experiment Readout: [EXPERIMENT NAME]

**Date:** [DD MMM YYYY]  
**Presenter:** [Name, Role]  
**Team:** [Team Name]  
**Platform Audit Status:** [PASS / WARN / FAIL — from MetaSignal]

---

### What We Tested

[One sentence. What changed? Which surface? What user population?]

> Example: "We tested moving the checkout CTA from grey to blue on the mobile checkout
> page for all new users who had added at least one item to cart."

---

### The Hypothesis

[One sentence. What did we expect and why?]

> Example: "We expected conversion rate to increase because blue CTAs have consistently
> outperformed grey in prior brand studies and aligns with our design system primary action colour."

---

### Result Summary

| Metric | Control | Treatment | Lift | Significant? |
|--------|---------|-----------|------|-------------|
| [Primary metric] | [X%] | [X%] | [+X%] | [Yes / No] |
| [Guardrail 1] | [val] | [val] | [Δ%] | [PASS / WARN] |
| [Guardrail 2] | [val] | [val] | [Δ%] | [PASS / WARN] |

**Statistical validity:** p = [X.XXX] (threshold α = 0.05)  
**Practical significance:** Lift of [X%] [exceeds / does not exceed] our [1%] threshold  
**Experiment health score:** [0–100] — [Clean / Minor Issues / Multiple Warnings / Invalidated]

---

### Flags (if any)

> Leave blank if MetaSignal audit returned PASS with no warnings.

- **SRM:** [PASS / FAIL — if FAIL, stop here, do not recommend ship]
- **Peeking risk:** [NONE / LOW / HIGH — if HIGH, note duration and interim looks]
- **Guardrail:** [List any WARN guardrails with delta and tolerance]
- **Novelty effect:** [Detected / Not detected]

---

### Recommendation

☐ **Ship** — Significant lift, practical threshold met, no blocking flags  
☐ **Hold** — Significant but not practically meaningful; revisit hypothesis  
☐ **No ship** — SRM failure / guardrail regression / not significant  
☐ **Extend** — Borderline power; extend duration by [X] days  

**Recommended by:** [Name]  
**Decision required from:** [VP / Director / Product Lead]

---

### What Happens Next

[One sentence. What's the action after this meeting?]

> Example: "Engineering will ramp treatment to 100% by [date] pending sign-off today."
> Example: "We will extend the experiment by 7 days to reach adequate power before re-reviewing."
> Example: "Experiment will be invalidated; assignment pipeline audit scheduled for [date]."

---

*Prepared using MetaSignal Experimentation Platform*  
*Full audit report available at: [link to MetaSignal audit JSON / dashboard tab]*
