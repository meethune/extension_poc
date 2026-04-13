"""Mod structure validation and build integrity tests."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
DIST_DIR = PROJECT_ROOT / "dist"
SCHEMAS_DIR = PROJECT_ROOT / "schemas"
CONTENT_XML = PROJECT_ROOT / "content.xml"

REQUIRED_CONTENT_ATTRS = ("id", "version", "name")

# Structural checks: root element → required children/attributes.
# These catch the most common mistakes without full XSD compilation.
STRUCTURE_RULES: dict[str, dict[str, object]] = {
    "md": {
        "root_tag": "mdscript",
        "required_attrs": ["name"],
        "required_children": ["cues"],
    },
    "aiscripts": {
        "root_tag": "aiscript",
        "required_attrs": ["name"],
        "required_children": ["interrupts", "init", "attention"],
    },
}

# Maps src/ subdirectories to their XSD schema paths (relative to schemas/).
SCHEMA_MAP: dict[str, str] = {
    "md": "md/md.xsd",
    "aiscripts": "aiscripts/aiscripts.xsd",
}


class TestValidate:
    """Pre-build validation — XML well-formedness and structural checks."""

    def test_content_xml_exists(self) -> None:
        assert CONTENT_XML.exists(), "content.xml missing from project root"

    def test_content_xml_has_required_attributes(self) -> None:
        root = ET.parse(CONTENT_XML).getroot()
        assert root.tag == "content"
        for attr in REQUIRED_CONTENT_ATTRS:
            assert attr in root.attrib, f"content.xml missing required attribute: {attr}"

    def test_content_xml_has_dependency(self) -> None:
        root = ET.parse(CONTENT_XML).getroot()
        deps = root.findall("dependency")
        assert deps, "content.xml should declare at least one <dependency>"
        assert "version" in deps[0].attrib, "dependency missing version attribute"

    def test_src_dir_exists(self) -> None:
        assert SRC_DIR.is_dir(), "src/ directory missing"

    def test_src_has_mod_files(self) -> None:
        files = list(SRC_DIR.rglob("*"))
        mod_files = [f for f in files if f.is_file()]
        assert mod_files, "src/ contains no files to pack"

    def test_all_xml_well_formed(self) -> None:
        xml_files = list(SRC_DIR.rglob("*.xml"))
        for xml_file in xml_files:
            try:
                ET.parse(xml_file)
            except ET.ParseError as e:
                pytest.fail(f"{xml_file.relative_to(PROJECT_ROOT)}: {e}")

    def test_xml_structure(self) -> None:
        errors: list[str] = []
        for subdir, rules in STRUCTURE_RULES.items():
            src_subdir = SRC_DIR / subdir
            if not src_subdir.is_dir():
                continue
            for xml_file in sorted(src_subdir.rglob("*.xml")):
                rel = xml_file.relative_to(PROJECT_ROOT)
                root = ET.parse(xml_file).getroot()
                if root.tag != rules["root_tag"]:
                    errors.append(
                        f"{rel}: expected root <{rules['root_tag']}>, got <{root.tag}>"
                    )
                    continue
                for attr in rules.get("required_attrs", []):  # type: ignore[union-attr]
                    if attr not in root.attrib:
                        errors.append(f"{rel}: missing required attribute '{attr}'")
                for child in rules.get("required_children", []):  # type: ignore[union-attr]
                    if root.find(str(child)) is None:
                        errors.append(f"{rel}: missing required element <{child}>")
        if errors:
            pytest.fail("Structural validation errors:\n" + "\n".join(errors))


class TestSchema:
    """Full XSD schema validation — slow (~70s), opt-in via ``make schema-validate``.

    Requires schemas extracted from game files:
    ``make schemas X4_GAME_DIR="/path/to/X4 Foundations"``
    """

    @pytest.fixture(autouse=True)
    def _require_schemas(self) -> None:
        if not SCHEMAS_DIR.is_dir() or not any(SCHEMAS_DIR.rglob("*.xsd")):
            pytest.skip("schemas/ not found — run 'make schemas' to extract from game")

    @staticmethod
    def _load_schema(xsd_path: Path) -> "etree.XMLSchema":  # type: ignore[name-defined]
        from lxml import etree

        schema_doc = etree.parse(str(xsd_path))
        return etree.XMLSchema(schema_doc)

    @staticmethod
    def _collect_xml_for_schema(subdir: str) -> list[Path]:
        src_subdir = SRC_DIR / subdir
        if not src_subdir.is_dir():
            return []
        return sorted(src_subdir.rglob("*.xml"))

    def test_md_scripts_valid(self) -> None:
        xsd_path = SCHEMAS_DIR / SCHEMA_MAP["md"]
        if not xsd_path.exists():
            pytest.skip(f"Schema not found: {xsd_path}")
        xml_files = self._collect_xml_for_schema("md")
        if not xml_files:
            pytest.skip("No MD scripts in src/md/")
        schema = self._load_schema(xsd_path)
        self._validate_files(schema, xml_files)

    def test_aiscripts_valid(self) -> None:
        xsd_path = SCHEMAS_DIR / SCHEMA_MAP["aiscripts"]
        if not xsd_path.exists():
            pytest.skip(f"Schema not found: {xsd_path}")
        xml_files = self._collect_xml_for_schema("aiscripts")
        if not xml_files:
            pytest.skip("No AI scripts in src/aiscripts/")
        schema = self._load_schema(xsd_path)
        self._validate_files(schema, xml_files)

    @staticmethod
    def _validate_files(schema: "etree.XMLSchema", xml_files: list[Path]) -> None:  # type: ignore[name-defined]
        from lxml import etree

        errors: list[str] = []
        for xml_file in xml_files:
            doc = etree.parse(str(xml_file))
            if not schema.validate(doc):
                rel = xml_file.relative_to(PROJECT_ROOT)
                for err in schema.error_log:
                    errors.append(f"{rel}:{err.line}: {err.message}")
        if errors:
            pytest.fail("XSD validation errors:\n" + "\n".join(errors))


class TestBuild:
    """Post-build verification — catalog integrity and round-trip correctness."""

    def test_dist_catalog_exists(self) -> None:
        assert (DIST_DIR / "ext_01.cat").exists(), "dist/ext_01.cat missing — run 'make build'"
        assert (DIST_DIR / "ext_01.dat").exists(), "dist/ext_01.dat missing — run 'make build'"

    def test_dist_content_xml_exists(self) -> None:
        assert (DIST_DIR / "content.xml").exists(), "dist/content.xml missing — run 'make build'"

    def test_dist_content_xml_matches_source(self) -> None:
        assert CONTENT_XML.read_text() == (DIST_DIR / "content.xml").read_text()

    def test_catalog_contains_all_src_files(self) -> None:
        from x4_catalog import build_vfs

        vfs = build_vfs(DIST_DIR, prefix="ext_")
        src_files = {
            f.relative_to(SRC_DIR).as_posix()
            for f in SRC_DIR.rglob("*")
            if f.is_file() and not f.is_symlink()
        }
        assert set(vfs.keys()) == src_files

    def test_catalog_payload_matches_src(self) -> None:
        from x4_catalog import build_vfs
        from x4_catalog._core import _read_payload

        vfs = build_vfs(DIST_DIR, prefix="ext_")
        for vpath, entry in vfs.items():
            src_data = (SRC_DIR / vpath).read_bytes()
            packed_data = _read_payload(entry)
            assert packed_data == src_data, f"content mismatch for {vpath}"

    def test_catalog_excludes_content_xml(self) -> None:
        from x4_catalog import build_vfs

        vfs = build_vfs(DIST_DIR, prefix="ext_")
        assert "content.xml" not in vfs, (
            "content.xml should not be packed into the catalog"
        )
