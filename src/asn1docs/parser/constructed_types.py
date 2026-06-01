import pyparsing
from . import lexical_items
from . import javadoc
from . import values_types

# ITU-T X.680 Section 25

ExtensionAndException = pyparsing.Forward()
OptionalExtensionMarker = pyparsing.Forward()
DocumentedComponentType = pyparsing.Forward()
ComponentType = pyparsing.Forward()
ComponentTypeLists = pyparsing.Forward()
ComponentTypeList = pyparsing.Forward()
ExtensionAdditions = pyparsing.Forward()
ExtensionAddition = pyparsing.Forward()
ExtensionAdditionList = pyparsing.Forward()
ExtensionAdditionGroup = pyparsing.Forward()
ExtensionEndMarker = pyparsing.Forward()
VersionNumber = pyparsing.Forward()
ComponentValueList = pyparsing.Forward()
ValueList = pyparsing.Forward()
NamedValueList = pyparsing.Forward()
AlternativeTypeLists = pyparsing.Forward()
AlternativeTypeList = pyparsing.Forward()
DocumentedNamedType = pyparsing.Forward()
ExtensionAdditionAlternativesList = pyparsing.Forward()
ExtensionAdditionAlternativesGroup = pyparsing.Forward()
ExtensionAdditionAlternatives = pyparsing.Forward()
ExtensionAdditionAlternative = pyparsing.Forward()

# 25.1
SequenceType = pyparsing.Group(
    (pyparsing.Keyword("SEQUENCE") + lexical_items.LBRACE + lexical_items.RBRACE)
    | (pyparsing.Keyword("SEQUENCE") + lexical_items.LBRACE + ComponentTypeLists("component_type_lists") + lexical_items.RBRACE)
    | (pyparsing.Keyword("SEQUENCE") + lexical_items.LBRACE + ExtensionAndException + OptionalExtensionMarker + lexical_items.RBRACE)
)

ExtensionAndException <<= pyparsing.Group(
    lexical_items.ellipsis
    | (lexical_items.ellipsis + values_types.ExceptionSpec)
)

OptionalExtensionMarker <<= pyparsing.Group(
    pyparsing.Optional(lexical_items.COMMA + lexical_items.ellipsis)
)

ComponentTypeLists <<= pyparsing.Group(
    (ComponentTypeList("component_type_list") + lexical_items.COMMA + ExtensionAndException + ExtensionAdditions + ExtensionEndMarker + lexical_items.COMMA + ComponentTypeList)
    | (ComponentTypeList("component_type_list") + lexical_items.COMMA + ExtensionAndException + ExtensionAdditions + OptionalExtensionMarker)
    | ComponentTypeList("component_type_list")
    | (ExtensionAndException + ExtensionAdditions + ExtensionEndMarker + lexical_items.COMMA + ComponentTypeList)
    | (ExtensionAndException + ExtensionAdditions + OptionalExtensionMarker)
)

ExtensionEndMarker <<= pyparsing.Group(lexical_items.COMMA + lexical_items.ellipsis)

ExtensionAdditions <<= pyparsing.Group(
    pyparsing.Optional(lexical_items.COMMA + ExtensionAdditionList)
)

ExtensionAdditionList <<= pyparsing.DelimitedList(
    ExtensionAddition,
    delim=lexical_items.COMMA,
    min=1
)

ExtensionAddition <<= pyparsing.Group(
    ComponentType
    | ExtensionAdditionGroup
)

ExtensionAdditionGroup <<= pyparsing.Group(
    lexical_items.LBRACK + lexical_items.LBRACK + VersionNumber + ComponentTypeList + lexical_items.RBRACK + lexical_items.RBRACK
)

VersionNumber <<= pyparsing.Group(
    pyparsing.Optional(lexical_items.number + lexical_items.COLON)
)

ComponentTypeList <<= pyparsing.Group(pyparsing.DelimitedList(
    DocumentedComponentType("component_type"),
    delim=lexical_items.COMMA,
    min=1
))

DocumentedComponentType <<= pyparsing.Group(
    pyparsing.Optional(javadoc.javadoc("javadoc")) +
    ComponentType("component_type")
)

