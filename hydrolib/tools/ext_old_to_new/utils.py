from pathlib import Path
from typing import Type

from hydrolib.core.basemodel import FileModel, PathOrStr


def construct_filemodel_new_or_existing(
    model_class: Type[FileModel], filepath: PathOrStr, *args, **kwargs
) -> FileModel:
    """Construct a new instance of a FileModel subclass, either loading an
    existing model file, or starting a blank one.

    If the given filepath exists, it will be loaded, as if the constructor
    was directly called. If it does not exist, the blank model instance
    will only have its filepath attribute set, e.g., for future saving.

    Args:
        model_class (type[FileModel]): The FileModel subclass to construct or update.
        filepath (PathOrStr): The filepath to use for the new or existing model input.
        *args: Additional positional arguments to pass to the ModelClass constructor
        **kwargs: Additional keywords arguments to pass to the ModelClass constructor
    """
    if Path(filepath).is_file():
        model = model_class(filepath=filepath, *args, **kwargs)
    else:
        model = model_class(*args, **kwargs)
        model.filepath = filepath

    return model


def backup_file(filepath: PathOrStr, backup: bool = True) -> None:
    """Create a backup of the given file by copying it to a new file with a
    '.bak' extension.

    Args:
        filepath (PathOrStr): The path to the file to back up.
        backup (bool): Whether to create a backup of the file or not.
    """
    if not backup:
        return

    source = Path(filepath)
    if source.is_file():
        backup = source.with_suffix(".bak")
        source.replace(backup)


def construct_filepath_with_postfix(filepath: PathOrStr, postfix: str) -> Path:
    """Construct a new filepath by adding a postfix to the existing
    filepath, still keeping the original file suffix.
    For example, 'file.txt' with postfix '_new' will become 'file_new.txt'.

    Args:
        filepath (PathOrStr): The path to the file.
        postfix (str): The postfix to add to the filename.

    Returns:
        Path: The new filepath with the postfix included.

    """
    file_as_path = Path(filepath)
    return file_as_path.with_stem(file_as_path.stem + postfix)
