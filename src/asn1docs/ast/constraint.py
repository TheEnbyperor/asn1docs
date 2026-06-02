import enum
import typing
import dataclasses
import pyparsing
from . import value, util, module


Constraint = typing.Union[
    "ValueRange", "SingleValue", "SizeConstraint", "PermittedAlphabetConstraint", "SingleInnerType", "MultipleInnerType",
    "ConstraintUnion", "ConstraintIntersection", "ConstraintExclusion", "ConstraintInverse"
]

@dataclasses.dataclass
class SingleValue:
    CONSTRAINT_TYPE = "SINGLE_VALUE"

    value: "value.Value"


@dataclasses.dataclass
class ValueRange:
    CONSTRAINT_TYPE = "VALUE_RANGE"

    min: typing.Optional["value.Value"] = None
    max: typing.Optional["value.Value"] = None
    min_inclusive: bool = True
    max_inclusive: bool = True

    @classmethod
    def build(
            cls, constraint_def: pyparsing.ParseResults,
            parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
    ) -> "ValueRange":
        if constraint_def.lower_endpoint.inc_lower_end_value:
            if constraint_def.lower_endpoint.inc_lower_end_value.value:
                min_val = value.build_value(constraint_def.lower_endpoint.inc_lower_end_value.value, parameters)
            else:
                min_val = None
            min_inclusive = True
        elif constraint_def.lower_endpoint.exc_lower_end_value:
            if constraint_def.lower_endpoint.exc_lower_end_value.value:
                min_val = value.build_value(constraint_def.lower_endpoint.exc_lower_end_value.value, parameters)
            else:
                min_val = None
            min_inclusive = False
        else:
            util.assert_never(constraint_def.lower_endpoint)
        if constraint_def.upper_endpoint.inc_upper_end_value:
            if constraint_def.upper_endpoint.inc_upper_end_value.value:
                max_val = value.build_value(constraint_def.upper_endpoint.inc_upper_end_value.value, parameters)
            else:
                max_val = None
            max_inclusive = True
        elif constraint_def.upper_endpoint.exc_upper_end_value:
            if constraint_def.upper_endpoint.exc_upper_end_value.value:
                max_val = value.build_value(constraint_def.upper_endpoint.exc_upper_end_value.value, parameters)
            else:
                max_val = None
            max_inclusive = False
        else:
            util.assert_never(constraint_def.upper_endpoint)

        return cls(
            min=min_val,
            min_inclusive=min_inclusive,
            max=max_val,
            max_inclusive=max_inclusive,
        )


@dataclasses.dataclass
class SizeConstraint:
    CONSTRAINT_TYPE = "SIZE_CONSTRAINT"

    length_range: typing.Union[ValueRange, SingleValue]

    @classmethod
    def build(
            cls, constraint_def: pyparsing.ParseResults,
            parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
    ) -> "SizeConstraint":
        constraint_spec = constraint_def.constraint[0].constraint_spec
        if constraint_spec.general_constraint:
            raise SyntaxError(f"General constraint invalid in a size constraint")
        inner_constraint = build_constraint(constraint_spec, parameters)
        if isinstance(inner_constraint, ValueRange):
            if inner_constraint.min:
                if isinstance(inner_constraint.min, value.Integer):
                    if (inner_constraint.min_inclusive and inner_constraint.min.value < 0) or (
                            not inner_constraint.min_inclusive and inner_constraint.min.value < -1):
                        raise SyntaxError(f"Size constraint minimum value cannot be negative")
                elif not isinstance(inner_constraint.min_inclusive, value.Reference):
                    raise SyntaxError(f"Size constraint minimum value is not an integer")
            if inner_constraint.max and not isinstance(inner_constraint.max, value.Integer) \
                    and not isinstance(inner_constraint.max, value.Reference):
                raise SyntaxError(f"Size constraint maximum value is not an integer")
        elif isinstance(inner_constraint, SingleValue):
            if isinstance(inner_constraint.value, value.Integer):
                if inner_constraint.value.value < 0:
                    raise SyntaxError(f"Size constraint value cannot be negative")
            elif not isinstance(inner_constraint.value, value.Reference):
                raise SyntaxError(f"Size constraint value is not an integer")
        else:
            raise SyntaxError(f"Size constraint inner constraint is not suitable: {inner_constraint}")
        return cls(
            length_range=inner_constraint
        )


@dataclasses.dataclass
class PermittedAlphabetConstraint:
    CONSTRAINT_TYPE = "PERMITTED_ALPHABET"

    alphabet: Constraint


@dataclasses.dataclass
class SingleInnerType:
    CONSTRAINT_TYPE = "SINGLE_INNER_TYPE"

    constraint: Constraint

class Presence(enum.Enum):
    Present = enum.auto()
    Absent = enum.auto()
    Optional = enum.auto()

@dataclasses.dataclass
class ComponentConstraint:
    value_constraint: typing.Optional[Constraint]
    presence_constraint: typing.Optional[Presence]

