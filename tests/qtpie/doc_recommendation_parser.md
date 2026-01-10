# Documentation Proposal: Translation YAML Parser

## Overview

The translation parser is a core component of QtPie's i18n system that deserves dedicated documentation coverage. While `CLAUDE.md` covers the high-level translation workflow, the parser's YAML structure, features, and advanced capabilities need clear technical documentation for users authoring translation files.

---

## Files to Add/Update

### Primary: `docs/guides/translations.md` (NEW)
**Status**: Missing - referenced in mkdocs.yml nav but not yet created

**Purpose**: Comprehensive guide to QtPie's translation system, including the YAML parser

**Sections to Add**:
1. Basic Translation Workflow (existing CLAUDE.md content)
2. **YAML File Structure** (NEW - parser-focused)
3. Advanced Parser Features (NEW - parser-focused)
4. CLI Commands
5. Best Practices

### Secondary: `docs/reference/yaml-format.md` (NEW)
**Status**: Should be added to mkdocs nav under "Reference" section

**Purpose**: Technical reference for YAML translation file format - quick lookup for syntax

**Content**: Formal specification of the YAML schema with exhaustive examples

---

## Suggested Nav Location

### Primary Documentation
Add to existing nav structure in `mkdocs.yml`:
```yaml
- Guides:
    - Translations: guides/translations.md  # EXISTS in nav, file is MISSING
```

### Reference Documentation
Extend nav structure:
```yaml
- Reference:
    - YAML Format: reference/yaml-format.md  # NEW entry
```

---

## Content Outline

### `docs/guides/translations.md`

#### 1. Getting Started (Brief)
- What is `t()` and why use it
- Basic widget example
- Setting up `@entrypoint` with translations

#### 2. YAML File Structure (Parser Focus - MAIN ADDITION)
- File location conventions
- Basic structure: `context: { source: { lang: translation } }`
- The `:global:` context (maps to `@default`)
- Widget-specific contexts (class name)
- Complete minimal example

#### 3. Advanced Parser Features (MAIN ADDITION)
- **Disambiguation with `|`**
  - When same text has different meanings
  - `"Open|menu"` vs `"Open|status"`
  - How parser splits on LAST pipe
  - Context vs disambiguation distinction

- **Plural Forms**
  - Array syntax for plurals
  - Language-specific plural rules
  - The `%n` placeholder
  - Example: `"%n file(s)"` with English/French forms

- **Translator Notes**
  - `:note:` metadata
  - When to use notes
  - Example with form submission context

- **Multiple File Merging**
  - Using `parse_yaml_files()` with multiple paths
  - Deep merge behavior (overlay precedence)
  - Use cases: base translations + overrides
  - QRC resource paths support (`:/translations/app.yml`)

#### 4. CLI Commands (Brief - link to reference)
- `qtpie tr compile` overview
- Generating `.ts` and `.qm` files

#### 5. Best Practices
- When to use `:global:` vs widget contexts
- Organizing large translation files
- Using disambiguation effectively
- Naming conventions for source keys

### `docs/reference/yaml-format.md`

#### Format Specification
- YAML schema definition
- Key types and constraints
- Value types (string, list, dict)

#### Complete Syntax Reference
Table format:
```
| Feature          | Syntax                              | Example                        |
|------------------|-------------------------------------|--------------------------------|
| Simple           | `Source: { lang: translation }`     | `Hello: { fr: Bonjour }`       |
| Disambiguation   | `"Source|context": { ... }`         | `"Open|menu": { fr: Ouvrir }`  |
| Plural           | `Source: { lang: [form1, form2] }`  | `en: ["%n file", "%n files"]`  |
| Translator Note  | `:note: description`                | `:note: Form button`           |
| Global Context   | `:global:`                          | Top-level key                  |
| Widget Context   | `WidgetClassName:`                  | Top-level key                  |
```

#### Parser Behavior Notes
- `:global:` is normalized to `@default` context
- Pipe disambiguation: splits on LAST pipe only
- YAML boolean literals (`Yes`, `No`, `True`, `False`) are stringified
- Deep merge semantics for multiple files

