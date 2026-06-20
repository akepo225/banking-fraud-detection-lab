"""Tests for regulatory source-note structure and safety wording."""

import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

from banking_fraud_lab.schema import PATTERN_IDS
from private_banking_test_constants import (
    DIGITAL_V0_4_MODULE_PREFIX,
    DIGITAL_V0_4_PATTERN_IDS,
    PRIVATE_BANKING_V0_3_MODULE_PREFIX,
    PRIVATE_BANKING_V0_3_PATTERN_IDS,
)


REGULATORY_INDEX = Path("docs/regulation/index.md")
SOURCE_NOTE_DIR = Path("docs/regulation/source_notes")

REQUIRED_SOURCE_FAMILIES = {
    "swiss_amla",
    "swiss_amlo",
    "finma",
    "app_scam_payment",
    "fatf_typologies",
    "model_risk_governance",
}
REQUIRED_SECTIONS = (
    "## Source Scope",
    "## Official Sources",
    "## Learning Implications",
    "## Linked Exercises",
    "## Human Review",
)
ALLOWED_OFFICIAL_DOMAINS = {
    "fedlex.admin.ch",
    "finma.ch",
    "psr.org.uk",
    "fatf-gafi.org",
    "federalreserve.gov",
}
BANNED_IMPERATIVE_PATTERNS = (
    r"\byou must\b",
    r"\bmust comply\b",
    r"\bmust report\b",
    r"\brequired to comply\b",
    r"\blegal requirement for learners\b",
)


def test_regulatory_index_declares_educational_non_advice_scope() -> None:
    """The top-level index must state the educational, non-advisory boundary."""
    text = REGULATORY_INDEX.read_text(encoding="utf-8")
    normalized = text.lower()

    assert "educational" in normalized
    assert "not legal or compliance advice" in normalized
    for note_path in _source_note_paths():
        assert note_path.name in text


def test_regulatory_index_links_all_source_notes() -> None:
    """The regulatory index must link every draft source note."""
    index_text = REGULATORY_INDEX.read_text(encoding="utf-8")

    for note_path in _source_note_paths():
        relative_path = note_path.as_posix().removeprefix("docs/regulation/")
        assert f"]({relative_path})" in index_text, f"Index does not link {relative_path}"


def test_regulatory_notes_cover_required_source_families_and_official_links() -> None:
    """Draft notes must cover each v0.1 family and use official HTTPS source links."""
    covered_families: set[str] = set()

    for note_path in _source_note_paths():
        metadata, _body = _read_note(note_path)
        families = set(metadata["source_families"])
        urls = metadata["primary_official_sources"]

        assert metadata["status"] == "draft-hitl"
        assert metadata["hitl_review_required"] == "true"
        assert families
        assert urls
        assert all(url.startswith("https://") for url in urls)
        assert all(_is_allowed_official_domain(url) for url in urls)

        covered_families.update(families)

    assert REQUIRED_SOURCE_FAMILIES <= covered_families


def test_regulatory_notes_have_required_sections_and_hitl_marker() -> None:
    """Each source note must keep the same learner-facing safety structure."""
    for note_path in _source_note_paths():
        _metadata, body = _read_note(note_path)
        normalized = body.lower()

        assert "<!-- HITL-REVIEW-REQUIRED -->" in body
        assert "educational use only" in normalized
        assert "not legal or compliance advice" in normalized
        for section in REQUIRED_SECTIONS:
            assert section in body, f"{note_path} is missing {section}"


def test_regulatory_notes_list_metadata_sources_in_official_sources_section() -> None:
    """Official source URLs should be visible in the learner-facing source section."""
    for note_path in _source_note_paths():
        metadata, body = _read_note(note_path)
        official_sources_section = _section_text(body, "## Official Sources")
        urls = metadata["primary_official_sources"]

        assert isinstance(urls, list)
        for url in urls:
            assert url in official_sources_section, f"{note_path} does not list {url}"


def test_regulatory_learning_implications_are_substantive() -> None:
    """Learning implications should contain original learner-facing analysis."""
    for note_path in _source_note_paths():
        _metadata, body = _read_note(note_path)
        learning_implications = _section_text(body, "## Learning Implications")
        word_count = len(re.findall(r"\b\w+\b", learning_implications))

        assert word_count >= 40, f"{note_path} has thin learning implications"


def test_regulatory_notes_link_existing_exercises() -> None:
    """Regulatory notes must connect source material to real notebooks."""
    for note_path in _source_note_paths():
        metadata, _body = _read_note(note_path)
        linked_modules = _linked_modules(metadata)

        assert linked_modules
        for linked_module in linked_modules:
            assert linked_module.startswith("notebooks/")
            linked_path = Path(linked_module)
            assert linked_path.is_file(), f"{note_path} links missing file {linked_module}"
            assert linked_path.suffix == ".ipynb", (
                f"{note_path} must link notebook files, got {linked_module}"
            )


def test_regulatory_note_pattern_ids_are_valid_when_present() -> None:
    """Structured pattern_ids metadata must reference the shared Detection pattern registry."""
    for note_path in _source_note_paths():
        metadata, _body = _read_note(note_path)
        pattern_ids = metadata.get("pattern_ids")

        if pattern_ids is None:
            continue
        assert isinstance(pattern_ids, list), f"{note_path} pattern_ids must be a list"
        assert pattern_ids, f"{note_path} pattern_ids must not be empty"
        invalid_pattern_ids = sorted(set(pattern_ids) - set(PATTERN_IDS))
        assert not invalid_pattern_ids, (
            f"{note_path} has unknown pattern_ids: {invalid_pattern_ids}"
        )


