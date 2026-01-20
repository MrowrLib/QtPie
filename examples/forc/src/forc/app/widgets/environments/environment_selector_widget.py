from qtpy.QtWidgets import QComboBox, QLabel, QSizePolicy, QToolButton

from qtpie import Widget, new, widget


@widget(layout="horizontal")
class EnvironmentSelectorWidget(Widget):
    ### Widgets ###
    label: QLabel = new("Environment:")
    environments_chooser: QComboBox = new(
        bind="workspace?.environments",
        format="{name}",
        selectedItem="workspace?.active_environment",
        sizePolicy=QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed),
    )
    settings_button: QToolButton = new(icon=":/settings-dark.svg", clicked="_on_test_clicked")

    ### Methods ###
    def _on_test_clicked(self) -> None:
        print("Test button clicked!")
