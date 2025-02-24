import sys

import pytest

from hydrolib.core import __version__
from hydrolib.tools.ext_old_to_new.cli import main


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
