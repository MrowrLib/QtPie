# Translation YAML Parser

## Source Key Parsing

Parses source text with optional disambiguation context using pipe separator (`source|context`).

```python
def test_source_with_disambiguation(self) -> None:
    source, disambig = parse_source_key("Open|menu")
    assert_that(source).is_equal_to("Open")
    assert_that(disambig).is_equal_to("menu")
```

## Deep Dictionary Merging

Recursively merges translation dictionaries, with overlay values taking precedence.

```python
def test_merge_nested(self) -> None:
    base: dict[str, object] = {"x": {"a": 1}}
    overlay: dict[str, object] = {"x": {"b": 2}}
    result = deep_merge(base, overlay)
    assert_that(result).is_equal_to({"x": {"a": 1, "b": 2}})
```

## YAML Parsing

Parses YAML translation files with support for contexts, global scope, disambiguation, translator notes, and plurals.

```python
def test_parse_with_disambiguation(self) -> None:
    yaml_content = """
:global:
    "Open|menu":
        fr: Ouvrir
"""
    entries = parse_yaml(yaml_content)
    assert_that(entries[0].source).is_equal_to("Open")
    assert_that(entries[0].disambiguation).is_equal_to("menu")

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
    assert_that(entries[0].translations["en"]).is_equal_to(["%n file", "%n files"])
```

## File Loading and Merging

Loads and merges multiple YAML translation files from disk.

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
    # ... write to temp files ...
    entries = parse_yaml_files([path1, path2])
    assert_that(entries).is_length(2)
    sources = [e.source for e in entries]
    assert_that(sources).contains("Hello", "Goodbye")
```
