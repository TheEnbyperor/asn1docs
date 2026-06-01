from . import lexical_items
from . import values_types
from . import built_in_types
from . import constructed_types
from . import object_identifier
from . import constraints
from . import parametisation
from . import javadoc
from . import module

ASN1_GRAMMAR = module.ModuleDefinition.ignore(lexical_items.comment)