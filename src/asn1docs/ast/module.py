import typing
import dataclasses
import pyparsing

from . import type, util, javadoc, value, highlight
from .. import parser, oid_tree

@dataclasses.dataclass
class AssignmentParameter:
    is_value: bool
    governor: typing.Optional["type.Type"] = None


@dataclasses.dataclass
class TypeAssignment:
    ASSIGNMENT_TYPE = "TYPE"

    type_definition: "type.Type"
    parameters: typing.Dict[str, AssignmentParameter] = dataclasses.field(default_factory=dict)
    javadoc: typing.Optional["javadoc.JavaDoc"] = None

    def apply_parameters(self, params: typing.List["util.ReferenceParameter"]) -> typing.Dict[str, typing.Optional["util.ReferenceParameter"]]:
        return {
            k: params[i] if i < len(params) else None
            for i, (k, _) in enumerate(self.parameters.items())
        }


@dataclasses.dataclass
class ValueAssignment:
    ASSIGNMENT_TYPE = "VALUE"

    value_type: "type.Type"
    value: "value.Value"
    parameters: typing.Dict[str, AssignmentParameter] = dataclasses.field(default_factory=dict)
    javadoc: typing.Optional["javadoc.JavaDoc"] = None

    def apply_parameters(self, params: typing.List["util.ReferenceParameter"]) -> typing.Dict[str, typing.Optional["util.ReferenceParameter"]]:
        return {
            k: params[i] if i < len(params) else None
            for i, (k, _) in enumerate(self.parameters.items())
        }


def build_assignment_parameters(param_def: pyparsing.ParseResults) -> typing.Dict[str, AssignmentParameter]:
    out = {}
    for parameter in param_def.parameters:
        if parameter.dummy_reference.type_reference:
            name = parameter.dummy_reference.type_reference[0]
            is_value = False
        elif parameter.dummy_reference.value_reference:
            name = parameter.dummy_reference.value_reference[0]
            is_value = True
        else:
            util.assert_never(parameter.dummy_reference)

        if name in out:
            raise SyntaxError(f"Duplicate parameter dummy reference: {name}")

        if parameter.governor:
            if parameter.governor.governor and parameter.governor.governor.type:
                governor = type.build_type(parameter.governor.governor.type[0])
            else:
                raise NotImplementedError(f"Unhandled parameter governor {parameter.governor}")
        else:
            governor = None

        out[name] = AssignmentParameter(
            is_value=is_value,
            governor=governor
        )
    return out

