"""Frozen model-documentation template and monitoring-checklist vocabulary.

Mirrors the frozen-spec precedent set by :mod:`banking_fraud_lab.schema`
(``PatternSpec`` / ``PATTERN_IDS``) and
:mod:`banking_fraud_lab.graph.features_spec` (``GraphFeatureFamilySpec``).

The template defines the required sections a fraud-detection model must be
documented against (purpose, data lineage, assumptions, limitations, monitoring
needs) so a learner can produce a structured, stakeholder-readable model
documentation artifact for both Alpine Crest Private Bank and NovaBank Digital
models. The monitoring-checklist vocabulary defines the validation/monitoring
dimensions (drift, stability, false-positive concentration, segment, data
quality) the companion :mod:`banking_fraud_lab.governance.template` builder
fills deterministically from a fitted model and its evaluation outputs.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelDocumentationSectionSpec:
    """Structured metadata for one required model-documentation section."""

    section_id: str
    display_name: str
    description: str
    guidance: str


@dataclass(frozen=True)
class MonitoringChecklistDimensionSpec:
    """Structured metadata for one monitoring/validation checklist dimension."""

    dimension_id: str
    display_name: str
    description: str
    guidance: str
    #: The evaluation/model signal this dimension draws on, named so reviewers
    #: can trace a checklist item back to a v0.7 utility (e.g.
    #: ``concentrate_false_positives`` or ``evaluate_alert_scores``).
    evidence_source: str


# --- Model documentation sections ------------------------------------------
# The five required sections follow the SR 11-7 documentation expectation and the
# PRD's model-documentation template deliverable: purpose, data lineage,
# assumptions, limitations, and monitoring needs.

DOC_PURPOSE = ModelDocumentationSectionSpec(
    section_id="purpose",
    display_name="Purpose and intended use",
    description=(
        "States what the model is for, which Detection pattern it supports, and "
        "the decisions it is intended to inform inside the Alert lifecycle."
    ),
    guidance=(
        "Name the institution (Alpine Crest Private Bank or NovaBank Digital), "
        "the Detection pattern id the model scores, and the alert decision it "
        "feeds. Keep intended use scoped to the learner exercise; do not claim "
        "production deployment or certification."
    ),
)

DOC_DATA_LINEAGE = ModelDocumentationSectionSpec(
    section_id="data_lineage",
    display_name="Data lineage",
    description=(
        "Records the generated tables, feature families, and seed used to build "
        "the training frame so the model inputs are reproducible."
    ),
    guidance=(
        "List the source generated tables (transactions, alerts, cases, "
        "outcomes), the feature-family ids consumed, and the generator seed and "
        "scale. Note that inputs are synthetic and not real Client or User data."
    ),
)

DOC_ASSUMPTIONS = ModelDocumentationSectionSpec(
    section_id="assumptions",
    display_name="Assumptions",
    description=(
        "Lists the modelling assumptions (score distribution, cost model, label "
        "reliability) so reviewers can see where the model's behaviour is "
        "conditioned on choices rather than data."
    ),
    guidance=(
        "Capture the estimator family (e.g. LogisticRegression), the class-"
        "weight handling, the threshold-selection assumptions, and the cost "
        "parameters (investigation, false-positive, missed-fraud) the alert "
        "decision is evaluated against."
    ),
)

DOC_LIMITATIONS = ModelDocumentationSectionSpec(
    section_id="limitations",
    display_name="Limitations",
    description=(
        "Surfaces what the model cannot do, anchoring the 'a model should not be "
        "judged by headline accuracy' framing the v0.7 module teaches."
    ),
    guidance=(
        "State that headline accuracy is out of scope (sparse labels, operational "
        "alert outcomes), that explanations are not proof of correctness, and "
        "that segment concentration is a review prompt rather than a fairness "
        "verdict."
    ),
)

DOC_MONITORING_NEEDS = ModelDocumentationSectionSpec(
    section_id="monitoring_needs",
    display_name="Monitoring needs",
    description=(
        "Points to the monitoring/checklist dimensions the model must be watched "
        "against after deployment so drift, stability, and concentration are "
        "tracked."
    ),
    guidance=(
        "Reference the monitoring-checklist dimensions (drift, stability, "
        "false-positive concentration, segment, data quality) and any threshold "
        "or capacity the operations team should re-review periodically."
    ),
)

MODEL_DOCUMENTATION_SECTIONS: tuple[ModelDocumentationSectionSpec, ...] = (
    DOC_PURPOSE,
    DOC_DATA_LINEAGE,
    DOC_ASSUMPTIONS,
    DOC_LIMITATIONS,
    DOC_MONITORING_NEEDS,
)

MODEL_DOCUMENTATION_SECTION_IDS: tuple[str, ...] = tuple(
    section.section_id for section in MODEL_DOCUMENTATION_SECTIONS
)

#: Required sections as a set, for the fill-validation guard.
REQUIRED_DOCUMENTATION_SECTION_IDS: frozenset[str] = frozenset(
    MODEL_DOCUMENTATION_SECTION_IDS
)


# --- Monitoring / validation checklist dimensions --------------------------
# The five dimensions follow the PRD's validation/monitoring checklist deliverable:
# drift, stability, false-positive concentration, segment, and data quality.

MON_DRIFT = MonitoringChecklistDimensionSpec(
    dimension_id="score_drift",
    display_name="Score drift",
    description=(
        "Checks whether the alert-score distribution has shifted between the "
        "training window and a later review window, signalling that model inputs "
        "may be moving away from the population it was calibrated on."
    ),
    guidance=(
        "Compare the mean and spread of alert scores across windows; flag a "
        "drift review when the shift exceeds a stated tolerance."
    ),
    evidence_source="alert_scores",
)

MON_STABILITY = MonitoringChecklistDimensionSpec(
    dimension_id="metric_stability",
    display_name="Metric stability",
    description=(
        "Checks whether precision, recall, and PR-AUC stay stable across "
        "thresholds and review windows, so the model's alert behaviour is not "
        "sensitive to small input changes."
    ),
    guidance=(
        "Inspect the threshold summaries and cost curve from "
        "evaluate_alert_scores; flag instability when precision or recall swing "
        "sharply across neighbouring thresholds."
    ),
    evidence_source="evaluate_alert_scores",
)

MON_FP_CONCENTRATION = MonitoringChecklistDimensionSpec(
    dimension_id="false_positive_concentration",
    display_name="False-positive concentration",
    description=(
        "Checks whether false positives concentrate by alert_type, track, or "
        "Banking relationship, so review burden and potential segment effects "
        "are visible rather than averaged away."
    ),
    guidance=(
        "Run concentrate_false_positives by segment and review the highest-share "
        "groups; flag any segment carrying a disproportionate false-positive "
        "share for human review."
    ),
    evidence_source="concentrate_false_positives",
)

MON_SEGMENT = MonitoringChecklistDimensionSpec(
    dimension_id="segment_review",
    display_name="Segment review",
    description=(
        "Checks alert and outcome rates by Detection track and segment so the "
        "model's behaviour is reviewed per Client/User/Banking-relationship "
        "cohort, not just in aggregate."
    ),
    guidance=(
        "Group alerts by track and alert_type; compare alert and confirmation "
        "rates. Treat differences as review prompts, not fairness verdicts."
    ),
    evidence_source="alerts",
)

MON_DATA_QUALITY = MonitoringChecklistDimensionSpec(
    dimension_id="data_quality",
    display_name="Data quality",
    description=(
        "Checks the completeness and validity of the inputs feeding the model "
        "(feature columns, labels, money fields) so a degradation upstream does "
        "not silently distort scores."
    ),
    guidance=(
        "Confirm required feature columns are non-null and within expected "
        "ranges, confirmed_fraud labels are well-formed, and any "
        "loss_amount_chf values are non-negative. Use generate_dataset_quality_"
        "report where applicable."
    ),
    evidence_source="generate_dataset_quality_report",
)

MONITORING_CHECKLIST_DIMENSIONS: tuple[MonitoringChecklistDimensionSpec, ...] = (
    MON_DRIFT,
    MON_STABILITY,
    MON_FP_CONCENTRATION,
    MON_SEGMENT,
    MON_DATA_QUALITY,
)

MONITORING_CHECKLIST_DIMENSION_IDS: tuple[str, ...] = tuple(
    dimension.dimension_id for dimension in MONITORING_CHECKLIST_DIMENSIONS
)

#: Required dimensions as a set, for the fill-validation guard.
REQUIRED_MONITORING_DIMENSION_IDS: frozenset[str] = frozenset(
    MONITORING_CHECKLIST_DIMENSION_IDS
)


__all__ = [
    "DOC_ASSUMPTIONS",
    "DOC_DATA_LINEAGE",
    "DOC_LIMITATIONS",
    "DOC_MONITORING_NEEDS",
    "DOC_PURPOSE",
    "MODEL_DOCUMENTATION_SECTION_IDS",
    "MODEL_DOCUMENTATION_SECTIONS",
    "MON_DATA_QUALITY",
    "MON_DRIFT",
    "MON_FP_CONCENTRATION",
    "MON_SEGMENT",
    "MON_STABILITY",
    "MONITORING_CHECKLIST_DIMENSION_IDS",
    "MONITORING_CHECKLIST_DIMENSIONS",
    "ModelDocumentationSectionSpec",
    "MonitoringChecklistDimensionSpec",
    "REQUIRED_DOCUMENTATION_SECTION_IDS",
    "REQUIRED_MONITORING_DIMENSION_IDS",
]
