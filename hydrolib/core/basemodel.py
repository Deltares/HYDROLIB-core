"""
Here we define our Pydantic `BaseModel` with custom settings,
as well as a `FileModel` that inherits from a `BaseModel` but
also represents a file on disk.

"""
import logging
import shutil
from abc import ABC, abstractclassmethod, abstractmethod
from contextlib import contextmanager
from contextvars import ContextVar
from enum import IntEnum
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from weakref import WeakValueDictionary

from pydantic import BaseModel as PydanticBaseModel
from pydantic import validator
from pydantic.error_wrappers import ErrorWrapper, ValidationError
from pydantic.fields import ModelField, PrivateAttr

from hydrolib.core.base import DummmyParser, DummySerializer
from hydrolib.core.utils import (
    FilePathStyleConverter,
    OperatingSystem,
    PathStyle,
    get_operating_system,
    get_path_style_for_current_operating_system,
    str_is_empty_or_none,
    to_key,
)

logger = logging.getLogger(__name__)

# We use ContextVars to keep a reference to the folder
# we're currently parsing files in. In the future
# we could move to https://github.com/samuelcolvin/pydantic/issues/1549
context_file_loading: ContextVar["FileLoadContext"] = ContextVar("file_loading")


class BaseModel(PydanticBaseModel):
    class Config:
        arbitrary_types_allowed = True
        validate_assignment = True
        use_enum_values = True
        extra = "forbid"  # will throw errors so we can fix our models
        allow_population_by_field_name = True
        alias_generator = to_key

    def __init__(self, **data: Any) -> None:
        """Initialize a BaseModel with the provided data.

        Raises:
            ValidationError: A validation error when the data is invalid.
        """
        try:
            super().__init__(**data)
        except ValidationError as e:

            # Give a special message for faulty list input
            for re in e.raw_errors:
                if (
                    hasattr(re, "_loc")
                    and hasattr(re.exc, "msg_template")
                    and isinstance(data.get(to_key(re._loc)), list)
                ):
                    re.exc.msg_template += (
                        f". The key {re._loc} might be duplicated in the input file."
                    )

            # Update error with specific model location name
            identifier = self._get_identifier(data)
            if identifier is None:
                raise e
            else:
                # If there is an identifier, include this in the ValidationError messages.
                raise ValidationError([ErrorWrapper(e, loc=identifier)], self.__class__)

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

    def _get_identifier(self, data: dict) -> Optional[str]:
        """Get the identifier for this model.

        Args:
            data (dict): The data from which to retrieve the identifier

        Returns:
            str: The identifier or None.
        """
        return None


TAcc = TypeVar("TAcc")


class ModelTreeTraverser(Generic[TAcc]):
    """ModelTreeTraverser is responsible for traversing a ModelTree using the provided
    functions.

    The ModelTreeTraverser will only traverse BaseModel and derived objects.
    Type parameter TAcc defines the type of Accumulator to be used.
    """

    def __init__(
        self,
        should_traverse: Optional[Callable[[BaseModel, TAcc], bool]] = None,
        should_execute: Optional[Callable[[BaseModel, TAcc], bool]] = None,
        pre_traverse_func: Optional[Callable[[BaseModel, TAcc], TAcc]] = None,
        post_traverse_func: Optional[Callable[[BaseModel, TAcc], TAcc]] = None,
    ):
        """Create a new ModelTreeTraverser with the given functions.

        If a predicate it is not defined, it is assumed to always be true, i.e. we will
        always traverse to the next node, or always execute the traverse functions.

        If a traverse function is not defined, it will be skipped.

        The traverse functions share an accumulator, i.e. the accumulator argument
        is passed through all evaluated traverse functions. It is expected that the
        traverse function return the (potentially) changed accumulator.

        Args:
            should_traverse (Optional[Callable[[BaseModel, TAcc], bool]], optional):
                Function to evaluate whether to traverse to the provided BaseModel. Defaults to None.
            should_execute (Optional[Callable[[BaseModel, TAcc], bool]], optional):
                Function to evaluate whether to execute the traverse functions for the
                provided BaseModel. Defaults to None.
            pre_traverse_func (Callable[[BaseModel, TAcc], TAcc], optional):
                Traverse function executed before we traverse into the next BaseModel,
                i.e. top-down traversal. Defaults to None.
            post_traverse_func (Callable[[BaseModel, TAcc], TAcc], optional):
                Traverse function executed after we traverse into the next BaseModel,
                i.e. bottom-up traversal. Defaults to None.
        """
        self._should_traverse_func = should_traverse
        self._should_execute_func = should_execute
        self._pre_traverse_func = pre_traverse_func
        self._post_traverse_func = post_traverse_func

    def _should_execute(self, model: BaseModel, acc: TAcc) -> bool:
        return self._should_execute_func is None or self._should_execute_func(
            model, acc
        )

    def _should_execute_pre(self, model: BaseModel, acc: TAcc) -> bool:
        return self._pre_traverse_func is not None and self._should_execute(model, acc)

    def _should_execute_post(self, model: BaseModel, acc: TAcc) -> bool:
        return self._post_traverse_func is not None and self._should_execute(model, acc)

    def _should_traverse(self, value: Any, acc: TAcc) -> bool:
        return isinstance(value, BaseModel) and (
            self._should_traverse_func is None or self._should_traverse_func(value, acc)
        )

    def traverse(self, model: BaseModel, acc: TAcc) -> TAcc:
        """Traverse the model tree of BaseModels including the model as the root, with
        the provided state of the acc and return the final accumulator.

        The actual executed functions as well as the predicates defining whether these
        functions should be executed for this model as well as whether child BaseModel
        objects should be traversed are provided in the constructor of the
        ModelTreeTraverser.

        The final accumulator is returned.

        Args:
            model (BaseModel):
                The root model in which the traversal of the model tree starts.
            acc (TAcc):
                The current accumulator.

        Returns:
            TAcc: The accumulator after the traversal of the model tree.
        """
        if self._should_execute_pre(model, acc):
            acc = self._pre_traverse_func(model, acc)  # type: ignore[arg-type]

        for _, value in model:
            if not isinstance(value, list):
                value = [value]

            for v in value:
                if self._should_traverse(v, acc):
                    acc = self.traverse(v, acc)

        if self._should_execute_post(model, acc):
            acc = self._post_traverse_func(model, acc)  # type: ignore[arg-type]

        return acc


