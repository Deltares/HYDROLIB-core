from pathlib import Path
from hydrolib.tools.ext_old_to_new import main_converter
from hydrolib.tools.ext_old_to_new.main_converter import \
    ext_old_to_new_from_mdu, \
    ext_old_to_new_dir_recursive, \
    ext_old_to_new



class TestExtOldToNew:
    def test_wind_combi_uniform_curvi(self, capsys, input_files_dir: Path):
        main_converter._verbose = True
        mdu_filename = input_files_dir.joinpath("e02/f011_wind/c081_combi_uniform_curvi/windcase.mdu")
        ext_old_to_new_from_mdu(mdu_filename)
        captured = capsys.readouterr()
        assert captured.out.startswith(f"Could not read {mdu_filename} as a valid FM model:")

    def test_extrapolate_slr(self, capsys, input_files_dir: Path):
        main_converter._verbose = True
        mdu_filename = input_files_dir.joinpath("e02/f006_external_forcing/c011_extrapolate_slr/slrextrapol.mdu")
        ext_old_to_new_from_mdu(mdu_filename)
        captured = capsys.readouterr()
        assert captured.out.startswith(f"Could not read {mdu_filename} as a valid FM model:")

    def test_basinsquares(self, capsys, input_files_dir: Path):
        main_converter._verbose = True
        mdu_filename = input_files_dir.joinpath(
            "e02/f006_external_forcing/c020_basinnofriction_squares/basinsquares.mdu"
        )
        ext_old_to_new_from_mdu(mdu_filename)
        captured = capsys.readouterr()
        assert captured.out.startswith(f"Could not read {mdu_filename} as a valid FM model:")

    def test_recursive(self, capsys, input_files_dir: Path):
        main_converter._verbose = True
        path = input_files_dir.joinpath("e02/f006_external_forcing")
        ext_old_to_new_dir_recursive(path)

    def test_trial(self):
        path = "tests/data/input/old-external-forcing.ext"
        new_ext_file = "tests/data/new-external-forcing.ext"
        new_initial_file = "tests/data/new-initial-conditions.ext"
        new_structure_file = "tests/data/new-structure.ext"
        result = ext_old_to_new(path, new_ext_file, new_initial_file, new_structure_file)
        print(result)
