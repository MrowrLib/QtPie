# CLI Documentation Proposal

## Overview

The QtPie CLI (`qtpie` command) provides translation management tools. Currently, the CLI is documented inline in CLAUDE.md but deserves dedicated user-facing documentation.

## Files to Add/Update

### New Files

1. **`docs/guides/cli.md`** - Main CLI reference page
   - Overview of CLI capabilities
   - Installation/availability (automatically available after `pip install qtpie`)
   - Command structure and help system

2. **`docs/guides/cli-translations.md`** - Translation CLI commands (detailed)
   - `tr compile` command reference
   - `tr list` command reference
   - Workflow examples (dev vs production)
   - Integration with build processes

### Files to Update

1. **`docs/guides/translations.md`** (existing)
   - Add section linking to CLI docs: "See [CLI Translation Tools](cli-translations.md) for command reference"
   - Brief mention that YAML can be compiled to .ts/.qm files
   - Link to CLI page for compilation details

2. **`mkdocs.yml`** - Update nav structure (see below)

## Suggested Nav Location

Add under **Guides** section (after translations):

```yaml
  - Guides:
      - Windows & Menus: guides/windows-menus.md
      - Form Layouts: guides/forms.md
      - Grid Layouts: guides/grids.md
      - Translations: guides/translations.md
      - CLI Tools: guides/cli.md           # NEW - overview
      - CLI Translations: guides/cli-translations.md  # NEW - detailed commands
      - App & Entry Points: guides/app.md
      - Async: guides/async.md
      - Testing: guides/testing.md
```

**Alternative**: Create a separate "Tools" section if more CLI features are planned:

```yaml
  - Tools:
      - CLI Reference: tools/cli.md
      - Translation Commands: tools/cli-translations.md
```

## Content Outline

### `docs/guides/cli.md`

```markdown
# QtPie CLI

Overview and installation
- Automatically installed with `pip install qtpie`
- Entry point: `uv run qtpie` or `qtpie`

Available Commands
- `qtpie --help` - Show help
- `qtpie tr` - Translation management (see CLI Translations)

Getting Help
- Global help: `qtpie --help`
- Command help: `qtpie tr --help`
- Subcommand help: `qtpie tr compile --help`

Usage Patterns
- Development workflows
- CI/CD integration
```

### `docs/guides/cli-translations.md`

```markdown
# CLI Translation Tools

The `qtpie tr` command provides translation file management.

## Compile Translations

Convert YAML to Qt .ts/.qm files

### Basic Usage
### Output Directory
### Language Filtering (--lang)
### Binary .qm Generation (--qm)
### Multiple Input Files
### CI/CD Examples

## List Translations

View all translations in YAML files

### Basic Usage
### Output Format
### Disambiguation Display

## Workflows

### Development Workflow
- Use YAML + hot-reload in @entrypoint
- No compilation needed
- Fast iteration

### Production Workflow
- Compile to .qm for distribution
- Load with QTranslator
- Smaller bundle size

## Integration Examples

### Pre-commit Hook
### GitHub Actions
### Build Scripts
```

## Code Examples Needed

### CLI Help
```bash
$ qtpie --help
Usage: qtpie [OPTIONS] COMMAND [ARGS]...

Commands:
  tr  Translation management
```

### Compile Basic
```bash
# Generate .ts files
uv run qtpie tr compile translations.yml -o ./i18n/

# Output:
# Generated 2 .ts file(s) in ./i18n/
#   - fr.ts
#   - de.ts
```

### Compile with Language Filter
```bash
# Only French
uv run qtpie tr compile translations.yml -o ./i18n/ --lang fr

# Output:
# Generated 1 .ts file(s) in ./i18n/
#   - fr.ts
```

### Compile with .qm Files
```bash
# Requires lrelease in PATH
uv run qtpie tr compile translations.yml -o ./i18n/ --qm

# Output:
# Generated 2 .ts file(s) in ./i18n/
#   - fr.ts
#   - de.ts
# Generated 2 .qm file(s) in ./i18n/
#   - fr.qm
#   - de.qm
```

### Multiple Input Files
```bash
uv run qtpie tr compile translations.yml strings.yml -o ./i18n/
```

### List Translations
```bash
$ uv run qtpie tr list translations.yml

Context: :global
Languages: fr, de
Entries: 2

  Hello
    fr: Bonjour
    de: Hallo

  Goodbye
    fr: Au revoir
    de: Auf Wiedersehen
```

### List with Disambiguation
```bash
$ uv run qtpie tr list translations.yml

Context: :global
Languages: fr
Entries: 2

  Open (menu)
    fr: Ouvrir

  Open (status)
    fr: Ouvert
```

### CI/CD Examples

**GitHub Actions:**
```yaml
- name: Compile Translations
  run: |
    uv run qtpie tr compile translations.yml -o ./i18n/ --qm
```

**Pre-commit Hook:**
```bash
#!/bin/bash
# .git/hooks/pre-commit
uv run qtpie tr compile translations.yml -o ./i18n/ --qm
git add i18n/*.ts i18n/*.qm
```

**Build Script:**
```python
# build.py
import subprocess

subprocess.run([
    "uv", "run", "qtpie", "tr", "compile",
    "translations.yml", "-o", "./dist/i18n/", "--qm"
], check=True)
```

## Cross-References

### From Translation Guide
- "For command-line translation management, see [CLI Translations](cli-translations.md)"
- "To compile YAML to .ts/.qm files, use `qtpie tr compile` ([reference](cli-translations.md#compile-translations))"

### From CLI Pages
- Link to main Translations guide for YAML format
- Link to @entrypoint decorator reference for hot-reload setup
- Link to examples for complete translation workflows

### From Installation/Getting Started
- Mention CLI is automatically available after install
- Link to CLI reference for available commands

### From Examples Page
- Add example showing full translation workflow (YAML → CLI → runtime)

## Priority

**HIGH**

### Rationale

1. **User Discovery**: CLI is mentioned in CLAUDE.md but not in user-facing docs. Users who install QtPie won't know the CLI exists or how to use it.

2. **Translation Feature Completeness**: Translations are documented (guides/translations.md), but without CLI docs, users don't know how to:
   - Generate production-ready .qm files
   - Filter languages for deployment
   - Integrate with build systems
   - Inspect YAML files before runtime

3. **Professional Polish**: CLI tools are a sign of mature tooling. Undocumented CLI makes the library feel incomplete.

4. **Low Effort, High Impact**: Test file (test_cli.md) already provides excellent examples. Converting to docs is straightforward.

5. **Developer Workflow**: CLI tools are essential for:
   - CI/CD pipelines
   - Build automation
   - Deployment preparation
   - Team collaboration (committing .ts files)

## Implementation Notes

### Tone and Style
- Match existing docs: concise, example-heavy, practical
- Start with simple examples, progress to advanced
- Use `uv run` consistently (matches CLAUDE.md conventions)

### Structure Considerations
- Keep CLI overview separate from detailed command reference
- Translation commands get their own page (likely to grow)
- Leave room for future CLI commands (codegen, project init, etc.)

### Testing Integration
- All examples should match test_cli.md test cases
- Ensure command output examples are accurate
- Reference error messages users might encounter

### Search Optimization
- Use keywords: "compile translations", "ts files", "qm files", "lrelease"
- Include common questions: "how to generate .ts", "translation workflow"
- Add synonyms: "i18n", "internationalization", "localization"
