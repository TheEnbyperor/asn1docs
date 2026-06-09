# ITU-T X.680 Section 32 object identifier

import pyparsing
from . import lexical_items
from . import values_types

ObjIdComponentsList = pyparsing.Forward()
ObjIdComponents = pyparsing.Forward()
NameForm = pyparsing.Forward()
NumberForm = pyparsing.Forward()
NameAndNumberForm = pyparsing.Forward()
RelativeOIDComponentsList = pyparsing.Forward()
RelativeOIDComponents = pyparsing.Forward()

# ITU-T X.680 Section 32

# 32.1
ObjectIdentifierType = pyparsing.Keyword("OBJECT IDENTIFIER")

# 32.3
ObjectIdentifierValue = pyparsing.Group(
    (
            lexical_items.LBRACE
            + values_types.DefinedValue("value")
            + ObjIdComponentsList("components")
            + lexical_items.RBRACE
    ) |
    (
            lexical_items.LBRACE
            + ObjIdComponentsList("components")
            + lexical_items.RBRACE
    )
)

ObjIdComponentsList <<= pyparsing.Group(pyparsing.OneOrMore(ObjIdComponents))

ObjIdComponents <<= pyparsing.Group(
    NameAndNumberForm
    ^ NumberForm
    ^ NameForm
)

NameForm <<= lexical_items.identifier("name")

NumberForm <<= (
        lexical_items.number("number")
        | values_types.DefinedValue("number_defined_value")
)

NameAndNumberForm <<= (
        lexical_items.identifier("name")
        + pyparsing.Suppress("(")
        + NumberForm
        + pyparsing.Suppress(")")
)

# ITU-T X.680 Section 33

# 33.1
RelativeOIDType = pyparsing.Keyword("RELATIVE-OID")

# 33.3
RelativeOIDValue = pyparsing.Group(
    lexical_items.LBRACE + RelativeOIDComponentsList + lexical_items.RBRACE
)

RelativeOIDComponentsList <<= pyparsing.Group(
    RelativeOIDComponents
    | (RelativeOIDComponents + RelativeOIDComponentsList)
)

RelativeOIDComponents <<= pyparsing.Group(
    NumberForm
    | NameAndNumberForm
    | values_types.DefinedValue
)

# ITU-T X.680 Section 34

FirstArcIdentifier = pyparsing.Forward()
SubsequentArcIdentifier = pyparsing.Forward()
ArcIdentifier = pyparsing.Forward()

# 34.1
IRIType = pyparsing.Keyword("OID-IRI")

# 34.3
IRIValue = pyparsing.Group(
    lexical_items.QUOTE + FirstArcIdentifier + SubsequentArcIdentifier + lexical_items.QUOTE
)

FirstArcIdentifier <<= pyparsing.Group(
    lexical_items.SLASH + ArcIdentifier
)

SubsequentArcIdentifier <<= pyparsing.Group(
    (lexical_items.SLASH + ArcIdentifier + SubsequentArcIdentifier)
    | lexical_items.empty
)

ArcIdentifier <<= pyparsing.Group(
    lexical_items.integerUnicodeLabel,
    lexical_items.non_integerUnicodeLabel
)

# ITU-T X.680 Section 35

FirstRelativeArcIdentifier = pyparsing.Forward()

# 35.1
RelativeIRIType = pyparsing.Keyword("RELATIVE-OID-IRI")

# 35.3
RelativeIRIValue = pyparsing.Group(
    lexical_items.QUOTE + FirstRelativeArcIdentifier + SubsequentArcIdentifier + lexical_items.QUOTE
)

FirstRelativeArcIdentifier <<= pyparsing.Group(ArcIdentifier)
