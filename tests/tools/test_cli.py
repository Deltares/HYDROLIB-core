import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import argparse
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


class TestGetParser:
    """
    Unit tests for the _get_parser function, covering all argument scenarios and error handling.
    """

    @pytest.fixture(autouse=True)
    def setup_parser(self, tmp_path):
        from hydrolib.tools.extforce_convert.cli import _get_parser

        self.parser = _get_parser()
        # Create dummy files for file arguments
        self.mdu = tmp_path / "test.mdu"
        self.ext = tmp_path / "test.ext"
        self.mdu.write_text("")
        self.ext.write_text("")
        self.tmp_path = tmp_path

    @pytest.mark.unit
    def test_only_mdufile(self):
        """
        Test that only --mdufile is accepted and parsed correctly, and other mutually exclusive arguments are None.
        """
        args = self.parser.parse_args(["--mdufile", str(self.mdu)])
        assert args.mdufile == self.mdu
        assert args.extoldfile is None
        assert args.dir is None

    @pytest.mark.unit
    def test_only_extoldfile(self):
        """
        Test that only --extoldfile is accepted and parsed correctly, and other mutually exclusive arguments are None.
        """
        args = self.parser.parse_args(["--extoldfile", str(self.ext)])
        assert args.extoldfile == self.ext
        assert args.mdufile is None
        assert args.dir is None

    @pytest.mark.unit
    def test_only_dir(self):
        """
        Test that only --dir is accepted and parsed correctly, and other mutually exclusive arguments are None.
        """
        args = self.parser.parse_args(["--dir", str(self.tmp_path)])
        assert args.dir == str(self.tmp_path)
        assert args.mdufile is None
        assert args.extoldfile is None

    @pytest.mark.unit
    def test_outfiles_with_three_values(self):
        """
        Test that --outfiles accepts exactly three values and parses them correctly.
        """
        args = self.parser.parse_args(
            ["--mdufile", str(self.mdu), "--outfiles", "a.ext", "b.ini", "c.str"]
        )
        assert args.outfiles == ["a.ext", "b.ini", "c.str"]

    @pytest.mark.unit
    def test_backup_and_no_backup(self):
        """
        Test that --backup and --no-backup flags are mutually exclusive and set the backup attribute correctly.
        """
        args = self.parser.parse_args(["--mdufile", str(self.mdu)])
        assert args.backup is True
        args = self.parser.parse_args(["--mdufile", str(self.mdu), "--no-backup"])
        assert args.backup is False
        args = self.parser.parse_args(["--mdufile", str(self.mdu), "--backup"])
        assert args.backup is True

    @pytest.mark.unit
    def test_remove_legacy_files(self):
        """
        Test that --remove-legacy-files flag sets the remove_legacy attribute to True.
        """
        args = self.parser.parse_args(["--mdufile", str(self.mdu), "--remove-legacy-files"])
        assert args.remove_legacy is True

    @pytest.mark.unit
    def test_verbose(self):
        """
        Test that --verbose flag sets the verbose attribute to True.
        """
        args = self.parser.parse_args(["--mdufile", str(self.mdu), "--verbose"])
        assert args.verbose is True

    @pytest.mark.unit
    def test_mutually_exclusive_group(self):
        """
        Test that mutually exclusive arguments (--mdufile, --extoldfile, --dir) cannot be used together and raise SystemExit.
        """
        with pytest.raises(SystemExit):
            self.parser.parse_args(["--mdufile", str(self.mdu), "--extoldfile", str(self.ext)])
        with pytest.raises(SystemExit):
            self.parser.parse_args(["--mdufile", str(self.mdu), "--dir", str(self.tmp_path)])
        with pytest.raises(SystemExit):
            self.parser.parse_args(["--extoldfile", str(self.ext), "--dir", str(self.tmp_path)])

    @pytest.mark.unit
    def test_missing_required_argument(self):
        """
        Test that missing all mutually exclusive required arguments raises SystemExit.
        """
        with pytest.raises(SystemExit):
            self.parser.parse_args([])

    @pytest.mark.unit
    def test_wrong_number_of_outfiles(self):
        """
        Test that providing fewer than three values to --outfiles raises SystemExit.
        """
        with pytest.raises(SystemExit):
            self.parser.parse_args(["--mdufile", str(self.mdu), "--outfiles", "a.ext", "b.ini"])  # only 2

    @pytest.mark.unit
    def test_nonexistent_file_argument(self):
        """
        Test that providing a non-existent file to --mdufile or --extoldfile raises ArgumentTypeError.
        """
        with pytest.raises(argparse.ArgumentTypeError):
            self.parser.parse_args(["--mdufile", str(self.tmp_path / "doesnotexist.mdu")])
        with pytest.raises(argparse.ArgumentTypeError):
            self.parser.parse_args(["--extoldfile", str(self.tmp_path / "doesnotexist.ext")])
