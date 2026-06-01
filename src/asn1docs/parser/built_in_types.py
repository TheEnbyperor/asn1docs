import pyparsing
from . import lexical_items
from . import values_types
from . import object_identifier
from . import constructed_types
from . import constraints
from . import javadoc

BooleanType = pyparsing.Forward()
BooleanValue = pyparsing.Forward()
IntegerType = pyparsing.Forward()
IntegerValue = pyparsing.Forward()
EnumeratedType = pyparsing.Forward()
EnumeratedValue = pyparsing.Forward()
RealType = pyparsing.Forward()
RealValue = pyparsing.Forward()
BitStringType = pyparsing.Forward()
BitStringValue = pyparsing.Forward()
OctetStringType = pyparsing.Forward()
OctetStringValue = pyparsing.Forward()
NullType = pyparsing.Forward()
NullValue = pyparsing.Forward()
PrefixedType = pyparsing.Forward()
PrefixedValue = pyparsing.Forward()
TaggedType = pyparsing.Forward()
Tag = pyparsing.Forward()
EncodingReference = pyparsing.Forward()
ClassNumber = pyparsing.Forward()
Class = pyparsing.Forward()
EncodingPrefixedType = pyparsing.Forward()
EncodingPrefix = pyparsing.Forward()
EmbeddedPDVType = pyparsing.Forward()
EmbeddedPDVValue = pyparsing.Forward()
ExternalType = pyparsing.Forward()
ExternalValue = pyparsing.Forward()
TimeType = pyparsing.Forward()
TimeValue = pyparsing.Forward()
DateType = pyparsing.Forward()
TimeOfDayType = pyparsing.Forward()
DateTimeType = pyparsing.Forward()
DurationType = pyparsing.Forward()
CharacterStringType = pyparsing.Forward()
CharacterStringValue = pyparsing.Forward()
UsefulType = pyparsing.Forward()
ExceptionIdentification = pyparsing.Forward()

# ITU-T X.680 Section 17

BuiltinType = pyparsing.Forward()
BuiltinValue = pyparsing.Forward()
ReferencedType = pyparsing.Forward()
ReferencedValue = pyparsing.Forward()

# 17.1
values_types.Type <<= pyparsing.Group(
    constraints.ConstrainedType("constrained_type")
    | BuiltinType("built_in_type")
    | ReferencedType("referenced_type")
)

values_types.UnconstrainedType <<= pyparsing.Group(
    ReferencedType("referenced_type")
    ^ BuiltinType("built_in_type")
)

# 17.2
BuiltinType <<= pyparsing.Group(
    # BitStringType
    NullType("null_type")
    | BooleanType("boolean_type")
    | IntegerType("integer_type")
    | OctetStringType("octet_string_type")
    | CharacterStringType("character_string_type")
    | object_identifier.ObjectIdentifierType("object_identifier_type")
    | object_identifier.IRIType("iri_type")
    | object_identifier.RelativeOIDType("relative_oid_type")
    | object_identifier.RelativeIRIType("relative_iri_type")
    | EnumeratedType("enumerated_type")
    | constructed_types.ChoiceType("choice_type")
    | constructed_types.SequenceOfType("sequence_of_type")
    | constructed_types.SequenceType("sequence_type")
    | constructed_types.SetOfType("set_of_type")
    | constructed_types.SetType("set_type")
    # ^ DateType
    # ^ DateTimeType
    # ^ DurationType
    # ^ EmbeddedPDVType
    # ^ ExternalType
    # TODO: ITU-T X.681
    # | InstanceOfType
    # TODO: ITU-T X.681
    # | ObjectClassFieldType
    # ^ RealType
    # ^ PrefixedType
    # ^ TimeType
    # ^ TimeOfDayType
)

# 17.3
ReferencedType <<= pyparsing.Group(
    values_types.DefinedType("defined_type")
    | UsefulType("useful_type")
    | constructed_types.SelectionType("selection_type")
    # TODO: ITU-T X.681
    # | TypeFromObject
    # | ValueSetFromObjects
)

# 17.5
values_types.NamedType <<= pyparsing.Group(
    lexical_items.identifier("type_name") + values_types.Type("type")
)

