"""
Here we define our Pydantic `BaseModel` with custom settings,
as well as a `FileModel` that inherits from a `BaseModel` but
also represents a file on disk.

"""
import logging
from abc import ABC, abstractclassmethod
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Type
from warnings import warn
from weakref import WeakValueDictionary

from pydantic import BaseModel as PydanticBaseModel
from pydantic.error_wrappers import ErrorWrapper, ValidationError

from hydrolib.core.io.base import DummmyParser, DummySerializer
from hydrolib.core.utils import to_key

logger = logging.getLogger(__name__)

# We use ContextVars to keep a reference to the folder
# we're currently parsing files in. In the future
# we could move to https://github.com/samuelcolvin/pydantic/issues/1549
context_dir: ContextVar[Path] = ContextVar("folder")


def _reset_context_dir(token):
    # Once the model has been completely initialized
    # reset the context
    if token:
        logger.info("Reset context.")
        context_dir.reset(token)


class BaseModel(PydanticBaseModel):
    class Config:
        arbitrary_types_allowed = True
        validate_assignment = True
        use_enum_values = True
        extra = "forbid"  # will throw errors so we can fix our models
        allow_population_by_field_name = True
        alias_generator = to_key

    def __init__(self, **data: Any) -> None:
        """Initializes a BaseModel with the provided data.

        Raises:
            ValidationError: A validation error when the data is invalid.
        """
        try:
            super().__init__(**data)
        except ValidationError as e:
            id = self._get_identifier(data)
            if id is None:
                raise e
            else:
                raise ValidationError([ErrorWrapper(e, loc=id)], self.__class__)

    def is_file_link(self) -> bool:
        """Generic attribute for models backed by a file."""
        return False

    def is_intermediate_link(self) -> bool:
        """Generic attribute for models that have children fields that could contain files."""
        return self.is_file_link()

    def show_tree(self, indent=0):
        """Recursive print function for showing a tree of a model."""
        angle = "∟" if indent > 0 else ""

        # Only print if we're backed by a file
        if self.is_file_link():
            print(" " * indent * 2, angle, self)

        # Otherwise we recurse through the fields of a model
        for _, value in self:
            # Handle lists of items
            if not isinstance(value, list):
                value = [value]
            for v in value:
                if hasattr(v, "is_intermediate_link") and v.is_intermediate_link():
                    # If the field is only an intermediate, print the name only
                    if not v.is_file_link():
                        print(" " * (indent * 2 + 2), angle, v.__class__.__name__)
                    v.show_tree(indent + 1)

    def _apply_recurse(self, f, *args, **kwargs):
        # TODO Could we use this function for `show_tree`?
        for _, value in self:
            # Handle lists of items
            if not isinstance(value, list):
                value = [value]
            for v in value:
                if hasattr(v, "is_intermediate_link") and v.is_intermediate_link():
                    v._apply_recurse(f, *args, **kwargs)

        # Run self as last, so we can make use of the nested updates
        if self.is_file_link():
            getattr(self, f)(*args, **kwargs)

    def _get_identifier(self, data: dict) -> str:
        """Gets the identifier for this model.

        Args:
            data (dict): The data from which to retrieve the identifier

        Returns:
            str: The identifier or None.
        """
        return None


