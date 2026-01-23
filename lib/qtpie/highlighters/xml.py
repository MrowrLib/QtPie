"""XML syntax highlighter."""

import re
from typing import ClassVar

from qtpie.highlighters.base import (
    HighlightRule,
    MultiLineRule,
    SyntaxHighlighter,
    make_format,
)


class XmlHighlighter(SyntaxHighlighter):
    """Syntax highlighter for XML."""

    rules: ClassVar[list[HighlightRule]] = [
        # XML declaration
        HighlightRule(
            pattern=re.compile(r"<\?xml[^?]*\?>"),
            format=make_format(color="#808080", italic=True),
        ),
        # Processing instructions
        HighlightRule(
            pattern=re.compile(r"<\?[\w:-]+[^?]*\?>"),
            format=make_format(color="#808080", italic=True),
        ),
        # CDATA
        HighlightRule(
            pattern=re.compile(r"<!\[CDATA\[.*?\]\]>", re.DOTALL),
            format=make_format(color="#a5c261"),
        ),
        # Tags (opening and closing)
        HighlightRule(
            pattern=re.compile(r"</?[\w:-]+"),
            format=make_format(color="#e8bf6a"),
        ),
        # Closing bracket of tags
        HighlightRule(
            pattern=re.compile(r"/?>"),
            format=make_format(color="#e8bf6a"),
        ),
        # Attribute names
        HighlightRule(
            pattern=re.compile(r"\b[\w:-]+(?=\s*=)"),
            format=make_format(color="#bababa"),
        ),
        # Attribute values (double-quoted)
        HighlightRule(
            pattern=re.compile(r'"[^"]*"'),
            format=make_format(color="#6a8759"),
        ),
        # Attribute values (single-quoted)
        HighlightRule(
            pattern=re.compile(r"'[^']*'"),
            format=make_format(color="#6a8759"),
        ),
        # Entities
        HighlightRule(
            pattern=re.compile(r"&[\w#]+;"),
            format=make_format(color="#cc7832"),
        ),
    ]

    multiline_rules: ClassVar[list[MultiLineRule]] = [
        # XML comments
        MultiLineRule(
            start_pattern=re.compile(r"<!--"),
            end_pattern=re.compile(r"-->"),
            format=make_format(color="#808080", italic=True),
            state=1,
        ),
    ]
