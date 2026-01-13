from forc.app.application import ForcApp
from qtpie import entrypoint

# TODO: have a toggle for using the QRC resource when we run/build in like a production mode
# @entrypoint(stylesheet=":/styles.qss"


# Hmm, idea... can we define different stylesheets for light/dark mode and have a toggle in the app to switch?
@entrypoint(stylesheet="resources/styles/styles.scss", scss_output="resources/styles.qss", watch_stylesheet=True, light_mode=True)
def main():
    return ForcApp()
