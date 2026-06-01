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
    | pyparsing.Group(pyparsing.Keyword("SET") + Constraint("constraint") + pyparsing.Keyword("OF") + values_types.Type("type"))("set_of_type")
    | pyparsing.Group(pyparsing.Keyword("SEQUENCE") + SizeConstraint("size_constraint") + pyparsing.Keyword("OF") + values_types.Type("type"))("size_sequence_of_type")
    | pyparsing.Group(pyparsing.Keyword("SEQUENCE") + Constraint("constraint") + pyparsing.Keyword("OF") + values_types.Type("type"))("sequence_of_type")
    # ^ (pyparsing.Keyword("SET") + Constraint + pyparsing.Keyword("OF") + values_types.NamedType)
    # ^ (pyparsing.Keyword("SET") + SizeConstraint + pyparsing.Keyword("OF") + values_types.NamedType)
    # ^ (pyparsing.Keyword("SEQUENCE") + Constraint + pyparsing.Keyword("OF") + values_types.NamedType)
    # ^ (pyparsing.Keyword("SEQUENCE") + SizeConstraint + pyparsing.Keyword("OF") + values_types.NamedType)
)

# 49.6
Constraint <<= pyparsing.Group(
    lexical_items.LPAR + ConstraintSpec("constraint_spec") + values_types.ExceptionSpec + lexical_items.RPAR
)

ConstraintSpec <<= pyparsing.Group(
    ElementSetSpecs("subtype_constraint")
    # ^ GeneralConstraint("general_constraint")
)

# ITU-T X.680 Section 50

RootElementSetSpec = pyparsing.Forward()
ElementSetSpec = pyparsing.Forward()
AdditionalElementSetSpec = pyparsing.Forward()
Unions = pyparsing.Forward()
Intersections = pyparsing.Forward()
IntersectionElements = pyparsing.Forward()
Exclusions = pyparsing.Forward()
UnionMark = pyparsing.Forward()
IntersectionMark = pyparsing.Forward()
Elements = pyparsing.Forward()
SubtypeElements = pyparsing.Forward()
ObjectSetElements = pyparsing.Forward()

# 50.1
ElementSetSpecs <<= pyparsing.Group(
    (ElementSetSpec + lexical_items.COMMA + lexical_items.ellipsis + lexical_items.COMMA + ElementSetSpec)
    | (ElementSetSpec + lexical_items.COMMA + lexical_items.ellipsis)
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
    pyparsing.Keyword("EXCEPT") + Elements
)

UnionMark <<= "|" | pyparsing.Keyword("UNION")

IntersectionMark <<= "^" | pyparsing.Keyword("INTERSECTION")

# 50.6
Elements <<= pyparsing.Group(
    (lexical_items.LPAR + ElementSetSpec + lexical_items.RPAR)
    | SubtypeElements("subtype_elements")
    # ^ ObjectSetElements
)

# ITU-T X.680 Section 51

# 51.1
SubtypeElements <<= pyparsing.Group(
    SizeConstraint("size_constraint")
    | ValueRange("value_range")
    | SingleValue("single_value")
    | PermittedAlphabet("permitted_alphabet")
    # ^ ContainedSubtype
    # ^ TypeConstraint
    # ^ InnerTypeConstraints
    # ^ PatternConstraint
    # ^ PropertySettings
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
    (pyparsing.Keyword("WITH COMPONENT") + SingleTypeConstraint)
    | (pyparsing.Keyword("WITH COMPONENTS") + MultipleTypeConstraints)
)

# 51.8.4
SingleTypeConstraint <<= Constraint

# 51.8.5
MultipleTypeConstraints <<= pyparsing.Group(
    FullSpecification
    | PartialSpecification
)

FullSpecification <<= pyparsing.Group(
    lexical_items.LBRACE + TypeConstraints + lexical_items.RBRACE
)

PartialSpecification <<= pyparsing.Group(
    lexical_items.LBRACE + lexical_items.ellipsis + lexical_items.COMMA + TypeConstraints + lexical_items.RBRACE
)

TypeConstraints <<= pyparsing.Group(pyparsing.DelimitedList(
    NamedConstraint,
    delim=lexical_items.COMMA,
    min=1
))

NamedConstraint <<= pyparsing.Group(
    lexical_items.identifier + ComponentConstraint
)

# 51.8.8
ComponentConstraint <<= pyparsing.Group(
    pyparsing.Optional(Constraint) + pyparsing.Optional(PresenceConstraint)
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