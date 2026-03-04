"""Base classes for HYDROLIB-core file models.

Import from sub-modules directly::

    from hydrolib.core.base.models import FileModel, ParsableFileModel
    from hydrolib.core.base.file_manager import FileLoadContext
"""

from hydrolib.core.base.file_manager import (
    FileLoadContext,
    PathOrStr,
    ResolveRelativeMode,
)
from hydrolib.core.base.models import (
    BaseModel,
    DiskOnlyFileModel,
    FileModel,
    ModelSaveSettings,
    ModelTreeTraverser,
    ParsableFileModel,
    SerializerConfig,
)

__all__ = [
    # models
    "BaseModel",
    "FileModel",
    "ParsableFileModel",
    "DiskOnlyFileModel",
    "SerializerConfig",
    "ModelSaveSettings",
    "ModelTreeTraverser",
    # file_manager
    "FileLoadContext",
    "ResolveRelativeMode",
    "PathOrStr",
]
