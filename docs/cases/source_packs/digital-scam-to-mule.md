---
title: Digital Scam-To-Mule Source Pack
status: draft-hitl
hitl_review_required: true
v0_1_area: digital_scam_to_mule
track: Digital-banking fraud detection
detection_pattern: authorised scam payment to mule or fraudster account
pattern_id: digital_scam_to_mule
institution_type: payment service provider or digital bank
source_authority: Payment Systems Regulator
source_type: regulator
geography: United Kingdom / payments
product: authorised push payments
source_quality: official payment regulator source candidate
linked_modules: notebooks/02_digital_scam_to_mule/novabank_scam_to_mule_baseline.ipynb, notebooks/03_alert_governance/alert_governance_memo.ipynb
---

# Digital Scam-To-Mule Source Pack

<!-- HITL-REVIEW-REQUIRED -->

This is educational material for the Banking Fraud Detection Lab. It is not legal,
compliance, audit, investment, regulatory, or professional advice.

## Summary

This source pack anchors the `digital_scam_to_mule` **Detection pattern** — an authorised scam
payment to a mule or fraudster account — using a Payment Systems Regulator publication as a
public source candidate. It supports the digital-banking track at **NovaBank Digital**. The
learner outcome is to investigate scam-to-mule flow from account age, shared-device, and
pass-through signals, and to produce feature-interpretation artifacts without reconstructing
the public matter.

## Source Links

- Payment Systems Regulator APP fraud data: https://www.psr.org.uk/app-fraud-data/

## Public Facts

- The source candidate is an official Payment Systems Regulator page about authorised push payment scam performance data.
- APP scam framing is relevant to a **Scam-to-mule flow** where a victim authorised a payment and funds move to a fraudster or mule account.
- The page is used as a source pack candidate, not as a claim that the synthetic NovaBank Digital scenario reconstructs real events.

## Interpretation For Detection Patterns

This source pack supports a **Detection pattern** around authorised scam payments, receiving-account risk, and onward movement. The analytic lesson is to connect victim payment behavior with beneficiary changes, device/session telemetry, early-life accounts, and rapid pass-through.

## Likely Data Signals

- New beneficiary shortly before payment (`db_is_new_beneficiary`).
- Receiving account with short account age (`db_account_age_days`, `db_is_early_life_account`).
- Shared device or network signals across Users (`db_is_shared_device`, `db_device_user_count`).
- Rapid onward transfer after incoming victim payment (`db_is_rapid_pass_through`, `db_hours_since_prior_credit`, `db_prior_credit_amount_chf`).
- Noisy case outcomes where some alerts close without confirmation.

## Linked Modules And Exercises

- `notebooks/02_digital_scam_to_mule/novabank_scam_to_mule_baseline.ipynb`
- `notebooks/03_alert_governance/alert_governance_memo.ipynb`

### Exercise 1 — Investigate early-life-account and shared-device correlation

- Pattern: `digital_scam_to_mule`
- Module: `notebooks/02_digital_scam_to_mule/novabank_scam_to_mule_baseline.ipynb`
- Prompt: Using the scam-to-mule baseline module, investigate how often `db_is_early_life_account` and `db_is_shared_device` co-occur across the synthetic NovaBank Digital sessions, and how that co-occurrence relates to rapid pass-through (`db_is_rapid_pass_through`).
- Learner output: A short correlation/co-occurrence summary plus two or three sentences on what the combination suggests for review and one limitation (for example, shared household devices).

## Regulatory Hooks

- Payment-scam reporting and reimbursement discussions can shape governance questions.
- Human review must decide how much payment-policy context belongs in the learner exercise.

## Limitations

- This draft does not provide legal or compliance advice.
- This draft does not imply that NovaBank Digital is based on any named payment firm.
- Human review is required before publication.

## Human Review

<!-- HITL-REVIEW-REQUIRED -->

- Verify source selection and whether a more specific APP scam report should be linked.
- Review wording for victim-sensitive language.
- Confirm the bridge from payment-source data to analytics exercises.
