"""Tests for regulatory source-note structure and safety wording."""

from pathlib import Path
from urllib.parse import urlparse

import re


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
    "## Linked v0.1 Exercises",
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


def test_regulatory_notes_link_existing_v0_1_exercises() -> None:
    """Regulatory notes must connect source material to real v0.1 notebooks."""
    for note_path in _source_note_paths():
        metadata, _body = _read_note(note_path)
        linked_modules = metadata["linked_modules"]

        assert linked_modules
        for linked_module in linked_modules:
            assert linked_module.startswith("notebooks/")
            assert Path(linked_module).exists(), f"{note_path} links missing {linked_module}"


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


def _read_note(note_path: Path) -> tuple[dict[str, str | list[str]], str]:
    """Read front matter and body from a simple YAML-like Markdown note."""
    text = note_path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{note_path} must start with front matter"

    _prefix, raw_metadata, body = text.split("---", 2)
    return _parse_front_matter(raw_metadata), body


def _parse_front_matter(raw_metadata: str) -> dict[str, str | list[str]]:
    """Parse the small front-matter subset used by regulatory source notes."""
    metadata: dict[str, str | list[str]] = {}
    current_list_key: str | None = None

    for raw_line in raw_metadata.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        if line.startswith("  - "):
            assert current_list_key is not None, f"List item without key: {line}"
            list_value = metadata[current_list_key]
            assert isinstance(list_value, list)
            list_value.append(line.removeprefix("  - ").strip())
            continue

        key, separator, value = line.partition(":")
        assert separator, f"Invalid front-matter line: {line}"
        key = key.strip()
        value = value.strip().strip('"')
        if value:
            metadata[key] = value
            current_list_key = None
        else:
            metadata[key] = []
            current_list_key = key

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
