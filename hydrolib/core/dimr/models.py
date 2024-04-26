from abc import ABC, abstractclassmethod
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Literal, Optional, Type, Union

from pydantic.v1 import Field, validator

from hydrolib.core import __version__
from hydrolib.core.basemodel import (
    BaseModel,
    FileModel,
    ModelSaveSettings,
    ParsableFileModel,
    SerializerConfig,
)
from hydrolib.core.dflowfm.mdu.models import FMModel
from hydrolib.core.dimr.parser import DIMRParser
from hydrolib.core.dimr.serializer import DIMRSerializer
from hydrolib.core.rr.models import RainfallRunoffModel
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

    @validator("setting", "parameter", pre=True, allow_reuse=True)
    def validate_setting(cls, v):
        return to_list(v)

    def is_intermediate_link(self) -> bool:
        return True

    def _get_identifier(self, data: dict) -> Optional[str]:
        return data.get("name")

    def dict(self, *args, **kwargs):
        # Exclude the FileModel from any DIMR serialization.
        kwargs["exclude"] = {"model"}
        return super().dict(*args, **kwargs)


class FMComponent(Component):
    """Component to include the D-Flow FM program in a DIMR control flow."""

    library: Literal["dflowfm"] = "dflowfm"

    @validator("process", pre=True)
    def validate_process(cls, value, values: dict) -> Union[None, int]:
        if value is None:
            return None

        if isinstance(value, str):
            split_values = value.split()
            if cls.validate_process_as_str(split_values):
                return len(split_values)

        if isinstance(value, int):
            if value <= 0:
                raise ValueError(
                    f"In component '{values.get('name')}', the keyword process can not be 0 or negative, please specify value of 1 or greater."
                )
            return value

        raise ValueError(
            f"In component '{values.get('name')}', the keyword process '{value}', is incorrect."
        )

    @classmethod
    def validate_process_as_str(cls, values: str) -> bool:
        if len(values) < 1:
            return False

        if values[0] != "0":
            return False

        for value in values:
            if not value.isdigit():
                return False

        return True

    @classmethod
    def get_model(cls):
        return FMModel


class RRComponent(Component):
    """Component to include the RainfallRunoff program in a DIMR control flow."""

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

    def _get_identifier(self, data: dict) -> Optional[str]:
        return data.get("name")


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

    def _get_identifier(self, data: dict) -> Optional[str]:
        return data.get("name")


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


class ControlModel(BaseModel):
    """
    Overrides to make sure that the control elements in the DIMR
    are parsed and serialized correctly.
    """

    _type: str

    def dict(self, *args, **kwargs):
        """Add control element prefixes for serialized data."""
        return {
            str(self._type): super().dict(*args, **kwargs),
        }

    @classmethod
    def validate(cls, v):
        """Remove control element prefixes from parsed data."""

        # should be replaced by discriminated unions once merged
        # https://github.com/samuelcolvin/pydantic/pull/2336
        if isinstance(v, dict) and len(v.keys()) == 1:
            key = list(v.keys())[0]
            v = v[key]
        return super().validate(v)


class Parallel(ControlModel):
    """
    Specification of a parallel control flow: one main component and a group of related components and couplers.
    Step wise execution order according to order in parallel control flow.

    Attributes:
        startGroup: Group of components and couplers to be executed.
        start: Main component to be executed step wise (provides start time, end time and time step).
    """

    _type: Literal["parallel"] = "parallel"
    startGroup: StartGroup
    start: ComponentOrCouplerRef


class Start(ControlModel):
    """
    Specification of a serial control flow: one main component.

    Attributes:
        name: Name of the reference to a BMI-compliant model component instance
    """

    _type: Literal["start"] = "start"
    name: str


