"""
Here we define our Pydantic `BaseModel` with custom settings,
as well as a `FileModel` that inherits from a `BaseModel` but
also represents a file on disk.

"""
import logging
from abc import ABC, abstractclassmethod
from contextlib import contextmanager
from contextvars import ContextVar
from enum import IntEnum
from pathlib import Path
from typing import Any, Callable, Dict, Generic, List, Optional, Tuple, Type, TypeVar
from warnings import warn
from weakref import WeakValueDictionary

from pydantic import BaseModel as PydanticBaseModel
from pydantic.error_wrappers import ErrorWrapper, ValidationError
from pydantic.fields import PrivateAttr

from hydrolib.core.io.base import DummmyParser, DummySerializer
from hydrolib.core.utils import to_key

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
        """Initializes a BaseModel with the provided data.

        Raises:
            ValidationError: A validation error when the data is invalid.
        """
        try:
            super().__init__(**data)
        except ValidationError as e:
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
        """Gets the identifier for this model.

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

    Args:
        Generic ([type]): The type of Accumulator to be used.
    """

    def __init__(
        self,
        should_traverse: Optional[Callable[[BaseModel, TAcc], bool]] = None,
        should_execute: Optional[Callable[[BaseModel, TAcc], bool]] = None,
        pre_traverse_func: Callable[[BaseModel, TAcc], TAcc] = None,
        post_traverse_func: Callable[[BaseModel, TAcc], TAcc] = None,
    ):
        """Creates a new ModelTreeTraverser with the given functions.

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


class FilePathResolver:
    """FilePathResolver is responsible for resolving relative paths.

    The current state to which paths are resolved can be altered by
    pushing a new parent path to the FilePathResolver, or removing the
    latest added parent path from the FilePathResolver
    """

    def __init__(self) -> None:
        """Creates a new empty FilePathResolver."""
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
        """Creates a new empty FileModelCache."""
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


class FileLoadContext:
    """FileLoadContext provides the context necessary to resolve paths
    during the init of a FileModel, as well as ensure the relevant models
    are only read once.
    """

    def __init__(self) -> None:
        """Creates a new empty FileLoadContext."""
        self._path_resolver = FilePathResolver()
        self._cache = FileModelCache()

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


@contextmanager
def file_load_context():
    """Provides a FileLoadingContext. If none has been created in the context of
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

    def __new__(cls, filepath: Optional[Path] = None, *args, **kwargs):
        """Creates a new model.
        If the file at the provided file path was already parsed, this instance is returned.

        Args:
            filepath (Optional[Path], optional): The file path to the file. Defaults to None.

        Returns:
            FileModel: A file model.
        """
        with file_load_context() as context:
            if (file_model := context.retrieve_model(filepath)) is not None:
                return file_model
            else:
                return super().__new__(cls)

    def __init__(self, filepath: Optional[Path] = None, *args, **kwargs):
        """Creates a new FileModel from the given filepath.

        If no filepath is provided, the model is initialized as an empty
        model with default values.
        If the filepath is provided, it is read from disk.
        """
        if not filepath:
            super().__init__(*args, **kwargs)
            return

        with file_load_context() as context:
            context.register_model(filepath, self)

            self._absolute_anchor_path = context.get_current_parent()
            loading_path = context.resolve(filepath)

            context.push_new_parent(filepath.parent, self._relative_mode)
            logger.info(f"Loading data from {filepath}")

            data = self._load(loading_path)
            data["filepath"] = filepath
            kwargs.update(data)

            super().__init__(*args, **kwargs)
            self._post_init_load()

            context.pop_last_parent()

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
    def save_location(self) -> Path:
        """Gets the current save location which will be used when calling `save()`

        Returns:
            Path: The location at which this model will be saved.
        """
        filepath = self.filepath or self._generate_name()

        if filepath.is_absolute():
            return filepath
        else:
            return self._absolute_anchor_path / filepath

    def is_file_link(self) -> bool:
        return True

    @classmethod
    def validate(cls: Type["FileModel"], value: Any):
        # Enable initialization with a Path.
        if isinstance(value, (Path, str)):
            # Pydantic Model init requires a dict
            value = {"filepath": Path(value)}
        return super().validate(value)

    def _load(self, filepath: Path) -> Dict:
        # TODO Make this lazy in some cases
        # so it doesn't become slow
        if filepath.is_file():
            return self._parse(filepath)
        else:
            warn(f"File: `{filepath}` not found, skipped parsing.")
            return {}

    def save(self, filepath: Optional[Path] = None, recurse: bool = False) -> None:
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
        """
        if filepath is not None:
            self.filepath = filepath

        # Handle save
        with file_load_context() as context:
            context.push_new_parent(self._absolute_anchor_path, self._relative_mode)

            if recurse:
                self._save_tree(context)
            else:
                self._save_instance()

    def _save_instance(self) -> None:
        if self.filepath is None:
            self.filepath = self._generate_name()

        self._save()

    def _save_tree(self, context: FileLoadContext) -> None:
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
                model._save()
            return acc

        save_traverser = ModelTreeTraverser[FileLoadContext](
            should_traverse=_should_traverse,
            should_execute=_should_execute,
            pre_traverse_func=save_pre,
            post_traverse_func=save_post,
        )
        save_traverser.traverse(self, context)

    def _save(self) -> None:
        """Save the data of this FileModel.

        _save provides a hook for child models to overwrite the save behaviour as
        called during the tree traversal.
        """
        self._serialize(self.dict())

    def _serialize(self, data: dict) -> None:
        path = self._resolved_filepath
        if path is None:
            # TODO: Do we need to add a warning / exception here
            return

        path.parent.mkdir(parents=True, exist_ok=True)
        self._get_serializer()(path, data)

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

    def _get_identifier(self, data: dict) -> Optional[str]:
        filepath = data.get("filepath")
        if filepath:
            return filepath.name
        return None

    @property
    def _relative_mode(self) -> ResolveRelativeMode:
        """Gets the ResolveRelativeMode of this FileModel.

        Returns:
            ResolveRelativeMode: The ResolveRelativ
        """
        return ResolveRelativeMode.ToParent
