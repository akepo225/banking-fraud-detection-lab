"""Deterministic model-documentation and monitoring-checklist builders.

Provides two fillable, deterministic builders that turn a fitted model and its
evaluation outputs into a structured model-documentation artifact and a
validation/monitoring checklist, following the frozen template/dimension
vocabulary in :mod:`banking_fraud_lab.governance.spec`.

Outputs are plain dictionaries (JSON-serialisable) so they can be rendered into
a governance memo or persisted without coupling to a specific document format.
Every required section/dimension is present and filled, so a learner can hand a
fitted model + model frame to :func:`build_model_documentation` and read back a
documentation artifact ready for the governance memo (slice 6).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import pandas as pd

from banking_fraud_lab.governance.spec import (
    MODEL_DOCUMENTATION_SECTIONS,
    MONITORING_CHECKLIST_DIMENSIONS,
    ModelDocumentationSectionSpec,
    REQUIRED_DOCUMENTATION_SECTION_IDS,
    REQUIRED_MONITORING_DIMENSION_IDS,
)

# Glossary terms used verbatim in generated documentation text so reviewers see
# the repo's fixed vocabulary (Client / User / Banking relationship).
_INSTITUTIONS = ("Alpine Crest Private Bank", "NovaBank Digital")


def build_model_documentation(
    model: Any,
    *,
    institution: str,
    detection_pattern_id: str,
    feature_columns: Sequence[str],
    model_frame: pd.DataFrame | None = None,
    seed: int | None = None,
    scale: str | None = None,
    estimator_summary: str | None = None,
    cost_parameters: Mapping[str, float] | None = None,
    extra_section_text: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Build a structured, frozen-section model documentation artifact.

    Fills every required section from
    :data:`MODEL_DOCUMENTATION_SECTIONS` deterministically from the fitted
    ``model`` and the supplied context, so the output is reproducible across
    runs for the same inputs.

    Args:
        model: A fitted classifier or Pipeline. Used to derive a default
            estimator summary when ``estimator_summary`` is not given.
        institution: The synthetic institution name; must be one of Alpine Crest
            Private Bank or NovaBank Digital (glossary institutions).
        detection_pattern_id: The Detection pattern id this model scores (from
            :data:`banking_fraud_lab.schema.PATTERN_IDS`).
        feature_columns: The feature columns the model was trained on; recorded
            in the data-lineage section.
        model_frame: Optional training frame used to record row/column counts in
            data lineage.
        seed: Optional generator seed recorded for reproducibility.
        scale: Optional dataset scale recorded for reproducibility.
        estimator_summary: Optional human-readable estimator description (e.g.
            ``"LogisticRegression(class_weight='balanced')"``). Derived from the
            model when omitted.
        cost_parameters: Optional cost-model parameters (investigation / false-
            positive / missed-fraud CHF) recorded in assumptions.
        extra_section_text: Optional mapping of section_id to additional text to
            APPEND to a section's generated text (e.g. bespoke limitations).

    Returns:
        A dict with keys ``institution``, ``detection_pattern_id``, ``sections``
        (a dict of section_id -> ``{display_name, description, guidance, text}``),
        and ``metadata`` (estimator_summary, feature_columns, row_count,
        column_count, seed, scale, cost_parameters). Every required section is
        present and non-empty.

    Raises:
        ValueError: If ``institution`` is not one of the glossary institutions,
            or if ``extra_section_text`` references an unknown section id.
    """
    if institution not in _INSTITUTIONS:
        raise ValueError(
            f"institution must be one of {_INSTITUTIONS}; got {institution!r}"
        )
    extra = dict(extra_section_text or {})
    unknown_sections = sorted(set(extra) - REQUIRED_DOCUMENTATION_SECTION_IDS)
    if unknown_sections:
        raise ValueError(
            f"extra_section_text references unknown sections: {unknown_sections}"
        )

    resolved_estimator = estimator_summary or _summarise_estimator(model)
    feature_list = list(feature_columns)
    lineage_text = _data_lineage_text(
        feature_list=feature_list,
        model_frame=model_frame,
        seed=seed,
        scale=scale,
    )
    assumptions_text = _assumptions_text(
        resolved_estimator=resolved_estimator,
        cost_parameters=cost_parameters,
    )

    sections: dict[str, dict[str, Any]] = {}
    for spec in MODEL_DOCUMENTATION_SECTIONS:
        generated = _section_text(
            spec=spec,
            institution=institution,
            detection_pattern_id=detection_pattern_id,
            lineage_text=lineage_text,
            assumptions_text=assumptions_text,
        )
        appended = extra.get(spec.section_id)
        text = generated if not appended else f"{generated}\n\n{appended}"
        sections[spec.section_id] = {
            "display_name": spec.display_name,
            "description": spec.description,
            "guidance": spec.guidance,
            "text": text,
        }

    metadata = {
        "estimator_summary": resolved_estimator,
        "feature_columns": feature_list,
        "row_count": int(len(model_frame)) if model_frame is not None else None,
        "column_count": int(len(model_frame.columns))
        if model_frame is not None
        else None,
        "seed": seed,
        "scale": scale,
        "cost_parameters": dict(cost_parameters) if cost_parameters else None,
    }
    return {
        "institution": institution,
        "detection_pattern_id": detection_pattern_id,
        "sections": sections,
        "metadata": metadata,
    }