def test_private_banking_v0_3_regulatory_notes_reference_required_pattern_ids() -> None:
    """v0.3 private-banking regulatory notes must carry approved pattern IDs."""
    for note_path in _source_note_paths():
        metadata, _body = _read_note(note_path)
        linked_modules = _linked_modules(metadata)
        is_private_banking_v0_3 = any(
            linked_module.startswith(PRIVATE_BANKING_V0_3_MODULE_PREFIX)
            for linked_module in linked_modules
        )

        if is_private_banking_v0_3:
            pattern_ids = metadata.get("pattern_ids")
            assert pattern_ids is not None, (
                f"{note_path} must define pattern_ids metadata"
            )
            assert isinstance(pattern_ids, list), f"{note_path} pattern_ids must be a list"
            assert pattern_ids, f"{note_path} pattern_ids must not be empty"
            invalid_pattern_ids = sorted(set(pattern_ids) - PRIVATE_BANKING_V0_3_PATTERN_IDS)
            assert not invalid_pattern_ids, (
                f"{note_path} must use v0.3 private-banking pattern_ids from "
                f"{sorted(PRIVATE_BANKING_V0_3_PATTERN_IDS)}; got {invalid_pattern_ids}"
            )


def test_digital_v0_4_regulatory_notes_reference_digital_pattern_ids_and_modules() -> None:
    """v0.4 digital regulatory notes must carry digital pattern IDs and v0.4 modules."""
    required_digital_families = {"app_scam_payment", "fatf_typologies"}
    covered_digital_families: set[str] = set()

    for note_path in _source_note_paths():
        metadata, _body = _read_note(note_path)
        linked_modules = _linked_modules(metadata)
        is_digital_v0_4 = any(
            linked_module.startswith(DIGITAL_V0_4_MODULE_PREFIX)
            for linked_module in linked_modules
        )

        if is_digital_v0_4:
            pattern_ids = metadata.get("pattern_ids")
            assert pattern_ids is not None, f"{note_path} must define pattern_ids metadata"
            assert isinstance(pattern_ids, list), f"{note_path} pattern_ids must be a list"
            assert pattern_ids, f"{note_path} pattern_ids must not be empty"
            invalid_pattern_ids = sorted(set(pattern_ids) - DIGITAL_V0_4_PATTERN_IDS)
            assert not invalid_pattern_ids, (
                f"{note_path} must use digital pattern_ids from "
                f"{sorted(DIGITAL_V0_4_PATTERN_IDS)}; got {invalid_pattern_ids}"
            )
            digital_modules = [
                linked_module
                for linked_module in linked_modules
                if linked_module.startswith(DIGITAL_V0_4_MODULE_PREFIX)
            ]
            assert digital_modules, f"{note_path} must link at least one v0.4 notebook"
            covered_digital_families.update(set(metadata["source_families"]))

    assert required_digital_families <= covered_digital_families, (
        f"Missing digital v0.4 regulatory families: "
        f"{required_digital_families - covered_digital_families}"
    )


def test_regulatory_notes_avoid_imperative_compliance_wording() -> None:
    """Notes should teach implications without issuing compliance instructions."""
    for note_path in _source_note_paths():
        text = note_path.read_text(encoding="utf-8").lower()
        for pattern in BANNED_IMPERATIVE_PATTERNS:
            assert not re.search(pattern, text), f"{note_path} contains banned wording: {pattern}"


def test_regulatory_notes_do_not_include_direct_quote_blocks() -> None:
    """Draft notes should avoid direct quotation unless a future review approves excerpts."""
    for note_path in _source_note_paths():
        text = note_path.read_text(encoding="utf-8")

        assert not any(line.lstrip().startswith(">") for line in text.splitlines()), (
            f"{note_path} contains a direct quote block"
        )


def _source_note_paths() -> tuple[Path, ...]:
    """Return regulatory source notes in deterministic order."""
    return tuple(sorted(SOURCE_NOTE_DIR.glob("*.md")))


def _linked_modules(metadata: dict[str, str | list[str]]) -> tuple[str, ...]:
    """Return linked module paths from source-note metadata."""
    linked_modules = metadata["linked_modules"]
    assert isinstance(linked_modules, list), "linked_modules must be a list"
    return tuple(linked_modules)


def _read_note(note_path: Path) -> tuple[dict[str, str | list[str]], str]:
    """Read front matter and body from a simple YAML-like Markdown note."""
    text = note_path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{note_path} must start with front matter"

    _prefix, raw_metadata, body = text.split("---", 2)
    return _parse_front_matter(raw_metadata), body


def _parse_front_matter(raw_metadata: str) -> dict[str, str | list[str]]:
    """Parse regulatory source-note front matter with a YAML parser."""
    parsed: Any = yaml.safe_load(raw_metadata)
    assert isinstance(parsed, dict), "Front matter must be a mapping"

    metadata: dict[str, str | list[str]] = {}
    for raw_key, raw_value in parsed.items():
        assert isinstance(raw_key, str), f"Front-matter key must be a string: {raw_key!r}"
        if isinstance(raw_value, str):
            metadata[raw_key] = raw_value
        elif isinstance(raw_value, bool):
            metadata[raw_key] = str(raw_value).lower()
        elif isinstance(raw_value, list):
            assert all(isinstance(item, str) for item in raw_value), (
                f"{raw_key} must contain only string values"
            )
            metadata[raw_key] = raw_value
        else:
            raise AssertionError(f"Unsupported front-matter value for {raw_key}: {raw_value!r}")

    return metadata


def _is_allowed_official_domain(url: str) -> bool:
    """Return whether the source URL is on an expected official-source domain."""
    domain = urlparse(url).netloc.lower().removeprefix("www.")
    return domain in ALLOWED_OFFICIAL_DOMAINS


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
