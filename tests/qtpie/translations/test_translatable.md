# Translatable Tests

## Basic `t()` Function

The `t()` function creates a `Translatable` marker object that stores source text and optional context for lazy translation.

```python
result = t("Hello World")
assert_that(result).is_instance_of(Translatable)
assert_that(result.text).is_equal_to("Hello World")
```

```python
result = t("Open", context="menu")
assert_that(result.text).is_equal_to("Open")
assert_that(result.context).is_equal_to("menu")
```

## Translation Resolution

Calling `.resolve()` on a `Translatable` returns the translated text in the current language, or falls back to the source text if no translation exists.

```python
entries = [
    TranslationEntry(
        context="@default",
        source="Hello",
        translations={"fr": "Bonjour"},
    )
]
load_translations_from_entries(entries)
set_language("fr")

marker = t("Hello")
result = marker.resolve()
assert_that(result).is_equal_to("Bonjour")
```

## Disambiguation with Context

When the same source text has different meanings, use `context=` to disambiguate. Translations can specify `disambiguation=` to match.

```python
entries = [
    TranslationEntry(
        context="@default",
        source="Open",
        disambiguation="menu",
        translations={"fr": "Ouvrir (menu)"},
    ),
    TranslationEntry(
        context="@default",
        source="Open",
        disambiguation="action",
        translations={"fr": "Ouvrir (action)"},
    ),
]
load_translations_from_entries(entries)
set_language("fr")

marker = t("Open", context="menu")
result = marker.resolve()
assert_that(result).is_equal_to("Ouvrir (menu)")
```

## Widget Context

Translations can be scoped to specific widget classes. Use `set_translation_context()` to specify the current widget.

```python
entries = [
    TranslationEntry(
        context="MyWidget",
        source="Title",
        translations={"fr": "Titre (MyWidget)"},
    )
]
load_translations_from_entries(entries)
set_language("fr")

set_translation_context("MyWidget")
marker = t("Title")
result = marker.resolve()
assert_that(result).is_equal_to("Titre (MyWidget)")
```

## Plural Support

Call a `Translatable` with a count to get plural-aware translation. Use `%n` in the source text as a placeholder for the count.

```python
entries = [
    TranslationEntry(
        context="@default",
        source="%n file(s)",
        translations={"en": ["%n file", "%n files"]},
    )
]
load_translations_from_entries(entries)
set_language("en")

marker = t("%n file(s)")

result = marker(1)
assert_that(result).is_equal_to("1 file")

result = marker(5)
assert_that(result).is_equal_to("5 files")
```

## Hashable and Frozen

`Translatable` is a frozen dataclass, making it hashable and immutable. Instances with the same text and context are equal.

```python
a = t("Open", context="menu")
b = t("Open", context="menu")
c = t("Open", context="action")
assert_that(a).is_equal_to(b)
assert_that(a).is_not_equal_to(c)
```
