# Optional Neo4j Export

<!-- HITL-REVIEW-REQUIRED: optional-extension-framing -->

This document describes the **optional** Neo4j export path for the v0.6 graph and
network analytics module. Neo4j is **not required** for the core v0.6 learning
path, is **not** installed by the default setup, and is **not** exercised by CI.

## Status: optional and outside the core learner path

The Banking Fraud Detection Lab is NetworkX-first and local-first. A learner can
complete every v0.6 exercise (graph construction, feature extraction, and the
private-banking and digital-banking graph notebooks) using only NetworkX and the
canonical generated tables. The Neo4j export exists for learners who want to
explore the same graph in a labelled property graph database; it adds no
analytic capability that NetworkX does not already provide in the core path.

Per ADR-0004, advanced infrastructure dependencies stay optional unless a later
ADR changes core scope. This export honours that boundary:

- The `neo4j` Python driver is declared behind an **optional** `neo4j` extra.
- `uv sync --extra dev` (the documented developer setup) and CI do **not**
  install it.
- All driver imports are guarded, so `import banking_fraud_lab.graph` succeeds
  whether or not the driver is installed.
- The learner quickstart and the CI commands are unchanged by this slice.

## What it provides

Given the `MultiDiGraph` produced by `build_banking_graph(tables)`, the export
module serializes the graph into Neo4j-ingestible artifacts that require **no
live database** to generate:

- `export_graph_to_cypher(graph)` returns a runnable Cypher script (one
  idempotent `MERGE` per node and per edge) that a learner can paste into
  Neo4j Browser or `cypher-shell`. Node labels are CamelCase versions of the
  frozen node types (e.g. `BankingRelationship`); relationship types are
  `UPPER_SNAKE` versions of the frozen edge types (e.g. `CLIENT_PARTNER`).
- `export_graph_to_neo4j_csvs(graph, output_dir)` writes `nodes.csv` and
  `edges.csv` for Neo4j's `LOAD CSV WITH HEADERS` ingest.

An optional driver-based helper, `push_graph_to_neo4j(graph, uri, ...)`, is also
provided. It degrades gracefully: when the optional driver is not installed it
raises a clear `RuntimeError` with install guidance rather than failing at
import time.

## Install (optional)

To use the driver-based push helper, install the optional extra:

```bash
uv sync --extra neo4j
```

The Cypher and CSV export helpers work **without** this extra and need no
database connection.

## Glossary alignment

- **Banking relationship**: the Swiss-bank-style container modelled as a node.
- **Partner**, **Client**, **User**: the glossary identities modelled as nodes.
- **Detection pattern**: modelled as a node when linking alerts to graph signal.

No real client data, no affiliation claims, no legal or compliance advice, and
no reconstruction of real events are involved. All data is synthetic.
