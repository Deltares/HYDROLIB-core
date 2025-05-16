import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from hydrolib.core import __version__
from hydrolib.tools.extforce_convert.cli import ExternalForcingConverter, main


def test_no_arguments(monkeypatch, capsys):
    """
    Purpose:
        Ensures that when no arguments are provided, the CLI fails with an appropriate usage message.
    Expected Behavior:
        The program exits with a `SystemExit` error (code `2`), and the help text is displayed.

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
    """
    Purpose:
        Verifies that the `--help` argument correctly displays usage information.
    Expected Behavior:
        The program exits normally and prints usage instructions, including a brief description of the tool.
    """
    # Simulate `--help`
    monkeypatch.setattr(sys, "argv", ["prog_name", "--help"])
    with pytest.raises(SystemExit):  # `argparse` raises SystemExit on `--help`
        main()
    captured = capsys.readouterr()
    assert "usage:" in captured.out
    assert "Convert D-Flow FM legacy external forcings" in captured.out


def test_version(monkeypatch, capsys):
    """
    Purpose:
        Confirms that the `--version` argument correctly prints the package version.
    Expected Behavior:
        The program exits normally and displays the `__version__` string.
    """
    # Simulate `--version`
    monkeypatch.setattr(sys, "argv", ["prog_name", "--version"])
    with pytest.raises(SystemExit):
        main()
    captured = capsys.readouterr()
    assert __version__ in captured.out


def test_mdufile_ok(monkeypatch, capsys, input_files_dir: Path):
    """
    Purpose:
        Tests the CLI behavior when a valid `--mdufile` argument is provided.
    Expected Behavior:
      - The CLI processes the given file without errors.
      - It calls the `update`, `save`, and `clean` methods of `ExternalForcingConverter`.
      - The expected success messages appear in the output.
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
