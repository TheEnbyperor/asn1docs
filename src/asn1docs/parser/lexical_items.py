# ITU-T X.680 Section 12 lexical items

import pyparsing
import re

pyparsing.ParserElement.enable_packrat()
pyparsing.ParserElement.set_default_whitespace_chars(" \t\n\r\v\f\u00A0")

UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
LOWER = "abcdefghijklmnopqrstuvwxyz"
LETTERS = UPPER + LOWER
DIGITS = "0123456789"
IDENT_BODY = LETTERS + DIGITS


def hyphenated_word(first_chars: str, body_chars: str):
    """Match a word that may contain internal hyphens, but not trailing or doubled hyphens."""
    head = pyparsing.Word(first_chars, body_chars)
    tail = pyparsing.ZeroOrMore(pyparsing.Literal("-") + pyparsing.Word(body_chars))
    return pyparsing.Combine(head + tail)

block_comment = pyparsing.Regex(r"/\*(?!\*).*?\*/", re.S)
block_comment_with_javadoc = pyparsing.Regex(r"/\*.*?\*/", re.S)
line_comment = pyparsing.Regex(r"--[^\n\r]*")
comment = line_comment | block_comment

RESERVED_WORDS = [
    "ABSENT",
    "ABSTRACT-SYNTAX",
    "ALL",
    "APPLICATION",
    "AUTOMATIC",
    "BEGIN",
    "BIT",
    "BMPString",
    "BOOLEAN",
    "BY",
    "CHARACTER",
    "CHOICE",
    "CLASS",
    "COMPONENT",
    "COMPONENTS",
    "CONSTRAINED",
    "CONTAINING",
    "DATE",
    "DATE-TIME",
    "DEFAULT",
    "DEFINITIONS",
    "DURATION",
    "EMBEDDED",
    "ENCODED",
    "ENCODING-CONTROL",
    "END",
    "ENUMERATED",
    "EXCEPT",
    "EXPLICIT",
    "EXPORTS",
    "EXTENSIBILITY",
    "EXTERNAL",
    "FALSE",
    "FROM",
    "GeneralizedTime",
    "GeneralString",
    "GraphicString",
    "IA5String",
    "IDENTIFIER",
    "IMPLICIT",
    "IMPLIED",
    "IMPORTS",
    "INCLUDES",
    "INSTANCE",
    "INSTRUCTIONS",
    "INTEGER",
    "INTERSECTION",
    "ISO646String",
    "MAX",
    "MIN",
    "MINUS-INFINITY",
    "NOT-A-NUMBER",
    "NULL",
    "NumericString",
    "OBJECT",
    "ObjectDescriptor",
    "OCTET",
    "OF",
    "OID-IRI",
    "OPTIONAL",
    "PATTERN",
    "PDV",
    "PLUS-INFINITY",
    "PRESENT",
    "PrintableString",
    "PRIVATE",
    "REAL",
    "RELATIVE-OID",
    "RELATIVE-OID-IRI",
    "SEQUENCE",
    "SET",
    "SETTINGS",
    "SIZE",
    "STRING",
    "SYNTAX",
    "T61String",
    "TAGS",
    "TeletexString",
    "TIME",
    "TIME-OF-DAY",
    "TRUE",
    "TYPE-IDENTIFIER",
    "UNION",
    "UNIQUE",
    "UNIVERSAL",
    "UniversalString",
    "UTCTime",
    "UTF8String",
    "VideotexString",
    "VisibleString",
    "WITH"
]
reserved_word = pyparsing.MatchFirst([pyparsing.Keyword(w) for w in RESERVED_WORDS])

# 12.2 typereference
typereference = (~reserved_word + hyphenated_word(UPPER, IDENT_BODY))

# 12.3 identifier
identifier = (~reserved_word + hyphenated_word(LOWER, IDENT_BODY))

# 12.4 valuereference
valuereference = identifier.copy()

# 12.5 modulereference
modulereference = typereference.copy()

# 12.6 comments are handled by `ignore()` on the root grammar

# 12.7 empty lexical item
empty = pyparsing.Empty()

# 12.8 number
number = pyparsing.Regex(r"(?:0|[1-9][0-9]*)")

