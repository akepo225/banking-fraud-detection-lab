"""Generate the Alpine Crest interpretability + model-risk notebook (v0.7 #184).

Mirrors the generator-script convention used by the v0.6 graph notebooks: this
script emits the deterministic ``.ipynb`` JSON so the notebook content is
reproducible and reviewable as code. Regeneration is optional and manual — the
committed ``.ipynb`` is authoritative.

Run from the repo root::

    uv run python notebooks/07_interpretability_model_risk/_build_alpine_crest_interpretability_notebook.py
"""

from __future__ import annotations

import json
from pathlib import Path

# Resolve relative to this script so it works regardless of cwd.
NOTEBOOK_DIR = Path(__file__).resolve().parent
NOTEBOOK_PATH = NOTEBOOK_DIR / "alpine_crest_interpretability.ipynb"


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
        "# Alpine Crest Interpretability And Model Risk\n"
        "\n"
        "This notebook turns the v0.3 private-banking model outputs into inspectable "
        "explanations and a model-risk review for **Alpine Crest Private Bank**. It is "
        "the first of two v0.7 interpretability track notebooks and consumes the "
        "explanation utilities (slice 1), the threshold / false-positive utilities "
        "(slice 2), and the model-documentation template (slice 3).\n"
        "\n"
        "Learning goal: explain *why* a specific alert was generated, choose a threshold "
        "that reflects alert capacity and cost, review where false positives concentrate, "
        "and keep the limitation-aware framing visible — **a model should not be judged by "
        "headline accuracy**.\n"
        "\n"
        "> Educational exercise on synthetic data. No real Client, account, or "
        "transaction data; no certification or legal-advice claim."
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
        "    build_model_documentation,\n"
        "    build_partial_dependence_grid,\n"
        "    build_private_banking_features,\n"
        "    concentrate_false_positives,\n"
        "    evaluate_alert_scores,\n"
        "    extract_feature_importance,\n"
        "    generate_private_banking_transaction_fraud_world,\n"
        "    recommend_lowest_cost_threshold,\n"
        ")\n"
        "from banking_fraud_lab.features import PRIVATE_BANKING_FEATURE_FAMILIES\n"
        "from banking_fraud_lab.interpretability import PATTERN_TO_EXPLANATION_FAMILY\n"
        "from banking_fraud_lab.schema import PROTECTED_SCENARIO_ANSWER_KEYS\n"
        "\n"
        "pd.set_option(\"display.max_columns\", 40)"
    ),
    _md(
        "## Generate Learner-Facing Data\n"
        "\n"
        "The supervised label comes from generated case outcomes for the "
        "`pb_transaction_fraud` and `pb_high_value_movement` Detection patterns. "
        "Protected answer keys stay separate from the learner-facing views."
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
        "learner_summary = pd.DataFrame(\n"
        "    {\n"
        "        \"table\": [\"cases\", \"case_outcomes\", \"alerts\", \"transactions\"],\n"
        "        \"rows\": [\n"
        "            len(learner_tables[\"cases\"]),\n"
        "            len(learner_tables[\"case_outcomes\"]),\n"
        "            len(learner_tables[\"alerts\"]),\n"
        "            len(learner_tables[\"transactions\"]),\n"
        "        ],\n"
        "    }\n"
        ")\n"
        "learner_summary"
    ),
    _md(
        "## Build The Supervised Modeling Frame\n"
        "\n"
        "Join cases, alerts, outcomes, and the v0.3 private-banking feature frame into one "
        "modeling frame, then fit the same reproducible baseline used in the supervised "
        "baseline notebook so explanations are anchored to a real fitted model."
    ),
    _code(
        "feature_frame = build_private_banking_features(learner_tables)\n"
        "\n"
        "model_frame = (\n"
        "    learner_tables[\"cases\"][\n"
        "        [\"case_id\", \"alert_id\", \"transaction_id\", \"banking_relationship_id\"]\n"
        "    ]\n"
        "    .merge(\n"
        "        learner_tables[\"alerts\"][[\"alert_id\", \"alert_type\", \"severity\", \"reason\"]],\n"
        "        on=\"alert_id\",\n"
        "        how=\"inner\",\n"
        "        validate=\"one_to_one\",\n"
        "    )\n"
        "    .merge(\n"
        "        learner_tables[\"case_outcomes\"][\n"
        "            [\"case_id\", \"confirmed_fraud\", \"loss_amount_chf\"]\n"
        "        ],\n"
        "        on=\"case_id\",\n"
        "        how=\"inner\",\n"
        "        validate=\"one_to_one\",\n"
        "    )\n"
        "    .merge(\n"
        "        feature_frame,\n"
        "        on=[\"transaction_id\", \"banking_relationship_id\"],\n"
        "        how=\"inner\",\n"
        "        validate=\"one_to_one\",\n"
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
        "model_frame[[\"alert_id\", \"alert_type\", \"confirmed_fraud\", \"score\"]].head()"
    ),
    _md(
        "## Why Was This Alert Generated? Per-Alert Explanation\n"
        "\n"
        "Feature importance explains which inputs drove each alert's score. The "
        "`ExplanationFamilySpec` vocabulary ties every feature to its **Detection pattern** "
        "so the explanation is traceable to a pattern id, not a black box. Note that importance "
        "is an inspection aid, not proof the model is correct — a model should not be judged by "
        "headline accuracy."
    ),
    _code(
        "pb_high_value_spec = PATTERN_TO_EXPLANATION_FAMILY[\"pb_high_value_movement\"]\n"
        "pb_tx_fraud_spec = PATTERN_TO_EXPLANATION_FAMILY[\"pb_transaction_fraud\"]\n"
        "\n"
        "# Feature importance is global to the fitted model; a family groups a subset\n"
        "# of the model's columns, so we score over ALL numeric features and then\n"
        "# filter to each family's columns to read that pattern's drivers.\n"
        "global_importance = extract_feature_importance(\n"
        "    baseline_model,\n"
        "    numeric_feature_columns,\n"
        "    feature_frame=model_frame[numeric_feature_columns],\n"
        ")\n"
        "\n"
        "importance_overview = pd.concat(\n"
        "    [\n"
        "        global_importance[\n"
        "            global_importance[\"feature\"].isin(pb_high_value_spec.feature_columns)\n"
        "        ].assign(detection_pattern_id=\"pb_high_value_movement\"),\n"
        "        global_importance[\n"
        "            global_importance[\"feature\"].isin(pb_tx_fraud_spec.feature_columns)\n"
        "        ].assign(detection_pattern_id=\"pb_transaction_fraud\"),\n"
        "    ]\n"
        ")\n"
        "importance_overview.sort_values(\"native_importance\", ascending=False)"
    ),
    _md(
        "### Partial-Dependence Grid For The Top Driver\n"
        "\n"
        "A partial-dependence / ICE grid shows how the positive-class score moves as one "
        "feature is swept across its observed range — a compact view of the model's marginal "
        "behaviour, tied to the same Detection pattern id."
    ),
    _code(
        "top_feature = str(\n"
        "    importance_overview.sort_values(\"native_importance\", ascending=False)\n"
        "    .iloc[0][\"feature\"]\n"
        ")\n"
        "pd_grid = build_partial_dependence_grid(\n"
        "    baseline_model,\n"
        "    model_frame[numeric_feature_columns],\n"
        "    top_feature,\n"
        "    grid_points=7,\n"
        "    detection_pattern_id=\"pb_high_value_movement\",\n"
        ")\n"
        "pd_grid"
    ),
    _md(
        "## Compare Rule, Model, Graph, And Case Evidence\n"
        "\n"
        "Private-banking alerts draw on four signal types. Keeping them side by side reminds "
        "reviewers that a model score is one signal among several, and that the v0.6 graph "
        "(`circular_funds_movement`) and v0.5 case narratives add context the score alone "
        "does not capture.\n"
        "\n"
        "| Signal type | v0.x source | What it adds to a private-banking alert |\n"
        "|---|---|---|\n"
        "| Rule | v0.1 alert generator | Deterministic trigger thresholds (amount, velocity). |\n"
        "| Model | v0.3 supervised baseline | Calibrated score from engineered features. |\n"
        "| Graph | v0.6 `circular_funds_movement` | Network cycles / bridge nodes across Partners. |\n"
        "| Case | v0.5 Alpine Crest narrative | Investigator reasoning and outcome. |"
    ),
    _code(
        "signal_evidence = pd.DataFrame(\n"
        "    [\n"
        "        {\n"
        "            \"alert_id\": row[\"alert_id\"],\n"
        "            \"alert_type\": row[\"alert_type\"],\n"
        "            \"model_score\": row[\"score\"],\n"
        "            \"rule_triggered\": row[\"alert_type\"] in {\n"
        "                \"private_banking_high_value\",\n"
        "                \"private_banking_transaction_fraud\",\n"
        "            },\n"
        "            \"graph_pattern\": \"circular_funds_movement\"\n"
        "            if row[\"alert_type\"] == \"private_banking_high_value\"\n"
        "            else None,\n"
        "        }\n"
        "        for _, row in model_frame.head(8).iterrows()\n"
        "    ]\n"
        ")\n"
        "signal_evidence"
    ),
    _md(
        "## Threshold Selection With Capacity And Costs\n"
        "\n"
        "Thresholds are an operational decision: a low threshold raises recall but overloads "
        "investigators and inflates false-positive cost. The recommender sweeps alert capacity "
        "and the investigation / false-positive / missed-fraud costs so the chosen threshold "
        "reflects those tradeoffs rather than a default."
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
        "\n"
        "recommendation_overview = pd.DataFrame(\n"
        "    [\n"
        "        {\n"
        "            \"alert_capacity\": capacity,\n"
        "            \"lowest_cost_threshold\": entry[\"lowest_cost_threshold\"],\n"
        "            \"total_cost_chf\": entry[\"lowest_cost_summary\"][\"total_cost_chf\"],\n"
        "            \"recall\": entry[\"lowest_cost_summary\"][\"recall\"],\n"
        "        }\n"
        "        for capacity, entry in threshold_recommendation[\"per_capacity\"].items()\n"
        "    ]\n"
        ")\n"
        "recommendation_overview"
    ),
    _md(
        "## False-Positive Concentration Review\n"
        "\n"
        "Where do false positives fall? Grouping by `alert_type` and Banking relationship "
        "shows whether review burden is spread evenly or concentrated on one segment — a "
        "review prompt, not a fairness verdict."
    ),
    _code(
        "fp_concentration = concentrate_false_positives(\n"
        "    cases=model_frame[[\"case_id\", \"alert_id\"]],\n"
        "    case_outcomes=learner_tables[\"case_outcomes\"],\n"
        "    alert_scores=alert_scores,\n"
        "    threshold=threshold_recommendation[\"recommended_threshold\"],\n"
        "    segment_columns=[\"alert_type\"],\n"
        "    alerts=learner_tables[\"alerts\"],\n"
        ")\n"
        "fp_concentration"
    ),
    _md(
        "## Model Documentation\n"
        "\n"
        "The frozen template fills every required section (purpose, data lineage, assumptions, "
        "limitations, monitoring needs) deterministically from the fitted model, producing a "
        "stakeholder-readable artifact for the governance memo."
    ),
    _code(
        "documentation = build_model_documentation(\n"
        "    baseline_model,\n"
        "    institution=\"Alpine Crest Private Bank\",\n"
        "    detection_pattern_id=\"pb_high_value_movement\",\n"
        "    feature_columns=numeric_feature_columns,\n"
        "    model_frame=model_frame,\n"
        "    seed=42,\n"
        "    cost_parameters={\n"
        "        \"investigation_cost_chf\": 75.0,\n"
        "        \"false_positive_cost_chf\": 25.0,\n"
        "        \"missed_fraud_cost_chf\": 1_000.0,\n"
        "    },\n"
        ")\n"
        "\n"
        "documentation_sections = pd.DataFrame(\n"
        "    [\n"
        "        {\n"
        "            \"section\": section[\"display_name\"],\n"
        "            \"text\": section[\"text\"],\n"
        "        }\n"
        "        for section in documentation[\"sections\"].values()\n"
        "    ]\n"
        ")\n"
        "documentation_sections"
    ),
    _md(
        "## Keep Evaluation Limits Visible\n"
        "\n"
        "Headline accuracy is out of scope: fraud labels are sparse, alert outcomes are "
        "operational decisions, and protected answer keys stay separate from learner-facing "
        "data. Explanations are inspection aids, not proof of correctness. **A model should "
        "not be judged by headline accuracy.**"
    ),
    _code(
        "report = evaluate_alert_scores(\n"
        "    cases=model_frame[[\"case_id\", \"alert_id\"]],\n"
        "    case_outcomes=learner_tables[\"case_outcomes\"],\n"
        "    alert_scores=alert_scores,\n"
        "    thresholds=(threshold_recommendation[\"recommended_threshold\"],),\n"
        "    alert_capacity=10,\n"
        "    investigation_cost_chf=75.0,\n"
        "    false_positive_cost_chf=25.0,\n"
        "    missed_fraud_cost_chf=1_000.0,\n"
        ")\n"
        "assert \"accuracy is out of scope\" in report[\"limitation_summary\"]\n"
        "pd.DataFrame(\n"
        "    [\n"
        "        {\n"
        "            \"metric\": \"limitation_summary\",\n"
        "            \"value\": report[\"limitation_summary\"],\n"
        "        }\n"
        "    ]\n"
        ")"
    ),
    _md(
        "## Optional SHAP Explanation\n"
        "\n"
        "SHAP is an optional explainability tool, kept behind the `shap` extra so it does not "
        "add dependency cost to the core curriculum or CI. When the extra is installed, the cell "
        "below shows a SHAP-based feature ranking; when it is absent, the cell prints a skip "
        "message and the notebook continues. SHAP is a complementary view, not a requirement."
    ),
    _code(
        "from banking_fraud_lab import SHAP_AVAILABLE, explain_with_shap\n"
        "\n"
        "if SHAP_AVAILABLE:\n"
        "    shap_explanation = explain_with_shap(\n"
        "        baseline_model,\n"
        "        model_frame[numeric_feature_columns],\n"
        "        numeric_feature_columns,\n"
        "        detection_pattern_id=\"pb_high_value_movement\",\n"
        "    )\n"
        "    print(shap_explanation)\n"
        "else:\n"
        "    print(\n"
        "        \"SHAP optional extra not installed; skipping SHAP explanation. \"\n"
        "        \"Install with `uv sync --extra shap` to view SHAP rankings.\"\n"
        "    )"
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
    """Write the notebook to disk under notebooks/07_interpretability_model_risk/."""
    NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
    NOTEBOOK_PATH.write_text(
        json.dumps(build_notebook(), indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {NOTEBOOK_PATH} ({len(CELLS)} cells)")


if __name__ == "__main__":
    main()
