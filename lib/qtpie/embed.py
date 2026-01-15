"""Embed configuration for embedding widgets in model views."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EmbedConfig:
    """Configuration for embedding a Widget inside a model view (QListView, QTableView, QTreeView).

    Stores the widget class and kwargs to apply when creating widget instances.
    The kwargs follow the same patterns as new() - signal connections, variable bindings, etc.
    """

    widget_class: type[Any]
    kwargs: dict[str, Any] = field(default_factory=dict[str, Any])
    column_name: str | None = None  # Override column header for QTableView widget columns


def embed(widget_class: type[Any], *, column_name: str | None = None, **kwargs: Any) -> EmbedConfig:
    """Configure a widget to be embedded in a model view.

    Use this to specify bindings, signal connections, and variable pass-through
    when embedding a Widget subclass in QListView, QTableView, or QTreeView.

    Examples:
        # Simple - just the class (no embed() needed)
        _list: QListView = new(bind="_dogs", widget=DogCard)

        # With row index injection
        _list: QListView = new(
            bind="_dogs",
            widget=embed(DogCard, selectedIndex="row"),
        )

        # With signal connection to parent
        _list: QListView = new(
            bind="_dogs",
            widget=embed(DogCard, on_delete="remove_dog"),
        )

        # With parent Variable pass-through
        _list: QListView = new(
            bind="_dogs",
            widget=embed(DogCard, show_details="_show_details"),
        )

        # In QTableView columns with custom column header
        _table: QTableView = new(
            bind="_dogs",
            columns=["name", "age", embed(DogActions, column_name="Actions", on_delete="remove_dog")],
        )

    Args:
        widget_class: The Widget subclass to embed. Can be Widget[T] for record binding
                      or plain Widget with bare Variables for injection.
        column_name: Override column header for QTableView widget columns. If not specified,
                     uses the widget's @widget(title=...) or falls back to empty string.
        **kwargs: Same kwargs as new() - signal connections, variable bindings, etc.
                  Plus special kwargs for injection:
                  - selectedItem="var": Bind the row's item to a bare Variable
                  - selectedIndex="var": Bind the row index to a bare Variable (QListView/QTreeView)
                  - selectedRow="var": Bind the row index to a bare Variable (QTableView)

    Returns:
        EmbedConfig containing the widget class, kwargs, and column_name.
    """
    return EmbedConfig(widget_class=widget_class, kwargs=kwargs, column_name=column_name)
