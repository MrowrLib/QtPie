# Translations

QtPie provides a complete internationalization (i18n) system that makes translating your app straightforward. Define translations in YAML, use them declaratively in your widgets, and even hot-reload during development.

## Quick Start

### 1. Create a YAML Translation File

```yaml
# translations.yml
MyWidget:
  Hello:
    fr: Bonjour
    de: Hallo
    ja: こんにちは

  Save:
    fr: Sauvegarder
    de: Speichern
    ja: 保存
```

### 2. Use `tr[]` in Your Widgets

```python
from qtpie import widget, make, tr
from qtpy.QtWidgets import QWidget, QLabel, QPushButton

@widget
class MyWidget(QWidget):
    # Positional arg (e.g. for text property)
    label: QLabel = make(QLabel, tr["Hello"])

    # Keyword arg (for any property)
    button: QPushButton = make(QPushButton, text=tr["Save"], toolTip=tr["Save your work"])
```

### 3. Enable Translations in Your Entry Point

```python
from qtpie import entrypoint, widget, make, tr
from qtpy.QtWidgets import QWidget, QLabel

@entrypoint(
    translations="translations.yml",
    language="fr",
    watch_translations=True,  # Hot-reload in dev
)
@widget
class MyApp(QWidget):
    label: QLabel = make(QLabel, tr["Hello"])
```

Run your app and you'll see "Bonjour" instead of "Hello"!

---

## YAML Syntax

### Basic Structure

```yaml
# Context (usually class name):
MyWidget:
  # Source text:
  #   language_code: translation
  Hello:
    fr: Bonjour
    de: Hallo
```

The **context** matches your widget class name. Qt uses this to scope translations.

### Global Translations

Use `:global:` for strings shared across all widgets:

```yaml
:global:
  OK:
    fr: OK
    de: OK
    ja: はい

  Cancel:
    fr: Annuler
    de: Abbrechen
    ja: キャンセル

MyDialog:
  "Are you sure?":
    fr: "Êtes-vous sûr ?"
    de: "Sind Sie sicher?"
```

### Disambiguation

Same source text with different meanings? Use `|` to disambiguate:

```yaml
MyWidget:
  # "Open" as a verb (menu action)
  Open|menu:
    fr: Ouvrir
    de: Öffnen

  # "Open" as an adjective (status)
  Open|status:
    fr: Ouvert
    de: Geöffnet
```

Use in code:

```python
menu_open: QAction = make(QAction, text=tr["Open", "menu"])
status_label: QLabel = make(QLabel, text=tr["Open", "status"])
```

### Translator Notes

Help translators understand context with `:note:`:

```yaml
MyWidget:
  "Save changes?":
    :note: Shown when closing with unsaved work
    fr: "Enregistrer les modifications ?"
    de: "Änderungen speichern?"
```

### Plurals

Different languages have different plural rules. Define all forms as a list:

```yaml
MyWidget:
  "%n file(s)":
    en: ["%n file", "%n files"]
    fr: ["%n fichier", "%n fichiers"]
    ru: ["%n файл", "%n файла", "%n файлов"]  # Russian has 3 forms
```

Call `tr[]` with the count to get the correct plural form:

```python
# tr["source"](count) returns the plural form with %n replaced
self.label.setText(tr["%n file(s)"](5))   # "5 files" in English
self.label.setText(tr["%n file(s)"](1))   # "1 file" in English
```

---

## The `tr[]` Accessor

The `tr[]` accessor creates translatable markers that get resolved when widgets are created.

### Basic Usage

```python
from qtpie import tr

# Positional arg (common widgets)
label: QLabel = make(QLabel, tr["Hello"])
button: QPushButton = make(QPushButton, tr["Save"], clicked="on_save")

# Keyword arg (explicit property)
label: QLabel = make(QLabel, text=tr["Hello"])
button: QPushButton = make(QPushButton, text=tr["Save"], toolTip=tr["Save changes"])

# With disambiguation
menu_open: QAction = make(QAction, text=tr["Open", "menu"])
```

Positional `tr[]` works for common widgets:
- `QLabel`, `QPushButton`, `QCheckBox`, `QRadioButton`, `QToolButton` → `text`
- `QGroupBox`, `QMenu` → `title`
- `QLineEdit`, `QAction` → `text`

For other widgets or properties like `toolTip`, use keyword args.

