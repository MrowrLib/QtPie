# Translatable Feature Analysis

This document describes the usage patterns for QtPie's translation system, specifically the `t()` function and `Translatable` class.

## The `t()` Function

The primary entry point for marking strings as translatable. Returns a `Translatable` marker object for lazy resolution.

```python
from qtpie.translations import t

result = t("Hello")  # Basic usage - mark string for translation
```

## Disambiguation with Context

When the same source text has different meanings (e.g., "Open" as a menu item vs. status), use the `context` parameter:

```python
menu_open = t("Open", context="menu")     # For menu items
status_open = t("Open", context="action")  # For action status
```

## Translation Resolution

The `Translatable.resolve()` method returns the translated string based on current language:

```python
marker = t("Hello")
translated_text = marker.resolve()  # Returns translated string or source if no translation
```

## Loading Translations Programmatically

Translations can be loaded from `TranslationEntry` objects. The `@default` context is used for global translations:

```python
from qtpie.translations import load_translations_from_entries, set_language
from qtpie.translations.parser import TranslationEntry

entries = [
    TranslationEntry(
        context="@default",
        source="Hello",
        translations={"fr": "Bonjour"},
    )
]
load_translations_from_entries(entries)
set_language("fr")
```

## Widget-Specific Translations

Translations can be scoped to specific widgets using context:

```python
from qtpie.translations import set_translation_context

# Set context to widget class name
set_translation_context("MyWidget")

# Now t("Title") will look for translations under "MyWidget" context first
marker = t("Title")
```

## Plural Support

Use `%n` placeholder for count-dependent translations. Call the marker with a count to get the correct plural form:

```python
marker = t("%n file(s)")

singular = marker(1)  # "1 file"
plural = marker(5)    # "5 files"
zero = marker(0)      # "0 files"
```

Translation entries for plurals use a list instead of a single string:

```python
TranslationEntry(
    context="@default",
    source="%n file(s)",
    translations={"en": ["%n file", "%n files"]},  # [singular, plural]
)
```

## Key Translation Functions

| Function | Purpose |
|----------|---------|
| `t("text")` | Mark string for translation |
| `t("text", context="x")` | Mark with disambiguation context |
| `set_language("fr")` | Set active language |
| `set_translation_context("Widget")` | Set widget context for resolution |
| `get_translation_context()` | Get current widget context |
| `load_translations_from_entries(entries)` | Load translations programmatically |
| `clear_translations()` | Reset all translation state |
| `enable_memory_store(True)` | Use in-memory store (for testing/dev) |

## Translatable Properties

The `Translatable` object is a frozen dataclass with these properties:

- `text` - The source text string
- `context` - Optional disambiguation context (defaults to `None`)
- Hashable and supports equality comparison
