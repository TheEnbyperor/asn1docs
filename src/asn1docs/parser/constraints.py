import pyparsing
from . import lexical_items
from . import values_types

Constraint = pyparsing.Forward()
SizeConstraint = pyparsing.Forward()
TypeWithConstraint = pyparsing.Forward()
ConstraintSpec = pyparsing.Forward()
GeneralConstraint = pyparsing.Forward()
ElementSetSpecs = pyparsing.Forward()
SingleValue = pyparsing.Forward()
ContainedSubtype = pyparsing.Forward()
ValueRange = pyparsing.Forward()
TypeConstraint = pyparsing.Forward()
PermittedAlphabet = pyparsing.Forward()
InnerTypeConstraints = pyparsing.Forward()
PatternConstraint = pyparsing.Forward()
PropertySettings = pyparsing.Forward()
Includes = pyparsing.Forward()
LowerEndpoint = pyparsing.Forward()
UpperEndpoint = pyparsing.Forward()
LowerEndValue = pyparsing.Forward()
UpperEndValue = pyparsing.Forward()
SingleTypeConstraint = pyparsing.Forward()
MultipleTypeConstraints = pyparsing.Forward()
FullSpecification = pyparsing.Forward()
PartialSpecification = pyparsing.Forward()
TypeConstraints = pyparsing.Forward()
NamedConstraint = pyparsing.Forward()
ComponentConstraint = pyparsing.Forward()
ValueConstraint = pyparsing.Forward()
PresenceConstraint = pyparsing.Forward()


# ITU-T X.680 Section 49

# 49.1
ConstrainedType = pyparsing.Group(
    TypeWithConstraint("type_of_with_constraint")
    | pyparsing.Group(values_types.UnconstrainedType("inner_type") + Constraint("constraint"))("constrained_type")
)

# 49.5
TypeWithConstraint <<= pyparsing.Group(
    pyparsing.Group(pyparsing.Keyword("SET") + SizeConstraint("size_constraint") + pyparsing.Keyword("OF") + values_types.Type("type"))("size_set_of_type")
    | pyparsing.Group(pyparsing.Keyword("SET") + SizeConstraint + pyparsing.Keyword("OF") + values_types.NamedType("named_type"))("size_set_of_type")
    | pyparsing.Group(pyparsing.Keyword("SET") + Constraint("constraint") + pyparsing.Keyword("OF") + values_types.Type("type"))("set_of_type")
    | pyparsing.Group(pyparsing.Keyword("SET") + Constraint("constraint") + pyparsing.Keyword("OF") + values_types.NamedType("named_type"))("set_of_type")
    | pyparsing.Group(pyparsing.Keyword("SEQUENCE") + SizeConstraint("size_constraint") + pyparsing.Keyword("OF") + values_types.Type("type"))("size_sequence_of_type")
    | pyparsing.Group(pyparsing.Keyword("SEQUENCE") + SizeConstraint("size_constraint") + pyparsing.Keyword("OF") + values_types.NamedType("named_type"))("size_sequence_of_type")
    | pyparsing.Group(pyparsing.Keyword("SEQUENCE") + Constraint("constraint") + pyparsing.Keyword("OF") + values_types.Type("type"))("sequence_of_type")
    | pyparsing.Group((pyparsing.Keyword("SEQUENCE") + Constraint("constraint") + pyparsing.Keyword("OF") + values_types.NamedType("named_type")))("sequence_of_type")
)

# 49.6
Constraint <<= pyparsing.Group(
    lexical_items.LPAR + ConstraintSpec("constraint_spec") + values_types.ExceptionSpec + lexical_items.RPAR
)

ConstraintSpec <<= pyparsing.Group(
    GeneralConstraint("general_constraint")
    | ElementSetSpecs("subtype_constraint")
)

# ITU-T X.680 Section 50

ElementSetSpec = pyparsing.Forward()
Unions = pyparsing.Forward()
Intersections = pyparsing.Forward()
IntersectionElements = pyparsing.Forward()
Exclusions = pyparsing.Forward()
UnionMark = pyparsing.Forward()
IntersectionMark = pyparsing.Forward()
Elements = pyparsing.Forward()
SubtypeElements = pyparsing.Forward()

