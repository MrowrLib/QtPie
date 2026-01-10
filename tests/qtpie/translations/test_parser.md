# Translation Parser Features

## Parsing Source Keys with Disambiguation

Extracts source text and optional disambiguation context from `source|context` keys.

```python
def test_source_with_disambiguation(self) -> None:
    source, disambig = parse_source_key("Open|menu")
    assert_that(source).is_equal_to("Open")
    assert_that(disambig).is_equal_to("menu")

def test_source_with_pipe_in_text(self) -> None:
    # Only first pipe is treated as separator
    source, disambig = parse_source_key("A | B|context")
    assert_that(source).is_equal_to("A | B")
    assert_that(disambig).is_equal_to("context")
```

## Deep Merging Dictionaries

Merges nested dictionaries recursively, with overlay values taking precedence.

```python
def test_merge_nested(self) -> None:
    base: dict[str, object] = {"x": {"a": 1}}
    overlay: dict[str, object] = {"x": {"b": 2}}
    result = deep_merge(base, overlay)
    assert_that(result).is_equal_to({"x": {"a": 1, "b": 2}})

def test_merge_overlay_wins(self) -> None:
    base: dict[str, object] = {"a": 1}
    overlay: dict[str, object] = {"a": 2}
    result = deep_merge(base, overlay)
    assert_that(result).is_equal_to({"a": 2})
```

## Parsing YAML Translation Content

Converts YAML structure `context: {source: {lang: translation}}` into translation entries.

```python
def test_parse_simple(self) -> None:
    yaml_content = """
:global:
    Hello:
        fr: Bonjour
"""
    entries = parse_yaml(yaml_content)
    assert_that(entries).is_length(1)
    assert_that(entries[0].source).is_equal_to("Hello")
    assert_that(entries[0].translations).is_equal_to({"fr": "Bonjour"})
    assert_that(entries[0].context).is_equal_to("@default")

def test_parse_with_context(self) -> None:
    yaml_content = """
MyWidget:
    Title:
        fr: Titre
"""
    entries = parse_yaml(yaml_content)
    assert_that(entries).is_length(1)
    assert_that(entries[0].context).is_equal_to("MyWidget")
    assert_that(entries[0].source).is_equal_to("Title")
```

## Disambiguation Support

Parses `source|context` keys to handle same text with different meanings.

```python
def test_parse_with_disambiguation(self) -> None:
    yaml_content = """
:global:
    "Open|menu":
        fr: Ouvrir
"""
    entries = parse_yaml(yaml_content)
    assert_that(entries).is_length(1)
    assert_that(entries[0].source).is_equal_to("Open")
    assert_that(entries[0].disambiguation).is_equal_to("menu")
```

## Translator Notes

Extracts `:note:` metadata for translator context.

```python
def test_parse_with_note(self) -> None:
    yaml_content = """
:global:
    Submit:
        :note: This is for form submission
        fr: Soumettre
"""
    entries = parse_yaml(yaml_content)
    assert_that(entries).is_length(1)
    assert_that(entries[0].note).is_equal_to("This is for form submission")
```

## Plural Forms

Parses plural translations as arrays for languages with different plural rules.

```python
def test_parse_plural(self) -> None:
    yaml_content = """
:global:
    "%n file(s)":
        en:
            - "%n file"
            - "%n files"
        fr:
            - "%n fichier"
            - "%n fichiers"
"""
    entries = parse_yaml(yaml_content)
    assert_that(entries).is_length(1)
    assert_that(entries[0].translations["en"]).is_equal_to(["%n file", "%n files"])
    assert_that(entries[0].translations["fr"]).is_equal_to(["%n fichier", "%n fichiers"])
```

## Parsing from Files

Reads and merges translation entries from one or more YAML files.

```python
def test_parse_multiple_files_merge(self) -> None:
    yaml1 = """
:global:
    Hello:
        fr: Bonjour
"""
    yaml2 = """
:global:
    Goodbye:
        fr: Au revoir
"""
    # ... (temp file setup) ...
    entries = parse_yaml_files([path1, path2])
    assert_that(entries).is_length(2)
    sources = [e.source for e in entries]
    assert_that(sources).contains("Hello", "Goodbye")
```
