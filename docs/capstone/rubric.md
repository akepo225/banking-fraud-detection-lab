---
title: Capstone Evaluation Rubric
linked_modules: docs/capstone/alpine_crest_brief.md, docs/capstone/novabank_brief.md, sql/examples/12_capstone_private_banking.sql, sql/examples/13_capstone_digital_banking.sql, notebooks/09_capstone/
---

# Capstone Evaluation Rubric

<!-- HITL-REVIEW-REQUIRED -->

This is educational material for the Banking Fraud Detection Lab. It is not legal,
compliance, audit, investment, regulatory, or professional advice. The repository is
pre-publication; v0.9 is a beta review point, not a shipped release.

This rubric is a self-, peer-, and human assessment guide. It is **not** an automated
grader or hosted platform: a reviewer scores a submission against the dimensions below, and
a learner self-assesses their own work. It grades the **actual** v0.9 capstone deliverables
(the scenario briefs, the two SQL feature extractions, the two scoring notebooks, and the
synthesis / governance notebook) — not aspirational artifacts that do not exist.

Each dimension lists three observable quality levels: **Strong**, **Adequate**, and
**Needs work**. A submission does not have to be "Strong" everywhere to pass; reviewers
weigh the dimensions together and use the level descriptors to justify a judgement.

## How to use this rubric

1. Confirm the submission follows the [Alpine Crest Private Bank](alpine_crest_brief.md)
   or [NovaBank Digital](novabank_brief.md) brief end-to-end.
2. Read each dimension, find the level that best matches the submission, and note the
   observable evidence (a cell output, a SQL CTE, a memo paragraph).
3. Score on the alert-aware surfaces below. A model **should not be judged by headline
   accuracy** — precision, recall, PR-AUC, false-positive concentration, and a
   capacity-aware threshold are the operational signals that matter.
4. Write the findings into the [presentation template](presentation_template.md).

## 1. SQL quality

Grades the capstone SQL feature extraction for the chosen track —
[12_capstone_private_banking.sql](../../sql/examples/12_capstone_private_banking.sql) for
**Alpine Crest Private Bank**, [13_capstone_digital_banking.sql](../../sql/examples/13_capstone_digital_banking.sql)
for **NovaBank Digital**. The query must tie rows back to **Banking relationship**,
**Client** (and, for the digital track, **User**), and Alert lifecycle lineage.

- **Strong.** The query uses a layered CTE pipeline (e.g. the private-banking
  `private_accounts` / `transaction_context` / `relationship_velocity` flow, or the
  digital `digital_accounts` / `transaction_session` flow), applies window functions for
  velocity / pass-through context, filters to the correct institution name, and every
  derived column traces to a **Detection pattern** signal.
- **Adequate.** The query joins the right tables and returns usable features, but the
  lineage to **Banking relationship** / Alert lifecycle is partial, or velocity is computed
  without a window function.
- **Needs work.** The query is a flat `SELECT` over one table, mixes institutions, or
  drops the **Banking relationship** / **Client** context entirely.

## 2. Fraud-domain reasoning (Detection pattern linkage)

Grades whether the submission links its features and findings to the private-banking or
digital-banking **Detection patterns** named in the brief.

- **Strong.** Each scored feature is tied to a named pattern id —
  `pb_high_value_movement`, `pb_transaction_fraud`, `circular_funds_movement` for
  **Alpine Crest Private Bank**; `digital_scam_to_mule`, `new_beneficiary_payment`,
  `mule_ring` for **NovaBank Digital** — and the submission explains *why* a feature is a
  signal for that pattern (e.g. early-life mule account age signals `digital_scam_to_mule`).
- **Adequate.** The patterns are named, but the feature-to-pattern justification is thin
  or lists patterns without explaining the structural signal.
- **Needs work.** The submission treats the score as a generic fraud detector and never
  connects a feature to a **Detection pattern**.

## 3. Model evaluation (alert-aware, NOT headline accuracy)

Grades the scoring notebook for the track —
[alpine_crest_capstone_scoring.ipynb](../../notebooks/09_capstone/alpine_crest_capstone_scoring.ipynb)
or [novabank_capstone_scoring.ipynb](../../notebooks/09_capstone/novabank_capstone_scoring.ipynb).
A model **should not be judged by headline accuracy**.

- **Strong.** The submission reports precision, recall, PR-AUC, and false-positive
  concentration through `evaluate_alert_scores`, names the alert volume / cost tradeoff,
  and explicitly states that headline accuracy is the wrong lens for an alert-operations
  setting.
- **Adequate.** Some alert-aware metrics are reported, but the submission still leans on a
  single score, or PR-AUC / false-positive concentration is missing.
- **Needs work.** The submission reports accuracy (or accuracy alone) and never surfaces
  the alert-aware surfaces.

## 4. Alert interpretation / Alert lifecycle

Grades the capacity-aware threshold decision, the per-alert "why" explanation, and the
reviewer-action flow into the [capstone synthesis notebook](../../notebooks/09_capstone/capstone_synthesis.ipynb).

- **Strong.** The submission selects a threshold through
  `recommend_lowest_cost_threshold`, justifies it as a capacity-aware (not pure-recall)
  choice, gives a per-alert explanation from the interpretability surface, and traces the
  chosen alerts through the synthesis notebook's `decide_alerts` / `inspect_alert_queue` /
  `record_reviewer_action` flow.
- **Adequate.** A threshold is chosen and explained, and some alerts are interpreted, but
  the link into the synthesis alert queue is missing or the threshold rationale ignores
  reviewer capacity.
- **Needs work.** A fixed threshold is applied with no rationale and no per-alert
  explanation, and the Alert lifecycle is not traced.

## 5. Governance / limitations

Grades the governance memo and limitations honesty produced in the
[capstone synthesis notebook](../../notebooks/09_capstone/capstone_synthesis.ipynb)
(`build_model_documentation`, `build_monitoring_checklist`).

- **Strong.** The submission ships a governance memo that names the model's purpose, data,
  and limitations, a monitoring checklist with concrete drift / quality checks, and states
  honestly that the capstone is synthetic and does not reconstruct any real event or
  institution.
- **Adequate.** A governance artefact exists, but the monitoring checks are generic, or a
  limitation is overstated (e.g. claiming operational readiness).
- **Needs work.** No governance artefact, or limitations are absent / contradict the
  synthetic-data boundary.

## 6. Communication

Grades how findings are communicated using the [presentation template](presentation_template.md).

- **Strong.** The submission follows the template structure, leads with the detection
  pattern and the alert-aware decision, presents graph evidence (`circular_funds_movement`
  or `mule_ring`) as investigative support only, and avoids headline-accuracy claims.
- **Adequate.** The template is followed, but graph evidence is presented as proof rather
  than support, or a headline-accuracy framing slips in.
- **Needs work.** Findings are unstructured, or the communication overclaims what the
  score proves.

## Limitations

- The capstone is synthetic; it does not reconstruct any real event or institution.
- This rubric is a human assessment guide, not an automated grader. Reviewer judgement is
  required, and any single level descriptor is evidence, not the full operational truth.
- The `tiny` scale is for the smoke-test path; larger scales are generated locally and
  stay out of git.

## Human Review

- [ ] Confirm the six dimensions and their level descriptors match the v0.9 scope.
- [ ] Confirm the rubric grades only the real capstone deliverables (briefs, SQL, scoring
      notebooks, synthesis notebook) and does not reference aspirational artifacts.
- [ ] Confirm the glossary (Client / User / Banking relationship; Alpine Crest Private
      Bank; NovaBank Digital) is respected throughout.
