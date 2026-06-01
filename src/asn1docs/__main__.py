import argparse
import pathlib
import jinja2
import pyparsing
import typing

from .ast import module, value, type
from . import oid_tree

jinja_env = jinja2.Environment(
    loader=jinja2.PackageLoader("asn1docs"),
    autoescape=jinja2.select_autoescape()
)
MODULE_TEMPLATE = jinja_env.get_template("module.html")
OID_INDEX_TEMPLATE = jinja_env.get_template("oid_index.html")

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
        if ref.module_reference:
            return True
        elif isinstance(ref, value.Reference) and ref.value_reference in current_module.assignments:
            return False
        elif isinstance(ref, type.Reference) and ref.type_reference in current_module.assignments:
            return False
        else:
            return True

    def module_relative_link(self, ref: typing.Union[value.Reference, type.Reference], current_module: module.Module):
        if isinstance(ref, value.Reference):
            symbol = ref.value_reference
        elif isinstance(ref, type.Reference):
            symbol = ref.type_reference
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

    def resolve_reference(self, symbol: str, module_reference: typing.Optional[str], current_module: module.Module) -> typing.Union[
        module.TypeAssignment, module.ValueAssignment]:
        if module_reference:
            raise NotImplementedError("Reference via module reference not implemented")

        if symbol in current_module.assignments:
            return current_module.assignments[symbol]

        module_import = next(filter(lambda i: symbol in i.symbols, current_module.imports), None)
        if not module_import:
            raise ValueError(f"External reference {symbol} is not imported")

        if module_import.oid:
            imported_module = self.oid_modules.get(module_import.oid.components)
        else:
            imported_module = self.name_modules.get(module_import.module_reference)

        if not imported_module:
            raise ValueError(f"Module {module_import.module_reference} not found")
        if symbol not in imported_module.assignments:
            raise ValueError(
                f"External reference {symbol} is present in imported module {imported_module.module_reference}")
        return imported_module.assignments[symbol]

    def resolve_type_reference(self, ref: type.Reference, current_module: module.Module) -> module.TypeAssignment:
        assignment = self.resolve_reference(ref.type_reference, ref.module_reference, current_module)
        if not isinstance(assignment, module.TypeAssignment):
            raise ValueError(f"Type reference {ref.type_reference} is not a type assignment")
        return assignment

    def resolve_value_reference(self, ref: value.Reference, current_module: module.Module) -> module.ValueAssignment:
        assignment = self.resolve_reference(ref.value_reference, ref.module_reference, current_module)
        if not isinstance(assignment, module.ValueAssignment):
            raise ValueError(f"Value reference {ref.value_reference} is not a value assignment")
        return assignment

    def store_oid(self, oid: value.ObjectIdentifier, current_module: module.Module) -> oid_tree.ObjectIdentifier:
        if oid.origin:
            origin_value = self.resolve_value_reference(oid.origin, current_module)
            if not isinstance(origin_value.value, value.ObjectIdentifier):
                raise ValueError(f"OID origin {oid.origin} is not an object identifier")
            origin = self.store_oid(origin_value.value, current_module)
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

def render_oid_indexes(nodes: typing.List[oid_tree.OIDNode], context: Context, base_path: pathlib.Path):
    for node in nodes[-1].children.values():
        if node.name:
            node_path = base_path / node.name
        else:
            node_path = base_path / str(node.number)

        components = tuple([n.number for n in nodes[1:]] + [node.number])
        if components not in context.oid_modules:
            node_path.mkdir(parents=True, exist_ok=True)
            with open(node_path / "index.html", "w") as f:
                f.write(OID_INDEX_TEMPLATE.render(oid=oid_tree.ObjectIdentifier(
                    components=components,
                    root_node=nodes[0]
                ), node=node, context=context))

        render_oid_indexes(nodes + [node], context, node_path)

def main():
    parser = argparse.ArgumentParser(
        prog="ASN1Docs",
        description="Compile ASN.1 modules into HTML documentation."
    )
    parser.add_argument("modules", nargs="+", help="ASN.1 modules to compile")
    parser.add_argument("-o", "--ouptput", required=True, help="Output directory")
    args = parser.parse_args()

    out_dir = pathlib.Path(args.ouptput)

    pyparsing.ParserElement.enable_packrat()

    context = Context()
    modules = []

    for filename in args.modules:
        print(f"Generating {filename}", flush=True)
        with open(filename, "r") as f:
            source = f.read()
        modules.append(module.parse_module(source, context.oid_root))

    for m in modules:
        context.add_module(m)

    for m in modules:
        print(f"Rendering {m.module_reference}", flush=True)
        module_dir = out_dir
        if m.oid:
            module_dir = module_dir / "oid"
            for component in m.oid.named_components():
                if component.name:
                    module_dir = module_dir / component.name
                else:
                    module_dir = module_dir / str(component.number)
        else:
            module_dir = module_dir / "without-oid" / m.module_reference
        module_out_path = module_dir / "index.html"
        module_dir.mkdir(parents=True, exist_ok=True)
        with open(module_out_path, "w") as f:
            f.write(MODULE_TEMPLATE.render(module=m, context=context))

    render_oid_indexes([context.oid_root], context, out_dir / "oid")
    with open(out_dir / "oid" / "index.html", "w") as f:
        f.write(OID_INDEX_TEMPLATE.render(oid=None, node=context.oid_root, context=context))


if __name__ == "__main__":
    main()
