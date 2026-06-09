# Alert-Aware Metrics

The v0.1 evaluation utility scores alert-level model outputs against generated
case outcomes. It is designed for notebook explanations of alert capacity,
threshold choice, and operational tradeoffs.

## Input Format

Use `evaluate_alert_scores(cases, case_outcomes, alert_scores)` with:

- `cases`: generated case records containing `case_id` and `alert_id`.
- `case_outcomes`: generated outcomes containing `case_id`, `confirmed_fraud`,
  and optionally `loss_amount_chf`.
- `alert_scores`: model-like scores containing `alert_id` and `score`, where
  `score` is normalized from `0` to `1`.

The utility joins scores to the alert lifecycle through `cases` and
`case_outcomes`; it does not train a model or expose protected scenario answer
keys.

The v0.3 Alpine Crest supervised-baseline notebook at
`../notebooks/04_private_banking_feature_engineering/alpine_crest_supervised_baseline.ipynb`
uses this report shape for threshold tuning over private-banking feature-library
outputs.

## Report Fields

The returned report includes:

- `pr_auc`: average precision over generated case outcomes.
- `threshold_summaries`: precision, recall, confusion-matrix counts, alert
  volume, alert capacity, capacity utilization, and over-capacity alert counts.
- `cost_curve`: investigation cost, false-positive cost, missed-fraud cost, and
  total cost by threshold.
- `lowest_cost_threshold`: the lowest-cost threshold among the supplied
  thresholds.
- `limitation_summary`: notebook-ready language for explaining interpretation
  limits.

## Why Accuracy Is Out Of Scope

Simplistic accuracy claims are out of scope for banking fraud detection because
confirmed fraud is sparse, alert volume is capacity-constrained, false positives
consume investigation time, and missed fraud carries loss and Client harm. Use
precision, recall, PR-AUC, alert capacity, and cost summaries instead.
