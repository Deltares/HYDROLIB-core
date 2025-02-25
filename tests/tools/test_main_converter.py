from pathlib import Path
from typing import Dict, List
from unittest.mock import MagicMock, Mock, patch

import pytest

from hydrolib.core.dflowfm.ext.models import ExtModel
from hydrolib.core.dflowfm.extold.models import ExtOldModel
from hydrolib.core.dflowfm.inifield.models import IniFieldModel
from hydrolib.core.dflowfm.mdu.legacy import LegacyFMModel
from hydrolib.core.dflowfm.structure.models import StructureModel
from hydrolib.tools.ext_old_to_new import main_converter
from hydrolib.tools.ext_old_to_new.main_converter import (
    ExternalForcingConverter,
    ext_old_to_new_dir_recursive,
)
from tests.utils import compare_two_files


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
        fm_model = converter.fm_model
        assert isinstance(fm_model, LegacyFMModel)
        assert len(converter.extold_model.forcing) == 5
        assert isinstance(fm_model.external_forcing.extforcefilenew, ExtModel)
        assert not hasattr(fm_model.external_forcing, "extforcefile")

        # check the saved files
        converter.save()

        # check that the mdu file has the relative pathes, not the absolute pathes
        # the pathes are changes to the relative pathes inside the save function.
        mdu_path = fm_model.external_forcing.extforcefilenew.filepath
        assert mdu_path.parent == Path(".")  # no parent

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
        converter = ExternalForcingConverter.from_mdu(
            mdu_filename, suppress_errors=True
        )
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
            "hydrolib.tools.ext_old_to_new.main_converter.ExternalForcingConverter.save",
            return_value=None,
        ):
            ext_old_to_new_dir_recursive(path, suppress_errors=True)


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
        assert converter.ext_model.filepath == rdir.joinpath("new-external-forcing.ext")
        assert isinstance(converter.inifield_model, IniFieldModel)
        assert converter.inifield_model.filepath == rdir.joinpath(
            "new-initial-conditions.ext"
        )
        assert isinstance(converter.structure_model, StructureModel)
        assert converter.structure_model.filepath == rdir.joinpath("new-structure.ext")

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

    def test_save(self, old_forcing_file_initial_condition: Dict[str, str]):
        """
        Mock test to test only the save method of the ExternalForcingConverter class.

        - The ExtOldModel instance is mocked.
        - The new models are created using the default paths.
        - The save method is called to save the new models.
        """
        mock_ext_old_model = MagicMock(spec=ExtOldModel)
        mock_ext_old_model.filepath = old_forcing_file_initial_condition["path"]

        converter = ExternalForcingConverter(mock_ext_old_model)
        converter.save()

        assert converter.ext_model.filepath.exists()
        assert not converter.inifield_model.filepath.exists()
        assert not converter.structure_model.filepath.exists()
        try:
            converter.ext_model.filepath.unlink()
        except PermissionError:
            pass

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

    def test_boundary_only(self, old_forcing_file_boundary: Dict[str, str]):
        """
        The old external forcing file contains only 9 boundary condition quantities all with polyline location files
        and no forcing files. The update method should convert all the quantities to boundary conditions.
        """
        mdu_info = {
            "refdate": "minutes since 2015-01-01 00:00:00",
        }
        converter = ExternalForcingConverter(
            old_forcing_file_boundary["path"], mdu_info=mdu_info
        )

        # Mock the fm_model
        mock_fm_model = Mock()
        converter._fm_model = mock_fm_model
        ext_model, inifield_model, structure_model = converter.update()

        # all the quantities in the old external file are initial conditions
        # check that all the quantities (3) were converted to initial conditions
        num_quantities = len(old_forcing_file_boundary["quantities"])
        assert len(ext_model.boundary) == num_quantities
        # no parameters or any other structures, lateral or meteo data
        assert len(inifield_model.parameter) == 0
        assert len(ext_model.lateral) == 0
        assert len(ext_model.meteo) == 0
        assert len(structure_model.structure) == 0
        quantities = ext_model.boundary
        assert [
            str(quantities[i].locationfile.filepath) for i in range(num_quantities)
        ] == old_forcing_file_boundary["locationfile"]
        r_dir = converter.root_dir
        # test save files
        ext_model.save(recurse=True)

        reference_files = ["new-external-forcing-reference.ext", "tfl_01-reference.bc"]
        files = ["new-external-forcing.ext", "tfl_01.bc"]
        for i in range(2):
            assert (r_dir / files[i]).exists()
            diff = compare_two_files(r_dir / reference_files[i], r_dir / files[i])
            assert diff == []
            (r_dir / files[i]).unlink()


