# Translation Store Tests

## Language Setting

Get and set the current language for translations. Defaults to "en".

```python
def test_set_language(self) -> None:
    set_language("fr")
    assert_that(get_language()).is_equal_to("fr")
```

## Translation Lookup

Look up translations by context and source text. Returns source text if no translation exists.

```python
def test_lookup_with_translation(self) -> None:
    entries = [
        TranslationEntry(
            context="@default",
            source="Hello",
            translations={"fr": "Bonjour"},
        )
    ]
    load_translations_from_entries(entries)
    set_language("fr")

    result = lookup("@default", "Hello")
    assert_that(result).is_equal_to("Bonjour")
```

## Disambiguation

Handle the same source text with different meanings using disambiguation contexts.

```python
def test_lookup_with_disambiguation(self) -> None:
    entries = [
        TranslationEntry(
            context="@default",
            source="Open",
            disambiguation="file_menu",
            translations={"fr": "Ouvrir (fichier)"},
        ),
        TranslationEntry(
            context="@default",
            source="Open",
            disambiguation="edit_menu",
            translations={"fr": "Ouvrir (edition)"},
        ),
    ]
    load_translations_from_entries(entries)
    set_language("fr")

    result1 = lookup("@default", "Open", "file_menu")
    result2 = lookup("@default", "Open", "edit_menu")

    assert_that(result1).is_equal_to("Ouvrir (fichier)")
    assert_that(result2).is_equal_to("Ouvrir (edition)")
```

## Context Fallback

Widget-specific contexts fall back to `@default` if no specific translation exists. Widget contexts override default when both exist.

```python
def test_lookup_fallback_to_default_context(self) -> None:
    entries = [
        TranslationEntry(
            context="@default",
            source="Global",
            translations={"fr": "Globale"},
        )
    ]
    load_translations_from_entries(entries)
    set_language("fr")

    # Lookup with specific context should fall back to @default
    result = lookup("MyWidget", "Global")
    assert_that(result).is_equal_to("Globale")
```

## Plural Forms

Look up plural translations with count-dependent forms. Replaces `%n` with the count.

```python
def test_lookup_plural_singular(self) -> None:
    entries = [
        TranslationEntry(
            context="@default",
            source="%n item(s)",
            translations={"en": ["%n item", "%n items"]},
        )
    ]
    load_translations_from_entries(entries)
    set_language("en")

    result = lookup_plural("@default", "%n item(s)", 1)
    assert_that(result).is_equal_to("1 item")

def test_lookup_plural_multiple(self) -> None:
    entries = [
        TranslationEntry(
            context="@default",
            source="%n item(s)",
            translations={"en": ["%n item", "%n items"]},
        )
    ]
    load_translations_from_entries(entries)
    set_language("en")

    result = lookup_plural("@default", "%n item(s)", 5)
    assert_that(result).is_equal_to("5 items")
```
