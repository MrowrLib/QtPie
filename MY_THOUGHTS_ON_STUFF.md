# My Thoughts on SCSS/Styling/App Architecture

## Current State (IMPLEMENTED in qtpie/styles/)

### What's Built ✅

| Module | What it does |
|--------|--------------|
| `compiler.py` | `compile_scss()` - Uses pyscss to compile SCSS → QSS |
| `loader.py` | `load_stylesheet()` - Load from local file or QRC resource (with fallback) |
| `watcher.py` | `QssWatcher`, `ScssWatcher`, `watch_qss()`, `watch_scss()`, `watch_styles()` |

### compiler.py
```python
compile_scss(scss_path, qss_path, search_paths=None)
# - Uses `from scss import Compiler` (pyscss - pure Python)
# - Supports @import resolution via search_paths
# - Creates output directory if needed
# - Raises FileNotFoundError or SassError on problems
```

### loader.py
```python
load_stylesheet(qss_path=None, qrc_path=None) -> str
# - Tries local file first, falls back to QRC resource
# - Returns empty string if neither exists
# - Good for: dev mode uses local, prod uses bundled QRC
```

### watcher.py
```python
watch_qss(target, qss_path) -> QssWatcher
watch_scss(target, scss_path, qss_path, search_paths=None) -> ScssWatcher
watch_styles(target, qss_path, scss_path=None, search_paths=None) -> QssWatcher | ScssWatcher

# Features:
# - Target can be QApplication OR QWidget
# - Uses QFileSystemWatcher + debouncing (50ms)
# - Handles editor delete+recreate (vim, VSCode)
# - Watches for file creation if file doesn't exist yet
# - ScssWatcher watches all .scss files in search_paths
```

### Test Coverage
- 22 tests across 3 test files
- Tests for: compilation, imports, watchers, hot reload, editor quirks, fallback behavior

---

## What's NOT Built Yet

1. **App class** - No wrapper for QApplication with convenience features
2. **CSS class helpers** - `add_class()`, `remove_class()`, `toggle_class()` from drafts
3. **Dark mode setup** - No helpers for light/dark mode configuration
4. **qasync integration** - No async event loop wrapper

---

## Problems / Concerns

1. **Dark mode env var timing** - MUST be set BEFORE `QApplication()` is created. If we add an `App` class it can handle this, but standalone users need a helper.

2. **Coupling** - Current style utilities are nicely decoupled! Keep it that way. Don't force qasync on people who just want styles.

3. **Single top-level stylesheet** - Want ONE stylesheet on the app, not per-widget. Current `watch_*` functions support this by accepting QApplication as target. ✅

---

## Qt 6.5+ / 6.8+ Dark Mode News

**Detection (Qt 6.5+):**
```python
QGuiApplication.styleHints().colorScheme()  # Returns Qt.ColorScheme.Dark or .Light
```

**Runtime switching (Qt 6.8+):**
```python
# Can now SET the color scheme at runtime!
app.styleHints().setColorScheme(Qt.ColorScheme.Dark)
```

This means the env var hack is less necessary on modern Qt. Can detect version and use new APIs when available.

---

## Design Options

### Option A: Keep App class, make it smarter
- Detect Qt version, use new APIs when available
- Fall back to env var for older Qt
- Everything in one place

### Option B: Separate concerns (LEANING THIS WAY)
- `configure_dark_mode()` helper - call before ANY QApplication
- Style utilities already standalone ✅
- `App` is optional convenience wrapper
- More flexible, less coupled

### Option C: Minimal helper functions
- `set_color_scheme(mode: "light" | "dark" | "system")`
- Style utilities already exist ✅
- Let users compose as they wish
- Most flexible, least opinionated

---

## Questions to Decide

1. Support runtime light/dark switching (Qt 6.8+ only)?
2. Keep it simple with startup-only mode selection?
3. Detect Qt version and offer both?
4. How tightly couple SCSS to App vs standalone? → **Already standalone, keep it that way**
5. Require `App` class or make it optional convenience? → **Optional convenience**

---

## Next Steps

1. **CSS class helpers** - Add `add_class()`, `remove_class()`, `toggle_class()`, `has_class()` to qtpie/styles/
2. **Dark mode helper** - `configure_color_scheme()` that handles env var vs Qt 6.8+ API
3. **App class** (optional) - Convenience wrapper that ties it all together

---

## Files to Reference

### Implemented (USE THESE)
- `qtpie/styles/compiler.py` - SCSS compilation
- `qtpie/styles/loader.py` - Load from file or QRC
- `qtpie/styles/watcher.py` - Hot reload watchers

### From Drafts (FOR REFERENCE)
- `DRAFT/other_drafting/qtpie/styles.py` - has QtStyleClass (add/remove/toggle CSS classes)
- `DRAFT/more_recent_drafting/qtpie/qtpie/app.py` - App class design
- `DRAFT/more_recent_drafting/qtpie/qtpie/startup.py` - run_app with qasync
- `DRAFT/other_drafting/qtpie/run_app.py` - older run_app with dev mode flag
