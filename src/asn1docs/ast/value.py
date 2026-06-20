import abc
import typing
import dataclasses
import pyparsing
from . import util, module, javadoc

class Value(metaclass=abc.ABCMeta):
    VALUE_TYPE: str

    @property
    def is_type(self):
        return False

    @property
    def is_value(self):
        return True

@dataclasses.dataclass
class Null(Value):
    VALUE_TYPE = "NULL"

@dataclasses.dataclass
class Integer(Value):
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
class CharacterString(Value):
    VALUE_TYPE = "CHARACTER_STRING"

    value: str


@dataclasses.dataclass
class OctetString(Value):
    VALUE_TYPE = "OCTET_STRING"

    value: bytes

    @property
    def as_ascii(self):
        return self.value.decode("ascii", "replace")


@dataclasses.dataclass
class Enumeration(Value):
    VALUE_TYPE = "ENUMERATION"

    value: str


@dataclasses.dataclass
class Boolean(Value):
    VALUE_TYPE = "BOOLEAN"

    value: bool


@dataclasses.dataclass
class Choice(Value):
    VALUE_TYPE = "CHOICE"

    variant: str
    value: Value

@dataclasses.dataclass
class SequenceValue:
    javadoc: typing.Optional["javadoc.Javadoc"]
    value: Value


@dataclasses.dataclass
class Sequence(Value):
    VALUE_TYPE = "SEQUENCE"

    fields: typing.Dict[str, SequenceValue]

@dataclasses.dataclass
class SequenceOf(Value):
    VALUE_TYPE = "SEQUENCE_OF"

    values: typing.List[Value]


@dataclasses.dataclass
class ObjectIdentifierComponent:
    name: typing.Optional[str]
    number: typing.Optional[int]


@dataclasses.dataclass
class ObjectIdentifier(Value):
    VALUE_TYPE = "OBJECT_IDENTIFIER"

    origin: typing.Optional["Reference"]
    components: typing.List[ObjectIdentifierComponent]

    @classmethod
    def build(
            cls, value_def: pyparsing.ParseResults, m: module.Module,
            parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
    ) -> ObjectIdentifier:
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
            origin=Reference.build(value_def.value, m, parameters) if value_def.value else None,
            components=oid
        )

    @property
    def numeric_oid(self) -> typing.Optional[str]:
        return ".".join(str(i.number) for i in self.components)


@dataclasses.dataclass
class Reference(Value):
    VALUE_TYPE = "VALUE_REFERENCE"

    module: module.Module
    value_reference: str
    module_reference: typing.Optional[str] = None
    is_parameter: bool = False
    parameters: typing.List[util.ReferenceParameter] = dataclasses.field(default_factory=list)

    @classmethod
    def build(
            cls,
            value_def: pyparsing.ParseResults,
            m: module.Module,
            parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
    ) -> "Reference":
        if value_def.value_reference:
            ref = value_def.value_reference[0]
            return Reference(
                module=m,
                value_reference=ref,
                is_parameter=bool(parameters and (ref in parameters) and parameters[ref].parameter_type == module.ParameterType.Value),
            )
        elif value_def.external_value_reference:
            return Reference(
                module=m,
                value_reference=value_def.external_value_reference.value_reference[0],
                module_reference=value_def.external_value_reference.module_reference[0]
            )
        elif value_def.parameterised_value:
            if value_def.parameterized_value.simple_defined_value.value_reference:
                ref = value_def.parameterized_value.simple_defined_value \
                    .value_reference[0]
                return Reference(
                    module=m,
                    value_reference=ref,
                    is_parameter=bool(parameters and (ref in parameters) and parameters[ref].parameter_type == module.ParameterType.Value),
                    parameters=[util.ReferenceParameter.build(parameter, m, parameters) for parameter in
                                value_def.parameterized_value.parameter_list.parameters]
                )
            elif value_def.parameterized_value.simple_defined_value.external_value_reference:
                return Reference(
                    module=m,
                    value_reference=value_def.parameterized_value.simple_defined_value \
                        .external_value_reference.value_reference[0],
                    module_reference=value_def.parameterized_value.simple_defined_value \
                        .external_value_reference.module_reference[0],
                    parameters=[util.ReferenceParameter.build(parameter, m, parameters) for parameter in
                                value_def.parameterized_value.parameter_list.parameters]
                )
            else:
                util.assert_never(value_def.parameterized_value.simple_defined_value)
        else:
            util.assert_never(value_def)

@dataclasses.dataclass
class FromObjectReference(Value):
    VALUE_TYPE = "FROM_OBJECT_REFERENCE"

    @classmethod
    def build(
            cls,
            value_def: pyparsing.ParseResults,
            parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
    ) -> "FromObjectReference":
        raise NotImplementedError()

def build_value(
        value_def: pyparsing.ParseResults,
        m: module.Module,
        parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
) -> Value:
    if value_def.built_in_value:
        if value_def.built_in_value.null_value:
            return Null()
        elif value_def.built_in_value.integer_value:
            if value_def.built_in_value.integer_value.signed_number:
                return Integer.build(value_def.built_in_value.integer_value.signed_number[0])
        elif value_def.built_in_value.character_string_value:
            if value_def.built_in_value.character_string_value.cstring:
                return CharacterString(
                    value_def.built_in_value.character_string_value.cstring[1:-1].replace('""', '"')
                )
        elif value_def.built_in_value.octet_string_value:
            if value_def.built_in_value.octet_string_value.hstring:
                return OctetString(
                    bytes.fromhex(value_def.built_in_value.octet_string_value.hstring[1:-2])
                )
        elif value_def.built_in_value.enumerated_value:
            return Enumeration(value_def.built_in_value.enumerated_value[0])
        elif value_def.built_in_value.boolean_value:
            return Boolean(True if value_def.built_in_value.boolean_value == "TRUE" else False)
        elif value_def.built_in_value.choice_value:
            return Choice(
                variant=value_def.built_in_value.choice_value.identifier[0],
                value=build_value(value_def.built_in_value.choice_value.value, m, parameters),
            )
        elif value_def.built_in_value.sequence_value:
            if value_def.built_in_value.sequence_value.component_value_list:
                fields = {}
                for field in value_def.built_in_value.sequence_value.component_value_list:
                    ref = field.named_value.name[0]
                    if ref in fields:
                        raise SyntaxError(f"Duplicate field {ref} in sequence value")
                    fields[ref] = SequenceValue(
                        javadoc=javadoc.JavaDoc.build(field.javadoc) if field.javadoc else None,
                        value=build_value(field.named_value.value[0], m, parameters)
                    )
                return Sequence(fields=fields)
            else:
                return Sequence(fields={})
        elif value_def.built_in_value.sequence_of_value:
            if value_def.built_in_value.sequence_of_value.value_list:
                values = []
                for value in value_def.built_in_value.sequence_of_value.value_list:
                    values.append(build_value(value, m, parameters))
                return SequenceOf(values=values)
        elif value_def.built_in_value.object_identifier_value:
            return ObjectIdentifier.build(value_def.built_in_value.object_identifier_value, m, parameters)
        raise NotImplementedError(f"Unhandled value {value_def}")
    elif value_def.referenced_value:
        if value_def.referenced_value.defined_value:
            return Reference.build(value_def.referenced_value.defined_value, m, parameters)
        elif value_def.referenced_value.information_from_object:
            return FromObjectReference.build(value_def.reference_value.information_from_object)
        else:
            util.assert_never(value_def.referenced_value)
    elif value_def.object_class_field_value:
        raise NotImplementedError()
    else:
        util.assert_never(value_def)
