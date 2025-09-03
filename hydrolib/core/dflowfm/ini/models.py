import logging
from abc import ABC
from enum import Enum
from inspect import isclass
from math import isnan
from typing import (
    Annotated,
    Any,
    Callable,
    List,
    Literal,
    Optional,
    Set,
    Type,
    Union,
    get_args,
    get_origin,
)

from pandas import DataFrame
from pydantic import (
    BeforeValidator,
    ConfigDict,
    Field,
    GetCoreSchemaHandler,
    field_validator,
    model_validator,
)
from pydantic.fields import FieldInfo
from pydantic_core import core_schema

from hydrolib.core import __version__ as version
from hydrolib.core.base.file_manager import FilePathStyleConverter
from hydrolib.core.base.models import (
    BaseModel,
    FileModel,
    ModelSaveSettings,
    ParsableFileModel,
)
from hydrolib.core.base.utils import FortranScientificNotationConverter
from hydrolib.core.dflowfm.ini.io_models import (
    CommentBlock,
    Document,
    Property,
    Section,
)
from hydrolib.core.dflowfm.ini.parser import Parser
from hydrolib.core.dflowfm.ini.serializer import (
    DataBlockINIBasedSerializerConfig,
    INISerializerConfig,
    write_ini,
)
from hydrolib.core.dflowfm.ini.util import UnknownKeywordErrorManager, make_list

logger = logging.getLogger(__name__)


