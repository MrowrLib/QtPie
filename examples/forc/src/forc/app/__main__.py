import logging
import os

os.environ["QTPIE_DEBUG"] = "1"  # Must be set before importing qtpie

# Set up file logging for debug output
logging.basicConfig(
    level=logging.DEBUG,
    format="%(name)s: %(message)s",
    handlers=[
        logging.FileHandler("forc_debug.log", mode="w"),
    ],
)

from forc.app.application import ForcApp  # noqa: E402
from forc.app.qrc_resources import qt_resource_data  # noqa: E402
from qtpie import entrypoint  # noqa: E402

# TODO: have a toggle for using the QRC resource when we run/build in like a production mode
# @entrypoint(stylesheet=":/styles.qss"

_qrc = qt_resource_data  # Prevent unused import from being removed


@entrypoint(
    themes="resources/themes",
    theme="dark",
    watch_themes=True,
)
def main():
    return ForcApp()
