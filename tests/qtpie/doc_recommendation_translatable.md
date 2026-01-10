# Documentation Recommendation: Translatable Feature

## Priority: **HIGH**

Translations/i18n is a core feature for desktop applications and is already well-documented in CLAUDE.md but missing from the user-facing docs. The feature is implemented, tested, and ready to document.

---

## Files to Add/Update

### **Add: `docs/guides/translations.md`**
Main comprehensive guide for the translation system. This file is already referenced in mkdocs.yml nav but doesn't exist yet.

### **Update: `docs/index.md`**
Minor update: The translation example in the "Key Features" section should be expanded slightly to mention `@entrypoint` integration and YAML config.

### **Add: `docs/reference/factories/t.md`**
API reference for the `t()` function (parallel to existing `new()` reference).

### **Add: `docs/reference/functions/set_language.md`**
API reference for language switching at runtime.

---

## Suggested Nav Location

**Current location in mkdocs.yml is already correct:**
```yaml
Guides:
  - Translations: guides/translations.md  # Line 78
```

**Additional reference pages to add under Reference section:**
```yaml
Reference:
  - Functions:
      - "t()": reference/functions/t.md
      - "set_language()": reference/functions/set_language.md
```

---

## Content Outline: `docs/guides/translations.md`

### 1. Introduction
- Why translations matter for desktop apps
- QtPie's declarative approach vs Qt's imperative QTranslator
- Two modes: dev (in-memory YAML) vs production (.qm files)

### 2. Quick Start
- Basic `t()` usage in widgets
- Setting up `@entrypoint` with translations
- Running your first translated app
- Runtime language switching with `set_language()`

### 3. YAML Translation Format
- File structure (`:global:` vs widget-specific contexts)
- Basic translations (key: {lang: text})
- Disambiguation with context (`"Open|menu"` syntax)
- Plural forms with `%n` placeholder
- Translator notes with `:note:`

### 4. Disambiguation
- When to use context parameter
- Same source text, different meanings
- Example: "Open" (menu action vs status label)

### 5. Plurals
- Using `%n` in source strings
- Calling translatables with counts: `t("%n file(s)")(count)`
- Language-specific plural rules (en: 2 forms, fr: 2 forms, etc.)

### 6. Widget Context
- How context defaults to widget class name
- Fallback to `:global:` (formerly `@default`)
- Scoping translations to specific widgets
- Override context in `resolve()`

### 7. CLI Tools
- `qtpie tr compile` - YAML to .ts/.qm
- `qtpie tr list` - View all translations
- Language filtering (`--lang`)
- Production workflow: compile to .qm files

### 8. Development Workflow
- Hot-reload with `watch_translations=True`
- Edit YAML, see changes immediately
- Memory store vs QTranslator modes

### 9. Production Workflow
- Compile YAML to .qm binary files
- Bundle .qm files with app
- Load .qm files at runtime
- Disable memory store for production

### 10. Advanced Topics
- Using translations in bindings (not just initial text)
- Translatable in format strings
- Manual translation context management
- Integration with Qt Linguist (optional)

### 11. Best Practices
- When to use disambiguation
- Organizing translations by widget/module
- Handling missing translations (graceful fallback)
- Testing translated UIs
- Working with translators (YAML is translator-friendly)

### 12. Troubleshooting
- Translation not showing up (context mismatch)
- Plurals not working (check `%n` format)
- Hot-reload not working (check `watch_translations`)
- .qm file not loading (check file paths)

---

## Code Examples Needed

### Basic Usage
```python
from qtpie import Widget, new, t, widget

@widget
class MyWidget(Widget):
    label: QLabel = new(t("Hello"))
    button: QPushButton = new(t("Click Me"))
```

### With @entrypoint
```python
from qtpie import Widget, entrypoint, new, t, widget

@entrypoint(
    translations="translations.yml",
    language="fr",
    watch_translations=True,
)
@widget
class MyApp(Widget):
    label: QLabel = new(t("Hello"))
```

### Language Switching
```python
from qtpie import set_language

def change_to_french(self) -> None:
    set_language("fr")  # All t() strings retranslate automatically
```

### Disambiguation
```python
@widget
class FileMenu(Widget):
    # Same source text, different meanings
    open_action: QAction = new(t("Open", context="menu"))
    status_label: QLabel = new(t("Open", context="status"))
```

### Plurals
```python
# In widget
file_count: Variable[int] = new(5)
status_label: QLabel = new()

def update_status(self) -> None:
    count = self.file_count.get()
    self.status_label.setText(t("%n file(s)")(count))
```

### YAML Structure
```yaml
# translations.yml

:global:
    Hello:
        en: Hello
        fr: Bonjour
        de: Hallo
        es: Hola

    "Open|menu":
        en: Open
        fr: Ouvrir
        de: Öffnen

    "Open|status":
        en: Open
        fr: Ouvert
        de: Offen

    "%n file(s)":
        en:
            - "%n file"
            - "%n files"
        fr:
            - "%n fichier"
            - "%n fichiers"

    Submit:
        :note: Button text for form submission
        en: Submit
        fr: Soumettre

MainWindow:
    Title:
        en: My Application
        fr: Mon Application
```

