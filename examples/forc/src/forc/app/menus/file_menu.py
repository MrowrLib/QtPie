from qtpy.QtCore import Signal
from qtpy.QtGui import QAction

from qtpie import Menu, menu, new


@menu(title="File")
class FileMenu(Menu):
    on_quit = Signal()

    quit: QAction = new("&Quit", shortcut="Ctrl+Q", triggered="on_quit")
