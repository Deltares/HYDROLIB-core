import os
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import MagicMock, patch

import pytest

from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.base.utils import FilePathStyleConverter, PathStyle
from hydrolib.core.dflowfm.ext.models import (
    Boundary,
    ExtModel,
    Lateral,
    Meteo,
    SourceSink,
)
from hydrolib.core.dflowfm.extold.models import ExtOldModel
from hydrolib.core.dflowfm.inifield.models import (
    DataFileType,
    IniFieldModel,
    InitialField,
)
from hydrolib.core.dflowfm.structure.models import Structure, StructureModel
from hydrolib.tools.extforce_convert import main_converter
from hydrolib.tools.extforce_convert.main_converter import (
    ExternalForcingConverter,
    recursive_converter,
)


class TestExtOldToNewFromMDU:
    def test_wind_combi_uniform_curvi(self, capsys, input_files_dir: Path):
        """
        The mdu file in this test is read correctly with the `LegacyFMModel` class.
        """
        mdu_filename = (
            input_files_dir / "e02/f011_wind/c081_combi_uniform_curvi/windcase.mdu"
        )
        converter = ExternalForcingConverter.from_mdu(mdu_filename)
        converter.verbose = True
        ext_model, _, _ = converter.update()
        assert len(converter.extold_model.forcing) == 5

        # check the saved files
        converter.save()

        assert ext_model.filepath.exists()
        ext_model.filepath.unlink()
        # delete the mdu file (this is the updated one with the new external forcing file)
        mdu_filename.unlink()
        # check the mdu backup file
        assert mdu_filename.with_suffix(".mdu.bak").exists()
        # rename back the backup file
        mdu_filename.with_suffix(".mdu.bak").rename(mdu_filename)

    def test_extrapolate_slr(self, capsys, input_files_dir: Path):
        """
        - This test used mdu file with `Unknown keywords` so the reading of the mdu file using the `LegacyFMModel`
        fails.
        - Since the `LegacyFMModel` class is not created, the converter will read only the [physics] and [time] section
        """
        main_converter._verbose = True
        mdu_filename = (
            input_files_dir
            / "e02/f006_external_forcing/c011_extrapolate_slr/slrextrapol.mdu"
        )
        converter = ExternalForcingConverter.from_mdu(mdu_filename)
        ext_model, _, _ = converter.update()
        assert isinstance(ext_model, ExtModel)
        assert len(ext_model.meteo) == 1
        # check the saved files
        converter.save()

        assert ext_model.filepath.exists()
        ext_model.filepath.unlink()
        # delete the mdu file (this is the updated one with the new external forcing file)
        mdu_filename.unlink()
        # check the mdu backup file
        assert mdu_filename.with_suffix(".mdu.bak").exists()
        # rename back the backup file
        mdu_filename.with_suffix(".mdu.bak").rename(mdu_filename)

    def test_recursive(self, capsys, input_files_dir: Path):
        main_converter._verbose = True
        path = input_files_dir / "e02/f006_external_forcing"
        with patch(
            "hydrolib.tools.extforce_convert.main_converter.ExternalForcingConverter.save",
            return_value=None,
        ):
            recursive_converter(path, suppress_errors=True)

    @pytest.mark.parametrize(
        "mdu_file_content, input_files, expected",
        [
            (
                {
                    "external_forcing": {
                        "extforcefile": "old_forcing.ext",
                        "extforcefilenew": "new_forcing.ext",
                    },
                    "geometry": {
                        "inifieldfile": "initial_conditions.ini",
                        "structurefile": "structures.ini",
                    },
                },
                (None, None, None),
                ("new_forcing.ext", "initial_conditions.ini", "structures.ini"),
            ),
            (
                {
                    "external_forcing": {
                        "extforcefile": "old_forcing.ext",
                    },
                    "geometry": {
                        "inifieldfile": "initial_conditions.ini",
                        "structurefile": "structures.ini",
                    },
                },
                ("user_provided.ext", None, None),
                ("user_provided.ext", "initial_conditions.ini", "structures.ini"),
            ),
            (
                {
                    "external_forcing": {
                        "extforcefile": "old_forcing.ext",
                        "extforcefilenew": "new_forcing.ext",
                    },
                    "geometry": {
                        "structurefile": "structures.ini",
                    },
                },
                (None, "user_initial_conditions.ini", None),
                ("new_forcing.ext", "user_initial_conditions.ini", "structures.ini"),
            ),
            (
                {
                    "external_forcing": {
                        "extforcefile": "old_forcing.ext",
                        "extforcefilenew": "new_forcing.ext",
                    },
                    "geometry": {
                        "inifieldfile": "initial_conditions.ini",
                    },
                },
                (None, None, "user_structures.ini"),
                ("new_forcing.ext", "initial_conditions.ini", "user_structures.ini"),
            ),
            (
                {
                    "external_forcing": {
                        "extforcefile": "old_forcing.ext",
                        "extforcefilenew": None,
                    },
                    "geometry": {
                        "inifieldfile": Path("initial_conditions.ini"),
                        "structurefile": Path("structures.ini"),
                    },
                },
                (None, None, None),
                ("old_forcing-new.ext", "initial_conditions.ini", "structures.ini"),
            ),
        ],
        ids=[
            "Valid MDU file with all fields present",
            "MDU file missing extforcefilenew, user provides ext_file",
            "MDU file missing inifieldfile, user provides inifield_file",
            "MDU file missing structurefile, user provides structure_file",
            "MDU file empty extforcefilenew",
        ],
    )
    def test_from_mdu(
        self,
        mdu_file_content: Dict[str, Any],
        input_files: Tuple[Optional[str], Optional[str], Optional[str]],
        expected: Tuple[str, str, str],
        tmp_path: Path,
    ):
        # ext_file, inifield_file, structure_file
        """Test the from_mdu method of ExternalForcingConverter with various scenarios."""
        mdu_file = tmp_path / "test.mdu"
        mdu_file.touch()

        with (
            patch(
                "hydrolib.tools.extforce_convert.mdu_parser.MDUParser._load_with_fm_model"
            ) as mock_get_mdu_info,
            patch(
                "hydrolib.tools.extforce_convert.mdu_parser.MDUParser.get_temperature_salinity_data"
            ),
            patch(
                "hydrolib.tools.extforce_convert.main_converter.ExternalForcingConverter._read_old_file"
            ),
            patch(
                "hydrolib.tools.extforce_convert.utils.construct_filemodel_new_or_existing"
            ),
        ):
            mock_get_mdu_info.return_value = mdu_file_content

            converter = ExternalForcingConverter.from_mdu(
                mdu_file, input_files[0], input_files[1], input_files[2]
            )
        mdu_file.unlink()

        assert converter.ext_model.filepath.name == expected[0]
        assert converter.inifield_model.filepath.name == expected[1]
        assert converter.structure_model.filepath.name == expected[2]

    def test_from_mdu_not_exist(self):
        with pytest.raises(FileNotFoundError):
            ExternalForcingConverter.from_mdu("not_exist.mdu")


