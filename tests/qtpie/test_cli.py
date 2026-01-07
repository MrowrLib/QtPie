"""Tests for the qtpie CLI."""

from pathlib import Path

from assertpy import assert_that
from typer.testing import CliRunner

from qtpie.cli.main import app

runner = CliRunner()


class TestQtpieCli:
    """Tests for the main qtpie CLI."""

    def test_help_shows_commands(self) -> None:
        """qtpie --help shows available commands."""
        result = runner.invoke(app, ["--help"])
        assert_that(result.exit_code).is_equal_to(0)
        assert_that(result.stdout).contains("tr")

    def test_no_args_shows_help(self) -> None:
        """qtpie with no args shows help."""
        result = runner.invoke(app, [])
        assert_that(result.stdout).contains("Usage:")


class TestTrCommand:
    """Tests for the qtpie tr command."""

    def test_tr_help(self) -> None:
        """qtpie tr --help shows compile command."""
        result = runner.invoke(app, ["tr", "--help"])
        assert_that(result.exit_code).is_equal_to(0)
        assert_that(result.stdout).contains("compile")
        assert_that(result.stdout).contains("list")

    def test_tr_no_args_shows_help(self) -> None:
        """qtpie tr with no args shows help."""
        result = runner.invoke(app, ["tr"])
        assert_that(result.output).contains("Usage:")


class TestTrCompileCommand:
    """Tests for the qtpie tr compile command."""

    def test_compile_help(self) -> None:
        """qtpie tr compile --help shows options."""
        result = runner.invoke(app, ["tr", "compile", "--help"])
        assert_that(result.exit_code).is_equal_to(0)
        assert_that(result.stdout).contains("--output")
        assert_that(result.stdout).contains("--qm")
        assert_that(result.stdout).contains("--lang")

    def test_compile_basic(self, tmp_path: Path) -> None:
        """qtpie tr compile creates .ts files."""
        yaml_content = """
:global:
    Hello:
        fr: Bonjour
        de: Hallo
"""
        yaml_file = tmp_path / "app.yml"
        yaml_file.write_text(yaml_content)
        output_dir = tmp_path / "i18n"

        result = runner.invoke(
            app,
            [
                "tr",
                "compile",
                str(yaml_file),
                "-o",
                str(output_dir),
            ],
        )

        assert_that(result.exit_code).is_equal_to(0)
        assert_that((output_dir / "fr.ts").exists()).is_true()
        assert_that((output_dir / "de.ts").exists()).is_true()
        assert_that(result.stdout).contains("Generated 2 .ts file(s)")

    def test_compile_with_language_filter(self, tmp_path: Path) -> None:
        """qtpie tr compile --lang filters languages."""
        yaml_content = """
:global:
    Hello:
        fr: Bonjour
        de: Hallo
        es: Hola
"""
        yaml_file = tmp_path / "app.yml"
        yaml_file.write_text(yaml_content)
        output_dir = tmp_path / "i18n"

        result = runner.invoke(
            app,
            [
                "tr",
                "compile",
                str(yaml_file),
                "-o",
                str(output_dir),
                "--lang",
                "fr",
            ],
        )

        assert_that(result.exit_code).is_equal_to(0)
        assert_that((output_dir / "fr.ts").exists()).is_true()
        assert_that((output_dir / "de.ts").exists()).is_false()
        assert_that((output_dir / "es.ts").exists()).is_false()

    def test_compile_multiple_languages(self, tmp_path: Path) -> None:
        """qtpie tr compile --lang can be repeated."""
        yaml_content = """
:global:
    Hello:
        fr: Bonjour
        de: Hallo
        es: Hola
"""
        yaml_file = tmp_path / "app.yml"
        yaml_file.write_text(yaml_content)
        output_dir = tmp_path / "i18n"

        result = runner.invoke(
            app,
            [
                "tr",
                "compile",
                str(yaml_file),
                "-o",
                str(output_dir),
                "--lang",
                "fr",
                "--lang",
                "de",
            ],
        )

        assert_that(result.exit_code).is_equal_to(0)
        assert_that((output_dir / "fr.ts").exists()).is_true()
        assert_that((output_dir / "de.ts").exists()).is_true()
        assert_that((output_dir / "es.ts").exists()).is_false()

    def test_compile_multiple_files(self, tmp_path: Path) -> None:
        """qtpie tr compile accepts multiple YAML files."""
        yaml1 = """
WidgetA:
    Hello:
        fr: Bonjour
"""
        yaml2 = """
WidgetB:
    Goodbye:
        fr: Au revoir
"""
        file1 = tmp_path / "a.yml"
        file2 = tmp_path / "b.yml"
        file1.write_text(yaml1)
        file2.write_text(yaml2)
        output_dir = tmp_path / "i18n"

        result = runner.invoke(
            app,
            [
                "tr",
                "compile",
                str(file1),
                str(file2),
                "-o",
                str(output_dir),
            ],
        )

        assert_that(result.exit_code).is_equal_to(0)
        assert_that((output_dir / "fr.ts").exists()).is_true()

        # Check both contexts are in the output
        ts_content = (output_dir / "fr.ts").read_text()
        assert_that(ts_content).contains("WidgetA")
        assert_that(ts_content).contains("WidgetB")

    def test_compile_missing_file_error(self) -> None:
        """qtpie tr compile errors on missing file."""
        result = runner.invoke(
            app,
            [
                "tr",
                "compile",
                "/nonexistent/file.yml",
                "-o",
                "/tmp/out",
            ],
        )

        assert_that(result.exit_code).is_not_equal_to(0)

    def test_compile_empty_yaml_error(self, tmp_path: Path) -> None:
        """qtpie tr compile errors on empty YAML."""
        yaml_file = tmp_path / "empty.yml"
        yaml_file.write_text("")
        output_dir = tmp_path / "i18n"

        result = runner.invoke(
            app,
            [
                "tr",
                "compile",
                str(yaml_file),
                "-o",
                str(output_dir),
            ],
        )

        assert_that(result.exit_code).is_equal_to(1)
        assert_that(result.output).contains("No translations found")

    def test_compile_ts_file_content(self, tmp_path: Path) -> None:
        """Generated .ts file has correct XML content."""
        yaml_content = """
:global:
    Hello:
        fr: Bonjour
"""
        yaml_file = tmp_path / "app.yml"
        yaml_file.write_text(yaml_content)
        output_dir = tmp_path / "i18n"

        result = runner.invoke(
            app,
            ["tr", "compile", str(yaml_file), "-o", str(output_dir)],
        )

        assert_that(result.exit_code).is_equal_to(0)

        ts_content = (output_dir / "fr.ts").read_text()
        assert_that(ts_content).contains('<?xml version="1.0" encoding="utf-8"?>')
        assert_that(ts_content).contains('<TS version="2.1" language="fr">')
        assert_that(ts_content).contains("<source>Hello</source>")
        assert_that(ts_content).contains("<translation>Bonjour</translation>")


