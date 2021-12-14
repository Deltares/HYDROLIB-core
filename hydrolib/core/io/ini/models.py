import logging
from abc import ABC
from typing import Any, Callable, List, Literal, Optional, Set, Type, Union

from pydantic import Extra, Field, root_validator
from pydantic.class_validators import validator

from hydrolib.core import __version__ as version
from hydrolib.core.basemodel import BaseModel, FileModel

from .io_models import CommentBlock, Document, Property, Section
from .parser import Parser
from .serializer import SerializerConfig, write_ini
from .util import make_list_validator

logger = logging.getLogger(__name__)


class INIBasedModel(BaseModel, ABC):
    """INIBasedModel defines the base model for ini models

    INIBasedModel instances can be created from Section instances
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
        arbitrary_types_allowed = False

    @classmethod
    def _supports_comments(cls):
        return True

    @classmethod
    def _duplicate_keys_as_list(cls):
        return False

    @classmethod
    def list_delimiter(cls) -> str:
        return ";"

    class Comments(BaseModel, ABC):
        """Comments defines the comments of an INIBasedModel"""

        class Config:
            extra = Extra.allow
            arbitrary_types_allowed = False

    comments: Optional[Comments] = Comments()

    @root_validator(pre=True)
    def _skip_nones_and_set_header(cls, values):
        """Drop None fields for known fields."""
        dropkeys = []
        for k, v in values.items():
            if v is None and k in cls.__fields__.keys():
                dropkeys.append(k)

        logger.info(f"Dropped unset keys: {dropkeys}")
        for k in dropkeys:
            values.pop(k)

        if "_header" in values:
            values["_header"] = cls._header

        return values

    @validator("comments", always=True, allow_reuse=True)
    def comments_matches_has_comments(cls, v):
        if not cls._supports_comments() and v is not None:
            logging.warning(f"Dropped unsupported comments from {cls.__name__} init.")
            v = None
        return v

    @classmethod
    def validate(cls: Type["INIBasedModel"], value: Any) -> "INIBasedModel":
        if isinstance(value, Section):
            value = value.flatten(
                cls._duplicate_keys_as_list(), cls._supports_comments()
            )

        return super().validate(value)

    @classmethod
    def _exclude_fields(cls) -> Set:
        return {"comments", "datablock", "_header"}

    @staticmethod
    def _convert_value(v: Any) -> str:
        if isinstance(v, bool):
            return str(int(v))
        elif isinstance(v, list):
            return ";".join([str(x) for x in v])
        elif v is None:
            return ""
        else:
            return str(v)

    def _to_section(self) -> Section:
        props = []
        for key, value in self:
            if key in self._exclude_fields():
                continue

            if key in self.__fields__:
                key = self.__fields__[key].alias

            prop = Property(
                key=key,
                value=INIBasedModel._convert_value(value),
                comment=getattr(self.comments, key.lower(), None),
            )
            props.append(prop)
        return Section(header=self._header, content=props)


class DataBlockINIBasedModel(INIBasedModel):
    """DataBlockINIBasedModel defines the base model for ini models with datablocks."""

    datablock: List[List[Union[float, str]]] = []

    _make_lists = make_list_validator("datablock")

    def _to_section(self) -> Section:
        section = super()._to_section()
        section.datablock = self.datablock
        return section


class INIGeneral(INIBasedModel):
    _header: Literal["General"] = "General"
    fileversion: str = Field("3.00", alias="fileVersion")
    filetype: str = Field(alias="fileType")

    @classmethod
    def _supports_comments(cls):
        return True


class INIModel(FileModel):
    """INI Model representation."""

    general: INIGeneral

    @classmethod
    def _ext(cls) -> str:
        return ".ini"

    @classmethod
    def _filename(cls) -> str:
        return "fm"

    @classmethod
    def _get_serializer(cls):
        pass  # unused in favor of direct _serialize

    @classmethod
    def _get_parser(cls) -> Callable:
        return Parser.parse_as_dict

    def _to_document(self) -> Document:
        header = CommentBlock(lines=[f"written by HYDROLIB-core {version}"])
        sections = []
        for _, value in self:
            if _ == "filepath" or value is None:
                continue
            if isinstance(value, list):
                for v in value:
                    sections.append(v._to_section())
            else:
                sections.append(value._to_section())
        return Document(header_comment=[header], sections=sections)

    def _serialize(self, _: dict) -> None:
        # We skip the passed dict for a better one.
        config = SerializerConfig(section_indent=0, property_indent=4)
        write_ini(self._resolved_filepath, self._to_document(), config=config)
