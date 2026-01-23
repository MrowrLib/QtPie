"""JavaScript syntax highlighter."""

import re
from typing import ClassVar

from qtpie.highlighters.base import (
    HighlightRule,
    MultiLineRule,
    SyntaxHighlighter,
    make_format,
)


class JavaScriptHighlighter(SyntaxHighlighter):
    """Syntax highlighter for JavaScript/TypeScript.

    Good enough for most code. Known limitations:
    - Template literals with expressions `${...}` just highlight the whole thing as string
    - Regex literals may occasionally mis-highlight (e.g., division after parentheses)
    """

    rules: ClassVar[list[HighlightRule]] = [
        # Single-line comments
        HighlightRule(
            pattern=re.compile(r"//.*$", re.MULTILINE),
            format=make_format(color="#808080", italic=True),
        ),
        # Keywords
        HighlightRule(
            pattern=re.compile(
                r"\b(?:async|await|break|case|catch|class|const|continue|debugger|default|"
                r"delete|do|else|enum|export|extends|finally|for|function|if|implements|"
                r"import|in|instanceof|interface|let|new|of|package|private|protected|"
                r"public|return|static|super|switch|this|throw|try|typeof|var|void|while|"
                r"with|yield|from|as|get|set)\b"
            ),
            format=make_format(color="#cc7832", bold=True),
        ),
        # Built-in values
        HighlightRule(
            pattern=re.compile(r"\b(?:true|false|null|undefined|NaN|Infinity)\b"),
            format=make_format(color="#cc7832", bold=True),
        ),
        # Built-in objects/types
        HighlightRule(
            pattern=re.compile(
                r"\b(?:Array|Boolean|Date|Error|Function|JSON|Math|Number|Object|"
                r"Promise|Proxy|RegExp|String|Symbol|Map|Set|WeakMap|WeakSet|"
                r"ArrayBuffer|DataView|Float32Array|Float64Array|Int8Array|Int16Array|"
                r"Int32Array|Uint8Array|Uint16Array|Uint32Array|BigInt|console|window|"
                r"document|globalThis)\b"
            ),
            format=make_format(color="#ffc66d"),
        ),
        # Function/method calls
        HighlightRule(
            pattern=re.compile(r"\b[\w$]+(?=\s*\()"),
            format=make_format(color="#ffc66d"),
        ),
        # Numbers (including hex, octal, binary, bigint)
        HighlightRule(
            pattern=re.compile(r"\b(?:0[xX][0-9a-fA-F_]+|0[oO][0-7_]+|0[bB][01_]+|\d[\d_]*(?:\.[\d_]+)?(?:[eE][+-]?\d+)?n?)\b"),
            format=make_format(color="#6897bb"),
        ),
        # Template literals (basic - just color the whole thing)
        HighlightRule(
            pattern=re.compile(r"`[^`\\]*(?:\\.[^`\\]*)*`"),
            format=make_format(color="#6a8759"),
        ),
        # Double-quoted strings
        HighlightRule(
            pattern=re.compile(r'"[^"\\]*(?:\\.[^"\\]*)*"'),
            format=make_format(color="#6a8759"),
        ),
        # Single-quoted strings
        HighlightRule(
            pattern=re.compile(r"'[^'\\]*(?:\\.[^'\\]*)*'"),
            format=make_format(color="#6a8759"),
        ),
        # Regex literals (basic - after = or ( or , or : or [ or ! or &)
        HighlightRule(
            pattern=re.compile(r"(?<=[=(:,\[!&|?])\s*/(?!\*)(?:[^/\\]|\\.)+/[gimsuy]*"),
            format=make_format(color="#e8bf6a"),
        ),
        # Arrow functions
        HighlightRule(
            pattern=re.compile(r"=>"),
            format=make_format(color="#cc7832"),
        ),
        # Operators
        HighlightRule(
            pattern=re.compile(r"(?:\.\.\.|\?\?|===|!==|==|!=|<=|>=|&&|\|\||<<|>>>|>>|\+\+|--|\+=|-=|\*=|/=|%=|&=|\|=|\^=)"),
            format=make_format(color="#cc7832"),
        ),
        # Decorators (TypeScript/proposal)
        HighlightRule(
            pattern=re.compile(r"@[\w$]+"),
            format=make_format(color="#bbb529"),
        ),
    ]

    multiline_rules: ClassVar[list[MultiLineRule]] = [
        # Block comments
        MultiLineRule(
            start_pattern=re.compile(r"/\*"),
            end_pattern=re.compile(r"\*/"),
            format=make_format(color="#808080", italic=True),
            state=1,
        ),
    ]
