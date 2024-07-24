from pathlib import Path
from typing import Type

from hydrolib.core.basemodel import FileModel, PathOrStr


def construct_filemodel_new_or_existing(
    ModelClass: Type[FileModel], filepath: PathOrStr, *args, **kwargs
) -> FileModel:
    """Construct a new instance of a FileModel subclass, either loading an
    existing model file, or starting a blank one.

    If the given filepath exists, it will be loaded, as if the constructor
    was directly called. If it does not exist, the blank model instance
    will only have its filepath attribute set, e.g., for future saving.

    Args:
        ModelClass (type[FileModel]): The FileModel subclass to construct or update.
        filepath (PathOrStr): The filepath to use for the new or existing model input.
        *args: Additional positional arguments to pass to the ModelClass constructor
        **kwargs: Additional keywords arguments to pass to the ModelClass constructor
    """
    if Path(filepath).is_file():
        model = ModelClass(filepath=filepath, *args, **kwargs)
    else:
        model = ModelClass(*args, **kwargs)
        model.filepath = filepath

    return model
