from assertpy import assert_that

from qtpie.config import QtPieConfiguration, configure_qtpie, qtpie_configuration


class TestQtPieConfiguration:
    def test_defaults(self) -> None:
        """Test that QtPieConfiguration has correct default values."""
        config = QtPieConfiguration()

        assert_that(config.all_decorators_dataclass_transformer).is_true()
        assert config.widget_decorator_dataclass_transformer is None


class TestConfigureQtPie:
    def setup_method(self) -> None:
        """Reset configuration before each test."""
        qtpie_configuration().widget_decorator_dataclass_transformer = None
        qtpie_configuration().all_decorators_dataclass_transformer = True

    def test_global_config_defaults(self) -> None:
        """Test that global configuration has correct default values."""
        assert qtpie_configuration().widget_decorator_dataclass_transformer is None
        assert_that(qtpie_configuration().all_decorators_dataclass_transformer).is_true()

    def test_partial_update_widget_decorator(self) -> None:
        """Test updating only widget_decorator_dataclass_transformer."""
        configure_qtpie(widget_decorator_dataclass_transformer=False)

        assert_that(qtpie_configuration().widget_decorator_dataclass_transformer).is_false()
        assert_that(qtpie_configuration().all_decorators_dataclass_transformer).is_true()

    def test_partial_update_all_decorators(self) -> None:
        """Test updating only all_decorators_dataclass_transformer."""
        configure_qtpie(all_decorators_dataclass_transformer=False)

        assert qtpie_configuration().widget_decorator_dataclass_transformer is None
        assert_that(qtpie_configuration().all_decorators_dataclass_transformer).is_false()

    def test_multiple_calls(self) -> None:
        """Test multiple calls to configure_qtpie with different options."""
        configure_qtpie(widget_decorator_dataclass_transformer=False)
        assert_that(qtpie_configuration().widget_decorator_dataclass_transformer).is_false()
        assert_that(qtpie_configuration().all_decorators_dataclass_transformer).is_true()

        configure_qtpie(all_decorators_dataclass_transformer=False)
        assert_that(qtpie_configuration().widget_decorator_dataclass_transformer).is_false()
        assert_that(qtpie_configuration().all_decorators_dataclass_transformer).is_false()

    def test_update_both_options(self) -> None:
        """Test updating both options in a single call."""
        configure_qtpie(widget_decorator_dataclass_transformer=False, all_decorators_dataclass_transformer=False)

        assert_that(qtpie_configuration().widget_decorator_dataclass_transformer).is_false()
        assert_that(qtpie_configuration().all_decorators_dataclass_transformer).is_false()

    def test_none_values_ignored(self) -> None:
        """Test that None values don't change existing configuration."""
        configure_qtpie(widget_decorator_dataclass_transformer=False)
        configure_qtpie(widget_decorator_dataclass_transformer=None, all_decorators_dataclass_transformer=False)

        assert_that(qtpie_configuration().widget_decorator_dataclass_transformer).is_false()
        assert_that(qtpie_configuration().all_decorators_dataclass_transformer).is_false()

    def test_widget_override_when_all_false(self) -> None:
        """Test that widget=True overrides all_decorators=False."""
        configure_qtpie(all_decorators_dataclass_transformer=False, widget_decorator_dataclass_transformer=True)

        assert_that(qtpie_configuration().widget_decorator_dataclass_transformer).is_true()
        assert_that(qtpie_configuration().all_decorators_dataclass_transformer).is_false()

    def test_widget_override_when_all_true(self) -> None:
        """Test that widget=False overrides all_decorators=True."""
        configure_qtpie(all_decorators_dataclass_transformer=True, widget_decorator_dataclass_transformer=False)

        assert_that(qtpie_configuration().widget_decorator_dataclass_transformer).is_false()
        assert_that(qtpie_configuration().all_decorators_dataclass_transformer).is_true()

    def test_reset_widget_to_none(self) -> None:
        """Test that setting widget back to None removes the override."""
        configure_qtpie(widget_decorator_dataclass_transformer=False)
        assert_that(qtpie_configuration().widget_decorator_dataclass_transformer).is_false()

        # This should be a no-op since we're passing None
        configure_qtpie(widget_decorator_dataclass_transformer=None)
        assert_that(qtpie_configuration().widget_decorator_dataclass_transformer).is_false()
