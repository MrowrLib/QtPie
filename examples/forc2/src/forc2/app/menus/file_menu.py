from qtpy.QtGui import QAction

from qtpie import Menu, menu, new


@menu(title="File")
class FileMenu(Menu):
    ### Actions ###
    load_workspace: QAction = new("&Load Workspace...", shortcut="Ctrl+O", triggered="on_choose_workspace")
    save: QAction = new("&Save", shortcut="Ctrl+S", triggered="on_save")
    quit: QAction = new("&Quit", shortcut="Ctrl+Q", triggered="on_quit")