class FileModel(BaseModel, ABC):
    """Base class to represent models with a file representation.

    It therefore always has a `filepath` and if it is given on
    initilization, it will parse that file.

    This class extends the `validate` option of Pydantic,
    so when when a Path is given to a field with type `FileModel`,
    it doesn't error, but actually initializes the `FileModel`.
    """

    __slots__ = ["__weakref__"]
    # Use WeakValueDictionary to keep track of file paths with their respective parsed file models.
    _file_models_cache: WeakValueDictionary = WeakValueDictionary()
    filepath: Optional[Path] = None

    def __new__(cls, filepath: Optional[Path] = None, *args, **kwargs):
        """Creates a new model.
        If the file at the provided file path was already parsed, this instance is returned.

        Args:
            filepath (Optional[Path], optional): The absolute file path to the file. Defaults to None.

        Returns:
            FileModel: A file model.
        """

        if filepath:
            filepath = Path(filepath)

            if filepath in FileModel._file_models_cache:
                filemodel = FileModel._file_models_cache[filepath]
                logger.info(
                    f"Returning existing {type(filemodel).__name__} from cache, because {filepath} was already parsed."
                )
                return filemodel

        return super().__new__(cls)

    def __init__(self, filepath: Optional[Path] = None, *args, **kwargs):
        """Initialize a model.

        The model is empty (with defaults) if no `filepath` is given,
        otherwise the file at `filepath` will be parsed."""
        # Parse the file if path is given
        context_dir_reset_token = None
        if filepath:
            filepath = Path(filepath)  # so we also accept strings

            if filepath in FileModel._file_models_cache:
                return None

            # If not set, this is the root file path
            if not context_dir.get(None):
                logger.info(f"Set context to {filepath.parent}")
                context_dir_reset_token = context_dir.set(filepath.parent)

            FileModel._file_models_cache[filepath] = self

            logger.info(f"Loading data from {filepath}")
            data = self._load(filepath)
            data["filepath"] = filepath
            kwargs.update(data)

        try:
            super().__init__(*args, **kwargs)
        finally:
            _reset_context_dir(context_dir_reset_token)

    def is_file_link(self) -> bool:
        return True

    @classmethod
    def validate(cls: Type["FileModel"], value: Any):
        # Enable initialization with a Path.
        if isinstance(value, (Path, str)):
            filepath = Path(value)

            # Use the context if needed to resolve the absolute file path
            if not filepath.is_absolute():
                # The context_dir has been set within the initializer of the root FileModel
                folder = context_dir.get()
                logger.info(f"Used context to get {folder} for {filepath}")
                filepath = folder / filepath

            # Pydantic Model init requires a dict
            value = {"filepath": filepath}
        return super().validate(value)

    def _load(self, filepath: Path) -> Dict:
        # TODO Make this lazy in some cases
        # so it doesn't become slow
        if filepath.is_file():
            return self._parse(filepath)
        else:
            warn(f"File: `{filepath}` not found, skipped parsing.")
            return {}

    def save(self, folder: Optional[Path] = None) -> Path:
        """Save model and child models to their set filepaths.

        If a folder is given, for models with an unset filepath,
        we generate one based on the given `folder` and a default name.
        Otherwise we override the folder part of already set filepaths.
        This can thus be used to copy complete models.

        Args:
            folder: path to the folder where this FileModel will be stored
        """
        if not self.filepath and not folder:
            raise ValueError(
                "Either set the `filepath` on the model or pass a `folder` when saving."
            )

        if not folder:
            folder = self.filepath.absolute().parent

        self._apply_recurse("_save", folder)
        return self.filepath.absolute()

    def _save(self, folder):
        filename = Path(self.filepath.name) if self.filepath else self._generate_name()
        self.filepath = folder / filename

        self._serialize(self.dict())

    def _serialize(self, data: dict) -> None:
        self._get_serializer()(self.filepath, data)

    @classmethod
    def _parse(cls, path: Path) -> Dict:
        return cls._get_parser()(path)

    @classmethod
    def _generate_name(cls) -> Path:
        name, ext = cls._filename(), cls._ext()
        return Path(f"{name}{ext}")

    @abstractclassmethod
    def _filename(cls):
        return "test"

    @abstractclassmethod
    def _ext(cls):
        return ".test"

    @abstractclassmethod
    def _get_serializer(cls) -> Callable:
        return DummySerializer.serialize

    @abstractclassmethod
    def _get_parser(cls) -> Callable:
        return DummmyParser.parse

    def __str__(self) -> str:
        return str(self.filepath if self.filepath else "")

    def _get_identifier(self, data: dict) -> str:
        return data["filepath"].name
