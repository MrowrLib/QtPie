# Translation Parser - Usage Patterns

This document describes the YAML translation parser patterns used in QtPie's i18n system.

## Imports

```python
from qtpie.translations import deep_merge, parse_source_key, parse_yaml, parse_yaml_files
```

## Global Translations

Use `:global:` context for translations available to all widgets. Parsed entries have `context="@default"`.

```python
yaml_content = """
:global:
    Hello:
        fr: Bonjour
"""
entries = parse_yaml(yaml_content)
# entries[0].context == "@default"
# entries[0].source == "Hello"
# entries[0].translations == {"fr": "Bonjour"}
```

## Widget-Specific Context

Use the widget class name as the context key for widget-scoped translations.

```python
yaml_content = """
MyWidget:
    Title:
        fr: Titre
"""
entries = parse_yaml(yaml_content)
# entries[0].context == "MyWidget"
# entries[0].source == "Title"
```

## Disambiguation

Use `source|context` syntax when the same source text has different meanings.

```python
yaml_content = """
:global:
    "Open|menu":
        fr: Ouvrir
"""
entries = parse_yaml(yaml_content)
# entries[0].source == "Open"
# entries[0].disambiguation == "menu"
```

The `parse_source_key()` function handles this parsing:

```python
source, disambig = parse_source_key("Open|menu")
# source == "Open", disambig == "menu"
```

## Translator Notes

Add `:note:` key for translator context (not a language code).

```python
yaml_content = """
:global:
    Submit:
        :note: This is for form submission
        fr: Soumettre
"""
entries = parse_yaml(yaml_content)
# entries[0].note == "This is for form submission"
```

## Plural Forms

Use a list of forms per language for pluralization with `%n` placeholder.

```python
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
# entries[0].translations["en"] == ["%n file", "%n files"]
```

## Parsing Files

Use `parse_yaml_files()` to parse from disk. Supports single file or multiple files with automatic merging.

```python
from pathlib import Path
entries = parse_yaml_files([Path("translations.yml")])
```

Multiple files are merged together:

```python
entries = parse_yaml_files([Path("base.yml"), Path("overrides.yml")])
```

## Deep Merge Utility

The `deep_merge()` function combines dictionaries recursively, with overlay values winning on conflict.

```python
base = {"x": {"a": 1}}
overlay = {"x": {"b": 2}}
result = deep_merge(base, overlay)
# result == {"x": {"a": 1, "b": 2}}
```
