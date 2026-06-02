import pyparsing
from . import lexical_items
from . import values_types
from . import constraints

ObjectClass = pyparsing.Forward()
Object = pyparsing.Forward()
ObjectSet = pyparsing.Forward()

# ITU-T X.681 Section 8

ExternalObjectClassReference = pyparsing.Forward()
ExternalObjectReference = pyparsing.Forward()
ExternalObjectSetReference = pyparsing.Forward()
UsefulObjectClassReference = pyparsing.Forward()

# 8.1
DefinedObjectClass = pyparsing.Group(
    ExternalObjectClassReference
    | lexical_items.objectclassreference("object_class_reference")
    | UsefulObjectClassReference
)
DefinedObject = pyparsing.Group(
    ExternalObjectReference
    | lexical_items.valuereference("object_reference")
)
DefinedObjectSet = pyparsing.Group(
    ExternalObjectSetReference
    | lexical_items.typereference("object_set_reference")
)

# 8.3
ExternalObjectClassReference <<= pyparsing.Group(
    lexical_items.modulereference
    + lexical_items.DOT
    + lexical_items.objectclassreference
)

ExternalObjectReference <<= pyparsing.Group(
    lexical_items.modulereference
    + lexical_items.DOT
    + lexical_items.valuereference("object_reference")
)

ExternalObjectSetReference <<= pyparsing.Group(
    lexical_items.modulereference
    + lexical_items.DOT
    + lexical_items.typereference("object_set_reference")
)

# 8.4
UsefulObjectClassReference <<= pyparsing.Group(
    pyparsing.Keyword("TYPE-IDENTIFIER")
    | pyparsing.Keyword("ABSTRACT-SYNTAX")
)

# ITU-T X.681 Section 9

ObjectClassDefn = pyparsing.Forward()
ParameterizedObjectClass = pyparsing.Forward()
FieldSpec = pyparsing.Forward()
WithSyntaxSpec = pyparsing.Forward()
SyntaxList = pyparsing.Forward()
TypeFieldSpec = pyparsing.Forward()
TypeOptionalitySpec = pyparsing.Forward()
FixedTypeValueFieldSpec = pyparsing.Forward()
ValueOptionalitySpec = pyparsing.Forward()
VariableTypeValueFieldSpec = pyparsing.Forward()
FixedTypeValueSetFieldSpec = pyparsing.Forward()
ValueSetOptionalitySpec = pyparsing.Forward()
VariableTypeValueSetFieldSpec = pyparsing.Forward()
ObjectFieldSpec = pyparsing.Forward()
ObjectOptionalitySpec = pyparsing.Forward()
ObjectSetFieldSpec = pyparsing.Forward()
ObjectSetOptionalitySpec = pyparsing.Forward()
PrimitiveFieldName = pyparsing.Forward()
FieldName = pyparsing.Forward()

# 9.1
ObjectClassAssignment = pyparsing.Group(
    lexical_items.objectclassreference("object_class_reference")
    + lexical_items.assignment
    + ObjectClass("object_class")
)

# 9.2
ObjectClass <<= pyparsing.Group(
    ObjectClassDefn
    | DefinedObjectClass
    | ParameterizedObjectClass
)

# 9.3
ObjectClassDefn <<= pyparsing.Group(
    pyparsing.Keyword("CLASS")
    + lexical_items.LBRACE
    + pyparsing.delimited_list(
        FieldSpec,
        delim=lexical_items.COMMA,
        min=1
    )
    + lexical_items.RBRACE
    + pyparsing.Optional(WithSyntaxSpec)
)

WithSyntaxSpec <<= pyparsing.Group(
    pyparsing.Keyword("WITH SYNTAX") + SyntaxList
)

# 9.4
FieldSpec <<= pyparsing.Forward(
    TypeFieldSpec
    | FixedTypeValueFieldSpec
    | VariableTypeValueFieldSpec
    | FixedTypeValueSetFieldSpec
    | VariableTypeValueSetFieldSpec
    | ObjectFieldSpec
    | ObjectSetFieldSpec
)

# 9.5
TypeFieldSpec <<= pyparsing.Group(
    lexical_items.typefieldreference
    + pyparsing.Optional(TypeOptionalitySpec)
)

