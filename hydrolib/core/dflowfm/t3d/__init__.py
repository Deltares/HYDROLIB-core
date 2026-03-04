"""T3D (3D time series) file model.

Import from sub-modules directly::

    from hydrolib.core.dflowfm.t3d.models import T3DModel, T3DTimeRecord
"""

from .models import LayerType, T3DModel, T3DTimeRecord

__all__ = [
    "T3DModel",
    "T3DTimeRecord",
    "LayerType",
]
