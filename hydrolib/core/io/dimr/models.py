from abc import ABC, abstractclassmethod
from datetime import datetime
from pathlib import Path
from typing import List, Literal, Optional, Type

from pydantic import Field, validator

from hydrolib.core import __version__
from hydrolib.core.basemodel import BaseModel, FileModel
from hydrolib.core.utils import to_list


class KeyValuePair(BaseModel):
    key: str
    value: str


class Component(BaseModel, ABC):
    """
    Attributes:
        library:
        name:
        workingDir:
        inputFile:
        process:
        setting:
        parameter:
        mpiCommunicator:
    """

    library: str
    name: str
    workingDir: Path
    inputFile: Path
    process: Optional[int] = 0
    setting: Optional[List[KeyValuePair]]
    parameter: Optional[List[KeyValuePair]]
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


class FMComponent(Component):
    library: Literal["dflowfm"]

    @classmethod
    def get_model(cls):
        from hydrolib.core.models import FMModel  # prevent circular import

        return FMModel


class RRComponent(Component):
    library: Literal["rr_dll"]

    @classmethod
    def get_model(cls):
        raise NotImplementedError("Model not implemented yet.")


class Documentation(BaseModel):
    """
    Attributes:
        fileVersion:
        createdBy:
        creationDate:
    """

    fileVersion: str = "1.3"
    createdBy: str = f"hydrolib-core {__version__}"
    creationDate: datetime = Field(default_factory=datetime.utcnow)


class GlobalSettings(BaseModel):
    """
    Attributes:
        logger_ncFormat:
    """

    logger_ncFormat: int


class ComponentOrCouplerRef(BaseModel):
    """
    Attributes:
        name:
    """

    name: str


class CoupledItem(BaseModel):
    """
    Attributes:
        sourceName:
        targetName:
    """

    sourceName: str
    targetName: str


class Logger(BaseModel):
    """
    Attributes:
        workingDir:
        outputFile:
    """

    workingDir: Path
    outputFile: Path


class Coupler(BaseModel):
    """
    Attributes:
        name:
        sourceComponent:
        targetComponent:
        item:
        logger:
    """

    name: str
    sourceComponent: str
    targetComponent: str
    item: List[CoupledItem]
    logger: Optional[Logger]

    @validator("item", pre=True)
    def validate_item(cls, v):
        return to_list(v)


class StartGroup(BaseModel):
    """
    Attributes:
        time:
        start:
        coupler:
    """

    time: str
    start: List[ComponentOrCouplerRef]
    coupler: List[ComponentOrCouplerRef]

    @validator("start", "coupler", pre=True)
    def validate_start(cls, v):
        return to_list(v)


class Parallel(BaseModel):
    """
    Attributes:
        startGroup
        start:
    """

    startGroup: StartGroup
    start: ComponentOrCouplerRef


class Control(BaseModel):
    """
    Attributes:
        parallel:
        start:
    """

    parallel: Optional[List[Parallel]]
    start: Optional[List[ComponentOrCouplerRef]]

    @validator("parallel", "start", pre=True)
    def validate_parallel(cls, v):
        return to_list(v)
