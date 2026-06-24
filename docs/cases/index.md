# Case Library

The case library is organized by **Detection pattern** first, with machine-readable
facets for track, institution type, source authority, source type, geography, product,
and linked module. Each pack's front matter carries these facets; the per-pattern
tables below mirror them for at-a-glance navigation.

All packs are draft HITL artifacts and require human review before publication.

## Inclusion Rule

A case belongs here only if it has:

- Public sources.
- A clear detection pattern.
- Learner exercise potential.
- Explicit limitations.

## Source Quality

Source tiers (highest to lowest authority) are documented in
[Source Quality Rubric](source_quality_rubric.md):

1. Official regulator, court, or enforcement sources.
2. Bank annual reports, official disclosures, or payment-system operators.
3. Reputable journalism or industry reports.

Each pack's `source_quality` front-matter value names the source-specific phrase
family for its tier (for example `official regulator source candidate`); the
machine-readable `source_type` facet classifies the source body itself.

## Template

Case documents follow the canonical [Case Template](TEMPLATE.md): source links,
facts vs interpretation, detection patterns, likely data signals, linked modules
with learner-output exercises, regulatory hooks, limitations, and human review.
See [Contributing Case Source Packs](CONTRIBUTING.md) for the contributor checklist.

## Detection Patterns

Packs grouped by their `pattern_id`. The `pattern_id` values are frozen in the
shared Detection pattern registry (`src/banking_fraud_lab/schema/detection_patterns.py`).

### `pb_high_value_movement`

High-value private-banking movement read with Banking relationship context.

| Pack | Track | Institution | Source authority | Source type | Geography |
| --- | --- | --- | --- | --- | --- |
| [Private-banking high-value movement](source_packs/private-banking-high-value-movement.md) | Private-banking | private bank | FINMA | regulator | Switzerland / cross-border |

### `pb_transaction_fraud`

Relationship- and transaction-monitoring control failure in private banking.

| Pack | Track | Institution | Source authority | Source type | Geography |
| --- | --- | --- | --- | --- | --- |
| [Private-banking transaction monitoring](source_packs/private-banking-transaction-monitoring.md) | Private-banking | private bank | FINMA | regulator | Switzerland / cross-border |

### `digital_scam_to_mule`

Authorised scam payment to a mule or fraudster account, and early-life mule behavior.

| Pack | Track | Institution | Source authority | Source type | Geography |
| --- | --- | --- | --- | --- | --- |
| [Digital scam-to-mule](source_packs/digital-scam-to-mule.md) | Digital-banking | PSP / digital bank | Payment Systems Regulator | regulator | United Kingdom / payments |
| [Digital money mule behavior](source_packs/digital-money-mule-behavior.md) | Digital-banking | PSP / digital bank | UK Finance | industry_report | United Kingdom / cross-border payments |
| [Graph network money mules](source_packs/graph-network-money-mules.md) | Future graph/network analytics | digital banking & payments network | Europol | enforcement | Europe / international |

### `new_beneficiary_payment`

Authorised push payment scam and payment-system guidance on new-beneficiary confirmation.

| Pack | Track | Institution | Source authority | Source type | Geography |
| --- | --- | --- | --- | --- | --- |
| [Authorised push payment scam to a newly added beneficiary](source_packs/digital-app-scam-payments.md) | Digital-banking | PSP / digital bank | Payment Systems Regulator | regulator | United Kingdom / payments |
| [Payment-system beneficiary guidance](source_packs/digital-payment-system-guidance.md) | Digital-banking | PSP / digital bank | Pay.UK | payment_system_operator | United Kingdom / payment rails |

### `session_payment_velocity`

Account-takeover with elevated session payment velocity in online banking.

| Pack | Track | Institution | Source authority | Source type | Geography |
| --- | --- | --- | --- | --- | --- |
| [Online-bank account control failure](source_packs/digital-online-bank-control-failures.md) | Digital-banking | PSP / digital bank | National Cyber Security Centre | cyber_authority | United Kingdom / online banking |

## Cross-Pattern and Governance

Packs that are cross-track governance or method artifacts rather than a single
Detection pattern. These keep `pattern_id` optional.

| Pack | Track | Institution | Source authority | Source type | Geography |
| --- | --- | --- | --- | --- | --- |
| [Model-output governance and threshold documentation](source_packs/model-governance-method.md) | Cross-track governance | cross-bank model governance | Federal Reserve | regulator | United States / cross-border method |

Each draft must keep `<!-- HITL-REVIEW-REQUIRED -->` until source selection, framing, and limitations are reviewed by a human.
