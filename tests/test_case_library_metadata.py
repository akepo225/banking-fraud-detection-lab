"""Validation tests for pattern-linked case-library source packs."""

from __future__ import annotations

from pathlib import Path

CASE_SOURCE_PACK_DIR = Path("docs/cases/source_packs")
HITL_MARKER = "<!-- HITL-REVIEW-REQUIRED -->"
REQUIRED_METADATA_FIELDS = {
    "title",
    "status",
    "hitl_review_required",
    "v0_1_area",
    "track",
    "detection_pattern",
    "geography",
    "source_quality",
    "linked_modules",
}
REQUIRED_AREAS = {
    "private_banking_transaction_fraud",
    "digital_scam_to_mule",
    "regulatory_or_model_governance_method",
    "graph_or_network_pattern",
}
REQUIRED_SECTIONS = {
    "## Source Links",
    "## Public Facts",
    "## Interpretation For Detection Patterns",
    "## Likely Data Signals",
    "## Linked Modules And Exercises",
    "## Regulatory Hooks",
    "## Limitations",
    "## Human Review",
}


def test_case_source_packs_cover_v0_1_learning_areas() -> None:
    """The draft case library must cover each v0.1 source-pack area."""
    source_packs = _source_pack_paths()
    areas = {_metadata(path)["v0_1_area"] for path in source_packs}

    assert REQUIRED_AREAS <= areas


def test_case_source_packs_have_required_metadata_and_sections() -> None:
    """Each source pack must carry machine-readable metadata and required sections."""
    for path in _source_pack_paths():
        text = path.read_text(encoding="utf-8")
        metadata = _metadata(path)

        assert REQUIRED_METADATA_FIELDS <= set(metadata)
        assert metadata["status"] == "draft-hitl"
        assert metadata["hitl_review_required"] == "true"
        assert HITL_MARKER in text
        assert "https://" in text, f"{path} must include at least one source URL"
        missing_sections = REQUIRED_SECTIONS - set(_section_headings(text))
        assert not missing_sections, f"{path} is missing sections: {sorted(missing_sections)}"


def _source_pack_paths() -> tuple[Path, ...]:
    """Return source-pack markdown files, failing clearly if none exist."""
    paths = tuple(sorted(CASE_SOURCE_PACK_DIR.glob("*.md")))
    assert paths, f"No source packs found under {CASE_SOURCE_PACK_DIR}"
    return paths


def _metadata(path: Path) -> dict[str, str]:
    """Parse simple key-value front matter from a source-pack file."""
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path} is missing opening front matter"
    _, raw_front_matter, _ = text.split("---", maxsplit=2)
    metadata = {}
    for raw_line in raw_front_matter.splitlines():
        if not raw_line.strip() or ":" not in raw_line:
            continue
        key, value = raw_line.split(":", maxsplit=1)
        metadata[key.strip()] = value.strip()
    return metadata


def _section_headings(text: str) -> set[str]:
    """Extract level-two markdown section headings."""
    return {line.strip() for line in text.splitlines() if line.startswith("## ")}
