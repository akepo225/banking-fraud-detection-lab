"""Tests for package-level imports and version."""

from banking_fraud_lab import (
    FOUNDATION_PROGRESSIVE_VIEW_SPECS,
    DatasetQualityReport,
    ProgressiveViewSpec,
    __version__,
    build_learner_facing_views,
    build_foundation_progressive_views,
    create_minimal_banking_world_sqlite,
    evaluate_alert_scores,
    generate_dataset_quality_report,
    generate_digital_scam_to_mule_world,
    generate_learner_facing_digital_scam_to_mule_world,
    generate_learner_facing_private_banking_transaction_fraud_world,
    generate_learner_facing_minimal_banking_world,
    generate_minimal_banking_world,
    generate_private_banking_transaction_fraud_world,
    inject_digital_scam_to_mule_flow,
    inject_private_banking_transaction_fraud,
    load_tables_to_sqlite,
)


def test_package_imports() -> None:
    """The package must expose the correct version and a callable generator."""
    assert __version__ == "0.1.0"
    assert FOUNDATION_PROGRESSIVE_VIEW_SPECS
    assert DatasetQualityReport
    assert ProgressiveViewSpec
    assert callable(generate_minimal_banking_world)
    assert callable(build_learner_facing_views)
    assert callable(build_foundation_progressive_views)
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
