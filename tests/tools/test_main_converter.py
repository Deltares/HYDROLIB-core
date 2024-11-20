from pathlib import Path
from typing import List

from hydrolib.tools.ext_old_to_new import main_converter
from hydrolib.tools.ext_old_to_new.main_converter import (
    _read_ext_old_data,
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
