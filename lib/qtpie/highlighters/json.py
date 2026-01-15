"""JSON syntax highlighter."""

import re
from typing import ClassVar

from qtpie.highlighters.base import HighlightRule, SyntaxHighlighter, make_format


class JsonHighlighter(SyntaxHighlighter):
    """Syntax highlighter for JSON."""

    rules: ClassVar[list[HighlightRule]] = [
        # Keys (strings followed by colon)
        HighlightRule(
            pattern=re.compile(r'"[^"\\]*(?:\\.[^"\\]*)*"\s*(?=:)'),
            format=make_format(color="#9876aa"),
        ),
        # String values
        HighlightRule(
            pattern=re.compile(r':\s*"[^"\\]*(?:\\.[^"\\]*)*"'),
            format=make_format(color="#6a8759"),
        ),
        # Numbers
        HighlightRule(
            pattern=re.compile(r"-?\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b"),
            format=make_format(color="#6897bb"),
        ),
        # Booleans
        HighlightRule(
            pattern=re.compile(r"\b(?:true|false)\b"),
            format=make_format(color="#cc7832", bold=True),
        ),
        # Null
        HighlightRule(
            pattern=re.compile(r"\bnull\b"),
            format=make_format(color="#cc7832", bold=True),
        ),
    ]
