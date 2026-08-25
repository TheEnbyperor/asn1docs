import dataclasses
import typing
import collections

import pyparsing

from . import util, module, type, value, constraint
from .. import context


@dataclasses.dataclass
class Field:
    optional: bool


@dataclasses.dataclass
class TypeField(Field):
    FIELD_TYPE = "TYPE"

    default: typing.Optional["type.Type"]

    @classmethod
    def build(
            cls,
            field_def: pyparsing.ParseResults,
            m: module.Module,
            parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
    ) -> "TypeField":
        return TypeField(
            optional=bool(field_def.optionality and field_def.optionality.optional),
            default=type.build_type(
                field_def.optionality.default, m, parameters
            ) if field_def.optionality and field_def.optionality.default else None,
        )


@dataclasses.dataclass
class FixedTypeValueField(Field):
    FIELD_TYPE = "FIXED_TYPE_VALUE"

    type: "type.Type"
    unique: bool
    default: typing.Optional["value.Value"]

    @classmethod
    def build(
            cls,
            field_def: pyparsing.ParseResults,
            m: module.Module,
            parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
    ) -> "FixedTypeValueField":
        return FixedTypeValueField(
            type=type.build_type(field_def.type, m, parameters),
            unique=bool(field_def.unique),
            optional=bool(field_def.optionality and field_def.optionality.optional),
            default=value.build_value(
                field_def.optionality.default, m, parameters
            ) if field_def.optionality and field_def.optionality.default else None,
        )


SyntaxLiteral = collections.namedtuple("SyntaxLiteral", ["value"])
SyntaxTypeFieldReference = collections.namedtuple("SyntaxTypeFieldReference", ["name"])
SyntaxValueFieldReference = collections.namedtuple("SyntaxTypeFieldReference", ["name"])
SyntaxElement = typing.Union[SyntaxLiteral, SyntaxTypeFieldReference, SyntaxValueFieldReference, "SyntaxOptionalGroup"]


@dataclasses.dataclass
class SyntaxOptionalGroup:
    elements: typing.List[SyntaxElement]


def build_syntax_group(
        fields: typing.Dict[str, Field],
        syntax_def: pyparsing.ParseResults,
) -> typing.List[SyntaxElement]:
    elements = []
    for token_or_group in syntax_def.token_or_groups:
        if token_or_group.optional_group:
            elements.append(SyntaxOptionalGroup(
                elements=build_syntax_group(fields, token_or_group.optional_group)
            ))
        elif token_or_group.required_token:
            if token_or_group.required_token.literal:
                elements.append(SyntaxLiteral(token_or_group.required_token.literal))
            elif token_or_group.required_token.field_name:
                if token_or_group.required_token.field_name[0].type_field_reference:
                    ref = token_or_group.required_token.field_name[0].type_field_reference
                    if ref not in fields:
                        raise SyntaxError(f"Object class syntax references undefined field: {ref}")
                    elements.append(SyntaxTypeFieldReference(ref))
                elif token_or_group.required_token.field_name[0].value_field_reference:
                    ref = token_or_group.required_token.field_name[0].value_field_reference
                    if ref not in fields:
                        raise SyntaxError(f"Object class syntax references undefined field: {ref}")
                    elements.append(SyntaxValueFieldReference(ref))
                else:
                    util.assert_never(token_or_group.required_token.field_name[0])
            else:
                util.assert_never(token_or_group)
        else:
            util.assert_never(token_or_group)
    return elements


@dataclasses.dataclass
class Class:
    fields: typing.Dict[str, Field]
    syntax: typing.Optional[typing.List[SyntaxElement]]

    @classmethod
    def build(
            cls,
            class_def: pyparsing.ParseResults,
            m: module.Module,
            parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
    ) -> "Class":
        fields = {}
        for field in class_def.field_spec:
            field_ref = field[0].reference
            if field_ref in fields:
                raise SyntaxError(f"Duplicate field in object class: {field_ref}")
            if field.type_field:
                fields[field_ref] = TypeField.build(field.type_field, m, parameters)
            elif field.fixed_type_value_field:
                fields[field_ref] = FixedTypeValueField.build(field.fixed_type_value_field, m, parameters)
            else:
                raise NotImplementedError()

        if class_def.with_syntax:
            syntax = build_syntax_group(fields, class_def.with_syntax.syntax)
        else:
            syntax = None

        return cls(fields, syntax)

@dataclasses.dataclass
class ClassReference:
    module: module.Module
    class_reference: str
    module_reference: typing.Optional[str] = None
    is_parameter: bool = False

    @classmethod
    def build(
            cls,
            class_def: pyparsing.ParseResults, m: module.Module,
            parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
    ) -> "ClassReference":
        if class_def.object_class_reference:
            ref = class_def.object_class_reference[0]
            return cls(
                module=m,
                class_reference=ref,
                is_parameter=bool(parameters and (ref in parameters) and parameters[ref].parameter_type == module.ParameterType.ObjectClass),
            )
        elif class_def.external_value_reference:
            return cls(
                module=m,
                class_reference=class_def.external_class_reference.object_class_reference[0],
                module_reference=class_def.external_class_reference.module_reference[0]
            )
        else:
            util.assert_never(class_def)

