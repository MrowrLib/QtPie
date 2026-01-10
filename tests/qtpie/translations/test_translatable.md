# Translatable Tests

## Creating Translatable Markers

The `t()` function creates `Translatable` marker objects that store source text and optional context for later resolution.

```python
result = t("Hello World")
assert_that(result).is_instance_of(Translatable)
assert_that(result.text).is_equal_to("Hello World")

# With disambiguation context
result = t("Open", context="menu")
assert_that(result.context).is_equal_to("menu")
```

## Resolving Translations

Translatable markers resolve to translated strings based on current language. Falls back to source text if no translation exists.

```python
# Without translation - returns source
marker = t("Hello")
result = marker.resolve()
assert_that(result).is_equal_to("Hello")

# With translation
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

## Context Disambiguation

Same source text can have different translations based on context.

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

Translations can be scoped to specific widget classes using the translation context.

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

## Plural Forms

Plural translations use `%n` placeholder and resolve based on count. Call the marker with a count to get the appropriate plural form.

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

# Singular
result = marker(1)
assert_that(result).is_equal_to("1 file")

# Plural
result = marker(5)
assert_that(result).is_equal_to("5 files")
```

## Hashable and Frozen

Translatable objects are frozen dataclasses that can be hashed and compared for equality.

```python
marker = t("Hello")
hash(marker)  # Should not raise

a = t("Hello")
b = t("Hello")
assert_that(a).is_equal_to(b)

a = t("Open", context="menu")
c = t("Open", context="action")
assert_that(a).is_not_equal_to(c)
```