@dataclasses.dataclass
class ModuleImport:
    module_reference: str
    oid: typing.Optional["value.ObjectIdentifier"] = None
    symbols: typing.List[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class ModuleSource:
    head: str
    exports: str
    before_imports: str
    imports: str
    before_assignments: str
    assignments: typing.List[str]
    footer: str

    @property
    def head_spans(self):
        return highlight.to_highlight_spans(self.head)

    @property
    def exports_spans(self):
        return highlight.to_highlight_spans(self.exports)

    @property
    def before_imports_spans(self):
        return highlight.to_highlight_spans(self.before_imports)

    @property
    def imports_spans(self):
        return highlight.to_highlight_spans(self.imports)

    @property
    def before_assignments_spans(self):
        return highlight.to_highlight_spans(self.before_assignments)

    @property
    def assignments_spans(self):
        return [highlight.to_highlight_spans(a) for a in self.assignments]

    @property
    def footer_spans(self):
        return highlight.to_highlight_spans(self.footer)


class Module:
    def __init__(self, module_reference: str):
        self.module_reference = module_reference
        self.oid = None
        self.source = None
        self.assignments = {}
        self.javadoc = None
        self.implicit_all_exports = False
        self.all_exports = False
        self.exports = []
        self.imports: typing.List[ModuleImport] = []

    def set_oid(self, oid: "oid_tree.ObjectIdentifier"):
        self.oid = oid

    def set_source(self, source: ModuleSource):
        self.source = source

    def set_javadoc(self, doc: "javadoc.JavaDoc"):
        self.javadoc = doc

    def add_export(self, symbol: str):
        self.exports.append(symbol)

    def add_import(self, module_import: ModuleImport):
        self.imports.append(module_import)

    def add_assignment(self, symbol: str, assignment: typing.Union[TypeAssignment, ValueAssignment]):
        if symbol in self.assignments:
            raise SyntaxError(f"Duplicate assignment {symbol} in module")
        self.assignments[symbol] = assignment



def parse_module(source: str, oid_root: "oid_tree.OIDNode") -> Module:
    result = parser.ASN1_GRAMMAR.parse_with_tabs().parse_string(source)
    module = Module(
        module_reference=result.ModuleDefinition.module_identifier.module_reference[0]
    )
    if result.ModuleDefinition.module_identifier.definitive_identification:
        if result.ModuleDefinition.module_identifier.definitive_identification.oid:
            oid = result.ModuleDefinition.module_identifier.definitive_identification.oid
        else:
            oid = result.ModuleDefinition.module_identifier.definitive_identification.oid_and_iri.oid
        oid = oid_root.store_oid(value.ObjectIdentifier.build(oid))
        module.set_oid(oid)

    if result.ModuleDefinition.javadoc:
        module.set_javadoc(javadoc.JavaDoc.build(result.ModuleDefinition.javadoc))

    body = result.ModuleDefinition.module_body
    exports = body.value.exports
    imports = body.value.imports
    assignments = result.ModuleDefinition.module_body.value.assignments
    module_source = ModuleSource(
        head=source[0:body.locn_start],
        exports=source[body.locn_start:exports.locn_end] if exports else "",
        before_imports=source[exports.locn_end if exports else body.locn_start:imports.locn_start] if imports else "",
        imports=source[imports.locn_start:imports.locn_end] if imports else "",
        before_assignments=source[
            imports.locn_end if imports else exports.locn_end if exports else body.locn_start:assignments.locn_start] if assignments else "",
        assignments=[],
        footer=source[
            assignments.locn_end if assignments else imports.locn_end if imports else exports.locn_end if exports else body.locn_start:],
    )

    if exports:
        if exports.value.symbols_exported:
            for symbol in exports.value.symbols_exported.symbols:
                module.add_export(symbol[0])
        elif exports.value.all:
            module.all_exports = True
    else:
        module.implicit_all_exports = True

    if imports:
        for import_module in imports.value.symbols_imported.from_modules:
            if import_module.value.from_module.assigned_identifier:
                oid = oid_root.store_oid(
                    value.ObjectIdentifier.build(import_module.value.from_module.assigned_identifier))
            else:
                oid = None
            module.add_import(ModuleImport(
                module_reference=import_module.value.from_module.module_reference[0],
                oid=oid,
                symbols=[s[0] for s in import_module.value.symbols]
            ))

    for assignment_def in assignments.value:
        doc = javadoc.JavaDoc.build(assignment_def.value[0].javadoc) if assignment_def.value[0].javadoc else None
        if ta := assignment_def.value[0].assignment.type_assignment:
            symbol = ta.type_reference[0]
            assignment = TypeAssignment(
                type_definition=type.build_type(ta.type),
                javadoc=doc,
            )
        elif va := assignment_def.value[0].assignment.value_assignment:
            symbol = va.value_reference[0]
            assignment = ValueAssignment(
                value_type=type.build_type(va.type),
                value=value.build_value(va.value),
                javadoc=doc,
            )
        elif pa := assignment_def.value[0].assignment.parameterised_assignment:
            if ta := pa.type_assignment:
                symbol = ta.type_reference[0]
                parameters = build_assignment_parameters(ta.parameters)
                assignment = TypeAssignment(
                    type_definition=type.build_type(ta.type[0], parameters),
                    javadoc=doc,
                    parameters=parameters,
                )
            else:
                raise NotImplementedError(f"Unhandled parameterised assignment {pa}")
        else:
            raise NotImplementedError(f"Unhandled assignment {assignment_def.value[0].assignment}")
        module.add_assignment(symbol, assignment)
        module_source.assignments.append(source[assignment_def.locn_start:assignment_def.locn_end])

    module.set_source(module_source)

    return module
