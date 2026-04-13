"""Mod structure validation and build integrity tests."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
DIST_DIR = PROJECT_ROOT / "dist"
CONTENT_XML = PROJECT_ROOT / "content.xml"

REQUIRED_CONTENT_ATTRS = ("id", "version", "name")


class TestValidate:
    """Pre-build validation — XML well-formedness and content.xml structure."""

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
