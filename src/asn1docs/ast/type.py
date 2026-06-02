import typing
import dataclasses
import enum
import pyparsing
from . import value, util, javadoc, constraint, module

Type = typing.Union[
    "Reference", "Null", "Boolean", "Integer", "OctetString", "BitString", "CharacterString",
    "ObjectIdentifier", "Sequence", "SequenceOf", "Choice", "Enumeration", "ConstrainedType"
]


@dataclasses.dataclass
class Reference:
    TYPE_NAME = "TYPE_REFERENCE"

    type_reference: str
    module_reference: typing.Optional[str] = None
    is_parameter: bool = False
    parameters: typing.List["util.ReferenceParameter"] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Null:
    TYPE_NAME = "NULL"


@dataclasses.dataclass
class Boolean:
    TYPE_NAME = "BOOLEAN"


@dataclasses.dataclass
class Integer:
    TYPE_NAME = "INTEGER"


@dataclasses.dataclass
class OctetString:
    TYPE_NAME = "OCTET_STRING"


@dataclasses.dataclass
class BitString:
    TYPE_NAME = "BIT_STRING"


@dataclasses.dataclass
class ObjectIdentifier:
    TYPE_NAME = "OBJECT_IDENTIFIER"


class CharacterStringType(enum.Enum):
    BMPString = enum.auto()
    GeneralString = enum.auto()
    GraphicString = enum.auto()
    IA5String = enum.auto()
    ISO646String = enum.auto()
    NumericString = enum.auto()
    PrintableString = enum.auto()
    TeletexString = enum.auto()
    T61String = enum.auto()
    UniversalString = enum.auto()
    UTF8String = enum.auto()
    VideotexString = enum.auto()
    VisibleString = enum.auto()


@dataclasses.dataclass
class CharacterString:
    TYPE_NAME = "CHARACTER_STRING"

    string_type: CharacterStringType


@dataclasses.dataclass
class SequenceComponent:
    type_definition: Type
    optional: bool = False
    default: typing.Optional["value.Value"] = None
    javadoc: typing.Optional["javadoc.JavaDoc"] = None


@dataclasses.dataclass
class Sequence:
    TYPE_NAME = "SEQUENCE"

    components: typing.Dict[str, SequenceComponent]

    @classmethod
    def build_type(
            cls, type_def: pyparsing.ParseResults,
            parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
    ) -> "Sequence":
        components = {}
        if type_def.component_type_lists:
            if type_def.component_type_lists.component_type_list:
                for component in type_def.component_type_lists.component_type_list:
                    if component.component_type.simple_named_type:
                        named_type = component.component_type.simple_named_type
                        optional = False
                        default = None
                    elif component.component_type.optional_named_type:
                        named_type = component.component_type.optional_named_type.named_type
                        optional = True
                        default = None
                    elif component.component_type.default_named_type:
                        named_type = component.component_type.default_named_type.named_type
                        optional = False
                        default = component.component_type.default_named_type.default
                    elif component.component_type.components_of_type:
                        raise NotImplementedError(f"COMPONENTS OF not implemented")
                    else:
                        util.assert_never(component)

                    component_name = named_type.type_name[0]
                    if component_name in components:
                        raise SyntaxError(f"Duplicate component {component_name} in SEQUENCE")

                    component_type = build_type(named_type.type[0], parameters)
                    default_value = value.build_value(default, parameters) if default else None

                    components[component_name] = SequenceComponent(
                        type_definition=component_type,
                        optional=optional,
                        default=default_value,
                        javadoc=javadoc.JavaDoc.build(component.javadoc) if component.javadoc else None
                    )
        return cls(components=components)


@dataclasses.dataclass
class EnumerationItem:
    name: str
    value: typing.Optional["value.Integer"] = None
    javadoc: typing.Optional["javadoc.JavaDoc"] = None


