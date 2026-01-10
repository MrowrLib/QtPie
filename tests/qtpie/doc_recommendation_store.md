# Documentation Proposal: Translation Store (i18n Internal API)

## Overview

The Translation Store is QtPie's internal translation management system that powers the user-facing `t()` function and `@entrypoint(translations=...)` features. While end-users primarily interact with the high-level i18n API documented in `docs/guides/translations.md`, the store provides lower-level functions for advanced use cases like plugins, custom translation sources, or runtime translation management.

This is a **LOW priority** documentation task because:
1. Most users will never need to interact with the store directly
2. The high-level API in `translations.md` covers 95% of use cases
3. The store is primarily internal implementation

However, documentation should exist for:
- Framework integrators and plugin authors
- Advanced users building custom translation workflows
- Contributors understanding the architecture

## 1. Files to Add

### `docs/advanced/translation-store.md` (NEW)

**Purpose**: Document the low-level translation store API for advanced users.

**Target audience**:
- Plugin/extension developers
- Framework integrators
- Users building custom translation loaders
- Contributors to QtPie

**Content**: Comprehensive reference for store functions with usage examples.

## 2. Files to Update

### `docs/guides/translations.md` (Minor Update)

**Current status**: Already excellent user-facing documentation.

**Additions needed**:
- Add brief "Advanced: Translation Store API" section at the end
- Explain when users might need the store API vs the high-level API
- Link to `advanced/translation-store.md` for details
- Example: "For custom translation sources or runtime management, see [Translation Store API](../advanced/translation-store.md)"

### `mkdocs.yml` (Navigation Update)

Add new "Advanced Topics" section if it doesn't exist, or add to existing:

```yaml
- Advanced:
    - Translation Store API: advanced/translation-store.md
```

## 3. Suggested Nav Location

Create or expand an "Advanced Topics" section in the nav:

```yaml
- Guides:
    - Windows & Menus: guides/windows-menus.md
    - Form Layouts: guides/forms.md
    - Grid Layouts: guides/grids.md
    - Translations: guides/translations.md  # High-level API
    - App & Entry Points: guides/app.md
    - Async: guides/async.md
    - Testing: guides/testing.md
- Advanced:  # NEW or EXISTING SECTION
    - Translation Store API: advanced/translation-store.md  # NEW
    - Custom Bindings: advanced/custom-bindings.md  # Future
    - Extending QtPie: advanced/extending.md  # Future
```

**Rationale**:
- Keeps advanced/internal APIs separate from user-facing guides
- "Advanced" section signals this is not required reading
- Natural place for future low-level documentation

## 4. Content Outline

### `docs/advanced/translation-store.md` (New File)

#### Section 1: Introduction
- What is the Translation Store?
- Relationship to high-level `t()` API
- When to use store functions directly
- Warning: "Most users should use `t()` and `@entrypoint` instead"
- Link back to `guides/translations.md` for normal usage

#### Section 2: Language Management
- **`get_language() -> str`**
  - Returns current language code (default: "en")
  - Example from test lines 8-9

- **`set_language(lang: str) -> None`**
  - Sets current language globally
  - Triggers retranslation of all registered widgets
  - Example from test lines 11-13

- **Use case**: Custom language switcher without using high-level API
  ```python
  from qtpie.translations.store import get_language, set_language

  current = get_language()
  set_language("fr")  # Switch to French
  ```

#### Section 3: Loading Translations

- **`load_translations_from_entries(entries: list[TranslationEntry]) -> None`**
  - Loads translations from list of TranslationEntry objects
  - Used internally by YAML parser
  - Example from test lines 22-30

- **`TranslationEntry` dataclass structure**:
  ```python
  @dataclass
  class TranslationEntry:
      context: str  # Widget class name or "@default"
      source: str  # Source text to translate
      translations: dict[str, str | list[str]]  # lang -> translation(s)
      disambiguation: str | None = None  # Optional disambiguator
  ```

