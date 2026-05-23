---
title: Digital Scam-To-Mule Source Pack
status: draft-hitl
hitl_review_required: true
v0_1_area: digital_scam_to_mule
track: Digital-banking fraud detection
detection_pattern: authorised scam payment to mule or fraudster account
geography: United Kingdom / payments
source_quality: official payment regulator source candidate
linked_modules: notebooks/02_digital_scam_to_mule/novabank_scam_to_mule_baseline.ipynb, notebooks/03_alert_governance/alert_governance_memo.ipynb
---

# Digital Scam-To-Mule Source Pack

<!-- HITL-REVIEW-REQUIRED -->

## Source Links

- Payment Systems Regulator APP fraud data: https://www.psr.org.uk/app-fraud-data/

## Public Facts

- The source candidate is an official Payment Systems Regulator page about authorised push payment scam performance data.
- APP scam framing is relevant to a **Scam-to-mule flow** where a victim authorizes a payment and funds move to a fraudster or mule account.
- The page is used as a source pack candidate, not as a claim that the synthetic NovaBank Digital scenario reconstructs real events.

## Interpretation For Detection Patterns

This source pack supports a **Detection pattern** around authorised scam payments, receiving-account risk, and onward movement. The analytic lesson is to connect victim payment behavior with beneficiary changes, device/session telemetry, early-life accounts, and rapid pass-through.

## Likely Data Signals

- New beneficiary shortly before payment.
- Receiving account with short account age.
- Shared device or network signals across Users.
- Rapid onward transfer after incoming victim payment.
- Noisy case outcomes where some alerts close without confirmation.

## Linked Modules And Exercises

- `notebooks/02_digital_scam_to_mule/novabank_scam_to_mule_baseline.ipynb`
- `notebooks/03_alert_governance/alert_governance_memo.ipynb`

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
