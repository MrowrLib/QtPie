from qtpie import entry_point
from qtpy.QtWidgets import QLabel


@entry_point
def main():
    return QLabel("Hello, World!")
