import pyparsing
from . import lexical_items
from . import values_types
from . import constraints

# ITU-T X.681 Section 8

ExternalObjectClassReference = pyparsing.Forward()
ExternalObjectReference = pyparsing.Forward()
ExternalObjectSetReference = pyparsing.Forward()
UsefulObjectClassReference = pyparsing.Forward()

# 8.1
values_types.DefinedObjectClass <<= pyparsing.Group(
    ExternalObjectClassReference("external_class_reference")
    | lexical_items.objectclassreference("object_class_reference")
    | UsefulObjectClassReference("useful_object_class_reference")
)
values_types.DefinedObject <<= pyparsing.Group(
    ExternalObjectReference("external_object_reference")
    | lexical_items.valuereference("object_reference")
)
values_types.DefinedObjectSet <<= pyparsing.Group(
    ExternalObjectSetReference("external_object_set_reference")
    | lexical_items.typereference("object_set_reference")
)

# 8.3
ExternalObjectClassReference <<= pyparsing.Group(
    lexical_items.modulereference("module_reference")
    + lexical_items.DOT
    + lexical_items.objectclassreference("object_class_reference")
)

ExternalObjectReference <<= pyparsing.Group(
    lexical_items.modulereference("module_reference")
    + lexical_items.DOT
    + lexical_items.valuereference("object_reference")
)

ExternalObjectSetReference <<= pyparsing.Group(
    lexical_items.modulereference("module_reference")
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
    + values_types.ObjectClass("object_class")
)

# 9.2
values_types.ObjectClass <<= pyparsing.Group(
    ParameterizedObjectClass("parameterized_object_class")
    | ObjectClassDefn("object_class_defn")
    | values_types.DefinedObjectClass("defined_object_class")
)

# 9.3
ObjectClassDefn <<= pyparsing.Group(
    pyparsing.Keyword("CLASS")
    + lexical_items.LBRACE
    + pyparsing.delimited_list(
        FieldSpec,
        delim=lexical_items.COMMA,
        min=1
    )("field_spec")
    + lexical_items.RBRACE
    + pyparsing.Optional(WithSyntaxSpec("with_syntax"))
)

WithSyntaxSpec <<= pyparsing.Group(
    pyparsing.Keyword("WITH SYNTAX") + SyntaxList("syntax")
)

# 9.4
FieldSpec <<= pyparsing.Group(
    TypeFieldSpec("type_field")
    | FixedTypeValueFieldSpec("fixed_type_value_field")
    | VariableTypeValueFieldSpec("variable_type_value_field")
    | FixedTypeValueSetFieldSpec("fixed_type_value_set_field")
    | VariableTypeValueSetFieldSpec("variable_type_value_set_field")
    | ObjectFieldSpec("object_field")
    | ObjectSetFieldSpec("object_set_field")
)

# 9.5
TypeFieldSpec <<= pyparsing.Group(
    lexical_items.typefieldreference("reference")
    + pyparsing.Optional(TypeOptionalitySpec("optionality"))
)

TypeOptionalitySpec <<= pyparsing.Group(
    pyparsing.Keyword("OPTIONAL")("optional")
    | (pyparsing.Keyword("DEFAULT") + values_types.Type("default"))
)

# 9.6
FixedTypeValueFieldSpec <<= pyparsing.Group(
    lexical_items.valuefieldreference("reference")
    + values_types.Type("type")
    + pyparsing.Optional(pyparsing.Keyword("UNIQUE")("unique"))
    + pyparsing.Optional(ValueOptionalitySpec("optionality"))
)

ValueOptionalitySpec <<= pyparsing.Group(
    pyparsing.Keyword("OPTIONAL")("optional")
    | (pyparsing.Keyword("DEFAULT") + values_types.Value("default"))
)

# 9.8
VariableTypeValueFieldSpec <<= pyparsing.Group(
    lexical_items.valuefieldreference("reference")
    + FieldName("field_name")
    + pyparsing.Optional(ValueOptionalitySpec)
)

# 9.9
FixedTypeValueSetFieldSpec <<= pyparsing.Group(
    lexical_items.typefieldreference("reference")
    + values_types.Type
    + pyparsing.Optional(ValueSetOptionalitySpec)
)

ValueSetOptionalitySpec <<= pyparsing.Group(
    pyparsing.Keyword("OPTIONAL")
    | (pyparsing.Keyword("DEFAULT") + values_types.ValueSet)
)

# 9.10
VariableTypeValueSetFieldSpec <<= pyparsing.Group(
    lexical_items.typefieldreference("reference")
    + FieldName("field_name")
    + pyparsing.Optional(ValueSetOptionalitySpec)
)

# 9.11
ObjectFieldSpec <<= pyparsing.Group(
    lexical_items.valuefieldreference("reference")
    + values_types.DefinedObjectClass
    + pyparsing.Optional(ObjectOptionalitySpec)
)

ObjectOptionalitySpec <<= pyparsing.Group(
    pyparsing.Keyword("OPTIONAL")
    | (pyparsing.Keyword("DEFAULT") + values_types.Object)
)

