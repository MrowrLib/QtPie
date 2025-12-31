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

    Used with tr["text"] syntax. The actual translation happens
    when the make() factory runs, using the context set by @widget.

    For plurals, call the Translatable with a count:
        tr["%n file(s)"](5)  # Returns "5 files"
    """

    text: str
    disambiguation: str | None = None

    def __call__(self, n: int, context: str | None = None) -> str:
        """Resolve with plural count.

        Args:
            n: The count for plural form selection.
            context: Optional translation context override.

        Returns:
            The translated plural string with %n replaced by count.
        """
        ctx = context or _translation_context.get()
        if not ctx:
            return self.text.replace("%n", str(n))

        if _use_memory_store:
            from qtpie.translations.store import lookup_plural

            return lookup_plural(ctx, self.text, n, self.disambiguation)

        # Use Qt's QTranslator (production mode with .qm files)
        return QCoreApplication.translate(ctx, self.text, self.disambiguation, n)

    def resolve(self, context: str | None = None) -> str:
        """Resolve this translatable to actual translated text.

        Args:
            context: The translation context (class name). If None,
                     uses the context from the current widget processing.

        Returns:
            The translated string, or original if no translation found.
        """
        ctx = context or _translation_context.get()
        if not ctx:
            return self.text

        if _use_memory_store:
            # Use in-memory store (dev mode with hot-reload)
            from qtpie.translations.store import lookup

            return lookup(ctx, self.text, self.disambiguation)

        # Use Qt's QTranslator (production mode with .qm files)
        return QCoreApplication.translate(ctx, self.text, self.disambiguation)


class _TrAccessor:
    """Accessor for tr["text"] syntax.

    Usage:
        tr["Hello"]                    # Basic
        tr["Hello", "greeting"]        # With disambiguation
        tr["Open", "menu"]             # Same source, different context
    """

    def __getitem__(self, key: str | tuple[str, str]) -> Translatable:
        """Create a Translatable marker.

        Args:
            key: Either a string, or tuple of (text, disambiguation)

        Returns:
            Translatable marker that gets resolved later.
        """
        if isinstance(key, tuple):
            text, disambiguation = key
            return Translatable(text=text, disambiguation=disambiguation)
        return Translatable(text=key)


# The global tr accessor
tr = _TrAccessor()


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
