# 06_graph_network_fraud

v0.6 graph and network analytics for the **Banking Fraud Detection Lab**. Learners
build a NetworkX graph from the canonical generated tables and investigate
relationship and transaction networks using explainable graph features.

Graph evidence **extends** the v0.1–v0.5 tabular investigation — it does not
replace it. Every network signal is connected back to the existing tabular
features and case context.

## Notebooks

- [alpine_crest_graph_investigation.ipynb](alpine_crest_graph_investigation.ipynb):
  **Alpine Crest Private Bank** private-banking graph investigation covering
  beneficial ownership, shared counterparties, related entities, and circular
  funds movement.
- [novabank_graph_investigation.ipynb](novabank_graph_investigation.ipynb):
  **NovaBank Digital** digital-banking graph investigation covering mule rings,
  shared devices, shared beneficiaries, and pass-through clusters. Respects the
  **User** (digital login identity) vs **Client** (legal customer) distinction.

## How to run

```bash
uv run jupyter notebook notebooks/06_graph_network_fraud/alpine_crest_graph_investigation.ipynb
```

The notebook runs end-to-end on the tiny seed-42 canonical dataset with no extra
infrastructure. Neo4j is optional and not required (see
[../../docs/graph/neo4j_export.md](../../docs/graph/neo4j_export.md)).

## Case library and regulatory context

Graph-network source packs are linked from the
[case library index](../../docs/cases/index.md) under the graph-network facet.
See the full catalog:

- [Case library index](../../docs/cases/index.md)
- [Regulatory source index](../../docs/regulation/index.md)

## Glossary alignment

- **Banking relationship**: the Swiss-bank-style container modelled as a node.
- **Partner**, **Client**: the glossary identities modelled as nodes.
- **Alpine Crest Private Bank**: the fictional private bank for these scenarios.

No real client data, no reconstruction of real events, and no legal advice.