# 9.12
ObjectSetFieldSpec <<= pyparsing.Group(
    lexical_items.typefieldreference("reference")
    + values_types.DefinedObjectClass
    + pyparsing.Optional(ObjectSetOptionalitySpec)
)

ObjectSetOptionalitySpec <<= pyparsing.Group(
    pyparsing.Keyword("OPTIONAL")
    | (pyparsing.Keyword("DEFAULT") + values_types.ObjectSet)
)

# 9.13
PrimitiveFieldName <<= pyparsing.Group(
    lexical_items.typefieldreference("type_field_reference")
    ^ lexical_items.valuefieldreference("value_field_reference")
)

# 9.14
FieldName <<= pyparsing.Group(pyparsing.DelimitedList(
    PrimitiveFieldName,
    delim=lexical_items.DOT,
    min=1
))

# ITU-T X.681 Section 10

TokenOrGroupSpec = pyparsing.Forward()
OptionalGroup = pyparsing.Forward()
RequiredToken = pyparsing.Forward()
Literal = pyparsing.Forward()

# 10.5
SyntaxList <<= pyparsing.Group(
    lexical_items.LBRACE
    + pyparsing.OneOrMore(TokenOrGroupSpec)("token_or_groups")
    + lexical_items.RBRACE
)

TokenOrGroupSpec <<= pyparsing.Group(
    OptionalGroup("optional_group")
    | RequiredToken("required_token")
)

OptionalGroup <<= pyparsing.Group(
    lexical_items.LBRACK
    + pyparsing.OneOrMore(TokenOrGroupSpec)("token_or_groups")
    + lexical_items.RBRACK
)

RequiredToken <<= pyparsing.Group(
    Literal("literal")
    ^ PrimitiveFieldName("field_name")
)

Literal <<= pyparsing.Combine(
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
    + values_types.DefinedObjectClass("object_class")
    + lexical_items.assignment
    + values_types.Object("object")
)

# 11.3
values_types.Object <<= pyparsing.Group(
    values_types.DefinedObject("defined_object")
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
    PrimitiveFieldName("field_name") + Setting("setting")
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
    values_types.Value("value")
    | values_types.Type("type")
    | values_types.ValueSet("value_set")
    | values_types.Object("object")
    | values_types.ObjectSet("object_set")
)

# ITU-T X.681 Section 12

ObjectSetSpec = pyparsing.Forward()
ParameterizedObjectSet = pyparsing.Forward()

# 12.1
ObjectSetAssignment = pyparsing.Group(
    lexical_items.typereference("object_set_reference")
    + values_types.DefinedObjectClass("object_class")
    + lexical_items.assignment
    + values_types.ObjectSet("object_set")
)

# 12.3
values_types.ObjectSet <<= pyparsing.Group(
    lexical_items.LBRACE
    + ObjectSetSpec("spec")
    + lexical_items.RBRACE
)

ObjectSetSpec <<= pyparsing.Group(
    (constraints.ElementSetSpec("root_element_spec") + lexical_items.COMMA + lexical_items.ellipsis("extensible") + lexical_items.COMMA + constraints.ElementSetSpec)
    | (constraints.ElementSetSpec("root_element_spec") + lexical_items.COMMA + lexical_items.ellipsis("extensible"))
    | constraints.ElementSetSpec("root_element_spec")
    | (lexical_items.ellipsis("extensible") + lexical_items.COMMA + constraints.ElementSetSpec)
    | lexical_items.ellipsis("extensible")
)

# 12.10
values_types.ObjectSetElements <<= pyparsing.Group(
    values_types.Object("object")
    | ParameterizedObjectSet("parameterised_object_set")
    | values_types.DefinedObjectSet("defined_object_set")
    # | ObjectSetFromObjects
)

# ITU-T X.681 Section 14

OpenTypeFieldVal = pyparsing.Forward()
FixedTypeFieldVal = pyparsing.Forward()

# 14.1
ObjectClassFieldType = pyparsing.Group(
    values_types.DefinedObjectClass("object_class")
    + lexical_items.DOT
    + FieldName("field_name")
)

# 14.6
ObjectClassFieldValue = pyparsing.Group(
    values_types.Type + lexical_items.COLON + values_types.Value
)

# ITU-T X.681 Section 15

ReferencedObjects = pyparsing.Forward()

# 15.1
InformationFromObject = pyparsing.Group(
    ReferencedObjects("referenced_objects")
    + lexical_items.DOT
    + FieldName("field_name")
)

ReferencedObjects <<= pyparsing.Group(
    values_types.DefinedObject("defined_object")
    | ParameterizedObject("parameterized_object")
    | values_types.DefinedObjectSet("defined_object_set")
    | ParameterizedObjectSet("parameterized_object_set")
)

# ITU-T X.681 Annex C

# C.2
InstanceOfType = pyparsing.Group(
    pyparsing.Keyword("INSTANCE OF") + values_types.DefinedObjectClass
)