"""Tests for package-level imports and version."""

from banking_fraud_lab import (
    EDGE_CATEGORY_IDS,
    EDGE_SPECS,
    EDGE_TYPE_IDS,
    EXPLANATION_FAMILY_IDS,
    EXPLANATION_FAMILY_SPECS,
    FEATURE_FAMILY_IDS,
    FOUNDATION_PROGRESSIVE_VIEW_SPECS,
    GRAPH_FEATURE_FAMILIES,
    GRAPH_FEATURE_FAMILY_IDS,
    NODE_SPECS,
    NODE_TYPE_IDS,
    PRIVATE_BANKING_FEATURE_FAMILIES,
    DatasetQualityReport,
    EdgeSpec,
    ExplanationFamilySpec,
    FeatureFamilySpec,
    GraphFeatureFamilySpec,
    NodeSpec,
    ProgressiveViewSpec,
    __version__,
    build_all_graph_features,
    build_banking_graph,
    build_bridge_node_features,
    build_centrality_features,
    build_community_features,
    build_connected_component_features,
    build_node_degree_features,
    build_path_length_features,
    build_partial_dependence_grid,
    build_learner_facing_views,
    build_foundation_progressive_views,
    build_private_banking_features,
    calculate_amount_to_aum_features,
    calculate_amount_to_baseline_features,
    calculate_cross_border_features,
    calculate_new_counterparty_features,
    calculate_off_hours_features,
    calculate_rm_concentration_features,
    calculate_velocity_features,
    create_minimal_banking_world_sqlite,
    evaluate_alert_scores,
    explain_feature_family,
    extract_feature_importance,
    generate_dataset_quality_report,
    generate_digital_scam_to_mule_world,
    generate_learner_facing_digital_scam_to_mule_world,
    generate_learner_facing_private_banking_transaction_fraud_world,
    generate_learner_facing_minimal_banking_world,
    generate_minimal_banking_world,
    generate_private_banking_transaction_fraud_world,
    inject_digital_scam_to_mule_flow,
    inject_private_banking_transaction_fraud,
    join_graph_features_to_view,
    load_tables_to_sqlite,
)


def test_package_imports() -> None:
    """The package must expose the correct version and a callable generator."""
    assert __version__ == "0.1.0"
    assert FEATURE_FAMILY_IDS
    assert FOUNDATION_PROGRESSIVE_VIEW_SPECS
    assert PRIVATE_BANKING_FEATURE_FAMILIES
    assert DatasetQualityReport
    assert FeatureFamilySpec
    assert GraphFeatureFamilySpec
    assert NodeSpec
    assert EdgeSpec
    assert ExplanationFamilySpec
    assert ProgressiveViewSpec
    assert EDGE_CATEGORY_IDS
    assert EDGE_SPECS
    assert EDGE_TYPE_IDS
    assert GRAPH_FEATURE_FAMILIES
    assert GRAPH_FEATURE_FAMILY_IDS
    assert EXPLANATION_FAMILY_IDS
    assert EXPLANATION_FAMILY_SPECS
    assert NODE_SPECS
    assert NODE_TYPE_IDS
    assert callable(generate_minimal_banking_world)
    assert callable(build_all_graph_features)
    assert callable(build_banking_graph)
    assert callable(build_bridge_node_features)
    assert callable(build_centrality_features)
    assert callable(build_community_features)
    assert callable(build_connected_component_features)
    assert callable(build_node_degree_features)
    assert callable(build_path_length_features)
    assert callable(build_partial_dependence_grid)
    assert callable(extract_feature_importance)
    assert callable(explain_feature_family)
    assert callable(join_graph_features_to_view)
    assert callable(build_learner_facing_views)
    assert callable(build_foundation_progressive_views)
    assert callable(build_private_banking_features)
    assert callable(calculate_amount_to_aum_features)
    assert callable(calculate_amount_to_baseline_features)
    assert callable(calculate_cross_border_features)
    assert callable(calculate_new_counterparty_features)
    assert callable(calculate_off_hours_features)
    assert callable(calculate_rm_concentration_features)
    assert callable(calculate_velocity_features)
    assert callable(generate_digital_scam_to_mule_world)
    assert callable(generate_learner_facing_digital_scam_to_mule_world)
    assert callable(generate_learner_facing_private_banking_transaction_fraud_world)
    assert callable(generate_learner_facing_minimal_banking_world)
    assert callable(create_minimal_banking_world_sqlite)
    assert callable(generate_private_banking_transaction_fraud_world)
    assert callable(inject_digital_scam_to_mule_flow)
    assert callable(inject_private_banking_transaction_fraud)
    assert callable(load_tables_to_sqlite)
    assert callable(evaluate_alert_scores)
    assert callable(generate_dataset_quality_report)
