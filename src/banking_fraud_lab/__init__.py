"""Banking Fraud Detection Lab package."""

from banking_fraud_lab.generators import (
    build_learner_facing_views,
    generate_learner_facing_minimal_banking_world,
    generate_minimal_banking_world,
)

__all__ = [
    "__version__",
    "build_learner_facing_views",
    "generate_learner_facing_minimal_banking_world",
    "generate_minimal_banking_world",
]

__version__ = "0.1.0"
