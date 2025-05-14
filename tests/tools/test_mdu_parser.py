from pathlib import Path
from typing import Tuple
from unittest.mock import patch

import pytest

from hydrolib.tools.extforce_convert.mdu_parser import MDUParser, save_mdu_file


@pytest.mark.parametrize(
    "input_file, on_line, expected_line, ext_file",
    [
        (
            "dflowfm_individual_files/with_optional_sections.mdu",
            (232, 233),
            "ExtForceFileNew                           = test.ext\n",
            "test.ext",
        ),
        (
            "e02/f011_wind/c081_combi_uniform_curvi/windcase.mdu",
            (149, 150),
            "ExtForceFileNew                      = test.ext                              # New format for external forcings file *.ext, link with bc     -format boundary conditions specification\n",
            "test.ext",
        ),
        (
            "e02/f011_wind/c081_combi_uniform_curvi/windcase.mdu",
            (149, 150),
            "ExtForceFileNew                      = really_long_external_forcing_file_results_name.ext # New format for external forcings file *.ext, link with bc     -format boundary conditions specification\n",
            "really_long_external_forcing_file_results_name.ext",
        ),
    ],
    ids=["without comment", "with comment", "overflow comment"],
)
def test_update_mdu_on_the_fly(
    input_files_dir: Path,
    input_file: str,
    on_line: Tuple[int, int],
    expected_line: str,
    ext_file: str,
):
    mdu_filename = input_files_dir / input_file
    new_mdu_file = mdu_filename.with_stem(f"{mdu_filename.stem}-updated")
    updater = MDUParser(mdu_filename, ext_file)
    updated_mdu_file = updater.update_extforce_file_new()
    assert updated_mdu_file[on_line[0]] == "[external forcing]\n"
    assert updated_mdu_file[on_line[1]] == expected_line
    # test the save mdu file function
    save_mdu_file(updated_mdu_file, new_mdu_file)
    assert new_mdu_file.exists()
    try:
        new_mdu_file.unlink()
    except PermissionError:
        pass


@pytest.mark.parametrize(
    "line, expected",
    [
        (
            "ExtForceFileNew                           = old_file.ext",
            "ExtForceFileNew                           = new_file.ext\n",
        ),
        (
            "ExtForceFileNew                           = old_file.ext # Comment",
            "ExtForceFileNew                           = new_file.ext # Comment\n",
        ),
        (
            "ExtForceFileNew",
            "ExtForceFileNew",
        ),
    ],
    ids=["without comment", "with comment", "without equals sign"],
)
def test_replace_extforcefilenew(line, expected):
    """Test the replace_extforcefilenew method."""
    with patch("hydrolib.tools.extforce_convert.mdu_parser.MDUParser._read_file"):
        parser = MDUParser("dummy_path", "new_file.ext")

    assert parser.replace_extforcefilenew(line) == expected


def test_is_section_header():
    """Test the is_section_header method."""
    # Test with valid section headers
    assert MDUParser.is_section_header("[general]") is True
    assert MDUParser.is_section_header("[output]") is True

    # Test with invalid section headers
    assert MDUParser.is_section_header("general") is False
    assert MDUParser.is_section_header("[general") is False
    assert MDUParser.is_section_header("general]") is False

    # Test with external forcing section header (should return False)
    assert MDUParser.is_section_header("[external forcing]") is False
    assert MDUParser.is_section_header("[EXTERNAL FORCING]") is False
