import os
from pathlib import Path
from typing import Tuple
from unittest.mock import MagicMock, patch

import pytest

from hydrolib.tools.extforce_convert.mdu_parser import (
    MDUParser,
    get_ref_time,
    save_mdu_file,
)


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
    updater = MDUParser(mdu_filename)
    updater.new_forcing_file = ext_file
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


def test_save_mdu_file(tmp_path):
    """Test the save_mdu_file function."""
    # Create test content
    content = ["[general]\n", "Name = Test\n", "[geometry]\n", "NetFile = test.nc\n"]

    # Create a temporary file path
    output_path = tmp_path / "test_save.mdu"

    # Save the content to the file
    save_mdu_file(content, output_path)

    # Check that the file exists
    assert output_path.exists()

    # Check that the file contains the expected content
    with open(output_path, "r", encoding="utf-8") as f:
        saved_content = f.readlines()

    assert saved_content == content


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
    # Mock the MDUParser class and its methods
    with (
        patch("hydrolib.tools.extforce_convert.mdu_parser.MDUParser._read_file"),
        patch("pathlib.Path.exists", return_value=True),
        patch(
            "hydrolib.tools.extforce_convert.mdu_parser.MDUParser._load_with_fm_model",
            return_value=MagicMock(geometry=MagicMock()),
        ),
        patch(
            "hydrolib.tools.extforce_convert.mdu_parser.MDUParser.get_temperature_salinity_data",
            return_value=None,
        ),
    ):
        parser = MDUParser("dummy_path")
        parser.new_forcing_file = Path("new_file.ext")

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


def test_get_ref_time():
    """Test the get_ref_time function."""
    # Test with valid date
    result = get_ref_time("20220101")
    assert "MINUTES SINCE" in result
    assert "2022-01-01" in result

    # Test with custom format
    result = get_ref_time("01-02-2022", date_format="%d-%m-%Y")
    assert "MINUTES SINCE" in result
    assert "2022-02-01" in result


