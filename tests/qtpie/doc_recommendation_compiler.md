# Documentation Proposal: Translation & Style Compilers

## Overview

QtPie has two compiler systems that need documentation:

1. **Translation Compiler** - Converts YAML translations to Qt `.ts` (and `.qm`) files
2. **Style Compiler** - Converts SCSS to QSS stylesheets

Both are production-ready with CLI interfaces but missing from user-facing docs.

---

## Priority: HIGH

**Rationale:**
- Translation compiler is mentioned in CLAUDE.md but not in user docs
- Both are essential for production deployment (`.qm` for translations, QSS for styling)
- Users need to know how to build production artifacts
- CLI commands already exist (`qtpie tr compile`) but undocumented

---

## Files to Add/Update

### 1. **CREATE: `docs/guides/build-tools.md`** (NEW)

Main documentation page covering both compilers.

**Suggested Nav Location:**
```yaml
nav:
  - Guides:
      - Build Tools: guides/build-tools.md  # Add after 'guides/app.md'
```

**Content Outline:**
```markdown
# Build Tools

## Translation Compiler

### Overview
- Compiles YAML translations to Qt .ts/.qm files
- Supports multiple languages
- Integration with Qt Linguist workflow

### CLI Usage
- Basic: compile YAML to .ts
- Advanced: compile to .qm (requires lrelease)
- Selective language compilation
- Output directory control

### Examples
- Single file compilation
- Multiple file compilation
- Production builds
- Development workflow

### Programmatic API
- compile_translations() function
- compile_to_ts() for single language
- compile_qm() for binary format
- get_all_languages() helper

### Integration
- With @entrypoint for dev mode
- Production builds with .qm files
- CI/CD pipeline examples

## Style Compiler

### Overview
- Compiles SCSS to QSS stylesheets
- Supports SCSS features (variables, nesting, mixins)
- Import resolution

### Usage
- compile_scss() function
- Search paths for @import
- File watching (development)

### Examples
- Basic SCSS to QSS
- With variables and nesting
- Multi-file projects with @import

### Integration
- Loading compiled QSS in apps
- Development vs production workflows
```

---

### 2. **UPDATE: `docs/guides/translations.md`** (IF EXISTS)

Add section on compilation workflow if translation docs exist.

**Add Section:**
```markdown
## Building for Production

### Compiling to .ts/.qm Files

For production, compile YAML to Qt's binary .qm format:

```bash
qtpie tr compile translations.yml -o ./i18n/ --qm
```

See [Build Tools](build-tools.md) for full compiler documentation.
```

---

### 3. **UPDATE: `docs/index.md`**

Add build tools to feature highlights (optional, low priority).

---

## Code Examples Needed

### Translation Compiler Examples

```python
# Example 1: CLI usage
"""
# Compile all languages
qtpie tr compile app.yml -o ./i18n/

# Compile specific languages only
qtpie tr compile app.yml -o ./i18n/ --lang fr --lang de

# Also generate .qm binary files
qtpie tr compile app.yml -o ./i18n/ --qm

# List all translations
qtpie tr list app.yml
"""

# Example 2: Programmatic usage
from pathlib import Path
from qtpie.translations import compile_translations, parse_yaml_files

entries = parse_yaml_files(["app.yml"])
ts_files = compile_translations(entries, Path("./i18n"))
print(f"Generated {len(ts_files)} .ts files")

# Example 3: Development vs production
@entrypoint(
    translations="translations.yml",  # Dev: loads YAML directly
    language="fr",
    watch_translations=True,  # Hot-reload in dev
)

# Production: load .qm files
from PySide6.QtCore import QTranslator
translator = QTranslator()
translator.load("./i18n/fr.qm")
app.installTranslator(translator)

# Example 4: CI/CD pipeline
"""
# In your CI build script
uv run qtpie tr compile translations/*.yml -o ./dist/i18n/ --qm

# Package .qm files with your app (not .yml)
"""
```

### Style Compiler Examples

