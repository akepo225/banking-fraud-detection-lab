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
    DIGITAL_BANKING_FEATURE_FAMILIES,
    FEATURE_FAMILY_IDS,
    PRIVATE_BANKING_FEATURE_FAMILIES,
    FeatureFamilySpec,
    build_digital_banking_features,
    build_private_banking_features,
    calculate_amount_to_aum_features,
    calculate_amount_to_baseline_features,
    calculate_cross_border_features,
    calculate_db_account_age_features,
    calculate_db_beneficiary_novelty_features,
    calculate_db_pass_through_features,
    calculate_db_payment_velocity_features,
    calculate_db_risky_channel_features,
    calculate_db_session_risk_features,
    calculate_db_shared_device_features,
    calculate_new_counterparty_features,
    calculate_off_hours_features,
    calculate_rm_concentration_features,
    calculate_velocity_features,
)
from banking_fraud_lab.graph import (
    EDGE_CATEGORY_IDS,
    EDGE_SPECS,
    EDGE_TYPE_IDS,
    EdgeSpec,
    GRAPH_FEATURE_FAMILIES,
    GRAPH_FEATURE_FAMILY_IDS,
    GraphFeatureFamilySpec,
    NODE_SPECS,
    NODE_TYPE_IDS,
    NodeSpec,
    build_all_graph_features,
    build_banking_graph,
    build_bridge_node_features,
    build_centrality_features,
    build_community_features,
    build_connected_component_features,
    build_node_degree_features,
    build_path_length_features,
    join_graph_features_to_view,
)

__all__ = [
    "DIGITAL_BANKING_FEATURE_FAMILIES",
    "EDGE_CATEGORY_IDS",
    "EDGE_SPECS",
    "EDGE_TYPE_IDS",
    "FEATURE_FAMILY_IDS",
    "FOUNDATION_PROGRESSIVE_VIEW_SPECS",
    "GRAPH_FEATURE_FAMILIES",
    "GRAPH_FEATURE_FAMILY_IDS",
    "PRIVATE_BANKING_FEATURE_FAMILIES",
    "EdgeSpec",
    "FeatureFamilySpec",
    "GraphFeatureFamilySpec",
    "NodeSpec",
    "NODE_SPECS",
    "NODE_TYPE_IDS",
    "ProgressiveViewSpec",
    "SCALE_PROFILES",
    "DatasetScaleProfile",
    "DatasetQualityReport",
    "__version__",
    "build_all_graph_features",
    "build_banking_graph",
    "build_bridge_node_features",
    "build_centrality_features",
    "build_community_features",
    "build_connected_component_features",
    "build_digital_banking_features",
    "build_foundation_progressive_views",
    "build_learner_facing_views",
    "build_node_degree_features",
    "build_path_length_features",
    "build_private_banking_features",
    "calculate_amount_to_aum_features",
    "calculate_amount_to_baseline_features",
    "calculate_cross_border_features",
    "calculate_db_account_age_features",
    "calculate_db_beneficiary_novelty_features",
    "calculate_db_pass_through_features",
    "calculate_db_payment_velocity_features",
    "calculate_db_risky_channel_features",
    "calculate_db_session_risk_features",
    "calculate_db_shared_device_features",
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
    "join_graph_features_to_view",
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
