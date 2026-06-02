# ITU-T X.680 Section 13 module

import pyparsing
from . import lexical_items
from . import values_types
from . import object_identifier
from . import javadoc
from . import parametisation
from . import object_class

# Keywords used in clause 13
DEFINITIONS = pyparsing.Keyword("DEFINITIONS")
BEGIN = pyparsing.Keyword("BEGIN")
END = pyparsing.Keyword("END")
INSTRUCTIONS = pyparsing.Keyword("INSTRUCTIONS")
EXPLICIT = pyparsing.Keyword("EXPLICIT")
IMPLICIT = pyparsing.Keyword("IMPLICIT")
AUTOMATIC = pyparsing.Keyword("AUTOMATIC")
TAGS = pyparsing.Keyword("TAGS")
EXTENSIBILITY = pyparsing.Keyword("EXTENSIBILITY")
IMPLIED = pyparsing.Keyword("IMPLIED")
EXPORTS = pyparsing.Keyword("EXPORTS")
IMPORTS = pyparsing.Keyword("IMPORTS")
FROM = pyparsing.Keyword("FROM")
WITH = pyparsing.Keyword("WITH")
SUCCESSORS = pyparsing.Keyword("SUCCESSORS")
DESCENDANTS = pyparsing.Keyword("DESCENDANTS")
ALL = pyparsing.Keyword("ALL")

ModuleIdentifier = pyparsing.Forward()
IRIValue = pyparsing.Forward()
DefinitiveIdentification = pyparsing.Forward()
DefinitiveOID = pyparsing.Forward()
DefinitiveOIDandIRI = pyparsing.Forward()
DefinitiveObjIdComponentList = pyparsing.Forward()
DefinitiveObjIdComponent = pyparsing.Forward()
DefinitiveNumberForm = pyparsing.Forward()
DefinitiveNameAndNumberForm = pyparsing.Forward()
EncodingReferenceDefault = pyparsing.Forward()
TagDefault = pyparsing.Forward()
ExtensionDefault = pyparsing.Forward()
ModuleBody = pyparsing.Forward()
Exports = pyparsing.Forward()
SymbolsExported = pyparsing.Forward()
Imports = pyparsing.Forward()
SymbolsImported = pyparsing.Forward()
SymbolsFromModuleList = pyparsing.Forward()
SymbolsFromModule = pyparsing.Forward()
SelectionOption = pyparsing.Forward()
GlobalModuleReference = pyparsing.Forward()
AssignedIdentifier = pyparsing.Forward()
SymbolList = pyparsing.Forward()
Symbol = pyparsing.Forward()
AssignmentList = pyparsing.Forward()
DocumentedAssignment = pyparsing.Forward()
Assignment = pyparsing.Forward()
EncodingControlSections = pyparsing.Forward()

ModuleDefinition = pyparsing.Group(
    pyparsing.Optional(javadoc.javadoc("javadoc"))
    + ModuleIdentifier("module_identifier")
    + DEFINITIONS
    + pyparsing.Optional(EncodingReferenceDefault("encoding_reference_default"))
    + pyparsing.Optional(TagDefault("tag_default"))
    + pyparsing.Optional(ExtensionDefault("extension_default"))
    + pyparsing.Suppress("::=")
    + BEGIN
    + ModuleBody("module_body")
    # TODO: section 54
    # + EncodingControlSections("encoding_control_sections")
    + END
)("ModuleDefinition")

ModuleIdentifier <<= pyparsing.Group(
    lexical_items.modulereference("module_reference")
    + pyparsing.Optional(DefinitiveIdentification("definitive_identification"))
)

DefinitiveIdentification <<= pyparsing.Group(DefinitiveOIDandIRI("oid_and_iri") | DefinitiveOID("oid"))

DefinitiveOID <<= pyparsing.Group(
    pyparsing.Suppress("{")
    + DefinitiveObjIdComponentList("components")
    + pyparsing.Suppress("}")
)