```python
# Example 1: Basic SCSS to QSS
from qtpie.styles import compile_scss

compile_scss(
    scss_path="styles/main.scss",
    qss_path="dist/main.qss"
)

# Example 2: With search paths for @import
compile_scss(
    scss_path="styles/main.scss",
    qss_path="dist/main.qss",
    search_paths=["styles/components", "styles/themes"]
)

# Example 3: SCSS with variables
"""
// main.scss
$primary-color: #3498db;
$border-radius: 4px;

QPushButton {
    background-color: $primary-color;
    border-radius: $border-radius;

    &:hover {
        background-color: darken($primary-color, 10%);
    }
}
"""

# Example 4: Loading in app
from qtpie import entrypoint, Widget, widget
from pathlib import Path

@entrypoint
@widget
class MyApp(Widget):
    def __setup__(self) -> None:
        qss = Path("dist/main.qss").read_text()
        self.setStyleSheet(qss)
```

---

## Cross-References

### From Build Tools Page
- Link to [Translations Guide](translations.md) - YAML format, t() function
- Link to [Styling](../basics/styling.md) - QSS basics
- Link to [App & Entry Points](app.md) - Loading translations in production
- Link to Qt Linguist docs (external) - for editing .ts files

### To Build Tools Page
- From [Translations Guide](translations.md) - "See Build Tools for compiling to .qm"
- From [Styling](../basics/styling.md) - "Use SCSS compiler for complex stylesheets"
- From [App & Entry Points](app.md) - "See Build Tools for production builds"

---

## Technical Details to Document

### Translation Compiler

**Key Functions:**
- `compile_to_ts(entries, language)` - Single language to XML
- `compile_translations(entries, output_dir, languages=None)` - Batch compile to .ts
- `compile_qm(ts_path, qm_path=None)` - Binary .qm format
- `compile_all_qm(ts_files, output_dir=None)` - Batch .qm compilation
- `get_all_languages(entries)` - Extract language codes

**CLI Commands:**
- `qtpie tr compile <input> -o <output> [--qm] [--lang <lang>...]`
- `qtpie tr list <input>`

**Requirements:**
- `lrelease` tool required for .qm compilation (from PySide6 or Qt)
- Auto-detects `pyside6-lrelease` or system `lrelease`

**Output Format:**
- `.ts` files: XML format compatible with Qt Linguist
- `.qm` files: Binary format for runtime loading

### Style Compiler

**Key Function:**
- `compile_scss(scss_path, qss_path, search_paths=None)`

**Features:**
- Full SCSS support via pyScss library
- `@import` resolution with search paths
- Variables, nesting, mixins, functions

**Limitations:**
- QSS is a subset of CSS - not all SCSS features apply
- No live preview (use file watcher for dev)

---

## Missing Documentation Context

Based on mkdocs.yml nav structure, these docs appear planned but don't exist yet:
- `docs/start/` directory (install, hello-world, concepts)
- `docs/basics/` directory (widgets, layouts, signals, styling)
- `docs/state/` directory (variables, bindings, format-expressions, property-bindings)
- `docs/data/` directory (records, lists-dicts, validation, dirty-tracking)
- `docs/guides/` directory (windows-menus, forms, grids, translations, app, async, testing)
- `docs/reference/` directory (decorators, factories, classes, styles)

**Recommendation:** Create `docs/guides/build-tools.md` as a standalone page that can be written immediately, since build tools are orthogonal to other guides.

---

## Implementation Notes

1. **Do not create full guides yet** - many referenced guides don't exist
2. **Focus on build-tools.md** as standalone documentation
3. **Link to CLAUDE.md sections** as interim cross-references if needed
4. **Wait for other guides** before adding extensive cross-links
5. **Prioritize CLI examples** since that's the primary user interface

---

## Urgency Assessment

**HIGH Priority because:**
- Translation compiler CLI exists but is completely undocumented in user docs
- Users following translation guide in CLAUDE.md hit a wall at deployment
- Style compiler provides critical SCSS support but users don't know it exists
- Both are production-ready, tested features (test_compiler.md exists)
- Low-hanging fruit: small doc page, big user value

**Can be documented independently** - doesn't depend on other missing guides.
