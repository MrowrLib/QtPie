"""YAML syntax highlighter."""

import re
from typing import ClassVar

from qtpie.highlighters.base import HighlightRule, SyntaxHighlighter, make_format


class YamlHighlighter(SyntaxHighlighter):
    """Syntax highlighter for YAML."""

    rules: ClassVar[list[HighlightRule]] = [
        # Comments
        HighlightRule(
            pattern=re.compile(r"#.*$", re.MULTILINE),
            format=make_format(color="#808080", italic=True),
        ),
        # Keys (before colon)
        HighlightRule(
            pattern=re.compile(r"^[\s-]*[\w.-]+(?=\s*:)", re.MULTILINE),
            format=make_format(color="#9876aa"),
        ),
        # Anchors and aliases
        HighlightRule(
            pattern=re.compile(r"[&*][\w-]+"),
            format=make_format(color="#cc7832"),
        ),
        # Tags
        HighlightRule(
            pattern=re.compile(r"![\w!./:-]+"),
            format=make_format(color="#cc7832"),
        ),
        # Double-quoted strings
        HighlightRule(
            pattern=re.compile(r'"[^"\\]*(?:\\.[^"\\]*)*"'),
            format=make_format(color="#6a8759"),
        ),
        # Single-quoted strings
        HighlightRule(
            pattern=re.compile(r"'[^']*'"),
            format=make_format(color="#6a8759"),
        ),
        # Numbers
        HighlightRule(
            pattern=re.compile(r"\b-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b"),
            format=make_format(color="#6897bb"),
        ),
        # Booleans and null
        HighlightRule(
            pattern=re.compile(r"\b(?:true|false|yes|no|on|off|null|~)\b", re.IGNORECASE),
            format=make_format(color="#cc7832", bold=True),
        ),
        # Document markers
        HighlightRule(
            pattern=re.compile(r"^(?:---|\.\.\.)\s*$", re.MULTILINE),
            format=make_format(color="#cc7832", bold=True),
        ),
    ]
