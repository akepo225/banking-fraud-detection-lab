# Dataset Quality Report

The dataset quality report is a local, deterministic check over generated
foundation data. It helps learners and maintainers distinguish expected
synthetic-data behavior from generator defects before using a dataset in SQL,
notebooks, or later fraud detection tracks.

No external infrastructure is required. The report uses the canonical generated
tables, schema metadata, temporal rules, protected-key boundaries, and
foundation Progressive data views.

## Generate A Report

Generate the committed tiny scale report:

```bash
uv run python -m banking_fraud_lab.data_quality --scale tiny
```

Generate tiny and one larger local scale profile into a Markdown file:

```bash
uv run python -m banking_fraud_lab.data_quality --scale tiny --scale small --output data/generated/reports/dataset-quality.md
```

Use JSON when another validation script needs structured output:

```bash
uv run python -m banking_fraud_lab.data_quality --scale medium --format json --output data/generated/reports/dataset-quality-medium.json
```

The `data/generated/` directory is ignored by git, so local report files do not
become accidental repository changes.

## Interpret The Dimensions

The report dimensions cover row counts, key nullability, referential integrity,
temporal ranges, prevalence ranges, protected-key exclusion, and Progressive
data view health.

- `row_counts`: counts every canonical table for the selected scale profile.
- `key_nullability`: checks primary keys are non-null and unique, and required
  schema columns are populated.
- `referential_integrity`: checks every documented foreign-key reference points
  to an existing parent row.
- `temporal_ranges`: summarizes datetime ranges and validates the foundation
  temporal orderings, including Alert lifecycle order.
- `prevalence_ranges`: checks stable rate bands such as suspicious activities
  per transaction and confirmed-fraud outcomes per transaction. These are range
  checks, not row-level answer keys.
- `protected_key_exclusion`: verifies Protected answer keys exist internally,
  remain unavailable to learners, and are excluded from learner-facing tables.
- `progressive_view_health`: verifies foundation Progressive data views can be
  built, match their contracts, contain rows, and do not expose protected-key
  columns.

A passing report means the generated dataset is coherent enough for the
foundation learning path. It does not mean the synthetic data is real, complete,
or suitable for legal, regulatory, audit, investment, or professional decisions.