class ResolveRelativeMode(IntEnum):
    """ResolveRelativeMode defines the possible resolve modes used within the
    FilePathResolver.

    It determines how the relative paths to child models within some FileModel
    should be interpreted. By default it should be relative to the parent model,
    i.e. the model in which the mode is defined. However there exist some exceptions,
    where the relative paths should be evaluated relative to some other folder,
    regardless of the current parent location.

    Options:
        ToParent:
            Relative paths should be resolved relative to their direct parent model.
        ToAnchor:
            All relative paths should be resolved relative to the specified regardless
            of subsequent parent model locations.
    """

    ToParent = 0
    ToAnchor = 1


class FileCasingResolver:
    """Class for resolving file path in a case-insensitive manner."""

    def resolve(self, path: Path) -> Path:
        """Resolve the casing of a file path when the file does exist but not with the exact casing.

        Args:
            path (Path): The path of the file or directory for which the casing needs to be resolved.

        Returns:
            Path: The file path with the matched casing if a match exists; otherwise, the original file path.

        Raises:
            NotImplementedError: When this function is called with an operating system other than Windows, Linux or MacOS.
        """

        operating_system = get_operating_system()
        if operating_system == OperatingSystem.WINDOWS:
            return self._resolve_casing_windows(path)
        if operating_system == OperatingSystem.LINUX:
            return self._resolve_casing_linux(path)
        if operating_system == OperatingSystem.MACOS:
            return self._resolve_casing_macos(path)
        else:
            raise NotImplementedError(
                f"Path case resolving for operating system {operating_system} is not supported yet."
            )

    def _resolve_casing_windows(self, path: Path):
        return path.resolve()

    def _resolve_casing_linux(self, path: Path):
        if path.exists():
            return path

        if not path.parent.exists() and not str_is_empty_or_none(path.parent.name):
            path = self._resolve_casing_linux(path.parent) / path.name

        return self._find_match(path)

    def _resolve_casing_macos(self, path: Path):
        if not str_is_empty_or_none(path.parent.name):
            path = self._resolve_casing_macos(path.parent) / path.name

        return self._find_match(path)

    def _find_match(self, path: Path):
        if path.parent.exists():
            for item in path.parent.iterdir():
                if item.name.lower() == path.name.lower():
                    return path.with_name(item.name)

        return path


class FilePathResolver:
    """FilePathResolver is responsible for resolving relative paths.

    The current state to which paths are resolved can be altered by
    pushing a new parent path to the FilePathResolver, or removing the
    latest added parent path from the FilePathResolver
    """

    def __init__(self) -> None:
        """Create a new empty FilePathResolver."""
        self._anchors: List[Path] = []
        self._parents: List[Tuple[Path, ResolveRelativeMode]] = []

    @property
    def _anchor(self) -> Optional[Path]:
        return self._anchors[-1] if self._anchors else None

    @property
    def _direct_parent(self) -> Path:
        return self._parents[-1][0] if self._parents else Path.cwd()

    def get_current_parent(self) -> Path:
        """Get the current absolute path with which files are resolved.

        If the current mode is relative to the parent, the latest added
        parent is added. If the current mode is relative to an anchor
        path, the latest added anchor path is returned.

        Returns:
            Path: The absolute path to the current parent.
        """
        if self._anchor:
            return self._anchor
        return self._direct_parent

    def resolve(self, path: Path) -> Path:
        """Resolve the provided path to an absolute path given the current state.

        If the provided path is already absolute, it will be returned as is.

        Args:
            path (Path): The path to resolve

        Returns:
            Path: An absolute path resolved given the current state.
        """
        if path.is_absolute():
            return path

        parent = self.get_current_parent()
        return (parent / path).resolve()

    def push_new_parent(
        self, parent_path: Path, relative_mode: ResolveRelativeMode
    ) -> None:
        """Push a new parent_path with the given relative_mode to this FilePathResolver.

        Relative paths added to this FilePathResolver will be resolved with respect
        to the current state, i.e. similar to FilePathResolver.resolve.

        Args:
            parent_path (Path): The parent path
            relative_mode (ResolveRelativeMode): The relative mode used to resolve.
        """
        absolute_parent_path = self.resolve(parent_path)
        if relative_mode == ResolveRelativeMode.ToAnchor:
            self._anchors.append(absolute_parent_path)

        self._parents.append((absolute_parent_path, relative_mode))

    def pop_last_parent(self) -> None:
        """Pop the last added parent from this FilePathResolver

        If there are currently no parents defined, nothing will happen.
        """
        if not self._parents:
            return

        _, relative_mode = self._parents.pop()

        if relative_mode == ResolveRelativeMode.ToAnchor:
            self._anchors.pop()


