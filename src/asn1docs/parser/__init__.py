from . import lexical_items
from . import module

ASN1_GRAMMAR = module.ModuleDefinition.ignore(lexical_items.comment)