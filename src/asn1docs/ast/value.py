import typing
import dataclasses
import pyparsing
from . import util, module

Value = typing.Union[
    "Reference", "Integer", "CharacterString", "Enumeration", "Boolean", "Choice", "Sequence", "ObjectIdentifier"]


@dataclasses.dataclass
class Integer:
    VALUE_TYPE = "INTEGER"

    value: int

    @classmethod
    def build(cls, signed_number: pyparsing.ParseResults) -> "Integer":
        if signed_number.positive_number:
            return cls(int(signed_number.positive_number, 10))
        elif signed_number.negative_number:
            return cls(-int(signed_number.negative_number.number, 10))
        else:
            util.assert_never(signed_number)


@dataclasses.dataclass
class CharacterString:
    VALUE_TYPE = "CHARACTER_STRING"

    value: str


@dataclasses.dataclass
class Enumeration:
    VALUE_TYPE = "ENUMERATION"

    value: str


@dataclasses.dataclass
class Boolean:
    VALUE_TYPE = "BOOLEAN"

    value: bool


@dataclasses.dataclass
class Choice:
    VALUE_TYPE = "CHOICE"

    variant: str
    value: Value


@dataclasses.dataclass
class Sequence:
    VALUE_TYPE = "SEQUENCE"

    fields: typing.Dict[str, Value]


@dataclasses.dataclass
class ObjectIdentifierComponent:
    name: typing.Optional[str]
    number: typing.Optional[int]


@dataclasses.dataclass
class ObjectIdentifier:
    VALUE_TYPE = "OBJECT_IDENTIFIER"

    origin: typing.Optional["Reference"]
    components: typing.List[ObjectIdentifierComponent]

    @classmethod
    def build(cls, value_def: pyparsing.ParseResults) -> ObjectIdentifier:
        oid = []
        for component in value_def.components:
            if component.name and component.number:
                oid.append(ObjectIdentifierComponent(
                    name=component.name[0],
                    number=int(component.number, 10)
                ))
            elif component.name:
                oid.append(ObjectIdentifierComponent(
                    name=component.name[0],
                    number=None
                ))
            elif component.number:
                oid.append(ObjectIdentifierComponent(
                    name=None,
                    number=int(component.number, 10)
                ))
        return cls(
            origin=Reference.build(value_def.value) if value_def.value else None,
            components=oid
        )

    @property
    def numeric_oid(self) -> typing.Optional[str]:
        return ".".join(str(i.number) for i in self.components)


@dataclasses.dataclass
class Reference:
    VALUE_TYPE = "VALUE_REFERENCE"

    value_reference: str
    module_reference: typing.Optional[str] = None
    is_parameter: bool = False
    parameters: typing.List[util.ReferenceParameter] = dataclasses.field(default_factory=list)

    @classmethod
    def build(
            cls,
            value_def: pyparsing.ParseResults,
            parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
    ) -> Reference:
        if value_def.value_reference:
            ref = value_def.value_reference[0]
            return Reference(
                value_reference=ref,
                is_parameter=bool(parameters and (ref in parameters) and parameters[ref].is_value),
            )
        elif value_def.external_value_reference:
            return Reference(
                value_def.external_value_reference.value_reference[0],
                value_def.external_value_reference.module_reference[0]
            )
        elif value_def.parameterised_value:
            if value_def.parameterized_value.simple_defined_value.value_reference:
                ref = value_def.parameterized_value.simple_defined_value \
                    .value_reference[0]
                return Reference(
                    value_reference=ref,
                    is_parameter=bool(parameters and (ref in parameters) and parameters[ref].is_value),
                    parameters=[util.ReferenceParameter.build(parameter, parameters) for parameter in
                                value_def.parameterized_value.parameter_list.parameters]
                )
            elif value_def.parameterized_value.simple_defined_value.external_value_reference:
                return Reference(
                    value_def.parameterized_value.simple_defined_value \
                        .external_value_reference.value_reference[0],
                    value_def.parameterized_value.simple_defined_value \
                        .external_value_reference.module_reference[0],
                    parameters=[util.ReferenceParameter.build(parameter, parameters) for parameter in
                                value_def.parameterized_value.parameter_list.parameters]
                )
            else:
                util.assert_never(value_def.parameterized_value.simple_defined_value)
        else:
            util.assert_never(value_def)


def build_value(
        value_def: pyparsing.ParseResults,
        parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
) -> Value:
    if value_def.built_in_value:
        if value_def.built_in_value.integer_value:
            if value_def.built_in_value.integer_value.signed_number:
                return Integer.build(value_def.built_in_value.integer_value.signed_number[0])
        elif value_def.built_in_value.character_string_value:
            if value_def.built_in_value.character_string_value.cstring:
                return CharacterString(
                    value_def.built_in_value.character_string_value.cstring[1:-1].replace('""', '"')
                )
        elif value_def.built_in_value.enumerated_value:
            return Enumeration(value_def.built_in_value.enumerated_value[0])
        elif value_def.built_in_value.boolean_value:
            return Boolean(True if value_def.built_in_value.boolean_value[0] == "TRUE" else False)
        elif value_def.built_in_value.choice_value:
            return Choice(
                variant=value_def.built_in_value.choice_value.identifier[0],
                value=build_value(value_def.built_in_value.choice_value.value, parameters),
            )
        elif value_def.built_in_value.sequence_value:
            if value_def.built_in_value.sequence_value.component_value_list:
                fields = {}
                for field in value_def.built_in_value.sequence_value.component_value_list:
                    ref = field.name[0]
                    if ref in fields:
                        raise SyntaxError(f"Duplicate field {ref} in sequence value")
                    fields[ref] = build_value(field.value[0], parameters)
                return Sequence(fields=fields)
            else:
                return Sequence(fields={})
        elif value_def.built_in_value.object_identifier_value:
            return ObjectIdentifier.build(value_def.built_in_value.object_identifier_value)
        raise NotImplementedError(f"Unhandled value {value_def}")
    elif value_def.referenced_value:
        return Reference.build(value_def.referenced_value.defined_value)
    else:
        util.assert_never(value_def)