ComponentType <<= pyparsing.Group(
    pyparsing.Group(values_types.NamedType("named_type") + pyparsing.Keyword("OPTIONAL"))("optional_named_type")
    | pyparsing.Group(
        values_types.NamedType("named_type") + pyparsing.Keyword("DEFAULT") + values_types.Value("default"))("default_named_type")
    | values_types.NamedType("simple_named_type")
    | pyparsing.Group(pyparsing.Keyword("COMPONENTS OF") + values_types.Type("type"))("components_of_type")
)

# 25.18
SequenceValue = pyparsing.Group(
    (lexical_items.LBRACE + NamedValueList("component_value_list") + lexical_items.RBRACE)
    | (lexical_items.LBRACE + lexical_items.RBRACE)
)

# ITU-T X.680 Section 26

# 26.1
SequenceOfType = pyparsing.Group(
    (pyparsing.Keyword("SEQUENCE OF") + values_types.Type("type"))
    | (pyparsing.Keyword("SEQUENCE OF") + values_types.NamedType("named_type"))
)

# 26.3
SequenceOfValue = pyparsing.Group(
    (lexical_items.LBRACE + NamedValueList + lexical_items.RBRACE)
    | (lexical_items.LBRACE + ValueList + lexical_items.RBRACE)
    | (lexical_items.LBRACE + lexical_items.RBRACE)
)

ValueList <<= pyparsing.Group(pyparsing.delimited_list(
    values_types.Value,
    delim=lexical_items.COMMA,
    min=1
))

NamedValueList <<= pyparsing.Group(pyparsing.delimited_list(
    values_types.NamedValue,
    delim=lexical_items.COMMA,
    min=1
))

# ITU-T X.680 Section 27

# 27.1
SetType = pyparsing.Group(
    (pyparsing.Keyword("SET") + lexical_items.LBRACE + lexical_items.RBRACE)
    | (pyparsing.Keyword("SET") + lexical_items.LBRACE + ExtensionAndException + OptionalExtensionMarker + lexical_items.RBRACE)
    | (pyparsing.Keyword("SET") + lexical_items.LBRACE + ComponentTypeLists + lexical_items.RBRACE)
)

# ITU-T X.680 Section 28

# 28.1
SetOfType = pyparsing.Group(
    (pyparsing.Keyword("SET OF") + values_types.Type)
    | (pyparsing.Keyword("SET OF") + values_types.NamedType)
)

# ITU-T X.680 Section 29

# 29.1
ChoiceType = pyparsing.Group(
    pyparsing.Keyword("CHOICE") + lexical_items.LBRACE + AlternativeTypeLists("alternate_type_lists") + lexical_items.RBRACE
)

AlternativeTypeLists <<= pyparsing.Group(
    (AlternativeTypeList("alternate_type_list") + lexical_items.COMMA + ExtensionAndException + ExtensionAdditionAlternatives + OptionalExtensionMarker)
    | AlternativeTypeList("alternate_type_list")
)

ExtensionAdditionAlternatives <<= pyparsing.Group(
    pyparsing.Optional(lexical_items.COMMA + ExtensionAdditionAlternativesList)
)

ExtensionAdditionAlternativesList <<= pyparsing.Group(
    ExtensionAdditionAlternative
    | (ExtensionAdditionAlternativesList + lexical_items.COMMA + ExtensionAdditionAlternative)
)

ExtensionAdditionAlternative <<= pyparsing.Group(
    ExtensionAdditionAlternativesGroup
    | values_types.NamedType
)

ExtensionAdditionAlternativesGroup <<= pyparsing.Group(
    lexical_items.LBRACK + lexical_items.LBRACK + VersionNumber + AlternativeTypeList + lexical_items.RBRACK + lexical_items.RBRACK
)

AlternativeTypeList <<= pyparsing.Group(pyparsing.DelimitedList(
    DocumentedNamedType("alternate_type"),
    delim=lexical_items.COMMA,
    min=1
))

DocumentedNamedType <<= pyparsing.Group(
    pyparsing.Optional(javadoc.javadoc("javadoc")) +
    values_types.NamedType("named_type")
)

# 29.11
ChoiceValue = pyparsing.Group(
    lexical_items.identifier("identifier") + lexical_items.COLON + values_types.Value("value")
)

# ITU-T X.680 Section 30

# 30.1
SelectionType = pyparsing.Group(
    lexical_items.identifier + lexical_items.LANGLE + values_types.Type
)