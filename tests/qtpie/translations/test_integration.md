# Translation Integration Tests

## Basic Translation with t()

Mark strings for translation using `t()` in widget definitions. Without translations loaded, shows source text. With translations, resolves to target language.

```python
@widget
class TestWidget(Widget):
    label: QLabel = new(t("Hello"))

# Without translation -> "Hello"
# With fr translation -> "Bonjour"
```

## Widget Context Resolution

Translation context defaults to widget class name. Falls back to `@default` if no widget-specific translation exists.

```python
entries = [
    TranslationEntry(
        context="MyCustomWidget",
        source="Title",
        translations={"fr": "Titre personnalisé"},
    )
]

@widget
class MyCustomWidget(Widget):
    label: QLabel = new(t("Title"))  # Uses "MyCustomWidget" context
```

## Disambiguation

Use `context=` parameter when same source text has different meanings.

```python
@widget
class TestWidget(Widget):
    menu_open: QLabel = new(t("Open", context="menu"))    # "Ouvrir (menu)"
    file_open: QLabel = new(t("Open", context="file"))    # "Ouvrir (fichier)"
```

## Runtime Language Switching

`set_language()` automatically retranslates all bound widgets.

```python
@widget
class TestWidget(Widget):
    label: QLabel = new(t("Hello"))

w = TestWidget()
# Initially English: "Hello"

set_language("fr")  # Auto-retranslates to "Bonjour"

set_language("de")  # Auto-retranslates to "Hallo"
```

## Form Layout Labels

`label=t()` works in form layouts and retranslates on language change.

```python
@widget(layout="form", record=Person())
class FormWidget(Widget[Person]):
    name: QLineEdit = new(label=t("Name"))

# In French: form label shows "Nom"
```

## Format String Bindings

`bind=t()` supports format strings that resolve and bind reactively.

```python
@dataclass
class Person:
    name: str = "Alice"

@widget(record=Person())
class BindWidget(Widget[Person]):
    info: QLabel = new(bind=t("Name: {name}"))

# Shows: "Nom: Alice" (in French)

set_language("en")  # Updates to: "Name: Alice"
```

## Entrypoint Configuration

`@entrypoint` stores translation configuration (file paths, language, watch mode).

```python
@entrypoint(translations="app.yml", language="fr", watch_translations=True)
@widget
class TestApp(Widget):
    label: QLabel = new(t("Hello"))

# Config stored in class, translations loaded when app runs
```

## Non-Qt Object Retranslation

Retranslation works for any object with `setXxx()` methods or property setters.

```python
class MyObject:
    def __init__(self) -> None:
        self._text = ""

    def setText(self, value: str) -> None:
        self._text = value

obj = MyObject()
obj.setText("Hello")
register_binding(obj, "text", "Hello")

set_language("fr")  # Automatically calls obj.setText("Bonjour")
```
