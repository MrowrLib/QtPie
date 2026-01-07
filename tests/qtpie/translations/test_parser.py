"""Tests for the YAML parser."""

import tempfile
from pathlib import Path

from assertpy import assert_that

from qtpie.translations import deep_merge, parse_source_key, parse_yaml, parse_yaml_files


class TestParseSourceKey:
    """Tests for parsing source|disambiguation keys."""

    def test_simple_source(self) -> None:
        source, disambig = parse_source_key("Hello")
        assert_that(source).is_equal_to("Hello")
        assert_that(disambig).is_none()

    def test_source_with_disambiguation(self) -> None:
        source, disambig = parse_source_key("Open|menu")
        assert_that(source).is_equal_to("Open")
        assert_that(disambig).is_equal_to("menu")

    def test_source_with_pipe_in_text(self) -> None:
        # Only first pipe is treated as separator
        source, disambig = parse_source_key("A | B|context")
        assert_that(source).is_equal_to("A | B")
        assert_that(disambig).is_equal_to("context")


class TestDeepMerge:
    """Tests for deep merging dictionaries."""

    def test_merge_simple(self) -> None:
        base: dict[str, object] = {"a": 1}
        overlay: dict[str, object] = {"b": 2}
        result = deep_merge(base, overlay)
        assert_that(result).is_equal_to({"a": 1, "b": 2})

    def test_merge_nested(self) -> None:
        base: dict[str, object] = {"x": {"a": 1}}
        overlay: dict[str, object] = {"x": {"b": 2}}
        result = deep_merge(base, overlay)
        assert_that(result).is_equal_to({"x": {"a": 1, "b": 2}})

    def test_merge_overlay_wins(self) -> None:
        base: dict[str, object] = {"a": 1}
        overlay: dict[str, object] = {"a": 2}
        result = deep_merge(base, overlay)
        assert_that(result).is_equal_to({"a": 2})


class TestParseYaml:
    """Tests for parsing YAML content."""

    def test_parse_simple(self) -> None:
        # YAML structure: context: {source: {lang: translation}}
        yaml_content = """
:global:
    Hello:
        fr: Bonjour
"""
        entries = parse_yaml(yaml_content)
        assert_that(entries).is_length(1)
        assert_that(entries[0].source).is_equal_to("Hello")
        assert_that(entries[0].translations).is_equal_to({"fr": "Bonjour"})
        assert_that(entries[0].context).is_equal_to("@default")

    def test_parse_with_context(self) -> None:
        yaml_content = """
MyWidget:
    Title:
        fr: Titre
"""
        entries = parse_yaml(yaml_content)
        assert_that(entries).is_length(1)
        assert_that(entries[0].context).is_equal_to("MyWidget")
        assert_that(entries[0].source).is_equal_to("Title")

    def test_parse_global_context(self) -> None:
        yaml_content = """
:global:
    Hello:
        fr: Bonjour
"""
        entries = parse_yaml(yaml_content)
        assert_that(entries).is_length(1)
        assert_that(entries[0].context).is_equal_to("@default")

    def test_parse_with_disambiguation(self) -> None:
        yaml_content = """
:global:
    "Open|menu":
        fr: Ouvrir
"""
        entries = parse_yaml(yaml_content)
        assert_that(entries).is_length(1)
        assert_that(entries[0].source).is_equal_to("Open")
        assert_that(entries[0].disambiguation).is_equal_to("menu")

    def test_parse_with_note(self) -> None:
        yaml_content = """
:global:
    Submit:
        :note: This is for form submission
        fr: Soumettre
"""
        entries = parse_yaml(yaml_content)
        assert_that(entries).is_length(1)
        assert_that(entries[0].note).is_equal_to("This is for form submission")

    def test_parse_plural(self) -> None:
        yaml_content = """
:global:
    "%n file(s)":
        en:
            - "%n file"
            - "%n files"
        fr:
            - "%n fichier"
            - "%n fichiers"
"""
        entries = parse_yaml(yaml_content)
        assert_that(entries).is_length(1)
        assert_that(entries[0].translations["en"]).is_equal_to(["%n file", "%n files"])
        assert_that(entries[0].translations["fr"]).is_equal_to(["%n fichier", "%n fichiers"])


class TestParseYamlFiles:
    """Tests for parsing YAML files from disk."""

    def test_parse_single_file(self) -> None:
        yaml_content = """
:global:
    Hello:
        fr: Bonjour
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            path = Path(f.name)

        try:
            entries = parse_yaml_files([path])
            assert_that(entries).is_length(1)
            assert_that(entries[0].source).is_equal_to("Hello")
        finally:
            path.unlink()

    def test_parse_multiple_files_merge(self) -> None:
        yaml1 = """
:global:
    Hello:
        fr: Bonjour
"""
        yaml2 = """
:global:
    Goodbye:
        fr: Au revoir
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f1:
            f1.write(yaml1)
            f1.flush()
            path1 = Path(f1.name)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f2:
            f2.write(yaml2)
            f2.flush()
            path2 = Path(f2.name)

        try:
            entries = parse_yaml_files([path1, path2])
            assert_that(entries).is_length(2)
            sources = [e.source for e in entries]
            assert_that(sources).contains("Hello", "Goodbye")
        finally:
            path1.unlink()
            path2.unlink()