# 50.1
ElementSetSpecs <<= pyparsing.Group(
    (ElementSetSpec("basic_constraint") + lexical_items.COMMA + lexical_items.ellipsis("extended") + lexical_items.COMMA + ElementSetSpec("extended_constraint"))
    | (ElementSetSpec("basic_constraint") + lexical_items.COMMA + lexical_items.ellipsis("extensible"))
    | ElementSetSpec("basic_constraint")
)

ElementSetSpec <<= pyparsing.Group(
    (pyparsing.Keyword("ALL") + Exclusions("exclusions"))
    | Unions("unions")
)

Unions <<= pyparsing.Group(
    (Intersections("intersections_union_with") + UnionMark + Unions("unions"))
    | Intersections("intersections")
)

Intersections <<= pyparsing.Group(
    (IntersectionElements("intersection_elements_intersection_with") + IntersectionMark + Intersections("intersections"))
    | IntersectionElements("intersection_elements")
)

IntersectionElements <<= pyparsing.Group(
    (Elements("elements") + Exclusions("exclusions"))
    | Elements("elements")
)

Exclusions <<= pyparsing.Group(
    pyparsing.Keyword("EXCEPT") + Elements("elements")
)

UnionMark <<= "|" | pyparsing.Keyword("UNION")

IntersectionMark <<= "^" | pyparsing.Keyword("INTERSECTION")

# 50.6
Elements <<= pyparsing.Group(
    (lexical_items.LPAR + ElementSetSpec("element_set_spec") + lexical_items.RPAR)
    | SubtypeElements("subtype_elements")
    | values_types.ObjectSetElements("object_set_elements")
)

# ITU-T X.680 Section 51

# 51.1
SubtypeElements <<= pyparsing.Group(
    SizeConstraint("size_constraint")
    | ValueRange("value_range")
    | SingleValue("single_value")
    | PermittedAlphabet("permitted_alphabet")
    | InnerTypeConstraints("inner_type_constraints")
    | PatternConstraint("pattern")
    | PropertySettings("property_settings")
    # ^ ContainedSubtype
    # ^ TypeConstraint
)

# 51.2.1
SingleValue <<= values_types.Value

# 51.3.1
ContainedSubtype <<= pyparsing.Group(
    Includes + values_types.Type
)

Includes <<= (pyparsing.Keyword("INCLUDES") | lexical_items.empty)

# 51.4.1
ValueRange <<= pyparsing.Group(
    LowerEndpoint("lower_endpoint") + lexical_items.range_separator + UpperEndpoint("upper_endpoint")
)

# 51.4.3
LowerEndpoint <<= pyparsing.Group(
    (LowerEndValue("exc_lower_end_value") + lexical_items.LANGLE)
    | LowerEndValue("inc_lower_end_value")
)

UpperEndpoint <<= pyparsing.Group(
    (lexical_items.LANGLE + UpperEndValue("exc_upper_end_value"))
    | UpperEndValue("inc_upper_end_value")
)

# 51.4.4
LowerEndValue <<= pyparsing.Group(
    pyparsing.Keyword("MIN")("min")
    | values_types.Value("value")
)

UpperEndValue <<= pyparsing.Group(
    pyparsing.Keyword("MAX")("max")
    | values_types.Value("value")
)

# 51.5.1
SizeConstraint <<= pyparsing.Group(
    pyparsing.Keyword("SIZE") + Constraint("constraint")
)

# 51.6.1
TypeConstraint <<= values_types.Type

# 51.7.1
PermittedAlphabet <<= pyparsing.Group(
    pyparsing.Keyword("FROM") + Constraint("constraint")
)

# 51.8.1
InnerTypeConstraints <<= pyparsing.Group(
    (pyparsing.Keyword("WITH COMPONENT") + Constraint("single_type_constraint"))
    | (pyparsing.Keyword("WITH COMPONENTS") + MultipleTypeConstraints("multiple_type_constraints"))
)

# 51.8.5
MultipleTypeConstraints <<= pyparsing.Group(
    PartialSpecification("partial_specification")
    | FullSpecification("full_specification")
)