class TestTrListCommand:
    """Tests for the qtpie tr list command."""

    def test_list_help(self) -> None:
        """qtpie tr list --help shows usage."""
        result = runner.invoke(app, ["tr", "list", "--help"])
        assert_that(result.exit_code).is_equal_to(0)
        assert_that(result.stdout).contains("INPUT_FILES")

    def test_list_basic(self, tmp_path: Path) -> None:
        """qtpie tr list shows translations."""
        yaml_content = """
:global:
    Hello:
        fr: Bonjour
    Goodbye:
        fr: Au revoir
"""
        yaml_file = tmp_path / "app.yml"
        yaml_file.write_text(yaml_content)

        result = runner.invoke(app, ["tr", "list", str(yaml_file)])

        assert_that(result.exit_code).is_equal_to(0)
        assert_that(result.stdout).contains("Languages:")
        assert_that(result.stdout).contains("fr")
        assert_that(result.stdout).contains("Entries: 2")
        assert_that(result.stdout).contains("Hello")
        assert_that(result.stdout).contains("Goodbye")

    def test_list_with_contexts(self, tmp_path: Path) -> None:
        """qtpie tr list groups by context."""
        yaml_content = """
:global:
    Hello:
        fr: Bonjour
MyWidget:
    Title:
        fr: Titre
"""
        yaml_file = tmp_path / "app.yml"
        yaml_file.write_text(yaml_content)

        result = runner.invoke(app, ["tr", "list", str(yaml_file)])

        assert_that(result.exit_code).is_equal_to(0)
        assert_that(result.stdout).contains("(global)")
        assert_that(result.stdout).contains("[MyWidget]")

    def test_list_with_disambiguation(self, tmp_path: Path) -> None:
        """qtpie tr list shows disambiguation."""
        yaml_content = """
:global:
    "Open|menu":
        fr: Ouvrir
"""
        yaml_file = tmp_path / "app.yml"
        yaml_file.write_text(yaml_content)

        result = runner.invoke(app, ["tr", "list", str(yaml_file)])

        assert_that(result.exit_code).is_equal_to(0)
        assert_that(result.stdout).contains("Open")
        assert_that(result.stdout).contains("menu")

    def test_list_empty_file(self, tmp_path: Path) -> None:
        """qtpie tr list handles empty YAML."""
        yaml_file = tmp_path / "empty.yml"
        yaml_file.write_text("")

        result = runner.invoke(app, ["tr", "list", str(yaml_file)])

        assert_that(result.exit_code).is_equal_to(0)
        assert_that(result.stdout).contains("No translations found")

    def test_list_multiple_languages(self, tmp_path: Path) -> None:
        """qtpie tr list shows all languages."""
        yaml_content = """
:global:
    Hello:
        fr: Bonjour
        de: Hallo
        es: Hola
"""
        yaml_file = tmp_path / "app.yml"
        yaml_file.write_text(yaml_content)

        result = runner.invoke(app, ["tr", "list", str(yaml_file)])

        assert_that(result.exit_code).is_equal_to(0)
        assert_that(result.stdout).contains("fr")
        assert_that(result.stdout).contains("de")
        assert_that(result.stdout).contains("es")
