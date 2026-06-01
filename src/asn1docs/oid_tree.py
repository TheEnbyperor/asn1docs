import typing
import dataclasses
from .ast import value

@dataclasses.dataclass
class NamedComponent:
    number: int
    name: typing.Optional[str]

@dataclasses.dataclass
class ObjectIdentifier:
    components: typing.Tuple[int, ...]
    root_node: OIDNode

    @property
    def numeric_oid(self) -> typing.Optional[str]:
        return ".".join(str(i) for i in self.components)

    def named_components(self) -> typing.Iterable[NamedComponent]:
        n = self.root_node
        for component in self.components:
            n = n.children[component]
            yield NamedComponent(
                number=n.number,
                name=n.name,
            )

@dataclasses.dataclass
class OIDNode:
    number: int
    name: typing.Optional[str] = None
    children: typing.Dict[int, OIDNode] = dataclasses.field(default_factory=dict)

    @classmethod
    def root(cls):
        return cls(
            number=0,
            name="ROOT",
        )

    def store_oid(self, oid: value.ObjectIdentifier, origin: typing.Optional[ObjectIdentifier] = None) -> ObjectIdentifier:
        nodes = [self]
        if origin is not None:
            for component in origin.components:
                nodes.append(nodes[-1].children[component])
        for component in oid.components:
            if component.number is not None:
                if component.number not in nodes[-1].children:
                    new_node = OIDNode(
                        number=component.number,
                        name=component.name
                    )
                    nodes[-1].children[component.number] = new_node
                    nodes.append(new_node)
                else:
                    next_node = nodes[-1].children[component.number]
                    nodes.append(next_node)
                    if component.name:
                        if next_node.name is None:
                            next_node.name = component.name
                        elif next_node.name != component.name:
                            raise SyntaxError(f"Different name for OID node {'.'.join(str(n.number) for n in nodes[1:])}, expected {next_node.name} found {component.name}")
            elif component.name:
                next_component = next(filter(lambda x: x.name == component.name, nodes[-1].children), None)
                if not next_component:
                    raise SyntaxError(
                        f"Cannot find OID node {component.name} under arc {'.'.join(str(n.number) for n in nodes[1:])}")
                nodes.append(next_component)

        return ObjectIdentifier(
            components=tuple(n.number for n in nodes[1:]),
            root_node=self,
        )


