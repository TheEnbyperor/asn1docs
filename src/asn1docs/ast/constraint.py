import enum
import typing
import dataclasses
import pyparsing
from . import type, value, util, module, object


Constraint = typing.Union[
    "ValueRange", "SingleValue", "Object", "SizeConstraint", "PermittedAlphabetConstraint", "SingleInnerType", "MultipleInnerType",
    "Contents", "ConstraintUnion", "ConstraintIntersection", "ConstraintExclusion", "ConstraintInverse", "UserDefinedConstraint",
    "TableConstraint"
]

@dataclasses.dataclass
class SingleValue:
    CONSTRAINT_TYPE = "SINGLE_VALUE"

    value: "value.Value"

@dataclasses.dataclass
class Object:
    CONSTRAINT_TYPE = "OBJECT"

    object: "object.Object"


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
            m: module.Module,
            parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
    ) -> "ValueRange":
        if constraint_def.lower_endpoint.inc_lower_end_value:
            if constraint_def.lower_endpoint.inc_lower_end_value.value:
                min_val = value.build_value(constraint_def.lower_endpoint.inc_lower_end_value.value, m, parameters)
            else:
                min_val = None
            min_inclusive = True
        elif constraint_def.lower_endpoint.exc_lower_end_value:
            if constraint_def.lower_endpoint.exc_lower_end_value.value:
                min_val = value.build_value(constraint_def.lower_endpoint.exc_lower_end_value.value, m, parameters)
            else:
                min_val = None
            min_inclusive = False
        else:
            util.assert_never(constraint_def.lower_endpoint)
        if constraint_def.upper_endpoint.inc_upper_end_value:
            if constraint_def.upper_endpoint.inc_upper_end_value.value:
                max_val = value.build_value(constraint_def.upper_endpoint.inc_upper_end_value.value, m, parameters)
            else:
                max_val = None
            max_inclusive = True
        elif constraint_def.upper_endpoint.exc_upper_end_value:
            if constraint_def.upper_endpoint.exc_upper_end_value.value:
                max_val = value.build_value(constraint_def.upper_endpoint.exc_upper_end_value.value, m, parameters)
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
            inner_type: typing.Optional[type.Type], m: module.Module,
            parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
    ) -> "SizeConstraint":
        constraint_spec = constraint_def.constraint[0].constraint_spec
        if constraint_spec.general_constraint:
            raise SyntaxError(f"General constraint invalid in a size constraint")
        inner_constraint = build_constraint(constraint_spec, inner_type, m, parameters)
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
            inner_type: typing.Optional[type.Type], m: module.Module,
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
                value_constraint=build_constraint(
                    constraint.component_constraint.constraint[0].constraint_spec, inner_type, m, parameters
                ) if constraint.component_constraint.constraint else None,
                presence_constraint=presence_constraint
            )

        return cls(
            partial=partial,
            components=components
        )

@dataclasses.dataclass
class Contents:
    CONSTRAINT_TYPE = "CONTENTS"
    containing_type: typing.Optional[type.Type]
    encoded_by: typing.Optional[value.Value]


@dataclasses.dataclass
class ConstraintUnion:
    CONSTRAINT_TYPE = "UNION"
    constraints: typing.List[Constraint]


@dataclasses.dataclass
class ConstraintIntersection:
    CONSTRAINT_TYPE = "INTERSECTION"
    constraints: typing.List[Constraint]


@dataclasses.dataclass
class ConstraintExclusion:
    CONSTRAINT_TYPE = "EXCLUSION"
    base_values: Constraint
    exclusion: Constraint


@dataclasses.dataclass
class ConstraintInverse:
    CONSTRAINT_TYPE = "INVERSE"
    constraint: Constraint


@dataclasses.dataclass
class UserDefinedConstraint:
    CONSTRAINT_TYPE = "USER_DEFINED"


@dataclasses.dataclass
class TableConstraintField:
    fields: typing.List[str]
    innermost_offset: typing.Optional[int] = None

@dataclasses.dataclass
class TableConstraint:
    CONSTRAINT_TYPE = "TABLE"

    object_set: "object.SetReference"
    fields: typing.List[TableConstraintField]

    @classmethod
    def build(
            cls, constraint_def: pyparsing.ParseResults,
            inner_type: typing.Optional[type.Type], m: module.Module,
            parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
    ) -> "TableConstraint":
        if not isinstance(inner_type, type.ObjectClassField):
            raise SyntaxError("Table constraint can only be applied to an ObjectClassFieldType")
        fields = []
        if constraint_def.simple_table_constraint:
            os = object.Set.build(constraint_def.simple_table_constraint, inner_type, m, parameters)
            if not (not os.extensible and len(os.members) == 1 and isinstance(os.members[0], object.SetReference)):
                raise NotImplementedError("Table constraint with non-inline object set")
            set_reference = os.members[0]
        elif constraint_def.component_relation_constraint:
            set_reference = object.SetReference.build(constraint_def.component_relation_constraint.defined_object_set, m, parameters)
            for field in constraint_def.component_relation_constraint.at_notation:
                if field.dots:
                    innermost_offset = len(field.dots) - 1
                else:
                    innermost_offset = None
                fields.append(TableConstraintField(
                    innermost_offset=innermost_offset,
                    fields=field.identifiers
                ))
        else:
            util.assert_never(constraint_def)

        return cls(
            object_set=set_reference,
            fields=fields
        )


