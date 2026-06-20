import argparse
import pathlib
import sys

import jinja2
import pyparsing
import typing

from .ast import module
from . import context, oid_tree

jinja_env = jinja2.Environment(
    loader=jinja2.PackageLoader("asn1docs"),
    autoescape=jinja2.select_autoescape()
)
MODULE_TEMPLATE = jinja_env.get_template("module.html")
OID_INDEX_TEMPLATE = jinja_env.get_template("oid_index.html")


def render_oid_indexes(nodes: typing.List[oid_tree.OIDNode], c: context.Context, base_path: pathlib.Path):
    for node in nodes[-1].children.values():
        if node.name:
            node_path = base_path / node.name
        else:
            node_path = base_path / str(node.number)

        components = tuple([n.number for n in nodes[1:]] + [node.number])
        if components not in c.oid_modules:
            node_path.mkdir(parents=True, exist_ok=True)
            with open(node_path / "index.html", "w") as f:
                f.write(OID_INDEX_TEMPLATE.render(oid=oid_tree.ObjectIdentifier(
                    components=components,
                    root_node=nodes[0]
                ), node=node, context=c))

        render_oid_indexes(nodes + [node], c, node_path)

def main():
    sys.setrecursionlimit(9000)

    parser = argparse.ArgumentParser(
        prog="ASN1Docs",
        description="Compile ASN.1 modules into HTML documentation."
    )
    parser.add_argument("modules", nargs="+", help="ASN.1 modules to compile")
    parser.add_argument("-o", "--ouptput", required=True, help="Output directory")
    args = parser.parse_args()

    out_dir = pathlib.Path(args.ouptput)

    pyparsing.ParserElement.enable_packrat()

    c = context.Context()
    modules = []

    for filename in args.modules:
        print(f"Generating {filename}", flush=True)
        with open(filename, "r") as f:
            source = f.read()
        modules.append(module.parse_module(source, c.oid_root))

    for m in modules:
        c.add_module(m)

    c.hydrate_values_all()

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
            f.write(MODULE_TEMPLATE.render(module=m, context=c))

    render_oid_indexes([c.oid_root], c, out_dir / "oid")
    with open(out_dir / "oid" / "index.html", "w") as f:
        f.write(OID_INDEX_TEMPLATE.render(oid=None, node=c.oid_root, context=c))


if __name__ == "__main__":
    main()
