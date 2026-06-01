import pyparsing
from . import lexical_items

Reference = pyparsing.Forward()
ParameterizedType = pyparsing.Forward()
ParameterizedValue = pyparsing.Forward()

# ITU-T X.680 Section 14

ExternalTypeReference = pyparsing.Group(
    lexical_items.modulereference("module_reference") + lexical_items.DOT + lexical_items.typereference("type_reference")
)

ExternalValueReference = pyparsing.Group(
    lexical_items.modulereference + lexical_items.DOT + lexical_items.valuereference
)

DefinedType = pyparsing.Group(
    ParameterizedType("parameterized_type")
    | ExternalTypeReference("external_type_reference")
    | lexical_items.typereference("type_reference")
)

DefinedValue = pyparsing.Group(
    ParameterizedValue("parameterised_value")
    | ExternalValueReference("external_value_reference")
    | lexical_items.valuereference("value_reference")
)

# ITU-T X.680 Section 16

Type = pyparsing.Forward()
UnconstrainedType = pyparsing.Forward()
Value = pyparsing.Forward()
ValueSet = pyparsing.Forward()
ElementSetSpecs = pyparsing.Forward()
NamedType = pyparsing.Forward()
NamedValue = pyparsing.Forward()

TypeAssignment = pyparsing.Group(
    lexical_items.typereference("type_reference") + lexical_items.assignment + Type("type")
)

ValueAssignment = pyparsing.Group(
    lexical_items.valuereference("value_reference") + Type("type") + lexical_items.assignment + Value("value")
)

ValueSetTypeAssignment = pyparsing.Group(
    lexical_items.typereference("type_reference") + Type("type") + lexical_items.assignment + ValueSet("value_set")
)

ValueSet <<= pyparsing.Group(
    lexical_items.LBRACE + ElementSetSpecs + lexical_items.RBRACE
)

# ITU-T X.680 Section 53
ExceptionIdentification = pyparsing.Forward()
SignedNumber = pyparsing.Forward()

# 53.4
ExceptionSpec = pyparsing.Group(
   pyparsing.Optional(lexical_items.BANG + ExceptionIdentification)
)

ExceptionIdentification <<= pyparsing.Group(
    SignedNumber
    | DefinedValue
    | (Type + lexical_items.COLON + Value)
)