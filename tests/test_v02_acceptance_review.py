"""Tests for the v0.2 foundation acceptance review document."""

from pathlib import Path


REVIEW_PATH = Path("docs/release/v0.2-foundation-acceptance-review.md")


def test_v02_acceptance_review_has_hitl_boundary_and_evidence() -> None:
    """The v0.2 review must stay explicit about HITL status and command evidence."""
    review = REVIEW_PATH.read_text(encoding="utf-8")

    required_terms = [
        "Status: draft for human review.",
        "<!-- HITL-REVIEW-REQUIRED:",
        "Ready for human v0.2 acceptance review",
        "uv sync --extra dev",
        "uv run ruff check .",
        "uv run pytest tests/test_foundations_notebook.py",
        "tests/test_warmup_notebooks.py",
        "uv run pytest tests/test_sqlite_loader.py::test_representative_sql_examples_execute_successfully",
        "uv run python -m banking_fraud_lab.data_quality --scale tiny --scale small --scale medium --scale large",
        "uv run pytest",
        "167 passed",
        "gh run list --branch main --workflow CI --limit 5",
        "Prohibited-content and source-boundary scan",
    ]
    for term in required_terms:
        assert term in review


def test_v02_acceptance_review_maps_merged_prs_and_deferred_scope() -> None:
    """The review must map v0.2 implementation slices and future work explicitly."""
    review = REVIEW_PATH.read_text(encoding="utf-8")

    for issue_number, pr_number in [
        (59, 69),
        (60, 70),
        (61, 71),
        (62, 72),
        (63, 73),
        (64, 74),
        (65, 75),
    ]:
        assert f"Issue #{issue_number} / PR #{pr_number}" in review

    for follow_up_issue in range(46, 59):
        assert f"#{follow_up_issue}" in review

    assert "No new blocking v0.2 defect was identified" in review
    assert "No automatic next-version work was started" in review


def test_v02_acceptance_review_uses_glossary_and_boundary_terms() -> None:
    """The review should preserve repo vocabulary and source-boundary language."""
    review = REVIEW_PATH.read_text(encoding="utf-8")

    required_terms = [
        "Partner",
        "Client",
        "User",
        "Banking relationship",
        "Progressive data view",
        "Alert lifecycle",
        "Alpine Crest Private Bank",
        "NovaBank Digital",
        "real-client-data claim",
        "real-bank affiliation claim",
        "reconstruction claim",
        "legal-advice instruction",
    ]
    for term in required_terms:
        assert term in review
