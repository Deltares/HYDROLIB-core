from hydrolib.core.io.polyfile.components import PolyObject
from hydrolib.core.io.polyfile.serializer import write_polyfile
from hydrolib.core.io.polyfile.parser import read_polyfile
from hydrolib.core.basemodel import FileModel
from typing import Callable, Sequence


class PolyFile(FileModel):
    """Poly-file (.pol/.pli/.pliz) representation."""

    has_z_values: bool = False
    objects: Sequence[PolyObject] = []

    @classmethod
    def _ext(cls) -> str:
        return ".pli"

    @classmethod
    def _filename(cls) -> str:
        return "objects"

    @classmethod
    def _get_serializer(cls) -> Callable:
        return write_polyfile

    @classmethod
    def _get_parser(cls) -> Callable:
        return read_polyfile
