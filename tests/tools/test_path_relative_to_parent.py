import ntpath

from pathlib import PureWindowsPath
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from hydrolib.core.dflowfm.extold.models import ExtOldForcing
from hydrolib.tools.extforce_convert import utils as converter_utils
from hydrolib.tools.extforce_convert.mdu_parser import MDUParser
from hydrolib.tools.extforce_convert.utils import path_relative_to_parent

MAPPED_DRIVE = "P:"
UNC_SHARE = r"\\storage013.directory.intra\dflowfm"


class _MappedDrivePath(PureWindowsPath):
    """Windows path whose `resolve()` mimics a mapped network drive.

    On Windows, `Path.resolve()` rewrites a mapped drive letter (`P:`) to the UNC
    share it points to (`\\\\server\\share`) and normalizes `..` segments. This
    class reproduces that deterministically on any OS, without a real network share.
    """

    def resolve(self) -> "_MappedDrivePath":
        normalized = ntpath.normpath(str(self))
        if normalized.upper().startswith(MAPPED_DRIVE + "\\"):
            normalized = UNC_SHARE + normalized[len(MAPPED_DRIVE) :]
        return type(self)(normalized)


@pytest.fixture
def windows_os_path(monkeypatch):
    """Use Windows path semantics in `utils` regardless of the OS running the tests."""
    monkeypatch.setattr(converter_utils, "os", SimpleNamespace(path=ntpath))


@pytest.fixture
def relative_to_parent_mdu() -> MagicMock:
    mdu_parser = MagicMock(spec=MDUParser)
    mdu_parser.is_relative_to_parent = True
    return mdu_parser


def _forcing(filename: str) -> ExtOldForcing:
    return ExtOldForcing(
        quantity="initialsalinity",
        filename=filename,
        filetype=7,
        method=5,
        operand="override",
    )


@pytest.mark.usefixtures("windows_os_path")
class TestPathRelativeToParentMountNormalization:

    def test_unnormalized_mixed_mount_paths_reproduce_reported_error(self):
        """Guard: the path forms used below are the ones that triggered the bug."""
        ext_old_path = _MappedDrivePath(rf"{MAPPED_DRIVE}\project\model\old.ext")
        inifile_path = _MappedDrivePath(
            rf"{UNC_SHARE}\project\model\fields\initialFields.ini"
        )
        forcing = _forcing("../initial/salinity.xyz")

        with pytest.raises(ValueError, match="mount"):
            ntpath.relpath(
                ext_old_path.parent / forcing.filename.filepath, inifile_path.parent
            )

    @pytest.mark.parametrize(
        "ext_old_path, inifile_path",
        [
            pytest.param(
                rf"{MAPPED_DRIVE}\project\model\old.ext",
                rf"{UNC_SHARE}\project\model\fields\initialFields.ini",
                id="ext-on-mapped-drive_inifile-on-unc",
            ),
            pytest.param(
                rf"{UNC_SHARE}\project\model\old.ext",
                rf"{MAPPED_DRIVE}\project\model\fields\initialFields.ini",
                id="ext-on-unc_inifile-on-mapped-drive",
            ),
        ],
    )
    def test_mapped_drive_and_unc_paths_give_relative_path(
        self, ext_old_path: str, inifile_path: str, relative_to_parent_mdu
    ):
        """Regression: with `pathsRelativeToParent = 1`, one path addressed through a
        mapped drive (`P:`) and the other already resolved to its UNC form (as done by
        `MDUParser.get_inifield_file`) used to raise
        `ValueError: path is on mount 'P:', start on mount '\\\\storage013...'`.
        """
        forcing = _forcing("../initial/salinity.xyz")

        result = path_relative_to_parent(
            forcing,
            _MappedDrivePath(inifile_path),
            _MappedDrivePath(ext_old_path),
            relative_to_parent_mdu,
        )

        assert PureWindowsPath(result) == PureWindowsPath(r"..\..\initial\salinity.xyz")



