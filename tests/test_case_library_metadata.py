"""Validation tests for pattern-linked case-library source packs."""

from __future__ import annotations

from pathlib import Path
import re

from banking_fraud_lab.schema import PATTERN_IDS
from private_banking_test_constants import (
    PRIVATE_BANKING_V0_3_MODULE_PREFIX,
    PRIVATE_BANKING_V0_3_PATTERN_IDS,
)

CASE_SOURCE_PACK_DIR = Path("docs/cases/source_packs")
CASE_LIBRARY_INDEX = Path("docs/cases/index.md")
HITL_MARKER = "<!-- HITL-REVIEW-REQUIRED -->"
PRIVATE_BANKING_TRACK = "Private-banking fraud detection"
DIGITAL_TRACK = "Digital-banking fraud detection"
DIGITAL_V0_4_MODULE_PREFIX = "notebooks/05_digital_session_and_payment_fraud/"
DIGITAL_V0_4_PATTERN_IDS = {
    "digital_scam_to_mule",
    "new_beneficiary_payment",
    "session_payment_velocity",
}
REQUIRED_V0_4_DIGITAL_SOURCE_PACKS = {
    "digital-app-scam-payments.md",
    "digital-money-mule-behavior.md",
    "digital-online-bank-control-failures.md",
    "digital-payment-system-guidance.md",
}
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
BANNED_RECONSTRUCTION_PHRASES = (
    "reconstructs the",
    "reproduces the",
    "recreation of",
    "based on actual",
    "replicate the",
    "exact case",
)

# v0.5 case-library skill layer: canonical template, rubric, contributor guide,
# and the worked-example pack. The template sections are a superset of the
# REQUIRED_SECTIONS every source pack already carries; `## Summary` and the
# structured learner-output exercise format are introduced by v0.5 and migrate
# pack-by-pack in #119/#120/#121, so the new requirements are scoped to the
# template artifacts and the worked example rather than every pack at once.
CASE_TEMPLATE = Path("docs/cases/TEMPLATE.md")
CASE_QUALITY_RUBRIC = Path("docs/cases/source_quality_rubric.md")
CASE_CONTRIBUTING = Path("docs/cases/CONTRIBUTING.md")
WORKED_EXAMPLE_PACK = Path(
    "docs/cases/source_packs/private-banking-transaction-monitoring.md"
)
TEMPLATE_REQUIRED_SECTIONS = REQUIRED_SECTIONS | {"## Summary"}
WORKED_EXAMPLE_PATTERN_IDS = {"pb_transaction_fraud", "pb_high_value_movement"}


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


def test_case_source_pack_pattern_ids_are_valid_when_present() -> None:
    """Structured pattern_id metadata must reference the shared Detection pattern registry."""
    for path in _source_pack_paths():
        metadata = _metadata(path)
        pattern_id = metadata.get("pattern_id")

        if pattern_id:
            assert pattern_id in PATTERN_IDS, f"{path} has unknown pattern_id: {pattern_id}"


def test_private_banking_v0_3_source_packs_reference_required_pattern_ids() -> None:
    """v0.3 private-banking source packs must carry approved private-banking pattern IDs."""
    for path in _source_pack_paths():
        metadata = _metadata(path)
        linked_modules = _linked_modules(metadata)
        is_private_banking_v0_3 = (
            metadata["track"] == PRIVATE_BANKING_TRACK
            and any(
                linked_module.startswith(PRIVATE_BANKING_V0_3_MODULE_PREFIX)
                for linked_module in linked_modules
            )
        )

        if is_private_banking_v0_3:
            pattern_id = metadata.get("pattern_id")
            assert pattern_id is not None, f"{path} must define pattern_id metadata"
            assert pattern_id in PRIVATE_BANKING_V0_3_PATTERN_IDS, (
                f"{path} must use a v0.3 private-banking pattern_id from "
                f"{sorted(PRIVATE_BANKING_V0_3_PATTERN_IDS)}"
            )


def test_digital_v0_4_source_packs_cover_required_topics() -> None:
    """The four required v0.4 digital source packs must each be present."""
    source_pack_names = {path.name for path in _source_pack_paths()}
    assert REQUIRED_V0_4_DIGITAL_SOURCE_PACKS <= source_pack_names


