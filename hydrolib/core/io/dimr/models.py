from abc import ABC, abstractclassmethod
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Literal, Optional, Type, Union

from pydantic import Field, validator

from hydrolib.core import __version__
from hydrolib.core.basemodel import BaseModel, FileModel
from hydrolib.core.io.dimr.parser import DIMRParser
from hydrolib.core.io.dimr.serializer import DIMRSerializer
from hydrolib.core.io.fnm.models import RainfallRunoffModel
from hydrolib.core.io.mdu.models import FMModel
from hydrolib.core.utils import to_list


class KeyValuePair(BaseModel):
    """Key value pair to specify settings and parameters.

    Attributes:
        key: The key.
        value: The value.
    """

    key: str
    value: str


class Component(BaseModel, ABC):
    """
    Specification of a BMI-compliant model component instance that will be executed by DIMR.

    Attributes:
        library: The library name of the compoment.
        name: The component name.
        workingDir: The working directory.
        inputFile: The name of the input file.
        process: Number of subprocesses in the component.
        setting: A list of variables that are provided to the BMI model before initialization.
        parameter: A list of variables that are provided to the BMI model after initialization.
        mpiCommunicator: The MPI communicator value.
        model: The model represented by this component.
    """

    library: str
    name: str
    workingDir: Path
    inputFile: Path
    process: Optional[int]
    setting: Optional[List[KeyValuePair]] = []
    parameter: Optional[List[KeyValuePair]] = []
    mpiCommunicator: Optional[str]

    model: Optional[FileModel]

    @property
    def filepath(self):
        return self.workingDir / self.inputFile

    @abstractclassmethod
    def get_model(cls) -> Type[FileModel]:
        raise NotImplementedError("Model not implemented yet.")

    @validator("setting", "parameter", pre=True)
    def validate_setting(cls, v):
        return to_list(v)

    def is_intermediate_link(self) -> bool:
        return True

    def _get_identifier(self, data: dict) -> str:
        return data["name"] if "name" in data else None


class FMComponent(Component):
    library: Literal["dflowfm"] = "dflowfm"

    @classmethod
    def get_model(cls):
        return FMModel


class RRComponent(Component):
    library: Literal["rr_dll"] = "rr_dll"

    @classmethod
    def get_model(cls):
        return RainfallRunoffModel


class Documentation(BaseModel):
    """
    Information on the present DIMR configuration file.

    Attributes:
        fileVersion: The DIMR file version.
        createdBy: Creators of the DIMR file.
        creationDate: The creation date of the DIMR file.
    """

    fileVersion: str = "1.3"
    createdBy: str = f"hydrolib-core {__version__}"
    creationDate: datetime = Field(default_factory=datetime.utcnow)


class GlobalSettings(BaseModel):
    """
    Global settings for the DIMR configuration.

    Attributes:
        logger_ncFormat: NetCDF format type for logging.
    """

    logger_ncFormat: int


class ComponentOrCouplerRef(BaseModel):
    """
    Reference to a BMI-compliant model component instance.

    Attributes:
        name: Name of the reference to a BMI-compliant model component instance.
    """

    name: str

    def _get_identifier(self, data: dict) -> str:
        return data["name"] if "name" in data else None


class CoupledItem(BaseModel):
    """
    Specification of an item that has to be exchanged.

    Attributes:
        sourceName: Name of the item at the source component.
        targetName: Name of the item at the target component.
    """

    sourceName: str
    targetName: str

    def is_intermediate_link(self) -> bool:
        # TODO set to True once we replace Paths with FileModels
        return False


class Logger(BaseModel):
    """
    Used to log values to the specified file in workingdir for each timestep

    Attributes:
        workingDir: Directory where the log file is written.
        outputFile: Name of the log file.
    """

    workingDir: Path
    outputFile: Path