class DIMR(ParsableFileModel):
    """DIMR model representation.

    Attributes:
        documentation (Documentation): File metadata.
        control (List[Union[Start, Parallel]]): The `<control>` element with a list
            of [Start][hydrolib.core.dimr.models.Start]
            and [Parallel][hydrolib.core.dimr.models.Parallel] sub-elements,
            which defines the (sequence of) program(s) to be run.
            May be empty while constructing, but must be non-empty when saving!
            Also, all referenced components must be present in `component` when
            saving. Similarly, all referenced couplers must be present in `coupler`.
        component (List[Union[RRComponent, FMComponent, Component]]): List of
            `<component>` elements that defines which programs can be used inside
            the `<control>` subelements. Must be non-empty when saving!
        coupler (Optional[List[Coupler]]): optional list of `<coupler>` elements
            that defines which couplers can be used inside the `<parallel>`
            elements under `<control>`.
        waitFile (Optional[str]): Optional waitfile name for debugging.
        global_settings (Optional[GlobalSettings]): Optional global DIMR settings.
    """

    documentation: Documentation = Documentation()
    control: List[Union[Start, Parallel]] = Field([])
    component: List[Union[RRComponent, FMComponent, Component]] = []
    coupler: Optional[List[Coupler]] = []
    waitFile: Optional[str]
    global_settings: Optional[GlobalSettings]

    @validator("component", "coupler", "control", pre=True)
    def validate_component(cls, v):
        return to_list(v)

    def dict(self, *args, **kwargs):
        kwargs["exclude_none"] = True
        return super().dict(*args, **kwargs)

    def _post_init_load(self) -> None:
        """
        Load the component models of this DIMR model.
        """
        super()._post_init_load()

        for comp in self.component:
            try:
                comp.model = comp.get_model()(filepath=comp.filepath)
            except NotImplementedError:
                pass

    def _save(self, save_settings: ModelSaveSettings) -> None:
        dimr_as_dict = self.dict()
        dimr_as_dict = self.update_dimr_dictonary_with_adjusted_fmcomponent_values(
            dimr_as_dict
        )
        self._serialize(dimr_as_dict, save_settings)

    def update_dimr_dictonary_with_adjusted_fmcomponent_values(
        self, dimr_as_dict: Dict
    ):
        fmcomponents = [
            item for item in self.component if isinstance(item, FMComponent)
        ]

        list_of_fmcomponents_as_dict = self._get_list_of_updated_fm_components(
            fmcomponents
        )
        dimr_as_dict = self._update_dimr_dictionary(
            dimr_as_dict, list_of_fmcomponents_as_dict
        )
        return dimr_as_dict

    def _update_dimr_dictionary(
        self, dimr_as_dict: Dict, list_of_fm_components_as_dict: List[Dict]
    ) -> Dict:
        if len(list_of_fm_components_as_dict) > 0:
            dimr_as_dict.update({"component": list_of_fm_components_as_dict})

        return dimr_as_dict

    def _get_list_of_updated_fm_components(
        self, fmcomponents: List[FMComponent]
    ) -> List[Dict]:
        list_of_fm_components_as_dict = []
        for fmcomponent in fmcomponents:
            if fmcomponent is None or fmcomponent.process is None:
                continue

            if fmcomponent.process == 1:
                fmcomponent_process_value = "None"
            else:
                fmcomponent_process_value = " ".join(
                    str(i) for i in range(fmcomponent.process)
                )

            fmcomponent_as_dict = self._update_component_dictonary(
                fmcomponent, fmcomponent_process_value
            )
            list_of_fm_components_as_dict.append(fmcomponent_as_dict)

        return list_of_fm_components_as_dict

    def _update_component_dictonary(
        self, fmcomponent: FMComponent, fmcomponent_process_value: str
    ) -> Dict:
        fmcomponent_as_dict = fmcomponent.dict()
        fmcomponent_as_dict.update({"process": fmcomponent_process_value})
        return fmcomponent_as_dict

    @classmethod
    def _ext(cls) -> str:
        return ".xml"

    @classmethod
    def _filename(cls) -> str:
        return "dimr_config"

    @classmethod
    def _get_serializer(
        cls,
    ) -> Callable[[Path, Dict, SerializerConfig, ModelSaveSettings], None]:
        return DIMRSerializer.serialize

    @classmethod
    def _get_parser(cls) -> Callable:
        return DIMRParser.parse
