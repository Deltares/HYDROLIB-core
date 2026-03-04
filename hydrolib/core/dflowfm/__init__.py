"""D-Flow FM model file wrappers.

This package re-exports the most commonly used model classes for
convenient access.  Less common classes should be imported directly
from their sub-modules (e.g. ``from hydrolib.core.dflowfm.bc import T3D``).
"""

# Main model entry points
from .mdu import FMModel
from .research import ResearchFMModel

# File-level models (each represents a complete file)
from .bc import ForcingModel
from .crosssection import CrossDefModel, CrossLocModel
from .ext import ExtModel
from .extold import ExtOldModel
from .friction import FrictionModel
from .inifield import IniFieldModel
from .net import NetworkModel
from .obs import ObservationPointModel
from .obscrosssection import ObservationCrossSectionModel
from .onedfield import OneDFieldModel
from .polyfile import PolyFile
from .storagenode import StorageNodeModel
from .structure import StructureModel
from .tim import TimModel
from .xyn import XYNModel
from .xyz import XYZModel
from .gui import BranchModel
from .cmp import CMPModel

# Commonly used non-model classes
from .ext import Boundary, Lateral, Meteo, SourceSink
from .extold import ExtOldForcing
from .structure import Weir, Pump, Culvert, Orifice, Bridge, Dambreak, GeneralStructure
from .structure import FlowDirection, Orientation
from .bc import TimeSeries, Harmonic, Astronomic, Constant, QuantityUnitPair
from .net import Network, Mesh1d, Mesh2d, Branch, Link1d2d
from .inifield import InitialField, ParameterField
from .polyfile import PolyObject
from .common import LocationType, Operand

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
