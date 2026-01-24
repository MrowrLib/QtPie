import logging
import os

os.environ["QTPIE_DEBUG"] = "1"

logging.basicConfig(level=logging.DEBUG, format="%(name)s: %(message)s", handlers=[logging.FileHandler("forc_debug.log", mode="w"), logging.StreamHandler()])

from forc2.app.application import Application  # noqa: E402
from forc2.app.qrc_resources import qt_resource_data  # noqa: E402
from qtpie import entrypoint  # noqa: E402

# TODO: have a toggle for using the QRC resource when we run/build in like a production mode
# @entrypoint(stylesheet=":/styles.qss"

_qrc = qt_resource_data  # Prevent unused import from being removed


@entrypoint(
    themes="resources/themes",
    theme="dark",
    watch_themes=True,
    themes_output="build/themes",
)
def main():
    return Application()