DefinitiveOIDandIRI <<= pyparsing.Group(
    DefinitiveOID("oid")
    + IRIValue("iri")
)

DefinitiveObjIdComponentList <<= pyparsing.Group(
    DefinitiveObjIdComponent
    + pyparsing.ZeroOrMore(DefinitiveObjIdComponent)
)

DefinitiveObjIdComponent <<= pyparsing.Group(
    DefinitiveNumberForm
    | DefinitiveNameAndNumberForm
    | object_identifier.NameForm
)

DefinitiveNumberForm <<= lexical_items.number("number")

DefinitiveNameAndNumberForm <<= (
        lexical_items.identifier("name")
        + pyparsing.Suppress("(")
        + DefinitiveNumberForm
        + pyparsing.Suppress(")")
)

EncodingReferenceDefault <<= pyparsing.Group(
    lexical_items.encodingreference("encoding_reference")
    + INSTRUCTIONS
)

TagDefault <<= pyparsing.Group(
    (EXPLICIT("mode") | IMPLICIT("mode") | AUTOMATIC("mode"))
    + TAGS
)

ExtensionDefault <<= pyparsing.Group(
    EXTENSIBILITY
    + IMPLIED
)

ModuleBody <<= pyparsing.Group(pyparsing.Located(
    pyparsing.Optional(Exports("exports"))
    + pyparsing.Optional(Imports("imports"))
    + pyparsing.Optional(AssignmentList("assignments"))
))

Exports <<= pyparsing.Group(pyparsing.Located(
    EXPORTS
    + (pyparsing.Group(ALL)("all") | SymbolsExported("symbols_exported"))
    + lexical_items.SEMI
))

SymbolsExported <<= pyparsing.Group(SymbolList("symbols"))

Imports <<= pyparsing.Group(pyparsing.Located(
    IMPORTS
    + SymbolsImported("symbols_imported")
    + lexical_items.SEMI
))

SymbolsImported <<= pyparsing.Group(SymbolsFromModuleList("from_modules"))

SymbolsFromModuleList <<= pyparsing.Group(pyparsing.OneOrMore(SymbolsFromModule))

SymbolsFromModule <<= pyparsing.Group(pyparsing.Located(
    SymbolList("symbols")
    + FROM
    + GlobalModuleReference("from_module")
    + pyparsing.Optional(SelectionOption("selection_option"))
))

SelectionOption <<= (
    pyparsing.Group(WITH + SUCCESSORS)
    | pyparsing.Group(WITH + DESCENDANTS)
)

GlobalModuleReference <<= pyparsing.Group(
    lexical_items.modulereference("module_reference")
    + pyparsing.Optional(AssignedIdentifier("assigned_identifier"))
)

AssignedIdentifier <<= (object_identifier.ObjectIdentifierValue("oid") | values_types.DefinedValue)

SymbolList <<= pyparsing.Group(pyparsing.delimitedList(values_types.Reference))

values_types.Reference <<= pyparsing.Group(
    lexical_items.objectclassreference("object_class_reference")
    ^ lexical_items.typereference("type_reference")
    ^ lexical_items.valuereference("value_reference")
)

AssignmentList <<= pyparsing.Group(pyparsing.Located(pyparsing.OneOrMore(pyparsing.Group(pyparsing.Located(DocumentedAssignment)))))

DocumentedAssignment <<= pyparsing.Group(
    pyparsing.Optional(javadoc.javadoc("javadoc")) +
    Assignment("assignment")
)

Assignment <<= pyparsing.Group(
    object_class.ObjectClassAssignment("object_class_assignment")
    | object_class.ObjectAssignment("object_assignment")
    | object_class.ObjectSetAssignment("object_set_assignment")
    | parametisation.ParameterizedAssignment("parameterised_assignment")
    | values_types.TypeAssignment("type_assignment")
    | values_types.ValueAssignment("value_assignment")
    | values_types.ValueSetTypeAssignment("value_set_assignment")
)