class TestExternalFocingConverter:

    def test_constructor_extold_model_path(
        self, old_forcing_file_initial_condition: Dict[str, Path]
    ):
        """
        Test the constructor of the ExternalForcingConverter class. The default constructor should set the extold_model
        attribute to the ExtOldModel instance created from the old external forcing file.

        and create the new external forcing, initial conditions and structure models. The new external forcing file
        should be named new-external-forcing.ext, the new initial conditions file should be named
        new-initial-conditions.ext and the new structure file should be named new-structure.ext.
        """
        path = old_forcing_file_initial_condition["path"]
        ext_old_model = ExtOldModel(path)
        converter = ExternalForcingConverter(path)
        assert isinstance(converter.extold_model, ExtOldModel)
        rdir = ext_old_model.filepath.parent

        assert isinstance(converter.ext_model, ExtModel)
        assert converter.ext_model.filepath == rdir / "new-external-forcing.ext"
        assert isinstance(converter.inifield_model, IniFieldModel)
        assert converter.inifield_model.filepath == rdir / "new-initial-conditions.ini"
        assert isinstance(converter.structure_model, StructureModel)
        assert converter.structure_model.filepath == rdir / "new-structure.ini"

    def test_path_not_exist(self):
        """
        Test the constructor of the ExternalForcingConverter class with a wrong extold_model.
        """
        ext_old_model = "wrong model"
        with pytest.raises(FileNotFoundError):
            ExternalForcingConverter(ext_old_model)

    def test_change_models_paths_using_setters(
        self, old_forcing_file_initial_condition: Dict[str, str]
    ):
        """
        Test the setter methods of the ExternalForcingConverter class.
        """
        path = old_forcing_file_initial_condition["path"]
        new_ext_file = Path("tests/data/input/new-external-forcing.ext")
        new_initial_file = Path("tests/data/input/new-initial-conditions.ext")
        new_structure_file = Path("tests/data/input/new-structure.ext")

        converter = ExternalForcingConverter(
            path, new_ext_file, new_initial_file, new_structure_file
        )

        assert converter.ext_model.filepath == new_ext_file
        assert converter.inifield_model.filepath == new_initial_file
        assert converter.structure_model.filepath == new_structure_file

    def test_save_mock(self, old_forcing_file_initial_condition: Dict[str, str]):
        """
        Mock test to test only the save method of the ExternalForcingConverter class.

        - The ExtOldModel instance is mocked.
        - The new models are created using the default paths.
        - The save method is called to save the new models.
        """
        mock_ext_old_model = MagicMock(spec=ExtOldModel)
        mock_ext_old_model.filepath = old_forcing_file_initial_condition["path"]

        converter = ExternalForcingConverter(mock_ext_old_model)
        converter._ext_model = MagicMock(spec=ExtModel)
        converter._ext_model.meteo = [MagicMock(spec=Meteo)]
        converter._ext_model.sourcesink = [MagicMock(spec=SourceSink)]
        converter._ext_model.lateral = [MagicMock(spec=Lateral)]
        converter._ext_model.boundary = [MagicMock(spec=Boundary)]
        converter._ext_model.filepath = Path("any-path.ext")

        converter.save()
        converter._ext_model.save.assert_called_once()

    def test_read_old_file(
        self,
        capsys,
        old_forcing_file: Path,
        old_forcing_file_quantities: List[str],
        old_forcing_comment_len: int,
    ):
        """
        Test instantiate the class with an external forcing file that has meteo, initial conditions, boundary,
        and parameters.
        test also check the verbose output.
        """
        converter = ExternalForcingConverter(old_forcing_file)
        assert len(converter.extold_model.forcing) == len(old_forcing_file_quantities)
        assert len(converter.extold_model.comment) == old_forcing_comment_len
        quantities = [forcing.quantity for forcing in converter.extold_model.forcing]
        assert all([quantity in old_forcing_file_quantities for quantity in quantities])

    def test_update_mdu_file(self):
        """
        Test the _update_mdu_file method of the ExternalForcingConverter class.

        This test verifies that:
        1. The external forcing file is updated in the MDU file
        2. An inifield file entry is added if it doesn't exist and there are initial fields or parameters
        3. A structure file entry is added if it doesn't exist and there are structures
        """
        mock_ext_old_model = MagicMock(spec=ExtOldModel)
        mock_ext_old_model.filepath = Path("tests/data/input/mock_file.ext")

        with patch(
            "hydrolib.tools.extforce_convert.main_converter.ExternalForcingConverter._read_old_file",
            return_value=mock_ext_old_model,
        ):
            converter = ExternalForcingConverter(mock_ext_old_model)

        mock_mdu_parser = MagicMock()
        mock_mdu_parser.has_inifield_file.return_value = False
        mock_mdu_parser.has_structure_file.return_value = False
        converter._mdu_parser = mock_mdu_parser

        datafile = DiskOnlyFileModel(
            filepath=Path("tests/data/input/mock_datafile.xyz")
        )

        # Create an InitialField instance
        initial_field = InitialField(
            quantity="waterlevel", datafile=datafile, datafiletype=DataFileType.arcinfo
        )

        converter.inifield_model.initial = [initial_field]

        # Add some structures to the structure model
        structure = Structure(
            id="structure1",
            name="Test Structure",
            type="weir",
            branchid="branch1",
            chainage=100.0,
        )

        converter.structure_model.structure = [structure]

        converter._update_mdu_file()

        # Verify that the external forcing file was updated
        mock_mdu_parser.update_extforce_file_new.assert_called_once()

        # Verify that the inifield file was added
        mock_mdu_parser.update_inifield_file.assert_called_once_with(
            converter.inifield_model.filepath.name
        )

        # Verify that the structure file was added
        mock_mdu_parser.update_structure_file.assert_called_once_with(
            converter.structure_model.filepath.name
        )

        # Test case: inifield file already exists
        mock_mdu_parser.reset_mock()
        mock_mdu_parser.has_inifield_file.return_value = True
        converter._update_mdu_file()
        mock_mdu_parser.update_inifield_file.assert_called_once_with(
            converter.inifield_model.filepath.name
        )

        # Test case: structure file already exists
        mock_mdu_parser.reset_mock()
        mock_mdu_parser.has_structure_file.return_value = True
        converter._update_mdu_file()
        mock_mdu_parser.update_structure_file.assert_called_once_with(
            converter.structure_model.filepath.name
        )

        # Test case: no initial fields or parameters
        mock_mdu_parser.reset_mock()
        mock_mdu_parser.has_inifield_file.return_value = False
        converter.inifield_model.initial = []
        converter.inifield_model.parameter = []
        converter._update_mdu_file()
        mock_mdu_parser.update_inifield_file.assert_not_called()

        # Test case: no structures
        mock_mdu_parser.reset_mock()
        mock_mdu_parser.has_structure_file.return_value = False
        converter.structure_model.structure = []
        converter._update_mdu_file()
        mock_mdu_parser.update_structure_file.assert_not_called()

    @pytest.mark.parametrize("path_style", [PathStyle.UNIXLIKE, PathStyle.WINDOWSLIKE])
    def test_externalforcingconverter_path_style_converted_to_os_style(
        self, tmp_path, path_style
    ):
        ext_file = tmp_path / "test.ext"
        pol_file = tmp_path / "domain.pol"
        filepath = str(pol_file)
        if path_style == PathStyle.UNIXLIKE and os.name == "nt":
            filepath = FilePathStyleConverter._from_windows_to_posix_path(pol_file)
        elif path_style == PathStyle.WINDOWSLIKE and os.name != "nt":
            filepath = FilePathStyleConverter._from_posix_to_windows_path(pol_file)
        ext_file.write_text(
            "QUANTITY     =initialtracerdTR1\n"
            f"FILENAME     ={filepath}\n"
            "FILETYPE     =10\n"
            "METHOD       =4\n"
            "OPERAND      =O\n"
            "VALUE        =0\n"
        )
        pol_file.write_text(
            "L1\n"
            "     4     2\n"
            "    -244.151184    1790.310059\n"
            "    -228.566650    -617.508057\n"
            "   10065.006836    -251.270264\n"
            "    9994.876953    1868.232910\n"
        )

        converter = ExternalForcingConverter(
            extold_model=ext_file,
            path_style=path_style,
        )
        converter.update()

        assert len(converter.inifield_model.initial) == 1
        assert converter.extold_model.forcing[0].filename.filepath == pol_file


