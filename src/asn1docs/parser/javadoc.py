import pyparsing
from . import lexical_items

start = pyparsing.Suppress("/**")
end = pyparsing.Suppress("*/")
line_text = pyparsing.Regex(r"[^\r\n]*")
tag = pyparsing.Group(
    pyparsing.Suppress("@")
    + pyparsing.Word(pyparsing.alphas)("tag")
    + pyparsing.Optional(lexical_items.identifier("name"))
    + pyparsing.Optional(line_text("text"))
).ignore_whitespace()
body_line = pyparsing.Group(
    pyparsing.LineStart()
    + pyparsing.Optional(pyparsing.White(" \t"))
    + pyparsing.Suppress("*")
    + pyparsing.NotAny("/")
    + pyparsing.Optional(pyparsing.White(" \t"))
    + (tag("tagged") | line_text("text"))
    + pyparsing.LineEnd()
)

javadoc = pyparsing.Group(
    pyparsing.Optional(pyparsing.White(" \t\n\r"))
    + start
    + pyparsing.Optional(pyparsing.White(" \t"))
    + pyparsing.LineEnd()
    + pyparsing.ZeroOrMore(body_line)("lines")
    + pyparsing.Optional(pyparsing.White(" \t"))
    + end
).leave_whitespace()