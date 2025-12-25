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
        assert_that(result.stdout).contains("Translation tools")

    def test_no_args_shows_help(self) -> None:
        """qtpie with no args shows help."""
        result = runner.invoke(app, [])
        # Exit code 2 is expected for no_args_is_help=True
        assert_that(result.stdout).contains("Usage:")


class TestTrCommand:
    """Tests for the qtpie tr command."""

    def test_tr_help(self) -> None:
        """qtpie tr --help shows compile command."""
        result = runner.invoke(app, ["tr", "--help"])
        assert_that(result.exit_code).is_equal_to(0)
        assert_that(result.stdout).contains("compile")

    def test_tr_no_args_shows_help(self) -> None:
        """qtpie tr with no args shows help."""
        result = runner.invoke(app, ["tr"])
        # Exit code 2 is expected for no_args_is_help=True
        assert_that(result.stdout).contains("Usage:")


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
MyWidget:
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
        assert_that(result.stdout).contains("Created 2 .ts files")

    def test_compile_with_qm(self, tmp_path: Path) -> None:
        """qtpie tr compile --qm also creates .qm files."""
        yaml_content = """
MyWidget:
  Hello:
    fr: Bonjour
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
                "--qm",
            ],
        )

        assert_that(result.exit_code).is_equal_to(0)
        assert_that((output_dir / "fr.ts").exists()).is_true()
        assert_that((output_dir / "fr.qm").exists()).is_true()
        assert_that(result.stdout).contains(".ts and")
        assert_that(result.stdout).contains(".qm files")

    def test_compile_with_language_filter(self, tmp_path: Path) -> None:
        """qtpie tr compile --lang filters languages."""
        yaml_content = """
MyWidget:
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
MyWidget:
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

    def test_compile_verbose(self, tmp_path: Path) -> None:
        """qtpie tr compile --verbose shows detailed output."""
        yaml_content = """
MyWidget:
  Hello:
    fr: Bonjour
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
                "-v",
            ],
        )

        assert_that(result.exit_code).is_equal_to(0)
        assert_that(result.stdout).contains("Parsing")
        assert_that(result.stdout).contains("Found languages")

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

    def test_compile_missing_output_error(self, tmp_path: Path) -> None:
        """qtpie tr compile requires --output."""
        yaml_content = "MyWidget:\n  Hello:\n    fr: Bonjour\n"

        yaml_file = tmp_path / "app.yml"
        yaml_file.write_text(yaml_content)

        result = runner.invoke(
            app,
            [
                "tr",
                "compile",
                str(yaml_file),
            ],
        )

        # Exit code 2 means missing required option
        assert_that(result.exit_code).is_equal_to(2)

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
        # Error message goes to output (typer combines stdout/stderr)
        assert_that(result.output).contains("No translation entries")
