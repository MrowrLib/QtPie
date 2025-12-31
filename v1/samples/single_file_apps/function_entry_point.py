from qtpy.QtWidgets import QLabel

from qtpie import entrypoint


@entrypoint
def main():
    return QLabel("Hello, World!")
