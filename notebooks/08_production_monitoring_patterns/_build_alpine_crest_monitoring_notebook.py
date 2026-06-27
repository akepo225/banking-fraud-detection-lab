"""Generate the Alpine Crest production-monitoring notebook (v0.8 #207).

Mirrors the generator-script convention used by the v0.6 graph and v0.7
interpretability notebooks: this script emits the deterministic ``.ipynb`` JSON
so the notebook content is reproducible and reviewable as code. Regeneration is
optional and manual — the committed ``.ipynb`` is authoritative.

Run from the repo root::

    uv run python notebooks/08_production_monitoring_patterns/_build_alpine_crest_monitoring_notebook.py
"""

from __future__ import annotations

import json
from pathlib import Path

# Resolve relative to this script so it works regardless of cwd.
NOTEBOOK_DIR = Path(__file__).resolve().parent
NOTEBOOK_PATH = NOTEBOOK_DIR / "alpine_crest_monitoring.ipynb"


def _md(source: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": source.splitlines(keepends=True)}


def _code(source: str) -> dict:
    return {
        "cell_type": "code",
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }


CELLS = [
    _md(
        "# Alpine Crest Production Monitoring Patterns\n"
        "\n"
        "This notebook runs the v0.8 production-monitoring flow for **Alpine Crest Private "
        "Bank** (private-banking track). It consumes the v0.8 monitoring builders — batch "
        "scoring, alert decisions, reviewer/audit, alert-queue inspection, operational "
        "metrics, score/feature drift, and monitoring data-quality — on top of the v0.3 "
        "private-banking supervised baseline and the v0.7 threshold recommender / feature "
        "explanations.\n"
        "\n"
        "Learning goal: trace one Detection pattern (`pb_high_value_movement`) from a fitted "
        "score, through threshold selection, into the production score / threshold / "
        "alert_decision / reviewer_action / audit tables, into an inspectable Alert queue and "
        "an operational summary, and out to drift and data-quality checks. The notebook keeps "
        "the limitation-aware framing visible — monitoring is a review prompt, not a verdict, "
        "and **a model should not be judged by headline accuracy**.\n"
        "\n"
        "> Educational exercise on synthetic data. No real Client, account, or transaction "
        "data; no production-readiness, certification, or legal-advice claim."
    ),
    _code(
        "import pandas as pd\n"
        "from sklearn.compose import ColumnTransformer\n"
        "from sklearn.linear_model import LogisticRegression\n"
        "from sklearn.pipeline import Pipeline\n"
        "from sklearn.preprocessing import StandardScaler\n"
        "\n"
        "from banking_fraud_lab import (\n"
        "    build_learner_facing_views,\n"
        "    build_private_banking_features,\n"
        "    evaluate_alert_scores,\n"
        "    extract_feature_importance,\n"
        "    generate_private_banking_transaction_fraud_world,\n"
        "    recommend_lowest_cost_threshold,\n"
        ")\n"
        "from banking_fraud_lab.features import PRIVATE_BANKING_FEATURE_FAMILIES\n"
        "from banking_fraud_lab.monitoring import (\n"
        "    check_feature_drift,\n"
        "    check_monitoring_data_quality,\n"
        "    check_score_drift,\n"
        "    decide_alerts,\n"
        "    inspect_alert_queue,\n"
        "    record_reviewer_action,\n"
        "    run_batch_scoring,\n"
        "    summarise_alert_operations,\n"
        ")\n"
        "from banking_fraud_lab.schema import PROTECTED_SCENARIO_ANSWER_KEYS\n"
        "\n"
        "pd.set_option(\"display.max_columns\", 40)"
    ),
    _md(
        "## Generate Learner-Facing Data And Fit The Baseline\n"
        "\n"
        "The supervised label comes from generated case outcomes for the private-banking "
        "Detection patterns. Protected answer keys stay separate from the learner-facing "
        "views. The modeling frame, the LogisticRegression baseline, and the per-row score "
        "are produced exactly as in the v0.7 interpretability notebook, so the monitoring "
        "flow below starts from the same reproducible score."
    ),
    _code(
        "tables = generate_private_banking_transaction_fraud_world(\n"
        "    seed=42,\n"
        "    scenario_prevalence=0.2,\n"
        ")\n"
        "learner_tables = build_learner_facing_views(tables)\n"
        "\n"
        "assert PROTECTED_SCENARIO_ANSWER_KEYS in tables\n"
        "assert PROTECTED_SCENARIO_ANSWER_KEYS not in learner_tables\n"
        "\n"
        "feature_frame = build_private_banking_features(learner_tables)\n"
        "\n"
        "model_frame = (\n"
        "    learner_tables[\"cases\"]\n"
        "    .merge(\n"
        "        learner_tables[\"alerts\"][\n"
        "            [\n"
        "                \"alert_id\",\n"
        "                \"alert_type\",\n"
        "                \"severity\",\n"
        "                \"reason\",\n"
        "                \"generated_at\",\n"
        "                \"alert_status\",\n"
        "            ]\n"
        "        ],\n"
        "        on=\"alert_id\",\n"
        "        how=\"inner\",\n"
        "    )\n"
        "    .merge(\n"
        "        learner_tables[\"case_outcomes\"]\n"
        "        [[\"case_id\", \"confirmed_fraud\", \"loss_amount_chf\"]],\n"
        "        on=\"case_id\",\n"
        "        how=\"inner\",\n"
        "    )\n"
        "    .merge(\n"
        "        feature_frame,\n"
        "        on=[\"transaction_id\", \"banking_relationship_id\"],\n"
        "        how=\"inner\",\n"
        "    )\n"
        ")\n"
        "assert model_frame[\"confirmed_fraud\"].nunique() == 2\n"
        "\n"
        "feature_output_columns = [\n"
        "    output_column\n"
        "    for spec in PRIVATE_BANKING_FEATURE_FAMILIES\n"
        "    for output_column in spec.output_columns\n"
        "]\n"
        "numeric_feature_columns = [\n"
        "    column\n"
        "    for column in feature_output_columns\n"
        "    if pd.api.types.is_numeric_dtype(model_frame[column])\n"
        "]\n"
        "assert numeric_feature_columns\n"
        "\n"
        "preprocess = ColumnTransformer(\n"
        "    [(\"numeric\", StandardScaler(), numeric_feature_columns)],\n"
        "    remainder=\"drop\",\n"
        ")\n"
        "baseline_model = Pipeline(\n"
        "    [\n"
        "        (\"preprocess\", preprocess),\n"
        "        (\n"
        "            \"model\",\n"
        "            LogisticRegression(\n"
        "                random_state=42,\n"
        "                solver=\"lbfgs\",\n"
        "                max_iter=1000,\n"
        "                class_weight=\"balanced\",\n"
        "            ),\n"
        "        ),\n"
        "    ]\n"
        ")\n"
        "target = model_frame[\"confirmed_fraud\"].astype(bool)\n"
        "baseline_model.fit(model_frame[numeric_feature_columns], target)\n"
        "\n"
        "model_frame = model_frame.assign(\n"
        "    score=baseline_model.predict_proba(\n"
        "        model_frame[numeric_feature_columns]\n"
        "    )[:, 1].round(6)\n"
        ")\n"
        "model_frame[\n"
        "    [\"alert_id\", \"alert_type\", \"banking_relationship_id\", \"confirmed_fraud\", \"score\"]\n"
        "].head()"
    ),
    _md(
        "## Choose The Threshold And Run Batch Scoring\n"
        "\n"
        "The threshold is sourced from the v0.7 cost-aware recommender (reused, not "
        "recomputed). The scored frame carries Banking relationship, transaction, and alert "
        "lineage so each monitoring score row traces back to a Client-facing record. "
        "`run_batch_scoring` materializes the production `score` and `threshold` tables for "
        "the `pb_high_value_movement` Detection pattern."
    ),
    _code(
        "alert_scores = pd.DataFrame(\n"
        "    {\"alert_id\": model_frame[\"alert_id\"], \"score\": model_frame[\"score\"]}\n"
        ")\n"
        "threshold_recommendation = recommend_lowest_cost_threshold(\n"
        "    cases=model_frame[[\"case_id\", \"alert_id\"]],\n"
        "    case_outcomes=learner_tables[\"case_outcomes\"],\n"
        "    alert_scores=alert_scores,\n"
        "    candidate_thresholds=(0.25, 0.5, 0.75),\n"
        "    alert_capacities=(5, 10, 25),\n"
        "    investigation_cost_chf=75.0,\n"
        "    false_positive_cost_chf=25.0,\n"
        "    missed_fraud_cost_chf=1_000.0,\n"
        ")\n"
        "recommended_threshold = threshold_recommendation[\"recommended_threshold\"]\n"
        "\n"
        "scored_frame = model_frame[\n"
        "    [\"score\", \"banking_relationship_id\", \"transaction_id\", \"alert_id\"]\n"
        "].copy()\n"
        "\n"
        "batch = run_batch_scoring(\n"
        "    scored_frame,\n"
        "    detection_pattern_id=\"pb_high_value_movement\",\n"
        "    threshold=recommended_threshold,\n"
        "    scorer=\"alpine-crest-logreg\",\n"
        "    score_version=\"0.8.0\",\n"
        "    evidence_ref=\"v0.7 recommend_lowest_cost_threshold\",\n"
        ")\n"
        "\n"
        "threshold_id = str(batch.threshold_rows[\"threshold_id\"].iloc[0])\n"
        "print(f\"batch_id={batch.batch_id} threshold_id={threshold_id}\")\n"
        "batch.score_rows.head()"
    ),
    _code("batch.threshold_rows"),
    _md(
        "## Decide Alerts Against The Threshold\n"
        "\n"
        "`decide_alerts` applies the chosen threshold to the score rows, writing "
        "`alert_decision` rows (`alert` vs `suppress`) and one `audit_event` row per decision. "
        "Each decision carries forward the score, threshold, and Banking relationship lineage."
    ),
    _code(
        "decisions = decide_alerts(\n"
        "    batch.score_rows,\n"
        "    threshold=recommended_threshold,\n"
        "    threshold_id=threshold_id,\n"
        ")\n"
        "\n"
        "decision_split = decisions.alert_decision_rows[\"decision\"].value_counts()\n"
        "decision_split"
    ),
    _code("decisions.alert_decision_rows.head()"),
    _md(
        "## Record A Reviewer Action With v0.7 Explanation Evidence\n"
        "\n"
        "Each alert_decision can carry a reviewer action whose evidence is a v0.7 feature-"
        "importance summary. Recording the action emits a second audit event per row, so the "
        "score → decision → reviewer-action chain is fully traceable. The evidence here is the "
        "top feature driver for `pb_high_value_movement` from the fitted baseline."
    ),
    _code(
        "importance = extract_feature_importance(\n"
        "    baseline_model,\n"
        "    numeric_feature_columns,\n"
        "    feature_frame=model_frame[numeric_feature_columns],\n"
        "    detection_pattern_id=\"pb_high_value_movement\",\n"
        ")\n"
        "top_row = importance.sort_values(\"native_importance\", ascending=False).iloc[0]\n"
        "top_feature = str(top_row[\"feature\"])\n"
        "top_native_importance = float(top_row[\"native_importance\"])\n"
        "\n"
        "reviewer_actions = record_reviewer_action(\n"
        "    decisions.alert_decision_rows,\n"
        "    reviewer=\"rm-analyst\",\n"
        "    action=\"confirm\",\n"
        "    rationale=\"Reviewed against high-value movement playbook.\",\n"
        "    evidence={\n"
        "        \"detection_pattern_id\": \"pb_high_value_movement\",\n"
        "        \"top_feature\": top_feature,\n"
        "        \"native_importance\": top_native_importance,\n"
        "    },\n"
        ")\n"
        "\n"
        "audit_chain_summary = pd.DataFrame(\n"
        "    [\n"
        "        {\n"
        "            \"score_rows\": len(batch.score_rows),\n"
        "            \"alert_decision_rows\": len(decisions.alert_decision_rows),\n"
        "            \"decision_audit_rows\": len(decisions.audit_rows),\n"
        "            \"reviewer_action_rows\": len(reviewer_actions.reviewer_action_rows),\n"
        "            \"reviewer_audit_rows\": len(reviewer_actions.audit_rows),\n"
        "        }\n"
        "    ]\n"
        ")\n"
        "audit_chain_summary"
    ),
    _code("reviewer_actions.reviewer_action_rows.head()"),
    _md(
        "## Inspect The Alpine Crest Alert Queue\n"
        "\n"
        "Enriching the alert_decision rows with the foundation Alert lifecycle fields "
        "(`generated_at`, `severity`, `alert_status`) and an `institution_name` turns the "
        "decision table into an inspectable queue. `inspect_alert_queue` ranks alerts by "
        "severity (high > medium > low), then `generated_at`, then `alert_id`, mirroring "
        "`sql/examples/04_progressive_alert_queue.sql`, and reports queue age against a fixed "
        "`now` (not a wall clock)."
    ),
    _code(
        "queue_input = decisions.alert_decision_rows.merge(\n"
        "    learner_tables[\"alerts\"]\n"
        "    [[\"alert_id\", \"generated_at\", \"severity\", \"alert_status\"]],\n"
        "    on=\"alert_id\",\n"
        "    how=\"inner\",\n"
        "    validate=\"many_to_one\",\n"
        ")\n"
        "queue_input[\"institution_name\"] = \"Alpine Crest Private Bank\"\n"
        "\n"
        "queue = inspect_alert_queue(\n"
        "    queue_input,\n"
        "    institution=\"Alpine Crest Private Bank\",\n"
        "    now=pd.Timestamp(\"2024-01-01\"),\n"
        ")\n"
        "queue[[\"alert_queue_rank\", \"alert_id\", \"severity\", \"alert_status\", \"alert_age_hours\"]]"
    ),
    _md(
        "## Summarise Operational Metrics\n"
        "\n"
        "`summarise_alert_operations` reports alert volume against capacity, the closure "
        "distribution by Alert status, and the Detection patterns in scope. Precision and "
        "recall are reused from the v0.7 `evaluate_alert_scores` result rather than "
        "recomputed, so the operational summary stays consistent with the evaluation layer."
    ),
    _code(
        "operations_input = decisions.alert_decision_rows.merge(\n"
        "    learner_tables[\"alerts\"][[\"alert_id\", \"alert_status\"]],\n"
        "    on=\"alert_id\",\n"
        "    how=\"inner\",\n"
        "    validate=\"many_to_one\",\n"
        ")\n"
        "operations_input[\"institution_name\"] = \"Alpine Crest Private Bank\"\n"
        "\n"
        "evaluation = evaluate_alert_scores(\n"
        "    cases=model_frame[[\"case_id\", \"alert_id\"]],\n"
        "    case_outcomes=learner_tables[\"case_outcomes\"],\n"
        "    alert_scores=alert_scores,\n"
        "    thresholds=(recommended_threshold,),\n"
        "    alert_capacity=10,\n"
        "    investigation_cost_chf=75.0,\n"
        "    false_positive_cost_chf=25.0,\n"
        "    missed_fraud_cost_chf=1_000.0,\n"
        ")\n"
        "\n"
        "operations_summary = summarise_alert_operations(\n"
        "    operations_input,\n"
        "    alert_capacity=10,\n"
        "    evaluation=evaluation,\n"
        ")\n"
        "pd.DataFrame([operations_summary])"
    ),
    _md(
        "## Score And Feature Drift\n"
        "\n"
        "Drift checks compare a reference window against a review window. The score-drift "
        "check flags a review when the mean shift exceeds a stated tolerance; the feature-"
        "drift check reports per-feature shift so a reviewer can see which input family moved. "
        "Here the review window is a controlled upward shift of the reference, simulating drift "
        "on synthetic data only."
    ),
    _code(
        "reference_scores = batch.score_rows[\"score\"]\n"
        "review_scores = (reference_scores + 0.2).clip(upper=1.0)\n"
        "\n"
        "score_drift = check_score_drift(\n"
        "    reference_scores,\n"
        "    review_scores,\n"
        "    tolerance=0.05,\n"
        ")\n"
        "pd.DataFrame([score_drift.__dict__])"
    ),
    _code(
        "reference_features = model_frame[numeric_feature_columns].reset_index(drop=True)\n"
        "review_features = reference_features.copy()\n"
        "drift_columns = numeric_feature_columns[:4]\n"
        "for column in drift_columns:\n"
        "    review_features[column] = review_features[column] + review_features[column].abs().mean()\n"
        "\n"
        "feature_drift = check_feature_drift(\n"
        "    reference_features,\n"
        "    review_features,\n"
        "    feature_columns=drift_columns,\n"
        ")\n"
        "feature_drift"
    ),
    _md(
        "## Monitoring Data-Quality\n"
        "\n"
        "`check_monitoring_data_quality` verifies the monitoring input frame has the required "
        "columns and wraps the generated-dataset quality report. The result references the "
        "v0.7 `data_quality` governance dimension and the `generate_dataset_quality_report` "
        "evidence source, so a finding maps onto the monitoring checklist."
    ),
    _code(
        "data_quality = check_monitoring_data_quality(\n"
        "    model_frame,\n"
        "    required_columns=[\"score\", \"banking_relationship_id\", \"confirmed_fraud\"],\n"
        ")\n"
        "pd.DataFrame(\n"
        "    [\n"
        "        {\n"
        "            \"dimension_id\": data_quality.dimension_id,\n"
        "            \"evidence_source\": data_quality.evidence_source,\n"
        "            \"row_count\": data_quality.row_count,\n"
        "            \"missing_required_columns\": list(data_quality.missing_required_columns),\n"
        "            \"passed\": data_quality.passed,\n"
        "        }\n"
        "    ]\n"
        ")"
    ),
    _md(
        "## Keep Monitoring Limits Visible\n"
        "\n"
        "Monitoring is a review prompt, not a verdict. The score, queue, and metrics above "
        "surface what to look at — they do not certify the model. Fraud labels are sparse, "
        "alert outcomes are operational decisions, and protected answer keys stay separate "
        "from learner-facing data. A reviewer still has to read the alert, the explanation, "
        "and the case context. **A model should not be judged by headline accuracy.**"
    ),
]


def build_notebook() -> dict:
    """Assemble the notebook JSON."""
    return {
        "cells": CELLS,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main() -> None:
    """Write the notebook to disk under notebooks/08_production_monitoring_patterns/."""
    NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
    NOTEBOOK_PATH.write_text(
        json.dumps(build_notebook(), indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {NOTEBOOK_PATH} ({len(CELLS)} cells)")


if __name__ == "__main__":
    main()
