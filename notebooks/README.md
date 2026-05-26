# Notebooks

Featured notebooks are organized by module.

- `00_foundations/`: setup, data tour, schema, SQL feature extraction. Start with `00_foundations/foundations_data_tour.ipynb`, with the ERD-backed schema tour in `../docs/schema/erd.md`.
- `01_private_banking_transaction_fraud/`: private-banking transaction fraud baseline. Start with `01_private_banking_transaction_fraud/alpine_crest_baseline.ipynb`.
- `02_digital_scam_to_mule/`: digital scam-to-mule fraud detection baseline. Start with `02_digital_scam_to_mule/novabank_scam_to_mule_baseline.ipynb`.
- `03_alert_governance/`: alert interpretation and governance. Start with `03_alert_governance/alert_governance_memo.ipynb`.

## Run The Featured Notebooks

From the repository root, install the development dependencies first:

```bash
uv sync --extra dev
```

Open the notebooks interactively:

```bash
uv run jupyter lab notebooks
```

To execute the featured v0.1 notebooks without opening the UI, run the smoke
tests:

```bash
uv run pytest tests/test_foundations_notebook.py tests/test_private_banking_notebook.py tests/test_digital_scam_to_mule_notebook.py tests/test_alert_governance_notebook.py
```