- **Use case**: Loading translations from custom sources (database, API, JSON)
  ```python
  from qtpie.translations.store import load_translations_from_entries, TranslationEntry

  # Load from custom JSON format
  entries = [
      TranslationEntry(
          context="@default",
          source="Hello",
          translations={"fr": "Bonjour", "es": "Hola"}
      )
  ]
  load_translations_from_entries(entries)
  ```

#### Section 4: Translation Lookup

- **`lookup(context: str, source: str, disambiguation: str | None = None) -> str`**
  - Look up translation for source text
  - Falls back to source if not found
  - Context fallback: widget-specific → @default → source
  - Examples from test lines 22-58

- **Context fallback behavior**:
  - Widget-specific translations override global
  - Falls back to @default if no widget-specific translation
  - Returns source text if no translation found

- **Disambiguation**:
  - Used when same source text has different meanings
  - Example from test lines 35-58: "Open" in different contexts

- **Use case**: Manual translation lookup in custom widgets
  ```python
  from qtpie.translations.store import lookup

  # Manual lookup (usually not needed - use t() instead)
  translated = lookup("MyWidget", "Submit button")
  print(translated)
  ```

#### Section 5: Plural Translations

- **`lookup_plural(context: str, source: str, count: int, disambiguation: str | None = None) -> str`**
  - Looks up plural form based on count
  - Replaces `%n` with actual number
  - Uses language-specific plural rules
  - Examples from test lines 104-132

- **Plural form selection**:
  - English: 1 → singular, others → plural (2 forms)
  - Other languages may have different rules
  - Source must include `%n` placeholder

- **Use case**: Dynamic pluralization in computed strings
  ```python
  from qtpie.translations.store import lookup_plural

  def get_status(file_count: int) -> str:
      return lookup_plural("@default", "%n file(s) selected", file_count)

  print(get_status(1))  # "1 file selected"
  print(get_status(5))  # "5 files selected"
  ```

#### Section 6: Binding Management (Internal)

- **`get_binding_count() -> int`**
- **`get_format_binding_count() -> int`**
- **`clear_bindings() -> None`**
  - Internal functions for tracking registered bindings
  - Used by QtPie for managing widget retranslation
  - Tests from lines 139-146

- **Note**: These are internal APIs - users should not normally call them
- **Use case**: Framework testing, debugging translation issues

#### Section 7: Context Fallback Rules

Detailed explanation of context resolution:

1. Try widget-specific context (e.g., "MyWidget")
2. Fall back to "@default" (global translations)
3. Fall back to source text

**Example hierarchy**:
```python
# Given these entries:
# - context="@default", source="Title", translations={"fr": "Titre"}
# - context="MyWidget", source="Title", translations={"fr": "Mon Titre"}

lookup("MyWidget", "Title")      # → "Mon Titre" (widget-specific)
lookup("OtherWidget", "Title")   # → "Titre" (fallback to @default)
lookup("OtherWidget", "Missing") # → "Missing" (fallback to source)
```

#### Section 8: Disambiguation Patterns

When to use disambiguation:

- Same source text with different meanings
- Same source text in different UI contexts
- Avoiding translation conflicts

**Common patterns**:
```python
# Context-based disambiguation
"Open|menu"    → menu action "Open"
"Open|status"  → status label "Open"

# Type-based disambiguation
"File|noun"    → the file
"File|verb"    → to file (documents)

# Location-based disambiguation
"Save|toolbar"
"Save|dialog"
```

#### Section 9: Best Practices

- **Use high-level API when possible**: `t()` handles context automatically
- **Store API for special cases**:
  - Custom translation sources (database, API)
  - Runtime translation management
  - Framework integration
  - Testing translation logic

- **Don't bypass the store**:
  - Always use store functions for lookups
  - Don't implement parallel translation systems
  - Maintains consistency with `t()` behavior