@dataclasses.dataclass
class Enumeration:
    TYPE_NAME = "ENUMERATION"

    values: typing.List[EnumerationItem]

    @classmethod
    def build_type(
            cls, type_def: pyparsing.ParseResults,
            parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
    ) -> "Enumeration":
        values = []
        for item in type_def.enumerations.enumeration:
            if item.enumeration_item.named_number:
                values.append(EnumerationItem(
                    name=item.enumeration_item.named_number[0].identifier[0],
                    value=value.Integer.build(item.enumeration_item.named_number[0].number),
                    javadoc=javadoc.JavaDoc.build(item.javadoc) if item.javadoc else None,
                ))
            else:
                values.append(EnumerationItem(
                    name=item.enumeration_item.identifier,
                    javadoc=javadoc.JavaDoc.build(item.javadoc) if item.javadoc else None,
                ))
        return cls(values=values)


@dataclasses.dataclass
class ChoiceComponent:
    type_definition: Type
    javadoc: typing.Optional[JavaDoc] = None


@dataclasses.dataclass
class Choice:
    TYPE_NAME = "CHOICE"
    components: typing.Dict[str, ChoiceComponent]

    @classmethod
    def build_type(
            cls, type_def: pyparsing.ParseResults,
            parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
    ) -> "Choice":
        components = {}
        if type_def.alternate_type_lists:
            if type_def.alternate_type_lists.alternate_type_list:
                for component in type_def.alternate_type_lists.alternate_type_list:
                    component_name = component.named_type.type_name[0]
                    if component_name in components:
                        raise SyntaxError(f"Duplicate alternate {component_name} in CHOICE")
                    component_type = build_type(component.named_type.type[0], parameters)
                    components[component_name] = ChoiceComponent(
                        type_definition=component_type,
                        javadoc=javadoc.JavaDoc.build(component.javadoc) if component.javadoc else None,
                    )
        return cls(components=components)


@dataclasses.dataclass
class SequenceOf:
    TYPE_NAME = "SEQUENCE_OF"

    inner_type_definition: Type

    @classmethod
    def build_sequence_of_type(
            cls, type_def: pyparsing.ParseResults,
            parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
    ) -> "SequenceOf":
        return cls(
            inner_type_definition=build_type(type_def.type, parameters),
        )

    @classmethod
    def build_size_sequence_of_type(
            cls, type_def: pyparsing.ParseResults,
            parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
    ) -> "ConstrainedType":
        inner_type_definition = build_type(type_def.type, parameters)
        constraint_spec = type_def.size_constraint.constraint[0].constraint_spec
        if constraint_spec.general_constraint:
            raise SyntaxError(f"General constraint invalid in a size constraint")
        inner_constraint = constraint.build_constraint(constraint_spec, parameters)
        if not isinstance(inner_constraint, constraint.ValueRange):
            raise SyntaxError("Size constraint inner constraint is not a ValueRange")
        return ConstrainedType(
            inner_type_definition=cls(
                inner_type_definition=inner_type_definition,
            ),
            constraints=constraint.SizeConstraint(
                length_range=inner_constraint
            )
        )

@dataclasses.dataclass
class ConstrainedType:
    TYPE_NAME = "CONSTRAINED_TYPE"

    inner_type_definition: Type
    constraints: "constraint.Constraint"



