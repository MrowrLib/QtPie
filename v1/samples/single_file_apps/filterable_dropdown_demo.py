from qtpy.QtWidgets import QLabel, QWidget

from qtpie import entrypoint, make, widget
from qtpie.widgets import FilterableDropdown


@entrypoint(title="FilterableDropdown Demo", size=(400, 300))
@widget
class Demo(QWidget):
    instructions: QLabel = make(QLabel, "Type to filter, use arrow keys to navigate, Enter to select:")
    dropdown: FilterableDropdown = make(FilterableDropdown)
    selected_label: QLabel = make(QLabel, "Selected: (none)")

    def setup(self) -> None:
        self.dropdown.set_placeholder_text("Search for a fruit...")
        self.dropdown.set_items(
            [
                "Apple",
                "Apricot",
                "Avocado",
                "Banana",
                "Blackberry",
                "Blueberry",
                "Cherry",
                "Coconut",
                "Cranberry",
                "Date",
                "Dragon Fruit",
                "Elderberry",
                "Fig",
                "Grape",
                "Grapefruit",
                "Guava",
                "Honeydew",
                "Kiwi",
                "Lemon",
                "Lime",
                "Lychee",
                "Mango",
                "Melon",
                "Nectarine",
                "Orange",
                "Papaya",
                "Passion Fruit",
                "Peach",
                "Pear",
                "Pineapple",
                "Plum",
                "Pomegranate",
                "Raspberry",
                "Strawberry",
                "Tangerine",
                "Watermelon",
            ]
        )
        self.dropdown.item_selected.connect(self._on_item_selected)

    def _on_item_selected(self, text: str) -> None:
        self.selected_label.setText(f"Selected: {text}")
