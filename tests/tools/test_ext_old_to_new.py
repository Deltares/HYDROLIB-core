from hydrolib.tools.ext_old_to_new import main_converter

from tests.utils import (
    test_input_dir,
)


class TestExtOldToNew:
    def test_wind_combi_uniform_curvi(self, capsys):
        main_converter._verbose = True
        mdu_filename = (
            test_input_dir
            / "e02"
            / "f011_wind"
            / "c081_combi_uniform_curvi"
            / "windcase.mdu"
        )

        main_converter.ext_old_to_new_from_mdu(mdu_filename)
        captured = capsys.readouterr()
        assert captured.out.startswith(f"Could not read {mdu_filename} as a valid FM model:")

    def test_extrapolate_slr(self, capsys):
        main_converter._verbose = True
        mdu_filename = (
            test_input_dir
            / "e02"
            / "f006_external_forcing"
            / "c011_extrapolate_slr"
            / "slrextrapol.mdu"
        )
        main_converter.ext_old_to_new_from_mdu(mdu_filename)
        captured = capsys.readouterr()
        assert captured.out.startswith(f"Could not read {mdu_filename} as a valid FM model:")

    def test_basinsquares(self, capsys):
        main_converter._verbose = True
        mdu_filename = (
            test_input_dir
            / "e02"
            / "f006_external_forcing"
            / "c020_basinnofriction_squares"
            / "basinsquares.mdu"
        )

        main_converter.ext_old_to_new_from_mdu(mdu_filename)
        captured = capsys.readouterr()
        assert captured.out.startswith(f"Could not read {mdu_filename} as a valid FM model:")

    def test_recursive(self, capsys):
        main_converter._verbose = True
        dir = test_input_dir / "e02" / "f006_external_forcing"
        main_converter.ext_old_to_new_dir_recursive(dir)
        assert True
