# Styles Compiler Tests

## SCSS to QSS Compilation

Compiles SCSS files to Qt StyleSheet (QSS) format.

```python
compile_scss(
    scss_path=str(FIXTURES / "single_file" / "simple.scss"),
    qss_path=str(qss_path),
)

assert_that(qss_path.exists()).is_true()
qss = qss_path.read_text()
assert_that(qss).contains("QPushButton")
assert_that(qss).contains("background-color: blue")
```

## Import Resolution

Resolves `@import` statements from one or more search directories, including variable resolution across files.

```python
compile_scss(
    scss_path=str(FIXTURES / "two_search_dirs" / "main.scss"),
    qss_path=str(qss_path),
    search_paths=[
        str(FIXTURES / "two_search_dirs" / "core"),
        str(FIXTURES / "two_search_dirs" / "themes"),
    ],
)

assert_that(qss_path.exists()).is_true()
qss = qss_path.read_text()
# Variables from core/_variables.scss should be resolved in themes/_theme.scss
assert_that(qss).contains("16px")  # $base-size
assert_that(qss).contains("#333333")  # $base-color
```

## Auto-Create Output Directory

Creates output directory structure if it doesn't exist.

```python
qss_path = tmp_path / "nested" / "deep" / "output.qss"

compile_scss(
    scss_path=str(FIXTURES / "single_file" / "simple.scss"),
    qss_path=str(qss_path),
)

assert_that(qss_path.exists()).is_true()
```

## Error Handling

Raises appropriate errors for missing files and syntax errors.

```python
# Missing file
with pytest.raises(FileNotFoundError, match="SCSS file not found"):
    compile_scss(
        scss_path=str(tmp_path / "nonexistent.scss"),
        qss_path=str(qss_path),
    )

# Syntax error
bad_scss.write_text("QPushButton { color: $undefined_variable; }")
with pytest.raises(SassError):
    compile_scss(
        scss_path=str(bad_scss),
        qss_path=str(qss_path),
    )
```
