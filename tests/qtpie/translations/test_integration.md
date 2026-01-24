# QtPie Translation Integration Patterns

This document describes translation (i18n) patterns in QtPie based on integration tests.

## Basic Translation with `t()`

Mark strings for translation using the `t()` function as the first positional argument to `new()`.

```python
from qtpie import Widget, new, t, widget

@widget
class MyWidget(Widget):
    label: QLabel = new(t("Hello"))
    button: QPushButton = new(t("Click Me"))
```

When no translation is loaded, `t()` returns the source text unchanged.

## Loading Translations and Setting Language

Load translations from YAML and set the active language.

```python
from qtpie.translations import load_translations_from_yaml, set_language

load_translations_from_yaml("translations.yml")
set_language("fr")
```

## Disambiguation with Context

When the same source text has different meanings, use `context=` to disambiguate.

```python
@widget
class MyWidget(Widget):
    menu_open: QLabel = new(t("Open", context="menu"))     # "Ouvrir (menu)"
    file_open: QLabel = new(t("Open", context="file"))     # "Ouvrir (fichier)"
```

## Widget Class as Translation Context

The widget class name automatically becomes the translation context. Define translations under the class name in YAML.

```python
# YAML:
# MyCustomWidget:
#     Title:
#         fr: Titre personnalise

@widget
class MyCustomWidget(Widget):
    label: QLabel = new(t("Title"))  # Uses "MyCustomWidget" context
```

## Global Fallback Context

Translations under `:global:` (or `@default`) apply to all widgets when no widget-specific translation exists.

```python
# YAML:
# :global:
#     Global Text:
#         fr: Texte global

@widget
class AnyWidget(Widget):
    label: QLabel = new(t("Global Text"))  # Falls back to :global:
```

## Runtime Language Switching with Auto-Retranslation

Calling `set_language()` automatically retranslates all widgets using `t()`.

```python
set_language("en")  # Widget shows "Hello"
set_language("fr")  # Widget automatically updates to "Bonjour"
set_language("de")  # Widget automatically updates to "Hallo"
```

## Entrypoint Configuration

Configure translations declaratively with `@entrypoint`.

```python
@entrypoint(
    translations="app.yml",       # Translation file path
    language="fr",                # Initial language (default: "en")
    watch_translations=True,      # Hot-reload in development
)
@widget
class MyApp(Widget):
    label: QLabel = new(t("Hello"))
```

Multiple translation files:

```python
@entrypoint(translations=["a.yml", "b.yml"], language="de")
```

## Form Layout Labels with `t()`

Use `t()` with `label=` in form layouts for translated field labels.

```python
@widget(layout="form", record=Person())
class FormWidget(Widget[Person]):
    name: QLineEdit = new(label=t("Name"))  # Label shows "Nom" in French
```

Labels retranslate automatically when language changes.

## Format String Bindings with `t()`

Combine `t()` with `bind=` for translated format strings that include record values.

```python
@widget(record=Person())
class BindWidget(Widget[Person]):
    info: QLabel = new(bind=t("Name: {name}"))  # "Nom: Alice" in French
```

Format bindings retranslate when language changes, preserving the interpolated values.

## Multiple Translations in Same Widget

Multiple `t()` calls work correctly together and retranslate as a unit.

```python
@widget
class TestWidget(Widget):
    save_btn: QPushButton = new(t("Save"))
    cancel_btn: QPushButton = new(t("Cancel"))
```

## Complex Widget Example

Combining positional args, labels, and buttons with translations.

```python
@widget(layout="form", record=Dog())
class DogEditor(Widget[Dog]):
    name: QLineEdit = new(label=t("Dog's Name"))
    info_label: QLabel = new(t("Info"), label=t("Info"))
    save_btn: QPushButton = new(t("Save"), label=t("Save"))
```

## Test Fixture Pattern

Reset translation state between tests for isolation.

```python
from qtpie.translations import (
    clear_bindings,
    clear_translations,
    enable_memory_store,
    set_language,
)

@pytest.fixture(autouse=True)
def reset_translations() -> None:
    clear_translations()
    clear_bindings()
    enable_memory_store(True)
    set_language("en")
```

## TranslationEntry for Programmatic Loading

Load translations programmatically without YAML files.

```python
from qtpie.translations import load_translations_from_entries
from qtpie.translations.parser import TranslationEntry

entries = [
    TranslationEntry(
        context="@default",
        source="Hello",
        translations={"fr": "Bonjour", "de": "Hallo"},
    )
]
load_translations_from_entries(entries)
```

## Custom Object Retranslation

Register non-Qt objects for retranslation using `register_binding()`.

```python
from qtpie.translations import register_binding

class MyObject:
    def setText(self, value: str) -> None:
        self._text = value

obj = MyObject()
obj.setText("Hello")
register_binding(obj, "text", "Hello")

set_language("fr")  # obj._text becomes "Bonjour"
```

Supports both `setXxx()` methods and property setters. `setXxx()` is tried first.
