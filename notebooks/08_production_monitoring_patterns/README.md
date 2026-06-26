# 08_production_monitoring_patterns

v0.8 production-monitoring patterns for the **Banking Fraud Detection Lab**.
Learners turn a fitted score into the production-monitoring tables (score,
threshold, alert_decision, reviewer_action, audit_event), inspect an alert
queue and its aging, summarise operational metrics, run score/feature drift
and data-quality checks, and trace a monitoring anomaly back to a **Client** /
**Banking relationship** / Detection pattern — for both tracks.

This module **extends** the v0.1–v0.7 investigation — it does not replace it.
The monitoring flow consumes the v0.3 supervised baselines and engineered
features, the v0.6 graph evidence, and the v0.7 thresholds and feature
explanations as inputs, and uses the v0.8 monitoring builders rather than
inline logic. It deepens, rather than replaces, the governance bridge in
[`03_alert_governance`](../03_alert_governance/README.md) and the model-risk
review in
[`07_interpretability_model_risk`](../07_interpretability_model_risk/README.md);
the three modules cross-reference each other.

## Notebooks

- [alpine_crest_monitoring.ipynb](alpine_crest_monitoring.ipynb): **Alpine Crest
  Private Bank** private-banking production-monitoring notebook covering batch
  scoring, score/threshold tables, alert decisions and the audit chain, a
  reviewer action with v0.7 explanation evidence, alert-queue inspection and
  aging, operational metrics, and score/feature drift plus monitoring
  data-quality for the `pb_high_value_movement` Detection pattern.
- [novabank_monitoring.ipynb](novabank_monitoring.ipynb): **NovaBank Digital**
  digital-banking counterpart covering the same v0.8 monitoring flow for the
  `digital_scam_to_mule` Detection pattern, carrying **Banking relationship**
  and **User** (digital login identity) lineage through the score / decision /
  reviewer-action chain.

The two notebooks are track counterparts and respect the **User** (digital
login identity) vs **Client** (legal customer) distinction.

## How to run

```bash
uv run jupyter notebook notebooks/08_production_monitoring_patterns/alpine_crest_monitoring.ipynb
```

The notebook runs end-to-end on the seed-42 canonical dataset with no extra
infrastructure.

## Notebook generation / regeneration

The `.ipynb` notebooks are the **executed and tested artifacts**: the smoke
test in
[`tests/test_alpine_crest_monitoring_notebook.py`](../../tests/test_alpine_crest_monitoring_notebook.py)
runs the notebook directly and is the source of truth for behaviour.

The committed generator scripts are the **deterministic regeneration source** —
they document exactly how each notebook was produced and let it be rebuilt
identically:

- [`_build_alpine_crest_monitoring_notebook.py`](_build_alpine_crest_monitoring_notebook.py)
- [`_build_novabank_monitoring_notebook.py`](_build_novabank_monitoring_notebook.py)

To regenerate a notebook from its generator:

```bash
uv run python notebooks/08_production_monitoring_patterns/_build_alpine_crest_monitoring_notebook.py
```

Regeneration is **optional and manual**. The committed `.ipynb` files are
authoritative; only re-run a generator when intentionally changing notebook
content, then re-run the smoke tests.

## Regulatory context

- [Regulatory source index](../../docs/regulation/index.md)

## Glossary alignment

- **Client**: the legal customer.
- **User**: the digital login identity (NovaBank Digital).
- **Banking relationship**: the Swiss-bank-style relationship container.
- **Detection pattern**: the fraud pattern a score/decision is scoped to.
- **Alert lifecycle**: triaged → reviewed → closed, surfaced as an inspectable queue.
- **Alpine Crest Private Bank** / **NovaBank Digital**: the fictional
  institutions for these scenarios.

No real client data, no reconstruction of real events, and no legal advice.
Monitoring is a review prompt, not a verdict — a model should not be judged by
headline accuracy.
