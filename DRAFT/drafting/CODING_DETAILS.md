# QtPie Coding Details

## 🧠 Project Philosophy & Goals

QtPie is a modern, decorator-driven PyQt UI framework focused on:

- **Declarative widget construction** using Python decorators for both dataclass-style and manual-init widgets.
- **Strong typing** and modern Python 3.13+ idioms everywhere.
- **Explicit, testable, and extensible** code with a focus on clarity and maintainability.
- **Separation of concerns**: layout, styling, and widget logic are all cleanly separated.

## 🧱 Architecture Overview

- **Decorators**:
  - `@widget`: For dataclass-based widgets. Automatically applies `dataclass` and injects Qt widget setup.
  - `@widget_class`: For widgets with custom `__init__`. Also injects Qt widget setup.
  - Both use a shared `_widget_impl` function for all initialization logic, ensuring consistency.
- **Layout Types**: `"horizontal"`, `"vertical"`, `"grid"`, `"form"` (see `qtpie/types/widget_layout_type.py`).
- **Styling**:
  - Use `add_classes(widget, list[str])` to add CSS-like classes.
  - Use `get_classes(widget)` to retrieve the current class list.
  - The `classes` parameter on both decorators is the canonical way to set initial classes.
- **Helpers**: `_widget_impl` is the only injection point for decorator logic.

## 🧪 Testing Philosophy & Organization

- **Frameworks**: All tests use `pytest` and `assertpy` for fluent, readable assertions.
- **Assertion Style**:
  - Use `assert_that(...)` for all assertions except `None` checks (which use `assert x is None`).
  - No direct use of `isinstance` or internals—always use public API like `get_classes()`.
- **Test Structure**:
  - Each test embeds its own widget class definition, decorated inline, for maximum explicitness and isolation.
  - No shared test fixtures or helpers for widget classes—every test is self-contained.
  - This approach makes it easy to reason about each test and prevents accidental cross-test pollution.

### Test File Overview

- **tests/decorators/test_widget.py**  
  Tests the `@widget` decorator, including dataclass behavior, field defaults, layout modes, and the `classes` parameter.

- **tests/decorators/test_widget_class_decorator.py**  
  Tests the `@widget_class` decorator, focusing on manual `__init__` widgets, layout modes, and the `classes` parameter.

- **tests/decorators/test_widget_decorator.py**  
  Focuses on layout mode handling and class assignment for widgets using the `@widget` decorator.

- **tests/styles/test_style_classes.py**  
  Tests the styling system, especially `add_classes` and `get_classes`, ensuring class lists are managed correctly.

- **tests/test_config.py**  
  Validates configuration logic and any project-level settings.

- **tests/decorators/_test_helpers.py**  
  Contains minor helpers for test code, but widget classes are always defined inline in each test for clarity.

- **Other files**:  
  - `example_widgets.py`, `widget_decorator_examples.py`, `widget_class_decorator_examples.py`, and `test_widget_shared.py` are for illustrative or legacy purposes and are not used in the main test suite.

## 🧼 Coding Style

- **Python 3.13+**: Use the latest syntax and typing features.
- **Strong typing everywhere**:
  - No `Any`, no `Unknown`.
  - Use `|` instead of `Union`.
  - All function and method signatures are fully typed.
- **@dataclass** for value types and simple data containers.
- **No `__init__.py`**: All imports are explicit.
- **Modern idioms**:
  - Use `match` statements where appropriate.
  - Use `| None` instead of `Optional[...]`.
- **No semicolons, no unused imports**: The formatter will remove unused imports on save.

## 🛠 Tooling

- **uv**: Used for dependency management and running Python commands (`uv run ...`).
- **poe**: Task runner for common project tasks (`uv run poe dev`, `uv run poe qrc`, etc).
- **Never** activate virtual environments manually or use `pip` directly.

## 🧩 Extensibility

- Decorators are composable and easy to extend with new parameters.
- `_widget_impl` is the central place for all widget setup logic.
- Adding new layout modes or decorator options is straightforward.

## 🧭 Future Directions

- More layout primitives (e.g., stack, split).
- Style class inheritance and advanced styling features.
- Component registry or dependency injection.
- Live preview/hot reload for rapid UI development.

---

## 👩‍💻 Onboarding Notes

- **Tests are explicit and self-contained**: Every widget class is defined inside its test, decorated inline, and never reused. This makes the test suite easy to read and reason about.
- **Public API boundaries are respected**: Tests interact with widgets only through their public API (e.g., `get_classes()`), never through Qt internals.
- **Read the .clinerules/** directory**: Project-specific coding standards and test conventions are enforced via `.clinerules/`.

Welcome to QtPie! If you’re reading this, you’re already on the path to writing beautiful, explicit, and modern PyQt code.