# 12.9 realnumber
realnumber = pyparsing.Regex(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?")

# 12.10 binary string
bstring = pyparsing.Regex(r"'(?:[01]|\s)*'B", re.S)

# 12.11 XML binary string item
xmlbstring = pyparsing.Regex(r"(?:[01\s])+", re.S)

# 12.12 hexadecimal string
hstring = pyparsing.Regex(r"'(?:[0-9A-Fa-f]|\s)*'H", re.S)

# 12.13 XML hexadecimal string item
xmlhstring = pyparsing.Regex(r"(?:[0-9A-Fa-f\s])+", re.S)

# 12.14 character string
cstring = pyparsing.Regex(r'"(?:[^"]|"")*"', re.S)

# 12.15 XML character string item
# Practical parser form: allow XML escapes and raw XML-safe characters.
xmlcstring = pyparsing.Regex(
    r"(?:&#x[0-9A-Fa-f]+;|&#[0-9]+;|&(?:amp|lt|gt);|[\t\r\n\x20-\x7E\u0080-\U0010FFFF])+",
    re.S,
)

# 12.16 simple string
simplestring = pyparsing.Regex(r'"(?:[\x20-\x7E\r\n\v\f])*"', re.S)

# 12.17 time string
tstring = pyparsing.Regex(r'"[0-9+\-:.,/CDHMRPTWYZ]+"')

# 12.18 XML time string
xmltstring = pyparsing.Regex(r"(?:[0-9+\-:.,/CDHMRPTWYZ])+")

# 12.19 property and setting names
psname = hyphenated_word(UPPER, IDENT_BODY)

# 12.20 to 12.24 fixed tokens
assignment = pyparsing.Literal("::=")
range_separator = pyparsing.Literal("..")
ellipsis = pyparsing.Literal("...")
left_version_brackets = pyparsing.Literal("[[")
right_version_brackets = pyparsing.Literal("]]")

# 12.25 encodingreference
encodingreference = hyphenated_word(UPPER, UPPER + DIGITS)

# 12.26 integerUnicodeLabel
integerUnicodeLabel = pyparsing.Regex(r"(?:0|[1-9][0-9]*)")

# 12.27 non-integerUnicodeLabel
non_integerUnicodeLabel = pyparsing.Regex(r"(?![0-9]+\Z)\w+", re.UNICODE)

# 12.28 / 12.29 XML tag punctuators
xml_end_tag_start = pyparsing.Literal("</")
xml_single_tag_end = pyparsing.Literal("/>")

# 12.30 / 12.31 booleans
xml_boolean_true = pyparsing.Keyword("true")
xml_boolean_extended_true = pyparsing.Keyword("true") | pyparsing.Literal("1")
xml_boolean_false = pyparsing.Keyword("false")
xml_boolean_extended_false = pyparsing.Keyword("false") | pyparsing.Literal("0")

# 12.34 / 12.35 special XML reals
xml_real_nan = pyparsing.Keyword("NaN")
xml_real_inf = pyparsing.Keyword("INF")

# 12.36 xmlasn1typename (context-sensitive; keep as typereference for now)
xmlasn1typename = typereference.copy()

# 12.37 single character lexical items
LBRACE = pyparsing.Literal("{")
RBRACE = pyparsing.Literal("}")
LANGLE = pyparsing.Literal("<")
RANGLE = pyparsing.Literal(">")
COMMA = pyparsing.Literal(",")
DOT = pyparsing.Literal(".")
SLASH = pyparsing.Literal("/")
LPAR = pyparsing.Literal("(")
RPAR = pyparsing.Literal(")")
LBRACK = pyparsing.Literal("[")
RBRACK = pyparsing.Literal("]")
HYPHEN = pyparsing.Literal("-")
COLON = pyparsing.Literal(":")
EQUALS = pyparsing.Literal("=")
QUOTE = pyparsing.Literal('"')
APOSTROPHE = pyparsing.Literal("'")
SEMI = pyparsing.Literal(";")
AT = pyparsing.Literal("@")
BAR = pyparsing.Literal("|")
BANG = pyparsing.Literal("!")
CARET = pyparsing.Literal("^")

single_char_lexicals = pyparsing.MatchFirst(
    [
        LBRACE, RBRACE, LANGLE, RANGLE, COMMA, DOT, SLASH, LPAR, RPAR,
        LBRACK, RBRACK, HYPHEN, COLON, EQUALS, QUOTE, APOSTROPHE, SEMI,
        AT, BAR, BANG, CARET,
    ]
)
