"""CSS/SCSS syntax highlighter."""

import re
from typing import ClassVar

from qtpie.highlighters.base import (
    HighlightRule,
    MultiLineRule,
    SyntaxHighlighter,
    make_format,
)


class CssHighlighter(SyntaxHighlighter):
    """Syntax highlighter for CSS and SCSS.

    Handles nested braces for SCSS compatibility.
    """

    rules: ClassVar[list[HighlightRule]] = [
        # Single-line comments (SCSS)
        HighlightRule(
            pattern=re.compile(r"//.*$", re.MULTILINE),
            format=make_format(color="#808080", italic=True),
        ),
        # SCSS variables
        HighlightRule(
            pattern=re.compile(r"\$[\w-]+"),
            format=make_format(color="#9876aa"),
        ),
        # @rules (@import, @media, @mixin, @include, etc.)
        HighlightRule(
            pattern=re.compile(r"@[\w-]+"),
            format=make_format(color="#cc7832", bold=True),
        ),
        # Selectors - IDs
        HighlightRule(
            pattern=re.compile(r"#[\w-]+"),
            format=make_format(color="#e8bf6a"),
        ),
        # Selectors - classes
        HighlightRule(
            pattern=re.compile(r"\.[\w-]+"),
            format=make_format(color="#a5c261"),
        ),
        # Selectors - pseudo-classes and pseudo-elements
        HighlightRule(
            pattern=re.compile(r"::?[\w-]+"),
            format=make_format(color="#cc7832"),
        ),
        # Property names (before colon, not starting with --)
        HighlightRule(
            pattern=re.compile(r"(?<!-)\b[\w-]+(?=\s*:)"),
            format=make_format(color="#9876aa"),
        ),
        # CSS custom properties (--var-name)
        HighlightRule(
            pattern=re.compile(r"--[\w-]+"),
            format=make_format(color="#9876aa"),
        ),
        # Numbers with units
        HighlightRule(
            pattern=re.compile(r"-?\d+(?:\.\d+)?(?:px|em|rem|%|vh|vw|vmin|vmax|ch|ex|cm|mm|in|pt|pc|deg|rad|grad|turn|s|ms|Hz|kHz|dpi|dpcm|dppx)?"),
            format=make_format(color="#6897bb"),
        ),
        # Hex colors
        HighlightRule(
            pattern=re.compile(r"#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b"),
            format=make_format(color="#6897bb"),
        ),
        # Color keywords and other common values
        HighlightRule(
            pattern=re.compile(r"\b(?:transparent|inherit|initial|unset|none|auto|normal|bold|italic)\b"),
            format=make_format(color="#cc7832"),
        ),
        # Strings (double-quoted)
        HighlightRule(
            pattern=re.compile(r'"[^"\\]*(?:\\.[^"\\]*)*"'),
            format=make_format(color="#6a8759"),
        ),
        # Strings (single-quoted)
        HighlightRule(
            pattern=re.compile(r"'[^'\\]*(?:\\.[^'\\]*)*'"),
            format=make_format(color="#6a8759"),
        ),
        # Functions (url, rgb, calc, var, etc.)
        HighlightRule(
            pattern=re.compile(r"\b[\w-]+(?=\()"),
            format=make_format(color="#ffc66d"),
        ),
        # !important
        HighlightRule(
            pattern=re.compile(r"!important\b"),
            format=make_format(color="#cc7832", bold=True),
        ),
    ]

    multiline_rules: ClassVar[list[MultiLineRule]] = [
        # Block comments /* */
        MultiLineRule(
            start_pattern=re.compile(r"/\*"),
            end_pattern=re.compile(r"\*/"),
            format=make_format(color="#808080", italic=True),
            state=1,
        ),
    ]
