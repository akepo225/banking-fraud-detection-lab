"""Interpretability utilities and frozen explanation-family vocabulary.

Mirrors the frozen-spec precedent of :mod:`banking_fraud_lab.schema` and
:mod:`banking_fraud_lab.graph.features_spec`. The frozen
:class:`ExplanationFamilySpec` vocabulary lives in :mod:`.spec`; the deterministic
explainers live in :mod:`.explanations`.
"""

from __future__ import annotations

from banking_fraud_lab.interpretability.explanations import (
    build_partial_dependence_grid,
    explain_feature_family,
    extract_feature_importance,
)
from banking_fraud_lab.interpretability.shap_explainer import (
    SHAP_AVAILABLE,
    explain_with_shap,
)
from banking_fraud_lab.interpretability.spec import (
    DB_NEW_BENEFICIARY_EXPLANATION,
    DB_SCAM_TO_MULE_EXPLANATION,
    DB_SESSION_VELOCITY_EXPLANATION,
    EXPLANATION_FAMILY_IDS,
    EXPLANATION_FAMILY_SPECS,
    ExplanationFamilySpec,
    PATTERN_TO_EXPLANATION_FAMILY,
    PB_HIGH_VALUE_EXPLANATION,
    PB_TRANSACTION_FRAUD_EXPLANATION,
)

__all__ = [
    "DB_NEW_BENEFICIARY_EXPLANATION",
    "DB_SCAM_TO_MULE_EXPLANATION",
    "DB_SESSION_VELOCITY_EXPLANATION",
    "EXPLANATION_FAMILY_IDS",
    "EXPLANATION_FAMILY_SPECS",
    "ExplanationFamilySpec",
    "PATTERN_TO_EXPLANATION_FAMILY",
    "PB_HIGH_VALUE_EXPLANATION",
    "PB_TRANSACTION_FRAUD_EXPLANATION",
    "SHAP_AVAILABLE",
    "build_partial_dependence_grid",
    "explain_feature_family",
    "explain_with_shap",
    "extract_feature_importance",
]