class FileModelCache:
    """
    FileModelCache provides a simple structure to register and retrieve FileModel
    objects.
    """

    def __init__(self):
        """Create a new empty FileModelCache."""
        self._cache_dict: Dict[Path, "FileModel"] = {}

    def retrieve_model(self, path: Path) -> Optional["FileModel"]:
        """Retrieve the model associated with the (absolute) path if
        it has been registered before, otherwise return None.

        Returns:
            [Optional[FileModel]]:
                The FileModel associated with the Path if it has been registered
                before, otherwise None.
        """
        return self._cache_dict.get(path, None)

    def register_model(self, path: Path, model: "FileModel") -> None:
        """Register the model with the specified path in this FileModelCache.

        Args:
            path (Path): The path to associate the model with.
            model (FileModel): The model to be associated with the path.
        """
        self._cache_dict[path] = model

    def is_empty(self) -> bool:
        """Whether or not this file model cache is empty.

        Returns:
            bool: Whether or not the cache is empty.
        """
        return not any(self._cache_dict)


class ModelSaveSettings:
    """A class that holds the global settings for model saving."""

    _os_path_style = get_path_style_for_current_operating_system()

    def __init__(self, path_style: Optional[PathStyle] = None) -> None:
        """Initializes a new instance of the ModelSaveSettings class.

        Args:
            path_style (Optional[PathStyle], optional): Which file path style to use when saving the model. Defaults to the path style that matches the current operating system.
        """

        if path_style is None:
            path_style = self._os_path_style

        self._path_style = path_style

    @property
    def path_style(self) -> PathStyle:
        """Gets the path style setting.

        Returns:
            PathStyle: Which path style is used to save the files.
        """
        return self._path_style


class ModelLoadSettings:
    """A class that holds the global settings for model loading."""

    def __init__(
        self, recurse: bool, resolve_casing: bool, path_style: PathStyle
    ) -> None:
        """Initializes a new instance of the ModelLoadSettings class.

        Args:
            recurse (bool): Whether or not to recursively load the whole model.
            resolve_casing (bool): Whether or not to resolve the file casing.
            path_style (PathStyle): Which path style is used in the loaded files.
        """
        self._recurse = recurse
        self._resolve_casing = resolve_casing
        self._path_style = path_style

    @property
    def recurse(self) -> bool:
        """Gets the recurse setting.

        Returns:
            bool: Whether or not to recursively load the whole model.
        """
        return self._recurse

    @property
    def resolve_casing(self) -> bool:
        """Gets the resolve casing setting.

        Returns:
            bool: Whether or not to resolve the file casing.
        """
        return self._resolve_casing

    @property
    def path_style(self) -> PathStyle:
        """Gets the path style setting.

        Returns:
            PathStyle: Which path style is used in the loaded files.
        """
        return self._path_style


