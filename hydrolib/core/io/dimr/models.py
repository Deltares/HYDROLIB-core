from abc import ABC, abstractclassmethod
from datetime import datetime
from pathlib import Path
from typing import List, Literal, Optional, Type, Union

from pydantic import Field

from hydrolib.core import __version__
from hydrolib.core.basemodel import BaseModel, FileModel


class Component(BaseModel, ABC):
    library: str
    name: str
    workingDir: Path
    inputFile: Path

    model: Optional[FileModel]

    @property
    def filepath(self):
        return self.workingDir / self.inputFile

    @abstractclassmethod
    def get_model(cls) -> Type[FileModel]:
        raise NotImplementedError("Model not implemented yet.")


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
    fileVersion: str = "1.3"
    createdBy: str = f"hydrolib-core {__version__}"
    creationDate: datetime = Field(default_factory=datetime.utcnow)


class Item(BaseModel):
    sourceName: Path
    targetName: Path


class Logger(BaseModel):
    workingDir: Path
    outputFile: Path


class Coupler(BaseModel):
    name: str
    sourceComponent: str
    targetComponent: str
    item: List[Item]
    logger: Logger


class Start(BaseModel):
    name: str


class ControlCoupler(BaseModel):
    name: str


class StartGroup(BaseModel):
    time: str
    start: Start
    coupler: ControlCoupler


class Parallel(BaseModel):
    startGroup: StartGroup
    start: Start


class Control(BaseModel):
    parallel: Parallel