#### Error Cases
- Invalid YAML syntax
- Missing translations for a language
- Type mismatches (expecting string, got int)

---

## Code Examples Needed

### 1. Basic YAML File
```yaml
:global:
    Hello:
        en: Hello
        fr: Bonjour
        de: Hallo
```

### 2. Widget-Specific Context
```yaml
LoginDialog:
    Username:
        fr: Nom d'utilisateur
    Password:
        fr: Mot de passe
```

### 3. Disambiguation Example
```yaml
:global:
    "Open|menu":
        en: Open
        fr: Ouvrir
    "Open|status":
        en: Open
        fr: Ouvert
```

### 4. Plural Forms
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

### 5. Translator Notes
```yaml
:global:
    Submit:
        :note: Button for form submission
        en: Submit
        fr: Soumettre
```

### 6. Multiple File Merging
**base.yml**:
```yaml
:global:
    Hello:
        en: Hello
        fr: Bonjour
```

**overrides.yml**:
```yaml
:global:
    Hello:
        fr: Salut  # Overrides base.yml
    Goodbye:
        fr: Au revoir
```

**Python usage**:
```python
from qtpie.translations import parse_yaml_files

entries = parse_yaml_files(["base.yml", "overrides.yml"])
# Hello: fr=Salut (overridden), en=Hello (preserved)
# Goodbye: fr=Au revoir (added)
```

### 7. QRC Resource Paths
```python
@entrypoint(translations=":/i18n/app.yml")  # From .qrc file
```

### 8. Complex Real-World Example
```yaml
:global:
    # Common UI strings
    "Cancel":
        en: Cancel
        fr: Annuler
        de: Abbrechen

    "Save":
        :note: Save button in various dialogs
        en: Save
        fr: Enregistrer
        de: Speichern

    # Plurals
    "%n item(s) selected":
        en:
            - "%n item selected"
            - "%n items selected"
        fr:
            - "%n élément sélectionné"
            - "%n éléments sélectionnés"

    # Disambiguation
    "Open|file_menu":
        en: Open...
        fr: Ouvrir...

    "Open|connection_status":
        en: Open
        fr: Ouvert

DocumentEditor:
    "Untitled":
        en: Untitled
        fr: Sans titre
        de: Unbenannt
```

---

## Cross-References

### From Translation Docs
- Link to `@entrypoint` decorator reference
- Link to `t()` function reference
- Link to `set_language()` function reference
- Link to "Format Expressions" for using translated text in bindings
- Link to "Windows & Menus" for menu item translations
- Link to "Testing" for testing translation coverage

### To Translation Docs
- From `docs/index.md` - add translation example in "Key Features"
- From `docs/start/concepts.md` - mention i18n as a core concept
- From `docs/reference/decorators/entrypoint.md` - link to translation guide for `translations=` param
- From `docs/guides/windows-menus.md` - link for menu action translations

### Related Features
- Format expressions (`bind=` with `t()` strings)
- CLI commands (`qtpie tr compile`)
- QRC resources (embedding translation files)

---

## Priority

**HIGH**

**Rationale**:
1. **Translation parser is fully implemented** - documented in `test_parser.md` with comprehensive tests
2. **Nav structure already references it** - `docs/guides/translations.md` is in mkdocs.yml but file doesn't exist
3. **Advanced features are undocumented** - disambiguation, plurals, deep merging are not covered in CLAUDE.md
4. **Low barrier to completion** - test file provides excellent examples, CLAUDE.md has base content
5. **Critical for i18n users** - anyone doing internationalization needs this reference
6. **Professional feature** - well-implemented parser with YAML deep merging, QRC support, etc. deserves proper docs

The YAML parser is production-ready but invisible to users without documentation. This is high-hanging fruit - a complete, tested feature waiting for user-facing docs.

---

## Notes

- The test file (`test_parser.md`) provides excellent example coverage - use it as primary source
- CLAUDE.md has good high-level translation examples - extract and expand for guide
- Parser supports both filesystem and QRC paths - important for production deployments
- Deep merge feature enables modular translation file organization (base + region/dialect overrides)
- Consider adding a "Translation Workflow" diagram showing: YAML → parser → TranslationEntry → t() → QTranslator
