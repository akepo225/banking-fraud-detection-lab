---
title: Circular Funds Movement Source Pack
status: draft-hitl
hitl_review_required: true
v0_1_area: graph_or_network_pattern
track: Private-banking fraud detection
detection_pattern: circular funds movement among related entities and layered accounts
pattern_id: circular_funds_movement
institution_type: private bank
source_authority: FINMA
source_type: regulator
geography: Switzerland / cross-border
product: private-banking relationships and transactions
source_quality: official regulator source candidate
linked_modules: notebooks/06_graph_network_fraud/alpine_crest_graph_investigation.ipynb, notebooks/01_private_banking_transaction_fraud/alpine_crest_baseline.ipynb
---

# Circular Funds Movement Source Pack

<!-- HITL-REVIEW-REQUIRED -->

This is educational material for the Banking Fraud Detection Lab. It is not legal,
compliance, audit, investment, regulatory, or professional advice.

## Summary

This source pack anchors the `circular_funds_movement` graph-native **Detection
pattern** — funds cycling among related Partner, Client, and Banking relationship
entities through layered accounts and counterparties — using FINMA public
anti-money-laundering guidance as a source candidate. It supports the private-banking
track at **Alpine Crest Private Bank** and connects to the v0.6 graph investigation.
The learner outcome is to reason about circular-movement indicators (bridge nodes,
short return paths, related-entity clusters) from graph features and tabular features,
and to draft a network-hypothesis note without reconstructing the public matter.

## Source Links

- FINMA AML guidance source candidate: https://www.finma.ch/en/regulation/directives/finma-anti-money-laundering-ordinance/

## Public Facts

- The source candidate is official FINMA public guidance on anti-money-laundering obligations for supervised financial intermediaries.
- It addresses due diligence, beneficial ownership, and the detection of unusual or layered transaction structures.
- It is included as a graph/network source pack, not as a reconstruction target for synthetic data.

## Interpretation For Detection Patterns

This source pack supports the graph-native `circular_funds_movement` **Detection
pattern**: circular movement can appear when funds leave a Banking relationship,
pass through layered counterparties, and return to a related account through a short
path. The `pb_high_value_movement` and `pb_transaction_fraud` patterns capture
individual transactions; `circular_funds_movement` captures the cycle that links
them across related entities.

## Likely Data Signals

- Bridge-edge accounts or transactions that link otherwise separate relationship clusters (`graph_bridge_node`).
- Short path returning to a starting account through related entities (`graph_path_length`).
- Counterparty shared across related Partners or Clients within a Banking relationship (counterparty edges, new-counterparty tabular features).
- Connected component spanning related Partners, Clients, and accounts (`graph_connected_component`).

## Linked Modules And Exercises

- `notebooks/06_graph_network_fraud/alpine_crest_graph_investigation.ipynb`
- `notebooks/01_private_banking_transaction_fraud/alpine_crest_baseline.ipynb`

### Exercise 1 — Draft a circular-movement network-hypothesis note

- Pattern: `circular_funds_movement`
- Module: `notebooks/06_graph_network_fraud/alpine_crest_graph_investigation.ipynb`
- Prompt: Using the circular-movement behaviour described in the Public Facts section and the bridge-node and path-length graph features, draft a one-paragraph hypothesis on how a bridge-edge account with a short return path signals circular funds movement among related entities. Frame the note for stakeholder discussion and avoid claims about criminal intent.
- Learner output: A four-to-six-sentence network-hypothesis note referencing the bridge-node signal, the short-return-path indicator, the limitation that a cycle is a lead not proof, and a follow-up question. Educational framing only.

## Regulatory Hooks

- FINMA anti-money-laundering obligations and beneficial-ownership due diligence are relevant context.
- Human review decides how to connect this source to graph exercises without implying real-event reconstruction.

## Limitations

- A bridge node or short return path is an investigative lead, not proof of circular funds movement.
- Synthetic examples remain clearly fictional and limited to **Alpine Crest Private Bank**.
- Human review is required before publication.

## Human Review

<!-- HITL-REVIEW-REQUIRED -->

- Verify whether this source should be paired with FATF typologies or additional national-agency guidance.
- Review graph/network framing for the v0.6 module.
- Confirm source-pack status before publication.
