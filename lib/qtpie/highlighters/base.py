"""Base class for syntax highlighters."""

import re
from dataclasses import dataclass
from typing import ClassVar, override

from qtpy.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat, QTextDocument


@dataclass
class HighlightRule:
    """A single syntax highlighting rule."""

    pattern: re.Pattern[str]
    format: QTextCharFormat


def make_format(
    *,
    color: str | QColor | None = None,
    bold: bool = False,
    italic: bool = False,
    underline: bool = False,
) -> QTextCharFormat:
    """Create a QTextCharFormat with the given style."""
    fmt = QTextCharFormat()
    if color is not None:
        if isinstance(color, str):
            color = QColor(color)
        fmt.setForeground(color)
    if bold:
        fmt.setFontWeight(QFont.Weight.Bold)
    if italic:
        fmt.setFontItalic(True)
    if underline:
        fmt.setFontUnderline(True)
    return fmt


@dataclass
class MultiLineRule:
    """A rule for multi-line constructs like block comments or strings."""

    start_pattern: re.Pattern[str]
    end_pattern: re.Pattern[str]
    format: QTextCharFormat
    state: int  # Unique state ID for this multi-line rule


class SyntaxHighlighter(QSyntaxHighlighter):
    """Base class for declarative syntax highlighters.

    Subclass this and define `rules` and optionally `multiline_rules` as class variables.

    Example:
        class PythonHighlighter(SyntaxHighlighter):
            rules: ClassVar[list[HighlightRule]] = [
                HighlightRule(
                    pattern=re.compile(r"\\b(def|class|return|if|else)\\b"),
                    format=make_format(color="#cc7832", bold=True),
                ),
            ]
    """

    rules: ClassVar[list[HighlightRule]] = []
    multiline_rules: ClassVar[list[MultiLineRule]] = []

    def __init__(self, document: QTextDocument) -> None:
        super().__init__(document)

    @override
    def highlightBlock(self, text: str) -> None:
        """Apply highlighting rules to a block of text."""
        # Apply single-line rules
        for rule in self.rules:
            for match in rule.pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), rule.format)

        # Only set block state for multi-line rules
        if self.multiline_rules:
            self.setCurrentBlockState(0)
            for ml_rule in self.multiline_rules:
                self._apply_multiline_rule(text, ml_rule)

    def _apply_multiline_rule(self, text: str, rule: MultiLineRule) -> None:
        """Apply a multi-line highlighting rule."""
        start_index = 0

        # If we're continuing from a previous block in this state
        if self.previousBlockState() != rule.state:
            match = rule.start_pattern.search(text)
            start_index = match.start() if match else -1
        else:
            start_index = 0

        while start_index >= 0:
            end_match = rule.end_pattern.search(text, start_index + 1)

            if end_match is None:
                # No end found - highlight to end of block and set state
                self.setCurrentBlockState(rule.state)
                length = len(text) - start_index
            else:
                # Found end - highlight the whole span
                length = end_match.end() - start_index

            self.setFormat(start_index, length, rule.format)

            # Look for next occurrence
            next_match = rule.start_pattern.search(text, start_index + length)
            start_index = next_match.start() if next_match else -1
