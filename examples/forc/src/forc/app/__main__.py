from forc.app.application import ForcApp
from qtpie import entrypoint

# TODO: have a toggle for using the QRC resource when we run/build in like a production mode
# @entrypoint(stylesheet=":/styles.qss"


# TODO: light_mode=True isn't working? fix? to make sure it can work!
@entrypoint(stylesheet="resources/styles/styles.scss", scss_output="resources/styles.qss", watch_stylesheet=True, light_mode=True)
def main():
    return ForcApp()