def test_digital_v0_4_source_packs_reference_digital_pattern_ids_and_modules() -> None:
    """v0.4 digital source packs must use digital pattern IDs and v0.4 modules."""
    for path in _source_pack_paths():
        metadata = _metadata(path)
        linked_modules = _linked_modules(metadata)
        is_digital_v0_4 = metadata["track"] == DIGITAL_TRACK and any(
            linked_module.startswith(DIGITAL_V0_4_MODULE_PREFIX)
            for linked_module in linked_modules
        )

        if is_digital_v0_4:
            pattern_id = metadata.get("pattern_id")
            assert pattern_id is not None, f"{path} must define pattern_id metadata"
            assert pattern_id in DIGITAL_V0_4_PATTERN_IDS, (
                f"{path} must use a digital pattern_id from "
                f"{sorted(DIGITAL_V0_4_PATTERN_IDS)}"
            )
            digital_modules = [
                linked_module
                for linked_module in linked_modules
                if linked_module.startswith(DIGITAL_V0_4_MODULE_PREFIX)
            ]
            assert digital_modules, f"{path} must link at least one v0.4 notebook"
            for linked_module in digital_modules:
                assert Path(linked_module).exists()


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


def test_case_source_packs_do_not_claim_reconstruction() -> None:
    """Source packs must not claim to reproduce public matters in synthetic data."""
    for path in _source_pack_paths():
        text = path.read_text(encoding="utf-8").lower()
        for phrase in BANNED_RECONSTRUCTION_PHRASES:
            assert phrase not in text, f"{path} contains banned wording: {phrase}"


def test_case_source_packs_do_not_include_direct_quote_blocks() -> None:
    """Draft source packs should avoid direct quotation unless human review approves excerpts."""
    for path in _source_pack_paths():
        text = path.read_text(encoding="utf-8")

        assert not any(line.startswith(">") for line in text.splitlines()), (
            f"{path} contains a direct quote block"
        )


def test_case_source_pack_metadata_parser_handles_crlf_front_matter(tmp_path: Path) -> None:
    """Metadata parsing should be stable on Windows CRLF checkouts."""
    source_pack = _source_pack_paths()[0]
    crlf_path = tmp_path / source_pack.name
    crlf_text = source_pack.read_text(encoding="utf-8").replace("\n", "\r\n")
    crlf_path.write_bytes(crlf_text.encode("utf-8"))

    assert _metadata(crlf_path)["status"] == "draft-hitl"


def test_case_template_declares_required_sections() -> None:
    """The v0.5 template must document every section a migrated pack needs."""
    text = CASE_TEMPLATE.read_text(encoding="utf-8")

    assert HITL_MARKER in text
    assert "Detection pattern" in text
    missing = TEMPLATE_REQUIRED_SECTIONS - set(_template_section_headings(text))
    assert not missing, f"TEMPLATE.md missing sections: {sorted(missing)}"
    # The template must teach the facts-vs-interpretation split explicitly.
    assert "Public Facts" in text
    assert "Interpretation For Detection Patterns" in text
    # The template must teach the structured learner-output exercise format.
    assert "### Exercise" in text
    assert "Learner output" in text
    # The template must reference the frozen pattern vocabulary rather than IDs.
    assert "PATTERN_IDS" in text


def test_case_template_documents_front_matter_and_pattern_id() -> None:
    """The template must teach pattern_id referencing the shared registry."""
    text = CASE_TEMPLATE.read_text(encoding="utf-8")

    assert "pattern_id" in text
    for pattern_id in WORKED_EXAMPLE_PATTERN_IDS:
        assert pattern_id in text, f"TEMPLATE.md should mention {pattern_id}"
    assert "detection_pattern" in text
    assert "linked_modules" in text


def test_case_quality_rubric_weights_source_types() -> None:
    """The source-quality rubric must weight each source type tier."""
    text = CASE_QUALITY_RUBRIC.read_text(encoding="utf-8")
    normalized = text.lower()

    assert HITL_MARKER in text
    for source_type in (
        "regulator",
        "court",
        "official regulatory disclosure",
        "journalism",
        "industry",
    ):
        assert source_type in normalized, f"Rubric missing source type: {source_type}"
    # The rubric must teach non-reconstruction and non-affiliation discipline.
    assert "reconstruct" in normalized
    assert "affiliation" in normalized
    assert "Detection pattern" in text


def test_case_contributing_checklist_covers_required_disciplines() -> None:
    """The contributor checklist must cover the v0.5 disciplines."""
    text = CASE_CONTRIBUTING.read_text(encoding="utf-8")

    assert HITL_MARKER in text
    for discipline in (
        "source discipline",
        "non-reconstruction",
        "non-affiliation",
        "official-source linking",
        "learner-output exercise",
    ):
        assert discipline in text.lower(), f"CONTRIBUTING missing: {discipline}"
    # The checklist must reference the canonical template and rubric.
    assert "TEMPLATE.md" in text
    assert "source_quality_rubric.md" in text
    # The checklist must reinforce the frozen pattern vocabulary.
    assert "PATTERN_IDS" in text


