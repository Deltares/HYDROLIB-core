from pathlib import Path
from hydrolib.tools.ext_old_to_new import main_converter


class TestExtOldToNew:
    def test_wind_combi_uniform_curvi(self, capsys, input_files_dir: Path):
        main_converter._verbose = True
        mdu_filename = input_files_dir.joinpath("e02/f011_wind/c081_combi_uniform_curvi/windcase.mdu")
        main_converter.ext_old_to_new_from_mdu(mdu_filename)
        captured = capsys.readouterr()
        assert captured.out.startswith(f"Could not read {mdu_filename} as a valid FM model:")

    def test_extrapolate_slr(self, capsys, input_files_dir: Path):
        main_converter._verbose = True
        mdu_filename = input_files_dir.joinpath("e02/f006_external_forcing/c011_extrapolate_slr/slrextrapol.mdu")
        main_converter.ext_old_to_new_from_mdu(mdu_filename)
        captured = capsys.readouterr()
        assert captured.out.startswith(f"Could not read {mdu_filename} as a valid FM model:")

    def test_basinsquares(self, capsys, input_files_dir: Path):
        main_converter._verbose = True
        mdu_filename = input_files_dir.joinpath(
            "e02/f006_external_forcing/c020_basinnofriction_squares/basinsquares.mdu"
        )
        main_converter.ext_old_to_new_from_mdu(mdu_filename)
        captured = capsys.readouterr()
        assert captured.out.startswith(f"Could not read {mdu_filename} as a valid FM model:")

    def test_recursive(self, capsys):
        main_converter._verbose = True
        main_converter.ext_old_to_new_dir_recursive(f"{test_input_dir}/e02/f006_external_forcing")


