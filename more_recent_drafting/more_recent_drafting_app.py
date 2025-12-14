from dataclasses import dataclass

from qtpie import ModelWidget, Widget, make, make_widget, register_binding, widget
from qtpie.app import App
from qtpy.QtCore import Qt, Signal
from qtpy.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QWidget,
)

app = App(name="Single File App", version="0.1.0", dark_mode=True)
app.set_styles(watch=True, scss_path="./styles.scss", qss_path="./styles.qss")


# Custom widget with a signal - a labeled input field
class LabeledInput(QWidget):
    """A simple labeled text input widget with its own signal."""

    textChanged = Signal(str)

    def __init__(self, label: str = "Label:", parent: QWidget | None = None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel(label)
        self._input = QLineEdit()

        layout.addWidget(self._label)
        layout.addWidget(self._input)

        # Forward the inner signal
        self._input.textChanged.connect(self.textChanged.emit)

    def text(self) -> str:
        return self._input.text()

    def setText(self, value: str) -> None:
        self._input.setText(value)


# Register bindings
register_binding(
    QSlider,
    "value",
    setter=lambda w, v: w.setValue(int(v)),
    getter=lambda w: w.value(),
    signal="valueChanged",
    default=True,
)

register_binding(
    LabeledInput,
    "text",
    setter=lambda w, v: w.setText(str(v)),
    getter=lambda w: w.text(),
    signal="textChanged",
)


@dataclass
class Location:
    city: str = ""
    country: str = ""


@dataclass
class Habitat:
    name: str = ""
    climate: str = ""
    location: Location | None = None

    def __post_init__(self):
        if self.location is None:
            self.location = Location()


@dataclass
class Animal:
    name: str
    species: str
    nickname: str = ""
    age: int = 5
    habitat: Habitat | None = None

    def __post_init__(self):
        if self.habitat is None:
            self.habitat = Habitat()


# Pre-defined habitats for testing
HABITATS: dict[str, Habitat | None] = {
    "(No Habitat)": None,
    "Savanna": Habitat(
        name="Savanna",
        climate="Tropical",
        location=Location(city="Nairobi", country="Kenya"),
    ),
    "Arctic": Habitat(
        name="Arctic Tundra",
        climate="Polar",
        location=Location(city="Svalbard", country="Norway"),
    ),
    "Rainforest": Habitat(
        name="Amazon Rainforest",
        climate="Humid",
        location=Location(city="Manaus", country="Brazil"),
    ),
    "Desert (no location)": Habitat(
        name="Sahara Desert",
        climate="Arid",
        location=None,
    ),
}


# Regular widget - using signal connection in make()
@widget(name="CoolWidget", classes=["qss-styleable-class"], layout="horizontal")
class CoolWidget(QWidget, Widget):
    lbl_cool: QLabel = make(QLabel, "This is a cool widget!")
    btn_cool: QPushButton = make_widget(
        QPushButton,
        ["class-one", "class-two"],
        "Cool Button",
        clicked="on_cool_button_clicked",
    )

    def on_cool_button_clicked(self) -> None:
        print("Cool button was clicked! using the cool new syntax!")


@widget
class AnimalWidget(QWidget, ModelWidget[Animal]):
    # Show a cool widget
    cool_widget: CoolWidget = make(CoolWidget)  # <--- automatically added to layout!

    # Top-level bindings
    txt_animal_name: QLineEdit = make(QLineEdit, bind="name", placeholderText="Name")
    txt_animal_species: QLineEdit = make(
        QLineEdit, bind="species", placeholderText="Species"
    )
    txt_nickname: LabeledInput = make(LabeledInput, "Nickname:", bind="nickname")
    slider_age: QSlider = make(
        QSlider,
        Qt.Orientation.Horizontal,
        bind="age",
        minimum=0,
        maximum=20,
        minimumWidth=200,
        valueChanged="on_age_changed",
    )

    def on_age_changed(self, value: int) -> None:
        print(f"Age changed to: {value}")

    # Habitat selector (not bound - manual control, signal connected via make())
    lbl_habitat_selector: QLabel = make(QLabel, "Select Habitat:")
    cmb_habitat: QComboBox = make(QComboBox, currentTextChanged="on_habitat_changed")

    # Nested bindings - one level deep (with optional chaining)
    txt_habitat_name: QLineEdit = make(
        QLineEdit, bind="habitat?.name", placeholderText="Habitat Name"
    )
    txt_habitat_climate: QLineEdit = make(
        QLineEdit, bind="habitat?.climate", placeholderText="Climate"
    )
    # Nested bindings - two levels deep (with optional chaining)
    txt_location_city: QLineEdit = make(
        QLineEdit, bind="habitat?.location?.city", placeholderText="City"
    )
    txt_location_country: QLineEdit = make(
        QLineEdit, bind="habitat?.location?.country", placeholderText="Country"
    )

    btn_print_model_values: QPushButton = make(
        QPushButton, "Print Model Values", clicked="on_print_model_values_clicked"
    )

    def setup(self) -> None:
        # Populate habitat dropdown
        for habitat_name in HABITATS:
            self.cmb_habitat.addItem(habitat_name)

    def on_habitat_changed(self, habitat_key: str) -> None:
        """Change the animal's habitat when dropdown changes."""
        if self.model:
            new_habitat = HABITATS.get(habitat_key)
            # Update the model's habitat
            self.model.value.habitat = new_habitat
            # Notify the proxy that habitat changed
            self.model.proxy.observable(object, "habitat").set(new_habitat)
            print(f"Habitat changed to: {habitat_key}")

    def on_print_model_values_clicked(self) -> None:
        if self.model:
            animal = self.model.value
            nickname = f' "{animal.nickname}"' if animal.nickname else ""
            habitat = animal.habitat
            print("=" * 50)
            print(
                f"Animal: {animal.name}{nickname} the {animal.species}, Age: {animal.age}"
            )
            if habitat:
                print(f"Habitat: {habitat.name} ({habitat.climate})")
                if habitat.location:
                    print(
                        f"Location: {habitat.location.city}, {habitat.location.country}"
                    )
                else:
                    print("Location: (none)")
            else:
                print("Habitat: (none)")
            print("=" * 50)
        else:
            print("No model is set.")


def main():
    window = AnimalWidget()
    window.set_model(
        Animal(
            name="Leo",
            species="Lion",
            habitat=HABITATS["Savanna"],
        )
    )
    # Set dropdown to match initial habitat
    window.cmb_habitat.setCurrentText("Savanna")
    window.show()
    app.run()


if __name__ == "__main__":
    main()
