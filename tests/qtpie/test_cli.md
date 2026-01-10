# CLI Test Summary

## Main CLI Help

The qtpie CLI shows help text when invoked with no arguments or `--help`.

```python
def test_help_shows_commands(self) -> None:
    """qtpie --help shows available commands."""
    result = runner.invoke(app, ["--help"])
    assert_that(result.exit_code).is_equal_to(0)
    assert_that(result.stdout).contains("tr")
```

## Translation Command (`qtpie tr`)

The `tr` subcommand provides translation file management with `compile` and `list` subcommands.

```python
def test_tr_help(self) -> None:
    """qtpie tr --help shows compile command."""
    result = runner.invoke(app, ["tr", "--help"])
    assert_that(result.exit_code).is_equal_to(0)
    assert_that(result.stdout).contains("compile")
    assert_that(result.stdout).contains("list")
```

## Translation Compilation (`qtpie tr compile`)

Converts YAML translation files to Qt .ts files. Supports multiple input files, language filtering with `--lang`, and output directory specification with `-o`.

```python
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
```

```python
def test_compile_with_language_filter(self, tmp_path: Path) -> None:
    """qtpie tr compile --lang filters languages."""
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
```

## Translation Listing (`qtpie tr list`)

Displays all translations from YAML files, grouped by context, showing languages, entry counts, and disambiguation.

```python
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
```

```python
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
```