TypeOptionalitySpec <<= pyparsing.Group(
    pyparsing.Keyword("OPTIONAL")
    | (pyparsing.Keyword("DEFAULT") + values_types.Type)
)

# 9.6
FixedTypeValueFieldSpec <<= pyparsing.Group(
    lexical_items.valuefieldreference
    + values_types.Type
    + pyparsing.Optional(pyparsing.Keyword("UNIQUE"))
    + pyparsing.Optional(ValueOptionalitySpec)
)

ValueOptionalitySpec <<= pyparsing.Group(
    pyparsing.Keyword("OPTIONAL")
    | (pyparsing.Keyword("DEFAULT") + values_types.Value)
)

# 9.8
VariableTypeValueFieldSpec <<= pyparsing.Group(
    lexical_items.valuefieldreference
    + FieldName
    + pyparsing.Optional(ValueOptionalitySpec)
)

# 9.9
FixedTypeValueSetFieldSpec <<= pyparsing.Group(
    lexical_items.typefieldreference("value_set_field_reference")
    + values_types.Type
    + pyparsing.Optional(ValueSetOptionalitySpec)
)

ValueSetOptionalitySpec <<= pyparsing.Group(
    pyparsing.Keyword("OPTIONAL")
    | (pyparsing.Keyword("DEFAULT") + values_types.ValueSet)
)

# 9.10
VariableTypeValueSetFieldSpec <<= pyparsing.Group(
    lexical_items.typefieldreference("value_set_field_reference")
    + FieldName
    + pyparsing.Optional(ValueSetOptionalitySpec)
)

# 9.11
ObjectFieldSpec <<= pyparsing.Group(
    lexical_items.valuefieldreference("object_field_reference")
    + DefinedObjectClass
    + pyparsing.Optional(ObjectOptionalitySpec)
)

ObjectOptionalitySpec <<= pyparsing.Group(
    pyparsing.Keyword("OPTIONAL")
    | (pyparsing.Keyword("DEFAULT") + Object)
)

# 9.12
ObjectSetFieldSpec <<= pyparsing.Group(
    lexical_items.typefieldreference("object_set_field_reference")
    + DefinedObjectClass
    + pyparsing.Optional(ObjectSetOptionalitySpec)
)

ObjectSetOptionalitySpec <<= pyparsing.Group(
    pyparsing.Keyword("OPTIONAL")
    | (pyparsing.Keyword("DEFAULT") + ObjectSet)
)

# 9.13
PrimitiveFieldName <<= pyparsing.Group(
    lexical_items.typefieldreference
    ^ lexical_items.valuefieldreference
)

# 9.14
FieldName <<= pyparsing.DelimitedList(
    PrimitiveFieldName,
    delim=lexical_items.DOT,
    min=1
)

# ITU-T X.681 Section 10

TokenOrGroupSpec = pyparsing.Forward()
OptionalGroup = pyparsing.Forward()
RequiredToken = pyparsing.Forward()
Literal = pyparsing.Forward()

# 10.5
SyntaxList <<= pyparsing.Group(
    lexical_items.LBRACE
    + pyparsing.OneOrMore(TokenOrGroupSpec)
    + lexical_items.RBRACE
)

TokenOrGroupSpec <<= pyparsing.Group(OptionalGroup | RequiredToken)

OptionalGroup <<= pyparsing.Group(
    lexical_items.LBRACK
    + pyparsing.OneOrMore(TokenOrGroupSpec)
    + lexical_items.RBRACK
)

RequiredToken <<= pyparsing.Group(
    Literal
    ^ PrimitiveFieldName
)

Literal <<= pyparsing.Group(
    lexical_items.word
    ^ ","
)

# ITU-T X.681 Section 11

ObjectDefn = pyparsing.Forward()
ObjectFromObject = pyparsing.Forward()
ParameterizedObject = pyparsing.Forward()
DefaultSyntax = pyparsing.Forward()
DefinedSyntax = pyparsing.Forward()
FieldSetting = pyparsing.Forward()
Setting = pyparsing.Forward()
DefinedSyntaxToken = pyparsing.Forward()