# 17.7
values_types.Value <<= pyparsing.Group(
    ReferencedValue("referenced_value")
    ^ BuiltinValue("built_in_value")
    # TODO: ITU-T X.681
    # | ObjectClassFieldValue
)

# 17.9
BuiltinValue <<= pyparsing.Group(
    constructed_types.ChoiceValue("choice_value")
    | constructed_types.SequenceValue("sequence_value")
    | constructed_types.SequenceOfValue("sequence_of_value")
    | EnumeratedValue
    | NullValue("null_value")
    | BooleanValue("boolean_value")
    | IntegerValue("integer_value")
    | CharacterStringValue("character_string_value")
    | OctetStringValue("octet_string_value")
    | object_identifier.ObjectIdentifierValue("object_identifier_value")
    # BitStringValue
    # ^ EmbeddedPDVValue
    # ^ ExternalValue
    # TODO: ITU-T X.681
    # | InstanceOfValue
    # ^ object_identifier.IRIValue
    # ^ RealValue
    # ^ object_identifier.RelativeIRIValue
    # ^ object_identifier.RelativeOIDValue
    # ^ PrefixedValue
    # ^ TimeValue
)

# 17.11
ReferencedValue <<= pyparsing.Group(
    values_types.DefinedValue("defined_value")
    # TODO: ITU-T X.681
    # | ValueFromObject
)

# 17.13
values_types.NamedValue <<= pyparsing.Group(
    lexical_items.identifier("name") + values_types.Value("value")
)

# ITU-T X.680 Section 18

# 18.1
BooleanType <<= pyparsing.Keyword("BOOLEAN")

# 18.2
BooleanValue <<= pyparsing.Keyword("TRUE") | pyparsing.Keyword("FALSE")

# ITU-T X.680 Section 19

NamedNumberList = pyparsing.Forward()
NamedNumber = pyparsing.Forward()

# 19.1
IntegerType <<= (
    (pyparsing.Keyword("INTEGER") + lexical_items.LBRACE + NamedNumberList("named_numbers") + lexical_items.RBRACE)
    | pyparsing.Keyword("INTEGER")
)

NamedNumberList <<= pyparsing.Group(pyparsing.delimited_list(
    NamedNumber("named_number"),
    delim=lexical_items.COMMA,
    min=1
))

NamedNumber <<= pyparsing.Group(
    lexical_items.identifier("identifier") + lexical_items.LPAR + values_types.SignedNumber("number") + lexical_items.RPAR
    | lexical_items.identifier("identifier") + lexical_items.LPAR + values_types.DefinedValue("defined_value") + lexical_items.RPAR
)

values_types.SignedNumber <<= pyparsing.Group(
    pyparsing.Group(lexical_items.HYPHEN + lexical_items.number("number"))("negative_number")
    | lexical_items.number("positive_number")
)

# 19.9
IntegerValue <<= pyparsing.Group(
    values_types.SignedNumber("signed_number")
    | lexical_items.identifier
)

# ITU-T X.680 Section 20

Enumerations = pyparsing.Forward()
Enumeration = pyparsing.Forward()
DocumentedEnumerationItem = pyparsing.Forward()
EnumerationItem = pyparsing.Forward()

# 20.1
EnumeratedType <<= pyparsing.Group(
    pyparsing.Keyword("ENUMERATED") + lexical_items.LBRACE + Enumerations("enumerations") + lexical_items.RBRACE
)

Enumerations <<= pyparsing.Group(
    (Enumeration("enumeration") + lexical_items.COMMA + lexical_items.ellipsis + values_types.ExceptionSpec + lexical_items.COMMA + Enumeration)
    | (Enumeration("enumeration") + lexical_items.COMMA + lexical_items.ellipsis + values_types.ExceptionSpec)
    | Enumeration("enumeration")
)

Enumeration <<= pyparsing.Group(pyparsing.DelimitedList(
    DocumentedEnumerationItem,
    delim=lexical_items.COMMA,
    min=1
))

DocumentedEnumerationItem <<= pyparsing.Group(
    pyparsing.Optional(javadoc.javadoc("javadoc")) +
    EnumerationItem("enumeration_item")
)

EnumerationItem <<= pyparsing.Group(
    NamedNumber("named_number")
    | lexical_items.identifier("identifier")
)

# 20.8
EnumeratedValue <<= lexical_items.identifier("enumerated_value")