def build_monitoring_checklist(
    *,
    institution: str,
    detection_pattern_id: str,
    evaluation: Mapping[str, Any] | None = None,
    false_positive_concentration: pd.DataFrame | None = None,
    score_series: pd.Series | None = None,
    review_window_scores: pd.Series | None = None,
    extra_dimension_text: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Build a structured validation/monitoring checklist.

    Fills every required dimension from
    :data:`MONITORING_CHECKLIST_DIMENSIONS` deterministically from the supplied
    evaluation outputs so a learner can read off drift, stability, FP
    concentration, segment, and data-quality review items for a fitted model.

    Args:
        institution: The synthetic institution name (Alpine Crest Private Bank or
            NovaBank Digital).
        detection_pattern_id: The Detection pattern id the checklist covers.
        evaluation: Optional output of :func:`evaluate_alert_scores` used to fill
            the stability dimension (precision/recall/PR-AUC + lowest-cost
            threshold).
        false_positive_concentration: Optional output of
            :func:`concentrate_false_positives` used to fill the FP-concentration
            dimension with the top segments.
        score_series: Optional training-window alert scores used for the drift
            baseline.
        review_window_scores: Optional later-window alert scores; when both this
            and ``score_series`` are given, the drift dimension reports the
            mean-score shift.
        extra_dimension_text: Optional mapping of dimension_id to additional text
            to APPEND to that dimension's generated text.

    Returns:
        A dict with keys ``institution``, ``detection_pattern_id``, ``dimensions``
        (a dict of dimension_id -> ``{display_name, description, guidance,
        evidence_source, text, status}``), where ``status`` is one of
        ``"review"``, ``"ok"``, or ``"not_applicable"``. Every required dimension
        is present.

    Raises:
        ValueError: If ``institution`` is not a glossary institution, or if
            ``extra_dimension_text`` references an unknown dimension id.
    """
    if institution not in _INSTITUTIONS:
        raise ValueError(
            f"institution must be one of {_INSTITUTIONS}; got {institution!r}"
        )
    extra = dict(extra_dimension_text or {})
    unknown_dimensions = sorted(set(extra) - REQUIRED_MONITORING_DIMENSION_IDS)
    if unknown_dimensions:
        raise ValueError(
            f"extra_dimension_text references unknown dimensions: {unknown_dimensions}"
        )

    drift_text, drift_status = _drift_text(
        score_series=score_series, review_window_scores=review_window_scores
    )
    stability_text, stability_status = _stability_text(evaluation=evaluation)
    fp_text, fp_status = _fp_concentration_text(
        concentration=false_positive_concentration
    )

    dimension_fill: dict[str, tuple[str, str]] = {
        "score_drift": (drift_text, drift_status),
        "metric_stability": (stability_text, stability_status),
        "false_positive_concentration": (fp_text, fp_status),
        "segment_review": (
            _segment_text(institution=institution, detection_pattern_id=detection_pattern_id),
            "review",
        ),
        "data_quality": (_data_quality_text(evaluation=evaluation), "review"),
    }

    dimensions: dict[str, dict[str, Any]] = {}
    for spec in MONITORING_CHECKLIST_DIMENSIONS:
        base_text, status = dimension_fill[spec.dimension_id]
        appended = extra.get(spec.dimension_id)
        text = base_text if not appended else f"{base_text}\n\n{appended}"
        dimensions[spec.dimension_id] = {
            "display_name": spec.display_name,
            "description": spec.description,
            "guidance": spec.guidance,
            "evidence_source": spec.evidence_source,
            "text": text,
            "status": status,
        }
    return {
        "institution": institution,
        "detection_pattern_id": detection_pattern_id,
        "dimensions": dimensions,
    }


# --- Internal text builders -----------------------------------------------


def _summarise_estimator(model: Any) -> str:
    """Return a short human-readable summary of a fitted estimator."""
    estimator = model.steps[-1][1] if hasattr(model, "steps") else model
    class_name = type(estimator).__name__
    parts: list[str] = [class_name]
    for attr in ("solver", "max_iter", "criterion"):
        value = getattr(estimator, attr, None)
        if value is not None:
            parts.append(f"{attr}={value!r}")
    if getattr(estimator, "class_weight", None) is not None:
        parts.append(f"class_weight={estimator.class_weight!r}")
    if hasattr(estimator, "random_state") and getattr(estimator, "random_state") is not None:
        parts.append(f"random_state={estimator.random_state!r}")
    return ", ".join(parts)


def _data_lineage_text(
    *,
    feature_list: list[str],
    model_frame: pd.DataFrame | None,
    seed: int | None,
    scale: str | None,
) -> str:
    """Compose the data-lineage section text deterministically."""
    lines = [
        "Inputs are synthetic generated tables (transactions, alerts, cases, "
        "case_outcomes) joined through the foundation Progressive views; no real "
        "Client or User data is used.",
        f"Feature columns ({len(feature_list)}): {', '.join(feature_list)}.",
    ]
    if model_frame is not None:
        lines.append(
            f"Training frame: {len(model_frame)} rows x {len(model_frame.columns)} columns."
        )
    reproducibility = []
    if seed is not None:
        reproducibility.append(f"seed={seed}")
    if scale is not None:
        reproducibility.append(f"scale={scale!r}")
    if reproducibility:
        lines.append("Reproducibility: " + ", ".join(reproducibility) + ".")
    return "\n".join(lines)


def _assumptions_text(
    *,
    resolved_estimator: str,
    cost_parameters: Mapping[str, float] | None,
) -> str:
    """Compose the assumptions section text deterministically."""
    lines = [f"Estimator: {resolved_estimator}."]
    lines.append(
        "Confirmed-fraud labels are generated outcomes, not ground truth, and are "
        "sparse; class weighting (when used) is an assumption, not a correction."
    )
    if cost_parameters:
        cost_text = ", ".join(f"{key}={value}" for key, value in cost_parameters.items())
        lines.append(f"Alert-decision cost model: {cost_text}.")
    return "\n".join(lines)


def _section_text(
    *,
    spec: ModelDocumentationSectionSpec,
    institution: str,
    detection_pattern_id: str,
    lineage_text: str,
    assumptions_text: str,
) -> str:
    """Dispatch to the per-section text generator."""
    if spec.section_id == "purpose":
        return (
            f"{institution} model scoring the {detection_pattern_id} Detection "
            "pattern, intended to inform alert review inside the Alert lifecycle "
            "for a learner exercise. It is not deployed to production and carries "
            "no certification or compliance claim."
        )
    if spec.section_id == "data_lineage":
        return lineage_text
    if spec.section_id == "assumptions":
        return assumptions_text
    if spec.section_id == "limitations":
        return (
            "Headline accuracy is out of scope: fraud labels are sparse, alert "
            "outcomes are operational decisions, and protected answer keys stay "
            "separate from learner-facing data. Feature-importance and partial-"
            "dependence explanations are inspection aids, not proof of "
            "correctness. False-positive concentration is a review prompt, not a "
            "fairness verdict."
        )
    if spec.section_id == "monitoring_needs":
        return (
            "Watch this model against the monitoring-checklist dimensions: score "
            "drift, metric stability, false-positive concentration, segment "
            "review, and data quality. Re-review the chosen threshold and alert "
            "capacity periodically as generated populations evolve."
        )
    return spec.description


def _drift_text(
    *,
    score_series: pd.Series | None,
    review_window_scores: pd.Series | None,
) -> tuple[str, str]:
    """Compose the score-drift dimension text and status."""
    if score_series is None or score_series.empty:
        return (
            "No training-window scores supplied; provide score_series to "
            "establish the drift baseline.",
            "not_applicable",
        )
    baseline_mean = float(score_series.mean())
    if review_window_scores is not None and review_window_scores.empty:
        return (
            f"Training-window mean alert score: {baseline_mean:.4f}. Review "
            "window has no scores yet, so drift is not measurable.",
            "not_applicable",
        )
    if review_window_scores is None:
        return (
            f"Training-window mean alert score: {baseline_mean:.4f}. Supply "
            "review_window_scores to measure drift against this baseline.",
            "review",
        )
    review_mean = float(review_window_scores.mean())
    shift = review_mean - baseline_mean
    status = "ok" if abs(shift) < 0.05 else "review"
    return (
        f"Training-window mean alert score: {baseline_mean:.4f}; review-window "
        f"mean: {review_mean:.4f}; shift: {shift:+.4f}. "
        + ("Within the 0.05 drift tolerance." if status == "ok"
           else "Exceeds the 0.05 drift tolerance — review inputs."),
        status,
    )


def _stability_text(*, evaluation: Mapping[str, Any] | None) -> tuple[str, str]:
    """Compose the metric-stability dimension text and status."""
    if evaluation is None:
        return (
            "No evaluation output supplied; pass the result of "
            "evaluate_alert_scores to inspect precision/recall/PR-AUC stability "
            "across thresholds.",
            "not_applicable",
        )
    pr_auc = evaluation.get("pr_auc")
    summaries = evaluation.get("threshold_summaries", [])
    if not summaries:
        return ("Evaluation has no threshold summaries.", "not_applicable")
    precisions = [s["precision"] for s in summaries]
    recalls = [s["recall"] for s in summaries]
    precision_spread = max(precisions) - min(precisions) if precisions else 0.0
    recall_spread = max(recalls) - min(recalls) if recalls else 0.0
    lowest_cost = evaluation.get("lowest_cost_threshold")
    status = "ok" if precision_spread < 0.5 and recall_spread < 0.5 else "review"
    return (
        f"PR-AUC: {pr_auc:.4f}. Precision spread across thresholds: "
        f"{precision_spread:.4f}; recall spread: {recall_spread:.4f}. "
        f"Lowest-cost threshold: {lowest_cost}. "
        + ("Metrics are stable across thresholds." if status == "ok"
           else "Metrics swing sharply across thresholds — review threshold choice."),
        status,
    )


def _fp_concentration_text(
    *, concentration: pd.DataFrame | None
) -> tuple[str, str]:
    """Compose the false-positive-concentration dimension text and status."""
    if concentration is None:
        return (
            "No false-positive concentration output supplied; run "
            "concentrate_false_positives to surface where review burden falls.",
            "not_applicable",
        )
    if concentration.empty:
        return (
            "The supplied false-positive concentration output is empty, so no "
            "segment concentration needs review for this window.",
            "ok",
        )
    top = concentration.iloc[0]
    top_share = float(top["false_positive_share"])
    status = "review" if top_share >= 0.5 else "ok"
    segment_columns = [c for c in concentration.columns if c not in {
        "false_positive_count", "false_positive_share", "alerted_count",
        "false_positive_rate",
    }]
    segment_label = ", ".join(f"{c}={top[c]}" for c in segment_columns)
    return (
        f"Top false-positive segment ({segment_label}) carries "
        f"{top_share:.1%} of false positives ({int(top['false_positive_count'])} "
        f"of the total). " + ("Disproportionate concentration — review." if status == "review"
                              else "No single segment dominates false positives."),
        status,
    )


def _segment_text(*, institution: str, detection_pattern_id: str) -> str:
    """Compose the segment-review dimension text."""
    return (
        f"Group {institution} alerts by Detection track and alert_type around the "
        f"{detection_pattern_id} pattern and compare alert and confirmation "
        "rates. Treat segment differences as review prompts for the operations "
        "team, not as fairness verdicts on Client or User cohorts."
    )


def _data_quality_text(*, evaluation: Mapping[str, Any] | None) -> str:
    """Compose the data-quality dimension text."""
    base = (
        "Confirm feature columns are non-null and within expected ranges, "
        "confirmed_fraud labels are well-formed booleans, and any "
        "loss_amount_chf values are non-negative. Use "
        "generate_dataset_quality_report where a quality report is available."
    )
    if evaluation is not None:
        population = evaluation.get("population")
        if population:
            return (
                f"{base} Evaluation population: "
                f"{population.get('case_count')} cases, "
                f"{population.get('confirmed_fraud_count')} confirmed fraud."
            )
    return base


__all__ = [
    "build_model_documentation",
    "build_monitoring_checklist",
]
