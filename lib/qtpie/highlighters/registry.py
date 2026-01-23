"""Registry for mapping MIME types to syntax highlighters."""

from qtpy.QtGui import QSyntaxHighlighter

# Global registry: MIME type -> highlighter class
_mime_registry: dict[str, type[QSyntaxHighlighter]] = {}


def register_highlighter(mime_type: str, highlighter_class: type[QSyntaxHighlighter]) -> None:
    """Register a highlighter class for a MIME type.

    Args:
        mime_type: The MIME type (e.g., "application/json", "text/html")
        highlighter_class: The QSyntaxHighlighter subclass to use
    """
    _mime_registry[mime_type] = highlighter_class


def get_highlighter_for_mime(mime_type: str | None) -> type[QSyntaxHighlighter] | None:
    """Get the highlighter class for a MIME type.

    Args:
        mime_type: The MIME type to look up (can be None)

    Returns:
        The highlighter class, or None if no match found
    """
    if mime_type is None:
        return None
    return _mime_registry.get(mime_type)


def get_registered_mime_types() -> list[str]:
    """Get all registered MIME types."""
    return list(_mime_registry.keys())


def _register_default_highlighters() -> None:
    """Register built-in highlighters for common MIME types."""
    from qtpie.highlighters.css import CssHighlighter
    from qtpie.highlighters.html import HtmlHighlighter
    from qtpie.highlighters.javascript import JavaScriptHighlighter
    from qtpie.highlighters.json import JsonHighlighter
    from qtpie.highlighters.xml import XmlHighlighter
    from qtpie.highlighters.yaml import YamlHighlighter

    # JSON
    register_highlighter("application/json", JsonHighlighter)
    register_highlighter("text/json", JsonHighlighter)

    # HTML
    register_highlighter("text/html", HtmlHighlighter)
    register_highlighter("application/xhtml+xml", HtmlHighlighter)

    # XML
    register_highlighter("application/xml", XmlHighlighter)
    register_highlighter("text/xml", XmlHighlighter)

    # YAML
    register_highlighter("application/yaml", YamlHighlighter)
    register_highlighter("application/x-yaml", YamlHighlighter)
    register_highlighter("text/yaml", YamlHighlighter)
    register_highlighter("text/x-yaml", YamlHighlighter)

    # CSS/SCSS
    register_highlighter("text/css", CssHighlighter)
    register_highlighter("text/x-scss", CssHighlighter)
    register_highlighter("text/x-sass", CssHighlighter)

    # JavaScript/TypeScript
    register_highlighter("application/javascript", JavaScriptHighlighter)
    register_highlighter("text/javascript", JavaScriptHighlighter)
    register_highlighter("application/x-javascript", JavaScriptHighlighter)
    register_highlighter("application/typescript", JavaScriptHighlighter)
    register_highlighter("text/typescript", JavaScriptHighlighter)

    # Python
    from qtpie.highlighters.python import PythonHighlighter

    register_highlighter("text/x-python", PythonHighlighter)
    register_highlighter("application/x-python", PythonHighlighter)


# Register defaults on import
_register_default_highlighters()
