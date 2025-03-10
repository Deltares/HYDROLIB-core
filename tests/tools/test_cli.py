import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from hydrolib.core import __version__
from hydrolib.tools.extforce_convert.cli import ExternalForcingConverter, main


def test_no_arguments(monkeypatch, capsys):
    """
    If no arguments are provided, argparse should fail or show help.
    Because we used required=True in the mutually exclusive group,
    it will raise a SystemExit.
    """
    monkeypatch.setattr(sys, "argv", ["prog_name"])
    with pytest.raises(
        SystemExit
    ) as excinfo:  # Expecting a SystemExit due to missing required args
        main()

    assert excinfo.value.code == 2  # typical exit code for argparse usage error

    captured = capsys.readouterr()
    # You can check if usage/help text is printed
    assert "usage:" in captured.err or "usage:" in captured.out


def test_help(monkeypatch, capsys):
    # Simulate `--help`
    monkeypatch.setattr(sys, "argv", ["prog_name", "--help"])
    with pytest.raises(SystemExit):  # `argparse` raises SystemExit on `--help`
        main()
    captured = capsys.readouterr()
    assert "usage:" in captured.out
    assert "Convert D-Flow FM legacy external forcings" in captured.out


def test_version(monkeypatch, capsys):
    # Simulate `--version`
    monkeypatch.setattr(sys, "argv", ["prog_name", "--version"])
    with pytest.raises(SystemExit):
        main()
    captured = capsys.readouterr()
    assert __version__ in captured.out


def test_mdufile_ok(monkeypatch, capsys, input_files_dir: Path):
    """
    Test the minimal valid command with --mdufile.
    Ensures it doesn't raise an error.
    """
    mdu_file = input_files_dir / "e02/f011_wind/c081_combi_uniform_curvi/windcase.mdu"
    monkeypatch.setattr(sys, "argv", ["prog", "--mdufile", str(mdu_file)])

    # mock all the called methods from the ExternalForcingConverter.
    with (
        patch.object(ExternalForcingConverter, "update") as mock_update,
        patch.object(ExternalForcingConverter, "save") as mock_save,
        patch.object(ExternalForcingConverter, "clean") as mock_clean,
    ):
        mock_update.return_value = None, None, None
        mock_save.return_value = None
        mock_clean.return_value = None
        main()

    # Confirm nothing indicates an error
    captured = capsys.readouterr()
    assert (
        "Converting the old external forcing file to the new format files is done."
        in captured.out
    )
    assert "The new files are saved." in captured.out
