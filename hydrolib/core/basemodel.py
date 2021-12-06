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
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
)
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
    FilePathResolver. These are dependent on the type of model and as such
    defined in (the subclasses of) the FileModel

    Options:
        ToParent:
            Relative paths should be resolved relative to their direct parent model.
        ToAnchor:
            All relative paths should be resolved relative to the specified regardless
            of subsequent parent model locations.
    """

    ToParent = 0
    ToAnchor = 1


# TODO: This should probably be moved to a separate file
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

    def _get_current_parent(self) -> Path:
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

        parent = self._get_current_parent()
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
        if relative_mode == ResolveRelativeMode.ToAnchor:
            self._anchors.append(parent_path)

        self._parents.append((self.resolve(parent_path), relative_mode))

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

    def save(self, folder: Optional[Path] = None) -> Path:
        """Save model and child models to their set filepaths.

        If a folder is given, for models with an unset filepath,
        we generate one based on the given `folder` and a default name.
        Otherwise we override the folder part of already set filepaths.
        This can thus be used to copy complete models.

        Args:
            folder: path to the folder where this FileModel will be stored
        """
        if self.filepath is None and folder is None:
            raise ValueError(
                "Either set the `filepath` on the model or pass a `folder` when saving."
            )

        # Handle export
        if folder is not None:
            self._apply_recurse(self._export.__name__, folder)
            return self.filepath  # type: ignore[arg-type]

        # Handle save
        with file_load_context() as context:
            self._save_tree(context)
            return self._resolved_filepath  # type: ignore[arg-type]

    def _export(self, folder: Path) -> None:
        filename = Path(self.filepath.name) if self.filepath else self._generate_name()
        self.filepath = folder / filename

        self._serialize(self.dict())

    def _save_tree(self, context: FileLoadContext) -> None:
        # Ensure all names are generated prior to saving
        def should_traverse(model: BaseModel, _: FileLoadContext) -> bool:
            return model.is_intermediate_link()

        def should_execute(model: BaseModel, _: FileLoadContext) -> bool:
            return model.is_file_link()

        def execute_generate_name(
            model: BaseModel, acc: FileLoadContext
        ) -> FileLoadContext:
            if isinstance(model, FileModel) and model.filepath is None:
                model.filepath = model._generate_name()
            return acc

        name_traverser = ModelTreeTraverser[FileLoadContext](
            should_traverse=should_traverse,
            should_execute=should_execute,
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
                model._save()
            return acc

        save_traverser = ModelTreeTraverser[FileLoadContext](
            should_traverse=should_traverse,
            should_execute=should_execute,
            pre_traverse_func=save_pre,
            post_traverse_func=save_post,
        )
        save_traverser.traverse(self, context)

    def _save(self) -> None:
        """Save the data of this FileModel

        _save provides a hook for child models to overwrite the save behaviour as
        called during the tree traversal.
        """
        self._serialize(self.dict())

    def _serialize(self, data: dict) -> None:
        self._get_serializer()(self._resolved_filepath, data)

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
        return ResolveRelativeMode.ToParent
