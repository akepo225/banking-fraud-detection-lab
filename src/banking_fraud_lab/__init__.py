"""Banking Fraud Detection Lab package."""

from banking_fraud_lab.generators import (
    SCALE_PROFILES,
    DatasetScaleProfile,
    build_learner_facing_views,
    generate_digital_fraud_scenarios_world,
    generate_digital_scam_to_mule_world,
    generate_learner_facing_digital_fraud_scenarios_world,
    generate_learner_facing_digital_scam_to_mule_world,
    generate_learner_facing_private_banking_transaction_fraud_world,
    generate_learner_facing_minimal_banking_world,
    generate_minimal_banking_world,
    generate_private_banking_transaction_fraud_world,
    inject_digital_fraud_scenarios,
    inject_digital_scam_to_mule_flow,
    inject_private_banking_transaction_fraud,
)
from banking_fraud_lab.progressive_views import (
    FOUNDATION_PROGRESSIVE_VIEW_SPECS,
    ProgressiveViewSpec,
    build_foundation_progressive_views,
)
from banking_fraud_lab.sqlite_loader import (
    create_minimal_banking_world_sqlite,
    load_tables_to_sqlite,
)
from banking_fraud_lab.evaluation import evaluate_alert_scores
from banking_fraud_lab.features import (
    FEATURE_FAMILY_IDS,
    PRIVATE_BANKING_FEATURE_FAMILIES,
    FeatureFamilySpec,
    build_private_banking_features,
    calculate_amount_to_aum_features,
    calculate_amount_to_baseline_features,
    calculate_cross_border_features,
    calculate_new_counterparty_features,
    calculate_off_hours_features,
    calculate_rm_concentration_features,
    calculate_velocity_features,
)

__all__ = [
    "FEATURE_FAMILY_IDS",
    "FOUNDATION_PROGRESSIVE_VIEW_SPECS",
    "PRIVATE_BANKING_FEATURE_FAMILIES",
    "FeatureFamilySpec",
    "ProgressiveViewSpec",
    "SCALE_PROFILES",
    "DatasetScaleProfile",
    "DatasetQualityReport",
    "__version__",
    "build_foundation_progressive_views",
    "build_learner_facing_views",
    "build_private_banking_features",
    "calculate_amount_to_aum_features",
    "calculate_amount_to_baseline_features",
    "calculate_cross_border_features",
    "calculate_new_counterparty_features",
    "calculate_off_hours_features",
    "calculate_rm_concentration_features",
    "calculate_velocity_features",
    "create_minimal_banking_world_sqlite",
    "evaluate_alert_scores",
    "generate_dataset_quality_report",
    "generate_digital_fraud_scenarios_world",
    "generate_digital_scam_to_mule_world",
    "generate_learner_facing_digital_fraud_scenarios_world",
    "generate_learner_facing_digital_scam_to_mule_world",
    "generate_learner_facing_private_banking_transaction_fraud_world",
    "generate_learner_facing_minimal_banking_world",
    "generate_minimal_banking_world",
    "generate_private_banking_transaction_fraud_world",
    "inject_digital_fraud_scenarios",
    "inject_digital_scam_to_mule_flow",
    "inject_private_banking_transaction_fraud",
    "load_tables_to_sqlite",
]

__version__ = "0.1.0"


def __getattr__(name: str):
    """Lazy-load the data-quality API so module CLI execution stays warning-free."""
    if name == "DatasetQualityReport":
        from banking_fraud_lab.data_quality import DatasetQualityReport

        return DatasetQualityReport
    if name == "generate_dataset_quality_report":
        from banking_fraud_lab.data_quality import generate_dataset_quality_report

        return generate_dataset_quality_report
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