### How It Works

1. `tr["Hello"]` creates a `Translatable` marker
2. When `make()` runs, it resolves the translation using the widget's class name as context
3. The translation is looked up from the in-memory store (dev) or Qt's QTranslator (production)

### Using tr[] with bind=

You can use `tr[]` in the `bind=` parameter for translated format bindings:

```python
from qtpie import widget, make, tr, state
from qtpy.QtWidgets import QWidget, QLabel

@widget
class Counter(QWidget):
    count: int = state(0)
    label: QLabel = make(QLabel, bind=tr["Count: {count}"])
```

With translations:

```yaml
Counter:
  "Count: {count}":
    fr: "Compteur : {count}"
    de: "Zähler: {count}"
```

When the language changes (hot-reload), the translation is re-resolved **before** the format is applied, so the label updates correctly.

### Automatic Context

The `@widget` decorator sets the translation context to the class name:

```python
@widget
class LoginDialog(QWidget):  # Context = "LoginDialog"
    username_label: QLabel = make(QLabel, text=tr["Username"])
```

This means your YAML should use `LoginDialog` as the context:

```yaml
LoginDialog:
  Username:
    fr: "Nom d'utilisateur"
```

---

## Entry Point Options

### Enable Translations

```python
@entrypoint(
    translations="translations.yml",  # Path to YAML file
    language="fr",                     # Language code
)
@widget
class MyApp(QWidget):
    ...
```

### Hot-Reload for Development

Edit YAML and see changes instantly:

```python
@entrypoint(
    translations="translations.yml",
    language="fr",
    watch_translations=True,  # Enable hot-reload
)
@widget
class MyApp(QWidget):
    ...
```

When you save the YAML file, all widgets automatically update with new translations.

---

## Manual Watcher Setup

For more control, use `watch_translations()` directly:

```python
from pathlib import Path
from qtpie import widget
from qtpie.translations.watcher import watch_translations
from qtpy.QtWidgets import QWidget

@widget
class MyApp(QWidget):
    def setup(self) -> None:
        # Watch for changes and hot-reload
        self.tr_watcher = watch_translations(
            Path("translations.yml"),
            language="fr",
        )
```

### Change Language at Runtime

```python
# Change to German
self.tr_watcher.set_language("de")
# All widgets automatically update!
```

### Stop Watching

```python
self.tr_watcher.stop()
```

---

## Compiling to Qt Format

For production, compile YAML to Qt's binary `.qm` format using the CLI.

### Install the CLI

The `qtpie` CLI is included when you install qtpie:

=== "uv"

    ```bash
    uv add qtpie
    ```

=== "poetry"

    ```bash
    poetry add qtpie
    ```

=== "pip"

    ```bash
    pip install qtpie
    ```

### Compile to .ts Files

```bash
# Basic usage
qtpie tr compile translations.yml -o ./i18n/

# Output:
#   i18n/fr.ts
#   i18n/de.ts
#   i18n/ja.ts
```

### Compile to .qm Files

Add `--qm` to also generate binary `.qm` files:

```bash
qtpie tr compile translations.yml -o ./i18n/ --qm

# Output:
#   i18n/fr.ts
#   i18n/fr.qm
#   i18n/de.ts
#   i18n/de.qm
#   ...
```

### Filter Languages

Only compile specific languages:

```bash
qtpie tr compile translations.yml -o ./i18n/ --lang fr --lang de
```

### Multiple Input Files

Merge multiple YAML files:

```bash
qtpie tr compile common.yml dialogs.yml widgets.yml -o ./i18n/
```

### Verbose Output

See what's happening:

```bash
qtpie tr compile translations.yml -o ./i18n/ -v

# Parsing 1 YAML file(s)...
# Found languages: de, fr, ja
# Compiling to ./i18n/...
#   i18n/de.ts
#   i18n/fr.ts
#   i18n/ja.ts
# Created 3 .ts files.
```

### CLI Help

```bash
qtpie tr compile --help
```

---

## Loading .qm Files

For production apps, load compiled `.qm` files using Qt's `QTranslator`:

```python
from qtpy.QtCore import QTranslator
from qtpy.QtWidgets import QApplication

app = QApplication([])

# Load translation
translator = QTranslator()
if translator.load("i18n/fr.qm"):
    app.installTranslator(translator)

# Now tr[] uses the .qm file
```