class FileLoadContext:
    """FileLoadContext provides the context necessary to resolve paths
    during the init of a FileModel, as well as ensure the relevant models
    are only read once.
    """

    def __init__(self) -> None:
        """Create a new empty FileLoadContext."""
        self._path_resolver = FilePathResolver()
        self._cache = FileModelCache()
        self._file_casing_resolver = FileCasingResolver()
        self._file_path_style_converter = FilePathStyleConverter()
        self._load_settings: Optional[ModelLoadSettings] = None

    def initialize_load_settings(
        self, recurse: bool, resolve_casing: bool, path_style: PathStyle
    ):
        """Initialize the global model load setting. Can only be set once.

        Args:
            recurse (bool): Whether or not to recursively load the whole model.
            resolve_casing (bool): Whether or not to resolve the file casing.
            path_style (PathStyle): Which path style is used in the loaded files.
        """
        if self._load_settings is None:
            self._load_settings = ModelLoadSettings(recurse, resolve_casing, path_style)

    @property
    def load_settings(self) -> ModelLoadSettings:
        """Gets the model load settings.

        Raises:
            ValueError: When the model load settings have not been initialized yet.
        Returns:
            ModelLoadSettings: The model load settings.

        """
        if self._load_settings is None:
            raise ValueError(
                f"The model load settings have not been initialized yet. Make sure to call `{self.initialize_load_settings.__name__}` first."
            )

        return self._load_settings

    def retrieve_model(self, path: Optional[Path]) -> Optional["FileModel"]:
        """Retrieve the model associated with the path.

        If no model has been associated with the provided path, or the path is None,
        then None will be returned. Relative paths will be resolved based on the
        current state of the FileLoadContext.

        Returns:
            [Optional[FileModel]]:
                The file model associated with the provided path if it has been
                registered, else None.
        """
        if path is None:
            return None

        absolute_path = self._path_resolver.resolve(path)
        return self._cache.retrieve_model(absolute_path)

    def register_model(self, path: Path, model: "FileModel") -> None:
        """Associate the provided model with the provided path.

        Relative paths will be resolved based on the current state of the
        FileLoadContext.

        Args:
            path (Path): The relative path from which the model was loaded.
            model (FileModel): The loaded model.
        """
        absolute_path = self._path_resolver.resolve(path)
        self._cache.register_model(absolute_path, model)

    def cache_is_empty(self) -> bool:
        """Whether or not the file model cache is empty.

        Returns:
            bool: Whether or not the file model cache is empty.
        """
        return self._cache.is_empty()

    def get_current_parent(self) -> Path:
        """Get the current absolute path with which files are resolved.

        If the current mode is relative to the parent, the latest added
        parent is added. If the current mode is relative to an anchor
        path, the latest added anchor path is returned.

        Returns:
            Path: The absolute path to the current parent.
        """
        return self._path_resolver.get_current_parent()

    def resolve(self, path: Path) -> Path:
        """Resolve the provided path.

        If path is already absolute, it will be returned as is. Otherwise
        it will be resolved based on the current state of this FileLoadContext.

        Args:
            path (Path): The path to be resolved.

        Returns:
            Path: An absolute path resolved based on the current state.
        """
        return self._path_resolver.resolve(path)

    def push_new_parent(
        self, parent_path: Path, relative_mode: ResolveRelativeMode
    ) -> None:
        """Push a new parent_path with the given relative_mode on this
        FileLoadContext.

        Args:
            parent_path (Path): The parent path to be added to this FileLoadContext.
            relative_mode (ResolveRelativeMode): The relative mode.
        """
        self._path_resolver.push_new_parent(parent_path, relative_mode)

    def pop_last_parent(self) -> None:
        """Pop the last added parent off this FileLoadContext."""
        self._path_resolver.pop_last_parent()

    def resolve_casing(self, file_path: Path) -> Path:
        """Resolve the file casing for the provided file path.

        Args:
            file_path (Path): The file path to resolve the casing for.

        Returns:
            Path: The resolved file path.
        """
        if self.load_settings.resolve_casing:
            return self._file_casing_resolver.resolve(file_path)
        return file_path

    def convert_path_style(self, file_path: Path) -> Path:
        """Resolve the file path by converting it from its own file path style to the path style for the current operating system.

        Args:
            file_path (Path): The file path to convert to the OS path style.

        Returns:
            Path: The resolved file path.
        """

        if file_path.is_absolute():
            return file_path

        converted_file_path = self._file_path_style_converter.convert_to_os_style(
            file_path, self.load_settings.path_style
        )
        return Path(converted_file_path)


@contextmanager
def file_load_context():
    """Provide a FileLoadingContext. If none has been created in the context of
    this call stack yet, a new one will be created, which will be maintained
    until it goes out of scope.

    Yields:
        [FileLoadContext]: The file load context.
    """
    file_loading_context = context_file_loading.get(None)
    context_reset_token = None

    if not file_loading_context:
        file_loading_context = FileLoadContext()
        context_reset_token = context_file_loading.set(file_loading_context)

    try:
        yield file_loading_context
    finally:
        if context_reset_token is not None:
            context_file_loading.reset(context_reset_token)


def _should_traverse(model: BaseModel, _: FileLoadContext) -> bool:
    return model.is_intermediate_link()


def _should_execute(model: BaseModel, _: FileLoadContext) -> bool:
    return model.is_file_link()


PathOrStr = Union[Path, str]


