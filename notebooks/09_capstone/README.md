# 09_capstone

The v0.9 capstone module of the **Banking Fraud Detection Lab**. It integrates
the v0.1–v0.8 surfaces into a single end-to-end learner path: scenario brief →
synthetic data generation → SQL features → engineered features → fitted score →
alert review → graph/case evidence → production monitoring → governance memo.
It **extends** the prior modules; it does not replace them or introduce a new
feature family.

This directory holds the capstone scoring, alert review, and interpretability
notebooks (slice #227). The synthesis notebook (graph/case evidence, production
monitoring, governance memo) is added in slice #228.

## Notebooks

- [alpine_crest_capstone_scoring.ipynb](alpine_crest_capstone_scoring.ipynb): the
  **Private-banking fraud detection** capstone for **Alpine Crest Private Bank**.
  Runs generate → engineered features → fit score → alert-aware metrics →
  capacity-aware threshold → per-alert explanation against the `pb_high_value_movement`
  and `pb_transaction_fraud` **Detection patterns** on the v0.9 capstone dataset.
- [novabank_capstone_scoring.ipynb](novabank_capstone_scoring.ipynb): the
  **Digital-banking fraud detection** capstone for **NovaBank Digital**. Runs the
  same loop against the `digital_scam_to_mule` and `new_beneficiary_payment`
  **Detection patterns**. The **User** is the digital login identity, distinct
  from the **Client** who holds the Banking relationship.

Both notebooks reuse — they do not reimplement — the v0.3/v0.4 track feature
libraries, `evaluate_alert_scores`, `recommend_lowest_cost_threshold`,
`extract_feature_importance`, and `concentrate_false_positives`.

## How to run

```bash
uv run jupyter notebook notebooks/09_capstone/alpine_crest_capstone_scoring.ipynb
uv run jupyter notebook notebooks/09_capstone/novabank_capstone_scoring.ipynb
```

Each notebook runs on the seed-42 `tiny` capstone dataset generated in-cell, with
no extra infrastructure and no optional extras required.

## Notebook generation / regeneration

The `.ipynb` files are the executed and tested artifacts; the source of truth for
their content is the smoke test `tests/test_capstone_scoring_notebook.py`. Each
notebook has a deterministic `_build_*.py` regeneration source:

```bash
uv run python notebooks/09_capstone/_build_alpine_crest_capstone_scoring_notebook.py
uv run python notebooks/09_capstone/_build_novabank_capstone_scoring_notebook.py
```

Regeneration is **optional and manual**. The committed `.ipynb` files are
authoritative; only re-run a generator when intentionally changing notebook
content, then re-run the smoke tests.

## Scenario briefs

Each notebook follows the capstone scenario brief for its track, under
`../../docs/capstone/`:

- [Alpine Crest brief](../../docs/capstone/alpine_crest_brief.md)
- [NovaBank brief](../../docs/capstone/novabank_brief.md)

## Glossary alignment

- **Client**: the legal customer; **User**: the digital login identity; **Banking
  relationship**: the relationship container. Never "customer".
- **Alpine Crest Private Bank** (private-banking track); **NovaBank Digital**
  (digital-banking track). Never real banks.
- **Detection pattern** ids (`pb_high_value_movement`, `pb_transaction_fraud`,
  `digital_scam_to_mule`, `new_beneficiary_payment`) and the **Alert lifecycle**
  tie every alert back to its analytic lineage.

No real client data, no reconstruction of real events, and no legal advice. The
repository is pre-publication; v0.9 is a beta review point, not a shipped release.
