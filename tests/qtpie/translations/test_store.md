# Translation Store Usage Patterns

This document describes the translation store API patterns demonstrated in `test_store.py`.

## Language Management

The translation system has a global language setting that controls which translations are used.

```python
from qtpie.translations import get_language, set_language

# Default language is English
get_language()  # Returns "en"

# Change language at runtime
set_language("fr")
```

## Loading Translations

Translations are loaded via `TranslationEntry` objects containing context, source text, and language mappings.

```python
from qtpie.translations import load_translations_from_entries
from qtpie.translations.parser import TranslationEntry

entries = [
    TranslationEntry(
        context="@default",
        source="Hello",
        translations={"fr": "Bonjour"},
    )
]
load_translations_from_entries(entries)
```

## Basic Lookup

Look up translations with context and source text. Returns the source text if no translation exists.

```python
from qtpie.translations import lookup

result = lookup("@default", "Hello")  # Returns "Bonjour" if fr, else "Hello"
```

## Disambiguation

When the same source text has different meanings, use disambiguation strings.

```python
entries = [
    TranslationEntry(
        context="@default",
        source="Open",
        disambiguation="file_menu",
        translations={"fr": "Ouvrir (fichier)"},
    ),
]

# Lookup with disambiguation
result = lookup("@default", "Open", "file_menu")
```

## Context Hierarchy

Widget-specific translations override global (`@default`) translations. Lookups fall back to `@default` if no widget-specific translation exists.

```python
# Widget-specific context takes precedence
result = lookup("MyWidget", "Title")  # Uses MyWidget's translation if available

# Falls back to @default if no widget-specific translation
result = lookup("MyWidget", "Global")  # Uses @default's translation
```

## Plural Forms

Plurals use `%n` as a placeholder and provide singular/plural form arrays.

```python
from qtpie.translations import lookup_plural

entries = [
    TranslationEntry(
        context="@default",
        source="%n item(s)",
        translations={"en": ["%n item", "%n items"]},
    )
]

lookup_plural("@default", "%n item(s)", 1)   # Returns "1 item"
lookup_plural("@default", "%n item(s)", 5)   # Returns "5 items"
lookup_plural("@default", "%n item(s)", 42)  # Returns "42 files"
```

## State Management

Functions for managing translation and binding state, useful for testing.

```python
from qtpie.translations import (
    clear_translations,
    clear_bindings,
    get_binding_count,
    get_format_binding_count,
)

clear_translations()  # Clear all loaded translations
clear_bindings()      # Clear all widget bindings

# Check binding counts
get_binding_count()        # Number of widget bindings
get_format_binding_count() # Number of format bindings
```

## Key Conventions

- **@default context**: Global translations accessible from any widget
- **Widget context**: Class name (e.g., "MyWidget") for widget-specific translations
- **Disambiguation**: Use when same source text has different meanings
- **%n placeholder**: Replaced with count in plural forms
- **Fallback chain**: Widget context → @default context → source text
