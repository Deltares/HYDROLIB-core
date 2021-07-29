from abc import ABC
from functools import reduce
from typing import Any, Callable, Dict, List, Literal, Optional, Type

from pydantic import Extra
from pydantic.class_validators import validator

from hydrolib.core.basemodel import BaseModel, FileModel
from hydrolib.core.io.base import DummySerializer

from .parser import Parser
from .parser_models import Section
from .util import make_list_validator


class IniBasedModel(BaseModel, ABC):
    """IniBasedModel defines the base model for ini models

    IniBasedModel instances can be created from Section instances
    obtained through parsing ini documents. It further supports
    adding arbitrary fields to it, which will be written to file.
    Lastly, no arbitrary types are allowed for the defined fields.

    Attributes:
        comments (Optional[Comments]):
            Optional Comments if defined by the user.
    """

    _header: str

    class Config:
        extra = Extra.allow
        allow_population_by_field_name = True
        arbitrary_types_allowed = False

    @classmethod
    def _supports_comments(cls):
        return True

    @classmethod
    def _duplicate_keys_as_list(cls):
        return False

    class Comments(BaseModel, ABC):
        """Comments defines the comments of an IniBasedModel"""

        class Config:
            extra = Extra.allow
            allow_population_by_field_name = True
            arbitrary_types_allowed = False

    comments: Optional[Comments] = None

    @validator("comments", always=True, allow_reuse=True)
    def comments_matches_has_comments(cls, v):
        # if cls._supports_comments() and v is None:
        # raise ValueError(f"{cls} should have comments.")
        if not cls._supports_comments() and v is not None:
            raise ValueError(f"{cls} should not have comments.")

        return v

    @classmethod
    def validate(cls: Type["IniBasedModel"], value: Any) -> "IniBasedModel":
        if isinstance(value, Section):
            value = value.flatten(
                cls._duplicate_keys_as_list(), cls._supports_comments()
            )

        return super().validate(value)


class DataBlockIniBasedModel(IniBasedModel):
    """DataBlockIniBasedModel defines the base model for ini models with datablocks."""

    @classmethod
    def _convert_section_to_dict(cls, value: Section) -> Dict:
        return value.dict(
            exclude={
                "start_line",
                "end_line",
                "content",
            }
        )


class INIGeneral(IniBasedModel):
    fileVersion: str = "3.00"
    fileType: str


class CrossdefGeneral(INIGeneral):
    fileVersion: str = "3.00"
    fileType: Literal["crossDef"] = "crossDef"


class CrosslockGeneral(INIGeneral):
    fileVersion: str = "3.00"
    fileType: Literal["crossLoc"] = "crossLoc"


class INIModel(FileModel):
    """FM Model representation."""

    general: INIGeneral

    @classmethod
    def _ext(cls) -> str:
        return ".ini"

    @classmethod
    def _filename(cls) -> str:
        return "fm"

    @classmethod
    def _get_serializer(cls) -> Callable:
        return DummySerializer.serialize

    @classmethod
    def _get_parser(cls) -> Callable:
        return Parser.parse


class Definition(IniBasedModel):
    id: str
    type: str

    @classmethod
    def _duplicate_keys_as_list(cls):
        return True


class CrossDefModel(INIModel):
    general: CrossdefGeneral
    definition: List[Definition] = []

    @validator("definition")
    def split(cls, v):
        if isinstance(v, dict):
            v = [v]
        return v

    @classmethod
    def _filename(cls) -> str:
        return "crsdef"


class CrossSection(IniBasedModel):
    id: str
    branchid: str


class CrossLocModel(INIModel):
    general: CrosslockGeneral
    crosssection: List[CrossSection] = []

    @classmethod
    def _filename(cls) -> str:
        return "crsloc"


class Global(IniBasedModel):
    frictionId: str
    frictionType: str
    frictionValue: float


class FrictionModel(INIModel):
    general: INIGeneral
    Global: List[Global]

    _split_to_list = make_list_validator(
        "Global",
    )
