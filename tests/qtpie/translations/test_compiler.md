# Translation Compiler Tests

## Compile to .ts XML

Converts `TranslationEntry` objects to Qt Linguist .ts XML format for a specific language.

```python
entries = [
    TranslationEntry(
        context="@default",
        source="Hello",
        translations={"fr": "Bonjour"},
    )
]
result = compile_to_ts(entries, "fr")

assert_that(result).contains('<?xml version="1.0" encoding="utf-8"?>')
assert_that(result).contains('<TS version="2.1" language="fr">')
assert_that(result).contains("<source>Hello</source>")
assert_that(result).contains("<translation>Bonjour</translation>")
```

## Context Support

Entries can have context (widget class name) which groups translations in the .ts file.

```python
entries = [
    TranslationEntry(
        context="MyWidget",
        source="Title",
        translations={"fr": "Titre"},
    )
]
result = compile_to_ts(entries, "fr")

assert_that(result).contains("<name>MyWidget</name>")
```

## Disambiguation

For same source text with different meanings, disambiguation is written as `<comment>`.

```python
entries = [
    TranslationEntry(
        context="@default",
        source="Open",
        disambiguation="file_menu",
        translations={"fr": "Ouvrir"},
    )
]
result = compile_to_ts(entries, "fr")

assert_that(result).contains("<comment>file_menu</comment>")
```

## Translator Notes

Notes for translators are written as `<extracomment>`.

```python
entries = [
    TranslationEntry(
        context="@default",
        source="Submit",
        note="For form submission",
        translations={"fr": "Soumettre"},
    )
]
result = compile_to_ts(entries, "fr")

assert_that(result).contains("<extracomment>For form submission</extracomment>")
```

## Plural Forms

Translations that are lists (plural forms) are compiled with `numerus="yes"` and multiple `<numerusform>` elements.

```python
entries = [
    TranslationEntry(
        context="@default",
        source="%n file(s)",
        translations={"fr": ["%n fichier", "%n fichiers"]},
    )
]
result = compile_to_ts(entries, "fr")

assert_that(result).contains('numerus="yes"')
assert_that(result).contains("<numerusform>%n fichier</numerusform>")
assert_that(result).contains("<numerusform>%n fichiers</numerusform>")
```

## Extract All Languages

Gets all unique language codes from translation entries.

```python
entries = [
    TranslationEntry(
        context="@default",
        source="Hello",
        translations={"fr": "Bonjour", "de": "Hallo", "es": "Hola"},
    )
]
languages = get_all_languages(entries)
assert_that(languages).is_equal_to({"fr", "de", "es"})
```

## Compile to Disk

Creates .ts files on disk for all languages (or specific languages if requested).

```python
entries = [
    TranslationEntry(
        context="@default",
        source="Hello",
        translations={"fr": "Bonjour", "de": "Hallo"},
    )
]

with tempfile.TemporaryDirectory() as tmpdir:
    output_dir = Path(tmpdir)
    files = compile_translations(entries, output_dir)

    assert_that(files).is_length(2)
    assert_that((output_dir / "de.ts").exists()).is_true()
    assert_that((output_dir / "fr.ts").exists()).is_true()
```

```python
# Compile only specific languages
files = compile_translations(entries, output_dir, languages=["fr"])

assert_that(files).is_length(1)
assert_that((output_dir / "fr.ts").exists()).is_true()
assert_that((output_dir / "de.ts").exists()).is_false()
```
