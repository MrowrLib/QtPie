from typing import override

from PySide6.QtGui import QFontMetrics, Qt
from PySide6.QtWidgets import QPlainTextEdit

from qtpie import widget
from qtpie.core import Widget


@widget(layout="none", classes=["text-edit"])
class AutoHeightPlainTextEdit(QPlainTextEdit, Widget):
    @override
    def setup(self) -> None:
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.document().setDocumentMargin(0)
        self.document().contentsChanged.connect(self._adjust_height)
        self._adjust_height()

    def _adjust_height(self) -> None:
        text = self.toPlainText()
        font_metrics = QFontMetrics(self.font())
        line_height = font_metrics.height()
        visible_lines = text.count("\n") + 1 if text else 1
        margins = self.contentsMargins().top() + self.contentsMargins().bottom()
        height_for_text = (visible_lines * line_height) + margins
        self.setFixedHeight(height_for_text)
