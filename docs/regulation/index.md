# Regulatory Sources

Regulatory notes explain how public regulatory texts shape analytics questions, controls,
documentation, explainability, alert handling, and governance.

They are educational notes for the **Banking Fraud Detection Lab** curriculum and are not legal or compliance advice.

## Source Policy

- Link to official sources.
- Quote only short excerpts when necessary.
- Summarize learning implications in original wording.
- Connect sources to modules and case patterns.

## By Learning Use

Each source note is tagged with one or more `learning_use` categories in its front matter so
learners can find the right reference for a given task. A note may appear under several
categories. The six categories are:

- **Analytics Question** — shaping what makes a transaction, account, or network pattern investigable.
- **Control** — describing controls and evidence a learner can derive from observable signals.
- **Documentation** — keeping repeatable records of inputs, thresholds, limitations, and rationale.
- **Explainability** — connecting a score or alert to data signals and case notes for a reviewer.
- **Alert Handling** — working with alert lifecycle, capacity, and noisy labels.
- **Governance** — stakeholder review, threshold tradeoffs, and model-risk habits.

### Analytics Question

Sources that help frame what is investigable in synthetic data.

- [Swiss AMLA, AMLO, and FINMA AML anchors](source_notes/swiss-amla-amlo-finma.md) — relationship-manager responsibility, counterparty novelty, cross-border movement.
- [UK APP scam reimbursement guidance](source_notes/uk-app-scam-payment-guidance.md) — payment context: beneficiary novelty, account age, payment velocity, onward movement.
- [FATF typologies for money-mule networks](source_notes/fatf-money-mule-typologies.md) — multi-account and network movement patterns.

### Control

Sources that describe controls and observable control-failure evidence.

- [Swiss AMLA, AMLO, and FINMA AML anchors](source_notes/swiss-amla-amlo-finma.md)
- [UK APP scam reimbursement guidance](source_notes/uk-app-scam-payment-guidance.md)
- [FATF typologies for money-mule networks](source_notes/fatf-money-mule-typologies.md)

### Documentation

Sources that shape how learners document inputs, thresholds, limitations, and rationale.

- [Swiss AMLA, AMLO, and FINMA AML anchors](source_notes/swiss-amla-amlo-finma.md) — separating analytics evidence from legal conclusions.
- [Model-risk governance for fraud scoring](source_notes/model-risk-governance.md) — intended use, input data, threshold choice, known limitations, monitoring.
- [Independent model validation for fraud scoring](source_notes/model-validation.md) — effective challenge and the independent-reviewer stance.
- [Model documentation for fraud scoring](source_notes/model-documentation.md) — purpose, data lineage, assumptions, limitations, monitoring needs.

### Explainability

Sources that help connect a score to data signals and case notes.

- [Swiss AMLA, AMLO, and FINMA AML anchors](source_notes/swiss-amla-amlo-finma.md)
- [UK APP scam reimbursement guidance](source_notes/uk-app-scam-payment-guidance.md)
- [Model-risk governance for fraud scoring](source_notes/model-risk-governance.md)
- [Model explainability for fraud scoring](source_notes/model-explainability.md) — per-alert feature importance and partial-dependence tied to Detection patterns.

### Alert Handling

Sources relevant to alert lifecycle, investigation capacity, and noisy labels.

- [Swiss AMLA, AMLO, and FINMA AML anchors](source_notes/swiss-amla-amlo-finma.md)
- [UK APP scam reimbursement guidance](source_notes/uk-app-scam-payment-guidance.md)
- [Model-risk governance for fraud scoring](source_notes/model-risk-governance.md)
- [Ongoing model monitoring for fraud scoring](source_notes/model-monitoring.md) — drift, stability, false-positive concentration, and data quality.
- [Production-pattern monitoring](source_notes/production-pattern-monitoring.md) — batch scoring, alert queues with alert aging, drift checks, reviewer actions, and audit trails across both tracks.

### Governance

Sources that frame stakeholder review, threshold tradeoffs, and model-risk habits.

- [UK APP scam reimbursement guidance](source_notes/uk-app-scam-payment-guidance.md)
- [FATF typologies for money-mule networks](source_notes/fatf-money-mule-typologies.md)
- [Model-risk governance for fraud scoring](source_notes/model-risk-governance.md)
- [Model explainability for fraud scoring](source_notes/model-explainability.md)
- [Independent model validation for fraud scoring](source_notes/model-validation.md)
- [Model documentation for fraud scoring](source_notes/model-documentation.md)
- [Ongoing model monitoring for fraud scoring](source_notes/model-monitoring.md)
- [Production-pattern monitoring](source_notes/production-pattern-monitoring.md) — batch scoring, alert queues with alert aging, drift checks, reviewer actions, and audit trails.

## By Source Family

These notes are in draft HITL status. Human review is required before they are treated as
publication-ready educational material.

- **Swiss AMLA, AMLO, FINMA, and MROS-related sources** — [Swiss AMLA, AMLO, and FINMA AML anchors](source_notes/swiss-amla-amlo-finma.md).
- **APP scam or payment guidance from EU or UK sources** — [UK APP scam reimbursement guidance](source_notes/uk-app-scam-payment-guidance.md).
- **FATF typologies** — [FATF typologies for money-mule networks](source_notes/fatf-money-mule-typologies.md).
- **Model-risk, explainability, and governance references** — [Model-risk governance for fraud scoring](source_notes/model-risk-governance.md), [Ongoing model monitoring for fraud scoring](source_notes/model-monitoring.md), [Production-pattern monitoring](source_notes/production-pattern-monitoring.md).
