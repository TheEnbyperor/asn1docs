import abc
import typing
import dataclasses
import enum
import pyparsing
from . import value, util, javadoc, constraint, module, object
from .. import context


class Type(metaclass=abc.ABCMeta):
    TYPE_NAME: str

    @property
    def is_type(self):
        return True

    @property
    def is_value(self):
        return False

    @abc.abstractmethod
    def acceptable_value(self, value_instance: value.Value) -> bool:
        raise NotImplementedError()

    def is_item_of(self, ref: value.Reference) -> bool:
        return False


@dataclasses.dataclass
class Reference(Type):
    TYPE_NAME = "TYPE_REFERENCE"

    module: module.Module
    type_reference: str
    module_reference: typing.Optional[str] = None
    is_parameter: bool = False
    parameters: typing.List["util.ReferenceParameter"] = dataclasses.field(default_factory=list)

    def acceptable_value(self, value_instance: value.Value) -> bool:
        return False


@dataclasses.dataclass
class Any(Type):
    TYPE_NAME = "ANY"

    def acceptable_value(self, value_instance: value.Value) -> bool:
        return True


@dataclasses.dataclass
class Null(Type):
    TYPE_NAME = "NULL"

    def acceptable_value(self, value_instance: value.Value) -> bool:
        return False


@dataclasses.dataclass
class Boolean(Type):
    TYPE_NAME = "BOOLEAN"

    def acceptable_value(self, value_instance: value.Value) -> bool:
        return isinstance(value_instance, value.Boolean)


@dataclasses.dataclass
class Integer(Type):
    TYPE_NAME = "INTEGER"

    def acceptable_value(self, value_instance: value.Value) -> bool:
        return isinstance(value_instance, value.Integer)


@dataclasses.dataclass
class OctetString(Type):
    TYPE_NAME = "OCTET_STRING"

    def acceptable_value(self, value_instance: value.Value) -> bool:
        return False


@dataclasses.dataclass
class BitString(Type):
    TYPE_NAME = "BIT_STRING"

    def acceptable_value(self, value_instance: value.Value) -> bool:
        return False


@dataclasses.dataclass
class ObjectIdentifier(Type):
    TYPE_NAME = "OBJECT_IDENTIFIER"

    def acceptable_value(self, value_instance: value.Value) -> bool:
        return isinstance(value_instance, value.ObjectIdentifier)


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
class CharacterString(Type):
    TYPE_NAME = "CHARACTER_STRING"

    string_type: CharacterStringType

    def acceptable_value(self, value_instance: value.Value) -> bool:
        return isinstance(value_instance, value.CharacterString)


@dataclasses.dataclass
class SequenceComponent:
    type_definition: Type
    optional: bool = False
    default: typing.Optional["value.Value"] = None
    javadoc: typing.Optional["javadoc.JavaDoc"] = None


