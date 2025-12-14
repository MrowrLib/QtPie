import asyncio

import qasync
from PySide6.QtWidgets import QApplication

from qtpie.files import read_file
from qtpie.styles import watch_qss

app_close_event = asyncio.Event()


def run_app(
    app: QApplication,
    development_mode: bool = False,
    styles_qss_resource: str | None = None,
    styles_qss_local_path: str | None = None,
    main_scss_local_path: str | None = None,
) -> None:
    if development_mode:
        if main_scss_local_path and styles_qss_local_path:
            watch_qss(app, main_scss=main_scss_local_path, out_qss=styles_qss_local_path)
    else:
        if styles_qss_resource:
            app.setStyleSheet(read_file(styles_qss_resource))

    app.aboutToQuit.connect(app_close_event.set)
    event_loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(event_loop)
    with event_loop:
        event_loop.run_until_complete(app_close_event.wait())
