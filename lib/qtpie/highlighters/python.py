"""Python syntax highlighter."""

import re
from typing import ClassVar

from qtpie.highlighters.base import (
    HighlightRule,
    MultiLineRule,
    SyntaxHighlighter,
    make_format,
)


class PythonHighlighter(SyntaxHighlighter):
    """Syntax highlighter for Python."""

    rules: ClassVar[list[HighlightRule]] = [
        # Comments
        HighlightRule(
            pattern=re.compile(r"#.*$", re.MULTILINE),
            format=make_format(color="#808080", italic=True),
        ),
        # Keywords
        HighlightRule(
            pattern=re.compile(
                r"\b(?:and|as|assert|async|await|break|class|continue|def|del|elif|else|"
                r"except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|"
                r"pass|raise|return|try|while|with|yield|match|case|type)\b"
            ),
            format=make_format(color="#cc7832", bold=True),
        ),
        # Built-in constants
        HighlightRule(
            pattern=re.compile(r"\b(?:True|False|None|Ellipsis|NotImplemented|__debug__)\b"),
            format=make_format(color="#cc7832", bold=True),
        ),
        # Built-in functions
        HighlightRule(
            pattern=re.compile(
                r"\b(?:abs|aiter|all|anext|any|ascii|bin|bool|breakpoint|bytearray|bytes|"
                r"callable|chr|classmethod|compile|complex|delattr|dict|dir|divmod|"
                r"enumerate|eval|exec|filter|float|format|frozenset|getattr|globals|"
                r"hasattr|hash|help|hex|id|input|int|isinstance|issubclass|iter|len|"
                r"list|locals|map|max|memoryview|min|next|object|oct|open|ord|pow|print|"
                r"property|range|repr|reversed|round|set|setattr|slice|sorted|"
                r"staticmethod|str|sum|super|tuple|type|vars|zip|__import__)\b"
            ),
            format=make_format(color="#ffc66d"),
        ),
        # Decorators
        HighlightRule(
            pattern=re.compile(r"@[\w.]+"),
            format=make_format(color="#bbb529"),
        ),
        # Self/cls
        HighlightRule(
            pattern=re.compile(r"\b(?:self|cls)\b"),
            format=make_format(color="#9876aa", italic=True),
        ),
        # Function/method definitions
        HighlightRule(
            pattern=re.compile(r"(?<=\bdef\s)\w+"),
            format=make_format(color="#ffc66d"),
        ),
        # Class definitions
        HighlightRule(
            pattern=re.compile(r"(?<=\bclass\s)\w+"),
            format=make_format(color="#ffc66d", bold=True),
        ),
        # Numbers (int, float, complex, hex, octal, binary)
        HighlightRule(
            pattern=re.compile(r"\b(?:0[xX][0-9a-fA-F_]+|0[oO][0-7_]+|0[bB][01_]+|\d[\d_]*(?:\.[\d_]+)?(?:[eE][+-]?\d+)?j?)\b"),
            format=make_format(color="#6897bb"),
        ),
        # Triple-quoted strings (must come before single quotes)
        HighlightRule(
            pattern=re.compile(r'[fFrRbBuU]?"""[^"\\]*(?:(?:\\.|"(?!""))[^"\\]*)*"""'),
            format=make_format(color="#6a8759"),
        ),
        HighlightRule(
            pattern=re.compile(r"[fFrRbBuU]?'''[^'\\]*(?:(?:\\.|'(?!''))[^'\\]*)*'''"),
            format=make_format(color="#6a8759"),
        ),
        # Double-quoted strings
        HighlightRule(
            pattern=re.compile(r'[fFrRbBuU]?"[^"\\]*(?:\\.[^"\\]*)*"'),
            format=make_format(color="#6a8759"),
        ),
        # Single-quoted strings
        HighlightRule(
            pattern=re.compile(r"[fFrRbBuU]?'[^'\\]*(?:\\.[^'\\]*)*'"),
            format=make_format(color="#6a8759"),
        ),
        # Magic methods/attributes
        HighlightRule(
            pattern=re.compile(r"\b__\w+__\b"),
            format=make_format(color="#b200b2"),
        ),
    ]

    multiline_rules: ClassVar[list[MultiLineRule]] = [
        # Triple double-quoted strings
        MultiLineRule(
            start_pattern=re.compile(r'[fFrRbBuU]?"""'),
            end_pattern=re.compile(r'"""'),
            format=make_format(color="#6a8759"),
            state=1,
        ),
        # Triple single-quoted strings
        MultiLineRule(
            start_pattern=re.compile(r"[fFrRbBuU]?'''"),
            end_pattern=re.compile(r"'''"),
            format=make_format(color="#6a8759"),
            state=2,
        ),
    ]
