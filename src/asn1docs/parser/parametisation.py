import pyparsing
from . import lexical_items
from . import values_types

# ITU-T X.683 Section 8

ParameterizedTypeAssignment = pyparsing.Forward()
ParameterizedValueAssignment = pyparsing.Forward()
ParameterizedValueSetTypeAssignment = pyparsing.Forward()
# TODO: ITU-T X.681
# ParameterizedObjectClassAssignment = pyparsing.Forward()
# ParameterizedObjectAssignment = pyparsing.Forward()
# ParameterizedObjectSetAssignment = pyparsing.Forward()
ParameterList = pyparsing.Forward()
Parameter = pyparsing.Forward()
ParamGovernor = pyparsing.Forward()
Governor = pyparsing.Forward()

# 8.1
ParameterizedAssignment = pyparsing.Group(
    ParameterizedTypeAssignment("type_assignment")
    | ParameterizedValueAssignment
    | ParameterizedValueSetTypeAssignment
    # | ParameterizedObjectClassAssignment
    # | ParameterizedObjectAssignment
    # | ParameterizedObjectSetAssignment
)

# 8.2
ParameterizedTypeAssignment <<= pyparsing.Group(
    lexical_items.typereference("type_reference")
    + ParameterList("parameters")
    + lexical_items.assignment
    + values_types.Type("type")
)

ParameterizedValueAssignment <<= pyparsing.Group(
    lexical_items.valuereference
    + ParameterList
    + values_types.Type
    + lexical_items.assignment
    + values_types.Value
)

ParameterizedValueSetTypeAssignment <<= pyparsing.Group(
    lexical_items.valuereference
    + ParameterList
    + values_types.Type
    + lexical_items.assignment
    + values_types.ValueSet
)

# 8.3
ParameterList <<= pyparsing.Group(
    lexical_items.LBRACE
    + pyparsing.delimited_list(
        Parameter,
        delim=lexical_items.COMMA,
        min=1
    )("parameters")
    + lexical_items.RBRACE
)

Parameter <<= pyparsing.Group(
    (ParamGovernor("governor") + lexical_items.COLON + values_types.Reference("dummy_reference"))
    | values_types.Reference("dummy_reference")
)
ParamGovernor <<= pyparsing.Group(Governor("governor") | values_types.Reference("dummy_reference"))
Governor <<= pyparsing.Group(
    values_types.Type("type")
    # TODO: ITU-T X.681
    # | DefinedObjectClass
)

# ITU-T X.683 Section 9

SimpleDefinedType = pyparsing.Forward()
SimpleDefinedValue = pyparsing.Forward()
ActualParameterList = pyparsing.Forward()

# 9.2
values_types.ParameterizedType <<= pyparsing.Group(
    SimpleDefinedType("simple_defined_type")
    + ActualParameterList("parameter_list")
)

SimpleDefinedType <<= pyparsing.Group(
    values_types.ExternalTypeReference("external_type_reference")
    | lexical_items.typereference("type_reference")
)

values_types.ParameterizedValue <<= pyparsing.Group(
    SimpleDefinedValue("simple_defined_value")
    + ActualParameterList("parameter_list")
)

SimpleDefinedValue <<= pyparsing.Group(
    values_types.ExternalValueReference("external_type_reference")
    | lexical_items.valuereference("type_reference")
)

# TODO: ITU-T X.681
# ParameterizedObjectClass <<= pyparsing.Group(
#     DefinedObjectClass
#     + ActualParameterList
# )
#
# ParameterizedObjectSet <<= pyparsing.Group(
#     DefinedObjectSet
#     + ActualParameterList
# )
#
# ParameterizedObject <<= pyparsing.Group(
#     DefinedObject
#     + ActualParameterList
# )

# 9.5

ActualParameter = pyparsing.Forward()

ActualParameterList <<= pyparsing.Group(
    lexical_items.LBRACE
    + pyparsing.delimited_list(
        ActualParameter,
        delim=lexical_items.COMMA,
        min=1
    )("parameters")
    + lexical_items.RBRACE
)

ActualParameter <<= pyparsing.Group(
    values_types.Type("type")
    | values_types.Value("value")
    | values_types.ValueSet("value_set")
    # | DefinedObjectClass
    # | Object
    # | ObjectSet
)