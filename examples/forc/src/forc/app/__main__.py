from forc.app.application import ForcApp
from forc.app.qrc_resources import qt_resource_data
from qtpie import entrypoint

# TODO: have a toggle for using the QRC resource when we run/build in like a production mode
# @entrypoint(stylesheet=":/styles.qss"

_qrc = qt_resource_data  # Prevent unused import from being removed


# Hmm, idea... can we define different stylesheets for light/dark mode and have a toggle in the app to switch?
@entrypoint(
    stylesheet="resources/styles/styles.scss",
    scss_output="resources/styles.qss",
    watch_stylesheet=True,
)
def main():
    return ForcApp()