class TestUpdate:

    def test_meteo_only(self, old_forcing_file_meteo: Dict[str, str]):
        converter = ExternalForcingConverter(old_forcing_file_meteo["path"])

        ext_model, inifield_model, structure_model = converter.update()

        # all the quantities in the old external file are initial conditions
        # check that all the quantities (3) were converted to initial conditions
        num_quantities = len(old_forcing_file_meteo["quantities"])
        assert len(ext_model.meteo) == num_quantities
        # no parameters or any other structures, lateral or meteo data
        assert len(inifield_model.parameter) == 0
        assert len(ext_model.lateral) == 0
        assert len(inifield_model.initial) == 0
        assert len(structure_model.structure) == 0
        assert [
            ext_model.meteo[i].forcingfiletype for i in range(num_quantities)
        ] == old_forcing_file_meteo["file_type"]
        assert [
            str(ext_model.meteo[i].forcingfile.filepath) for i in range(num_quantities)
        ] == old_forcing_file_meteo["file_path"]

    def test_initial_contitions_only(
        self, old_forcing_file_initial_condition: Dict[str, str]
    ):
        converter = ExternalForcingConverter(old_forcing_file_initial_condition["path"])

        ext_model, inifield_model, structure_model = converter.update()

        # all the quantities in the old external file are initial conditions
        # check that all the quantities (3) were converted to initial conditions
        num_quantities = len(old_forcing_file_initial_condition["quantities"])
        assert len(inifield_model.initial) == num_quantities
        # no parameters or any other structures, lateral or meteo data
        assert len(inifield_model.parameter) == 0
        assert len(ext_model.lateral) == 0
        assert len(ext_model.meteo) == 0
        assert len(structure_model.structure) == 0
        assert [
            inifield_model.initial[i].datafiletype for i in range(num_quantities)
        ] == old_forcing_file_initial_condition["file_type"]
        assert [
            str(inifield_model.initial[i].datafile.filepath)
            for i in range(num_quantities)
        ] == old_forcing_file_initial_condition["file_path"]


def test_clean():
    """mock test to test the clean method of the ExternalForcingConverter class.

    Notes:
    - The glob method is mocked to return two files with the extension .tim.
    - The unlink method is mocked to return True.
    """
    with (patch("pathlib.Path.unlink", return_value=True) as mock_unlink,):
        converter = ExternalForcingConverter(
            "tests/data/input/old-external-forcing.ext"
        )
        converter.legacy_files = [Path("fake.tim"), Path("fake2.tim")]
        converter.clean()
        assert mock_unlink.call_count == 3
