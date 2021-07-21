"""
Here we define our Pydantic `BaseModel` with custom settings,
as well as a `FileModel` that inherits from a `BaseModel` but
also represents a file on disk.

"""
from abc import ABC, abstractclassmethod
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Type
from warnings import warn

from pydantic import BaseModel as PydanticBaseModel

from hydrolib.core.io.base import DummmyParser, DummySerializer
from hydrolib.core.utils import to_lowercase


class BaseModel(PydanticBaseModel):
    class Config:
        arbitrary_types_allowed = True
        validate_assignment = True
        use_enum_values = True
        extra = "forbid"  # will throw errors so we can fix our models
        allow_population_by_field_name = True
        alias_generator = to_lowercase


class FileModel(BaseModel, ABC):
    """Base class to represent models with a file representation.

    It therefore always has a `filepath` and if it is given on
    initilization, it will parse that file.

    This class extends the `validate` option of Pydantic,
    so when when a Path is given to a field with type `FileModel`,
    it doesn't error, but actually initializes the `FileModel`.
    """

    filepath: Optional[Path] = None

    def __init__(self, filepath: Optional[Path] = None, *args, **kwargs) -> None:
        """Initialize a model.

        The model is empty (with defaults) if no `filepath` is given,
        otherwise the file at `filepath` will be parsed."""
        # Parse the file if path is given
        if filepath:
            data = self._load(Path(filepath))  # so we also accept strings
            data["filepath"] = filepath
            kwargs.update(data)
        super().__init__(*args, **kwargs)

    @classmethod
    def validate(cls: Type["FileModel"], value: Any) -> "FileModel":
        # Enable initialization with a Path.
        if isinstance(value, Path):
            # Pydantic Model init requires a dict
            value = {"filepath": value}
        return super().validate(value)

    def _load(self, filepath: Path) -> Dict:
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

        if folder:
            filename = (
                Path(self.filepath.name) if self.filepath else self._generate_name()
            )
            self.filepath = folder / filename

        # Convert child FileModels first
        exclude = {"filepath"}
        filemodel_fields = {}
        for name, value in self:
            if isinstance(value, FileModel):
                filepath = value.save(folder)
                filemodel_fields[name] = filepath
                exclude.add(name)

        # Convert other values to dict
        data = self.dict(
            exclude=exclude,
            exclude_none=True,  # either skip it here, or in serializer
        )
        data.update(filemodel_fields)

        self._serialize(data)

        return self.filepath.absolute()

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
