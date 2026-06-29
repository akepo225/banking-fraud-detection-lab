"""Validation tests for pattern-linked case-library source packs."""

from __future__ import annotations

from pathlib import Path
import re

from banking_fraud_lab.schema import FOUNDATION_DETECTION_PATTERNS, PATTERN_IDS
from private_banking_test_constants import (
    PRIVATE_BANKING_V0_3_MODULE_PREFIX,
    PRIVATE_BANKING_V0_3_PATTERN_IDS,
)

CASE_SOURCE_PACK_DIR = Path("docs/cases/source_packs")
CASE_LIBRARY_INDEX = Path("docs/cases/index.md")
REGULATORY_SOURCE_NOTE_DIR = Path("docs/regulation/source_notes")
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
    "source_type",
    "geography",
    "product",
    "source_quality",
    "linked_modules",
}

# v0.5 (#119) machine-readable source taxonomy. `source_type` is a controlled
# vocabulary that classifies the source body independent of its human-readable
# `source_authority` / `source_quality` phrase family (the phrase family is
# documented in docs/cases/source_quality_rubric.md and intentionally not a
# single exact string, so the tests do not enforce it).
SOURCE_TYPES = {
    "regulator",
    "court",
    "enforcement",
    "bank_disclosure",
    "payment_system_operator",
    "cyber_authority",
    "industry_report",
    "journalism",
}
# Packs that are genuinely cross-track governance/method rather than a single
# Detection pattern keep `pattern_id` optional. Everything else must reference a
# frozen PATTERN_IDS value.
PATTERN_ID_OPTIONAL_PACKS = {"model-governance-method.md"}
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
# structured learner-output exercise format are introduced by v0.5. #118 lands
# them on the worked example and the template artifacts; #120 finishes the
# private-banking track, so the v0.5 conformance and learner-output exercise
# requirements now apply to every private-banking pack, not only the worked
# example (issue #120 acceptance criterion 3).
CASE_TEMPLATE = Path("docs/cases/TEMPLATE.md")
CASE_QUALITY_RUBRIC = Path("docs/cases/source_quality_rubric.md")
CASE_CONTRIBUTING = Path("docs/cases/CONTRIBUTING.md")
TEMPLATE_REQUIRED_SECTIONS = REQUIRED_SECTIONS | {"## Summary"}
WORKED_EXAMPLE_PATTERN_IDS = {"pb_transaction_fraud", "pb_high_value_movement"}
# Every source pack on the private-banking track must reach v0.5 template
# conformance (issue #120). Discovered dynamically so a new private-banking
# pack is governed the moment it lands.
CORE_NOTEBOOK_MODULES = tuple(
    sorted(p for p in Path("notebooks").glob("[0-9][0-9]_*") if p.is_dir())
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
        assert metadata["source_type"] in SOURCE_TYPES, (
            f"{path} has unknown source_type: {metadata['source_type']}"
        )
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


def test_case_source_pack_pattern_id_required_except_cross_track() -> None:
    """Detection-pattern packs must declare pattern_id; cross-track packs may omit it."""
    for path in _source_pack_paths():
        metadata = _metadata(path)
        pattern_id = metadata.get("pattern_id")
        if path.name in PATTERN_ID_OPTIONAL_PACKS:
            assert pattern_id in PATTERN_IDS or pattern_id is None, (
                f"{path} optional pattern_id must still be valid if set"
            )
        else:
            assert pattern_id is not None, f"{path} must declare pattern_id"
            assert pattern_id in PATTERN_IDS, (
                f"{path} has unknown pattern_id: {pattern_id}"
            )


def test_source_type_vocabulary_documented_in_rubric() -> None:
    """Every canonical source_type token must be documented in the rubric.

    The machine-readable ``source_type`` vocabulary lives canonically in
    ``SOURCE_TYPES``; the source-quality rubric documents each token's tier
    mapping and intended source body so a contributor copying TEMPLATE.md has an
    authoritative list. Guards against a token being added to ``SOURCE_TYPES``
    without being documented in the rubric.
    """
    rubric = CASE_QUALITY_RUBRIC.read_text(encoding="utf-8")
    missing = [token for token in SOURCE_TYPES if f"`{token}`" not in rubric]
    assert not missing, (
        "source_type tokens missing from docs/cases/source_quality_rubric.md: "
        f"{missing}"
    )


def test_template_front_matter_documents_source_type() -> None:
    """TEMPLATE.md front-matter example must include the source_type field."""
    template = CASE_TEMPLATE.read_text(encoding="utf-8")
    assert "source_type:" in template, (
        "TEMPLATE.md front-matter example must document the source_type field"
    )


def test_case_index_groups_packs_by_detection_pattern() -> None:
    """The case index must expose a section per tabular pattern_id and one for cross-track packs.

    Graph-derived patterns (v0.6) carry no generator activity type and their case
    source packs land in #155, so the index is only required to cover patterns
    that already have tabular signal and source packs.
    """
    index_text = CASE_LIBRARY_INDEX.read_text(encoding="utf-8")

    tabular_pattern_ids = {
        spec.pattern_id
        for spec in FOUNDATION_DETECTION_PATTERNS
        if spec.activity_types
    }
    for pattern_id in tabular_pattern_ids:
        assert f"### `{pattern_id}`" in index_text, (
            f"Index missing Detection-pattern section: {pattern_id}"
        )
    assert "## Cross-Pattern and Governance" in index_text
    # Every pack must be linked from the index (existing invariant, restated here
    # alongside the structure check for a single source of truth).
    for path in _source_pack_paths():
        relative_path = path.as_posix().removeprefix("docs/cases/")
        assert f"]({relative_path})" in index_text, (
            f"Index does not link {relative_path}"
        )


def test_case_index_pattern_sections_list_their_packs() -> None:
    """Each pack must appear under the section matching its own pattern_id."""
    index_text = CASE_LIBRARY_INDEX.read_text(encoding="utf-8")
    sections = _index_pattern_sections(index_text)

    for path in _source_pack_paths():
        metadata = _metadata(path)
        pattern_id = metadata.get("pattern_id")
        relative_path = path.as_posix().removeprefix("docs/cases/")
        link = f"]({relative_path})"
        if pattern_id:
            assert link in sections[pattern_id], (
                f"{path.name} (pattern_id {pattern_id}) not listed under its section"
            )
        else:
            assert link in sections["__cross__"], (
                f"{path.name} not listed under Cross-Pattern and Governance"
            )


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


def test_private_banking_source_packs_conform_to_v0_5_template() -> None:
    """Every private-banking pack must carry every v0.5 template section.

    Generalizes the worked-example check (#118) across the whole private-banking
    track once #120 finishes the upgrade, so a future edit cannot silently strip
    the ``## Summary`` (or any other template) section from a pack.
    """
    private_banking_packs = _private_banking_packs()
    assert private_banking_packs, "No private-banking source packs found to validate"
    for pack in private_banking_packs:
        text = pack.read_text(encoding="utf-8")
        assert HITL_MARKER in text, f"{pack.name} missing HITL marker"
        missing = TEMPLATE_REQUIRED_SECTIONS - _section_headings(text)
        assert not missing, f"{pack.name} missing sections: {sorted(missing)}"


def test_private_banking_source_packs_have_learner_output_exercises() -> None:
    """Every private-banking pack must include structured learner-output exercises.

    Each ``### Exercise N`` block must carry a Pattern, Module, Prompt, and
    Learner-output field, and there must be at least one exercise per pack
    (issue #120 acceptance criterion 1).
    """
    for pack in _private_banking_packs():
        text = pack.read_text(encoding="utf-8")
        exercise_section = _section_text(text, "## Linked Modules And Exercises")
        exercise_blocks = _exercise_blocks(exercise_section)
        assert exercise_blocks, f"{pack.name} needs at least one exercise"
        for index, block in enumerate(exercise_blocks, start=1):
            for label in ("Pattern:", "Module:", "Prompt:", "Learner output:"):
                assert label in block, (
                    f"{pack.name} exercise {index} missing field: {label}"
                )


def test_private_banking_source_pack_exercises_reference_valid_pattern_ids() -> None:
    """Private-banking exercises must cite frozen pattern IDs.

    v0.3 private-banking packs cite the private tabular pattern IDs; the v0.6
    graph pack on the private-banking track cites the graph-native
    ``circular_funds_movement`` pattern. Either is acceptable as long as every
    cited id is present in the frozen registry.
    """
    private_banking_pattern_ids = set(PRIVATE_BANKING_V0_3_PATTERN_IDS)
    graph_private_pattern_ids = {"circular_funds_movement"}
    for pack in _private_banking_packs():
        text = pack.read_text(encoding="utf-8")
        exercise_section = _section_text(text, "## Linked Modules And Exercises")
        referenced_pattern_ids: set[str] = set()
        for block in _exercise_blocks(exercise_section):
            referenced_pattern_ids.update(_exercise_pattern_ids(block))
        assert referenced_pattern_ids & (
            private_banking_pattern_ids | graph_private_pattern_ids
        ), (
            f"{pack.name} exercises must reference at least one of "
            f"{sorted(private_banking_pattern_ids | graph_private_pattern_ids)}"
        )
        invalid = referenced_pattern_ids - set(PATTERN_IDS)
        assert not invalid, (
            f"{pack.name} cites unknown pattern_id(s): {sorted(invalid)}"
        )


def test_private_banking_source_pack_exercises_link_existing_modules() -> None:
    """Private-banking exercise module paths must exist, checked per exercise."""
    for pack in _private_banking_packs():
        text = pack.read_text(encoding="utf-8")
        exercise_section = _section_text(text, "## Linked Modules And Exercises")
        exercise_blocks = _exercise_blocks(exercise_section)
        assert exercise_blocks, f"{pack.name} needs at least one exercise"
        for index, block in enumerate(exercise_blocks, start=1):
            module_paths = re.findall(r"Module: `(notebooks/[^`]+)`", block)
            assert module_paths, f"{pack.name} exercise {index} must name a Module path"
            for module_path in module_paths:
                assert Path(module_path).is_file(), (
                    f"{pack.name} exercise {index} links missing module: {module_path}"
                )


def test_digital_source_packs_conform_to_v0_5_template() -> None:
    """Every digital pack must carry every v0.5 template section.

    Digital mirror of ``test_private_banking_source_packs_conform_to_v0_5_template``
    so issue #121 (PR #130) is guarded the same way #120 is: a future edit
    cannot silently strip the ``## Summary`` (or any other template) section
    from a digital pack.
    """
    digital_packs = _digital_packs()
    assert digital_packs, "No digital source packs found to validate"
    for pack in digital_packs:
        text = pack.read_text(encoding="utf-8")
        assert HITL_MARKER in text, f"{pack.name} missing HITL marker"
        missing = TEMPLATE_REQUIRED_SECTIONS - _section_headings(text)
        assert not missing, f"{pack.name} missing sections: {sorted(missing)}"


def test_digital_source_packs_have_learner_output_exercises() -> None:
    """Every digital pack must include structured learner-output exercises.

    Each ``### Exercise N`` block must carry a Pattern, Module, Prompt, and
    Learner-output field, and there must be at least one exercise per pack
    (issue #121 acceptance criterion 1).
    """
    for pack in _digital_packs():
        text = pack.read_text(encoding="utf-8")
        exercise_section = _section_text(text, "## Linked Modules And Exercises")
        exercise_blocks = _exercise_blocks(exercise_section)
        assert exercise_blocks, f"{pack.name} needs at least one exercise"
        for index, block in enumerate(exercise_blocks, start=1):
            for label in ("Pattern:", "Module:", "Prompt:", "Learner output:"):
                assert label in block, (
                    f"{pack.name} exercise {index} missing field: {label}"
                )


def test_digital_source_pack_exercises_reference_valid_pattern_ids() -> None:
    """Digital exercises must cite frozen pattern IDs.

    v0.4 digital packs cite the digital tabular pattern IDs; v0.6 graph packs
    on the digital track cite the graph-native ``mule_ring`` pattern. Either is
    acceptable as long as every cited id is present in the frozen registry.
    """
    digital_pattern_ids = set(DIGITAL_V0_4_PATTERN_IDS)
    graph_digital_pattern_ids = {"mule_ring"}
    for pack in _digital_packs():
        text = pack.read_text(encoding="utf-8")
        exercise_section = _section_text(text, "## Linked Modules And Exercises")
        referenced_pattern_ids: set[str] = set()
        for block in _exercise_blocks(exercise_section):
            referenced_pattern_ids.update(_exercise_pattern_ids(block))
        assert referenced_pattern_ids & (digital_pattern_ids | graph_digital_pattern_ids), (
            f"{pack.name} exercises must reference at least one of "
            f"{sorted(digital_pattern_ids | graph_digital_pattern_ids)}"
        )
        invalid = referenced_pattern_ids - set(PATTERN_IDS)
        assert not invalid, (
            f"{pack.name} cites unknown pattern_id(s): {sorted(invalid)}"
        )


def test_digital_source_pack_exercises_link_existing_modules() -> None:
    """Digital exercise module paths must exist, checked per exercise."""
    for pack in _digital_packs():
        text = pack.read_text(encoding="utf-8")
        exercise_section = _section_text(text, "## Linked Modules And Exercises")
        exercise_blocks = _exercise_blocks(exercise_section)
        assert exercise_blocks, f"{pack.name} needs at least one exercise"
        for index, block in enumerate(exercise_blocks, start=1):
            module_paths = re.findall(r"Module: `(notebooks/[^`]+)`", block)
            assert module_paths, f"{pack.name} exercise {index} must name a Module path"
            for module_path in module_paths:
                assert Path(module_path).is_file(), (
                    f"{pack.name} exercise {index} links missing module: {module_path}"
                )


def test_every_core_module_has_an_inbound_case_or_regulatory_link() -> None:
    """Every core module must be linked back to by the case library or index.

    Closes issue #124 acceptance criterion 2. PR #134 wires an outbound
    "Case library and regulatory context" section into each module README; this
    test guards the reverse direction so a module can never silently lose every
    inbound link from a source pack or regulatory note. It is consolidated
    (every core module in one assertion set) rather than a per-module one-off,
    so a newly added module is governed the moment it lands under
    ``notebooks/``.
    """
    inbound_sources = _inbound_module_links()
    uncovered = sorted(
        str(module)
        for module in CORE_NOTEBOOK_MODULES
        if not inbound_sources.get(module)
    )
    assert not uncovered, (
        "Core modules with no inbound link from any source pack or regulatory "
        f"note: {uncovered}"
    )


# v1.0 frozen core (matches docs/release/v1.0-scope.md). CORE_NOTEBOOK_MODULES is
# discovered dynamically from notebooks/[0-9][0-9]_*; this pins the v1.0 freeze so
# the case/regulatory coverage gate is explicit about the ten required modules.
V10_FROZEN_CORE_MODULES = (
    "00_foundations",
    "01_private_banking_transaction_fraud",
    "02_digital_scam_to_mule",
    "03_alert_governance",
    "04_private_banking_feature_engineering",
    "05_digital_session_and_payment_fraud",
    "06_graph_network_fraud",
    "07_interpretability_model_risk",
    "08_production_monitoring_patterns",
    "09_capstone",
)


def test_v10_core_modules_have_case_or_regulatory_link() -> None:
    """Every frozen v1.0 core module has >= 1 inbound case/regulatory link.

    Generalizes test_every_core_module_has_an_inbound_case_or_regulatory_link
    (#124) with an explicit v1.0 frozen-list assertion: per-module, against the
    ten modules frozen by docs/release/v1.0-scope.md (00-09), not just the
    dynamic aggregate. Reuses _inbound_module_links() without weakening it.
    """
    inbound_sources = _inbound_module_links()
    frozen = [Path("notebooks") / module for module in V10_FROZEN_CORE_MODULES]
    uncovered = sorted(str(module) for module in frozen if not inbound_sources.get(module))
    assert not uncovered, (
        "Frozen v1.0 core modules with no inbound link from any source pack or "
        f"regulatory note: {uncovered}"
    )


def test_v10_frozen_core_matches_on_disk_core_modules() -> None:
    """The frozen v1.0 core equals the notebook modules discovered on disk.

    Reinforces the v1.0 boundary from the case-library angle: the frozen ten
    modules are exactly notebooks/[0-9][0-9]_* (no more, no fewer), so a new
    v1.1+ module added under notebooks/ would fail this check too.
    """
    assert set(CORE_NOTEBOOK_MODULES) == {
        Path("notebooks") / module for module in V10_FROZEN_CORE_MODULES
    }


def _exercise_blocks(exercise_section: str) -> list[str]:
    """Split the exercise section into one text block per ``### Exercise N``."""
    blocks = re.findall(
        r"(### Exercise \d+[\s\S]*?)(?=\n### Exercise \d+|\Z)", exercise_section
    )
    return [block.strip() for block in blocks]


def _exercise_pattern_ids(exercise_block: str) -> set[str]:
    """Extract every backticked ``pattern_id`` a ``Pattern:`` line references.

    A pattern line may name more than one id, for example
    ``Pattern: `pb_transaction_fraud` (overlaps `pb_high_value_movement`)``. All
    backticked ids on that line are returned so a typo in the overlap id is
    caught by the caller's registry check, not just the primary id. The line is
    matched whether or not it is written as a markdown bullet.
    """
    pattern_line_match = re.search(
        r"^\s*(?:-\s*)?Pattern:\s*(.+)$", exercise_block, re.MULTILINE
    )
    if not pattern_line_match:
        return set()
    return set(re.findall(r"`([a-z0-9_]+)`", pattern_line_match.group(1)))


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


def _private_banking_packs() -> tuple[Path, ...]:
    """Return source packs whose ``track`` is the private-banking track.

    These are the packs #120 must bring to v0.5 template conformance, so the
    v0.5 conformance and learner-output exercise validators run against every
    pack in this set rather than only the worked example.
    """
    packs = tuple(
        path
        for path in _source_pack_paths()
        if _metadata(path).get("track") == PRIVATE_BANKING_TRACK
    )
    assert packs, "No private-banking source packs found to validate"
    return packs


def _digital_packs() -> tuple[Path, ...]:
    """Return every source pack on the digital-banking track (or carrying a
    digital ``pattern_id``).

    These are the packs #121 (PR #130) brings to v0.5 template conformance.
    Selection is dynamic — ``track`` OR ``pattern_id`` — so the graph/network
    pack (``track`` ``Future graph/network analytics`` but ``pattern_id
    digital_scam_to_mule``) is covered, and a newly added digital pack is
    governed the moment it lands, without editing a filename list. The OR is
    what distinguishes this from the track-only filter that previously excluded
    the graph pack.
    """
    packs = tuple(
        path
        for path in _source_pack_paths()
        if _metadata(path).get("track") == DIGITAL_TRACK
        or _metadata(path).get("pattern_id") in DIGITAL_V0_4_PATTERN_IDS
    )
    assert packs, "No digital source packs found to validate"
    return packs


def _inbound_module_links() -> dict[Path, list[str]]:
    """Map each core module to the source packs/notes that link to it.

    Covers both ``linked_modules`` formats in the repo: case source packs use a
    comma-separated inline value, while regulatory source notes use a YAML list
    of indented ``- path`` entries. Any ``notebooks/...`` path referenced from
    either source family is attributed to the core module (``notebooks/NN_*``)
    that contains it.
    """
    inbound: dict[Path, list[str]] = {module: [] for module in CORE_NOTEBOOK_MODULES}

    def attribute(linked_module: str) -> None:
        normalized = linked_module.strip().strip("\"'")
        if not normalized.startswith("notebooks/"):
            return
        referenced = Path(normalized)
        for module in CORE_NOTEBOOK_MODULES:
            if module in referenced.parents:
                source = referenced.relative_to(module.parent).as_posix()
                if source not in inbound[module]:
                    inbound[module].append(source)
                return

    for pack in _source_pack_paths():
        metadata = _metadata(pack)
        if "linked_modules" in metadata:
            for linked_module in metadata["linked_modules"].split(","):
                attribute(linked_module)

    for note in _regulatory_source_note_paths():
        for linked_module in _yaml_list_field(note, "linked_modules"):
            attribute(linked_module)

    return inbound


def _regulatory_source_note_paths() -> tuple[Path, ...]:
    """Return regulatory source-note markdown files, failing clearly if none."""
    paths = tuple(sorted(REGULATORY_SOURCE_NOTE_DIR.glob("*.md")))
    assert paths, f"No regulatory source notes found under {REGULATORY_SOURCE_NOTE_DIR}"
    return paths


def _yaml_list_field(path: Path, field: str) -> list[str]:
    """Parse a YAML-list front-matter field (indented ``- value`` entries).

    Regulatory source notes express ``linked_modules`` as a YAML block rather
    than the inline comma-separated form used by case packs. Only the list
    values are returned; nested maps are ignored.
    """
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    if not text.startswith("---\n"):
        return []
    _, raw_front_matter, _ = text.split("---", maxsplit=2)
    values: list[str] = []
    in_field = False
    for line in raw_front_matter.splitlines():
        if re.match(rf"^{field}:\s*$", line):
            in_field = True
            continue
        if in_field:
            if line.startswith("  - "):
                values.append(line.removeprefix("  - ").strip())
            elif line and not line.startswith(" "):
                in_field = False
    return values


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


def _index_pattern_sections(index_text: str) -> dict[str, str]:
    """Map each pattern_id (and ``__cross__``) to its index-section body text."""
    normalized = index_text.replace("\r\n", "\n")
    sections: dict[str, str] = {}
    current_key: str | None = None
    current_lines: list[str] = []
    for line in normalized.splitlines():
        if line.startswith("### `") and line.endswith("`"):
            if current_key is not None:
                sections[current_key] = "\n".join(current_lines)
            current_key = line.removeprefix("### `").removesuffix("`")
            current_lines = []
        elif line.startswith("## Cross-Pattern and Governance"):
            if current_key is not None:
                sections[current_key] = "\n".join(current_lines)
            current_key = "__cross__"
            current_lines = []
        elif current_key is not None:
            current_lines.append(line)
    if current_key is not None:
        sections[current_key] = "\n".join(current_lines)
    return sections


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