class Coupler(BaseModel):
    """
    Specification of the coupling actions to be performed between two BMI-compliant model components.

    Attributes:
        name: The name of the coupler.
        sourceComponent: The component that provides the data to has to be exchanged.
        targetComponent: The component that consumes the data to has to be exchanged.
        item: A list of items that have to be exchanged.
        logger: Logger for logging the values that get exchanged.
    """

    name: str
    sourceComponent: str
    targetComponent: str
    item: List[CoupledItem] = []
    logger: Optional[Logger]

    @validator("item", pre=True)
    def validate_item(cls, v):
        return to_list(v)

    def is_intermediate_link(self) -> bool:
        # TODO set to True once we replace Paths with FileModels
        return False

    def _get_identifier(self, data: dict) -> str:
        return data["name"] if "name" in data else None


class StartGroup(BaseModel):
    """
    Specification of model components and couplers to be executed with a certain frequency.

    Attributes:
        time: Time frame specification for the present group: start time, stop time and frequency.
              Expressed in terms of the time frame of the main component.
        start: Ordered list of components to be executed.
        coupler: Oredered list of couplers to be executed.
    """

    time: str
    start: List[ComponentOrCouplerRef] = []
    coupler: List[ComponentOrCouplerRef] = []

    @validator("start", "coupler", pre=True)
    def validate_start(cls, v):
        return to_list(v)


class Parallel(BaseModel):
    """
    Specification of a parallel control flow: one main component and a group of related components and couplers.
    Step wise execution order according to order in parallel control flow.

    Attributes:
        startGroup: Group of components and couplers to be executed.
        start: Main component to be executed step wise (provides start time, end time and time step).
    """

    startGroup: StartGroup
    start: ComponentOrCouplerRef


class Control(BaseModel):
    """
    Control flow specification for the DIMR-execution.

    Attributes:
        parallel: Specification of a control flow that has to be executed in parallel.
        start: Reference to the component instance to be started.
    """

    parallel: Optional[List[Parallel]] = []
    start: Optional[List[ComponentOrCouplerRef]] = []

    @validator("parallel", "start", pre=True)
    def validate_parallel(cls, v):
        return to_list(v)

    def is_intermediate_link(self) -> bool:
        # TODO set to True once we replace Paths with FileModels
        return False


class DIMR(FileModel):
    """DIMR model representation."""

    documentation: Documentation = Documentation()
    control: Control = Control()
    component: List[Union[RRComponent, FMComponent, Component]] = []
    coupler: Optional[List[Coupler]] = []
    waitFile: Optional[str]
    global_settings: Optional[GlobalSettings]

    @validator("component", "coupler", pre=True)
    def validate_component(cls, v):
        return to_list(v)

    def dict(self, *args, **kwargs):
        """Converts this object recursively to a dictionary.

        Returns:
            dict: The created dictionary for this object.
        """
        return self._to_serializable_dict(self)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # After initilization, try to load all component models
        if self.filepath:
            for comp in self.component:
                fn = self.filepath.parent / comp.filepath
                try:
                    comp.model = comp.get_model()(filepath=fn)
                except NotImplementedError:
                    continue

    @classmethod
    def _ext(cls) -> str:
        return ".xml"

    @classmethod
    def _filename(cls) -> str:
        return "dimr_config"

    @classmethod
    def _get_serializer(cls) -> Callable:
        return DIMRSerializer.serialize

    @classmethod
    def _get_parser(cls) -> Callable:
        return DIMRParser.parse

    def _to_serializable_dict(self, obj) -> dict:
        if not hasattr(obj, "__dict__"):
            return obj

        result = {}

        for key, val in obj.__dict__.items():
            if (
                key.startswith("_")
                or key == "filepath"
                or isinstance(val, FileModel)
                or val is None
            ):
                continue

            element = []
            if isinstance(val, list):
                for item in val:
                    element.append(self._to_serializable_dict(item))
            else:
                element = self._to_serializable_dict(val)
            result[key] = element

        return result