class FileModel(BaseModel, ABC):
    """Base class to represent models with a file representation.

    It therefore always has a `filepath` and if it is given on
    initilization, it will parse that file. The filepath can be
    relative, in which case the paths are expected to be resolved
    relative to some root model. If a path is absolute, this path
    will always be used, regardless of a root parent.

    When saving a model, if the current filepath is relative, the
    last resolved absolute path will be used. If the model has just
    been read, the

    This class extends the `validate` option of Pydantic,
    so when when a Path is given to a field with type `FileModel`,
    it doesn't error, but actually initializes the `FileModel`.

    Attributes:
        filepath (Optional[Path]):
            The path of this FileModel. This path can be either absolute or relative.
            If it is a relative path, it is assumed to be resolved from some root
            model.
        save_location (Path):
            A readonly property corresponding with the (current) save location of this
            FileModel. If read from a file or after saving recursively or
            after calling synchronize_filepath, this value will be updated to its new
            state. If made from memory and filepath is not set, it will correspond with
            cwd / filename.extension
    """

    __slots__ = ["__weakref__"]
    # Use WeakValueDictionary to keep track of file paths with their respective parsed file models.
    _file_models_cache: WeakValueDictionary = WeakValueDictionary()
    filepath: Optional[Path] = None
    # Absolute anchor is used to resolve the save location when the filepath is relative.
    _absolute_anchor_path: Path = PrivateAttr(default_factory=Path.cwd)

    def __new__(cls, filepath: Optional[PathOrStr] = None, *args, **kwargs):
        """Create a new model.
        If the file at the provided file path was already parsed, this instance is returned.

        Args:
            filepath (Optional[PathOrStr], optional): The file path to the file. Defaults to None.

        Returns:
            FileModel: A file model.
        """
        filepath = FileModel._change_to_path(filepath)
        with file_load_context() as context:
            if (file_model := context.retrieve_model(filepath)) is not None:
                return file_model
            else:
                return super().__new__(cls)

    def __init__(
        self,
        filepath: Optional[PathOrStr] = None,
        resolve_casing: bool = False,
        recurse: bool = True,
        path_style: Optional[str] = None,
        *args,
        **kwargs,
    ):
        """Create a new FileModel from the given filepath.

        If no filepath is provided, the model is initialized as an empty
        model with default values.
        If the filepath is provided, it is read from disk.

        Args:
            filepath (Optional[PathOrStr], optional): The file path. Defaults to None.
            resolve_casing (bool, optional): Whether or not to resolve the file name references so that they match the case with what is on disk. Defaults to False.
            recurse (bool, optional): Whether or not to recursively load the model. Defaults to True.
            path_style (Optional[str], optional): Which path style is used in the loaded files. Defaults to the path style that matches the current operating system. Options: 'unix', 'windows'.

        Raises:
            ValueError: When an unsupported path style is passed.
        """
        if not filepath:
            super().__init__(*args, **kwargs)
            return

        filepath = FileModel._change_to_path(filepath)
        path_style = path_style_validator.validate(path_style)

        with file_load_context() as context:
            context.initialize_load_settings(recurse, resolve_casing, path_style)

            filepath = context.convert_path_style(filepath)

            if not FileModel._should_load_model(context):
                super().__init__(*args, **kwargs)
                self.filepath = filepath
                return

            self._absolute_anchor_path = context.get_current_parent()
            loading_path = context.resolve(filepath)
            loading_path = context.resolve_casing(loading_path)
            if context.load_settings.resolve_casing:
                filepath = self._get_updated_file_path(filepath, loading_path)

            logger.info(f"Loading data from {filepath}")

            data = self._load(loading_path)
            context.register_model(filepath, self)
            data["filepath"] = filepath
            kwargs.update(data)

            context.register_model(filepath, self)

            # Note: the relative mode needs to be obtained from the data directly
            # because self._relative_mode has not been resolved yet (this is done as
            # part of the __init__), however during the __init__ we need to already
            # have pushed the new parent. As such we cannot move this call later.
            relative_mode = self._get_relative_mode_from_data(data)
            context.push_new_parent(filepath.parent, relative_mode)

            super().__init__(*args, **kwargs)
            self._post_init_load()

            context.pop_last_parent()

    @classmethod
    def _should_load_model(cls, context: FileLoadContext) -> bool:
        """Determines whether the file model should be loaded or not.
        A file model should be loaded when either all models should be loaded recursively,
        or when no file model has been loaded yet.

        Returns:
            bool: Whether or not the file model should be loaded or not.
        """
        return context.load_settings.recurse or context.cache_is_empty()

    def _post_init_load(self) -> None:
        """
        _post_init_load provides a hook into the __init__ of the FileModel which can be
        used in subclasses for logic that requires the FileModel FileLoadContext.

        It is guaranteed to be called after the pydantic model is, with the FileLoadContext
        relative to this FileModel being loaded.
        """
        pass

    @property
    def _resolved_filepath(self) -> Optional[Path]:
        if self.filepath is None:
            return None

        with file_load_context() as context:
            return context.resolve(self.filepath)

    @property
    def save_location(self) -> Optional[Path]:
        """Get the current save location which will be used when calling `save()`

        This value can be None if the filepath is None and no name can be generated.

        Returns:
            Path: The location at which this model will be saved.
        """
        filepath = self.filepath or self._generate_name()

        if filepath is None:
            return None
        elif filepath.is_absolute():
            return filepath
        else:
            return self._absolute_anchor_path / filepath

    def is_file_link(self) -> bool:
        return True

    def _get_updated_file_path(self, file_path: Path, loading_path: Path) -> Path:
        """Update the file path with the resolved casing from the loading path.
        Logs an information message if a file path is updated.

        For example, given:
            file_path = "To/A/File.txt"
            loading_path = "D:/path/to/a/file.txt"

        Then the result will be: "to/a/file.txt"

        Args:
            file_path (Path): The file path.
            loading_path (Path): The resolved loading path.

        Returns:
            Path: The updated file path.
        """

        updated_file_parts = loading_path.parts[-len(file_path.parts) :]
        updated_file_path = Path(*updated_file_parts)

        if str(updated_file_path) != str(file_path):
            logger.info(
                f"Updating file reference from {file_path.name} to {updated_file_path}"
            )

        return updated_file_path

    @classmethod
    def validate(cls: Type["FileModel"], value: Any):
        # Enable initialization with a Path.
        if isinstance(value, (Path, str)):
            # Pydantic Model init requires a dict
            value = {"filepath": Path(value)}
        return super().validate(value)

    def save(
        self,
        filepath: Optional[Path] = None,
        recurse: bool = False,
        path_style: Optional[str] = None,
    ) -> None:
        """Save the model to disk.

        If recurse is set to True, all of the child FileModels will be saved as well.
        Relative child models are stored relative to this Model, according to the
        model file hierarchy specified with the respective filepaths.
        Absolute paths will be written to their respective locations. Note that this
        will overwrite any existing files that are stored in this location.

        Note that if recurse is set to True, the save_location properties of the
        children are updated to their respective new locations.

        If filepath it is specified, the filepath of this FileModel is set to the
        specified path before the save operation is executed. If none is specified
        it will use the current filepath.

        If the used filepath is relative, it will be stored at the current
        save_location. If you only want to save a child model of some root model, it is
        recommended to first call synchronize_filepaths on the root model, to ensure
        the child model's save_location is correctly determined.

        Args:
            filepath (Optional[Path], optional):
                The file path at which this model is saved. If None is specified
                it defaults to the filepath currently stored in the filemodel.
                Defaults to None.
            recurse (bool, optional):
                Whether to save all children of this FileModel (when set to True),
                or only save this model (when set to False). Defaults to False.
            path_style (Optional[str], optional):
                With which file path style to save the model. File references will
                be written with the specified path style. Defaults to the path style
                used by the current operating system. Options: 'unix', 'windows'.

        Raises:
            ValueError: When an unsupported path style is passed.
        """
        if filepath is not None:
            self.filepath = filepath

        path_style = path_style_validator.validate(path_style)
        save_settings = ModelSaveSettings(path_style=path_style)

        # Handle save
        with file_load_context() as context:
            context.push_new_parent(self._absolute_anchor_path, self._relative_mode)

            if recurse:
                self._save_tree(context, save_settings)
            else:
                self._save_instance(save_settings)

    def _save_instance(self, save_settings: ModelSaveSettings) -> None:
        if self.filepath is None:
            self.filepath = self._generate_name()
        self._save(save_settings)

    def _save_tree(
        self, context: FileLoadContext, save_settings: ModelSaveSettings
    ) -> None:
        # Ensure all names are generated prior to saving
        def execute_generate_name(
            model: BaseModel, acc: FileLoadContext
        ) -> FileLoadContext:
            if isinstance(model, FileModel) and model.filepath is None:
                model.filepath = model._generate_name()
            return acc

        name_traverser = ModelTreeTraverser[FileLoadContext](
            should_traverse=_should_traverse,
            should_execute=_should_execute,
            post_traverse_func=execute_generate_name,
        )

        name_traverser.traverse(self, context)

        def save_pre(model: BaseModel, acc: FileLoadContext) -> FileLoadContext:
            if isinstance(model, FileModel):
                acc.push_new_parent(model.filepath.parent, model._relative_mode)  # type: ignore[arg-type]
            return acc

        def save_post(model: BaseModel, acc: FileLoadContext) -> FileLoadContext:
            if isinstance(model, FileModel):
                acc.pop_last_parent()
                model._absolute_anchor_path = acc.get_current_parent()
                model._save(save_settings)
            return acc

        save_traverser = ModelTreeTraverser[FileLoadContext](
            should_traverse=_should_traverse,
            should_execute=_should_execute,
            pre_traverse_func=save_pre,
            post_traverse_func=save_post,
        )
        save_traverser.traverse(self, context)

    def synchronize_filepaths(self) -> None:
        """Synchronize the save_location properties of all child models respective to
        this FileModel's save_location.
        """

        def sync_pre(model: BaseModel, acc: FileLoadContext) -> FileLoadContext:
            if isinstance(model, FileModel):
                acc.push_new_parent(model.filepath.parent, model._relative_mode)  # type: ignore[arg-type]
            return acc

        def sync_post(model: BaseModel, acc: FileLoadContext) -> FileLoadContext:
            if isinstance(model, FileModel):
                acc.pop_last_parent()
                model._absolute_anchor_path = acc.get_current_parent()
            return acc

        traverser = ModelTreeTraverser[FileLoadContext](
            should_traverse=_should_traverse,
            should_execute=_should_execute,
            pre_traverse_func=sync_pre,
            post_traverse_func=sync_post,
        )

        with file_load_context() as context:
            context.push_new_parent(self._absolute_anchor_path, self._relative_mode)
            traverser.traverse(self, context)

    @property
    def _relative_mode(self) -> ResolveRelativeMode:
        """Get the ResolveRelativeMode of this FileModel.

        Returns:
            ResolveRelativeMode: The ResolveRelativeMode of this FileModel
        """
        return ResolveRelativeMode.ToParent

    @classmethod
    def _get_relative_mode_from_data(cls, data: Dict[str, Any]) -> ResolveRelativeMode:
        """Gets the ResolveRelativeMode of this FileModel based on the provided data.

        Note that by default, data is not used, and FileModels are always relative to
        the parent. In exceptional cases, the relative mode can be dependent on the
        data (i.e. the unvalidated/parsed dictionary fed into the pydantic basemodel).
        As such the data is provided for such classes where the relative mode is
        dependent on the state (e.g. the [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]).

        Args:
            data (Dict[str, Any]):
                The unvalidated/parsed data which is fed to the pydantic base model,
                used to determine the ResolveRelativeMode.

        Returns:
            ResolveRelativeMode: The ResolveRelativeMode of this FileModel
        """
        return ResolveRelativeMode.ToParent

    @abstractclassmethod
    def _generate_name(cls) -> Optional[Path]:
        """Generate a (default) name for this FileModel.

        Note that if _generate_name in theory can return a None value,
        if this is possible in the specific implementation, _save should
        be able to handle filepaths set to None.

        Returns:
            Optional[Path]:
                a relative path with the default name of the model.
        """
        raise NotImplementedError()

    @abstractmethod
    def _save(self, save_settings: ModelSaveSettings) -> None:
        """Save this instance to disk.

        This method needs to be implemented by any class deriving from
        FileModel, and is used in both the _save_instance and _save_tree
        methods.

        Args:
            save_settings (ModelSaveSettings): The model save settings.
        """
        raise NotImplementedError()

    @abstractmethod
    def _load(self, filepath: Path) -> Dict:
        """Load the data at filepath and returns it as a dictionary.

        If a derived FileModel does not load data from disk, this should
        return an empty dictionary.

        Args:
            filepath (Path): Path to the data to load.

        Returns:
            Dict: The data stored at filepath
        """
        raise NotImplementedError()

    def __str__(self) -> str:
        return str(self.filepath if self.filepath else "")

    @staticmethod
    def _change_to_path(filepath):
        if filepath is None:
            return filepath
        elif isinstance(filepath, Path):
            return filepath
        else:
            return Path(filepath)

    @validator("filepath")
    def _conform_filepath_to_pathlib(cls, value):
        return FileModel._change_to_path(value)


