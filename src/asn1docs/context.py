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

    def resolve_class_reference(self, ref: typing.Union[object.ObjectClass, object.ClassReference]) -> object.ObjectClass:
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
                raise NotImplementedError("OID relative to module without OID not implemented")
        else:
            current_oid = oid

        common_components = 0
        for c1, c2 in zip(truncated_oid.components, current_oid.components):
            if c1 == c2:
                common_components += 1
            else:
                break
        backtrack_needed = len(current_oid.components) - common_components
        components = "".join(["../" for _ in range(backtrack_needed)])
        for c in list(truncated_oid.named_components())[common_components:]:
            if c.name:
                components += f"{c.name}/"
            else:
                components += f"{str(c.number)}/"

        return components