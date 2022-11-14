import logging
from abc import ABC
from enum import Enum
from typing import Any, Callable, List, Literal, Optional, Set, Type, Union

from pydantic import Extra, Field, root_validator
from pydantic.class_validators import validator
from pydantic.fields import ModelField

from hydrolib.core import __version__ as version
from hydrolib.core.basemodel import BaseModel, ParsableFileModel

from ..ini.io_models import CommentBlock, Document, Property, Section
from .parser import Parser
from .serializer import (
    DataBlockINIBasedSerializerConfig,
    INISerializerConfig,
    write_ini,
)
from .util import make_list_validator

logger = logging.getLogger(__name__)


class INIBasedModel(BaseModel, ABC):
    """INIBasedModel defines the base model for blocks/chapters
    inside an INIModel (*.ini file).

    INIBasedModel instances can be created from Section instances
    obtained through parsing ini documents. It further supports
    adding arbitrary fields to it, which will be written to file.
    Lastly, no arbitrary types are allowed for the defined fields.

    Attributes:
        comments (Optional[Comments]):
            Optional Comments if defined by the user, containing
            descriptions for all data fields.
    """

    _header: str

    class Config:
        extra = Extra.ignore
        arbitrary_types_allowed = False

    @classmethod
    def _supports_comments(cls):
        return True

    @classmethod
    def _duplicate_keys_as_list(cls):
        return False

    @classmethod
    def get_list_delimiter(cls) -> str:
        """List delimiter string that will be used for serializing
        list field values for any IniBasedModel, **if** that field has
        no custom list delimiter.

        This function should be overridden by any subclass for a particular
        filetype that needs a specific/different list separator.
        """
        return " "

    @classmethod
    def get_list_field_delimiter(cls, field_key: str) -> str:
        """List delimiter string that will be used for serializing
        the given field's value.
        The returned delimiter is either the field's custom list delimiter
        if that was specified using Field(.., delimiter=".."), or the
        default list delimiter for the model class that this field belongs
        to.

        Args:
            field_key (str): the original field key (not its alias).
        """
        delimiter = None
        if (field := cls.__fields__.get(field_key)) and isinstance(field, ModelField):
            delimiter = field.field_info.extra.get("delimiter")
        if not delimiter:
            delimiter = cls.get_list_delimiter()

        return delimiter

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

    @classmethod
    def _convert_value(cls, key: str, v: Any, config: INISerializerConfig) -> str:
        if isinstance(v, bool):
            return str(int(v))
        elif isinstance(v, list):

            def to_string(x) -> str:
                return f"{x:{config.float_format}}" if isinstance(x, float) else str(x)

            return cls.get_list_field_delimiter(key).join([to_string(x) for x in v])
        elif isinstance(v, Enum):
            return v.value
        elif isinstance(v, float):
            return f"{v:{config.float_format}}"
        elif v is None:
            return ""
        else:
            return str(v)

    def _to_section(self, config: INISerializerConfig) -> Section:
        props = []
        for key, value in self:
            if key in self._exclude_fields():
                continue

            field_key = key
            if key in self.__fields__:
                key = self.__fields__[key].alias

            prop = Property(
                key=key,
                value=self.__class__._convert_value(field_key, value, config),
                comment=getattr(self.comments, key.lower(), None),
            )
            props.append(prop)
        return Section(header=self._header, content=props)


class DataBlockINIBasedModel(INIBasedModel):
    """DataBlockINIBasedModel defines the base model for ini models with datablocks.

    Attributes:
        datablock (List[List[Union[float, str]]]): (class attribute) the actual data
            columns.
    """

    datablock: List[List[Union[float, str]]] = []

    _make_lists = make_list_validator("datablock")

    def _to_section(self, config: DataBlockINIBasedSerializerConfig) -> Section:
        section = super()._to_section(config)
        section.datablock = self._to_datablock(config)
        return section

    def _to_datablock(self, config: DataBlockINIBasedSerializerConfig) -> List[List]:
        converted_datablock = []

        for row in self.datablock:
            converted_row = (
                DataBlockINIBasedModel.convert_value(value, config) for value in row
            )
            converted_datablock.append(list(converted_row))

        return converted_datablock

    @classmethod
    def convert_value(
        cls, value: Union[float, str], config: DataBlockINIBasedSerializerConfig
    ) -> str:
        if isinstance(value, float):
            return f"{value:{config.float_format_datablock}}"

        return value


class INIGeneral(INIBasedModel):
    _header: Literal["General"] = "General"
    fileversion: str = Field("3.00", alias="fileVersion")
    filetype: str = Field(alias="fileType")

    @classmethod
    def _supports_comments(cls):
        return True


class INIModel(ParsableFileModel):
    """INI Model representation of a *.ini file.

    Typically subclasses will implement the various sorts of ini files,
    specifically for their fileType/contents.
    Child elements of this class associated with chapters/blocks in the
    ini file will be (sub)class of INIBasedModel.
    """

    serializer_config: INISerializerConfig = INISerializerConfig()

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
        for key, value in self:
            if key in self._exclude_fields() or value is None:
                continue
            if isinstance(value, list):
                for v in value:
                    sections.append(v._to_section(self.serializer_config))
            else:
                sections.append(value._to_section(self.serializer_config))
        return Document(header_comment=[header], sections=sections)

    def _serialize(self, _: dict) -> None:
        write_ini(
            self._resolved_filepath, self._to_document(), config=self.serializer_config
        )
