# Notebooks

Featured notebooks are organized by module.

Track extension notebook naming and module-layout conventions are defined in
[`../docs/schema/track-extension-conventions.md`](../docs/schema/track-extension-conventions.md).

- `00_foundations/`: setup, data tour, schema, SQL feature extraction. Start with `00_foundations/foundations_data_tour.ipynb`, with the ERD-backed schema tour in `../docs/schema/erd.md`.
- `01_private_banking_transaction_fraud/`: private-banking transaction fraud baseline. Start with `01_private_banking_transaction_fraud/alpine_crest_baseline.ipynb`.
- `02_digital_scam_to_mule/`: digital scam-to-mule fraud detection baseline. Start with `02_digital_scam_to_mule/novabank_scam_to_mule_baseline.ipynb`.
- `03_alert_governance/`: alert interpretation and governance. Start with `03_alert_governance/alert_governance_memo.ipynb`.
- `04_private_banking_feature_engineering/`: private-banking feature
  engineering and supervised threshold tuning for Alpine Crest relationship,
  account, counterparty, velocity, and relationship-manager context. Start with
  `04_private_banking_feature_engineering/alpine_crest_feature_engineering.ipynb`,
  then run
  `04_private_banking_feature_engineering/alpine_crest_supervised_baseline.ipynb`.
- `05_digital_session_and_payment_fraud/`: NovaBank Digital session and payment
  fraud feature engineering. Start with
  `05_digital_session_and_payment_fraud/novabank_feature_engineering.ipynb`,
  then run
  `05_digital_session_and_payment_fraud/novabank_supervised_baseline.ipynb`.

## Optional Warm-Ups

The warm-ups under `00_foundations/warmups/` are outside the required core module
sequence and are not a separate beginner curriculum. Use them only when you want
to refresh mechanics with the same canonical synthetic data, SQLite path, and
foundation **Progressive data views** used by the foundations exercises.

- `00_foundations/warmups/python_canonical_data_warmup.ipynb`
- `00_foundations/warmups/pandas_progressive_views_warmup.ipynb`
- `00_foundations/warmups/sql_progressive_views_warmup.ipynb`
- `00_foundations/warmups/sklearn_alert_scoring_warmup.ipynb`

## Run The Featured Notebooks

From the repository root, install the development dependencies first:

```bash
uv sync --extra dev
```

Open the notebooks interactively:

```bash
uv run jupyter lab notebooks
```

To execute the featured notebooks without opening the UI, run the smoke tests:

```bash
uv run pytest tests/test_foundations_notebook.py tests/test_private_banking_notebook.py tests/test_digital_scam_to_mule_notebook.py tests/test_alert_governance_notebook.py tests/test_private_banking_feature_engineering_notebook.py tests/test_private_banking_supervised_baseline_notebook.py tests/test_digital_feature_engineering_notebook.py tests/test_digital_supervised_baseline_notebook.py
```

Run the optional warm-up notebooks:

```bash
uv run pytest tests/test_warmup_notebooks.py
```
