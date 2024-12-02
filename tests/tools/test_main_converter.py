from pathlib import Path
from typing import Dict, List
from unittest.mock import MagicMock

import pytest

from hydrolib.core.dflowfm.ext.models import ExtModel
from hydrolib.core.dflowfm.extold.models import ExtOldModel
from hydrolib.core.dflowfm.inifield.models import IniFieldModel
from hydrolib.core.dflowfm.structure.models import StructureModel
from hydrolib.tools.ext_old_to_new import main_converter
from hydrolib.tools.ext_old_to_new.main_converter import (
    ExternalForcingConverter,
    _get_parser,
    ext_old_to_new_dir_recursive,
    ext_old_to_new_from_mdu,
)


class TestExtOldToNew:
    def test_wind_combi_uniform_curvi(self, capsys, input_files_dir: Path):
        main_converter._verbose = True
        mdu_filename = input_files_dir.joinpath(
            "e02/f011_wind/c081_combi_uniform_curvi/windcase.mdu"
        )
        ext_old_to_new_from_mdu(mdu_filename)
        captured = capsys.readouterr()
        assert captured.out.startswith(
            f"Could not read {mdu_filename} as a valid FM model:"
        )

    def test_extrapolate_slr(self, capsys, input_files_dir: Path):
        main_converter._verbose = True
        mdu_filename = input_files_dir.joinpath(
            "e02/f006_external_forcing/c011_extrapolate_slr/slrextrapol.mdu"
        )
        ext_old_to_new_from_mdu(mdu_filename)
        captured = capsys.readouterr()
        assert captured.out.startswith(
            f"Could not read {mdu_filename} as a valid FM model:"
        )

    def test_basinsquares(self, capsys, input_files_dir: Path):
        main_converter._verbose = True
        mdu_filename = input_files_dir.joinpath(
            "e02/f006_external_forcing/c020_basinnofriction_squares/basinsquares.mdu"
        )
        ext_old_to_new_from_mdu(mdu_filename)
        captured = capsys.readouterr()
        assert captured.out.startswith(
            f"Could not read {mdu_filename} as a valid FM model:"
        )

    def test_recursive(self, capsys, input_files_dir: Path):
        main_converter._verbose = True
        path = input_files_dir.joinpath("e02/f006_external_forcing")
        ext_old_to_new_dir_recursive(path)


class TestExternalFocingConverter:

    def test_constructor_default(
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
        converter = ExternalForcingConverter(ext_old_model)
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

    def test_wrong_extold_model(self):
        """
        Test the constructor of the ExternalForcingConverter class with a wrong extold_model.
        """
        ext_old_model = "wrong model"
        with pytest.raises(ValueError):
            ExternalForcingConverter(ext_old_model)

    def test_change_models_paths_using_setters(
        self, old_forcing_file_initial_condition: Dict[str, str]
    ):
        """
        Test the setter methods of the ExternalForcingConverter class.
        """
        path = old_forcing_file_initial_condition["path"]
        converter = ExternalForcingConverter.read_old_file(path)

        new_ext_file = Path("tests/data/input/new-external-forcing.ext")
        new_initial_file = Path("tests/data/input/new-initial-conditions.ext")
        new_structure_file = Path("tests/data/input/new-structure.ext")

        converter.inifield_model = new_initial_file
        converter.structure_model = new_structure_file
        converter.ext_model = new_ext_file

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
        assert converter.inifield_model.filepath.exists()
        assert converter.structure_model.filepath.exists()

        converter.ext_model.filepath.unlink()
        converter.inifield_model.filepath.unlink()
        converter.structure_model.filepath.unlink()

    def test_read_old_file(
        self,
        capsys,
        old_forcing_file: Path,
        old_forcing_file_quantities: List[str],
        old_forcing_comment_len: int,
    ):
        """
        Test instantiate the class using the read_old_file class method.
        """
        converter = ExternalForcingConverter.read_old_file(old_forcing_file)
        assert len(converter.extold_model.forcing) == len(old_forcing_file_quantities)
        assert len(converter.extold_model.comment) == old_forcing_comment_len
        quantities = [forcing.quantity for forcing in converter.extold_model.forcing]
        assert all([quantity in old_forcing_file_quantities for quantity in quantities])
        # test verbose
        main_converter._verbose = True
        converter.read_old_file(old_forcing_file)
        captured = capsys.readouterr()

        assert captured.out.startswith(
            f"Read {(len(old_forcing_file_quantities))} forcing blocks from {old_forcing_file}."
        )


class TestUpdate:

    def test_meteo_only(self, old_forcing_file_meteo: Dict[str, str]):
        path = old_forcing_file_meteo["path"]
        converter = ExternalForcingConverter.read_old_file(path)

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
        path = old_forcing_file_initial_condition["path"]
        converter = ExternalForcingConverter.read_old_file(path)

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
