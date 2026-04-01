"""D-Flow FM model file wrappers.

This package re-exports the most commonly used model classes for
convenient access.  Less common classes should be imported directly
from their sub-modules (e.g. ``from hydrolib.core.dflowfm.bc import T3D``).
"""

# File-level models (each represents a complete file)
from .bc import (
    Astronomic,
    Constant,
    ForcingModel,
    Harmonic,
    QuantityUnitPair,
    TimeSeries,
)
from .cmp import CMPModel
from .common import LocationType, Operand
from .crosssection import CrossDefModel, CrossLocModel

# Commonly used non-model classes
from .ext import Boundary, ExtModel, Lateral, Meteo, SourceSink
from .extold import ExtOldForcing, ExtOldModel
from .friction import FrictionModel
from .gui import BranchModel
from .inifield import IniFieldModel, InitialField, ParameterField

# Main model entry points
from .mdu import FMModel
from .net import Branch, Link1d2d, Mesh1d, Mesh2d, Network, NetworkModel
from .obs import ObservationPointModel
from .obscrosssection import ObservationCrossSectionModel
from .onedfield import OneDFieldModel
from .polyfile import PolyFile, PolyObject
from .research import ResearchFMModel
from .storagenode import StorageNodeModel
from .structure import (
    Bridge,
    Culvert,
    Dambreak,
    FlowDirection,
    GeneralStructure,
    Orientation,
    Orifice,
    Pump,
    StructureModel,
    Weir,
)
from .tim import TimModel
from .xyn import XYNModel
from .xyz import XYZModel

__all__ = [
    # Main model entry points
    "FMModel",
    "ResearchFMModel",
    # File-level models
    "ForcingModel",
    "CrossDefModel",
    "CrossLocModel",
    "ExtModel",
    "ExtOldModel",
    "FrictionModel",
    "IniFieldModel",
    "NetworkModel",
    "ObservationPointModel",
    "ObservationCrossSectionModel",
    "OneDFieldModel",
    "PolyFile",
    "StorageNodeModel",
    "StructureModel",
    "TimModel",
    "XYNModel",
    "XYZModel",
    "BranchModel",
    "CMPModel",
    # Ext / boundary forcing
    "Boundary",
    "Lateral",
    "Meteo",
    "SourceSink",
    "ExtOldForcing",
    # Structures
    "Weir",
    "Pump",
    "Culvert",
    "Orifice",
    "Bridge",
    "Dambreak",
    "GeneralStructure",
    "FlowDirection",
    "Orientation",
    # Boundary conditions
    "TimeSeries",
    "Harmonic",
    "Astronomic",
    "Constant",
    "QuantityUnitPair",
    # Network / mesh
    "Network",
    "Mesh1d",
    "Mesh2d",
    "Branch",
    "Link1d2d",
    # Initial / parameter fields
    "InitialField",
    "ParameterField",
    # Polyfile
    "PolyObject",
    # Common enums
    "LocationType",
    "Operand",
]