# ITU-T X.680 Section 21

NumericRealValue = pyparsing.Forward()
SpecialRealValue = pyparsing.Forward()

# 21.1
RealType <<= pyparsing.Keyword("REAL")

# 21.6
RealValue <<= pyparsing.Group(
    NumericRealValue
    | SpecialRealValue
)

NumericRealValue <<= pyparsing.Group(
    lexical_items.realnumber
    | lexical_items.HYPHEN + lexical_items.realnumber
    | constructed_types.SequenceValue
)

SpecialRealValue <<= pyparsing.Group(
    pyparsing.Keyword("PLUS-INFINITY")
    | pyparsing.Keyword("MINUS-INFINITY")
    | pyparsing.Keyword("NOT-A-NUMBER")
)

# ITU-T X.680 Section 22

NamedBitList = pyparsing.Forward()
NamedBit = pyparsing.Forward()
IdentifierList = pyparsing.Forward()

# 22.1
BitStringType <<= pyparsing.Group(
    pyparsing.Keyword("BIT STRING")
    | (pyparsing.Keyword("BIT STRING") + lexical_items.LBRACE + NamedBitList + lexical_items.RBRACE)
)

NamedBitList <<= pyparsing.Group(
    NamedBit
    | NamedBitList + lexical_items.COMMA + NamedBit
)

NamedBit <<= pyparsing.Group(
    (lexical_items.identifier + lexical_items.LPAR + lexical_items.number + lexical_items.RPAR)
    | (lexical_items.identifier + lexical_items.LPAR + values_types.DefinedValue + lexical_items.RPAR)
)

# 22.9
BitStringValue <<= pyparsing.Group(
    lexical_items.bstring
    | lexical_items.hstring
    | (lexical_items.LBRACE + IdentifierList + lexical_items.RBRACE)
    | (lexical_items.LBRACE + lexical_items.RBRACE)
    | (pyparsing.Keyword("CONTAINING") + values_types.Value)
)

IdentifierList <<= pyparsing.Group(
    lexical_items.identifier
    | (IdentifierList + lexical_items.COMMA + lexical_items.identifier)
)

# ITU-T X.680 Section 23

# 23.1
OctetStringType <<= pyparsing.Keyword("OCTET STRING")

# 23.3
OctetStringValue <<= pyparsing.Group(
    lexical_items.bstring
    | lexical_items.hstring
    | (pyparsing.Keyword("CONTAINING") + values_types.Value)
)

# ITU-T X.680 Section 24

# 24.1
NullType <<= pyparsing.Keyword("NULL")

# 23.3
NullValue <<= pyparsing.Keyword("NULL")

# ITU-T X.680 Section 31

# 31.1.5
PrefixedType <<= pyparsing.Group(
    TaggedType
    | EncodingPrefixedType
)

# 31.1.6
PrefixedValue <<= values_types.Value

# 31.2.1
TaggedType <<= pyparsing.Group(
    (Tag + values_types.Type)
    | (Tag + pyparsing.Keyword("IMPLICIT") + values_types.Type)
    | (Tag + pyparsing.Keyword("EXPLICIT") + values_types.Type)
)

Tag <<= pyparsing.Group(
    lexical_items.LBRACK + EncodingReference + Class + ClassNumber + lexical_items.RBRACK
)

EncodingReference <<= pyparsing.Group(
    (lexical_items.encodingreference + lexical_items.COLON)
    | lexical_items.empty
)

ClassNumber <<= pyparsing.Group(
    lexical_items.number
    | values_types.DefinedValue
)

Class <<= pyparsing.Group(
    pyparsing.Keyword("UNIVERSAL")
    | pyparsing.Keyword("APPLICATION")
    | pyparsing.Keyword("PRIVATE")
    | lexical_items.empty
)

# 31.3.1
EncodingPrefixedType <<= pyparsing.Group(
    EncodingPrefix + values_types.Type
)

EncodingInstruction = pyparsing.Regex(r"[^\[\]]]+")

EncodingPrefix <<= pyparsing.Group(
    lexical_items.LBRACK + EncodingReference + EncodingInstruction + lexical_items.RBRACK
)

# ITU-T X.680 Section 36

