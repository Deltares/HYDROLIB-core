import logging
from abc import ABC
from enum import Enum
from math import isnan
from typing import Any, Callable, List, Literal, Optional, Set, Type, Union

from pydantic.v1 import Extra, Field, root_validator
from pydantic.v1.class_validators import validator
from pydantic.v1.fields import ModelField

from hydrolib.core import __version__ as version
from hydrolib.core.basemodel import (
    BaseModel,
    FileModel,
    FilePathStyleConverter,
    ModelSaveSettings,
    ParsableFileModel,
)

from ..ini.io_models import CommentBlock, Document, Property, Section
from .parser import Parser
from .serializer import (
    DataBlockINIBasedSerializerConfig,
    INISerializerConfig,
    write_ini,
)
from .util import make_list_validator

logger = logging.getLogger(__name__)

class UnknownKeyNotificationManager():
    """
    Notification manager for unknown keys.
    Detects unknown keys and manages the notification to the user.
    """
    
    def notify_unknown_keywords(self, data : dict[str, Any], section_header : str,  fields : dict[str, Any], excluded_fields : Set, config_extra : Extra):
        """
        Notify the user of unknown keywords.

        Args:
            data (dict[str, Any])   : Input data containing all set properties which are checked on unknown keywords.
            section_header (str)    : Header of the section in which unknown keys might be detected.
            fields (dict[str, Any]) : Known fields of the section.
            excluded_fields (Set)   : Fields which should be excluded from the check for unknown keywords.
            config_extra (Extra)    : Setting which determines if unknown keywords are allowed or dropped.
        """
        unknown_keywords = self._get_all_unknown_keywords(data, fields, excluded_fields)
                
        if len(unknown_keywords) == 0:
            return
        
        self._print_list_of_unknown_keywords(section_header, config_extra, unknown_keywords)
        
    def notify_unknown_keyword(self, name : str, section_header : str,  fields : dict[str, Any], excluded_fields : Set, config_extra : Extra):
        """
        Notify the user of a unknown keyword.

        Args:
            name (str)              : Keyword which is checked if it is an unknown keyword.
            section_header (str)    : Header of the section in which unknown keys might be detected.
            fields (dict[str, Any]) : Known fields of the section.
            excluded_fields (Set)   : Fields which should be excluded from the check for unknown keywords.
            config_extra (Extra)    : Setting which determines if unknown keywords are allowed or dropped.
        """
        if self._is_unknown_keyword(name, fields, excluded_fields):
            self._print_single_unknown_keyword(name, section_header, config_extra)
            
    def _get_all_unknown_keywords(self, data : dict[str, Any], fields : dict[str, Any], excluded_fields : Set) -> list[str]:
        list_of_unknown_keywords = []
        for name, _ in data.items():
            if self._is_unknown_keyword(name, fields, excluded_fields):
                list_of_unknown_keywords.append(name)
                
        return list_of_unknown_keywords
            
    def _is_unknown_keyword(self, name : str, fields : dict[str, Any], excluded_fields : Set):
        return name not in fields and name not in excluded_fields

    def _print_list_of_unknown_keywords(self, section_header : str, config_extra : Extra, list_of_unknown_keywords : list[str]):
        if config_extra == Extra.allow:
            print(f"Unknown keywords are detected in '{section_header}', these keywords will be kept in memory but will have no validation:")
        else:
            print(f"Unknown keywords are detected in '{section_header}', these keywords will be dropped:")
            
        for name in list_of_unknown_keywords:
            print(name)

    def _print_single_unknown_keyword(self, name : str, section_header : str, config_extra : Extra):
        if config_extra == Extra.allow:
            print(f"Unknown keyword detected in '{section_header}', '{name}', keyword will be kept in memory but will have no validation.")
        else:
            print(f"Unknown keyword detected in '{section_header}', '{name}', keyword will be dropped.")

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

    _header: str = ""
    _file_path_style_converter = FilePathStyleConverter()
    _unknown_key_notification_manager = UnknownKeyNotificationManager()

    class Config:
        extra = Extra.ignore
        arbitrary_types_allowed = False
        
    def __init__(self, **data):
        super().__init__(**data)
        self._unknown_key_notification_manager.notify_unknown_keywords(data, self._header,  self.__fields__, self._exclude_fields(), self.Config.extra)
    
    def __setattr__(self, name, value):
        self._unknown_key_notification_manager.notify_unknown_keyword(name, self._header,  self.__fields__, self._exclude_fields(), self.Config.extra)
        super().__setattr__(name, value)
    
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

    def _convert_value(
        self,
        key: str,
        v: Any,
        config: INISerializerConfig,
        save_settings: ModelSaveSettings,
    ) -> str:
        if isinstance(v, bool):
            return str(int(v))
        elif isinstance(v, list):
            convert_value = lambda x: self._convert_value(key, x, config, save_settings)
            return self.__class__.get_list_field_delimiter(key).join(
                [convert_value(x) for x in v]
            )
        elif isinstance(v, Enum):
            return v.value
        elif isinstance(v, float):
            return f"{v:{config.float_format}}"
        elif isinstance(v, FileModel) and v.filepath is not None:
            return self._file_path_style_converter.convert_from_os_style(
                v.filepath, save_settings.path_style
            )
        elif v is None:
            return ""
        else:
            return str(v)

    def _to_section(
        self, config: INISerializerConfig, save_settings: ModelSaveSettings
    ) -> Section:
        props = []
        for key, value in self:
            if key in self._exclude_fields():
                continue

            field_key = key
            if key in self.__fields__:
                key = self.__fields__[key].alias

            prop = Property(
                key=key,
                value=self._convert_value(field_key, value, config, save_settings),
                comment=getattr(self.comments, field_key, None),
            )
            props.append(prop)
        return Section(header=self._header, content=props)


Datablock = List[List[Union[float, str]]]


class DataBlockINIBasedModel(INIBasedModel):
    """DataBlockINIBasedModel defines the base model for ini models with datablocks.

    Attributes:
        datablock (Datablock): (class attribute) the actual data columns.
    """

    datablock: Datablock = []

    _make_lists = make_list_validator("datablock")

    def _to_section(
        self,
        config: DataBlockINIBasedSerializerConfig,
        save_settings: ModelSaveSettings,
    ) -> Section:
        section = super()._to_section(config, save_settings)
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

    @validator("datablock")
    def _validate_no_nans_are_present(cls, datablock: Datablock) -> Datablock:
        """Validate that the datablock does not have any NaN values.

        Args:
            datablock (Datablock): The datablock to verify.

        Raises:
            ValueError: When a NaN is present in the datablock.

        Returns:
            Datablock: The validated datablock.
        """
        if any(cls._is_float_and_nan(value) for list in datablock for value in list):
            raise ValueError("NaN is not supported in datablocks.")

        return datablock

    @staticmethod
    def _is_float_and_nan(value: float) -> bool:
        return isinstance(value, float) and isnan(value)


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

    def _to_document(self, save_settings: ModelSaveSettings) -> Document:
        header = CommentBlock(lines=[f"written by HYDROLIB-core {version}"])
        sections = []
        for key, value in self:
            if key in self._exclude_fields() or value is None:
                continue
            if isinstance(value, list):
                for v in value:
                    sections.append(
                        v._to_section(self.serializer_config, save_settings)
                    )
            else:
                sections.append(
                    value._to_section(self.serializer_config, save_settings)
                )
        return Document(header_comment=[header], sections=sections)

    def _serialize(self, _: dict, save_settings: ModelSaveSettings) -> None:
        write_ini(
            self._resolved_filepath,
            self._to_document(save_settings),
            config=self.serializer_config,
        )
