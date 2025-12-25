"""Tests for the translations YAML parser."""

from pathlib import Path
from textwrap import dedent

from assertpy import assert_that

from qtpie.translations.parser import (
    deep_merge,
    parse_source_key,
    parse_yaml,
    parse_yaml_files,
)


class TestParseSourceKey:
    """Tests for parse_source_key function."""

    def test_simple_key(self) -> None:
        """Simple key without disambiguation."""
        source, comment = parse_source_key("Save")
        assert_that(source).is_equal_to("Save")
        assert_that(comment).is_none()

    def test_key_with_disambiguation(self) -> None:
        """Key with pipe-separated disambiguation."""
        source, comment = parse_source_key("Open|menu")
        assert_that(source).is_equal_to("Open")
        assert_that(comment).is_equal_to("menu")

    def test_plural_key_with_disambiguation(self) -> None:
        """Plural key with disambiguation."""
        source, comment = parse_source_key("%n file(s)|selected")
        assert_that(source).is_equal_to("%n file(s)")
        assert_that(comment).is_equal_to("selected")

    def test_key_with_multiple_pipes(self) -> None:
        """Only first pipe is used for splitting."""
        source, comment = parse_source_key("a|b|c")
        assert_that(source).is_equal_to("a")
        assert_that(comment).is_equal_to("b|c")


class TestDeepMerge:
    """Tests for deep_merge function."""

    def test_simple_merge(self) -> None:
        """Merge two flat dicts."""
        base = {"a": 1, "b": 2}
        overlay = {"b": 3, "c": 4}
        result = deep_merge(base, overlay)
        assert_that(result).is_equal_to({"a": 1, "b": 3, "c": 4})

    def test_nested_merge(self) -> None:
        """Merge nested dicts."""
        base = {"x": {"a": 1, "b": 2}}
        overlay = {"x": {"b": 3, "c": 4}}
        result = deep_merge(base, overlay)
        assert_that(result).is_equal_to({"x": {"a": 1, "b": 3, "c": 4}})

    def test_deep_nested_merge(self) -> None:
        """Merge deeply nested dicts."""
        base = {"x": {"y": {"a": 1}}}
        overlay = {"x": {"y": {"b": 2}}}
        result = deep_merge(base, overlay)
        assert_that(result).is_equal_to({"x": {"y": {"a": 1, "b": 2}}})

    def test_overlay_replaces_non_dict(self) -> None:
        """Non-dict values are replaced entirely."""
        base = {"x": {"a": 1}}
        overlay = {"x": "replaced"}
        result = deep_merge(base, overlay)
        assert_that(result).is_equal_to({"x": "replaced"})

    def test_base_not_mutated(self) -> None:
        """Original base dict should not be modified."""
        base = {"a": 1}
        overlay = {"b": 2}
        deep_merge(base, overlay)
        assert_that(base).is_equal_to({"a": 1})


