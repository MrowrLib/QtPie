from forc.app.application import ForcApp
from qtpie import entrypoint


@entrypoint
def main():
    return ForcApp()
