from pathlib import Path
from typing import Callable, Dict, Optional
import shutil

from pydantic import PrivateAttr
from hydrolib.core.basemodel import FileModel, file_load_context


class GenericFileModel(FileModel):
    """GenericFileModel provides a stub implementation for file based
    models which are not explicitly implemented within hydrolib.core.

    It implements the FileModel with a void parser and serializer, and a
    save method which copies the file associated with the FileModel
    to a new location if it exists.

    We further explicitly assume that when the filepath is None, no
    file will be written. In this case the save location filename
    will be set to "UNDEFINED". No files will be copied.

    Actual file model implementations *should not* inherit from the
    GenericFileModel and instead inherit directly from FileModel.
    """

    _source_file_path: Optional[Path] = PrivateAttr(default=None)

    def _post_init_load(self) -> None:
        # After initialisation we retrieve the _resolved_filepath
        # this should correspond with the actual absolute path of the
        # underlying file. Only after saving this path will be updated.
        super()._post_init_load()
        self._source_file_path = self._resolved_filepath

    def save(self, filepath: Optional[Path] = None, recurse: bool = False) -> None:
        if filepath is not None:
            self.filepath = filepath

        with file_load_context() as context:
            context.push_new_parent(self._absolute_anchor_path, self._relative_mode)

            # We do not have to handle recursion as the GenericFileModel cannot have
            # children.

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
    def _filename(cls) -> str:
        return "UNDEFINED"

    @classmethod
    def _ext(cls) -> str:
        return ""

    def _serialize(self, data: dict) -> None:
        # GenericFileModels do not serialize anything instead they are copied as part
        # of the save operation.
        pass

    @classmethod
    def _get_serializer(cls) -> Callable[[Path, Dict], None]:
        # GenericFileModels do not serialize anything instead they are copied as part
        # of the save operation.
        return lambda path, data: None

    @classmethod
    def _get_parser(cls) -> Callable[[Path], Dict]:
        # GenericFileModels do not parse anything instead they merely hold a parser.
        return lambda path: dict()

    def _load(self, filepath: Path) -> Dict:
        return dict()
