"""Validation tests for pattern-linked case-library source packs."""

from __future__ import annotations

from pathlib import Path
import re

CASE_SOURCE_PACK_DIR = Path("docs/cases/source_packs")
CASE_LIBRARY_INDEX = Path("docs/cases/index.md")
HITL_MARKER = "<!-- HITL-REVIEW-REQUIRED -->"
REQUIRED_METADATA_FIELDS = {
    "title",
    "status",
    "hitl_review_required",
    "v0_1_area",
    "track",
    "detection_pattern",
    "institution_type",
    "source_authority",
    "geography",
    "product",
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
BANNED_IMPERATIVE_PATTERNS = (
    r"\byou must\b",
    r"\bmust comply\b",
    r"\bmust report\b",
    r"\brequired to comply\b",
    r"\blegal requirement for learners\b",
)


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
        for field_name in REQUIRED_METADATA_FIELDS:
            assert metadata[field_name], f"{path} has empty metadata field: {field_name}"
        assert metadata["status"] == "draft-hitl"
        assert metadata["hitl_review_required"] == "true"
        assert HITL_MARKER in text
        assert "https://" in text, f"{path} must include at least one source URL"
        missing_sections = REQUIRED_SECTIONS - set(_section_headings(text))
        assert not missing_sections, f"{path} is missing sections: {sorted(missing_sections)}"


def test_case_source_pack_source_links_are_structured() -> None:
    """Source URLs must be listed in the source-link section, not only elsewhere."""
    for path in _source_pack_paths():
        source_link_section = _section_text(path.read_text(encoding="utf-8"), "## Source Links")

        assert "https://" in source_link_section, f"{path} has no HTTPS URL under Source Links"


def test_case_source_pack_metadata_links_existing_modules() -> None:
    """Machine-readable linked modules should point to existing v0.1 artifacts."""
    for path in _source_pack_paths():
        metadata = _metadata(path)
        linked_modules = [
            linked_module.strip()
            for linked_module in metadata["linked_modules"].split(",")
            if linked_module.strip().startswith("notebooks/")
        ]

        assert linked_modules, f"{path} has no notebook paths in linked_modules"
        for linked_module in linked_modules:
            assert Path(linked_module).exists(), f"{path} links missing module: {linked_module}"


def test_case_library_index_links_all_source_packs() -> None:
    """The case-library index must expose every draft source pack."""
    index_text = CASE_LIBRARY_INDEX.read_text(encoding="utf-8")

    for path in _source_pack_paths():
        relative_path = path.as_posix().removeprefix("docs/cases/")
        assert f"]({relative_path})" in index_text, f"Index does not link {relative_path}"


def test_case_source_packs_avoid_imperative_compliance_wording() -> None:
    """Source packs should support learning without issuing compliance instructions."""
    for path in _source_pack_paths():
        text = path.read_text(encoding="utf-8").lower()
        for pattern in BANNED_IMPERATIVE_PATTERNS:
            assert not re.search(pattern, text), f"{path} contains banned wording: {pattern}"


def test_case_source_packs_do_not_include_direct_quote_blocks() -> None:
    """Draft source packs should avoid direct quotation unless human review approves excerpts."""
    for path in _source_pack_paths():
        text = path.read_text(encoding="utf-8")

        assert not any(line.startswith(">") for line in text.splitlines()), (
            f"{path} contains a direct quote block"
        )


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


def _section_text(text: str, heading: str) -> str:
    """Return the body of one level-two markdown section."""
    lines = text.splitlines()
    section_lines: list[str] = []
    in_section = False
    for line in lines:
        if line.strip() == heading:
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section:
            section_lines.append(line)
    return "\n".join(section_lines)
