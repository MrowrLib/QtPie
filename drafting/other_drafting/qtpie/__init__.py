"""
qtpie: A declarative DSL for Qt widgets in Python

This package provides a set of decorators and helpers for creating Qt widgets
in a declarative style, inspired by Ruby DSLs and Rails-style conventions.
"""

from mrowr.make import make, make_later
from qtpie.action import action
from qtpie.bindings import bind
from qtpie.core import Action, ModelWidget, Widget, WidgetModel
from qtpie.make_widget import make_form_row, make_form_row_widget, make_widget
from qtpie.menu import menu
from qtpie.run_app import run_app
from qtpie.styles import QtStyleClass, watch_qss
from qtpie.widget import widget
from qtpie.window import window

__all__ = [
    "widget",
    "window",
    "menu",
    "action",
    "make",
    "make_later",
    "make_widget",
    "Widget",
    "Action",
    "run_app",
    "watch_qss",
    "make_form_row",
    "make_form_row_widget",
    "bind",
    "ModelWidget",
    "WidgetModel",
    "QtStyleClass",
]
