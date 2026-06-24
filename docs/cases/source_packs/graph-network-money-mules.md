---
title: Graph Network Money Mules Source Pack
status: draft-hitl
hitl_review_required: true
v0_1_area: graph_or_network_pattern
track: Future graph/network analytics
detection_pattern: money mule network and shared-account movement
pattern_id: digital_scam_to_mule
institution_type: digital banking and payments network
source_authority: Europol
source_type: enforcement
geography: Europe / international
product: money movement and mule accounts
source_quality: official law-enforcement source candidate
linked_modules: notebooks/02_digital_scam_to_mule/novabank_scam_to_mule_baseline.ipynb
---

# Graph Network Money Mules Source Pack

<!-- HITL-REVIEW-REQUIRED -->

This is educational material for the Banking Fraud Detection Lab. It is not legal,
compliance, audit, investment, regulatory, or professional advice.

## Summary

This source pack anchors the `digital_scam_to_mule` **Detection pattern** at the
network level — money-mule networks and shared-account movement across multiple accounts —
using a Europol law-enforcement publication as a public source candidate. It supports the
digital-banking track at **NovaBank Digital** and frames future graph/network analytics. The
learner outcome is to reason about multi-account mule indicators (shared devices, beneficiary
reuse, clustered pass-through) from tabular features and to draft a network-hypothesis note
without reconstructing the public matter.

## Source Links

- Europol EMMA8 source candidate: https://www.europol.europa.eu/media-press/newsroom/news/2-469-money-mules-arrested-in-worldwide-crackdown-against-money-laundering

## Public Facts

- The source candidate is an official Europol public communication about money mule enforcement activity.
- It highlights money mules, recruiters, fraudulent transactions, and cross-border coordination.
- It is included as a future graph/network source pack, not as a reconstruction target for synthetic data.

## Interpretation For Detection Patterns

This source pack supports a graph/network **Detection pattern**: mule behavior can appear through shared devices, shared beneficiaries, rapid pass-through paths, related accounts, and connected components across Users, accounts, and transactions.

## Likely Data Signals

- Shared device fingerprint across multiple Users (`db_is_shared_device`, `db_device_user_count`).
- Beneficiary reuse across accounts (`db_is_new_beneficiary`, `db_beneficiary_age_days`).
- Short path from incoming victim payment to outgoing transfer (`db_is_rapid_pass_through`, `db_hours_since_prior_credit`).
- Clustered accounts with similar transaction timing or destination countries (`db_is_beneficiary_country_risky`).

## Linked Modules And Exercises

- `notebooks/02_digital_scam_to_mule/novabank_scam_to_mule_baseline.ipynb`
- Future `06_graph_network_analytics` module.

### Exercise 1 — Draft a network-hypothesis investigation note

- Pattern: `digital_scam_to_mule`
- Module: `notebooks/02_digital_scam_to_mule/novabank_scam_to_mule_baseline.ipynb`
- Prompt: Using the mule behavior described in the Public Facts section, draft a one-paragraph hypothesis on how shared-device fingerprints (`db_is_shared_device`, `db_device_user_count`) could indicate a mule network even from tabular features. Frame the note for stakeholder discussion and avoid claims about criminal intent.
- Learner output: A four-to-six-sentence network-hypothesis note referencing the shared-device signal, the candidate network indicator, the limitation (no graph module yet), and a follow-up question. Educational framing only.

## Regulatory Hooks

- Public-private information sharing and money-mule typologies are relevant context.
- Human review must decide how to connect this source to future graph exercises without implying real-event reconstruction.

## Limitations

- The v0.1 curriculum does not yet implement the graph module.
- Synthetic examples should remain clearly fictional and limited to **NovaBank Digital**.
- Human review is required before publication.

## Human Review

<!-- HITL-REVIEW-REQUIRED -->

- Verify whether this source should be paired with FATF or national-agency typologies.
- Review graph/network framing for the future module.
- Confirm source-pack status before publication.
