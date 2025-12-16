# My Thoughts on SCSS/Styling/App Architecture

## Current State (from DRAFT/more_recent_drafting)

### pyscss version (`styles/stylesheet.py`)
- Uses `from scss import Compiler` (pyscss - pure Python, works great)
- `StyleConfiguration` dataclass: `watch`, `scss_path`, `qss_path`, `qss_resource_path`, `watch_folders`
- `StylesheetWatcher` uses `QFileSystemWatcher` for hot reload
- Compiles with `Compiler(search_path=[...]).compile(path)`
- Transforms `data-` attributes to Qt-compatible format via regex

### App class (`app.py`)
```python
class App(QApplication):
    def __init__(self, name, version, light_mode=False, dark_mode=False, styles=None):
        # Dark mode MUST be set via env var BEFORE super().__init__()
        if light_mode:
            os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=0"
        elif dark_mode:
            os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=2"

        super().__init__(...)

    def run(self):
        run_app(self, styles=self._styles)
```

### run_app (`startup.py`)
- Takes `app` + `StyleConfiguration`
- If `watch=True`: starts `watch_qss()` for hot reload
- Otherwise: loads static QSS from `qss_resource_path`
- Runs async event loop via `qasync`

---

## Problems / Concerns

1. **Dark mode env var timing** - MUST be set BEFORE `QApplication()` is created. Current `App` class handles this, but if someone doesn't use `App`, they're stuck.

2. **Coupling** - SCSS/styles are coupled to `App.run()`. What if someone wants styles but not the `qasync` event loop? Or vice versa?

3. **Single top-level stylesheet** - Want ONE stylesheet on the app, not per-widget. Easier to customize, let users override.

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

### Option B: Separate concerns
- `configure_dark_mode()` helper - call before ANY QApplication
- `StyleManager` class - independent of App, just needs QApplication reference
- `App` is optional convenience wrapper
- More flexible, less coupled

### Option C: Minimal helper functions
- `set_color_scheme(mode: "light" | "dark" | "system")`
- `watch_scss(app, config)`
- Let users compose as they wish
- Most flexible, least opinionated

---

## Questions to Decide

1. Support runtime light/dark switching (Qt 6.8+ only)?
2. Keep it simple with startup-only mode selection?
3. Detect Qt version and offer both?
4. How tightly couple SCSS to App vs standalone?
5. Require `App` class or make it optional convenience?

---

## Files to Reference

- `DRAFT/more_recent_drafting/qtpie/qtpie/styles/stylesheet.py` - pyscss version (USE THIS)
- `DRAFT/more_recent_drafting/qtpie/qtpie/app.py` - App class
- `DRAFT/more_recent_drafting/qtpie/qtpie/startup.py` - run_app with qasync
- `DRAFT/other_drafting/qtpie/styles.py` - has QtStyleClass (add/remove/toggle CSS classes)
- `DRAFT/other_drafting/qtpie/run_app.py` - older run_app with dev mode flag
