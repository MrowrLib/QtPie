from qtpy.QtWidgets import QLabel, QWidget

from qtpie import entrypoint, make, widget
from qtpie.widgets import FilterableDropdownWithDescription


@entrypoint(title="FilterableDropdownWithDescription Demo", size=(500, 350))
@widget
class Demo(QWidget):
    instructions: QLabel = make(QLabel, "Type to filter by name or description, arrow keys to navigate, Enter to select:")
    dropdown: FilterableDropdownWithDescription = make(FilterableDropdownWithDescription)
    selected_label: QLabel = make(QLabel, "Selected: (none)")

    def setup(self) -> None:
        self.dropdown.set_placeholder_text("Search for a user...")
        self.dropdown.set_items(
            [
                ("alice", "Alice Johnson - Engineering Lead"),
                ("bob", "Bob Smith - Product Manager"),
                ("charlie", "Charlie Brown - Designer"),
                ("diana", "Diana Prince - Security Analyst"),
                ("eve", "Eve Wilson - Data Scientist"),
                ("frank", "Frank Miller - DevOps Engineer"),
                ("grace", "Grace Hopper - Backend Developer"),
                ("henry", "Henry Ford - Frontend Developer"),
                ("iris", "Iris West - QA Engineer"),
                ("jack", "Jack Ryan - Solutions Architect"),
                ("kate", "Kate Bishop - Mobile Developer"),
                ("leo", "Leo Messi - Platform Engineer"),
                ("maya", "Maya Angelou - Technical Writer"),
                ("nick", "Nick Fury - Security Director"),
                ("olivia", "Olivia Pope - Project Manager"),
            ]
        )
        self.dropdown.item_selected.connect(self._on_item_selected)

    def _on_item_selected(self, text: str) -> None:
        self.selected_label.setText(f"Selected: {text}")
