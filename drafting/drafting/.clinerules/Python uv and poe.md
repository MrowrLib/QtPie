## 🐍 Python Project Tooling Guide

This project uses **[uv](https://github.com/astral-sh/uv)** for dependency management and **Poe the Poet** for task automation.

---

### 📦 uv
- `uv` is used for all dependency management and running Python commands.
- Always use `uv run <command>` — never activate the virtual environment manually.
- All scripts and CLI tools must run through `uv run`.

#### Example:
```bash
uv run python some_script.py
uv run app --dev
```

#### Scripts (`pyproject.toml`)
```toml
[project.scripts]
app = "mrowrai.__main__:main"
```
- This defines the entrypoint for the application as `uv run app`.

> Note: `uv` uses the [PEP 621 `project.scripts`](https://packaging.python.org/en/latest/specifications/declaring-project-metadata/#scripts) section instead of `[tool.poetry.scripts]`.

---

### ⚙️ Poe the Poet
- Poe is used as the task runner via `uv run poe <task>`.
- Tasks are defined under `[tool.poe.tasks]` in `pyproject.toml`.

#### Common Tasks:
```toml
[tool.poe.tasks]
dev = "uv run app --dev"
dev-dark = "uv run app --dev --dark"
dev-debug = "uv run app --dev --debug"
dev-light = "uv run app --dev --light"
prod = "uv run app"
prod-dark = "uv run app --dark"
prod-light = "uv run app --light"
exe = "pyinstaller --onefile --windowed --noconfirm --name \"Papyrus Pad\" --icon resources/images/icon.ico src/mrowrai/app/__main__.py"
exe-dir = "pyinstaller --onedir --windowed --noconfirm --name \"Papyrus Pad\" --icon resources/images/icon.ico src/mrowrai/app/__main__.py"
qrc = "pyside6-rcc -o src/mrowrai/app/qrc_resources.py resources/resources.qrc"
```

#### Run a Poe task:
```bash
uv run poe dev
uv run poe prod-dark
uv run poe qrc
```

#### Supported Formats:
```toml
[tool.poe.tasks]
# Shell command
hello = "echo Hello world"

# Python script
start.script = "mrowrai.__main__:main"

# Shell (explicit)
custom.shell = "some_shell_command --arg1 value"
```

---

### 🛑 Avoid
- Never manually activate virtual environments
- Never use `pip` or `uv pip`
- Never run Python commands outside `uv run`

---

This setup ensures fast installs, consistent environments, reproducible builds, and centralized task automation using modern Python tooling.
