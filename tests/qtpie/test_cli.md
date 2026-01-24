# QtPie CLI Usage Patterns

This document describes the CLI commands and usage patterns demonstrated in `test_cli.py`.

## CLI Entry Point

The QtPie CLI is accessed via the `qtpie` command and uses Typer for command handling.

```python
from qtpie.cli.main import app
```

Running `qtpie` with no arguments or `--help` shows available commands.

## Translation Commands (`tr`)

The `tr` subcommand provides translation-related utilities for internationalization.

### `qtpie tr compile` - Compile YAML to .ts Files

Compiles YAML translation files into Qt `.ts` format.

**Basic usage:**
```bash
qtpie tr compile translations.yml -o ./i18n/
```

**Filter specific languages:**
```bash
qtpie tr compile translations.yml -o ./i18n/ --lang fr --lang de
```

**Multiple input files:**
```bash
qtpie tr compile a.yml b.yml -o ./i18n/
```

### `qtpie tr list` - List Translations

Shows all translations in a YAML file, grouped by context.

```bash
qtpie tr list translations.yml
```

Output includes:
- Languages available (e.g., `fr`, `de`, `es`)
- Entry count
- Source strings grouped by context (`(global)` or `[WidgetName]`)
- Disambiguation hints when present

## Translation YAML Format

### Global Translations

Use `:global:` for translations available to all widgets:

```yaml
:global:
    Hello:
        fr: Bonjour
        de: Hallo
```

### Widget-Specific Translations

Use the widget class name as the context:

```yaml
MyWidget:
    Title:
        fr: Titre
```

### Disambiguation

For the same source text with different meanings, use `|` separator:

```yaml
:global:
    "Open|menu":
        fr: Ouvrir
    "Open|status":
        fr: Ouvert
```

## Generated .ts File Format

The compile command produces standard Qt `.ts` XML files:

```xml
<?xml version="1.0" encoding="utf-8"?>
<TS version="2.1" language="fr">
    <context>
        <name>@default</name>
        <message>
            <source>Hello</source>
            <translation>Bonjour</translation>
        </message>
    </context>
</TS>
```

## Testing CLI Commands

Tests use Typer's `CliRunner` for invoking commands:

```python
from typer.testing import CliRunner
runner = CliRunner()
result = runner.invoke(app, ["tr", "compile", str(yaml_file), "-o", str(output_dir)])
```

Check results via `result.exit_code`, `result.stdout`, and `result.output`.