- **Context naming**:
  - Use widget class names for context
  - Use "@default" for global translations
  - Use descriptive disambiguators

#### Section 10: Integration Examples

##### Example 1: Load translations from database
```python
from qtpie.translations.store import load_translations_from_entries, TranslationEntry
import sqlite3

def load_from_db(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("""
        SELECT context, source, lang, translation
        FROM translations
    """)

    # Group by (context, source)
    entries_dict: dict[tuple[str, str], dict[str, str]] = {}
    for context, source, lang, translation in cursor:
        key = (context, source)
        if key not in entries_dict:
            entries_dict[key] = {}
        entries_dict[key][lang] = translation

    # Create TranslationEntry objects
    entries = [
        TranslationEntry(context=ctx, source=src, translations=trans)
        for (ctx, src), trans in entries_dict.items()
    ]

    load_translations_from_entries(entries)
```

##### Example 2: Custom language switcher UI
```python
from PySide6.QtWidgets import QComboBox
from qtpie import Widget, widget, new
from qtpie.translations.store import get_language, set_language

@widget
class LanguageSwitcher(Widget):
    _combo: QComboBox = new(
        currentTextChanged="on_language_changed"
    )

    def __setup__(self) -> None:
        self._combo.addItems(["English", "Français", "Español"])

        # Set current based on store
        current = get_language()
        lang_map = {"en": 0, "fr": 1, "es": 2}
        if current in lang_map:
            self._combo.setCurrentIndex(lang_map[current])

    def on_language_changed(self, text: str) -> None:
        lang_map = {
            "English": "en",
            "Français": "fr",
            "Español": "es"
        }
        set_language(lang_map[text])
```

##### Example 3: Runtime translation updates
```python
from qtpie.translations.store import load_translations_from_entries, TranslationEntry, set_language

def hot_reload_translations(yaml_path: str) -> None:
    """Reload translations without restarting app"""
    # Parse YAML (using internal parser or custom)
    entries = parse_yaml_translations(yaml_path)

    # Replace store contents
    load_translations_from_entries(entries)

    # Trigger retranslation by re-setting language
    current = get_language()
    set_language(current)
```

#### Section 11: Architecture Notes

Brief explanation of how the store works:

- **In-memory store**: Translations kept in memory for fast lookup
- **Reactive updates**: `set_language()` triggers widget retranslation
- **Context hierarchy**: Widget context → @default → source fallback
- **Binding registry**: Tracks all `t()` usages for retranslation
- **Thread safety**: Store operations are not thread-safe (use from main thread)

#### Section 12: Comparison: High-Level vs Store API

| Feature | High-Level (`t()`) | Store API |
|---------|-------------------|-----------|
| Load YAML | `@entrypoint(translations=...)` | `load_translations_from_entries()` |
| Translate text | `t("Hello")` | `lookup("@default", "Hello")` |
| Plurals | `t("%n items")(count)` | `lookup_plural("@default", "%n items", count)` |
| Auto-context | Yes (from widget class) | No (manual context) |
| Auto-retranslate | Yes (on `set_language`) | No (manual update) |
| Type safety | Full (returns `Translatable`) | Partial (returns `str`) |
| Use case | Normal app usage | Custom integrations |

**Recommendation**: Use `t()` unless you need custom translation loading or runtime management.

## 5. Code Examples Needed

All examples from `test_store.md`:

1. **Language management** (lines 8-13): get/set language
2. **Basic lookup** (lines 22-33): Simple translation lookup
3. **Disambiguation** (lines 35-58): Multiple translations for same source
4. **Context fallback** (lines 60-98): Widget-specific vs global
5. **Singular plurals** (lines 105-117): Plural with count=1
6. **Multiple plurals** (lines 119-132): Plural with count>1
7. **Binding management** (lines 139-146): Internal binding tracking

Additional examples to create:

