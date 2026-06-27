---
title: Graph Network Money Mules Source Pack
status: draft-hitl
hitl_review_required: true
v0_1_area: graph_or_network_pattern
track: Digital-banking fraud detection
detection_pattern: mule ring and shared-beneficiary cluster across accounts and devices
pattern_id: mule_ring
institution_type: digital bank
source_authority: Europol
source_type: enforcement
geography: Europe / international
product: digital current accounts and instant payments
source_quality: official law-enforcement source candidate
linked_modules: notebooks/06_graph_network_fraud/novabank_graph_investigation.ipynb, notebooks/02_digital_scam_to_mule/novabank_scam_to_mule_baseline.ipynb, notebooks/09_capstone/novabank_capstone_scoring.ipynb
---

# Graph Network Money Mules Source Pack

<!-- HITL-REVIEW-REQUIRED -->

This is educational material for the Banking Fraud Detection Lab. It is not legal,
compliance, audit, investment, regulatory, or professional advice.

## Summary

This source pack anchors the `mule_ring` graph-native **Detection pattern** —
networked mule and rented accounts moving funds through shared beneficiaries and
devices — using a Europol law-enforcement publication as a public source candidate.
It supports the digital-banking track at **NovaBank Digital** and connects to the v0.6
graph investigation. The learner outcome is to reason about mule-ring indicators
(large connected components, shared devices, beneficiary reuse, clustered pass-through)
from graph features and tabular features, and to draft a network-hypothesis note
without reconstructing the public matter.

## Source Links

- Europol EMMA8 source candidate: https://www.europol.europa.eu/media-press/newsroom/news/2-469-money-mules-arrested-in-worldwide-crackdown-against-money-laundering

## Public Facts

- The source candidate is an official Europol public communication about money mule enforcement activity.
- It highlights money mules, recruiters, fraudulent transactions, and cross-border coordination.
- It is included as a graph/network source pack, not as a reconstruction target for synthetic data.

## Interpretation For Detection Patterns

This source pack supports the graph-native `mule_ring` **Detection pattern**: mule
behaviour can appear through shared devices, shared beneficiaries, rapid pass-through
paths, related accounts, and connected components across Users, accounts, and
transactions. The single-edge `digital_scam_to_mule` pattern captures one victim-to-mule
flow; `mule_ring` captures the networked cluster that several such flows form.

## Likely Data Signals

- Large connected component spanning many Users, accounts, or beneficiaries (`graph_connected_component`).
- Device fingerprint shared across multiple Users (`graph_node_degree`, shared-device tabular features).
- Beneficiary reused across accounts (counterparty edges, beneficiary-novelty tabular features).
- Short path from incoming victim payment to outgoing transfer and onward pass-through (`graph_path_length`, pass-through tabular features).

## Linked Modules And Exercises

- `notebooks/06_graph_network_fraud/novabank_graph_investigation.ipynb`
- `notebooks/02_digital_scam_to_mule/novabank_scam_to_mule_baseline.ipynb`

### Exercise 1 — Draft a mule-ring network-hypothesis note

- Pattern: `mule_ring`
- Module: `notebooks/06_graph_network_fraud/novabank_graph_investigation.ipynb`
- Prompt: Using the mule-ring behaviour described in the Public Facts section and the connected-component and shared-device graph features, draft a one-paragraph hypothesis on how a large component with high-degree devices signals a mule ring. Frame the note for stakeholder discussion and avoid claims about criminal intent.
- Learner output: A four-to-six-sentence network-hypothesis note referencing the connected-component signal, the shared-device indicator, the limitation that a cluster is a lead not proof, and a follow-up question. Educational framing only.

## Regulatory Hooks

- Public-private information sharing and money-mule typologies are relevant context.
- Human review decides how to connect this source to graph exercises without implying real-event reconstruction.

## Limitations

- A connected component or shared device is an investigative lead, not proof of a mule ring.
- Synthetic examples remain clearly fictional and limited to **NovaBank Digital**.
- Human review is required before publication.

## Human Review

<!-- HITL-REVIEW-REQUIRED -->

- Verify whether this source should be paired with FATF or national-agency typologies.
- Review graph/network framing for the v0.6 module.
- Confirm source-pack status before publication.

