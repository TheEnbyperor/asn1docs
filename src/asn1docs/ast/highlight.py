import collections
import typing

import pyparsing
from ..parser import lexical_items

TokenRule = collections.namedtuple("TokenRule", ["type", "value"])
Span = collections.namedtuple("Span", ["type", "text"])

HIGHLIGHT_RULES = [
    TokenRule("comment", lexical_items.line_comment | lexical_items.block_comment_with_javadoc),
    TokenRule("keyword", lexical_items.reserved_word),
    TokenRule(
        "string",
        pyparsing.MatchFirst([
            lexical_items.bstring, lexical_items.hstring, lexical_items.cstring, lexical_items.simplestring,
            lexical_items.tstring,
        ]),
    ),
    TokenRule("number", pyparsing.MatchFirst([
        lexical_items.realnumber, lexical_items.number, lexical_items.integerUnicodeLabel
    ])),
    TokenRule(
        "identifier",
        pyparsing.MatchFirst([
            lexical_items.typereference, lexical_items.identifier, lexical_items.valuereference,
            lexical_items.modulereference, lexical_items.encodingreference, lexical_items.psname
        ]),
    ),
    TokenRule(
        "operator",
        pyparsing.MatchFirst([
            lexical_items.assignment, lexical_items.ellipsis, lexical_items.range_separator,
            lexical_items.left_version_brackets, lexical_items.right_version_brackets,
            lexical_items.single_char_lexicals,
        ]),
    ),
]


def to_highlight_spans(text: str) -> typing.List[Span]:
    matches = []
    for cls, expr in HIGHLIGHT_RULES:
        for _, start, end in expr.parse_with_tabs().scan_string(text):
            matches.append((start, end, cls))

    matches.sort(key=lambda item: (item[0], -(item[1] - item[0])))

    out = []
    pos = 0
    for start, end, cls in matches:
        if start < pos:
            continue

        if start > pos:
            out.append(Span(None, text[pos:start]))

        out.append(Span(cls, text[start:end]))
        pos = end

    if pos < len(text):
        out.append(Span(None, text[pos]))

    return out