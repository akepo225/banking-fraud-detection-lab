# 07_interpretability_model_risk

v0.7 interpretability, governance, and model-risk for the **Banking Fraud
Detection Lab**. Learners explain model behaviour, choose thresholds, document
limitations, and write governance-ready summaries for both tracks.

This module **extends** the v0.1–v0.6 investigation — it does not replace it.
Every explanation is connected back to a **Detection pattern** id and to the
existing feature, case, and graph evidence.

## Notebooks

- [alpine_crest_interpretability.ipynb](alpine_crest_interpretability.ipynb):
  **Alpine Crest Private Bank** private-banking interpretability and model-risk
  notebook covering per-alert "why", feature importance and partial-dependence
  explanations, threshold selection, false-positive concentration, and model
  documentation.
- (NovaBank digital-banking notebook and the governance memo land in later
  v0.7 slices.)

## How to run

```bash
uv run jupyter notebook notebooks/07_interpretability_model_risk/alpine_crest_interpretability.ipynb
```

The notebook runs end-to-end on the seed-42 canonical dataset with no extra
infrastructure.

## Notebook generation / regeneration

The `.ipynb` notebooks are the **executed and tested artifacts**: the smoke test
in [`tests/test_alpine_crest_interpretability_notebook.py`](../../tests/test_alpine_crest_interpretability_notebook.py)
runs the notebook directly and is the source of truth for behaviour.

The committed generator scripts are the **deterministic regeneration source** —
they document exactly how each notebook was produced and let it be rebuilt
identically:

- [`_build_alpine_crest_interpretability_notebook.py`](_build_alpine_crest_interpretability_notebook.py)

To regenerate a notebook from its generator:

```bash
uv run python notebooks/07_interpretability_model_risk/_build_alpine_crest_interpretability_notebook.py
```

Regeneration is **optional and manual**. The committed `.ipynb` files are
authoritative; only re-run a generator when intentionally changing notebook
content, then re-run the smoke tests.

## Regulatory context

- [Regulatory source index](../../docs/regulation/index.md)

## Glossary alignment

- **Client**: the legal customer.
- **Banking relationship**: the Swiss-bank-style relationship container.
- **Alpine Crest Private Bank** / **NovaBank Digital**: the fictional
  institutions for these scenarios.

No real client data, no reconstruction of real events, and no legal advice.
