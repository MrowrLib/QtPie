"""Translatable marker for declarative translations."""

from contextvars import ContextVar
from dataclasses import dataclass

from qtpy.QtCore import QCoreApplication

# Context variable set by @widget decorator
_translation_context: ContextVar[str] = ContextVar("translation_context", default="")

# Flag to use in-memory store instead of QTranslator
_use_memory_store: bool = False


def enable_memory_store(enabled: bool = True) -> None:
    """Enable or disable in-memory translation store.

    When enabled, translations are looked up from the in-memory store
    (loaded from YAML) instead of Qt's QTranslator. This is used for
    development hot-reload.
    """
    global _use_memory_store
    _use_memory_store = enabled


def is_memory_store_enabled() -> bool:
    """Check if in-memory store is enabled."""
    return _use_memory_store


@dataclass(frozen=True)
class Translatable:
    """Marker for a string that should be translated.

    Used with t("text") syntax. The actual translation happens
    when the new() factory runs, using the context set by @widget.

    For plurals, call the Translatable with a count:
        t("%n file(s)")(5)  # Returns "5 files"
    """

    text: str
    context: str | None = None

    def __call__(self, n: int, widget_context: str | None = None) -> str:
        """Resolve with plural count.

        Args:
            n: The count for plural form selection.
            widget_context: Optional translation context override.

        Returns:
            The translated plural string with %n replaced by count.
        """
        ctx = widget_context or _translation_context.get() or "@default"

        if _use_memory_store:
            from qtpie.translations.store import lookup_plural

            return lookup_plural(ctx, self.text, n, self.context)

        # Use Qt's QTranslator (production mode with .qm files)
        return QCoreApplication.translate(ctx, self.text, self.context, n)

    def resolve(self, widget_context: str | None = None) -> str:
        """Resolve this translatable to actual translated text.

        Args:
            widget_context: The translation context (class name). If None,
                     uses the context from the current widget processing.

        Returns:
            The translated string, or original if no translation found.
        """
        ctx = widget_context or _translation_context.get() or "@default"

        if _use_memory_store:
            # Use in-memory store (dev mode with hot-reload)
            from qtpie.translations.store import lookup

            return lookup(ctx, self.text, self.context)

        # Use Qt's QTranslator (production mode with .qm files)
        return QCoreApplication.translate(ctx, self.text, self.context)


def t(text: str, *, context: str | None = None) -> Translatable:
    """Create a Translatable marker.

    This is the primary way to mark strings for translation in QtPie.

    Args:
        text: The source text to translate.
        context: Optional disambiguation context (e.g., "menu" vs "status").
                 Use this when the same source text has different meanings.

    Returns:
        Translatable marker that gets resolved later by new().

    Examples:
        # Basic usage
        _label: QLabel = new(t("Hello"))

        # With disambiguation
        _menu_open: QAction = new(t("Open", context="menu"))
        _status_open: QLabel = new(t("Open", context="status"))

        # Plurals (call with count)
        label.setText(t("%n file(s)")(5))  # "5 files"
    """
    return Translatable(text=text, context=context)


def set_translation_context(context: str) -> None:
    """Set the current translation context (called by @widget)."""
    _translation_context.set(context)


def get_translation_context() -> str:
    """Get the current translation context."""
    return _translation_context.get()


def resolve_translatable(value: object) -> object:
    """Resolve a value if it's Translatable, otherwise return as-is."""
    if isinstance(value, Translatable):
        return value.resolve()
    return value
