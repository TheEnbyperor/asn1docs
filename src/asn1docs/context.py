import typing
from .ast import module, value, type, object, util
from . import oid_tree

class Context:
    oid_modules: typing.Dict[typing.Tuple[int], module.Module]
    name_modules: typing.Dict[str, module.Module]
    oid_root: oid_tree.OIDNode

    def __init__(self):
        self.oid_modules = {}
        self.name_modules = {}
        self.oid_root = oid_tree.OIDNode.root()
        self.hydration_type_cache = {}

    def add_module(self, m: module.Module):
        if m.oid:
            if m.oid.components in self.oid_modules:
                raise ValueError(f"Duplicate module OID {m.oid.numeric_oid()}")
            self.oid_modules[m.oid.components] = m
        else:
            if m.module_reference in self.name_modules:
                raise ValueError(f"Duplicate module reference {m.module_reference}")
            self.name_modules[m.module_reference] = m

    @staticmethod
    def is_external_reference(ref: typing.Union[value.Reference, type.Reference], current_module: module.Module) -> bool:
        if ref.module != current_module:
            return True
        if ref.module_reference:
            return True
        if isinstance(ref, value.Reference) and ref.value_reference in current_module.assignments:
            return False
        if isinstance(ref, type.Reference) and ref.type_reference in current_module.assignments:
            return False
        if isinstance(ref, object.ClassReference) and ref.class_reference in current_module.assignments:
            return False
        if isinstance(ref, object.SetReference) and ref.value_reference in current_module.assignments:
            return False
        return True

    def module_relative_link(self, ref: typing.Union[value.Reference, type.Reference], current_module: module.Module):
        if isinstance(ref, value.Reference) or isinstance(ref, object.SetReference):
            symbol = ref.value_reference
        elif isinstance(ref, type.Reference):
            symbol = ref.type_reference
        elif isinstance(ref, object.ClassReference):
            symbol = ref.class_reference
        else:
            util.assert_never(ref)
        if ref.module != current_module:
            if symbol in ref.module.assignments:
                if ref.module.oid:
                    return self.oid_relative_link(ref.module.oid, -1, current_module)
                else:
                    raise NotImplementedError("External reference to a non-OID import not implemented")

            if ref.module_reference:
                module_import = next(filter(lambda i: i.module_reference == ref.module_reference, ref.module.imports), None)
            else:
                module_import = next(filter(lambda i: symbol in i.symbols, ref.module.imports), None)
        else:
            if ref.module_reference:
                module_import = next(filter(lambda i: i.module_reference == ref.module_reference, current_module.imports), None)
            else:
                module_import = next(filter(lambda i: symbol in i.symbols, current_module.imports), None)

        if not module_import:
            raise ValueError(f"External reference {symbol} is not imported")
        if module_import.oid:
            return self.oid_relative_link(module_import.oid, -1, current_module)
        else:
            raise NotImplementedError("External reference to a non-OID import not implemented")

    def get_module_by_oid(self, components: typing.Iterable[int]) -> typing.Optional[module.Module]:
        components = tuple(components)
        return self.oid_modules.get(components)

    def resolve_reference(self, symbol: str, module_reference: typing.Optional[str], reference_module: module.Module) -> typing.Union[
        module.TypeAssignment, module.ValueAssignment]:
        if not module_reference and symbol in reference_module.assignments:
            return reference_module.assignments[symbol]

        if module_reference:
            module_import = next(filter(lambda i: i.module_reference == module_reference, reference_module.imports), None)
            if not module_import:
                raise ValueError(f"Module {module_reference} is not imported")
        else:
            module_import = next(filter(lambda i: symbol in i.symbols, reference_module.imports), None)
            if not module_import:
                raise ValueError(f"External reference {symbol} is not imported")

        if module_import.oid:
            imported_module = self.oid_modules.get(module_import.oid.components)
        else:
            imported_module = self.name_modules.get(module_import.module_reference)

        if not imported_module:
            raise ValueError(f"Module {module_import.module_reference} not found")

        if symbol not in imported_module.assignments:
            raise ValueError(f"External reference {symbol} is not present in imported module {imported_module.module_reference}")
        if not imported_module.all_exports and not imported_module.implicit_all_exports and symbol not in imported_module.exports:
            raise ValueError(f"External reference {symbol} is not exported from imported module {imported_module.module_reference}")
        return imported_module.assignments[symbol]

    def resolve_type_reference(self, ref: type.Reference) -> module.TypeAssignment:
        assignment = self.resolve_reference(ref.type_reference, ref.module_reference, ref.module)
        if not isinstance(assignment, module.TypeAssignment):
            raise ValueError(f"Type reference {ref.type_reference} is not a type assignment")
        return assignment

    def resolve_value_reference(self, ref: value.Value) -> value.Value:
        if not isinstance(ref, value.Reference):
            return ref
        assignment = self.resolve_reference(ref.value_reference, ref.module_reference, ref.module)
        if not isinstance(assignment, module.ValueAssignment):
            raise ValueError(f"Value reference {ref.value_reference} is not a value assignment")
        return assignment.value

    def resolve_class_reference(self, ref: typing.Union[object.Class, object.ClassReference]) -> object.Class:
        if not isinstance(ref, object.ClassReference):
            return ref
        assignment = self.resolve_reference(ref.class_reference, ref.module_reference, ref.module)
        if not isinstance(assignment, module.ObjectClassAssignment):
            raise ValueError(f"Class reference {ref.class_reference} is not an object class assignment")
        return assignment.object

    def resolve_object_reference(self, ref: typing.Union[object.Object, object.ObjectReference, value.Reference]) -> object.Object:
        if not isinstance(ref, object.ObjectReference) and not isinstance(ref, value.Reference):
            return ref
        assignment = self.resolve_reference(ref.value_reference, ref.module_reference, ref.module)
        if not isinstance(assignment, module.ObjectAssignment):
            raise ValueError(f"Object reference {ref.value_reference} is not an object assignment")
        return assignment.object

    def store_oid(self, oid: value.ObjectIdentifier, current_module: module.Module) -> oid_tree.ObjectIdentifier:
        if oid.origin:
            origin_value = self.resolve_value_reference(oid.origin)
            if not isinstance(origin_value, value.ObjectIdentifier):
                raise ValueError(f"OID origin {oid.origin} is not an object identifier")
            origin = self.store_oid(origin_value, current_module)
        else:
            origin = None

        return self.oid_root.store_oid(oid, origin)

    def oid_relative_link(self, oid: oid_tree.ObjectIdentifier, index: int, current_module: typing.Optional[
        module.Module]) -> str:
        if index == -1:
            index = len(oid.components)
        truncated_oid = oid_tree.ObjectIdentifier(
            components=tuple(oid.components[:index]),
            root_node=self.oid_root,
        )
        if current_module:
            if current_module.oid:
                current_oid = current_module.oid
            else:
                current_oid = None
        else:
            current_oid = oid

        common_components = 0
        if current_oid is not None:
            for c1, c2 in zip(truncated_oid.components, current_oid.components):
                if c1 == c2:
                    common_components += 1
                else:
                    break
            backtrack_needed = len(current_oid.components) - common_components
            components = "".join(["../" for _ in range(backtrack_needed)])
        else:
            components = "../../oid/"

        for c in list(truncated_oid.named_components())[common_components:]:
            if c.name:
                components += f"{c.name}/"
            else:
                components += f"{str(c.number)}/"

        return components

    def hydrate_values_all(self):
        for m in self.oid_modules.values():
            self.hydrate_values(m)
        for m in self.name_modules.values():
            self.hydrate_values(m)

    def hydrate_values(self, m: module.Module):
        for assignment in m.assignments.values():
            if not isinstance(assignment, module.ValueAssignment):
                continue
            if new_val := self.hydrate_value(self.hydrate_type(assignment.value_type), assignment.value):
                assignment.value = new_val

    def hydrate_value(self, type_def: type.Type, val: value.Value) -> typing.Optional[value.Value]:
        if isinstance(type_def, type.Sequence):
            return self.hydrate_sequence(type_def, val)
        elif isinstance(type_def, type.SequenceOf):
            return self.hydrate_sequence_of(type_def, val)
        elif isinstance(type_def, type.Choice):
            return self.hydrate_choice(type_def, val)
        elif isinstance(type_def, type.Enumeration):
            return self.hydrate_enumeration(type_def, val)
        elif isinstance(type_def, type.ConstrainedType):
            return self.hydrate_value(type_def.inner_type_definition, val)
        else:
            return None

    def hydrate_type(self, type_def: type.Type, parameters: typing.Dict[str, type.Type] = None) -> type.Type:
        if parameters is None:
            parameters = {}

        type_key = (id(type_def), tuple((k, id(v)) for k, v in parameters.items()))
        if type_key in self.hydration_type_cache:
            return self.hydration_type_cache[type_key]
        elif isinstance(type_def, type.Reference):
            if type_def.is_parameter:
                if type_def.type_reference not in parameters:
                    raise SyntaxError(f"Parameter {type_def.type_reference} is not defined")
                return parameters[type_def.type_reference]
            else:
                assignment = self.resolve_type_reference(type_def)
                return self.hydrate_parameters(type_def, assignment, parameters)
        elif isinstance(type_def, type.ObjectClassField):
            object_class = self.resolve_class_reference(type_def.object_class)
            if type_def.field[0] not in object_class.fields:
                raise SyntaxError(f"Field {type_def.field} is not defined on object class")
            field = object_class.fields[type_def.field[0]]
            if not isinstance(field, object.FixedTypeValueField):
                raise SyntaxError(f"Field {type_def.field} on object class does not have at type")
            return field.type
        elif isinstance(type_def, type.Sequence):
            new_type = type.Sequence(components={})
            self.hydration_type_cache[type_key] = new_type
            new_type.components = {
                k: type.SequenceComponent(
                    type_definition=self.hydrate_type(v.type_definition, parameters),
                    optional=v.optional,
                    default=v.default,
                    javadoc=v.javadoc,
                ) for k, v in type_def.components.items()
            }
            return new_type
        elif isinstance(type_def, type.SequenceOf):
            new_type = type.SequenceOf(inner_type_definition=None)
            self.hydration_type_cache[type_key] = new_type
            new_type.inner_type_definition = self.hydrate_type(type_def.inner_type_definition, parameters)
            return new_type
        elif isinstance(type_def, type.Choice):
            new_type = type.Choice(components={})
            self.hydration_type_cache[type_key] = new_type
            new_type.components = {
                k: type.ChoiceComponent(
                    type_definition=self.hydrate_type(v.type_definition, parameters),
                    javadoc=v.javadoc,
                ) for k, v in type_def.components.items()
            }
            return new_type
        else:
            return type_def

    def hydrate_parameters(
            self, type_def: type.Reference, assignment: module.TypeAssignment, parameters: typing.Dict[str, type.Type]
    ) -> typing.Union[type.Type, object.Set]:
        inner_type_def = assignment.type_definition
        if assignment.parameters:
            if len(type_def.parameters) != len(assignment.parameters):
                raise SyntaxError(f"Invalid number of parameters for {type_def.type_reference}")

            for (param_name, param), param_value in zip(assignment.parameters.items(), type_def.parameters):
                if param.parameter_type == module.ParameterType.Type:
                    if param_value.is_value:
                        raise SyntaxError(f"Value given to type parameter {param_name}")

                    if isinstance(param_value.value, type.Reference):
                        assignment = self.resolve_reference(param_value.value.type_reference,
                                                            param_value.value.module_reference,
                                                            param_value.value.module)
                        if isinstance(assignment, module.TypeAssignment):
                            param_value_type = self.hydrate_parameters(param_value.value, assignment, parameters)
                        elif isinstance(assignment, module.ObjectSetAssignment):
                            return assignment.object_set
                    else:
                        param_value_type = self.hydrate_type(param_value.value, parameters)

                    parameters[param_name] = param_value_type

        return self.hydrate_type(inner_type_def, parameters)

    def hydrate_sequence(self, type_def: type.Sequence, val: value.Value) -> typing.Optional[value.Value]:
        if not isinstance(val, value.Sequence):
            raise SyntaxError(f"Non-sequence value assigned to sequence type, got {val.VALUE_TYPE}")
        for field_name, field in type_def.components.items():
            if not (field.optional or field.default) and field_name not in val.fields:
                raise SyntaxError(f"Non-optional sequence field {field_name} not set")
            if field_name in val.fields:
                if new_val := self.hydrate_value(self.hydrate_type(field.type_definition), val.fields[field_name].value):
                    val.fields[field_name].value = new_val
        for field_name in val.fields.keys():
            if field_name not in type_def.components:
                raise SyntaxError(f"sequence field {field_name} does not exist")

    def hydrate_sequence_of(self, type_def: type.SequenceOf, val: value.Value) -> typing.Optional[value.Value]:
        if not isinstance(val, value.SequenceOf):
            raise SyntaxError(f"Non-sequence-of value assigned to sequence-of type, got {val.VALUE_TYPE}")
        inner_type = self.hydrate_type(type_def.inner_type_definition)
        for i, v in enumerate(val.values):
            if new_val := self.hydrate_value(inner_type, v):
                val.values[i] = new_val

    def hydrate_choice(self, type_def: type.Choice, val: value.Value) -> typing.Optional[value.Value]:
        if not isinstance(val, value.Choice):
            raise SyntaxError(f"Non-choice value assigned to choice type, got {val.VALUE_TYPE}")
        if val.variant not in type_def.components:
            raise SyntaxError(f"Choice variant {val.variant} does not exist")
        variant = type_def.components[val.variant]
        if new_val := self.hydrate_value(self.hydrate_type(variant.type_definition), val.value):
            val.value = new_val

    def hydrate_enumeration(self, type_def: type.Enumeration, val: value.Value) -> typing.Optional[value.Value]:
        if isinstance(val, value.Reference):
            if val.module_reference:
                return
            enum_value = next(filter(lambda e: e.name == val.value_reference, type_def.values), None)
            if enum_value:
                return value.Enumeration(
                    value=val.value_reference
                )