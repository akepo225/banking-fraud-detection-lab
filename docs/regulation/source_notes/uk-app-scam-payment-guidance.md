---
title: "UK APP scam reimbursement guidance"
status: draft-hitl
hitl_review_required: true
source_families:
  - app_scam_payment
pattern_ids:
  - new_beneficiary_payment
  - session_payment_velocity
learning_use:
  - analytics_question
  - control
  - explainability
  - alert_handling
  - governance
track: digital-banking fraud detection
primary_official_sources:
  - https://www.psr.org.uk/publications/policy-statements/ps255-app-scams-reimbursement-requirement/
  - https://www.psr.org.uk/our-work/app-scams/
linked_modules:
  - notebooks/02_digital_scam_to_mule/novabank_scam_to_mule_baseline.ipynb
  - notebooks/03_alert_governance/alert_governance_memo.ipynb
  - notebooks/05_digital_session_and_payment_fraud/novabank_feature_engineering.ipynb
  - notebooks/05_digital_session_and_payment_fraud/novabank_supervised_baseline.ipynb
  - notebooks/05_digital_session_and_payment_fraud/novabank_alert_triage.ipynb
---

# UK APP Scam Reimbursement Guidance

<!-- HITL-REVIEW-REQUIRED -->

Educational use only: this source note supports fraud-detection curriculum design and is not legal or compliance advice.

## Source Scope

This note links to Payment Systems Regulator material on authorised push payment scam
reimbursement and APP scams. It does not restate operational instructions from the UK regime;
instead, it extracts analytics lessons that help learners reason about scam-to-mule flows in
synthetic NovaBank Digital data. No direct quotations are needed for the v0.1 exercises.

## Learning Prompt

When building `new_beneficiary_payment` and `session_payment_velocity` features in the
NovaBank Digital notebooks, use this source to design scam-detection questions around payment
context (beneficiary novelty, account age, payment velocity, onward movement) rather than
authentication alone. Consider how reimbursement policy shapes the analytics question, the
controls you would describe, the quality of the explanation an investigator needs, how alerts
are triaged under capacity limits, and the governance tradeoff between catching mules and
overwhelming investigators.

## Official Sources

- [PSR PS25/5 APP scams reimbursement requirement](https://www.psr.org.uk/publications/policy-statements/ps255-app-scams-reimbursement-requirement/)
- [PSR APP scams workstream](https://www.psr.org.uk/our-work/app-scams/)

## Learning Implications

APP scam material helps learners distinguish authorised payment fraud from account takeover.
In the NovaBank Digital **Scam-to-mule flow**, the User may authenticate normally while the
Client is being socially engineered. The useful detection questions are therefore about payment
context: beneficiary novelty, account age, payment velocity, rapid onward movement, and links
between incoming victim payments and mule-account pass-through behavior.

The reimbursement policy context also gives governance exercises a stakeholder lens. A model
that only ranks outbound payments may miss receiving-side mule risk, while a model that flags
too broadly may overwhelm investigators and produce weak explanations for legitimate Clients.

## Linked Exercises

- `notebooks/02_digital_scam_to_mule/novabank_scam_to_mule_baseline.ipynb`: uses NovaBank
  Digital sessions, beneficiary changes, incoming victim payments, and onward transfers to
  score scam-to-mule risk.
- `notebooks/03_alert_governance/alert_governance_memo.ipynb`: compares thresholds, alert
  capacity, and false positives across private-banking and digital-banking scenarios.
- `notebooks/05_digital_session_and_payment_fraud/novabank_feature_engineering.ipynb`:
  builds the `db_` session-risk, beneficiary-novelty, and velocity features that connect APP
  scam signals to the `new_beneficiary_payment` and `session_payment_velocity` Detection
  patterns.
- `notebooks/05_digital_session_and_payment_fraud/novabank_supervised_baseline.ipynb`:
  tunes alert thresholds with investigation capacity and cost tradeoffs.
- `notebooks/05_digital_session_and_payment_fraud/novabank_alert_triage.ipynb`: reviews
  alerts where confirmed-fraud is an imperfect, noisy label.

## Human Review

HITL review should confirm that the UK APP scam framing is current, that PSR sources are the
right official anchors, and that the note avoids translating UK payment policy into general
legal advice for learners.