@dataclasses.dataclass
class MultipleInnerType:
    CONSTRAINT_TYPE = "MULTIPLE_INNER_TYPE"

    partial: bool
    components: typing.Dict[str, ComponentConstraint]

    @classmethod
    def build(
            cls, constraint_def: pyparsing.ParseResults,
            parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
    ) -> "MultipleInnerType":
        if constraint_def.partial_specification:
            partial = True
            type_constraints = constraint_def.partial_specification.type_constraints
        elif constraint_def.full_specification:
            partial = False
            type_constraints = constraint_def.full_specification.type_constraints
        else:
            util.assert_never(constraint_def)

        components = {}

        for constraint in type_constraints:
            if constraint.name[0] in components:
                raise SyntaxError(f"Duplicate component constraint {constraint.name[0]}")

            if constraint.component_constraint.presence_constraint:
                if constraint.component_constraint.presence_constraint[0] == "PRESENT":
                    presence_constraint = Presence.Present
                elif constraint.component_constraint.presence_constraint[0] == "ABSENT":
                    presence_constraint = Presence.Absent
                elif constraint.component_constraint.presence_constraint[0] == "OPTIONAL":
                    presence_constraint = Presence.Optional
                else:
                    util.assert_never(constraint.component_constraint.presence_constraint)
            else:
                presence_constraint = None

            components[constraint.name[0]] = ComponentConstraint(
                value_constraint=build_constraint(constraint.component_constraint.constraint[0].constraint_spec, parameters) if constraint.component_constraint.constraint else None,
                presence_constraint=presence_constraint
            )

        return cls(
            partial=partial,
            components=components
        )


@dataclasses.dataclass
class ConstraintUnion:
    CONSTRAINT_TYPE = "UNION"
    left: Constraint
    right: Constraint


@dataclasses.dataclass
class ConstraintIntersection:
    CONSTRAINT_TYPE = "INTERSECTION"
    left: Constraint
    right: Constraint


@dataclasses.dataclass
class ConstraintExclusion:
    CONSTRAINT_TYPE = "EXCLUSION"
    base_values: Constraint
    exclusion: Constraint


@dataclasses.dataclass
class ConstraintInverse:
    CONSTRAINT_TYPE = "INVERSE"
    constraint: Constraint


def build_constraint_element(
        element: pyparsing.ParseResults,
        parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
) -> Constraint:
    elm = element.elements
    if elm.subtype_elements:
        if elm.subtype_elements.size_constraint:
            base_constraint = SizeConstraint.build(elm.subtype_elements.size_constraint)
        elif elm.subtype_elements.single_value:
            base_constraint = SingleValue(
                value=value.build_value(elm.subtype_elements.single_value, parameters)
            )
        elif elm.subtype_elements.value_range:
            base_constraint = ValueRange.build(elm.subtype_elements.value_range)
        elif elm.subtype_elements.permitted_alphabet:
            base_constraint = PermittedAlphabetConstraint(
                alphabet=build_constraint(
                    elm.subtype_elements.permitted_alphabet.constraint[0].constraint_spec,
                    parameters
                )
            )
        elif elm.subtype_elements.inner_type_constraints:
            if elm.subtype_elements.inner_type_constraints.single_type_constraint:
                base_constraint = SingleInnerType(
                    constraint=build_constraint(elm.subtype_elements.inner_type_constraints.single_type_constraint, parameters)
                )
            elif elm.subtype_elements.inner_type_constraints.multiple_type_constraints:
                base_constraint = MultipleInnerType.build(elm.subtype_elements.inner_type_constraints.multiple_type_constraints)
            else:
                util.assert_never(elm.subtype_elements.inner_type_constraints)
        else:
            raise NotImplementedError(f"Unhandled constraint element {elm.dump()}")
    elif elm.element_set_spec:
        base_constraint = build_constraint_union(elm.element_set_spec[0].unions, parameters)
    else:
        util.assert_never(elm)

    if element.exclusions:
        return ConstraintExclusion(
            base_values=base_constraint,
            exclusion=build_constraint_element(element.exclusions, parameters)
        )
    else:
        return base_constraint


def build_constraint_intersection(
        intersection: pyparsing.ParseResults,
        parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
) -> Constraint:
    if intersection.intersection_elements_intersection_with:
        elm1 = build_constraint_element(intersection.intersection_elements_intersection_with, parameters)
        elm2 = build_constraint_intersection(intersection.intersections, parameters)
        return ConstraintIntersection(
            left=elm1,
            right=elm2,
        )
    else:
        elm = build_constraint_element(intersection.intersection_elements, parameters)
        return elm


def build_constraint_union(
        union: pyparsing.ParseResults, parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
) -> Constraint:
    if union.intersections_union_with:
        elm1 = build_constraint_intersection(union.intersections_union_with, parameters)
        elm2 = build_constraint_union(union.unions, parameters)
        return ConstraintUnion(
            left=elm1,
            right=elm2,
        )
    else:
        elm = build_constraint_intersection(union.intersections, parameters)
        return elm


def build_constraint_exclusions(
        constraint: pyparsing.ParseResults, parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
) -> Constraint:
    if constraint.exclusions:
        return ConstraintInverse(
            constraint=build_constraint_element(constraint.exclusions, parameters)
        )
    elif constraint.unions:
        return build_constraint_union(constraint.unions, parameters)
    else:
        util.assert_never(constraint)


def build_constraint(
        constraint: pyparsing.ParseResults, parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
) -> Constraint:
    if constraint.general_constraint:
        raise NotImplementedError(f"General constraint not implemented")

    return build_constraint_exclusions(constraint.subtype_constraint.basic_constraint, parameters)