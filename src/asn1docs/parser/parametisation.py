import pyparsing
from . import lexical_items
from . import values_types
from . import object_class

# ITU-T X.683 Section 8

ParameterizedTypeAssignment = pyparsing.Forward()
ParameterizedValueAssignment = pyparsing.Forward()
ParameterizedValueSetTypeAssignment = pyparsing.Forward()
ParameterizedObjectClassAssignment = pyparsing.Forward()
ParameterizedObjectAssignment = pyparsing.Forward()
ParameterizedObjectSetAssignment = pyparsing.Forward()
ParameterList = pyparsing.Forward()
Parameter = pyparsing.Forward()
ParamGovernor = pyparsing.Forward()

# 8.1
ParameterizedAssignment = pyparsing.Group(
    ParameterizedTypeAssignment("type_assignment")
    | ParameterizedValueAssignment("value_assignment")
    | ParameterizedValueSetTypeAssignment("value_set_assignment")
    | ParameterizedObjectClassAssignment("object_class_assignment")
    | ParameterizedObjectAssignment("object_assignment")
    | ParameterizedObjectSetAssignment("object_set_assignment")
)

# 8.2
ParameterizedTypeAssignment <<= pyparsing.Group(
    lexical_items.typereference("type_reference")
    + ParameterList("parameters")
    + lexical_items.assignment
    + values_types.Type("type")
)

ParameterizedValueAssignment <<= pyparsing.Group(
    lexical_items.valuereference("value_reference")
    + ParameterList("parameters")
    + values_types.Type("type")
    + lexical_items.assignment
    + values_types.Value("value")
)

ParameterizedValueSetTypeAssignment <<= pyparsing.Group(
    lexical_items.valuereference("value_set_reference")
    + ParameterList("parameters")
    + values_types.Type("type")
    + lexical_items.assignment
    + values_types.ValueSet("value")
)

ParameterizedObjectClassAssignment <<= pyparsing.Group(
    lexical_items.objectclassreference("object_class_reference")
    + ParameterList("parameters")
    + lexical_items.assignment
    + values_types.ObjectClass("object_class")
)

ParameterizedObjectAssignment <<= pyparsing.Group(
    lexical_items.valuereference("object_reference")
    + ParameterList("parameters")
    + values_types.DefinedObjectClass("object_class")
    + lexical_items.assignment
    + values_types.Object("object")
)

ParameterizedObjectSetAssignment <<= pyparsing.Group(
    lexical_items.typereference("object_set_reference")
    + ParameterList("parameters")
    + values_types.DefinedObjectClass("object_class")
    + lexical_items.assignment
    + values_types.ObjectSet("object_set")
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
ParamGovernor <<= pyparsing.Group(values_types.Governor("governor") | values_types.Reference("dummy_reference"))
values_types.Governor <<= pyparsing.Group(
    values_types.Type("type")
    | values_types.DefinedObjectClass
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

object_class.ParameterizedObjectClass <<= pyparsing.Group(
    values_types.DefinedObjectClass
    + ActualParameterList
)

object_class.ParameterizedObjectSet <<= pyparsing.Group(
    values_types.DefinedObjectSet
    + ActualParameterList
)

object_class.ParameterizedObject <<= pyparsing.Group(
    values_types.DefinedObject
    + ActualParameterList
)

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
    | values_types.DefinedObjectClass("object_class")
    | values_types.Object("object")
    | values_types.ObjectSet("object_set")
)