def build_type(
        type_def: pyparsing.ParseResults,
        parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
) -> Type:
    if type_def.built_in_type:
        if type_def.built_in_type.null_type:
            return Null()
        elif type_def.built_in_type.boolean_type:
            return Boolean()
        elif type_def.built_in_type.integer_type:
            return Integer()
        elif type_def.built_in_type.octet_string_type:
            return OctetString()
        elif type_def.built_in_type.bit_string_type:
            # TODO: named bits
            return BitString()
        elif type_def.built_in_type.object_identifier_type:
            return ObjectIdentifier()
        elif type_def.built_in_type.character_string_type:
            if type_def.built_in_type.character_string_type.restricted_character_string_type:
                st = type_def.built_in_type.character_string_type.restricted_character_string_type[0]
                if st == "VisibleString":
                    return CharacterString(string_type=CharacterStringType.VisibleString)
                elif st == "UTF8String":
                    return CharacterString(string_type=CharacterStringType.UTF8String)
                else:
                    raise NotImplementedError(f"Unhandled character_string_type {st}")
            elif type_def.built_in_type.character_string_type.unrestricted_character_string_type:
                raise NotImplementedError(f"Unrestricted character string not implemented")
            else:
                util.assert_never(type_def.built_in_type.character_string_type)
        elif type_def.built_in_type.choice_type:
            return Choice.build_type(type_def.built_in_type.choice_type, parameters)
        elif type_def.built_in_type.sequence_type:
            return Sequence.build_type(type_def.built_in_type.sequence_type, parameters)
        elif type_def.built_in_type.enumerated_type:
            return Enumeration.build_type(type_def.built_in_type.enumerated_type, parameters)
        elif type_def.built_in_type.sequence_of_type:
            return SequenceOf.build_sequence_of_type(type_def.built_in_type.sequence_of_type, parameters)
        elif type_def.built_in_type.object_class_field_type:
            pass
        else:
            raise NotImplementedError(f"Unhandled built-in type {type_def.built_in_type}")
    elif type_def.referenced_type:
        if type_def.referenced_type.defined_type:
            if type_def.referenced_type.defined_type.type_reference:
                ref = type_def.referenced_type.defined_type.type_reference[0]
                return Reference(
                    type_reference=ref,
                    is_parameter=bool(parameters and ref in parameters and parameters[ref].parameter_type == module.ParameterType.Type),
                )
            elif type_def.referenced_type.defined_type.external_type_reference:
                return Reference(
                    type_def.referenced_type.defined_type.external_type_reference.type_reference[0],
                    type_def.referenced_type.defined_type.external_type_reference.module_reference[0]
                )
            elif type_def.referenced_type.defined_type.parameterized_type:
                if type_def.referenced_type.defined_type.parameterized_type.simple_defined_type.type_reference:
                    ref = type_def.referenced_type.defined_type.parameterized_type.simple_defined_type.type_reference[0]
                    return Reference(
                        type_reference=ref,
                        is_parameter=bool(parameters and ref in parameters and parameters[ref].parameter_type == module.ParameterType.Type),
                        parameters=[util.ReferenceParameter.build(parameter, parameters) for parameter in
                                    type_def.referenced_type.defined_type.parameterized_type.parameter_list.parameters]
                    )
                elif type_def.referenced_type.defined_type.parameterized_type.simple_defined_type.external_type_reference:
                    return Reference(
                        type_def.referenced_type.defined_type.parameterized_type.simple_defined_type\
                            .external_type_reference.type_reference[0],
                        type_def.referenced_type.defined_type.parameterized_type.simple_defined_type\
                            .external_type_reference.module_reference[0],
                        parameters=[util.ReferenceParameter.build(parameter, parameters) for parameter in
                                    type_def.referenced_type.defined_type.parameterized_type.parameter_list.parameters]
                    )
                else:
                    util.assert_never(type_def.referenced_type.defined_type.parameterized_type.simple_defined_type)
            else:
                util.assert_never(type_def.referenced_type.defined_type)
        else:
            raise NotImplementedError(f"Unhandled referenced type {type_def.referenced_type}")
    elif type_def.constrained_type:
        if type_def.constrained_type.type_of_with_constraint:
            if type_def.constrained_type.type_of_with_constraint.sequence_of_type:
                return ConstrainedType(
                    inner_type_definition=SequenceOf.build_sequence_of_type(
                        type_def.constrained_type.type_of_with_constraint.sequence_of_type
                    ),
                    constraints=constraint.build_constraint(
                        type_def.constrained_type.type_of_with_constraint.sequence_of_type.constraint.constraint_spec,
                        parameters
                    )
                )
            elif type_def.constrained_type.type_of_with_constraint.size_sequence_of_type:
                return SequenceOf.build_size_sequence_of_type(
                    type_def.constrained_type.type_of_with_constraint.size_sequence_of_type
                )
            else:
                raise NotImplementedError(
                    f"Unhandled constrained type {type_def.constrained_type.type_of_with_constraint}")
        elif type_def.constrained_type.constrained_type:
            return ConstrainedType(
                inner_type_definition=build_type(type_def.constrained_type.constrained_type.inner_type, parameters),
                constraints=constraint.build_constraint(
                    type_def.constrained_type.constrained_type.constraint.constraint_spec,
                    parameters
                )
            )
        else:
            util.assert_never(type_def.constrained_type)
    else:
        util.assert_never(type_def)