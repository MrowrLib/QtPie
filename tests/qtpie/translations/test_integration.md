# Translation Integration Tests

## Basic Widget Translation

Mark widget text as translatable using `t()`. Text resolves to the current language or falls back to source text.

```python
@widget
class TestWidget(Widget):
    label: QLabel = new(t("Hello"))

# Without translation: shows "Hello"
# With translation loaded and set_language("fr"): shows "Bonjour"
```

## Disambiguation

Use `context=` to disambiguate identical source strings with different meanings.

```python
@widget
class TestWidget(Widget):
    menu_open: QLabel = new(t("Open", context="menu"))    # "Ouvrir (menu)"
    file_open: QLabel = new(t("Open", context="file"))    # "Ouvrir (fichier)"
```

## Widget Context

Translation context defaults to widget class name, with fallback to `@default` (global).

```python
# Translation entry has context="MyCustomWidget"
@widget
class MyCustomWidget(Widget):
    label: QLabel = new(t("Title"))  # Resolves to widget-specific translation first

# Translation entry has context="@default"
@widget
class AnyWidget(Widget):
    label: QLabel = new(t("Global Text"))  # Falls back to global translation
```

## Runtime Language Switching

Change language with `set_language()` - all registered widgets retranslate automatically.

```python
@widget
class TestWidget(Widget):
    label: QLabel = new(t("Hello"))

w = TestWidget()
# Initially: "Hello"

set_language("fr")
# Now: "Bonjour"

set_language("de")
# Now: "Hallo"
```

## Form Layout Labels

Use `t()` with `label=` parameter in form layouts. Labels retranslate on language change.

```python
@widget(layout="form", record=Person())
class FormWidget(Widget[Person]):
    name: QLineEdit = new(label=t("Name"))  # Form label shows "Nom" in French
```

## Format String Bindings

Combine `t()` with `bind=` for reactive format strings that also translate.

```python
@dataclass
class Person:
    name: str = "Alice"

@widget(record=Person())
class BindWidget(Widget[Person]):
    info: QLabel = new(bind=t("Name: {name}"))
    # Shows "Nom: Alice" in French
    # Updates automatically when record.name changes or language changes
```

## Entrypoint Configuration

Store translation configuration with `@entrypoint` decorator (loaded when app runs).

```python
@entrypoint(
    translations="app.yml",           # Single file or ["a.yml", "b.yml"] for multiple
    language="fr",                     # Defaults to "en"
    watch_translations=True            # Enable hot-reload in dev
)
@widget
class TestApp(Widget):
    label: QLabel = new(t("Hello"))
```

## Non-Qt Object Retranslation

Retranslation works for any object with `setXxx()` method or property setter. QtPie tries `setXxx()` first, then property assignment.

```python
class MyObject:
    def setText(self, value: str) -> None:
        self._text = value

obj = MyObject()
register_binding(obj, "text", "Hello")

set_language("fr")  # Calls obj.setText("Bonjour")
```