FullSpecification <<= pyparsing.Group(
    lexical_items.LBRACE + TypeConstraints("type_constraints") + lexical_items.RBRACE
)

PartialSpecification <<= pyparsing.Group(
    lexical_items.LBRACE + lexical_items.ellipsis + lexical_items.COMMA + TypeConstraints("type_constraints") + lexical_items.RBRACE
)

TypeConstraints <<= pyparsing.Group(pyparsing.DelimitedList(
    NamedConstraint,
    delim=lexical_items.COMMA,
    min=1
))

NamedConstraint <<= pyparsing.Group(
    lexical_items.identifier("name") + ComponentConstraint("component_constraint")
)

# 51.8.8
ComponentConstraint <<= pyparsing.Group(
    pyparsing.Optional(Constraint)("constraint") + pyparsing.Optional(PresenceConstraint)("presence_constraint")
)

# 51.8.9
ValueConstraint <<= pyparsing.Group(
    pyparsing.Optional(Constraint)
)

# 51.8.10
PresenceConstraint <<= pyparsing.Group(
    pyparsing.Keyword("PRESENT") | pyparsing.Keyword("ABSENT") | pyparsing.Keyword("OPTIONAL")
)

# 51.9.1
PatternConstraint <<= pyparsing.Group(
    pyparsing.Keyword("PATTERN") + values_types.Value
)

# 51.10.1
PropertySettings <<= pyparsing.Group(
    pyparsing.Keyword("SETTINGS") + lexical_items.simplestring
)

# ITU-T X.682 Section 8

ContentsConstraint = pyparsing.Forward()
UserDefinedConstraint = pyparsing.Forward()
TableConstraint = pyparsing.Forward()

# 8.1
GeneralConstraint <<= pyparsing.Group(
    TableConstraint("table_constraint")
    | UserDefinedConstraint("user_defined_constraint")
    | ContentsConstraint("contents_constraint")
)

# ITU-T X.682 Section 9

UserDefinedConstraintParameter = pyparsing.Forward()

# 9.1
UserDefinedConstraint <<= pyparsing.Group(
    pyparsing.Keyword("CONSTRAINED BY")
    + lexical_items.LBRACE
    + pyparsing.Optional(pyparsing.delimited_list(
        UserDefinedConstraintParameter,
        delim=lexical_items.COMMA,
        min=1
    ))
    + lexical_items.RBRACE
)

# 9.3
UserDefinedConstraintParameter <<= pyparsing.Group(
    (values_types.Governor + lexical_items.COLON + values_types.Object)
    | (values_types.Governor + lexical_items.COLON + values_types.Value)
    | values_types.DefinedObjectSet
    | values_types.DefinedObjectClass
)

# ITU-T X.682 Section 10

ComponentRelationConstraint = pyparsing.Forward()
AtNotation = pyparsing.Forward()

# 10.3
TableConstraint <<= pyparsing.Group(
    ComponentRelationConstraint("component_relation_constraint")
    | values_types.ObjectSet("simple_table_constraint")
)

# 10.7
ComponentRelationConstraint <<= pyparsing.Group(
    lexical_items.LBRACE
    + values_types.DefinedObjectSet("defined_object_set")
    + lexical_items.RBRACE
    + lexical_items.LBRACE
    + pyparsing.delimited_list(
        AtNotation,
        delim=lexical_items.COMMA,
        min=1
    )("at_notation")
    + lexical_items.RBRACE
)

AtNotation <<= pyparsing.Group(
    lexical_items.AT
    + pyparsing.ZeroOrMore(lexical_items.DOT)("dots")
    + pyparsing.delimited_list(
        lexical_items.identifier,
        delim=lexical_items.DOT,
        min=1
    )("identifiers")
)

# ITU-T X.682 Section 11

# 11.1
ContentsConstraint <<= pyparsing.Group(
    (pyparsing.Keyword("CONTAINING") + values_types.Type("type") + pyparsing.Keyword("ENCODED BY") + values_types.Value("encoded_by"))
    | (pyparsing.Keyword("CONTAINING") + values_types.Type("type"))
    | (pyparsing.Keyword("ENCODED BY") + values_types.Value("encoded_by"))
)