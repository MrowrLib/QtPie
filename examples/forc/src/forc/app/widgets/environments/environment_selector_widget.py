from qtpy.QtWidgets import QComboBox, QLabel, QSizePolicy, QToolButton

from qtpie import Variable, Widget, new, widget


@widget(layout="horizontal")
class EnvironmentSelectorWidget(Widget):
    ### Variables ###
    test_list: Variable[list[str]] = new(["Env 1", "Env 2", "Env 3"])

    ### Widgets ###
    label: QLabel = new("Environment:")
    environments_chooser: QComboBox = new(
        bind="test_list",
        sizePolicy=QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed),
    )
    settings_button: QToolButton = new(icon=":/settings-dark.svg", clicked="_on_test_clicked")

    ### Methods ###
    def _on_test_clicked(self) -> None:
        print("Test button clicked!")
