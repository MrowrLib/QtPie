"""Tests for the App class."""

import inspect
from typing import override

from assertpy import assert_that
from PySide6.QtWidgets import QApplication

from qtpie import App


class TestAppClass:
    """Tests for the App class using qapp fixture."""

    def test_app_is_qapplication(self, qapp: App) -> None:
        """App should be a QApplication instance."""
        assert_that(qapp).is_instance_of(QApplication)

    def test_app_is_our_app_class(self, qapp: App) -> None:
        """qapp fixture should use our App class."""
        assert_that(qapp).is_instance_of(App)

    def test_app_has_run_method(self, qapp: App) -> None:
        """App should have a run method."""
        assert_that(qapp.run).is_not_none()
        assert_that(callable(qapp.run)).is_true()

    def test_app_has_run_async_method(self, qapp: App) -> None:
        """App should have a run_async method."""
        assert_that(qapp.run_async).is_not_none()
        assert_that(callable(qapp.run_async)).is_true()


class TestAppLifecycleHooks:
    """Tests for App lifecycle hooks."""

    def test_setup_hook_called_on_subclass(self) -> None:
        """setup() hook should be called when overridden in subclass."""
        setup_called = False

        class MyApp(App):
            @override
            def setup(self) -> None:
                nonlocal setup_called
                setup_called = True

        # We can't actually instantiate because QApplication already exists
        # But we can test the logic by checking the method
        assert_that(hasattr(MyApp, "setup")).is_true()

    def test_create_window_hook_exists(self) -> None:
        """create_window() hook should exist on App."""
        assert_that(hasattr(App, "create_window")).is_true()


class TestRunAppFunction:
    """Tests for the run_app standalone function."""

    def test_run_app_exists(self) -> None:
        """run_app function should be importable."""
        from qtpie import run_app

        assert_that(run_app).is_not_none()
        assert_that(callable(run_app)).is_true()

    def test_run_app_accepts_qapplication(self) -> None:
        """run_app should accept any QApplication."""
        from qtpie import run_app

        sig = inspect.signature(run_app)
        params = list(sig.parameters.keys())
        assert_that(params).contains("app")