@dataclasses.dataclass
class Sequence(Type):
    TYPE_NAME = "SEQUENCE"

    components: typing.Dict[str, SequenceComponent]

    def acceptable_value(self, value_instance: value.Value) -> bool:
        return isinstance(value_instance, value.Sequence) and set(self.components.keys()) == set(value_instance.fields.keys())

    @classmethod
    def build_type(
            cls, type_def: pyparsing.ParseResults,
            m: module.Module,
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

                    component_type = build_type(named_type.type[0], m, parameters)
                    default_value = value.build_value(default, m, parameters) if default else None

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
class Enumeration(Type):
    TYPE_NAME = "ENUMERATION"

    values: typing.List[EnumerationItem]

    def acceptable_value(self, value_instance: value.Value) -> bool:
        return isinstance(value_instance, value.Enumeration) and value_instance.value in [v.name for v in self.values]

    def is_item_of(self, ref: value.Reference) -> bool:
        return any(e.name == ref.value_reference for e in self.values) and ref.module_reference is None


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
    javadoc: typing.Optional["javadoc.JavaDoc"] = None


@dataclasses.dataclass
class Choice(Type):
    TYPE_NAME = "CHOICE"
    components: typing.Dict[str, ChoiceComponent]

    def acceptable_value(self, value_instance: value.Value) -> bool:
        return isinstance(value_instance, value.Choice) and value_instance.variant in self.components \
            and self.components[value_instance.variant].type_definition.acceptable_value(value_instance.value)

    @classmethod
    def build_type(
            cls, type_def: pyparsing.ParseResults, m: module.Module,
            parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
    ) -> "Choice":
        components = {}
        if type_def.alternate_type_lists:
            if type_def.alternate_type_lists.alternate_type_list:
                for component in type_def.alternate_type_lists.alternate_type_list:
                    component_name = component.named_type.type_name[0]
                    if component_name in components:
                        raise SyntaxError(f"Duplicate alternate {component_name} in CHOICE")
                    component_type = build_type(component.named_type.type[0], m, parameters)
                    components[component_name] = ChoiceComponent(
                        type_definition=component_type,
                        javadoc=javadoc.JavaDoc.build(component.javadoc) if component.javadoc else None,
                    )
        return cls(components=components)


@dataclasses.dataclass
class SequenceOf(Type):
    TYPE_NAME = "SEQUENCE_OF"

    inner_type_definition: Type

    def acceptable_value(self, value_instance: value.Value) -> bool:
        return False

    @classmethod
    def build_sequence_of_type(
            cls, type_def: pyparsing.ParseResults, m: module.Module,
            parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
    ) -> "SequenceOf":
        return cls(
            inner_type_definition=build_type(type_def.type, m, parameters),
        )

    @classmethod
    def build_size_sequence_of_type(
            cls, type_def: pyparsing.ParseResults,
            inner_type: Type, m: module.Module,
            parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
    ) -> "ConstrainedType":
        inner_type_definition = build_type(type_def.type, m, parameters)
        constraint_spec = type_def.size_constraint.constraint[0].constraint_spec
        if constraint_spec.general_constraint:
            raise SyntaxError(f"General constraint invalid in a size constraint")
        inner_constraint = constraint.build_constraint(constraint_spec, inner_type, m, parameters)
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
class ConstrainedType(Type):
    TYPE_NAME = "CONSTRAINED_TYPE"

    inner_type_definition: Type
    constraints: "constraint.Constraint"

    def acceptable_value(self, value_instance: value.Value) -> bool:
        return self.inner_type_definition.acceptable_value(value_instance)


@dataclasses.dataclass
class ObjectClassField(Type):
    TYPE_NAME = "OBJECT_CLASS_FIELD"

    object_class: object.ClassReference
    field: typing.List[str]

    def acceptable_value(self, value_instance: value.Value) -> bool:
        return False

    def resolve_type(self, c: context.Context) -> Type:
        if len(self.field) != 1:
            raise NotImplementedError("Object class field reference too complex")
        object_class = c.resolve_class_reference(self.object_class)
        if self.field[0] not in object_class.fields:
            raise SyntaxError(f"Field {self.field[0]} does not exist in object class")
        field = object_class.fields[self.field[0]]
        if isinstance(field, object.TypeField):
            return Any()
        elif isinstance(field, object.FixedTypeValueField):
            return field.type
        else:
            util.assert_never(field)

    @classmethod
    def build_type(
            cls, type_def: pyparsing.ParseResults, m: module.Module,
            parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
    ) -> "ObjectClassField":
        field = []
        for component in type_def.field_name[0]:
            if component.type_field_reference:
                field.append(component.type_field_reference)
            elif component.value_field_reference:
                field.append(component.value_field_reference)
            else:
                util.assert_never(component)
        return ObjectClassField(
            object_class=object.ClassReference.build(type_def.object_class[0], m, parameters),
            field=field,
        )


def build_type(
        type_def: pyparsing.ParseResults,
        m: module.Module,
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
            return Choice.build_type(type_def.built_in_type.choice_type, m, parameters)
        elif type_def.built_in_type.sequence_type:
            return Sequence.build_type(type_def.built_in_type.sequence_type, m, parameters)
        elif type_def.built_in_type.enumerated_type:
            return Enumeration.build_type(type_def.built_in_type.enumerated_type, parameters)
        elif type_def.built_in_type.sequence_of_type:
            return SequenceOf.build_sequence_of_type(type_def.built_in_type.sequence_of_type, m, parameters)
        elif type_def.built_in_type.object_class_field_type:
            return ObjectClassField.build_type(type_def.built_in_type.object_class_field_type, m, parameters)
        else:
            raise NotImplementedError(f"Unhandled built-in type {type_def.built_in_type}")
    elif type_def.referenced_type:
        if type_def.referenced_type.defined_type:
            if type_def.referenced_type.defined_type.type_reference:
                ref = type_def.referenced_type.defined_type.type_reference[0]
                return Reference(
                    module=m,
                    type_reference=ref,
                    is_parameter=bool(parameters and ref in parameters and parameters[
                        ref].parameter_type == module.ParameterType.Type),
                )
            elif type_def.referenced_type.defined_type.external_type_reference:
                return Reference(
                    module=m,
                    type_reference=type_def.referenced_type.defined_type.external_type_reference.type_reference[0],
                    module_reference=type_def.referenced_type.defined_type.external_type_reference.module_reference[0]
                )
            elif type_def.referenced_type.defined_type.parameterized_type:
                if type_def.referenced_type.defined_type.parameterized_type.simple_defined_type.type_reference:
                    ref = type_def.referenced_type.defined_type.parameterized_type.simple_defined_type.type_reference[0]
                    return Reference(
                        module=m,
                        type_reference=ref,
                        is_parameter=bool(parameters and ref in parameters and parameters[
                            ref].parameter_type == module.ParameterType.Type),
                        parameters=[util.ReferenceParameter.build(parameter, m, parameters) for parameter in
                                    type_def.referenced_type.defined_type.parameterized_type.parameter_list.parameters]
                    )
                elif type_def.referenced_type.defined_type.parameterized_type.simple_defined_type.external_type_reference:
                    return Reference(
                        module=m,
                        type_reference=type_def.referenced_type.defined_type.parameterized_type.simple_defined_type \
                            .external_type_reference.type_reference[0],
                        module_reference=type_def.referenced_type.defined_type.parameterized_type.simple_defined_type \
                            .external_type_reference.module_reference[0],
                        parameters=[util.ReferenceParameter.build(parameter, m, parameters) for parameter in
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
                inner_type = SequenceOf.build_sequence_of_type(
                        type_def.constrained_type.type_of_with_constraint.sequence_of_type,
                        m, parameters,
                    )
                return ConstrainedType(
                    inner_type_definition=inner_type,
                    constraints=constraint.build_constraint(
                        type_def.constrained_type.type_of_with_constraint.sequence_of_type.constraint.constraint_spec,
                        inner_type, m, parameters
                    )
                )
            elif type_def.constrained_type.type_of_with_constraint.size_sequence_of_type:
                return SequenceOf.build_size_sequence_of_type(
                    type_def.constrained_type.type_of_with_constraint.size_sequence_of_type,
                    m, parameters,
                )
            else:
                raise NotImplementedError(
                    f"Unhandled constrained type {type_def.constrained_type.type_of_with_constraint}")
        elif type_def.constrained_type.constrained_type:
            inner_type = build_type(type_def.constrained_type.constrained_type.inner_type, m, parameters)
            return ConstrainedType(
                inner_type_definition=inner_type,
                constraints=constraint.build_constraint(
                    type_def.constrained_type.constrained_type.constraint.constraint_spec,
                    inner_type, m, parameters
                )
            )
        else:
            util.assert_never(type_def.constrained_type)
    else:
        util.assert_never(type_def)
