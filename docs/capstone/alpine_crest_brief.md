---
title: Alpine Crest Private Bank Capstone Brief
track: Private-banking fraud detection
institution: Alpine Crest Private Bank
detection_patterns: pb_high_value_movement, pb_transaction_fraud, circular_funds_movement
capstone_seed: 42
capstone_scale: tiny
linked_modules: notebooks/09_capstone/, sql/examples/capstone_private_banking.sql
---

# Alpine Crest Private Bank Capstone Brief

<!-- HITL-REVIEW-REQUIRED -->

This is educational material for the Banking Fraud Detection Lab. It is not legal,
compliance, audit, investment, regulatory, or professional advice. The repository is
pre-publication; v0.9 is a beta review point, not a shipped release.

## Business Context

You have joined the **Alpine Crest Private Bank** transaction-monitoring review team.
**Alpine Crest Private Bank** is the fictional private bank used throughout the
private-banking **Fraud detection track**. Your team reviews high-value debit activity
across **Banking relationship** containers, where a single relationship can hold multiple
accounts, portfolios, and counterparties managed under a relationship manager.

Wealth-management payments are legitimately large, so a high transaction amount is rarely
enough on its own. The investigation has to weigh the movement against the **Client's**
historical profile, the **Banking relationship** AUM tier, the counterparty history, and
the relationship-manager context. The same context also produces legitimate high-value
movements that look alarming in isolation — repatriations, routine FX, and expected fees —
which are the false-positive pressure on any scoring rule.

## Analytic Task

Investigate the capstone dataset and surface the transaction-monitoring signals behind
three private-banking **Detection patterns**:

- `pb_high_value_movement` — unusual high-value transactions within a private-banking
  relationship that deviate from the **Client's** historical profile.
- `pb_transaction_fraud` — injected transaction-fraud scenarios with structural fraud
  signals detectable through feature engineering and scoring rules.
- `circular_funds_movement` — a graph-derived pattern where funds cycle among related
  Partner, **Client**, and **Banking relationship** entities through layered accounts and
  counterparties.

Generate the capstone substrate, load it into SQLite, extract relationship / account /
counterparty / relationship-manager / velocity features, fit a transparent scoring rule,
and report alert-aware metrics with a capacity-aware threshold and a per-alert
explanation. Use the graph layer only as investigative support for the
`circular_funds_movement` pattern — it does not replace the tabular score.

## Capstone Dataset

The dataset is deterministic. Generate it from a clean checkout with the fixed capstone
seed and scale:

```bash
uv run python -m banking_fraud_lab.capstone --track private_banking --seed 42 --scale tiny --learner-facing --output data/capstone
```

- Seed: `42` (`CAPSTONE_SEED`).
- Scale: `tiny` (`CAPSTONE_SCALE`) — the committed smoke-test scale.
- Scenario prevalence: `0.2` — roughly one in five private-banking transactions carries
  the `pb_transaction_fraud` scenario label in the grading export.
- The learner-facing export **excludes** the protected `protected_scenario_answer_keys`
  table; the grading export includes it. Investigation work must not be solved by
  inspecting protected labels.

## Expected Outcome

- SQL feature extraction tying rows back to **Banking relationship**, **Client**, and
  Alert lifecycle lineage.
- A fitted scoring rule with precision / recall, PR-AUC, alert volume, and cost tradeoffs
  reported through `evaluate_alert_scores`, avoiding headline accuracy claims.
- A capacity-aware threshold from `recommend_lowest_cost_threshold` with its rationale.
- A per-alert "why" explanation from the interpretability surface.
- Graph evidence for `circular_funds_movement` presented as investigative support only.

## Limitations

- The capstone is synthetic; it does not reconstruct any real event or institution.
- Confirmed-fraud labels in the protected answer key are imperfect by design (the digital
  track adds label noise); avoid treating any single metric as the ground truth.
- The `tiny` scale is for the smoke-test path; larger scales are generated locally and
  stay out of git.

## Human Review

- [ ] Confirm the brief framing and Detection pattern references match the v0.9 scope.
- [ ] Confirm the glossary (Client / User / Banking relationship; Alpine Crest Private
      Bank) is respected throughout.
