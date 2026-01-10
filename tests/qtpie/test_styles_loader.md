# Stylesheet Loader Tests

## Loading from Local QSS Files

Loads stylesheet content from filesystem paths. Returns empty string for missing files.

```python
def test_loads_existing_file(self, tmp_path: Path) -> None:
    """Loads content from existing local QSS file."""
    qss_file = tmp_path / "styles.qss"
    qss_file.write_text("QPushButton { color: red; }")

    result = load_stylesheet(qss_path=str(qss_file))

    assert_that(result).contains("QPushButton")
    assert_that(result).contains("color: red")
```

## Loading from QRC Resources

Loads stylesheet content from Qt resource files (`:/ paths`). Uses QFile and QTextStream.

```python
def test_loads_from_qrc(self, mock_qfile: tuple[MagicMock, MagicMock]) -> None:
    """Loads content from QRC resource."""
    mock_file, mock_stream = mock_qfile

    with (
        patch("qtpie.styles.loader.QFile", return_value=mock_file),
        patch("qtpie.styles.loader.QTextStream", return_value=mock_stream),
    ):
        result = load_stylesheet(qrc_path=":/styles/test_styles.qss")

    assert_that(result).contains("QPushButton")
    assert_that(result).contains("background-color: red")
```

## Local-to-QRC Fallback

Local paths take precedence. Falls back to QRC when local file doesn't exist.

```python
def test_falls_back_to_qrc_when_local_missing(self) -> None:
    """Falls back to QRC when local file doesn't exist."""
    mock_file = MagicMock()
    mock_file.open.return_value = True

    mock_stream = MagicMock()
    mock_stream.readAll.return_value = "QPushButton { background-color: red; }"

    with (
        patch("qtpie.styles.loader.QFile", return_value=mock_file),
        patch("qtpie.styles.loader.QTextStream", return_value=mock_stream),
    ):
        result = load_stylesheet(
            qss_path="/nonexistent/styles.qss",
            qrc_path=":/styles/test_styles.qss",
        )

    # Should get QRC content
    assert_that(result).contains("QPushButton")
    assert_that(result).contains("background-color: red")
```