ClassType = typing.Union[Class, ClassReference]

def build_class(
        class_def: pyparsing.ParseResults,
        m: module.Module,
        parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
) -> ClassType:
    if class_def.object_class_defn:
        return Class.build(class_def.object_class_defn, m, parameters)
    elif class_def.defined_object_class:
        return ClassReference.build(class_def.defined_object_class, parameters)
    else:
        raise NotImplementedError()


@dataclasses.dataclass
class Set:
    members: typing.List[typing.Union[Object,  value.Value]]
    extensible: bool

    @classmethod
    def build(
            cls,
            set_def: pyparsing.ParseResults,
            inner_type: typing.Optional[type.Type],
            m: module.Module,
            parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
    ) -> "Set":
        members = []
        if set_def.spec.root_element_spec:
            spec = constraint.build_constraint_exclusions(set_def.spec.root_element_spec[0], inner_type, m, parameters)
            if isinstance(spec, constraint.Object):
                members.append(spec.object)
            elif isinstance(spec, constraint.SingleValue):
                members.append(spec.value)
            elif isinstance(spec, constraint.ConstraintUnion):
                for member in spec.constraints:
                    if isinstance(member, constraint.Object):
                        members.append(member.object)
                    elif isinstance(member, constraint.SingleValue):
                        members.append(member.value)
                    else:
                        raise NotImplementedError("Object set members too complicated")
            else:
                raise NotImplementedError("Object set members too complicated")
        return cls(
            members=members,
            extensible=bool(set_def.spec.extensible),
        )

@dataclasses.dataclass
class SetReference:
    module: module.Module
    value_reference: str
    module_reference: typing.Optional[str] = None
    is_parameter: bool = False

    @classmethod
    def build(
            cls,
            set_def: pyparsing.ParseResults,
            m: module.Module,
            parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
    ) -> "SetReference":
        if set_def.object_set_reference:
            ref = set_def.object_set_reference[0]
            return cls(
                module=m,
                value_reference=ref,
                is_parameter=bool(parameters and (ref in parameters) and parameters[ref].parameter_type == module.ParameterType.Type),
            )
        elif set_def.external_object_set_reference:
            return cls(
                module=m,
                value_reference=set_def.external_object_set_reference.object_set_reference[0],
                module_reference=set_def.external_object_set_reference.module_reference[0]
            )
        else:
            util.assert_never(set_def)

SetType = typing.Union[Set, SetReference]

@dataclasses.dataclass
class DefinedObject:
    fields: typing.Dict[str, typing.Union[None, type.Type, value.Value]]

@dataclasses.dataclass
class DefaultSyntax:
    fields: typing.Dict[str, typing.Union[type.Type, value.Value]]

@dataclasses.dataclass
class DefinedSyntax:
    tokens: typing.List[typing.Union[str, type.Type, value.Value]]