class SerializerConfig(BaseModel, ABC):
    """Class that holds the configuration settings for serialization."""

    float_format: str = ""
    """str: The string format that will be used for float serialization. If empty, the original number will be serialized. Defaults to an empty string.
        
        Examples:
            Input value = 123.456

            Format    | Output          | Description
            -------------------------------------------------------------------------------------------------------------------------------------
            ".0f"     | 123             | Format float with 0 decimal places.
            "f"       | 123.456000      | Format float with default (=6) decimal places.
            ".2f"     | 123.46          | Format float with 2 decimal places.
            "+.1f"    | +123.5          | Format float with 1 decimal place with a + or  sign.
            "e"       | 1.234560e+02    | Format scientific notation with the letter 'e' with default (=6) decimal places.
            "E"       | 1.234560E+02    | Format scientific notation with the letter 'E' with default (=6) decimal places.
            ".3e"     | 1.235e+02       | Format scientific notation with the letter 'e' with 3 decimal places.
            "<15"     | 123.456         | Left aligned in space with width 15
            "^15.0f"  |       123       | Center aligned in space with width 15 with 0 decimal places.
            ">15.1e"  |         1.2e+02 | Right aligned in space with width 15 with scientific notation with 1 decimal place.
            "*>15.1f" | **********123.5 | Right aligned in space with width 15 with 1 decimal place and fill empty space with *
            "%"       | 12345.600000%   | Format percentage with default (=6) decimal places.     
            ".3%"     | 12345.600%      | Format percentage with 3 decimal places.

            More information: https://docs.python.org/3/library/string.html#format-specification-mini-language
        """


