"""Generate the Alpine Crest capstone scoring notebook (v0.9 #227).

Mirrors the generator-script convention used by the v0.6–v0.8 notebooks: this
script emits the deterministic ``.ipynb`` JSON so the notebook content is
reproducible and reviewable as code. Regeneration is optional and manual — the
committed ``.ipynb`` is authoritative.

The capstone notebook reuses — does NOT reimplement — the v0.3 private-banking
feature library, ``evaluate_alert_scores``, ``recommend_lowest_cost_threshold``,
and the v0.7 interpretability surface, run on the v0.9 capstone dataset (#225).

Run from the repo root::

    uv run python notebooks/09_capstone/_build_alpine_crest_capstone_scoring_notebook.py
"""

from __future__ import annotations

import json
from pathlib import Path

NOTEBOOK_DIR = Path(__file__).resolve().parent
NOTEBOOK_PATH = NOTEBOOK_DIR / "alpine_crest_capstone_scoring.ipynb"


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
        "# Alpine Crest Capstone Scoring, Alert Review, And Interpretability\n"
        "\n"
        "This is the v0.9 capstone notebook for the **Private-banking fraud detection** track "
        "at **Alpine Crest Private Bank**. It runs the full capstone loop from the scenario "
        "brief: generate the capstone dataset, build the engineered feature frame, fit a "
        "transparent scoring rule, review alerts with alert-aware metrics, choose a "
        "capacity-aware threshold, and explain *why* each alert fired — without leaving the "
        "capstone flow.\n"
        "\n"
        "It reuses the v0.3 private-banking feature library, the v0.1 alert-aware evaluation, "
        "the capacity-aware threshold recommender, and the v0.7 per-alert explanations. The "
        "investigation targets the `pb_high_value_movement` and `pb_transaction_fraud` "
        "**Detection patterns** over the capstone substrate. Graph evidence "
        "(`circular_funds_movement`) is investigative support and is covered in the synthesis "
        "notebook.\n"
        "\n"
        "Learning goal: experience the integrated end-to-end path while keeping the limitation-"
        "aware framing visible — **a model should not be judged by headline accuracy**.\n"
        "\n"
        "> Educational exercise on synthetic data. No real Client, account, or transaction "
        "data; no certification or legal-advice claim. The repository is pre-publication; "
        "v0.9 is a beta review point."
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
        "    concentrate_false_positives,\n"
        "    evaluate_alert_scores,\n"
        "    extract_feature_importance,\n"
        "    generate_capstone_private_banking_world,\n"
        "    recommend_lowest_cost_threshold,\n"
        ")\n"
        "from banking_fraud_lab.features import PRIVATE_BANKING_FEATURE_FAMILIES\n"
        "from banking_fraud_lab.interpretability import PATTERN_TO_EXPLANATION_FAMILY\n"
        "from banking_fraud_lab.schema import PROTECTED_SCENARIO_ANSWER_KEYS\n"
        "\n"
        "pd.set_option(\"display.max_columns\", 40)"
    ),
    _md(
        "## Generate The Capstone Dataset\n"
        "\n"
        "The capstone uses a fixed seed and scale so every later step builds on one shared "
        "substrate. The supervised label comes from generated case outcomes for the "
        "`pb_transaction_fraud` and `pb_high_value_movement` Detection patterns. Protected "
        "answer keys stay separate from the learner-facing views so investigation work is not "
        "solved by inspecting labels."
    ),
    _code(
        "tables = generate_capstone_private_banking_world(seed=42)\n"
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
        "modeling frame, then fit a reproducible logistic-regression baseline on the engineered "
        "features. The feature columns come from the frozen `FeatureFamilySpec` vocabulary so "
        "the model is traceable to its Detection patterns."
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
        "## Alert-Aware Evaluation\n"
        "\n"
        "Alert-aware metrics report precision, recall, PR-AUC, alert volume, capacity use, and "
        "cost — never headline accuracy. Confirmed-fraud labels in the protected answer key are "
        "imperfect by design, so no single metric is the ground truth. The limitation summary "
        "keeps that framing visible."
    ),
    _code(
        "alert_scores = pd.DataFrame(\n"
        "    {\"alert_id\": model_frame[\"alert_id\"], \"score\": model_frame[\"score\"]}\n"
        ")\n"
        "report = evaluate_alert_scores(\n"
        "    cases=model_frame[[\"case_id\", \"alert_id\"]],\n"
        "    case_outcomes=learner_tables[\"case_outcomes\"],\n"
        "    alert_scores=alert_scores,\n"
        "    thresholds=(0.25, 0.5, 0.75),\n"
        "    alert_capacity=10,\n"
        "    investigation_cost_chf=75.0,\n"
        "    false_positive_cost_chf=25.0,\n"
        "    missed_fraud_cost_chf=1_000.0,\n"
        ")\n"
        "assert \"accuracy is out of scope\" in report[\"limitation_summary\"]\n"
        "\n"
        "metrics_overview = pd.DataFrame(\n"
        "    [\n"
        "        {\"metric\": \"pr_auc\", \"value\": report[\"pr_auc\"]},\n"
        "        {\"metric\": \"limitation_summary\", \"value\": report[\"limitation_summary\"]},\n"
        "    ]\n"
        ")\n"
        "metrics_overview"
    ),
    _md(
        "## Capacity-Aware Threshold Selection\n"
        "\n"
        "Thresholds are an operational decision. The recommender sweeps alert capacity and the "
        "investigation / false-positive / missed-fraud costs so the chosen threshold reflects "
        "those tradeoffs rather than a default."
    ),
    _code(
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
        "## Per-Alert Explanation: Why Was This Alert Generated?\n"
        "\n"
        "Feature importance explains which inputs drove each alert's score. The "
        "`ExplanationFamilySpec` vocabulary ties every feature to its **Detection pattern** so "
        "the explanation is traceable to a pattern id, not a black box. Importance is an "
        "inspection aid, not proof the model is correct."
    ),
    _code(
        "pb_high_value_spec = PATTERN_TO_EXPLANATION_FAMILY[\"pb_high_value_movement\"]\n"
        "pb_tx_fraud_spec = PATTERN_TO_EXPLANATION_FAMILY[\"pb_transaction_fraud\"]\n"
        "\n"
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
        "## False-Positive Concentration Review\n"
        "\n"
        "Where do false positives fall? Grouping by `alert_type` shows whether review burden is "
        "spread evenly or concentrated on one segment — a review prompt, not a fairness verdict."
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
        "## Capstone Takeaways\n"
        "\n"
        "This notebook ran the full private-banking capstone loop on the v0.9 capstone dataset: "
        "data generation, engineered features, a fitted scoring rule, alert-aware metrics, a "
        "capacity-aware threshold, a per-alert explanation, and a false-positive review. The "
        "synthesis notebook adds graph (`circular_funds_movement`) and case evidence as "
        "investigative support and renders the governance memo for both tracks.\n"
        "\n"
        "**A model should not be judged by headline accuracy.** Fraud labels are sparse, alert "
        "outcomes are operational decisions, and protected answer keys stay separate from "
        "learner-facing data."
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
    """Write the notebook to disk under notebooks/09_capstone/."""
    NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
    NOTEBOOK_PATH.write_text(
        json.dumps(build_notebook(), indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {NOTEBOOK_PATH} ({len(CELLS)} cells)")


if __name__ == "__main__":
    main()