# 36.1
EmbeddedPDVType <<= pyparsing.Keyword("EMBEDDED PDV")

# 36.8
EmbeddedPDVValue <<= constructed_types.SequenceValue

# ITU-T X.660 Section 70

# 37.1
ExternalType <<= pyparsing.Keyword("EXTERNAL")

# 37.7
ExternalValue <<= constructed_types.SequenceValue

# ITU-T X.680 Section 38

# 38.1.1
TimeType <<= pyparsing.Keyword("TIME")

# 38.3.1
TimeValue <<= lexical_items.tstring

# 38.4.1
DateType <<= pyparsing.Keyword("DATE")

# 38.4.2
TimeOfDayType <<= pyparsing.Keyword("TIME-OF-DAY")

# 38.4.3
DateTimeType <<= pyparsing.Keyword("DATE-TIME")

# 38.4.4
DurationType <<= pyparsing.Keyword("DURATION")

# ITU-T X.680 Section 40

RestrictedCharacterStringType = pyparsing.Forward()
UnrestrictedCharacterStringType = pyparsing.Forward()

# 40.1
CharacterStringType <<= pyparsing.Group(
    RestrictedCharacterStringType("restricted_character_string_type")
    | UnrestrictedCharacterStringType("unrestricted_character_string_type")
)

# ITU-T X.680 Section 41

CharacterStringList = pyparsing.Forward()
Quadruple = pyparsing.Forward()
Tuple = pyparsing.Forward()
CharSyms = pyparsing.Forward()
CharsDefn = pyparsing.Forward()
Group = pyparsing.Forward()
Plane = pyparsing.Forward()
Row = pyparsing.Forward()
Cell = pyparsing.Forward()
TableColumn = pyparsing.Forward()
TableRow = pyparsing.Forward()

RestrictedCharacterStringType <<= pyparsing.Group(
    pyparsing.Keyword("BMPString")
    | pyparsing.Keyword("GeneralString")
    | pyparsing.Keyword("GraphicString")
    | pyparsing.Keyword("IA5String")
    | pyparsing.Keyword("ISO646String")
    | pyparsing.Keyword("NumericString")
    | pyparsing.Keyword("PrintableString")
    | pyparsing.Keyword("TeletexString")
    | pyparsing.Keyword("T61String")
    | pyparsing.Keyword("UniversalString")
    | pyparsing.Keyword("UTF8String")
    | pyparsing.Keyword("VideotexString")
    | pyparsing.Keyword("VisibleString")
)

# 41.8
CharacterStringValue <<= pyparsing.Group(
    Quadruple("quadruple")
    | Tuple("tuple")
    | CharacterStringList("character_string_list")
    | lexical_items.cstring("cstring")
)

CharacterStringList <<= pyparsing.Group(
    lexical_items.LBRACE + CharSyms + lexical_items.RBRACE
)

CharSyms <<= pyparsing.Group(pyparsing.DelimitedList(
    CharsDefn,
    delim=lexical_items.COMMA,
    min=1
))

CharsDefn <<= pyparsing.Group(
    Quadruple("quadruple")
    | Tuple("tuple")
    | lexical_items.cstring("cstring")
    | values_types.DefinedValue("defined_value")
)

Quadruple <<= pyparsing.Group(
    lexical_items.LBRACE + Group + lexical_items.COMMA + Plane + lexical_items.COMMA + Row + lexical_items.COMMA + Cell + lexical_items.RBRACE
)

Group <<= lexical_items.number
Plane <<= lexical_items.number
Row <<= lexical_items.number
Cell <<= lexical_items.number

Tuple <<= pyparsing.Group(
    lexical_items.LBRACE + TableColumn + lexical_items.COMMA + TableRow + lexical_items.RBRACE
)

TableColumn <<= lexical_items.number
TableRow <<= lexical_items.number

# ITU-T X.680 Section 44

# 44.1
UnrestrictedCharacterStringType <<= pyparsing.Keyword("CHARACTER STRING")

# ITU-T X.680 Section 45

# 45.1
UsefulType <<= pyparsing.Group(
    # 46.1
    pyparsing.Keyword("GeneralizedTime")
    # 47.1
    | pyparsing.Keyword("UTCTime")
    # 48.1
    | pyparsing.Keyword("ObjectDescriptor")
)