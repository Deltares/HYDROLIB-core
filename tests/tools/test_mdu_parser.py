import types
from copy import deepcopy
from pathlib import Path
from typing import Tuple
from unittest.mock import MagicMock, patch

import pytest

from hydrolib.tools.extforce_convert.mdu_parser import (
    FileStyleProperties,
    Line,
    MDUParser,
    Section,
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
    # assume that the number of new quantities in the new external forcing file is 1 to trigger the update
    num_quantities = 1
    updater.update_extforce_file_new(ext_file, num_quantities)
    assert updater.content[on_line[0]] == "[external forcing]\n"
    assert updater.content[on_line[1]] == expected_line
    # test the save mdu file function
    save_mdu_file(updater.content, new_mdu_file)
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

    @pytest.mark.unit
    def test_has_inifield_file(self):
        """Test the has_inifield_file method."""

        parser = MagicMock(spec=MDUParser)
        parser.has_field = types.MethodType(MDUParser.has_field, parser)
        parser.find_keyword_lines = types.MethodType(
            MDUParser.find_keyword_lines, parser
        )
        parser.content = [
            "[general]\n",
            "Name = Test\n",
            "[geometry]\n",
            "IniFieldFile = new-inifield-file.ini\n",
        ]
        # Test with a file that has an inifield file
        assert MDUParser.has_inifield_file(parser) is True

        # Test with a file that does not have an inifield file
        parser.content = [
            "[general]\n",
            "Name = Test\n",
            "[geometry]\n",
            "NetFile = test.nc\n",
        ]
        assert MDUParser.has_inifield_file(parser) is False

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

        new_extforce_file = "new_test.ext"
        # assume that the number of new quantities in the new external forcing file is 1 to trigger the update
        num_quantities = 1
        parser.update_extforce_file_new(new_extforce_file, num_quantities)

        # Check that the updated content contain the new forcing file
        ind = parser.find_keyword_lines("extforcefilenew")
        assert ind is not None, "ExtForceFileNew keyword not found in the content"
        line = parser.content[ind]
        _, new_file = line.split("=")
        assert new_file.strip() == new_extforce_file

        # Test with a file that has an external forcing section but no ExtForceFileNew entry
        parser.content = [
            "[general]\n",  # 0
            "Name = Test\n",  # 1
            "[external forcing]\n",  # 2
            "ExtForceFile = old.ext\n",  # 3
            "[geometry]\n",  # 4
            "NetFile = test.nc\n",  # 5
        ]

        # assume that the number of new quantities in the new external forcing file is 1 to trigger the update
        num_quantities = 1
        MDUParser.update_extforce_file_new(parser, new_extforce_file, num_quantities)

        updated_lines = parser.content
        # Check that the ExtForceFileNew entry was added and ExtForceFile was removed
        assert len(updated_lines) == 6
        assert updated_lines[0] == "[general]\n"
        assert updated_lines[1] == "Name = Test\n"
        assert updated_lines[2] == "[external forcing]\n"
        assert "ExtForceFileNew" in updated_lines[3]
        assert "new_test.ext" in updated_lines[3]
        assert updated_lines[4] == "[geometry]\n"
        assert updated_lines[5] == "NetFile = test.nc\n"


class TestUpdateInifieldFile:
    file_path = "tests/data/input/dflowfm_individual_files/mdu/sp.mdu"

    @pytest.mark.unit
    def test_update_inifield_file_exists(self):
        """Test the update_inifield_file method. where the inifield file already exists. with empty value"""
        content = [
            "[general]\n",
            "Name = Test\n",
            "[geometry]\n",
            "IniFieldFile =     #some comments here\n",
        ]

        parser = MagicMock(spec=MDUParser)
        parser.update_inifield_file = types.MethodType(
            MDUParser.update_inifield_file, parser
        )
        parser.file_style_properties = FileStyleProperties(content)
        parser.find_keyword_lines = types.MethodType(
            MDUParser.find_keyword_lines, parser
        )
        parser.find_section_bounds = types.MethodType(MDUParser.get_section, parser)
        parser.has_field = types.MethodType(MDUParser.has_field, parser)
        parser.update_file_entry = types.MethodType(MDUParser.update_file_entry, parser)
        parser.insert_line = types.MethodType(MDUParser.insert_line, parser)
        parser.content = deepcopy(content)
        # Test with a file that has an inifield file
        MDUParser.update_inifield_file(parser, "new-inifield-file.ini")
        old_index = content.index("IniFieldFile =     #some comments here\n")
        assert (
            parser.content[old_index]
            == "IniFieldFile= new-inifield-file.ini #some comments here\n"
        )

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
        section_bounds = parser.get_section("geometry")
        ind = section_bounds.last_key_value_line_index
        assert (
            parser._content[ind]
            == "    IniFieldFile                        = new-inifield-file.ini\n"
        )

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
        section_bounds = parser.get_section("geometry")
        ind = section_bounds.last_key_value_line_index
        assert (
            parser._content[ind]
            == "    IniFieldFile                        = new-inifield-file.ini\n"
        )


class TestLocate:

    @pytest.mark.unit
    def test_same_position_all_lines(self):
        # All equal signs at the same position
        content = [
            "Param1    = value1\n",
            "Param2    = value2\n",
            "Param3    = value3\n",
        ]

        pos = FileStyleProperties._locate(content, "=")
        assert pos == content[0].find("=")

    @pytest.mark.unit
    def test_different_position(self):
        # Equal signs at different positions, most common should be chosen
        content = [
            "A = 1\n",  # pos 2
            "BB   = 2\n",  # pos 4
            "CCC = 3\n",  # pos 4
            "DDDD = 4\n",  # pos 5
            "E = 5\n",  # pos 2
            "F = 6\n",  # pos 2
        ]
        pos = FileStyleProperties._locate(content, "=")
        # pos 2 appears 3 times, pos 4 appears 2 times, pos 5 once
        assert pos == 2

    @pytest.mark.unit
    def test_lines_with_decorative_equal_sign(self):
        # Lines with comments and equal signs
        content = [
            "# This is a comment ==========\n",
            "Param = value # comment\n",
            "Another = something\n",
        ]
        pos = FileStyleProperties._locate(content, "=")
        assert pos == content[1].find("=")

    @pytest.mark.unit
    def test_no_equal_sign(self):
        # No equal signs at all
        content = [
            "No equals here\n",
            "Still no equals\n",
        ]

        pos = FileStyleProperties._locate(content, "=")
        assert pos is None

    @pytest.mark.unit
    def test_all_equal_sign_are_commented(self):
        # Only commented lines with equal signs (should be ignored)
        content = [
            "# Param = value\n",
            "# Another = something\n",
        ]

        pos = FileStyleProperties._locate(content, "=")
        assert pos is None


class TestGetLeadingSpaces:
    """
    Unit tests for FileStyleProperties._get_leading_spaces static method.

    Scenarios covered:
        - All lines have the same number of leading spaces.
        - Lines have varying numbers of leading spaces (most common is chosen).
        - Lines with no leading spaces.
        - Lines with only tabs as leading whitespace.
        - Lines with mixed tabs and spaces.
        - All lines are empty or whitespace only.
        - All lines are commented out.
        - Empty content.
    """

    @pytest.mark.unit
    def test_all_lines_same_leading_spaces(self):
        """All lines have the same number of leading spaces."""
        content = [
            "    Param1 = value1\n",
            "    Param2 = value2\n",
            "    Param3 = value3\n",
        ]
        result = FileStyleProperties._get_leading_spaces(content)
        assert result == 4

    @pytest.mark.unit
    def test_varying_leading_spaces(self):
        """Lines have varying numbers of leading spaces; most common is chosen."""
        content = [
            "  Param1 = value1\n",  # 2 spaces
            "    Param2 = value2\n",  # 4 spaces
            "  Param3 = value3\n",  # 2 spaces
            "Param4 = value4\n",  # 0 spaces
        ]
        result = FileStyleProperties._get_leading_spaces(content)
        assert result == 2

    @pytest.mark.unit
    def test_no_leading_spaces(self):
        """Lines with no leading spaces."""
        content = [
            "Param1 = value1\n",
            "Param2 = value2\n",
            "Param3 = value3\n",
        ]
        result = FileStyleProperties._get_leading_spaces(content)
        assert result == 0

    @pytest.mark.unit
    def test_leading_tabs_only(self):
        """Lines with only tabs as leading whitespace (tabs count as 1 char each).
        Notes:
            - the tab is counted as 1 leading space.
            - the following content has 1 tab, 2 tabs, and 0 spaces.
            - the most common leading space is the fist most frequent spacing.
            - in this case it is 1 tab, and two tabs, but one tab is at the top of the list, so it will be used.
        """
        content = [
            "\tParam1 = value1\n",
            "\t\tParam2 = value2\n",
            "Param3 = value3\n",
        ]
        result = FileStyleProperties._get_leading_spaces(content)
        assert result == 1  # 0 is most common (1 tab, 2 tabs, 0 spaces)

    @pytest.mark.unit
    def test_mixed_tabs_and_spaces(self):
        """Lines with mixed tabs and spaces as leading whitespace.

        Notes:
            - the following content has [1 space + i tab, 1 tab + 1 space, 2 spaces, no spaces], so the most common
            leading space is 2 spaces.
        """
        content = [
            " \tParam1 = value1\n",  # 1 space, 1 tab
            "\t Param2 = value2\n",  # 1 tab, 1 space
            "  Param3 = value3\n",  # 2 spaces
            "Param4 = value4\n",  # 0 spaces
        ]
        result = FileStyleProperties._get_leading_spaces(content)
        assert result == 2

    @pytest.mark.unit
    def test_all_empty_or_whitespace_lines(self):
        """All lines are empty or whitespace only."""
        content = [
            "",
            "   ",
            "\t",
        ]
        result = FileStyleProperties._get_leading_spaces(content)
        assert result == 0

    @pytest.mark.unit
    def test_all_commented_lines(self):
        """All lines are commented out; leading spaces return None."""
        content = [
            "  # Comment 1\n",
            "    # Comment 2\n",
            "# Comment 3\n",
        ]
        result = FileStyleProperties._get_leading_spaces(content)
        assert result is None

    @pytest.mark.unit
    def test_empty_content(self):
        """Empty content should return None."""
        content = []
        result = FileStyleProperties._get_leading_spaces(content)

        assert result is None


class TestFileStyleProperties:
    """
    Integration tests for the FileStyleProperties class.

    These tests instantiate FileStyleProperties and check that both leading_spaces and
    equal_sign_position are set correctly together, covering realistic scenarios.
    """

    def test_standard_content(self):
        """Integration: Consistent leading spaces and equal sign position."""
        content = [
            "Param1    = value1\n",
            "Param2    = value2\n",
            "Param3    = value3\n",
        ]
        style = FileStyleProperties(content)
        assert style.leading_spaces == 0
        assert style.equal_sign_position == 10
        assert style.comments_position is None

    def test_varying_equal_sign_positions(self):
        """Integration: Varying equal sign positions, most common is chosen."""
        content = [
            "A = 1\n",  # pos 2
            "BB   = 2\n",  # pos 4
            "CCC = 3\n",  # pos 4
            "DDDD = 4\n",  # pos 5
            "E = 5\n",  # pos 2
            "F = 6\n",  # pos 2
        ]
        style = FileStyleProperties(content)
        assert style.leading_spaces == 0
        assert style.equal_sign_position == 2
        assert style.comments_position is None

    def test_varying_leading_spaces(self):
        """Integration: Varying leading spaces, most common is chosen."""
        content = [
            "  Param1 = value1\n",  # 2 spaces, position 8
            "    Param2 = value2\n",  # 4 spaces, position 11
            "  Param3 = value3\n",  # 2 spaces, position 9
            "Param4 = value4\n",  # 0 spaces, position 7
        ]
        style = FileStyleProperties(content)
        assert style.leading_spaces == 2
        assert style.equal_sign_position == 9

    def test_no_equal_signs(self):
        """Integration: No equal signs, equal_sign_position should be None."""
        content = [
            "No equals here\n",
            "Still no equals\n",
        ]
        style = FileStyleProperties(content)
        assert style.leading_spaces == 0
        assert style.equal_sign_position is None

    def test_all_lines_commented(self):
        """Integration: All lines commented out; equal_sign_position should be None."""
        content = [
            "# Param1 = value1\n",
            "# Param2 = value2\n",
        ]
        style = FileStyleProperties(content)
        assert style.leading_spaces is None
        assert style.equal_sign_position is None

    def test_empty_content(self):
        """Integration: Empty content; both properties should be None."""
        content = []
        style = FileStyleProperties(content)
        assert style.leading_spaces is None
        assert style.equal_sign_position is None

    def test_leading_spaces_with_tabs(self):
        """Integration: Lines with tabs as leading whitespace."""
        content = [
            "\tParam1 = value1\n",
            "\t\tParam2 = value2\n",
            "Param3 = value3\n",
        ]
        style = FileStyleProperties(content)
        # Tabs count as 1 char each, so most common is 0 (no leading spaces)
        assert style.leading_spaces == 1
        assert style.equal_sign_position == 8

    def test_lines_with_comments(self):
        """Integration: Lines with comments; comments_position should be set."""
        content = [
            "Param1 = value1 # comment1\n",
            "Param2 = value2 # comment2\n",
            "Param3 = value3 # comment3\n",
        ]
        style = FileStyleProperties(content)
        assert style.leading_spaces == 0
        assert style.equal_sign_position == 7
        assert style.comments_position == content[0].find("#")


class TestGetCommentsPosition:
    """
    Unit tests for FileStyleProperties._get_comments_position method.

    Scenarios covered:
        - All lines have comments at the same position.
        - Lines have comments at different positions (most common is chosen).
        - Lines with no comments.
        - Lines with only commented lines.
        - Lines with both commented and non-commented lines.
        - Empty content.
        - Lines with multiple '#' characters (first occurrence is used).
    """

    @pytest.mark.unit
    def test_all_lines_same_comment_position(self):
        """Test when all lines have a comment at the same position (should return that position)."""
        content = [
            "Param1 = value1 # comment1\n",
            "Param2 = value2 # comment2\n",
            "Param3 = value3 # comment3\n",
        ]
        result = FileStyleProperties._get_comments_position(
            FileStyleProperties, content
        )
        assert result == content[0].find("#")

    @pytest.mark.unit
    def test_varying_comment_positions(self):
        """Test when comments appear at different positions; most common is chosen."""
        content = [
            "A = 1 # comment\n",  # pos 6
            "BB   = 2 # comment\n",  # pos 9
            "CCC = 3 # comment\n",  # pos 8
            "DDDD = 4 # comment\n",  # pos 9
            "E = 5 # comment\n",  # pos 6
            "F = 6 # comment\n",  # pos 6
        ]
        result = FileStyleProperties._get_comments_position(
            FileStyleProperties, content
        )
        # pos 6 appears 3 times, pos 9 appears 2 times, pos 8 once
        assert result == 6

    @pytest.mark.unit
    def test_no_comments(self):
        """Test when no lines have comments (should return None)."""
        content = [
            "Param1 = value1\n",
            "Param2 = value2\n",
            "Param3 = value3\n",
        ]
        result = FileStyleProperties._get_comments_position(
            FileStyleProperties, content
        )
        assert result is None

    @pytest.mark.unit
    def test_all_commented_lines(self):
        """Test when all lines are commented out (should return the most common position of '#')."""
        content = [
            "# Comment 1\n",
            "    # Comment 2\n",
            "# Comment 3\n",
        ]
        result = FileStyleProperties._get_comments_position(
            FileStyleProperties, content
        )
        # Most common is position 0
        assert result is None

    @pytest.mark.unit
    def test_commented_and_non_commented_lines(self):
        """Test with a mix of commented and non-commented lines (should return most common position among all)."""
        content = [
            "Param1 = value1 # comment1\n",
            "# Only comment\n",
            "Param2 = value2 # comment2\n",
            "    # Indented comment\n",
        ]
        result = FileStyleProperties._get_comments_position(
            FileStyleProperties, content
        )
        # Most common is position 0 (for indented and non-indented comments)
        assert result == content[0].find("#")

    @pytest.mark.unit
    def test_empty_content(self):
        """Test with empty content (should return None)."""
        content = []
        result = FileStyleProperties._get_comments_position(
            FileStyleProperties, content
        )
        assert result is None

    @pytest.mark.unit
    def test_multiple_hashes_in_line(self):
        """Test when a line contains multiple '#' characters (should use the first occurrence)."""
        content = [
            "Param1 = value1 # comment # extra\n",
            "Param2 = value2 # another # more\n",
        ]
        result = FileStyleProperties._get_comments_position(
            FileStyleProperties, content
        )
        assert result == content[0].find("#")


class TestLine:
    """
    Unit tests for the Line class in mdu_parser.py.

    Covers:
        - Comment extraction and position
        - Section header detection
        - Key-value parsing
        - Leading spaces calculation
        - Equal sign alignment
        - Edge cases (empty, whitespace, tabs, only comments, missing key/value)
    """

    @pytest.mark.unit
    def test_with_comment(self):
        """Test extracting comment and its position from a line with a comment."""
        line = Line("Param = value # comment here")
        assert line.comment_position == line.content.find("#")
        assert line.comments == "# comment here"

    @pytest.mark.unit
    def test_without_comment(self):
        """Test extracting comment from a line without a comment."""
        line = Line("Param = value")
        assert line.comment_position is None
        assert line.comments == ""

    @pytest.mark.unit
    def test_is_comment_true(self):
        """Test is_comment returns True for comment lines."""

        line = Line("   # This is a comment")
        assert line.is_comment() is True

    @pytest.mark.unit
    def test_is_comment_false(self):
        """Test is_comment returns False for non-comment lines."""

        line = Line("Param = value")
        assert line.is_comment() is False

    @pytest.mark.unit
    def test_is_section_header_true(self):
        """Test is_section_header returns True for section header lines."""
        line = Line("[general]")
        assert line.is_section_header() is True

    @pytest.mark.unit
    def test_is_section_header_false(self):
        """Test is_section_header returns False for non-section header lines."""
        line = Line("Param = value")
        assert line.is_section_header() is False

    @pytest.mark.unit
    def test_get_key_value_standard(self):
        """Test get_key_value parses key, value, and equal sign position for standard lines."""
        line = Line("Param = value")
        key, value = line.get_key_value()
        assert key == "Param"
        assert value == "value"
        assert line.equal_sign_position == line.content.find("=")

    @pytest.mark.unit
    def test_get_key_value_no_equal_sign(self):
        """Test get_key_value raises ValueError if no equal sign is present."""
        with pytest.raises(ValueError):
            line = Line("Param value")

    @pytest.mark.unit
    def test_get_key_value_comment_or_section(self):
        """Test get_key_value returns None for key/value/pos for comment or section header lines."""
        comment_line = Line("# Just a comment")
        section_line = Line("[general]")
        assert comment_line.get_key_value() == (None, None)
        assert section_line.get_key_value() == (None, None)

    @pytest.mark.unit
    def test_get_leading_spaces(self):
        """Test get_leading_spaces returns correct number of leading spaces."""
        line = Line("   Param = value")
        assert line.get_leading_spaces() == 3

    @pytest.mark.unit
    def test_get_leading_spaces_tabs(self):
        """Test get_leading_spaces with tabs (should count tabs as 1 char each)."""
        line = Line("\t\tParam = value")
        assert line.get_leading_spaces() == 2

    @pytest.mark.unit
    def test_get_leading_spaces_empty(self):
        """Test get_leading_spaces for empty line returns 0."""
        line = Line("")
        assert line.get_leading_spaces() == 0

    @pytest.mark.unit
    def test_recenter_equal_sign_default(self):
        """Test recenter_equal_sign aligns the equal sign at detected position."""
        line = Line("Param=val")
        line.recenter_equal_sign()
        # Should align at detected position
        assert line.content.startswith("Param=")

    @pytest.mark.unit
    def test_recenter_equal_sign_custom_position(self):
        """Test recenter_equal_sign aligns the equal sign at a custom position."""
        line = Line("Param=val")
        line.recenter_equal_sign(equal_sign_position=10)
        assert line.content.startswith("Param     = val")

    @pytest.mark.unit
    def test_recenter_equal_sign_with_leading_spaces(self):
        """Test recenter_equal_sign with custom leading spaces."""
        line = Line("Param=val")
        line.recenter_equal_sign(leading_spaces=2, equal_sign_position=8)
        assert line.content.startswith("  Param = val")

    @pytest.mark.unit
    def test_recenter_equal_sign_no_key_value(self):
        """Test recenter_equal_sign raises ValueError if no key/value present."""
        line = Line("# Just a comment")
        with pytest.raises(AttributeError):
            line.recenter_equal_sign()

    @pytest.mark.unit
    def test_recenter_equal_sign_empty_value(self):
        """Test recenter_equal_sign with empty value."""
        line = Line("Param=")
        line.recenter_equal_sign(equal_sign_position=8)
        assert line.content.startswith("Param   = ")


class TestLineRecenterComments:
    """
    Unit tests for the Line.recenter_comments method.

    Scenarios covered:
        - Line with a comment at a standard position.
        - Line with a comment at a custom target position.
        - Line without a comment (should return original line).
        - Line with only a comment.
        - Empty line.
        - Line with multiple '#' characters (should use the first occurrence).
    """

    @pytest.mark.unit
    def test_standard_comment_position(self):
        """
        Test recenter_comments with a line containing a comment at the default position.

        Example:
            Line: "Param = value # comment"
            Should align comment at its original position.
        """
        line = Line("Param = value # comment")
        line.recenter_comments()
        assert line.content.startswith("Param = value")
        assert line.content.endswith("# comment")

    @pytest.mark.unit
    def test_custom_comment_position(self):
        """
        Test recenter_comments with a custom target position for the comment.

        Example:
            Line: "Param = value # comment"
            Custom position: 30
            Should align comment at column 30.
        """
        line = Line("Param = value # comment")
        line.recenter_comments(comments_position=30)
        # The comment should start at column 30
        assert line.content[30:].startswith("# comment")

    @pytest.mark.unit
    def test_no_comment(self):
        """
        Test recenter_comments with a line that has no comment (should return original line).

        Example:
            Line: "Param = value"
            Should return the original line.
        """
        line = Line("Param = value")
        line.recenter_comments()
        assert line.content == "Param = value"

    @pytest.mark.unit
    def test_only_comment_line(self):
        """
        Test recenter_comments with a line that is only a comment.

        Example:
            Line: "# just a comment"
            Should return the original line.
        """
        line = Line("# just a comment")
        line.recenter_comments()
        assert line.content == "# just a comment"

    @pytest.mark.unit
    def test_empty_line(self):
        """
        Test recenter_comments with an empty line (should return empty string).

        Example:
            Line: ""
            Should return "".
        """
        line = Line("")
        line.recenter_comments()
        assert line.content == ""

    @pytest.mark.unit
    def test_multiple_hashes(self):
        """
        Test recenter_comments with a line containing multiple '#' characters (should use the first occurrence).

        Example:
            Line: "Param = value # comment # extra"
            Should align at the first '#'.
        """
        line = Line("Param = value # comment # extra")
        line.recenter_comments(comments_position=25)
        # The first comment should start at column 25
        assert line.content[25:].startswith("# comment # extra")


class TestLineFromKeyValue:
    """
    Unit tests for Line.from_key_value classmethod.

    Scenarios covered:
        - Standard key/value with default alignment.
        - Custom equal sign position and leading spaces.
        - Empty key or value.
        - Negative or invalid positions.
        - Non-string key/value.
        - Adding a comment.
    """

    @pytest.mark.unit
    def test_standard_key_value(self):
        """
        Test standard key/value with default alignment.

        Example:
            Line.from_key_value('Param', 'value') -> 'Param= value'
        """
        line = Line.from_key_value("Param", "value")
        assert line.content == "Param = value\n"

    @pytest.mark.unit
    def test_custom_alignment(self):
        """
        Test custom equal sign position and leading spaces.

        Example:
            Line.from_key_value('Param', 'value', equal_sign_position=10, leading_spaces=2) -> '  Param    = value'
        """
        line = Line.from_key_value(
            "Param", "value", equal_sign_position=10, leading_spaces=2
        )
        assert line.content == "  Param   = value\n"

    @pytest.mark.unit
    def test_empty_key(self):
        """
        Test with empty key and non-empty value (should succeed).

        Example:
            Line.from_key_value('', 'value') -> '= value'
        """
        with pytest.raises(ValueError):
            Line.from_key_value("", "value")

    @pytest.mark.unit
    def test_empty_value(self):
        """
        Test with non-empty key and empty value (should succeed).

        Example:
            Line.from_key_value('Param', '') -> 'Param= '
        """
        line = Line.from_key_value("Param", "")
        assert line.content == "Param = \n"

    @pytest.mark.unit
    def test_empty_key_and_value(self):
        """
        Test with both key and value empty (should raise ValueError).
        """
        with pytest.raises(ValueError):
            Line.from_key_value("", "")

    @pytest.mark.unit
    def test_negative_equal_sign_position(self):
        """
        Test with negative equal_sign_position (should raise ValueError).
        """
        with pytest.raises(ValueError):
            Line.from_key_value("Param", "value", equal_sign_position=-1)

    @pytest.mark.unit
    def test_negative_leading_spaces(self):
        """
        Test with negative leading_spaces (should raise ValueError).
        """
        with pytest.raises(ValueError):
            Line.from_key_value("Param", "value", leading_spaces=-2)

    @pytest.mark.unit
    def test_non_string_key(self):
        """
        Test with non-string key (should raise ValueError).
        """
        with pytest.raises(ValueError):
            Line.from_key_value(123, "value")

    @pytest.mark.unit
    def test_add_comment(self):
        """
        Test adding a comment to the line.
        Example:
            Line.from_key_value('Param', 'value', comment='# my comment') -> 'Param= value # my comment'
        """
        line = Line.from_key_value("Param", "value", comment="# my comment")
        assert line.content == "Param = value # my comment\n"


class TestLineUpdateValue:
    """
    Unit tests for the Line.update_value method.

    Scenarios covered:
        - Standard key/value update with preserved formatting.
        - Update with comment preserved.
        - Update on line with leading spaces and custom equal sign position.
        - Update on line with empty value.
        - Update on line with only whitespace.
        - Update on comment line (should raise ValueError).
        - Update on section header line (should raise ValueError).
        - Update on empty line (should raise ValueError).
    """

    @pytest.mark.unit
    def test_update_standard_value(self):
        """Update value for a standard key-value line, formatting is preserved."""
        line = Line("Param = oldvalue")
        updated = line.update_value("newvalue")
        assert updated.content == "Param = newvalue\n"

    @pytest.mark.unit
    def test_update_preserves_comment(self):
        """Update value for a line with a comment, comment is preserved."""
        line = Line("Param = oldvalue # comment")
        updated = line.update_value("newvalue")
        assert updated.content == "Param = newvalue # comment\n"

    @pytest.mark.unit
    def test_update_preserves_leading_spaces_and_equal_sign(self):
        """Update value for a line with leading spaces and custom equal sign position."""
        line = Line("   Param    = oldvalue # comment")
        updated = line.update_value("newvalue")
        # Leading spaces and equal sign alignment should be preserved
        assert updated.content.startswith("   Param    = newvalue")
        assert updated.content.endswith("# comment\n")

    @pytest.mark.unit
    def test_update_empty_value(self):
        """Update value for a line with an empty value."""
        line = Line("Param = ")
        updated = line.update_value("newvalue")
        assert updated.content == "Param = newvalue\n"

    @pytest.mark.unit
    def test_update_on_whitespace_line(self):
        """Update value for a line with only whitespace (should raise ValueError)."""
        line = Line("   ")
        with pytest.raises(ValueError):
            line.update_value("newvalue")

    @pytest.mark.unit
    def test_update_on_comment_line(self):
        """Update value for a comment line (should raise ValueError)."""
        line = Line("# just a comment")
        with pytest.raises(ValueError):
            line.update_value("newvalue")

    @pytest.mark.unit
    def test_update_on_section_header(self):
        """Update value for a section header line (should raise ValueError)."""
        line = Line("[general]")
        with pytest.raises(ValueError):
            line.update_value("newvalue")

    @pytest.mark.unit
    def test_update_on_empty_line(self):
        """Update value for an empty line (should raise ValueError)."""
        line = Line("")
        with pytest.raises(ValueError):
            line.update_value("newvalue")


class TestSection:
    """
    Unit tests for the Section class in mdu_parser.py.

    Scenarios covered:
        - Section at the end of file (with/without trailing empty/comment lines).
        - Section with only header.
        - Section with only comments/empty lines after header.
        - Section with no key-value lines.
        - Section with mixed content (key-value, comments, empty lines).
        - Section surrounded by decorative lines.
        - Section name case sensitivity.
        - Malformed section headers.
        - Multiple sections with same name (should pick first occurrence).
        - Section at the start of file.
        - Empty file.
    """

    file_path = "tests/data/input/dflowfm_individual_files/mdu/sp.mdu"

    def test_section_at_end_of_file(self):
        """Section is last in file, with trailing empty/comment lines."""
        content = [
            "[geometry]\n",
            "NetFile = test.nc\n",
            "[output]\n",
            "OutputFile = out.nc\n",
            "\n",
            "# comment\n",
            "\n",
        ]
        section = Section("output", content)
        assert section.start == 2
        assert section.end == 3 + 3  # last line index
        assert section.non_key_value_lines_at_end == 3
        assert section.last_key_value_line_index == 3

    def test_section_with_only_header(self):
        """Section contains only the header and no content."""
        content = [
            "[geometry]\n",  # 0
            "[output]\n",  # 1
            "[numerics]\n",  # 2
        ]
        section = Section("output", content)
        assert section.start == 1
        assert section.end == 1
        assert section.non_key_value_lines_at_end == 0
        assert section.last_key_value_line_index == 1

    def test_section_with_only_comments_and_empty_lines(self):
        """Section contains only comments and empty lines after header."""
        content = [
            "[geometry]\n",  # 0
            "[output]\n",  # 1
            "# comment\n",  # 2
            "\n",  # 3
            "\n",  # 4
            "[numerics]\n",  # 5
        ]
        section = Section("output", content)
        assert section.start == 1
        assert section.end == 4
        assert section.non_key_value_lines_at_end == 3
        assert section.last_key_value_line_index == 1

    def test_section_with_no_key_value_lines(self):
        """Section contains no key-value lines, only comments/empty lines."""
        content = [
            "[output]\n",  # 0
            "# comment\n",  # 1
            "\n",  # 2
        ]
        section = Section("output", content)
        assert section.start == 0
        assert section.end == 2
        assert section.non_key_value_lines_at_end == 2
        assert section.last_key_value_line_index == 0

    def test_section_with_mixed_content(self):
        """Section contains key-value lines, comments, and empty lines in various orders."""
        content = [
            "[output]\n",  # 0
            "OutputFile = out.nc\n",  # 1
            "# comment\n",  # 2
            "\n",  # 3
            "AnotherKey = 1\n",  # 4
            "\n",  # 5
            "# another comment\n",  # 6
        ]
        section = Section("output", content)
        assert section.start == 0
        assert section.end == 6
        assert section.non_key_value_lines_at_end == 2
        assert section.last_key_value_line_index == 4

    def test_section_with_decorative_lines(self):
        """Section surrounded by decorative lines (e.g., lines of #====)."""
        content = [
            "#================\n",  # 0
            "[output]\n",  # 1
            "OutputFile = out.nc\n",  # 2
            "#================\n",  # 3
        ]
        section = Section("output", content)
        assert section.start == 1
        assert section.end == 3
        assert section.non_key_value_lines_at_end == 1
        assert section.last_key_value_line_index == 2

    def test_section_name_case_insensitivity(self):
        """Section header with different cases (e.g., [GEOMETRY] vs [geometry])."""
        content = [
            "[GEOMETRY]\n",  # 0
            "NetFile = test.nc\n",  # 1
        ]
        section = Section("geometry", content)
        assert section.start == 0
        assert section.end == 1
        assert section.last_key_value_line_index == 1

    def test_malformed_section_headers(self):
        """Section headers that are not properly closed or opened are ignored."""
        content = [
            "[geometry\n",  # malformed         # 0
            "[output]\n",  # 1
            "OutputFile = out.nc\n",  # 2
            "output]\n",  # malformed           # 3
            "[numerics]\n",  # 4
        ]
        with pytest.raises(ValueError):
            Section("output", content)

    def test_multiple_sections_with_same_name(self):
        """Multiple sections with the same name (should pick the first occurrence)."""
        content = [
            "[output]\n",  # 0
            "OutputFile = out1.nc\n",  # 1
            "[geometry]\n",  # 2
            "[output]\n",  # 3
            "OutputFile = out2.nc\n",  # 4
        ]
        section = Section("output", content)
        assert section.start == 0
        assert section.end == 1
        assert section.last_key_value_line_index == 1

    def test_section_at_start_of_file(self):
        """Section is the very first lines in the file."""
        content = [
            "[output]\n",  # 0
            "OutputFile = out.nc\n",  # 1
            "[geometry]\n",  # 2
        ]
        section = Section("output", content)
        assert section.start == 0
        assert section.end == 1
        assert section.last_key_value_line_index == 1

    def test_empty_file(self):
        """Empty file should result in None for start and end."""
        content = []
        section = Section("output", content)
        assert section.start is None
        assert section.end is None

    def test_find_section_bounds(self):
        content = [
            "[geometry]\n",
            "    NetFile                             = sp_net.nc                          # *_net.nc\n",
            "    unknown_geometry                    = 5                                   # any comment\n",
            "    WaterLevIniFile                     =                                    # Initial water levels sample file *.xyz\n",
            "    LandBoundaryFile                    =                                    # Only for plotting\n",
            "    ThinDamFile                         =                                    # *_thd.pli, Polyline(s) for tracing thin dams.\n",
            "    FixedWeirFile                       =                                    # *_tdk.pli, Polyline(s) x,y,z, z = fixed weir top levels\n",
            "    ProflocFile                         =                                    # *_proflocation.xyz)    x,y,z, z = profile refnumber\n",
            "    ProfdefFile                         =                                    # *_profdefinition.def) definition for all profile nrs\n",
            "    WaterLevIni                         = 0.56                               # Initial water level\n",
            "\n",
            "#============================================\n",
            "#============================================\n",
            "[numerics]\n",
            "    any_key                             = any_value                          # any comment\n",
        ]
        section_bounds = Section("geometry", content)

        assert content[section_bounds.start] == "[geometry]\n"
        assert content[section_bounds.end] == content[12]
        last_line = section_bounds.last_key_value_line_index
        assert content[last_line] == content[9]

        # Test for a non-existing section
        non_existing_section = Section("non-existing", content)
        assert non_existing_section.start is None
        assert non_existing_section.end is None