# 11.1
ObjectAssignment = pyparsing.Group(
    lexical_items.valuereference("object_reference")
    + DefinedObjectClass("defined_object_class")
    + lexical_items.assignment
    + Object("object")
)

# 11.3
Object <<= pyparsing.Group(
    DefinedObject("defined_object")
    | ObjectDefn("object_definition")
    | ObjectFromObject("object_from_object")
    | ParameterizedObject("parameterized_object")
)

# 11.4
ObjectDefn <<= pyparsing.Group(
    DefaultSyntax("default_syntax")
    | DefinedSyntax("defined_syntax")
)

# 11.5
DefaultSyntax <<= pyparsing.Group(
    lexical_items.LBRACE
    + pyparsing.Optional(pyparsing.delimited_list(
        FieldSetting,
        delim=lexical_items.COMMA,
        min=1
    ))("field_settings")
    + lexical_items.RBRACE
)

FieldSetting <<= pyparsing.Group(
    PrimitiveFieldName + Setting
)

# 11.6
DefinedSyntax <<= pyparsing.Group(
    lexical_items.LBRACE
    + pyparsing.ZeroOrMore(DefinedSyntaxToken)("tokens")
    + lexical_items.RBRACE
)

DefinedSyntaxToken <<= pyparsing.Group(
    Literal("literal")
    ^ Setting("setting")
)

# 11.7
Setting <<= pyparsing.Group(
    values_types.Type("type")
    | values_types.Value("value")
    | values_types.ValueSet("value_set")
    | Object("object")
    | ObjectSet("object_set")
)

# ITU-T X.681 Section 12

ObjectSetSpec = pyparsing.Forward()
ObjectSetElements = pyparsing.Forward()
ParameterizedObjectSet = pyparsing.Forward()

# 12.1
ObjectSetAssignment = pyparsing.Group(
    lexical_items.typereference("object_set_reference")
    + DefinedObjectClass
    + lexical_items.assignment
    + ObjectSet
)

# 12.3
ObjectSet <<= pyparsing.Group(
    lexical_items.LBRACE
    + ObjectSetSpec
    + lexical_items.RBRACE
)

ObjectSetSpec <<= pyparsing.Group(
    (constraints.RootElementSetSpec + lexical_items.COMMA + lexical_items.ellipsis + lexical_items.COMMA + constraints.AdditionalElementSetSpec)
    | (constraints.RootElementSetSpec + lexical_items.COMMA + lexical_items.ellipsis)
    | (lexical_items.ellipsis + lexical_items.COMMA + constraints.AdditionalElementSetSpec)
    | lexical_items.ellipsis
    | constraints.RootElementSetSpec
)

# 12.10
ObjectSetElements <<= pyparsing.Group(
    Object
    | DefinedObjectSet
    # | ObjectSetFromObjects
    | ParameterizedObjectSet
)

# ITU-T X.681 Section 14

OpenTypeFieldVal = pyparsing.Forward()
FixedTypeFieldVal = pyparsing.Forward()

# 14.1
ObjectClassFieldType = pyparsing.Group(
    DefinedObjectClass
    + lexical_items.DOT
    + FieldName
)

# 14.6
ObjectClassFieldValue = pyparsing.Group(
    FixedTypeFieldVal
    | OpenTypeFieldVal
)

OpenTypeFieldVal <<= pyparsing.Group(
    values_types.Type + lexical_items.COLON + values_types.Value
)

FixedTypeFieldVal <<= pyparsing.Group(
    values_types.BuiltinValue |
    values_types.ReferencedValue
)

# ITU-T X.681 Section 15

ReferencedObjects = pyparsing.Forward()

# 15.1
InformationFromObject = pyparsing.Group(
    ReferencedObjects
    + lexical_items.DOT
    + FieldName
)

ReferencedObjects <<= pyparsing.Group(
    DefinedObject
    | ParameterizedObject
    | DefinedObjectSet
    | ParameterizedObjectSet
)

# ITU-T X.681 Annex C

# C.2
InstanceOfType = pyparsing.Group(
    pyparsing.Keyword("INSTANCE OF") + DefinedObjectClass
)