### CLI Commands
```bash
# Compile YAML to .ts files
uv run qtpie tr compile translations.yml -o ./i18n/

# Also generate .qm files (production)
uv run qtpie tr compile translations.yml -o ./i18n/ --qm

# Compile specific languages
uv run qtpie tr compile translations.yml -o ./i18n/ --lang fr --lang de

# List all translations
uv run qtpie tr list translations.yml
```

### Complete Working Example
```python
from dataclasses import dataclass
from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton, QComboBox
from qtpie import Widget, Variable, entrypoint, new, set_language, t, widget

@entrypoint(translations="app_translations.yml", language="en")
@widget
class TranslatedApp(Widget):
    # Language selector
    language_combo: QComboBox = new(
        items=["English", "Français", "Deutsch"],
        currentIndexChanged="on_language_changed"
    )

    # Translated labels
    greeting: QLabel = new(t("Hello"))
    instruction: QLabel = new(t("Enter your name"))

    # Translated form
    name_input: QLineEdit = new(placeholderText=t("Name"))
    submit_btn: QPushButton = new(t("Submit"), clicked="on_submit")

    # File count example
    file_count: Variable[int] = new(5)
    status: QLabel = new()

    def __setup__(self) -> None:
        self.update_status()

    def on_language_changed(self, index: int) -> None:
        languages = ["en", "fr", "de"]
        set_language(languages[index])
        self.update_status()  # Re-translate plurals manually

    def update_status(self) -> None:
        count = self.file_count.get()
        self.status.setText(t("%n file(s)")(count))

    def on_submit(self) -> None:
        name = self.name_input.text()
        # Format with translated string
        msg = t("Welcome, {name}").resolve().format(name=name)
        self.greeting.setText(msg)
```

---

## Cross-References

### Related Features
- **Data Bindings** (`state/bindings.md`) - How t() works with bind= parameter
- **Format Expressions** (`state/format-expressions.md`) - Using translations in format strings
- **@entrypoint decorator** (`reference/decorators/entrypoint.md`) - Translation config params
- **new() factory** (`reference/factories/new.md`) - How t() is resolved in new()

### External Links
- Qt's QTranslator documentation
- Qt Linguist tool (for advanced workflows)
- YAML format specification
- Unicode/i18n best practices

### Internal Implementation
- `lib/qtpie/translations/translatable.py` - Core Translatable class
- `lib/qtpie/translations/store.py` - In-memory translation store
- Test cases: `tests/qtpie/translations/test_translatable.py`

---

## Reference Pages Content Outline

### `docs/reference/functions/t.md`

**Signature:**
```python
def t(text: str, *, context: str | None = None) -> Translatable
```

**Purpose:**
Mark a string for translation. Returns a `Translatable` marker that resolves to translated text based on current language.

**Parameters:**
- `text: str` - Source text (English by convention)
- `context: str | None` - Disambiguation context (optional)

**Returns:**
`Translatable` object (frozen dataclass, hashable)

**Usage Examples:**
- Basic: `new(t("Hello"))`
- Disambiguation: `new(t("Open", context="menu"))`
- Plurals: `t("%n file(s)")(count)`

**Special Cases:**
- Plurals use `%n` placeholder
- Context defaults to widget class name
- Fallback to source text if translation missing

**See Also:**
- `set_language()` - Runtime language switching
- `Translatable.resolve()` - Manual resolution
- Guides: Translation System

---

### `docs/reference/functions/set_language.md`

**Signature:**
```python
def set_language(language_code: str) -> None
```

**Purpose:**
Change the application language at runtime. Automatically retranslates all widgets using `t()`.

**Parameters:**
- `language_code: str` - ISO 639-1 language code (e.g., "en", "fr", "de", "es")

**Effects:**
- Updates global language setting
- Triggers retranslation of all registered translatable widgets
- Affects all future `t().resolve()` calls

**Usage Example:**
```python
from qtpie import set_language

def switch_to_french(self) -> None:
    set_language("fr")
```

**Common Patterns:**
- Language selector dropdown
- Settings/preferences dialog
- System locale detection at startup

**Limitations:**
- Plurals (from `t("%n x")(count)`) must be manually retriggered
- Dynamic text (not from t()) won't update automatically

**See Also:**
- `t()` - Creating translatable strings
- `@entrypoint(language=...)` - Initial language
- Guides: Translation System

---

## Notes

- The CLAUDE.md file has excellent coverage (lines 650-784) that can be adapted for user docs
- Test file (`test_translatable.md`) provides clear behavioral examples
- Implementation is complete and stable
- CLI tools already exist and need documenting
- Feature is production-ready, just needs user-facing docs
- YAML format is more accessible than Qt's XML .ts files for non-technical translators
- Hot-reload during development is a major DX win worth highlighting
