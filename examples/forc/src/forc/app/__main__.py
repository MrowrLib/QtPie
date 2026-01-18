import os

os.environ["QTPIE_DEBUG"] = "1"  # Must be set before importing qtpie

from forc.app.application import ForcApp
from forc.app.qrc_resources import qt_resource_data
from qtpie import entrypoint

# TODO: have a toggle for using the QRC resource when we run/build in like a production mode
# @entrypoint(stylesheet=":/styles.qss"

_qrc = qt_resource_data  # Prevent unused import from being removed


@entrypoint(
    # themes="resources/themes",
    # theme="dark",
    # watch_themes=True,
)
def main():
    return ForcApp()
