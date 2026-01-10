# Translations

QtPie provides a declarative translation system using `t()` for marking translatable strings, YAML for translation files, and hot-reload during development.

## Quick Start

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
    watch_translations=True,  # Hot-reload in development
)
@widget
class MyApp(Widget):
    label: QLabel = new(t("Hello"))  # Shows "Bonjour" when language="fr"
```

### Runtime Language Switching

```python
from qtpie import set_language

def change_to_french(self) -> None:
    set_language("fr")  # Automatically retranslates all t() widgets
```

## YAML Translation Format

### Basic Structure

```yaml
# translations.yml

# Global translations (available to all widgets)
:global:
    Hello:
        en: Hello
        fr: Bonjour
        de: Hallo

# Widget-specific translations (context = class name)
MainWindow:
    Title:
        en: My Application
        fr: Mon Application
```

### Disambiguation

When the same source text has different meanings:

```yaml
:global:
    # Use pipe character: "Source|context"
    "Open|menu":
        en: Open
        fr: Ouvrir

    "Open|status":
        en: Open
        fr: Ouvert
```

```python
# In code - specify context
menu_open: QAction = new(t("Open", context="menu"))    # "Ouvrir"
status_open: QLabel = new(t("Open", context="status")) # "Ouvert"
```

### Plural Forms

Use `%n` for count-dependent text:

```yaml
:global:
    "%n file(s)":
        en:
            - "%n file"
            - "%n files"
        fr:
            - "%n fichier"
            - "%n fichiers"
```

```python
# In code - call with count
def update_status(self) -> None:
    count = 5
    text = t("%n file(s)")(count)  # "5 files" or "5 fichiers"
    self.status_label.setText(text)
```

### Translator Notes

Add context for translators:

```yaml
:global:
    Submit:
        :note: Button text for form submission
        en: Submit
        fr: Soumettre
```

## Widget Context

The translation context defaults to the widget class name:

```yaml
# translations.yml
LoginDialog:
    Username:
        fr: Nom d'utilisateur
    Password:
        fr: Mot de passe
```

```python
@widget
class LoginDialog(Widget):
    # These look up in "LoginDialog" context automatically
    username_label: QLabel = new(t("Username"))
    password_label: QLabel = new(t("Password"))
```

If not found in the widget context, falls back to `:global:`.

## Complete Example

```yaml
# translations.yml
:global:
    Cancel:
        en: Cancel
        fr: Annuler

    Save:
        :note: Save button in dialogs
        en: Save
        fr: Enregistrer

    "%n item(s) selected":
        en:
            - "%n item selected"
            - "%n items selected"
        fr:
            - "%n element selectionne"
            - "%n elements selectionnes"

    "Open|file_menu":
        en: Open...
        fr: Ouvrir...

    "Open|connection_status":
        en: Open
        fr: Ouvert

DocumentEditor:
    Untitled:
        en: Untitled
        fr: Sans titre
```

```python
from qtpie import Widget, Variable, entrypoint, new, set_language, t, widget

@entrypoint(translations="translations.yml", language="en")
@widget
class App(Widget):
    # Language selector
    language_combo: QComboBox = new(
        items=["English", "Francais"],
        currentIndexChanged="on_language_changed"
    )

    # Translated labels
    greeting: QLabel = new(t("Hello"))
    save_btn: QPushButton = new(t("Save"), clicked="on_save")

    # Disambiguation
    file_menu: QMenu = new(t("Open", context="file_menu"))

    # Plurals
    selection_count: Variable[int] = new(0)
    status: QLabel = new()

    def on_language_changed(self, index: int) -> None:
        languages = ["en", "fr"]
        set_language(languages[index])
        self.update_status()

    def update_status(self) -> None:
        count = self.selection_count.value
        self.status.setText(t("%n item(s) selected")(count))
```

## CLI Commands

### Compile Translations

Generate Qt `.ts` files (and optionally `.qm` binary files):

```bash
# Compile all languages
uv run qtpie tr compile translations.yml -o ./i18n/

# Compile specific languages only
uv run qtpie tr compile translations.yml -o ./i18n/ --lang fr --lang de

# Also generate .qm binary files (requires lrelease)
uv run qtpie tr compile translations.yml -o ./i18n/ --qm

# Multiple input files
uv run qtpie tr compile base.yml overrides.yml -o ./i18n/
```

### List Translations

View all translations:

```bash
uv run qtpie tr list translations.yml
```

## Development vs Production

### Development

Use YAML directly with hot-reload:

```python
@entrypoint(
    translations="translations.yml",
    language="fr",
    watch_translations=True,  # Changes reload automatically
)
```

### Production

Compile to `.qm` binary files for distribution:

```bash
uv run qtpie tr compile translations.yml -o ./i18n/ --qm
```

Load `.qm` files at runtime:

```python
from PySide6.QtCore import QTranslator

translator = QTranslator()
translator.load("./i18n/fr.qm")
app.installTranslator(translator)
```

## Multiple Translation Files

Merge multiple YAML files (later files override earlier):

```yaml
# base.yml
:global:
    Hello:
        en: Hello
        fr: Bonjour
```

```yaml
# overrides.yml
:global:
    Hello:
        fr: Salut  # Overrides base.yml
    Goodbye:
        fr: Au revoir  # New entry
```

```python
@entrypoint(translations=["base.yml", "overrides.yml"])
```

## Key Functions

| Function | Description |
|----------|-------------|
| `t("text")` | Mark string for translation |
| `t("text", context="x")` | Mark with disambiguation |
| `t("%n item(s)")(n)` | Plural with count |
| `set_language("fr")` | Change language (auto-retranslates) |

## See Also

- [App & Entry Points](app.md) - Translation config in @entrypoint
- [Widgets](../basics/widgets.md) - Using t() in widget fields