def test_worked_example_source_pack_conforms_to_template() -> None:
    """The v0.5 worked-example pack must carry every template section."""
    text = WORKED_EXAMPLE_PACK.read_text(encoding="utf-8")

    assert HITL_MARKER in text
    headings = _section_headings(text)
    missing = TEMPLATE_REQUIRED_SECTIONS - headings
    assert not missing, f"Worked example missing sections: {sorted(missing)}"


def test_worked_example_source_pack_has_learner_output_exercises() -> None:
    """The worked example must include structured learner-output exercises."""
    text = WORKED_EXAMPLE_PACK.read_text(encoding="utf-8")
    exercise_section = _section_text(text, "## Linked Modules And Exercises")

    exercise_blocks = re.findall(r"### Exercise \d", text)
    assert len(exercise_blocks) >= 1, "Worked example needs at least one exercise"
    # Each exercise block must carry a Pattern, Module, Prompt, and output.
    for label in ("Pattern:", "Module:", "Prompt:", "Learner output:"):
        assert label in exercise_section, f"Exercise missing field: {label}"


def test_worked_example_source_pack_exercises_reference_valid_pattern_ids() -> None:
    """Worked-example exercises must cite frozen private-banking pattern IDs."""
    text = WORKED_EXAMPLE_PACK.read_text(encoding="utf-8")
    exercise_section = _section_text(text, "## Linked Modules And Exercises")

    referenced_pattern_ids = {
        match.group(0)
        for pattern_id in WORKED_EXAMPLE_PATTERN_IDS
        for match in [re.search(re.escape(pattern_id), exercise_section)]
        if match
    }
    assert referenced_pattern_ids, (
        "Worked-example exercises must reference at least one of "
        f"{sorted(WORKED_EXAMPLE_PATTERN_IDS)}"
    )
    invalid = referenced_pattern_ids - set(PATTERN_IDS)
    assert not invalid, f"Worked example cites unknown pattern_id(s): {sorted(invalid)}"


def test_worked_example_source_pack_exercises_link_existing_modules() -> None:
    """Worked-example exercise module paths must exist in the repository."""
    text = WORKED_EXAMPLE_PACK.read_text(encoding="utf-8")
    exercise_section = _section_text(text, "## Linked Modules And Exercises")

    module_paths = re.findall(r"Module: `(notebooks/[^`]+)`", exercise_section)
    assert module_paths, "Worked-example exercises must name a Module path"
    for module_path in module_paths:
        assert Path(module_path).is_file(), (
            f"Worked-example exercise links missing module: {module_path}"
        )


def _template_section_headings(text: str) -> set[str]:
    """Return the level-two section names a template documents.

    TEMPLATE.md describes each required section as a ``### ## Heading`` line and
    also mentions section names in backticks, so this helper collects real
    ``## `` headings, the documented ``### ## Heading`` lines, and backticked
    ``## Heading`` references.
    """
    headings = {line.strip() for line in text.splitlines() if line.startswith("## ")}
    documented = {line.removeprefix("### ").strip() for line in text.splitlines() if line.startswith("### ## ")}
    backticked = set(re.findall(r"`(## [A-Z][^`]+)`", text))
    return headings | documented | backticked


def _source_pack_paths() -> tuple[Path, ...]:
    """Return source-pack markdown files, failing clearly if none exist."""
    paths = tuple(sorted(CASE_SOURCE_PACK_DIR.glob("*.md")))
    assert paths, f"No source packs found under {CASE_SOURCE_PACK_DIR}"
    return paths


def _linked_modules(metadata: dict[str, str]) -> tuple[str, ...]:
    """Return comma-separated linked modules from source-pack metadata."""
    return tuple(
        linked_module.strip()
        for linked_module in metadata["linked_modules"].split(",")
        if linked_module.strip()
    )


def _metadata(path: Path) -> dict[str, str]:
    """Parse simple key-value front matter from a source-pack file."""
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert text.startswith("---\n"), f"{path} is missing opening front matter"
    front_matter_parts = text.split("---", maxsplit=2)
    assert len(front_matter_parts) == 3, f"{path} is missing closing front matter"
    _, raw_front_matter, _ = front_matter_parts
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