### Loading from QRC Resources

Both YAML and .qm files can be loaded from Qt Resource Collection (QRC) paths:

```python
@entrypoint(
    translations=":/translations/app.yml",  # QRC path
    language="fr",
)
@widget
class MyApp(QWidget):
    ...
```

Or for .qm files:

```python
@entrypoint(
    translations=":/i18n/fr.qm",  # QRC path to compiled translations
    language="fr",
)
@widget
class MyApp(QWidget):
    ...
```

**Note:** `watch_translations=True` has no effect for QRC paths since embedded resources cannot be watched for changes. A log message will indicate when watching is skipped.

### With QtPie's App Class

```python
from qtpie import App, entrypoint, widget, make, tr
from qtpy.QtCore import QTranslator
from qtpy.QtWidgets import QWidget, QLabel

@widget
class MainWindow(QWidget):
    label: QLabel = make(QLabel, text=tr["Hello"])

@entrypoint
class MyApp(App):
    def setup(self) -> None:
        translator = QTranslator()
        if translator.load("i18n/fr.qm"):
            self.installTranslator(translator)

    def create_window(self):
        return MainWindow()
```

---

## Development vs Production

| Mode | How It Works | Use When |
|------|--------------|----------|
| **Development** | YAML → in-memory store, hot-reload | `watch_translations=True` |
| **Production** | YAML → .ts → .qm → QTranslator | Compiled, fast lookup |

### Development Flow

1. Create `translations.yml`
2. Use `@entrypoint(translations="...", watch_translations=True)`
3. Edit YAML, see changes instantly
4. No restart needed

### Production Flow

1. Compile: `qtpie tr compile translations.yml -o ./i18n/ --qm`
2. Load `.qm` with `QTranslator` in your app
3. Ship `.qm` files with your app

---

## Complete Example

### translations.yml

```yaml
:global:
  OK:
    fr: OK
    de: OK
  Cancel:
    fr: Annuler
    de: Abbrechen

Counter:
  "Count: {count}":
    fr: "Compteur : {count}"
    de: "Zähler: {count}"

  Increment:
    fr: Incrémenter
    de: Erhöhen

  Reset:
    fr: Réinitialiser
    de: Zurücksetzen
```

### counter.py

```python
from qtpie import entrypoint, widget, make, tr, state
from qtpy.QtWidgets import QWidget, QLabel, QPushButton

@entrypoint(
    translations="translations.yml",
    language="fr",
    watch_translations=True,
)
@widget
class Counter(QWidget):
    count: int = state(0)
    # bind=tr[] automatically updates when count OR translation changes
    label: QLabel = make(QLabel, bind=tr["Count: {count}"])
    inc_btn: QPushButton = make(QPushButton, tr["Increment"], clicked="increment")
    reset_btn: QPushButton = make(QPushButton, tr["Reset"], clicked="reset")

    def increment(self) -> None:
        self.count += 1  # Label auto-updates!

    def reset(self) -> None:
        self.count = 0  # Label auto-updates!
```

---

## API Reference

### `tr[]` Accessor

```python
from qtpie import tr

tr["source"]                    # Basic
tr["source", "disambiguation"]  # With disambiguation
tr["%n file(s)"](count)         # Plural form with count
```

### `@entrypoint` Options

```python
@entrypoint(
    translations="path/to/file.yml",  # YAML file path
    language="fr",                     # Language code (default: "en")
    watch_translations=True,           # Enable hot-reload (default: False)
)
```

### `watch_translations()`

```python
from qtpie.translations.watcher import watch_translations

watcher = watch_translations(
    yaml_paths="translations.yml",  # Path or list of paths
    language="fr",                   # Language code
)

watcher.set_language("de")  # Change language
watcher.stop()              # Stop watching
```

### CLI Commands

```bash
qtpie tr compile FILES -o OUTPUT [OPTIONS]

Arguments:
  FILES              YAML translation file(s)

Options:
  -o, --output PATH  Output directory for .ts/.qm files (required)
  --qm               Also compile .ts to .qm binary files
  --lang LANG        Only compile specific language(s), repeatable
  -v, --verbose      Show detailed output
```

---

## See Also

- [SCSS Hot Reload](scss.md) - Similar hot-reload for stylesheets
- [App & Entry Points](app.md) - More on `@entrypoint` options
