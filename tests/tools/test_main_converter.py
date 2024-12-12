from pathlib import Path
from typing import Dict, List

from hydrolib.tools.ext_old_to_new import main_converter
from hydrolib.tools.ext_old_to_new.main_converter import (
    _read_ext_old_data,
    ext_old_to_new,
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


def test__read_ext_old_data(
    capsys,
    old_forcing_file: Path,
    old_forcing_file_quantities: List[str],
    old_forcing_comment_len: int,
):
    model = _read_ext_old_data(old_forcing_file)
    assert len(model.forcing) == len(old_forcing_file_quantities)
    assert len(model.comment) == old_forcing_comment_len
    quantities = [forcing.quantity for forcing in model.forcing]
    assert all([quantity in old_forcing_file_quantities for quantity in quantities])
    # test verbose
    main_converter._verbose = True
    _read_ext_old_data(old_forcing_file)
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out.startswith(
        f"Read {(len(old_forcing_file_quantities))} forcing blocks from {old_forcing_file}."
    )


class TestExtOldToNew:

    def test_ext_with_only_initial_contitions(
        self, old_forcing_file_initial_condition: Dict[str, str]
    ):
        new_ext_file = Path("tests/data/input/new-external-forcing.ext")
        new_initial_file = Path("tests/data/input/new-initial-conditions.ext")
        new_structure_file = Path("tests/data/input/new-structure.ext")

        path = old_forcing_file_initial_condition["path"]
        extold_model, ext_model, inifield_model, structure_model = ext_old_to_new(
            path, new_ext_file, new_initial_file, new_structure_file
        )

        assert new_ext_file.exists()
        assert new_initial_file.exists()
        assert new_structure_file.exists()
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
        # clean up
        # try
        new_initial_file.unlink()
        new_ext_file.unlink()
        new_structure_file.unlink()
