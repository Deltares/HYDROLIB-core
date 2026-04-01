"""Shared INI-based file infrastructure for D-Flow FM models.

Import from sub-modules directly::

    from hydrolib.core.dflowfm.ini.models import INIBasedModel, INIModel
    from hydrolib.core.dflowfm.ini.parser import Parser, ParserConfig
"""

from hydrolib.core.dflowfm.ini.io_models import Document, Property, Section
from hydrolib.core.dflowfm.ini.models import (
    DataBlockINIBasedModel,
    INIBasedModel,
    INIGeneral,
    INIModel,
)
from hydrolib.core.dflowfm.ini.parser import Parser, ParserConfig
from hydrolib.core.dflowfm.ini.serializer import (
    DataBlockINIBasedSerializerConfig,
    INISerializerConfig,
)

__all__ = [
    # models
    "INIBasedModel",
    "DataBlockINIBasedModel",
    "INIGeneral",
    "INIModel",
    # io_models
    "Section",
    "Property",
    "Document",
    # serializer
    "INISerializerConfig",
    "DataBlockINIBasedSerializerConfig",
    # parser
    "Parser",
    "ParserConfig",
]
