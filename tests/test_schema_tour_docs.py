"""Tests for v0.2 ERD-backed schema tour documentation."""

from pathlib import Path
import re

from banking_fraud_lab.progressive_views import FOUNDATION_PROGRESSIVE_VIEW_SPECS
from banking_fraud_lab.schema import COLUMN_NAMES, TABLE_NAMES, TABLE_SPECS

SCHEMA_TOUR = Path("docs/schema/erd.md")
MODULE_VIEW_MAPS = Path("docs/schema/module_view_maps.md")

REQUIRED_GLOSSARY_TERMS = (
    "Partner",
    "Client",
    "User",
    "Banking relationship",
    "Detection pattern",
    "Alert lifecycle",
)

TABLE_ROW_RE = re.compile(
    r"^\| `(?P<table>[^`]+)` \| `(?P<primary_key>[^`]+)` \| (?P<relationships>.*?) \|$",
    re.MULTILINE,
)
REFERENCE_RE = re.compile(r"`(?P<table>[^`.]+)\.(?P<column>[^`]+)`")
VIEW_COLUMN_ROW_RE = re.compile(
    r"^\| `(?P<view_column>[^`]+)` \| `(?P<table>[^`.]+)\.(?P<column>[^`]+)` \|$",
    re.MULTILINE,
)


def test_erd_schema_tour_lists_canonical_tables_primary_keys_and_foreign_keys() -> None:
    """The ERD table map must match the schema contract table and FK references."""
    tour = SCHEMA_TOUR.read_text(encoding="utf-8")
    table_rows = {
        match.group("table"): (
            match.group("primary_key"),
            match.group("relationships"),
        )
        for match in TABLE_ROW_RE.finditer(tour)
    }

    assert set(table_rows) == set(TABLE_NAMES)
    for table_name in TABLE_NAMES:
        documented_primary_key, documented_relationships = table_rows[table_name]
        expected_references = {
            column.references
            for column in TABLE_SPECS[table_name].columns
            if column.references is not None
        }

        assert documented_primary_key == COLUMN_NAMES[table_name][0]
        assert _reference_tokens(documented_relationships) == expected_references


def test_erd_schema_tour_has_mermaid_erd_for_all_foundation_tables() -> None:
    """The schema tour must contain an ERD-style Mermaid diagram for all tables."""
    tour = SCHEMA_TOUR.read_text(encoding="utf-8")
    mermaid = _fenced_block(tour, "mermaid")

    assert "erDiagram" in mermaid
    assert "||--o{" in mermaid
    for table_name in TABLE_NAMES:
        assert table_name in mermaid


def test_module_view_maps_match_progressive_view_specs() -> None:
    """Module view maps must describe source tables and columns from view specs."""
    view_maps = MODULE_VIEW_MAPS.read_text(encoding="utf-8")
    normalized_view_maps = _normalize(view_maps)

    assert "`00_foundations`" in view_maps
    for spec in FOUNDATION_PROGRESSIVE_VIEW_SPECS:
        section = _markdown_section(view_maps, spec.name)
        assert spec.purpose in normalized_view_maps
        for source_table in spec.source_tables:
            assert f"`{source_table}`" in section
        for column_name in spec.columns:
            assert f"`{column_name}`" in section


def test_module_view_map_column_sources_exist_in_canonical_schema() -> None:
    """Every documented view column source must be a real canonical column."""
    view_maps = MODULE_VIEW_MAPS.read_text(encoding="utf-8")

    for spec in FOUNDATION_PROGRESSIVE_VIEW_SPECS:
        section = _markdown_section(view_maps, spec.name)
        source_rows = {
            match.group("view_column"): (
                match.group("table"),
                match.group("column"),
            )
            for match in VIEW_COLUMN_ROW_RE.finditer(section)
        }

        assert set(source_rows) == set(spec.columns)
        for source_table, source_column in source_rows.values():
            assert source_table in TABLE_NAMES
            assert source_column in COLUMN_NAMES[source_table]


def test_schema_tour_uses_glossary_terms_and_is_linked_from_learner_docs() -> None:
    """Learner docs must link the ERD tour and use the required glossary terms."""
    tour = SCHEMA_TOUR.read_text(encoding="utf-8")
    view_maps = MODULE_VIEW_MAPS.read_text(encoding="utf-8")
    schema_readme = Path("docs/schema/README.md").read_text(encoding="utf-8")
    notebooks_readme = Path("notebooks/README.md").read_text(encoding="utf-8")
    combined = f"{tour}\n{view_maps}"

    for term in REQUIRED_GLOSSARY_TERMS:
        assert term in combined

    assert "erd.md" in schema_readme
    assert "module_view_maps.md" in schema_readme
    assert "erd.md" in notebooks_readme


def _reference_tokens(markdown: str) -> set[str]:
    """Return schema reference tokens from a markdown table cell."""
    return {
        f"{match.group('table')}.{match.group('column')}"
        for match in REFERENCE_RE.finditer(markdown)
    }


def _fenced_block(markdown: str, language: str) -> str:
    """Return the first fenced code block for a language."""
    opening = f"```{language}\n"
    start = markdown.find(opening)
    assert start != -1, f"Missing {language} fenced block"
    start += len(opening)
    end = markdown.find("\n```", start)
    assert end != -1, f"Unclosed {language} fenced block"
    return markdown[start:end]


def _markdown_section(markdown: str, heading_name: str) -> str:
    """Return a markdown section headed by a backticked name."""
    heading = f"## `{heading_name}`"
    start = markdown.find(heading)
    assert start != -1, f"Missing section {heading}"
    next_start = markdown.find("\n## `", start + len(heading))
    if next_start == -1:
        return markdown[start:]
    return markdown[start:next_start]


def _normalize(markdown: str) -> str:
    """Collapse markdown whitespace for wrapped prose comparisons."""
    return " ".join(markdown.split())