class ParsableFileModel(FileModel):
    """ParsableFileModel defines a FileModel which can be parsed
    and serialized with a serializer .

    Each ParsableFileModel has a default _filename and _ext,
    which are used to generate the file name of any instance where
    the filepath is not (yet) set.

    Children of the ParsableFileModel are expected to implement a
    serializer function which takes a Path and Dict and writes the
    ParsableFileModel to disk, and a parser function which takes
    a Path and outputs a Dict.

    If more complicated solutions are required, a ParsableFileModel
    child can also opt to overwrite the _serialize and _parse methods,
    to skip the _get_serializer and _get_parser methods respectively.
    """

    serializer_config: SerializerConfig = SerializerConfig()

    def _load(self, filepath: Path) -> Dict:
        # TODO Make this lazy in some cases so it doesn't become slow
        if filepath.is_file():
            return self._parse(filepath)
        else:
            raise ValueError(f"File: `{filepath}` not found, skipped parsing.")

    def _save(self, save_settings: ModelSaveSettings) -> None:
        """Save the data of this FileModel.

        _save provides a hook for child models to overwrite the save behaviour as
        called during the tree traversal.

        Args:
            save_settings (ModelSaveSettings): The model save settings.
        """
        self._serialize(self.dict(), save_settings)

    def _serialize(self, data: dict, save_settings: ModelSaveSettings) -> None:
        """Serializes the data to file. Should not be called directly, only through `_save`.

        Args:
            save_settings (ModelSaveSettings): The model save settings.
        """
        path = self._resolved_filepath
        if path is None:
            # TODO: Do we need to add a warning / exception here
            return

        path.parent.mkdir(parents=True, exist_ok=True)
        self._get_serializer()(path, data, self.serializer_config, save_settings)

    def dict(self, *args, **kwargs):
        kwargs["exclude"] = self._exclude_fields()
        return super().dict(*args, **kwargs)

    @classmethod
    def _exclude_fields(cls) -> Set[str]:
        """A set containing the field names that should not be serialized."""
        return {"filepath", "serializer_config"}

    @classmethod
    def _parse(cls, path: Path) -> Dict:
        return cls._get_parser()(path)

    @classmethod
    def _generate_name(cls) -> Path:
        name, ext = cls._filename(), cls._ext()
        return Path(f"{name}{ext}")

    @abstractclassmethod
    def _filename(cls) -> str:
        return "test"

    @abstractclassmethod
    def _ext(cls) -> str:
        return ".test"

    @abstractclassmethod
    def _get_serializer(
        cls,
    ) -> Callable[[Path, Dict, SerializerConfig, ModelSaveSettings], None]:
        return DummySerializer.serialize

    @abstractclassmethod
    def _get_parser(cls) -> Callable[[Path], Dict]:
        return DummmyParser.parse

    def _get_identifier(self, data: dict) -> Optional[str]:
        filepath = data.get("filepath")
        if filepath:
            return filepath.name
        return None