1. **Database loader**: Load translations from SQL database
2. **JSON loader**: Load translations from REST API
3. **Custom language switcher**: Build language selector widget
4. **Hot reload**: Update translations without restart
5. **Plugin system**: Load translations from plugins
6. **Testing helper**: Create translations for tests

## 6. Cross-References

### Pages that should link TO translation-store.md:
- `guides/translations.md` - "For advanced usage, see Translation Store API"
- Future `advanced/extending.md` - "Custom translation sources use the store API"
- Future `contributing.md` - "Understanding the translation architecture"

### Pages that translation-store.md should link TO:
- `guides/translations.md` - "For normal usage, see Translations guide"
- `reference/decorators/entrypoint.md` - "High-level translation loading"
- `state/format-expressions.md` - "Format bindings work with translations"

### Internal cross-references:
- Link between sections (e.g., "See Plural Translations for plural forms")
- Link from lookup → disambiguation section
- Link from language management → binding management

## 7. Priority

**LOW PRIORITY - Advanced/Internal API**

### Reasoning:

1. **Internal Implementation**: The store is primarily used internally by QtPie's `t()` function. Most users never need direct store access.

2. **High-Level API Complete**: The `guides/translations.md` already documents the user-facing translation API comprehensively. It covers:
   - Basic `t()` usage
   - YAML format
   - Disambiguation
   - Plurals
   - Runtime language switching
   - CLI commands

3. **Narrow Use Cases**: Direct store API usage is only needed for:
   - Custom translation sources (non-YAML)
   - Framework integrators
   - Plugin systems
   - Advanced runtime translation management
   - Testing/debugging internals

4. **Stable API**: The store API is stable and unlikely to change, so documentation can be deferred.

5. **Self-Documenting Code**: The test file (`test_store.md`) effectively documents the API through examples.

### When to Prioritize:

Move to **MEDIUM priority** if:
- Users start building plugins/extensions
- Framework adoption increases
- Users request custom translation source support
- Contributing developers need architecture docs

Move to **HIGH priority** if:
- Planning to make store API official public API
- Building plugin ecosystem
- Targeting framework integrators

### Documentation Order (If Pursued):

1. **First**: Add one-paragraph mention in `guides/translations.md` linking to future advanced docs
2. **Second**: Create `advanced/translation-store.md` with comprehensive reference
3. **Third**: Add integration examples (database, API, plugins)
4. **Fourth**: Add to contributor documentation

For now, `guides/translations.md` covers user needs, and the store remains internal.

## 8. Additional Recommendations

### API Stability

If documenting the store API publicly:

- Mark functions as "stable" or "internal/unstable"
- Add version info (e.g., "Added in v2.0")
- Deprecation policy for future changes
- Semantic versioning considerations

### Testing Utilities

Consider adding helpers for tests:

```python
# qtpie.translations.testing (future)
def with_translations(entries: list[TranslationEntry]):
    """Context manager for temporary translations in tests"""

def with_language(lang: str):
    """Context manager for temporary language switch"""
```

### Documentation Maintenance

If added:
- Keep examples synced with `guides/translations.md`
- Ensure consistency in terminology
- Update when store API changes
- Add migration notes for breaking changes

### Plugin Documentation

If plugin system is planned:
- Separate "Building Plugins" guide
- Translation plugin example
- Best practices for plugin translations
- Namespace recommendations

## Summary

The Translation Store is a **low-priority** documentation task. The high-level translation API in `guides/translations.md` covers normal usage comprehensively. Store API documentation should only be added when:

1. Framework adoption grows and integrators need it
2. Plugin ecosystem is planned
3. Advanced users request custom translation source support

If/when documented:
- Place in new "Advanced" section (keeps it separate from user guides)
- Focus on custom integration use cases
- Emphasize that `t()` should be used for normal usage
- Provide practical examples (database, API, plugins)
- Cross-reference with high-level translation guide

The test file (`test_store.md`) effectively serves as internal documentation for now. Formal docs can wait until there's demonstrated user demand or a plugin ecosystem emerges.
