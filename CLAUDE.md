# QtPie - Context for Claude

## What Is This?

**QtPie** is a declarative UI library for Qt/PySide6 in Python. Think React/Vue patterns but for desktop apps. Or other GUI frameworks. And with the 'Conventions over Configuration' culture of Ruby on Rails.

Although we actually use `qtpy` library for all of dependencies so it works with PySide6 or PyQt6.

And we use qasync for async goodness.

## Running Things

**Run tests frequently!**

```bash
# Run all tests
uv run pytest tests/ -v

# Type check
uv run pyright lib/qtpie/ tests/unit/

# Lint
uv run ruff check lib/qtpie/ tests/unit/

# Format
uv run ruff format lib/qtpie/ tests/unit/
```

---

## ⚠️ CRITICAL: BEFORE ANNOUNCING ANY FEATURE AS DONE ⚠️

**YOU MUST RUN ALL THREE CHECKS ON THE ENTIRE PROJECT BEFORE SAYING A FEATURE IS COMPLETE:**

```bash
# 1. Ruff (linting) - ENTIRE PROJECT
uv run ruff check lib/qtpie/ tests/

# 2. Pyright (type checking) - ENTIRE PROJECT
uv run pyright lib/qtpie/ tests/unit/

# 3. Pytest (tests) - ENTIRE PROJECT
uv run python -m pytest tests/ -v
```

**ALL THREE MUST PASS WITH ZERO ERRORS BEFORE YOU ANNOUNCE COMPLETION.**

- Do NOT run checks on just the files you modified
- Do NOT skip ruff because "pyright passed"
- Do NOT skip any of these checks for any reason
- Do NOT announce a feature as done until all three pass

If ANY check fails, fix it FIRST, then re-run ALL checks again.

---

## Design Principles

1. **Declarative over imperative** - define what, not how
2. **Type safety** - pyright strict, no `Any` leakage, no ignore comments
3. **Zero magic strings** - signals connected by method reference when possible
4. **Dataclass patterns** - `@dataclass_transform()` for IDE support
5. **Test-driven** - write tests first, then implement
6. **Minimal API surface** - few things that compose well

---

## Code Style - No Unnecessary Bullshit

**Don't add imports or code that isn't actually needed.**

- **NO `from __future__ import annotations`** - Python 3.13+ doesn't need it. Only use if you have actual forward references (rare).
- **NO unnecessary imports** - Don't import things "just in case"
- **NO cargo-cult patterns** - If you can't explain why something is needed, don't add it
- **NO defensive coding against impossible cases** - Trust the type system
- **NO premature abstractions** - Write concrete code first
- Only use `if TYPE_CHECKING` when it super makes sense to use it

When in doubt, leave it out. Simpler is better.