class INIBasedModel(BaseModel, ABC):
    """INIBasedModel defines the base model for blocks/chapters
    inside an INIModel (*.ini file).

    - Abstract base class for representing INI-style configuration file blocks or chapters.
    - This class serves as the foundational model for handling blocks within INI configuration files.
    It supports creating instances from parsed INI sections, adding arbitrary fields, and ensuring
    well-defined serialization and deserialization behavior. Subclasses are expected to define
    specific behavior and headers for their respective INI blocks.

    Attributes:
        comments (Optional[Comments]):
            Optional Comments if defined by the user, containing descriptions for all data fields.

    Args:
        comments (Optional[Comments], optional):
            Comments for the model fields. Defaults to None.

    Raises:
        ValueError: If unknown fields are encountered during validation.

    See Also:
        BaseModel: The Pydantic base model extended by this class.
        INISerializerConfig: Provides configuration for INI serialization.


    Examples:
        Define a custom INI block subclass:
            ```python
            >>> from hydrolib.core.dflowfm.ini.models import INIBasedModel
            >>> class MyModel(INIBasedModel):
            ...     _header = "MyHeader"
            ...     field_a: str = "default_value"

            ```

        Parse an INI section:
            ```python
            >>> from hydrolib.core.dflowfm.ini.io_models import Section
            >>> section = Section(header="MyHeader", content=[{"key": "field_a", "value": "value"}])
            >>> model = MyModel.model_validate(section.flatten())
            >>> print(model.field_a)
            value

            ```

        Serialize a model to an INI format:
            ```python
            >>> from hydrolib.core.dflowfm.ini.serializer import INISerializerConfig
            >>> from hydrolib.core.base.models import ModelSaveSettings
            >>> config = INISerializerConfig()
            >>> section = model._to_section(config, save_settings=ModelSaveSettings())
            >>> print(section.header)
            MyHeader

            ```

    Notes:
        - Subclasses can override the `_header` attribute to define the INI block header.
        - Arbitrary fields can be added dynamically and are included during serialization.
    """

    _header: str = ""
    _file_path_style_converter = FilePathStyleConverter()
    model_config = ConfigDict(
        extra="ignore",
        arbitrary_types_allowed=False,
        populate_by_name=True,
        error_url_template=None,
    )

    @classmethod
    def _get_unknown_keyword_error_manager(cls) -> Optional[UnknownKeywordErrorManager]:
        """
        Retrieves the error manager for handling unknown keywords in INI files.

        Returns:
            Optional[UnknownKeywordErrorManager]:
                An instance of the error manager or None if unknown keywords are allowed.
        """
        return UnknownKeywordErrorManager()

    @classmethod
    def _supports_comments(cls) -> bool:
        """
        Indicates whether the model supports comments for its fields.

        Returns:
            bool: True if comments are supported; otherwise, False.
        """
        return True

    @classmethod
    def _duplicate_keys_as_list(cls) -> bool:
        """
        Indicates whether duplicate keys in INI sections should be treated as lists.

        Returns:
            bool: True if duplicate keys should be treated as lists; otherwise, False.
        """
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

        Returns:
            str: the delimiter string to be used for serializing the given field.
        """
        delimiter = None
        field_info = cls.model_fields.get(field_key)
        if (
            (field := field_info)
            and isinstance(field, FieldInfo)
            and field.json_schema_extra
        ):
            delimiter = field.json_schema_extra.get("delimiter")
        if not delimiter:
            delimiter = cls.get_list_delimiter()

        return delimiter

    class Comments(BaseModel, ABC):
        """
        Represents the comments associated with fields in an INIBasedModel.

        Attributes:
            Arbitrary fields can be added dynamically to store comments.

        Config:
            extra: Extra.allow
                Allows dynamic fields for comments.
            arbitrary_types_allowed: bool
                Indicates that only known types are allowed.
        """

        model_config = ConfigDict(extra="allow", arbitrary_types_allowed=False)

    comments: Optional[Comments] = Comments()

    @model_validator(mode="before")
    @classmethod
    def _validate_unknown_keywords(cls, values):
        """
        Validates fields and raises errors for unknown keywords.

        Args:
            values (dict): Dictionary of field values to validate.

        Returns:
            dict: Validated field values.

        Raises:
            ValueError: If unknown keywords are found.
        """
        unknown_keyword_error_manager = cls._get_unknown_keyword_error_manager()
        do_not_validate = cls._exclude_from_validation(values)
        if unknown_keyword_error_manager:
            unknown_keyword_error_manager.raise_error_for_unknown_keywords(
                values,
                cls._header,
                cls.model_fields,
                cls._exclude_fields() | do_not_validate,
            )
        return values

    @model_validator(mode="before")
    @classmethod
    def _skip_nones_and_set_header(cls, values):
        """Drop None fields for known fields.

        Filters out None values and sets the model header.

        Args:
            values (dict): Dictionary of field values.

        Returns:
            dict: Updated field values with None values removed.
        """
        # Convert Section to dictionary if needed
        values = cls._convert_section_to_dict(values)
        if not isinstance(values, dict):
            return values

        dropkeys = []
        for k, v in values.items():
            if v is None and k in cls.model_fields.keys():
                dropkeys.append(k)

        logger.info(f"Dropped unset keys: {dropkeys}")
        for k in dropkeys:
            values.pop(k)

        if "_header" in values:
            values["_header"] = cls._header

        return values

    @field_validator("comments", mode="after")
    @classmethod
    def comments_matches_has_comments(cls, v):
        """
        Validates the presence of comments if supported by the model.

        Args:
            v (Any): The comments field value.

        Returns:
            Any: Validated comments field value.
        """
        if not cls._supports_comments() and v is not None:
            logging.warning(f"Dropped unsupported comments from {cls.__name__} init.")
            v = None
        return v

    def __setattr__(self, key, value) -> None:
        """
        Custom setter to handle Fortran-style scientific notation conversion
        for float fields when setting attributes.
        """
        field = self.__class__.model_fields.get(key)
        if field is None:
            super().__setattr__(key, value)
            return

        field_type = field.annotation
        if field_type in (float, List[float]):
            value = FortranScientificNotationConverter.convert(value)
        super().__setattr__(key, value)

    @classmethod
    def preprocess_input(cls, values: dict) -> dict:
        """Pre-process input values for the model.

        The preprocess_input method is called before validation and triggers the following actions:
            - Convert Fortran-style scientific notation to Python float.
        """
        if isinstance(values, dict):
            new_values = FortranScientificNotationConverter.convert_fields(
                values, cls.model_fields
            )
        else:
            new_values = values

        return new_values

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        schema = handler(source_type)

        return core_schema.no_info_before_validator_function(
            cls.preprocess_input,  # this is called BEFORE validation
            schema,
        )

    @classmethod
    def _convert_section_to_dict(cls, value: Any) -> Any:
        """
        Converts a Section object to a dictionary if needed.

        Args:
            value (Any): The value to convert.

        Returns:
            Any: The converted value (dictionary) or the original value if not a Section.
        """
        if isinstance(value, Section):
            return value.flatten(
                cls._duplicate_keys_as_list(), cls._supports_comments()
            )
        return value

    @classmethod
    def _extract_file_model_from_section(
        cls, section: Section, key: str, file_model_class: Type
    ):
        """Extracts a file model from a Section object.

        Args:
            section (Section):
                The Section object to extract from.
            key (str):
                The key to look for in the Section.
            file_model_class (Type):
                The class to use for creating the file model.

        Returns:
            Optional[Any]:
                The file model if found, None otherwise.
        """
        for prop in section.content:
            if isinstance(prop, Property) and prop.key.lower() == key.lower():
                return file_model_class(prop.value)
        return None

    @classmethod
    def model_validate(cls: Type["INIBasedModel"], value: Any) -> "INIBasedModel":
        """
        Validates a value as an instance of INIBasedModel.

        Args:
            value (Any): The value to validate.

        Returns:
            INIBasedModel: The validated instance.
        """
        value = cls._convert_section_to_dict(value)
        return super().model_validate(value)

    @classmethod
    def _exclude_from_validation(cls, input_data: Optional[dict] = None) -> Set:
        """
        Fields that should not be checked when validating existing fields as they will be dynamically added.

        Args:
            input_data (Optional[dict]): Input data to process.

        Returns:
            Set: Set of field names to exclude from validation.
        """
        return set()

    @classmethod
    def _exclude_fields(cls) -> Set:
        """
        Defines fields to exclude from serialization.

        Returns:
            Set: Set of field names to exclude.
        """
        return {"comments", "datablock", "_header"}

    def _convert_value(
        self,
        key: str,
        v: Any,
        config: INISerializerConfig,
        save_settings: ModelSaveSettings,
    ) -> str:
        """
        Converts a field value to its serialized string representation.

        Args:
            key (str): The field key.
            v (Any): The field value.
            config (INISerializerConfig): Configuration for serialization.
            save_settings (ModelSaveSettings): Settings for saving the model.

        Returns:
            str: The serialized value.
        """
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
        """
        Converts the model to an INI section.

        Args:
            config (INISerializerConfig): Configuration for serialization.
            save_settings (ModelSaveSettings): Settings for saving the model.

        Returns:
            Section: The INI section representation of the model.
        """
        props = []
        cls_fields = type(self).model_fields  # cache the class-level dict
        for key, value in self:
            if not self._should_be_serialized(key, value, save_settings):
                continue

            field_key = key
            if key in cls_fields:
                key = cls_fields[key].alias

            prop = Property(
                key=key,
                value=self._convert_value(field_key, value, config, save_settings),
                comment=getattr(self.comments, field_key, None),
            )
            props.append(prop)
        return Section(header=self._header, content=props)

    def _should_be_serialized(
        self, key: str, value: Any, save_settings: ModelSaveSettings
    ) -> bool:
        """
        Determines if a field should be serialized.

        Args:
            key (str): The field key.
            value (Any): The field value.
            save_settings (ModelSaveSettings): Settings for saving the model.

        Returns:
            bool: True if the field should be serialized; otherwise, False.
        """
        if key in self._exclude_fields():
            return False

        if save_settings._exclude_unset and key not in self.model_fields_set:
            return False

        cls_fields = type(self).model_fields
        field = cls_fields.get(key)
        if not field:
            return value is not None

        field_type = field.annotation
        if self._is_union(field_type):
            return value is not None or self._union_has_filemodel(field_type)

        if self._is_list(field_type):
            field_type = get_args(field_type)[0]

        return self._value_is_not_none_or_type_is_filemodel(field_type, value)

    @staticmethod
    def _is_union(field_type: type) -> bool:
        """
        Checks if a type is a Union.

        Args:
            field_type (type): The type to check.

        Returns:
            bool: True if the type is a Union; otherwise, False.
        """
        return get_origin(field_type) is Union

    @staticmethod
    def _union_has_filemodel(field_type: type) -> bool:
        """
        Checks if a Union type includes a FileModel subtype.

        Args:
            field_type (type): The type to check.

        Returns:
            bool: True if the Union includes a FileModel; otherwise, False.
        """
        return any(
            isclass(arg) and issubclass(arg, FileModel) for arg in get_args(field_type)
        )

    @staticmethod
    def _is_list(field_type: type) -> bool:
        """
        Checks if a type is a list.

        Args:
            field_type (type): The type to check.

        Returns:
            bool: True if the type is a list; otherwise, False.
        """
        return get_origin(field_type) is List or get_origin(field_type) is list

    @staticmethod
    def _value_is_not_none_or_type_is_filemodel(field_type: type, value: Any) -> bool:
        """
        Checks if a value is not None or if its type is FileModel.

        Args:
        field_type (type): The expected type of the field.
        value (Any): The value to check.

        Returns:
            bool: True if the value is valid; otherwise, False.
        """
        return value is not None or issubclass(field_type, FileModel)


Datablock = List[List[Union[float, str]]]


class DataBlockINIBasedModel(INIBasedModel):
    """DataBlockINIBasedModel defines the base model for ini models with datablocks.

    This class extends the functionality of INIBasedModel to handle structured data blocks
    commonly found in INI files. It provides validation, serialization, and conversion methods
    for working with these data blocks.

    Attributes:
        datablock (Datablock): (class attribute) the actual data columns.

    Attributes:
    datablock (List[List[Union[float, str]]]):
        A two-dimensional list representing the data block. Each sub-list corresponds to
        a row in the data block, and the values can be either floats or strings.

    Args:
        datablock (List[List[Union[float, str]]], optional):
            The initial data block for the model. Defaults to an empty list.

    Raises:
        ValueError: If a NaN value is found within the data block.

    See Also:
        INIBasedModel: The parent class for models representing INI-based configurations.
        INISerializerConfig: Provides configuration for INI serialization.

    Examples:
        Create a model and validate its data block:
            ```python
            >>> from hydrolib.core.dflowfm.ini.models import DataBlockINIBasedModel
            >>> model = DataBlockINIBasedModel(datablock=[[1.0, 2.0], [3.0, 4.0]])
            >>> print(model.datablock)
            [[1.0, 2.0], [3.0, 4.0]]

            ```

        Attempt to create a model with invalid data:
            ```python
            >>> try:
            ...     model = DataBlockINIBasedModel(datablock=[[1.0, None]])
            ... except Exception as e:
            ...     print(e)
            1 validation error for DataBlockINIBasedModel
            datablock -> 0 -> 1
              none is not an allowed value (type=type_error.none.not_allowed)

            ```

    Notes:
        - The class includes a validator to ensure that no NaN values are present in the data block.
        - Data blocks are converted to a serialized format for writing to INI files.
    """

    datablock: Annotated[Datablock, BeforeValidator(make_list)] = Field(
        default_factory=list
    )

    @staticmethod
    def _is_float(value: str) -> bool:
        """
        Determines whether a value is a float.

        Args:
            value (str): The value to check.

        Returns:
            bool: True if the value can be converted to a float; otherwise, False.
        """
        try:
            float(value)
            return True
        except ValueError:
            return False

    @field_validator("datablock", mode="before")
    @classmethod
    def _convert_to_float(cls, datablock: Datablock) -> Datablock:
        """
        Validates that all values in the datablock are either floats or strings.

        Args:
            datablock (Datablock): The datablock to validate.

        Returns:
            Datablock: The validated datablock.

        Raises:
            ValueError: If any value in the datablock is not a float or string.
        """
        for r, row in enumerate(datablock):
            for c, value in enumerate(row):
                if isinstance(value, str) and cls._is_float(value):
                    datablock[r][c] = float(value)
        return datablock

    @classmethod
    def _get_unknown_keyword_error_manager(cls) -> Optional[UnknownKeywordErrorManager]:
        """
        The DataBlockINIBasedModel does not need to raise an error on unknown keywords.

        Returns:
            Optional[UnknownKeywordErrorManager]: Returns None as unknown keywords are ignored.
        """
        return None

    def as_dataframe(self) -> DataFrame:
        """Convert the datablock as a pandas DataFrame

        - The first number from each list in the block as an index for that row.

        Returns:
            DataFrame: The datablock as a pandas DataFrame.

        Examples:
                >>> from hydrolib.core.dflowfm.ini.models import DataBlockINIBasedModel
                >>> model = DataBlockINIBasedModel(datablock=[[0, 10, 100], [1, 20, 200]])
                >>> df = model.as_dataframe()
                >>> print(df)
                        0      1
                0.0  10.0  100.0
                1.0  20.0  200.0
        """
        df = DataFrame(self.datablock).set_index(0)
        df.index.name = None
        df.columns = range(len(df.columns))
        return df

    def _to_section(
        self,
        config: DataBlockINIBasedSerializerConfig,
        save_settings: ModelSaveSettings,
    ) -> Section:
        """
        Converts the current model to an INI Section representation.

        Args:
            config (DataBlockINIBasedSerializerConfig): Configuration for serializing the data block.
            save_settings (ModelSaveSettings): Settings for saving the model.

        Returns:
            Section: The INI Section containing serialized data and the data block.
        """
        section = super()._to_section(config, save_settings)
        section.datablock = self._to_datablock(config)
        return section

    def _to_datablock(self, config: DataBlockINIBasedSerializerConfig) -> List[List]:
        """
        Converts the data block to a serialized format based on the configuration.

        Args:
            config (DataBlockINIBasedSerializerConfig): Configuration for serializing the data block.

        Returns:
            List[List]: A serialized representation of the data block.
        """
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
        """
        Converts a value in the data block to its serialized string representation.

        Args:
            value (Union[float, str]): The value to be converted.
            config (DataBlockINIBasedSerializerConfig): Configuration for the conversion.

        Returns:
            str: The serialized string representation of the value.
        """
        if isinstance(value, float):
            return f"{value:{config.float_format_datablock}}"

        return value

    @field_validator("datablock", mode="after")
    @classmethod
    def _validate_no_nans_are_present(cls, datablock: Datablock) -> Datablock:
        """Validate that the datablock does not have any NaN values.

        Args:
            datablock (Datablock): The datablock to validate.

        Raises:
            ValueError: When a NaN is present in the datablock.

        Returns:
            Datablock: The validated datablock.
        """
        if any(cls._is_float_and_nan(value) for row in datablock for value in row):
            raise ValueError("NaN is not supported in datablocks.")

        return datablock

    @staticmethod
    def _is_float_and_nan(value: float) -> bool:
        """
        Determines whether a value is a float and is NaN.

        Args:
            value (float): The value to check.

        Returns:
            bool: True if the value is a NaN float; otherwise, False.
        """
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
            if save_settings._exclude_unset and key not in self.model_fields_set:
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
        """
        Create a `Document` from the model and write it to the file.
        """
        write_ini(
            self._resolved_filepath,
            self._to_document(save_settings),
            config=self.serializer_config,
        )
