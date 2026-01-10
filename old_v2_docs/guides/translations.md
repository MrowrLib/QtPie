# Translations Guide

QtPie provides a comprehensive internationalization (i18n) system for building multilingual desktop applications. The translation system combines a declarative API with YAML-based translation files, automatic retranslation on language changes, and optional hot-reload during development.

## Table of Contents

- [Quick Start](#quick-start)
- [The t() Function](#the-t-function)
- [Translation Files (YAML Format)](#translation-files-yaml-format)
- [Disambiguation](#disambiguation)
- [Plurals](#plurals)
- [Widget Contexts](#widget-contexts)
- [Runtime Language Switching](#runtime-language-switching)
- [Using with @entrypoint](#using-with-entrypoint)
- [Hot-Reload for Development](#hot-reload-for-development)
- [CLI Commands](#cli-commands)
- [Advanced Usage](#advanced-usage)

## Quick Start

Mark strings for translation using `t()`, create a YAML translation file, and configure the entrypoint:

```python
from PySide6.QtWidgets import QLabel, QPushButton
from qtpie import Widget, entrypoint, new, t, widget

@entrypoint(
    translations="translations.yml",
    language="fr"
)
@widget
class MyApp(Widget):
    greeting: QLabel = new(t("Hello"))
    button: QPushButton = new(t("Click Me"))
```

Create `translations.yml`:

```yaml
:global:
    Hello:
        en: Hello
        fr: Bonjour
        de: Hallo

    Click Me:
        en: Click Me
        fr: Cliquez-moi
        de: Klick mich
```

Run your app and it will display the French translations.

## The t() Function

The `t()` function creates a `Translatable` marker that resolves to translated text when widgets are created.

### Basic Usage

```python
from qtpie import t, new

# Mark a string for translation
label: QLabel = new(t("Hello World"))

# Works with any widget expecting text
button: QPushButton = new(t("Submit"))
action: QAction = new(t("Open File"))
```

### Without Translations

If no translation is loaded, `t()` returns the source text:

```python
# No translations loaded
label: QLabel = new(t("Hello"))  # Shows "Hello"
```

### With Context Parameter

Use `context=` for disambiguation when the same source text has different meanings:

```python
# Same word, different contexts
menu_open: QAction = new(t("Open", context="menu"))
status_open: QLabel = new(t("Open", context="status"))
```

### The Translatable Object

`t()` returns a `Translatable` dataclass that is frozen (immutable) and hashable:

```python
marker = t("Hello")
print(marker.text)      # "Hello"
print(marker.context)   # None

marker_with_ctx = t("Open", context="menu")
print(marker_with_ctx.context)  # "menu"

# Translatable objects are hashable and comparable
assert t("Hello") == t("Hello")
assert t("Open", context="menu") == t("Open", context="menu")
assert t("Open", context="menu") != t("Open", context="file")
```

## Translation Files (YAML Format)

Translation files use YAML format with a three-level structure:

```
context:
  source_text:
    language: translation
```

### Global Translations

Use `:global:` for translations available to all widgets:

```yaml
:global:
    Hello:
        en: Hello
        fr: Bonjour
        de: Hallo
        es: Hola

    Goodbye:
        en: Goodbye
        fr: Au revoir
        de: Auf Wiedersehen
```

**Note:** `:global:` translates internally to `@default` context.

### Simple Example

```yaml
:global:
    Submit:
        en: Submit
        fr: Soumettre
        de: Absenden

    Cancel:
        en: Cancel
        fr: Annuler
        de: Abbrechen
```

### Multiple Languages

Define as many languages as you need:

```yaml
:global:
    Welcome:
        en: Welcome
        fr: Bienvenue
        de: Willkommen
        es: Bienvenido
        it: Benvenuto
        ja: ようこそ
```

### Translator Notes

Add notes to help translators understand context:

```yaml
:global:
    Submit:
        :note: Button for form submission
        en: Submit
        fr: Soumettre

    Open:
        :note: Menu item to open a file
        en: Open
        fr: Ouvrir
```

Notes are exported to `.ts` files as `<extracomment>` tags, visible in translation tools like Qt Linguist.

## Disambiguation

When the same source text has different meanings, use the disambiguation syntax: `"source|context"`.

### YAML Format

```yaml
:global:
    "Open|menu":
        en: Open
        fr: Ouvrir

    "Open|status":
        en: Open
        fr: Ouvert
```

**Note:** Only the first `|` is treated as a separator. The text `"A | B|context"` splits into source `"A | B"` and context `"context"`.

### Usage in Code

```python
@widget
class FileManager(Widget):
    # Different translations based on context
    menu_action: QAction = new(t("Open", context="menu"))      # "Ouvrir"
    status_label: QLabel = new(t("Open", context="status"))    # "Ouvert"
```

### Multiple Disambiguations

```yaml
:global:
    "Close|menu":
        en: Close
        fr: Fermer

    "Close|window":
        en: Close
        fr: Fermer

    "Close|verb":
        en: Close
        fr: Clore
```

## Plurals

QtPie supports Qt's plural translation system using `%n` as a placeholder for the count.

### YAML Format

Use YAML lists for plural forms:

```yaml
:global:
    "%n file(s)":
        en:
            - "%n file"
            - "%n files"
        fr:
            - "%n fichier"
            - "%n fichiers"

    "%n item(s)":
        en:
            - "%n item"
            - "%n items"
        de:
            - "%n Artikel"
            - "%n Artikel"
```

### Usage in Code

Call the `Translatable` object with a count to get the plural form:

```python
@widget
class FileList(Widget):
    count_label: QLabel = new()

    def update_count(self, n: int) -> None:
        # Call t() with count to get plural form
        self.count_label.setText(t("%n file(s)")(n))

        # Examples:
        # n=0  -> "0 files"
        # n=1  -> "1 file"
        # n=5  -> "5 files"
```

### Plural Rules

Plural selection follows Qt's rules:

- English: singular for n=1, plural otherwise
- French: singular for n=0 or n=1, plural otherwise
- Other languages may have different rules (Qt handles this)

The `%n` placeholder is automatically replaced with the actual count.

### Example with Zero

```python
marker = t("%n item(s)")

print(marker(0))   # "0 items" (plural)
print(marker(1))   # "1 item"  (singular)
print(marker(42))  # "42 items" (plural)
```

## Widget Contexts

Translation contexts default to the widget class name, allowing widget-specific translations.

### Widget-Specific Translations

```yaml
:global:
    Title:
        en: Title
        fr: Titre Global

MyCustomWidget:
    Title:
        en: Title
        fr: Titre personnalisé
```

### Usage

```python
@widget
class MyCustomWidget(Widget):
    # Uses "MyCustomWidget" context -> "Titre personnalisé"
    title: QLabel = new(t("Title"))

@widget
class OtherWidget(Widget):
    # No match in "OtherWidget" context, falls back to :global: -> "Titre Global"
    title: QLabel = new(t("Title"))
```

### Context Fallback

Translation lookup follows this order:

1. Widget class name context (e.g., `"MyCustomWidget"`)
2. `@default` (`:global:` in YAML)
3. Source text if no translation found

```python
# Translation lookup for MyWidget using t("Save"):
# 1. Check "MyWidget" context for "Save"
# 2. Check "@default" context for "Save"
# 3. Return "Save" (source text)
```

### Complex Example

```yaml
:global:
    Save:
        en: Save
        fr: Enregistrer

    Cancel:
        en: Cancel
        fr: Annuler

DialogEditor:
    Save:
        en: Save
        fr: Sauvegarder  # Different translation for this specific widget
```

```python
@widget
class DialogEditor(Widget):
    save_btn: QPushButton = new(t("Save"))      # "Sauvegarder"
    cancel_btn: QPushButton = new(t("Cancel"))  # "Annuler" (from :global:)

@widget
class FileEditor(Widget):
    save_btn: QPushButton = new(t("Save"))      # "Enregistrer" (from :global:)
```

## Runtime Language Switching

Change the application language at runtime with automatic retranslation.

### Using set_language()

```python
from qtpie import set_language

def change_to_french(self) -> None:
    set_language("fr")  # All t() widgets automatically retranslate

def change_to_german(self) -> None:
    set_language("de")  # Instant retranslation
```

### Complete Example

```python
from PySide6.QtWidgets import QLabel, QPushButton, QComboBox
from qtpie import Widget, new, set_language, t, widget

@widget
class LanguageSwitcher(Widget):
    greeting: QLabel = new(t("Hello"))
    button: QPushButton = new(t("Click Me"))
    language_selector: QComboBox = new(
        currentTextChanged="on_language_changed"
    )

    def __setup__(self) -> None:
        self.language_selector.addItems(["en", "fr", "de"])

    def on_language_changed(self, lang: str) -> None:
        set_language(lang)
        # greeting and button text automatically update!
```

### Retranslation Behavior

When `set_language()` is called:

1. All widgets created with `t()` are automatically retranslated
2. Includes positional args (`new(t("text"))`)
3. Includes form labels (`new(label=t("Label"))`)
4. Includes format bindings (`new(bind=t("Hello {name}"))`)

### No-Op on Same Language

```python
set_language("fr")
set_language("fr")  # No retranslation happens (already "fr")
```

### Disabling Retranslation

```python
# Change language but don't retranslate existing widgets
set_language("fr", retranslate=False)
```

This is useful when loading translations before widgets are created.

## Using with @entrypoint

Configure translations when defining the application entry point.

### Basic Configuration

```python
from qtpie import entrypoint, widget

@entrypoint(
    translations="translations.yml",
    language="fr"
)
@widget
class MyApp(Widget):
    # ... widget definition
```

### Multiple Translation Files

Load translations from multiple YAML files (deep-merged):

```python
@entrypoint(
    translations=["base.yml", "custom.yml", "overrides.yml"],
    language="de"
)
@widget
class MyApp(Widget):
    # ... widget definition
```

Files are merged left-to-right, with later files overriding earlier ones.

### Default Language

If `language=` is omitted, defaults to English:

```python
@entrypoint(translations="app.yml")  # language="en" by default
@widget
class MyApp(Widget):
    # ... widget definition
```

### Without Translations

The `@entrypoint` decorator works without translations:

```python
@entrypoint  # No translations loaded
@widget
class MyApp(Widget):
    label: QLabel = new(t("Hello"))  # Shows "Hello" (source text)
```

## Hot-Reload for Development

Enable automatic reload when translation files change during development.

### Enabling Watch Mode

```python
@entrypoint(
    translations="translations.yml",
    language="fr",
    watch_translations=True  # Enable hot-reload
)
@widget
class MyApp(Widget):
    greeting: QLabel = new(t("Hello"))
```

### How It Works

When `watch_translations=True`:

1. QtPie monitors the translation file(s) for changes
2. On file modification, translations are reloaded
3. All widgets are automatically retranslated with new text

### Development Workflow

```bash
# 1. Start your app with watch_translations=True
python my_app.py

# 2. Edit translations.yml while app is running
# 3. Save the file
# 4. App instantly shows updated translations!
```

### Production Builds

For production, disable hot-reload and use compiled `.qm` files:

```python
@entrypoint(
    translations="translations.yml",
    language="fr",
    watch_translations=False  # Disable for production
)
@widget
class MyApp(Widget):
    # ... widget definition
```

Better yet, use compiled `.qm` files (see CLI Commands section).

### QRC Resources

Hot-reload works only with file paths. If translations are embedded in Qt resources (`.qrc`), watch mode is automatically disabled.

## CLI Commands

QtPie provides CLI commands for working with translations.

### Compile to .ts Files

Generate Qt Linguist `.ts` XML files from YAML:

```bash
# Compile all languages
uv run qtpie tr compile translations.yml -o ./i18n/

# Output:
#   ./i18n/en.ts
#   ./i18n/fr.ts
#   ./i18n/de.ts
```

### Compile Specific Languages

```bash
# Only French and German
uv run qtpie tr compile translations.yml -o ./i18n/ --lang fr --lang de

# Output:
#   ./i18n/fr.ts
#   ./i18n/de.ts
```

### Compile to .qm Files

Generate binary `.qm` files (requires `lrelease` tool):

```bash
# Generate both .ts and .qm files
uv run qtpie tr compile translations.yml -o ./i18n/ --qm

# Output:
#   ./i18n/en.ts
#   ./i18n/en.qm
#   ./i18n/fr.ts
#   ./i18n/fr.qm
```

### List All Translations

View all translations in a YAML file:

```bash
uv run qtpie tr list translations.yml
```

Output shows context, source, disambiguations, and translations for each entry.

### Multiple Input Files

```bash
# Compile from multiple YAML files
uv run qtpie tr compile base.yml overrides.yml -o ./i18n/
```

Files are deep-merged before compilation.

## Advanced Usage

### Using Translations with Form Layouts

The `label=` parameter in form layouts supports `t()`:

```python
from dataclasses import dataclass
from PySide6.QtWidgets import QLineEdit
from qtpie import Widget, new, t, widget

@dataclass
class Person:
    name: str = ""
    email: str = ""

@widget(layout="form", record=Person())
class PersonForm(Widget[Person]):
    name: QLineEdit = new(label=t("Name"))
    email: QLineEdit = new(label=t("Email Address"))
```

YAML:

```yaml
:global:
    Name:
        en: Name
        fr: Nom

    Email Address:
        en: Email Address
        fr: Adresse e-mail
```

Form labels automatically retranslate when language changes.

### Using Translations with Format Bindings

Combine `t()` with `bind=` for reactive translated text:

```python
from dataclasses import dataclass
from PySide6.QtWidgets import QLabel
from qtpie import Widget, new, t, widget

@dataclass
class User:
    name: str = "Alice"

@widget(record=User())
class GreetingWidget(Widget[User]):
    greeting: QLabel = new(bind=t("Hello {name}!"))
```

YAML:

```yaml
:global:
    "Hello {name}!":
        en: "Hello {name}!"
        fr: "Bonjour {name}!"
        de: "Hallo {name}!"
```

The format string is translated, then field substitution happens:

```python
# English: "Hello Alice!"
# French:  "Bonjour Alice!"
# German:  "Hallo Alice!"
```

Changing `set_language()` retranslates the format string, and the binding system re-evaluates it with current field values.

### Registering Custom Bindings

For non-Qt objects or custom retranslation logic:

```python
from qtpie.translations import register_binding, set_language

class CustomObject:
    def __init__(self) -> None:
        self._text = ""

    def setText(self, value: str) -> None:
        self._text = value

    def getText(self) -> str:
        return self._text

obj = CustomObject()
obj.setText("Hello")

# Register for retranslation
register_binding(obj, "text", "Hello")

# When language changes, QtPie calls obj.setText() with translated text
set_language("fr")  # obj now has "Bonjour"
```

The retranslation system tries these methods in order:

1. `setXxx()` method (e.g., `setText()`)
2. Property setter (e.g., `obj.text = value`)
3. Logs warning if neither exists

### Memory Store vs QTranslator

QtPie uses two translation backends:

**Memory Store (Development)**
- Enabled with `enable_memory_store(True)`
- Translations stored in Python dictionaries
- Supports hot-reload
- Used automatically by `@entrypoint` in dev mode

**QTranslator (Production)**
- Enabled with `enable_memory_store(False)`
- Translations loaded from `.qm` files
- Standard Qt mechanism
- Better performance for large translation sets

You typically don't need to manage this manually - `@entrypoint` handles it.

### Context Management

For advanced use cases, manually set translation context:

```python
from qtpie.translations import set_translation_context, get_translation_context

# Set context (normally done by @widget)
set_translation_context("MyWidget")

# Get current context
ctx = get_translation_context()  # "MyWidget"
```

This is used internally by the `@widget` decorator.

### Deep Merging Translation Files

When using multiple YAML files, they are deep-merged:

```yaml
# base.yml
:global:
    Save:
        en: Save
        fr: Enregistrer
```

```yaml
# overrides.yml
:global:
    Save:
        fr: Sauvegarder  # Overrides base.yml
    Cancel:
        en: Cancel
        fr: Annuler
```

Result:
```yaml
:global:
    Save:
        en: Save          # From base.yml
        fr: Sauvegarder   # From overrides.yml (override)
    Cancel:
        en: Cancel        # From overrides.yml
        fr: Annuler       # From overrides.yml
```

### Translation File Structure

Complete YAML example showing all features:

```yaml
# Global translations (available to all widgets)
:global:
    # Basic translation
    Hello:
        en: Hello
        fr: Bonjour
        de: Hallo

    # With translator note
    Submit:
        :note: Button to submit a form
        en: Submit
        fr: Soumettre
        de: Absenden

    # Disambiguation
    "Open|menu":
        :note: Menu item to open a file
        en: Open
        fr: Ouvrir

    "Open|status":
        :note: Status indicating something is open
        en: Open
        fr: Ouvert

    # Plurals
    "%n file(s)":
        en:
            - "%n file"
            - "%n files"
        fr:
            - "%n fichier"
            - "%n fichiers"

# Widget-specific translations
MainWindow:
    Title:
        en: My Application
        fr: Mon Application

DialogBox:
    OK:
        en: OK
        fr: D'accord
```

### Error Handling

If a translation is not found:

```python
# No translation for "Unknown" in French
set_language("fr")
label: QLabel = new(t("Unknown"))  # Shows "Unknown" (source text)
```

If a setter is not available for retranslation:

```python
class ImmutableObject:
    def __init__(self, text: str) -> None:
        self._text = text

    @property
    def text(self) -> str:
        return self._text
    # No setter!

obj = ImmutableObject("Hello")
register_binding(obj, "text", "Hello")

set_language("fr")  # Logs warning: "no setter found for property 'text'"
```

## Best Practices

1. **Use :global: for common strings** - Place frequently used translations like "Save", "Cancel", "OK" in `:global:`

2. **Use widget contexts sparingly** - Only create widget-specific translations when the same word needs different translations in different parts of your app

3. **Always provide English** - Even if English is your source language, include it in YAML for consistency

4. **Use disambiguation for identical strings** - When "Close" means different things, use `"Close|menu"` and `"Close|window"`

5. **Test with hot-reload** - Use `watch_translations=True` during development to see translations in real-time

6. **Compile for production** - Use `.qm` files in production for better performance

7. **Add translator notes** - Use `:note:` to help translators understand context

8. **Keep format strings translatable** - When using `bind=`, wrap the entire format string in `t()`, not individual parts:

```python
# Good
greeting: QLabel = new(bind=t("Hello {name}!"))

# Bad (don't do this)
greeting: QLabel = new(bind=f"{t('Hello')} {{name}}!")
```

9. **Use %n for plurals** - Follow Qt's plural convention with `%n` placeholder

10. **Check fallbacks** - Ensure your app works even without translations loaded (shows source text)
