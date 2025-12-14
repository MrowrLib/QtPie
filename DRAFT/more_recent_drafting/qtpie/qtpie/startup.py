import asyncio

import qasync
from qtpy.QtWidgets import QApplication

from qtpie.files import read_file
from qtpie.styles.stylesheet import StyleConfiguration, watch_qss

app_close_event = asyncio.Event()


def run_app(
    app: QApplication,
    styles: StyleConfiguration | None = None,
) -> None:
    if styles:
        if styles.watch:
            watch_qss(app, config=styles)
        else:
            if styles.qss_resource_path:
                app.setStyleSheet(read_file(styles.qss_resource_path))

    app.aboutToQuit.connect(app_close_event.set)
    event_loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(event_loop)
    with event_loop:
        event_loop.run_until_complete(app_close_event.wait())


#
