from qtpy.QtWidgets import QLabel, QSizePolicy, QSpacerItem

from qtpie import Widget, new, widget


@widget(layout="horizontal")
class ExampleComboBoxEmbedWidget(Widget):
    """
    This is an example of embedding a QComboBox inside a QtPie widget.
    """

    qlabel1: QLabel = new("Label 1")
    qlabel2: QLabel = new("Label 2")


@widget(layout="horizontal")
class EnvironmentSelectorWidget(Widget):
    """
    This will show a dropdown to select the environment for the current request
    and buttons for adding and removing environments.
    """

    # Let's just use QLabel placeholders for everything first.
    # Because even things like a "simple QComboBox" actually requires
    # knowing a good bit of things about how QComboBox works in QtPie, for example.

    environment_dropdown: QLabel = new("Environment Dropdown Placeholder")
    add_button: QLabel = new("[+]")
    remove_button: QLabel = new("[-]")
    spacer: QSpacerItem = new(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
