# Translation Compiler Usage Patterns

This document covers the QtPie translation compiler - functions that compile translation entries to Qt's `.ts` XML format.

## TranslationEntry Data Structure

The core data structure representing a translatable string with its translations.

```python
from qtpie.translations.parser import TranslationEntry

entry = TranslationEntry(
    context="@default",  # Widget class name or "@default" for global
    source="Hello",      # Original source string
    translations={"fr": "Bonjour", "de": "Hallo"},  # Language translations
)
```

## compile_to_ts - Generate TS XML String

Compiles translation entries to Qt's `.ts` XML format as a string.

```python
from qtpie.translations import compile_to_ts

xml = compile_to_ts(entries, "fr")  # Compile entries for French
```

### With Widget Context

Entries can be scoped to specific widget classes.

```python
entry = TranslationEntry(
    context="MyWidget",  # Context becomes <name> in XML
    source="Title",
    translations={"fr": "Titre"},
)
```

### With Disambiguation

Same source text with different meanings uses disambiguation.

```python
entry = TranslationEntry(
    context="@default",
    source="Open",
    disambiguation="file_menu",  # Becomes <comment> in XML
    translations={"fr": "Ouvrir"},
)
```

### With Translator Notes

Notes provide context for translators.

```python
entry = TranslationEntry(
    context="@default",
    source="Submit",
    note="For form submission",  # Becomes <extracomment> in XML
    translations={"fr": "Soumettre"},
)
```

### Plural Forms

Use `%n` placeholder with list of plural forms.

```python
entry = TranslationEntry(
    context="@default",
    source="%n file(s)",
    translations={"fr": ["%n fichier", "%n fichiers"]},  # List = plural
)
```

## get_all_languages - Extract Language Codes

Collects all language codes from translation entries.

```python
from qtpie.translations import get_all_languages

languages = get_all_languages(entries)  # Returns set: {"fr", "de", "es"}
```

## compile_translations - Write TS Files to Disk

Compiles entries to `.ts` files in a directory.

```python
from qtpie.translations import compile_translations
from pathlib import Path

# Compile all languages
files = compile_translations(entries, Path("./i18n"))
# Creates: i18n/fr.ts, i18n/de.ts, etc.

# Compile specific languages only
files = compile_translations(entries, Path("./i18n"), languages=["fr"])
# Creates: i18n/fr.ts only
```

## Import Summary

```python
from qtpie.translations import compile_to_ts, compile_translations, get_all_languages
from qtpie.translations.parser import TranslationEntry
```