class TestParseYaml:
    """Tests for parse_yaml function."""

    def test_basic_translation(self) -> None:
        """Parse basic translation entries."""
        yaml_content = dedent("""
            LoginDialog:
              Username:
                fr: Nom d'utilisateur
                de: Benutzername
        """)

        entries = parse_yaml(yaml_content)

        assert_that(entries).is_length(1)
        assert_that(entries[0].context).is_equal_to("LoginDialog")
        assert_that(entries[0].source).is_equal_to("Username")
        assert_that(entries[0].disambiguation).is_none()
        assert_that(entries[0].translations).is_equal_to(
            {
                "fr": "Nom d'utilisateur",
                "de": "Benutzername",
            }
        )

    def test_global_context(self) -> None:
        """:global: context becomes @default."""
        yaml_content = dedent("""
            :global:
              OK:
                fr: OK
                de: OK
        """)

        entries = parse_yaml(yaml_content)

        assert_that(entries).is_length(1)
        assert_that(entries[0].context).is_equal_to("@default")

    def test_disambiguation(self) -> None:
        """Parse disambiguation with pipe syntax."""
        yaml_content = dedent("""
            MainWindow:
              Open|menu:
                fr: Ouvrir
              Open|status:
                fr: Ouvert
        """)

        entries = parse_yaml(yaml_content)

        assert_that(entries).is_length(2)

        menu_entry = next(e for e in entries if e.disambiguation == "menu")
        assert_that(menu_entry.source).is_equal_to("Open")
        assert_that(menu_entry.translations["fr"]).is_equal_to("Ouvrir")

        status_entry = next(e for e in entries if e.disambiguation == "status")
        assert_that(status_entry.source).is_equal_to("Open")
        assert_that(status_entry.translations["fr"]).is_equal_to("Ouvert")

    def test_translator_note(self) -> None:
        """Parse translator note with :note: syntax."""
        yaml_content = dedent("""
            MainWindow:
              "Save changes?":
                :note: Shown when closing with unsaved work
                fr: "Enregistrer les modifications ?"
        """)

        entries = parse_yaml(yaml_content)

        assert_that(entries).is_length(1)
        assert_that(entries[0].note).is_equal_to("Shown when closing with unsaved work")
        assert_that(entries[0].translations["fr"]).is_equal_to("Enregistrer les modifications ?")

    def test_plural_forms(self) -> None:
        """Parse plural forms as arrays."""
        yaml_content = dedent("""
            MainWindow:
              "%n file(s)":
                en: ["%n file", "%n files"]
                fr: ["%n fichier", "%n fichiers"]
                ru: ["%n файл", "%n файла", "%n файлов"]
        """)

        entries = parse_yaml(yaml_content)

        assert_that(entries).is_length(1)
        assert_that(entries[0].source).is_equal_to("%n file(s)")
        assert_that(entries[0].is_plural).is_true()
        assert_that(entries[0].translations["en"]).is_equal_to(["%n file", "%n files"])
        assert_that(entries[0].translations["fr"]).is_equal_to(["%n fichier", "%n fichiers"])
        assert_that(entries[0].translations["ru"]).is_equal_to(["%n файл", "%n файла", "%n файлов"])

    def test_plural_with_disambiguation(self) -> None:
        """Parse plural forms with disambiguation."""
        yaml_content = dedent("""
            MainWindow:
              "%n item(s)|selected":
                en: ["%n item selected", "%n items selected"]
                fr: ["%n élément sélectionné", "%n éléments sélectionnés"]
        """)

        entries = parse_yaml(yaml_content)

        assert_that(entries).is_length(1)
        assert_that(entries[0].source).is_equal_to("%n item(s)")
        assert_that(entries[0].disambiguation).is_equal_to("selected")
        assert_that(entries[0].is_plural).is_true()

    def test_multiple_contexts(self) -> None:
        """Parse multiple contexts."""
        yaml_content = dedent("""
            :global:
              OK:
                fr: OK

            LoginDialog:
              Username:
                fr: Nom d'utilisateur

            MainWindow:
              Save:
                fr: Enregistrer
        """)

        entries = parse_yaml(yaml_content)

        assert_that(entries).is_length(3)

        contexts = {e.context for e in entries}
        assert_that(contexts).is_equal_to({"@default", "LoginDialog", "MainWindow"})

    def test_empty_yaml(self) -> None:
        """Empty YAML returns empty list."""
        entries = parse_yaml("")
        assert_that(entries).is_empty()

    def test_is_plural_property(self) -> None:
        """is_plural property correctly identifies plural entries."""
        yaml_content = dedent("""
            Test:
              singular:
                en: Hello
              plural:
                en: ["%n item", "%n items"]
        """)

        entries = parse_yaml(yaml_content)

        singular = next(e for e in entries if e.source == "singular")
        plural = next(e for e in entries if e.source == "plural")

        assert_that(singular.is_plural).is_false()
        assert_that(plural.is_plural).is_true()


class TestParseYamlFiles:
    """Tests for parse_yaml_files with file merging."""

    def test_merge_multiple_files(self, tmp_path: Path) -> None:
        """Multiple files are deep merged."""
        file1 = tmp_path / "base.tr.yml"
        file1.write_text(
            dedent("""
            :global:
              OK:
                en: OK
                fr: OK

            LoginDialog:
              Username:
                en: Username
                fr: Nom d'utilisateur
        """)
        )

        file2 = tmp_path / "german.tr.yml"
        file2.write_text(
            dedent("""
            :global:
              OK:
                de: OK

            LoginDialog:
              Username:
                de: Benutzername
        """)
        )

        entries = parse_yaml_files([file1, file2])

        # Should have 2 entries (OK and Username)
        assert_that(entries).is_length(2)

        ok_entry = next(e for e in entries if e.source == "OK")
        assert_that(ok_entry.translations).is_equal_to(
            {
                "en": "OK",
                "fr": "OK",
                "de": "OK",
            }
        )

        username_entry = next(e for e in entries if e.source == "Username")
        assert_that(username_entry.translations).is_equal_to(
            {
                "en": "Username",
                "fr": "Nom d'utilisateur",
                "de": "Benutzername",
            }
        )

    def test_later_files_override(self, tmp_path: Path) -> None:
        """Later files override earlier ones."""
        file1 = tmp_path / "base.tr.yml"
        file1.write_text(
            dedent("""
            Test:
              Hello:
                en: Hello
        """)
        )

        file2 = tmp_path / "override.tr.yml"
        file2.write_text(
            dedent("""
            Test:
              Hello:
                en: Hi there
        """)
        )

        entries = parse_yaml_files([file1, file2])

        assert_that(entries).is_length(1)
        assert_that(entries[0].translations["en"]).is_equal_to("Hi there")

    def test_context_split_files(self, tmp_path: Path) -> None:
        """Different contexts can be in different files."""
        login_file = tmp_path / "LoginDialog.tr.yml"
        login_file.write_text(
            dedent("""
            LoginDialog:
              Username:
                en: Username
              Password:
                en: Password
        """)
        )

        main_file = tmp_path / "MainWindow.tr.yml"
        main_file.write_text(
            dedent("""
            MainWindow:
              Save:
                en: Save
              Open:
                en: Open
        """)
        )

        entries = parse_yaml_files([login_file, main_file])

        assert_that(entries).is_length(4)

        login_entries = [e for e in entries if e.context == "LoginDialog"]
        main_entries = [e for e in entries if e.context == "MainWindow"]

        assert_that(login_entries).is_length(2)
        assert_that(main_entries).is_length(2)