class DiskOnlyFileModel(FileModel):
    """DiskOnlyFileModel provides a stub implementation for file based
    models which are not explicitly implemented within hydrolib.core.

    It implements the FileModel with a void parser and serializer, and a
    save method which copies the file associated with the FileModel
    to a new location if it exists.

    We further explicitly assume that when the filepath is None, no
    file will be written.

    Actual file model implementations *should not* inherit from the
    DiskOnlyFileModel and instead inherit directly from FileModel.
    """

    _source_file_path: Optional[Path] = PrivateAttr(default=None)

    def _post_init_load(self) -> None:
        # After initialisation we retrieve the _resolved_filepath
        # this should correspond with the actual absolute path of the
        # underlying file. Only after saving this path will be updated.
        super()._post_init_load()
        self._source_file_path = self._resolved_filepath

    def _load(self, filepath: Path) -> Dict:
        # We de not load any additional data, as such we return an empty dict.
        return dict()

    def _save(self, save_settings: ModelSaveSettings) -> None:
        # The target_file_path contains the new path to write to, while the
        # _source_file_path contains the original data. If these are not the
        # same we copy the file and update the underlying source path.
        target_file_path = self._resolved_filepath
        if self._can_copy_to(target_file_path):
            target_file_path.parent.mkdir(parents=True, exist_ok=True)  # type: ignore[arg-type]
            shutil.copy(self._source_file_path, target_file_path)  # type: ignore[arg-type]
        self._source_file_path = target_file_path

    def _can_copy_to(self, target_file_path: Optional[Path]) -> bool:
        return (
            self._source_file_path is not None
            and target_file_path is not None
            and self._source_file_path != target_file_path
            and self._source_file_path.exists()
            and self._source_file_path.is_file()
        )

    @classmethod
    def _generate_name(cls) -> Optional[Path]:
        # There is no common name for DiskOnlyFileModel, instead we
        # do not generate names and skip None filepaths.
        return None

    def is_intermediate_link(self) -> bool:
        # If the filepath is not None, there is an underlying file, and as such we need
        # to traverse it.
        return self.filepath is not None


def validator_set_default_disk_only_file_model_when_none() -> classmethod:
    """Validator to ensure a default empty DiskOnlyFileModel is created
    when the corresponding field is initialized with None.

    Returns:
        classmethod: Validator to adjust None values to empty DiskOnlyFileModel objects
    """

    def adjust_none(v: Any, field: ModelField) -> Any:
        if field.type_ is DiskOnlyFileModel and v is None:
            return {"filepath": None}
        return v

    return validator("*", allow_reuse=True, pre=True)(adjust_none)


class PathStyleValidator:
    """Class to take care of path style validation."""

    _os_path_style = get_path_style_for_current_operating_system()

    def validate(self, path_style: Optional[str]) -> PathStyle:
        """Validates the path style as string on whether it is a supported path style.
        If it is a valid path style the path style enum value will be return as a result.

        Args:
            path_style (Optional[str]): The path style as string value.

        Returns:
            PathStyle: The converted PathStyle object.

        Raises:
            ValueError: When an unsupported path style is passed.
        """
        if path_style is None:
            return self._os_path_style

        supported_path_styles = list(PathStyle)
        if path_style in supported_path_styles:
            return PathStyle(path_style)

        supported_path_style_str = ", ".join(([x.value for x in supported_path_styles]))
        raise ValueError(
            f"Path style '{path_style}' not supported. Supported path styles: {supported_path_style_str}"
        )


path_style_validator = PathStyleValidator()
