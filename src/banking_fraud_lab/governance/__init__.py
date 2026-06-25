"""Model-documentation template and validation/monitoring checklist vocabulary.

Mirrors the frozen-spec precedent of :mod:`banking_fraud_lab.schema` and
:mod:`banking_fraud_lab.graph.features_spec`. The frozen section/dimension
vocabulary lives in :mod:`.spec`; the deterministic fillable builders live in
:mod:`.template`.
"""

from __future__ import annotations

from banking_fraud_lab.governance.spec import (
    DOC_ASSUMPTIONS,
    DOC_DATA_LINEAGE,
    DOC_LIMITATIONS,
    DOC_MONITORING_NEEDS,
    DOC_PURPOSE,
    MODEL_DOCUMENTATION_SECTION_IDS,
    MODEL_DOCUMENTATION_SECTIONS,
    MON_DATA_QUALITY,
    MON_DRIFT,
    MON_FP_CONCENTRATION,
    MON_SEGMENT,
    MON_STABILITY,
    MONITORING_CHECKLIST_DIMENSION_IDS,
    MONITORING_CHECKLIST_DIMENSIONS,
    ModelDocumentationSectionSpec,
    MonitoringChecklistDimensionSpec,
    REQUIRED_DOCUMENTATION_SECTION_IDS,
    REQUIRED_MONITORING_DIMENSION_IDS,
)
from banking_fraud_lab.governance.template import (
    build_model_documentation,
    build_monitoring_checklist,
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
    "build_model_documentation",
    "build_monitoring_checklist",
]