class TestUpdateSourcesSinks:

    def test_sources_sinks_only(self, old_forcing_file_boundary: Dict[str, str]):
        """
        The old external forcing file contains only 3 quantities `discharge_salinity_temperature_sorsin`,
        `initialsalinity`, and `initialtemperature`.

        - polyline 2*3 file `leftsor.pliz` is used to read the source and sink points.
        - tim file `tim-3-columns.tim` with 3 columns (plus the time column) the name should be the same as the
        polyline but the `tim-3-columns.tim` is mocked in the test.

        """
        path = "tests/data/input/source-sink/source-sink.ext"
        mdu_info = {
            "refdate": "minutes since 2015-01-01 00:00:00",
        }
        converter = ExternalForcingConverter(path, mdu_info=mdu_info)
        # Mock the fm_model
        mock_fm_model = Mock()
        converter._fm_model = mock_fm_model

        tim_file = Path("tim-3-columns.tim")
        with patch("pathlib.Path.with_suffix", return_value=tim_file):
            ext_model, inifield_model, structure_model = converter.update()

        # all the quantities in the old external file are initial conditions
        # check that all the quantities (3) were converted to initial conditions
        num_quantities = 1
        assert len(ext_model.sourcesink) == num_quantities
        # no parameters or any other structures, lateral or meteo data
        assert len(inifield_model.parameter) == 0
        assert len(ext_model.lateral) == 0
        assert len(ext_model.meteo) == 0
        assert len(structure_model.structure) == 0
        assert len(inifield_model.initial) == 2
        quantities = ext_model.sourcesink
        quantities[0].name = "discharge_salinity_temperature_sorsin"

    def test_sources_sinks_with_fm(self, old_forcing_file_boundary: Dict[str, str]):
        """
        The old external forcing file contains only 3 quantities `discharge_salinity_temperature_sorsin`,
        `initialsalinity`, and `initialtemperature`.

        - polyline 2*3 file `leftsor.pliz` is used to read the source and sink points.
        - tim file `tim-3-columns.tim` with 3 columns (plus the time column) the name should be the same as the
        polyline but the `tim-3-columns.tim` is mocked in the test.

        """
        path = "tests/data/input/source-sink/source-sink.ext"
        mdu_info = {
            "refdate": "minutes since 2015-01-01 00:00:00",
            "salinity": True,
            "temperature": True,
        }
        converter = ExternalForcingConverter(path, mdu_info=mdu_info)

        # Mock the fm_model
        mock_fm_model = Mock()
        converter._fm_model = mock_fm_model

        tim_file = Path("tim-3-columns.tim")
        with patch("pathlib.Path.with_suffix", return_value=tim_file):
            ext_model, inifield_model, structure_model = converter.update()

        # all the quantities in the old external file are initial conditions
        # check that all the quantities (3) were converted to initial conditions
        num_quantities = 1
        assert len(ext_model.sourcesink) == num_quantities
        # no parameters or any other structures, lateral or meteo data
        assert len(inifield_model.parameter) == 0
        assert len(ext_model.lateral) == 0
        assert len(ext_model.meteo) == 0
        assert len(structure_model.structure) == 0
        assert len(inifield_model.initial) == 2
        quantities = ext_model.sourcesink
        quantities[0].name = "discharge_salinity_temperature_sorsin"
