---
title: Graph Network Money Mules Source Pack
status: draft-hitl
hitl_review_required: true
v0_1_area: graph_or_network_pattern
track: Future graph/network analytics
detection_pattern: money mule network and shared-account movement
geography: Europe / international
source_quality: official law-enforcement source candidate
linked_modules: notebooks/02_digital_scam_to_mule/novabank_scam_to_mule_baseline.ipynb
---

# Graph Network Money Mules Source Pack

<!-- HITL-REVIEW-REQUIRED -->

## Source Links

- Europol EMMA8 source candidate: https://www.europol.europa.eu/media-press/newsroom/news/2-469-money-mules-arrested-in-worldwide-crackdown-against-money-laundering

## Public Facts

- The source candidate is an official Europol public communication about money mule enforcement activity.
- It highlights money mules, recruiters, fraudulent transactions, and cross-border coordination.
- It is included as a future graph/network source pack, not as a reconstruction target for synthetic data.

## Interpretation For Detection Patterns

This source pack supports a graph/network **Detection pattern**: mule behavior can appear through shared devices, shared beneficiaries, rapid pass-through paths, related accounts, and connected components across Users, accounts, and transactions.

## Likely Data Signals

- Shared device fingerprint across multiple Users.
- Beneficiary reuse across accounts.
- Short path from incoming victim payment to outgoing transfer.
- Clustered accounts with similar transaction timing or destination countries.

## Linked Modules And Exercises

- `notebooks/02_digital_scam_to_mule/novabank_scam_to_mule_baseline.ipynb`
- Future `06_graph_network_analytics` module.

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
