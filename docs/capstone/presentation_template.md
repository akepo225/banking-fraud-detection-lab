---
title: Capstone Presentation Template
linked_modules: docs/capstone/alpine_crest_brief.md, docs/capstone/novabank_brief.md, notebooks/09_capstone/
---

# Capstone Presentation Template

<!-- HITL-REVIEW-REQUIRED -->

This is educational material for the Banking Fraud Detection Lab. It is not legal,
compliance, audit, investment, regulatory, or professional advice. The repository is
pre-publication; v0.9 is a beta review point, not a shipped release.

This template gives **Alpine Crest Private Bank** and **NovaBank Digital** capstone
submissions a consistent structure for communicating final findings. Fill in each section
for the chosen track, then self-assess against the [evaluation rubric](rubric.md). A model
**should not be judged by headline accuracy** — lead with the **Detection pattern** and the
alert-aware decision, and present any graph evidence as investigative support only.

## 1. Scenario context and detection patterns

State which **Fraud detection track** and institution the submission covers (**Alpine Crest
Private Bank** for private banking, **NovaBank Digital** for digital banking). Summarise the
business context from the brief and name the **Detection patterns** investigated:

- **Alpine Crest Private Bank**: `pb_high_value_movement`, `pb_transaction_fraud`,
  `circular_funds_movement`.
- **NovaBank Digital**: `digital_scam_to_mule`, `new_beneficiary_payment`, `mule_ring`.

## 2. Data and SQL-derived features

Describe the capstone substrate and the SQL feature extraction
([12_capstone_private_banking.sql](../../sql/examples/12_capstone_private_banking.sql) or
[13_capstone_digital_banking.sql](../../sql/examples/13_capstone_digital_banking.sql)).
State which **Banking relationship** / **Client** (and, for the digital track, **User**)
context each feature carries and which **Detection pattern** it serves.

## 3. Scoring approach and alert-aware metrics

Report the scoring rule and the alert-aware metrics from `evaluate_alert_scores` —
precision, recall, PR-AUC, alert volume, and false-positive concentration. State explicitly
that headline accuracy is not used and why.

## 4. Capacity-aware threshold decision

Present the threshold from `recommend_lowest_cost_threshold` and its rationale as a
capacity-aware (reviewer-throughput) decision, not a pure-recall one.

## 5. Per-alert explanation

Give a per-alert "why" from the interpretability surface for one or two representative
alerts, linking the explanation back to the **Detection pattern** signal.

## 6. Graph evidence as investigative support only

If the submission covers `circular_funds_movement` (Alpine Crest) or `mule_ring`
(NovaBank), present the graph evidence from the
[capstone synthesis notebook](../../notebooks/09_capstone/capstone_synthesis.ipynb) as
investigative support that contextualises the tabular score — not as a replacement for it.

## 7. Alert lifecycle and reviewer actions

Trace the chosen alerts through the synthesis notebook's `decide_alerts` /
`inspect_alert_queue` / `record_reviewer_action` flow, and state what a reviewer would do
with the resulting queue.

## 8. Governance limitations and monitoring

Summarise the governance memo (`build_model_documentation`, `build_monitoring_checklist`)
and state the model's limitations honestly: the capstone is synthetic, it does not
reconstruct any real event or institution, and no single metric is the full operational
truth.

## 9. Key takeaways

Three to five takeaways: the detection signal that mattered most, the alert-aware decision
that follows, and the limitation a reviewer must keep in mind.

## Limitations

- The capstone is synthetic; it does not reconstruct any real event or institution.
- This template structures communication only; it does not grade the submission. Use the
  [evaluation rubric](rubric.md) for assessment.
- The `tiny` scale is for the smoke-test path; larger scales are generated locally and
  stay out of git.

## Human Review

- [ ] Confirm the section skeleton works for both tracks without track-specific gaps.
- [ ] Confirm the alert-aware framing is preserved and graph evidence stays investigative.
- [ ] Confirm the glossary (Client / User / Banking relationship; Alpine Crest Private
      Bank; NovaBank Digital) is respected throughout.
