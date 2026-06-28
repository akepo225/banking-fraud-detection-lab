---
title: NovaBank Digital Capstone Brief
track: Digital-banking fraud detection
institution: NovaBank Digital
detection_patterns: digital_scam_to_mule, new_beneficiary_payment, mule_ring
capstone_seed: 42
capstone_scale: tiny
linked_modules: notebooks/09_capstone/, sql/examples/13_capstone_digital_banking.sql
---

# NovaBank Digital Capstone Brief

<!-- HITL-REVIEW-REQUIRED -->

This is educational material for the Banking Fraud Detection Lab. It is not legal,
compliance, audit, investment, regulatory, or professional advice. The repository is
pre-publication; v0.9 is a beta review point, not a shipped release.

## Business Context

You have joined the **NovaBank Digital** fraud-operations team. **NovaBank Digital** is
the fictional online bank used throughout the digital-banking **Fraud detection track**.
Your team reviews authorised payments and session activity across app and e-banking
channels, where a **User** is the digital login identity that authenticates a session and
acts through it, distinct from the **Client** who is the legal party that holds the
**Banking relationship**.

Digital payments move fast and the channel produces rich telemetry — device fingerprints,
network risk, beneficiary-change events, session velocity, and account age — but it also
produces noisy triage outcomes. A confirmed-fraud case may close as a false positive, and
a legitimate payment may briefly look like an authorised scam. That label noise is the
analytic pressure on any scoring rule.

## Analytic Task

Investigate the capstone dataset and surface the transaction-monitoring signals behind
three digital-banking **Detection patterns**:

- `digital_scam_to_mule` — a scam victim authorises a payment that moves into a mule or
  rented account and is rapidly passed onward, observed through beneficiary-change events,
  early-life mule accounts, shared-device signals, and pass-through velocity.
- `new_beneficiary_payment` — a payment to a recently added beneficiary, often signalling
  account takeover or authorised scam activity.
- `mule_ring` — a graph-derived pattern where several mule or rented accounts move funds
  through shared beneficiaries and devices, forming a connected ring.

Generate the capstone substrate, load it into SQLite, extract session / device /
beneficiary / pass-through / account-age features, fit a transparent scoring rule, and
report alert-aware metrics with a capacity-aware threshold and a per-alert explanation.
Use the graph layer only as investigative support for the `mule_ring` pattern — it does
not replace the tabular score.

## Capstone Dataset

The dataset is deterministic. Generate it from a clean checkout with the fixed capstone
seed and scale:

```bash
uv run python -m banking_fraud_lab.capstone --track digital_banking --seed 42 --scale tiny --learner-facing --output data/capstone/digital_banking
```

- Seed: `42` (`CAPSTONE_SEED`).
- Scale: `tiny` (`CAPSTONE_SCALE`) — the committed smoke-test scale.
- Scenario prevalence: `0.5` — roughly half of **NovaBank Digital** accounts participate
  in each scenario family in the grading export.
- Noisy outcome rate: `0.3` — a bounded share of the v0.4 scenario cases receive a triage
  outcome that deliberately disagrees with the true protected label.
- The learner-facing export **excludes** the protected `protected_scenario_answer_keys`
  table; the grading export includes it. Investigation work must not be solved by
  inspecting protected labels.

## Expected Outcome

- SQL feature extraction
  ([13_capstone_digital_banking.sql](../../sql/examples/13_capstone_digital_banking.sql))
  tying rows back to **Banking relationship**, **Client** or **User**, and Alert
  lifecycle lineage.
- A fitted scoring rule with precision / recall, PR-AUC, alert volume, and cost tradeoffs
  reported through `evaluate_alert_scores`, avoiding headline accuracy claims.
- A capacity-aware threshold from `recommend_lowest_cost_threshold` with its rationale.
- A per-alert "why" explanation from the interpretability surface.
- Graph evidence for `mule_ring` presented as investigative support only.

## Limitations

- The capstone is synthetic; it does not reconstruct any real event or institution.
- The protected answer key is the true reference signal for grading; noisy triage
  outcomes may deliberately disagree with it. Avoid treating any single operational
  outcome or metric as the full ground truth.
- The `tiny` scale is for the smoke-test path; larger scales are generated locally and
  stay out of git.

## Human Review

- [ ] Confirm the brief framing and Detection pattern references match the v0.9 scope.
- [ ] Confirm the glossary (Client / User / Banking relationship; NovaBank Digital) is
      respected throughout.
