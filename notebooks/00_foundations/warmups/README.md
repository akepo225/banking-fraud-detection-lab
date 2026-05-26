# Optional Canonical-Data Warm-Ups

These notebooks are optional refreshers before the required core module sequence.
They are not a separate beginner curriculum. Each warm-up uses tiny seed-42 data
from the same **Realistic synthetic data model** used by the featured notebooks.

- [`python_canonical_data_warmup.ipynb`](python_canonical_data_warmup.ipynb):
  practice Python iteration, dictionaries, and small helper functions over
  learner-facing generated tables.
- [`pandas_progressive_views_warmup.ipynb`](pandas_progressive_views_warmup.ipynb):
  practice pandas selection, grouping, and summary tables with foundation
  **Progressive data views**.
- [`sql_progressive_views_warmup.ipynb`](sql_progressive_views_warmup.ipynb):
  practice SQLite queries against the same local learner database surface used
  by the foundations exercises.
- [`sklearn_alert_scoring_warmup.ipynb`](sklearn_alert_scoring_warmup.ipynb):
  practice a small scikit-learn pipeline on Alert lifecycle rows and evaluate
  scores with fraud-aware metrics.

Run the warm-up smoke tests from the repository root:

```bash
uv run pytest tests/test_warmup_notebooks.py
```