class TestMduParser:
    file_path = "tests/data/input/dflowfm_individual_files/mdu/sp.mdu"

    def test_init(self):
        """Test the initialization of MDUParser."""
        # Test with a valid file path
        parser = MDUParser(self.file_path)
        assert parser.mdu_path == Path(self.file_path)
        assert parser.updated_lines == []
        assert parser.inside_external_forcing is False
        assert parser.found_extforcefilenew is False
        assert isinstance(parser._content, list)
        assert isinstance(parser.loaded_fm_data, dict)
        assert isinstance(parser.temperature_salinity_data, dict)

    def test_init_with_nonexistent_file(self):
        """Test initialization with a non-existent file."""
        with pytest.raises(FileNotFoundError):
            MDUParser("non_existent_file.mdu")

    def test_new_forcing_file_property(self):
        """Test the new_forcing_file property."""
        parser = MDUParser(self.file_path)

        # Test getting the property before it's set
        with pytest.raises(AttributeError):
            _ = parser.new_forcing_file

        # Test setting with valid values
        parser.new_forcing_file = "test.ext"
        assert parser.new_forcing_file == "test.ext"

        parser.new_forcing_file = Path("another_test.ext")
        assert parser.new_forcing_file == Path("another_test.ext")

        # Test setting with invalid value
        with pytest.raises(ValueError):
            parser.new_forcing_file = 123

    def test_geometry_property(self):
        """Test the geometry property."""
        parser = MDUParser(self.file_path)
        assert parser.geometry == parser._geometry

    def test_content_property(self):
        """Test the content property and setter."""
        parser = MDUParser(self.file_path)
        original_content = parser.content

        # Test setting new content
        new_content = ["New line 1\n", "New line 2\n"]
        parser.content = new_content
        assert parser.content == new_content

        # Restore original content
        parser.content = original_content

    def test_read_file(self):
        """Test the _read_file method."""
        parser = MDUParser(self.file_path)
        content = parser._read_file()
        assert isinstance(content, list)
        assert len(content) > 0
        assert all(isinstance(line, str) for line in content)

    def test_load_with_fm_model(self):
        """Test the _load_with_fm_model method."""
        parser = MDUParser(self.file_path)
        data = parser._load_with_fm_model()
        assert isinstance(data, dict)
        assert "geometry" in data

    def test_save(self, tmp_path):
        """Test the save method."""
        parser = MDUParser(self.file_path)

        # Create a temporary file path
        temp_file = tmp_path / "test_save.mdu"

        # Save to the temporary file
        with patch(
            "hydrolib.tools.extforce_convert.mdu_parser.backup_file"
        ) as mock_backup:
            # Save without backup
            parser.mdu_path = temp_file
            parser.save()
            mock_backup.assert_not_called()

            # Save with backup
            parser.save(backup=True)
            mock_backup.assert_called_once_with(temp_file)

    @pytest.mark.e2e
    def test_find_keyword_lines(self):
        parser = MDUParser(self.file_path)
        assert parser.find_keyword_lines("ThinDamFile") == 13
        assert parser.find_keyword_lines("ThinDamFile", case_sensitive=True) == 13

        # Test with a keyword that doesn't exist
        assert parser.find_keyword_lines("NonExistentKeyword") is None

    def test_insert_line(self):
        parser = MDUParser(self.file_path)
        new_line = "NewLine = value\n"
        parser.insert_line(new_line, 5)
        assert parser.content[5] == new_line

        # Test inserting at the beginning
        parser.insert_line("StartLine = value\n", 0)
        assert parser.content[0] == "StartLine = value\n"

        # Test inserting at the end
        end_index = len(parser.content)
        parser.insert_line("EndLine = value", end_index)
        assert parser.content[end_index] == "EndLine = value\n"

        # Test inserting with out-of-bounds index
        with pytest.raises(IndexError):
            parser.insert_line("Invalid", len(parser.content) + 1)

    def test_find_section_bounds(self):
        parser = MDUParser(self.file_path)
        section_start, section_end = parser.find_section_bounds("geometry")
        assert parser.content[section_start] == "[geometry]\n"
        assert parser.content[section_end] == "\n"

        # Test for a non-existing section
        non_existing_section = parser.find_section_bounds("non-existing")
        assert non_existing_section[0] is None
        assert non_existing_section[1] is None

    @pytest.mark.unit
    def test_update_inifield_file_without_decorative_line(self):
        """
        Test adding the inifield file path to the geometry section.
        The mdu file does not have lines around the section header.
        - Example mdu file content:
        ```ini
        [geometry]
        ...
        Dcenterinside                       = 1.
        PartitionFile                       =

        [numerics]
        ...
        ```

        - The inifield file should be added as:
        ```ini
        [geometry]
        ...
        Dcenterinside                       = 1.
        IniFieldFile = new-inifield-file.ini
        PartitionFile                       =

        [numerics]
        ...
        ```
        """
        parser = MDUParser(self.file_path)
        parser.update_inifield_file("new-inifield-file.ini")

        # Check if the inifield file was added to the geometry section
        _, end_ind = parser.find_section_bounds("geometry")
        assert parser._content[end_ind - 2] == "IniFieldFile = new-inifield-file.ini\n"

    @pytest.mark.unit
    def test_update_inifield_file_with_decorative_lines(self):
        """
        Test adding the inifield file path to the geometry section.

        The mdu file have decorative lines around the section header.

        ```ini
        #============================
        [geometry]
        #============================
        ...
        Dcenterinside                       = 1.
        PartitionFile                       =

        #============================
        [numerics]
        #============================
        ...
        ```
        """
        parser = MDUParser(self.file_path)
        # add the decorative lines at the upper line of the numerics section
        parser._content.insert(29, "#============================\n")
        parser.update_inifield_file("new-inifield-file.ini")

        # Check if the inifield file was added to the geometry section
        _, end_ind = parser.find_section_bounds("geometry")
        assert parser._content[end_ind - 2] == "IniFieldFile = new-inifield-file.ini\n"

    def test_handle_external_forcing_section(self):
        """Test the _handle_external_forcing_section method."""
        parser = MDUParser(self.file_path)
        parser.new_forcing_file = "test.ext"
        parser.inside_external_forcing = True
        parser.found_extforcefilenew = False
        parser.updated_lines = []

        # Test with a section header
        parser._handle_external_forcing_section("[general]")
        assert not parser.inside_external_forcing
        assert len(parser.updated_lines) == 3  # New line + empty line
        assert "ExtForceFileNew" in parser.updated_lines[0]

        # Reset for next test
        parser.inside_external_forcing = True
        parser.found_extforcefilenew = False
        parser.updated_lines = []

        # Test with ExtForceFileNew line
        parser._handle_external_forcing_section("ExtForceFileNew = old.ext")
        assert parser.found_extforcefilenew
        assert len(parser.updated_lines) == 1
        assert "test.ext" in parser.updated_lines[0]

        # Reset for next test
        parser.inside_external_forcing = True
        parser.found_extforcefilenew = False
        parser.updated_lines = []

        # Test with ExtForceFile line (should be skipped)
        parser._handle_external_forcing_section("ExtForceFile = old.ext")
        assert not parser.found_extforcefilenew
        assert len(parser.updated_lines) == 0

        # Test with regular line
        parser._handle_external_forcing_section("RegularLine = value")
        assert len(parser.updated_lines) == 1
        assert "RegularLine = value" in parser.updated_lines[0]

    def test_get_temperature_salinity_data(self):
        """Test the get_temperature_salinity_data method."""
        parser = MDUParser(self.file_path)
        data = parser.get_temperature_salinity_data()

        # Check that the returned data has the expected structure
        assert isinstance(data, dict)
        assert "file_path" in data
        assert "refdate" in data
        assert "temperature" in data
        assert "salinity" in data

        # Check that the file_path is correct
        assert data["file_path"] == Path(self.file_path)

        # Check that temperature and salinity are boolean values
        assert isinstance(data["temperature"], bool)
        assert isinstance(data["salinity"], (bool, int))

    def test_update_extforce_file_new(self):
        """Test the update_extforce_file_new method."""
        # Test with a file that has an external forcing section
        mdu_file = (
            "tests/data/input/dflowfm_individual_files/with_optional_sections.mdu"
        )
        parser = MDUParser(mdu_file)
        parser.new_forcing_file = "new_test.ext"

        # Update the file
        updated_lines = parser.update_extforce_file_new()

        # Check that the updated lines contain the new forcing file
        external_forcing_section = False
        found_extforcefilenew = False

        for line in updated_lines:
            if "[external forcing]" in line.lower():
                external_forcing_section = True
                continue

            if external_forcing_section and "extforcefilenew" in line.lower():
                found_extforcefilenew = True
                assert "new_test.ext" in line

            if external_forcing_section and line.strip().startswith("["):
                external_forcing_section = False

        assert found_extforcefilenew, "ExtForceFileNew entry not found in updated lines"

        # Test with a file that doesn't have an external forcing section
        # We'll create a mock file without an external forcing section
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch(
                "hydrolib.tools.extforce_convert.mdu_parser.MDUParser._read_file",
                return_value=[
                    "[general]\n",
                    "Name = Test\n",
                    "[geometry]\n",
                    "NetFile = test.nc\n",
                ],
            ),
            patch(
                "hydrolib.tools.extforce_convert.mdu_parser.MDUParser._load_with_fm_model",
                return_value={"geometry": {}},
            ),
            patch(
                "hydrolib.tools.extforce_convert.mdu_parser.MDUParser.get_temperature_salinity_data",
                return_value={},
            ),
        ):

            parser = MDUParser("dummy_path")
            parser.new_forcing_file = "new_test.ext"

            # Update the file
            updated_lines = parser.update_extforce_file_new()

            # Check that the updated lines are the same as the original (no external forcing section to update)
            assert len(updated_lines) == 4
            assert updated_lines == [
                "[general]\n",
                "Name = Test\n",
                "[geometry]\n",
                "NetFile = test.nc\n",
            ]

        # Test with a file that has an external forcing section but no ExtForceFileNew entry
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch(
                "hydrolib.tools.extforce_convert.mdu_parser.MDUParser._read_file",
                return_value=[
                    "[general]\n",
                    "Name = Test\n",
                    "[external forcing]\n",
                    "ExtForceFile = old.ext\n",
                    "[geometry]\n",
                    "NetFile = test.nc\n",
                ],
            ),
            patch(
                "hydrolib.tools.extforce_convert.mdu_parser.MDUParser._load_with_fm_model",
                return_value={"geometry": {}},
            ),
            patch(
                "hydrolib.tools.extforce_convert.mdu_parser.MDUParser.get_temperature_salinity_data",
                return_value={},
            ),
        ):

            parser = MDUParser("dummy_path")
            parser.new_forcing_file = "new_test.ext"

            # Update the file
            updated_lines = parser.update_extforce_file_new()

            # Check that the ExtForceFileNew entry was added and ExtForceFile was removed
            assert len(updated_lines) == 7
            assert updated_lines[0] == "[general]\n"
            assert updated_lines[1] == "Name = Test\n"
            assert updated_lines[2] == "[external forcing]\n"
            assert "ExtForceFileNew" in updated_lines[3]
            assert "new_test.ext" in updated_lines[3]
            assert updated_lines[4] == "\n"
            assert updated_lines[5] == "[geometry]\n"
