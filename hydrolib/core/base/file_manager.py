"""File Manager Module."""

from contextlib import contextmanager
from contextvars import ContextVar
from enum import IntEnum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from hydrolib.core.base.utils import (
    FileChecksumCalculator,
    FilePathStyleConverter,
    OperatingSystem,
    PathStyle,
    get_operating_system,
    get_path_style_for_current_operating_system,
    str_is_empty_or_none,
)

PathOrStr = Union[Path, str]
# We use ContextVars to keep a reference to the folder
# we're currently parsing files in. In the future
# we could move to https://github.com/samuelcolvin/pydantic/issues/1549
context_file_loading: ContextVar["FileLoadContext"] = ContextVar("file_loading")


class ResolveRelativeMode(IntEnum):
    """ResolveRelativeMode.

    ResolveRelativeMode defines the possible resolve modes used within the
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
        """Pop the last added parent from this FilePathResolver.

        If there are currently no parents defined, nothing will happen.
        """
        if not self._parents:
            return

        _, relative_mode = self._parents.pop()

        if relative_mode == ResolveRelativeMode.ToAnchor:
            self._anchors.pop()


class PathStyleValidator:
    """Class to take care of path style validation."""

    _os_path_style = get_path_style_for_current_operating_system()

    def validate(self, path_style: Optional[str]) -> PathStyle:
        """Validate.

        Validates the path style as string on whether it is a supported path style.
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


class CachedFileModel:
    """CachedFileModel provides a simple structure to keep the Filemodel and checksum together."""

    _model: "FileModel"
    _checksum: str

    @property
    def model(self) -> "FileModel":
        """FileModel."""
        return self._model

    @property
    def checksum(self) -> str:
        """Checksum of the file the filemodel is based on."""
        return self._checksum

    def __init__(self, model: "FileModel", checksum: str) -> None:
        """Create a new empty CachedFileModel.

        Args:
            model (FileModel): filemodel to cache.
            checksum (str): checksum of the file.
        """
        self._model = model
        self._checksum = checksum


class FileModelCache:
    """FileModelCache provides a simple structure to register and retrieve FileModel objects."""

    def __init__(self):
        """Create a new empty FileModelCache."""
        self._cache_dict: Dict[Path, CachedFileModel] = {}

    def retrieve_model(self, path: Path) -> Optional["FileModel"]:
        """Retrieve model.

        Retrieve the model associated with the (absolute) path if
        it has been registered before, otherwise return None.

        Returns:
            [Optional[FileModel]]:
                The FileModel associated with the Path if it has been registered
                before, otherwise None.
        """
        cached_file_model = self._cache_dict.get(path, None)
        if cached_file_model is None:
            return None
        return cached_file_model.model

    def register_model(self, path: Path, model: "FileModel") -> None:
        """Register the model with the specified path in this FileModelCache.

        Args:
            path (Path): The path to associate the model with.
            model (FileModel): The model to be associated with the path.
        """
        checksum = self._get_checksum(path)
        self._cache_dict[path] = CachedFileModel(model, checksum)

    def is_empty(self) -> bool:
        """Whether or not this file model cache is empty.

        Returns:
            bool: Whether or not the cache is empty.
        """
        return not any(self._cache_dict)

    def _exists(self, path: Path) -> bool:
        """Whether or not the filepath is in the cache.

        Args:
            path (Path): The path to verify if it is already added in the cache.

        Returns:
            bool: Whether or not the path is in the cache.
        """
        return path in self._cache_dict

    def has_changed(self, path: Path) -> bool:
        """Whether or not the file in the filepath has changed from the cache.

        Args:
            path (Path): The path to verify verify against.

        Returns:
            bool: Whether or the file has changed.
            True when the file has changed.
            True when the file does not exist in caching reference.
            False when the file has not changed.
        """
        if not self._exists(path):
            return True

        checksum = self._get_checksum(path)
        return checksum != self._cache_dict.get(path).checksum

    def _get_checksum(self, path: Path) -> Optional[str]:
        return FileChecksumCalculator.calculate_checksum(path)


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
        return path

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


class FileLoadContext:
    """FileLoadContext.

    FileLoadContext provides the context necessary to resolve paths
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
        """Push a new parent_path with the given relative_mode on this FileLoadContext.

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
        """convert_path_style.

        Resolve the file path by converting it from its own file path style to the path style for the current operating system.

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

    def is_content_changed(self, path: Path) -> bool:
        """Verify if the path is already known and if the content have changed.

        Relative paths will be resolved based on the current state of the
        FileLoadContext.

        Args:
            path (Path): The relative path from which the model was loaded.
            model (FileModel): The loaded model.

        Returns:
            True when the content from the path on the location has been changed.
            False when the content from the path is not priorly cached.
            False when the content from the path on the location has not been changed.
        """
        absolute_path = self._path_resolver.resolve(path)
        return self._cache.has_changed(absolute_path)


@contextmanager
def file_load_context():
    """file_load_context.

    Provide a FileLoadingContext. If none has been created in the context of
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


path_style_validator = PathStyleValidator()
