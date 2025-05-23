from dataclasses import dataclass


@dataclass
class QtPieConfiguration:
    all_decorators_dataclass_transformer: bool = True
    widget_decorator_dataclass_transformer: bool | None = None


_qtpie_configuration = QtPieConfiguration()


def qtpie_configuration() -> QtPieConfiguration:
    """Get the global QtPie configuration singleton."""
    return _qtpie_configuration


def configure_qtpie(
    *,
    widget_decorator_dataclass_transformer: bool | None = None,
    all_decorators_dataclass_transformer: bool | None = None,
) -> None:
    """Configure global QtPie settings."""
    config = qtpie_configuration()
    if widget_decorator_dataclass_transformer is not None:
        config.widget_decorator_dataclass_transformer = widget_decorator_dataclass_transformer
    if all_decorators_dataclass_transformer is not None:
        config.all_decorators_dataclass_transformer = all_decorators_dataclass_transformer