@dataclasses.dataclass
class Object:
    definition: typing.Union[DefaultSyntax, DefinedSyntax]

    def parse_definition_defined_syntax(self, object_class: Class, c: context.Context) -> DefinedObject:
        assert object_class.syntax is not None
        assert isinstance(self.definition, DefinedSyntax)

        fields = {}

        def match_elements(elements, i):
            for element in elements:
                if i >= len(self.definition.tokens):
                    raise SyntaxError(f"Object definition invalid: out of tokens")
                next_token = self.definition.tokens[i]

                if isinstance(element, SyntaxLiteral):
                    if not isinstance(next_token, str):
                        raise SyntaxError(f"Object definition invalid: expected {element.value} found {next_token}")
                    if next_token != element.value:
                        raise SyntaxError(f"Object definition invalid: expected {element.value} found {next_token}")
                    i += 1

                elif isinstance(element, SyntaxTypeFieldReference):
                    if isinstance(next_token, value.Null):
                        next_token = type.Null()
                    if not isinstance(next_token, type.Type):
                        raise SyntaxError(f"Object definition invalid: expected type found {next_token}")
                    if element.name not in object_class.fields:
                        raise SyntaxError(f"Object definition invalid: type field {element.name} not found")
                    if not isinstance(object_class.fields[element.name], TypeField):
                        raise SyntaxError(f"Object definition invalid: field {element.name} not a type field")
                    if element.name in fields:
                        raise SyntaxError(f"Object definition invalid: duplicate definition for field {element.name}")
                    fields[element.name] = next_token
                    i += 1

                elif isinstance(element, SyntaxValueFieldReference):
                    if not isinstance(next_token, value.Value):
                        raise SyntaxError(f"Object definition invalid: expected value found {next_token}")
                    if element.name not in object_class.fields:
                        raise SyntaxError(f"Object definition invalid: value field {element.name} not found")
                    if not isinstance(object_class.fields[element.name], FixedTypeValueField):
                        raise SyntaxError(f"Object definition invalid: field {element.name} not a value field")
                    if element.name in fields:
                        raise SyntaxError(f"Object definition invalid: duplicate definition for field {element.name}")
                    if isinstance(next_token, value.Reference):
                        token_value = c.resolve_value_reference(next_token)
                    else:
                        token_value = next_token
                    field_type = object_class.fields[element.name].type
                    if isinstance(field_type, type.Reference):
                        field_type = c.resolve_type_reference(field_type).type_definition
                    if not field_type.acceptable_value(token_value):
                        raise SyntaxError(f"Object definition invalid: unsuitable type for value field {element.name}: {token_value}")
                    fields[element.name] = next_token
                    i += 1

                elif isinstance(element, SyntaxOptionalGroup):
                    first_element = element.elements[0]
                    if isinstance(first_element, SyntaxLiteral):
                        if not isinstance(next_token, str):
                            continue
                        if next_token != first_element.value:
                            continue
                    i = match_elements(element.elements, i)

                else:
                    util.assert_never(element)

            return i

        match_elements(object_class.syntax, 0)

        for n, f in object_class.fields.items():
            if n in fields:
                continue
            if f.optional:
                fields[n] = None
            elif isinstance(f, TypeField) and f.default is not None:
                fields[n] = f.default
            elif isinstance(f, FixedTypeValueField) and f.default is not None:
                fields[n] = f.default
            else:
                raise SyntaxError(f"Object definition invalid: missing definition for field {n}")

        return DefinedObject(fields=fields)

    def parse_definition(self, object_class: Class, c: context.Context) -> DefinedObject:
        if object_class.syntax is not None:
            if isinstance(self.definition, DefaultSyntax):
                raise SyntaxError("Object defined with default syntax, but object class has defined syntax.")
            return self.parse_definition_defined_syntax(object_class, c)
        else:
            if isinstance(self.definition, DefinedSyntax):
                raise SyntaxError("Object defined with defined syntax, but object class has no defined syntax.")
            raise NotImplementedError()

    @classmethod
    def build_setting(
            cls,
            setting: pyparsing.ParseResults,
            m: module.Module,
            parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
    ) -> typing.Union[type.Type, value.Value]:
        if setting.value:
            return value.build_value(setting.value, m, parameters)
        elif setting.type:
            return type.build_type(setting.type, m, parameters)
        else:
            raise NotImplementedError()

    @classmethod
    def build(
            cls,
            object_def: pyparsing.ParseResults,
            m: module.Module,
            parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
    ) -> "Object":
        if object_def.default_syntax:
            fields = {}
            for field in object_def.default_syntax.field_settings:
                if field.field_name[0].type_field_reference:
                    ref = field.field_name[0].type_field_reference
                    if ref in fields:
                        raise SyntaxError(f"Duplicate field definition in object definition: {ref}")
                elif field.field_name[0].value_field_reference:
                    ref = field.field_name[0].value_field_reference
                    if ref in fields:
                        raise SyntaxError(f"Duplicate field definition in object definition: {ref}")
                else:
                    util.assert_never(field.field_name[0])

                fields[ref] = cls.build_setting(field.setting, m, parameters)
            return cls(
                definition=DefaultSyntax(
                    fields=fields,
                )
            )
        elif object_def.defined_syntax:
            tokens = []
            for token in object_def.defined_syntax.tokens:
                if token.literal:
                    tokens.append(token.literal)
                elif token.setting:
                    tokens.append(cls.build_setting(token.setting, m, parameters))
                else:
                    util.assert_never(token.literal)
            return cls(
                definition=DefinedSyntax(
                    tokens=tokens,
                )
            )
        else:
            util.assert_never(object_def)

@dataclasses.dataclass
class ObjectReference:
    module: module.Module
    value_reference: str
    module_reference: typing.Optional[str] = None
    is_parameter: bool = False

    @classmethod
    def build(
            cls,
            object_def: pyparsing.ParseResults,
            m: module.Module,
            parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
    ) -> "ObjectReference":
        if object_def.object_reference:
            ref = object_def.object_reference[0]
            return cls(
                module=m,
                value_reference=ref,
                is_parameter=bool(parameters and (ref in parameters) and parameters[ref].parameter_type == module.ParameterType.Value),
            )
        elif object_def.external_object_reference:
            return cls(
                module=m,
                value_reference=object_def.external_object_reference.object_reference[0],
                module_reference=object_def.external_object_reference.module_reference[0]
            )
        else:
            util.assert_never(object_def)

ObjectType = typing.Union[Object, ObjectReference]

def build_object(
        object_def: pyparsing.ParseResults,
        m: module.Module,
        parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
) -> ObjectType:
    if object_def.object_definition:
        return Object.build(object_def.object_definition, m, parameters)
    elif object_def.defined_object:
        return ObjectReference.build(object_def.defined_object, m, parameters)
    else:
        raise NotImplementedError()