def build_constraint_element(
        element: pyparsing.ParseResults,
        inner_type: typing.Optional[type.Type],
        m: module.Module,
        parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
) -> Constraint:
    elm = element.elements
    if elm.subtype_elements:
        if elm.subtype_elements.size_constraint:
            base_constraint = SizeConstraint.build(
                elm.subtype_elements.size_constraint, inner_type, m, parameters
            )
        elif elm.subtype_elements.single_value:
            base_constraint = SingleValue(
                value=value.build_value(elm.subtype_elements.single_value, m, parameters)
            )
        elif elm.subtype_elements.value_range:
            base_constraint = ValueRange.build(elm.subtype_elements.value_range, m, parameters)
        elif elm.subtype_elements.permitted_alphabet:
            base_constraint = PermittedAlphabetConstraint(
                alphabet=build_constraint(
                    elm.subtype_elements.permitted_alphabet.constraint[0].constraint_spec,
                    inner_type, m, parameters
                )
            )
        elif elm.subtype_elements.inner_type_constraints:
            if elm.subtype_elements.inner_type_constraints.single_type_constraint:
                base_constraint = SingleInnerType(
                    constraint=build_constraint(
                        elm.subtype_elements.inner_type_constraints.single_type_constraint,
                        inner_type, m, parameters
                    )
                )
            elif elm.subtype_elements.inner_type_constraints.multiple_type_constraints:
                base_constraint = MultipleInnerType.build(
                    elm.subtype_elements.inner_type_constraints.multiple_type_constraints,
                    inner_type, m, parameters
                )
            else:
                util.assert_never(elm.subtype_elements.inner_type_constraints)
        else:
            raise NotImplementedError(f"Unhandled constraint element {elm.dump()}")
    elif elm.element_set_spec:
        base_constraint = build_constraint_exclusions(elm.element_set_spec[0], inner_type, m, parameters)
    elif elm.object_set_elements:
        if elm.object_set_elements.object:
            base_constraint = Object(
                object=object.build_object(elm.object_set_elements.object[0], m, parameters)
            )
        elif elm.object_set_elements.defined_object_set:
            base_constraint = Object(
                object=object.SetReference.build(elm.object_set_elements.defined_object_set[0], m, parameters)
            )
        else:
            util.assert_never(elm.object_set_elements)
    else:
        util.assert_never(elm)

    if element.exclusions:
        return ConstraintExclusion(
            base_values=base_constraint,
            exclusion=build_constraint_element(element.exclusions, inner_type, m, parameters)
        )
    else:
        return base_constraint


def build_constraint_intersection(
        intersection: pyparsing.ParseResults,
        inner_type: typing.Optional[type.Type],
        m: module.Module,
        parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
) -> Constraint:
    if intersection.intersection_elements_intersection_with:
        elm1 = build_constraint_element(intersection.intersection_elements_intersection_with, inner_type, m, parameters)
        elm2 = build_constraint_intersection(intersection.intersections, inner_type, m, parameters)
        if isinstance(elm2, ConstraintIntersection):
            return ConstraintIntersection(
                constraints=[elm1] + elm2.constraints,
            )
        else:
            return ConstraintIntersection(
                constraints=[elm1, elm2]
            )
    else:
        elm = build_constraint_element(intersection.intersection_elements, inner_type, m, parameters)
        return elm


def build_constraint_union(
        union: pyparsing.ParseResults,
        inner_type: typing.Optional[type.Type],
        m: module.Module,
        parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
) -> Constraint:
    if union.intersections_union_with:
        elm1 = build_constraint_intersection(union.intersections_union_with, inner_type, m, parameters)
        elm2 = build_constraint_union(union.unions, inner_type, m, parameters)
        if isinstance(elm2, ConstraintUnion):
            return ConstraintUnion(
                constraints=[elm1] + elm2.constraints,
            )
        else:
            return ConstraintUnion(
                constraints=[elm1, elm2]
            )
    else:
        elm = build_constraint_intersection(union.intersections, inner_type, m, parameters)
        return elm


def build_constraint_exclusions(
        constraint: pyparsing.ParseResults,
        inner_type: typing.Optional[type.Type],
        m: module.Module,
        parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
) -> Constraint:
    if constraint.exclusions:
        return ConstraintInverse(
            constraint=build_constraint_element(constraint.exclusions, inner_type, m, parameters)
        )
    elif constraint.unions:
        return build_constraint_union(constraint.unions, inner_type, m, parameters)
    else:
        util.assert_never(constraint)

def build_general_constraint(
        constraint: pyparsing.ParseResults,
        inner_type: typing.Optional[type.Type],
        m: module.Module,
        parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
) -> Constraint:
    if constraint.contents_constraint:
        if constraint.contents_constraint.encoded_by:
            encoded_by = value.build_value(constraint.contents_constraint.encoded_by, m, parameters)
            if not isinstance(encoded_by, value.ObjectIdentifier) and not isinstance(encoded_by, value.Reference):
                raise SyntaxError("ENCODED BY constraint must be an OBJECT IDENTIFIER")
        else:
            encoded_by = None
        return Contents(
            containing_type=type.build_type(constraint.contents_constraint.type, m, parameters) if constraint.contents_constraint.type else None,
            encoded_by=encoded_by
        )
    elif constraint.user_defined_constraint:
        return UserDefinedConstraint()
    elif constraint.table_constraint:
        return TableConstraint.build(
            constraint.table_constraint, inner_type, m, parameters
        )
    else:
        raise NotImplementedError(f"Unhandled general constraint {constraint}")


def build_constraint(
        constraint: pyparsing.ParseResults,
        inner_type: typing.Optional[type.Type],
        m: module.Module,
        parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
) -> Constraint:
    if constraint.general_constraint:
        return build_general_constraint(constraint.general_constraint, inner_type, m, parameters)
    else:
        return build_constraint_exclusions(constraint.subtype_constraint.basic_constraint, inner_type, m, parameters)