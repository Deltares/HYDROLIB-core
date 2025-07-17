"""MDU Parser."""

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple

from hydrolib.core.base.file_manager import PathOrStr
from hydrolib.core.dflowfm.mdu.models import FMModel, Physics, Time
from hydrolib.tools.extforce_convert.utils import IgnoreUnknownKeyWordClass, backup_file

STRUCTURE_FILE_LINE = "StructureFile"
INIFIELD_FILE_LINE = "IniFieldFile"


@dataclass
class ExternalForcingBlock:
    extforcefile: Union[Path, str]
    extforcefilenew: Optional[Union[Path, str]] = field(default=None)
    comments: Optional[List[str]] = field(default=None)
    _header: Optional = "[external forcing]"
    root_dir: Optional[Path] = field(default=None)

    def __init__(self, **kwargs):
        valid_keys = {"extforcefile", "extforcefilenew", "comments", "_header"}
        for key in valid_keys:
            setattr(self, key, kwargs.get(key, None))

    @property
    def extforce_file(self) -> Path:
        old_ext_force_file = self.extforcefile
        if old_ext_force_file is None:
            raise ValueError(
                "An old formatted external forcing file (.ext) could not be found in the mdu file.\n"
                "Conversion is not possible or may not be necessary."
            )
        else:
            old_ext_force_file = Path(old_ext_force_file)

        return old_ext_force_file

    def get_new_extforce_file(self, ext_file: Optional[Path] = None) -> Path:
        """Get the new external forcing file path.

        Notes:
            - If the `extforcefilenew` exists in the MDU file, it will be used.
            - If it does not exist, it will create a new file with the old extforce file name with a "-new" suffix.
            - If an `ext_file` is provided, it will be used as the new extforce file.

        Args:
            ext_file (Path):
                Optional path to an external forcing file to use as the new extforce file.

        Returns:
            Path:
                Path to the new external forcing file.
        """
        _extforce_file_new = (
            Path(self.extforcefilenew) if self.extforcefilenew else None
        )

        if _extforce_file_new:
            # if the extforce_file_new exist in the MDU file, we use it
            ext_file = (self.root_dir / _extforce_file_new).resolve()
        else:
            # if the extforce_file_new does not exist in the MDU file
            if ext_file is None:
                # if no ext_file is provided, we use the old extforce file name to create the new extforce file
                ext_file = self.root_dir / self.extforce_file.with_stem(
                    self.extforce_file.stem + "-new"
                )
            else:
                # if an ext_file is provided, we use it
                ext_file = Path(ext_file).resolve()

        return ext_file


@dataclass
class FileStyleProperties:
    """
    Detects and stores style properties of an MDU file, such as leading spaces and equal sign alignment.

    This class analyzes the content of an MDU file to determine the most common number of leading spaces
    and the most common position of the equal sign for key-value pairs. These properties can be used to
    preserve formatting when updating or generating MDU files.

    Attributes:
        leading_spaces (int): The most common number of leading spaces at the start of lines.
        equal_sign_position (int): The most common position (column index) of the equal sign in key-value lines.

    Example:
        ```python
        >>> content = [
        ...     'Param1    = value1',
        ...     'Param2    = value2',
        ...     'Param3    = value3',
        ... ]
        >>> style = FileStyleProperties(content)
        >>> style.leading_spaces
        0
        >>> style.equal_sign_position
        9
        ```
    """

    leading_spaces: int = 0
    equal_sign_position: int = 0
    comments_position: Optional[int] = None

    def __init__(self, content: List[str]):
        """
        Initialize the FileStyleProperties.

        Args:
            content (List[str]): List of strings representing the content of the MDU file.
        """
        self.leading_spaces = self._get_leading_spaces(content)
        self.equal_sign_position = self._get_equal_sign_position(content)
        self.comments_position = self._get_comments_position(content)

    @staticmethod
    def _get_equal_sign_position(content: List[str]) -> Optional[int]:
        """
        Get the most common position (column index) of the equal sign in the MDU file.

        Args:
            content (List[str]): List of strings representing the content of the MDU file.

        Returns:
            Optional[int]: The most common index of the equal sign, or None if not found.

        Example:
            ```python
            >>> FileStyleProperties._get_equal_sign_position(
            ...     ['A = 1', 'BB   = 2', 'CCC = 3', '# Comment = 4']
            ... )
            2
            ```
        """
        position = FileStyleProperties._locate(content, "=")

        return position

    def _get_comments_position(self, content: List[str]) -> Optional[int]:
        """
        Get the most common position (column index) of the comment character in the MDU file.

        Args:
            content (List[str]):
                List of strings representing the content of the MDU file.

        Returns:
            Optional[int]:
                The most common index of the comment character, or None if not found.

        Notes:
            - This function is used to determine where comments start in the MDU file.
            - It ignores lines that start with the comment character `#` to avoid counting comments as part of the key-value pairs.
            - The function uses a Counter to find the most common position of the comment character.
            - If no lines with comments are found, it returns None.
            - if the line has multiple comment characters, it will only count the first one.
        """
        position = FileStyleProperties._locate(content, "#")

        return position

    @staticmethod
    def _locate(content: List[str], keyword: str) -> Optional[int]:
        """
        Get the most common position (column index) of the equal sign in the MDU file.

        Args:
            content (List[str]): List of strings representing the content of the MDU file.

        Returns:
            Optional[int]: The most common index of the equal sign, or None if not found.

        Example:
            ```python
            >>> FileStyleProperties._get_equal_sign_position(
            ...     ['A = 1', 'BB   = 2', 'CCC = 3', '# Comment = 4']
            ... )
            2
            ```
        """
        equal_sign_counter = Counter()
        for line in content:
            if "=" in line and not line.strip().startswith("#"):
                eq_index = line.find(keyword)
                if eq_index != -1:  # when the keyword is not found, eq_index will be -1
                    equal_sign_counter[eq_index] += 1

        position = None
        if equal_sign_counter:
            most_common_pos, _ = equal_sign_counter.most_common(1)[0]
            position = most_common_pos

        return position

    @staticmethod
    def _get_leading_spaces(content: List[str]) -> Optional[int]:
        """Get Leading Spaces.

        - Detect the most common number of leading spaces in each line of the MDU file.
        - The function returns the most common leading space count, which can be used to maintain consistent formatting

        Args:
            content (List[str]):
                List of strings representing the content of the MDU file.

        Returns:
            Optional[int]:
                The most common number of leading spaces, or None if not found.

        Notes:
            - All the lines that start with a comment character `#` are ignored.
            - The leading spaces are counted as the difference between the length of the line and the length of the line
                after stripping leading whitespace.
            - If no lines with leading spaces are found, returns None.
            - The function uses a Counter to find the most common leading space count.
            - tabs and spaces are treated the same, so if a line has 1 spaces and 1 tab, it will be counted as 2
            leading spaces.

        Example:
            ```python
            >>> FileStyleProperties._get_leading_spaces([
            ...     '  Param1 = value1', '    Param2 = value2', '  Param3 = value3'])
            2
            ```
        """
        leading_spaces = Counter()
        for line in content:
            if not line.strip().startswith("#"):
                num_spaces = len(line) - len(line.lstrip())
                leading_spaces[num_spaces] += 1

        spacing = None
        if leading_spaces:
            most_common_spacing, _ = leading_spaces.most_common(1)[0]
            spacing = most_common_spacing

        return spacing

    def recenter_equal_sign(self, line: str) -> str:
        """Recenter Equal Sign.

        Recenter the equal sign to a specific target column.

        Args:
            line (str):
                Input line like "IniFieldFile=my-file.ini"

        Returns:
            str:
                Re-aligned line with equal sign at target_pos
        """
        key, value = map(str.strip, line.split("=", 1))
        aligned_key = key.ljust(self.equal_sign_position - self.leading_spaces)
        spaces = " " * self.leading_spaces
        return f"{spaces}{aligned_key}= {value}"


class Line:

    def __init__(self, line: str):
        self.line = line
        self.comment_position, self.comments = self._get_comments()
        self.leading_spaces = self.get_leading_spaces()

    def _get_comments(self) -> Tuple[int, str]:
        """Get comments from the line."""
        comment_index = self.line.find("#")
        if comment_index != -1:
            comments = self.line[comment_index:].strip()
        else:
            comment_index = None
            comments = ""

        return comment_index, comments

    def is_comment(self) -> bool:
        """Check if the line is a comment."""
        return self.line.strip().startswith("#")

    def is_section_header(self) -> bool:
        """Check if the line is a section header (e.g., '[...]')."""
        return self.line.startswith("[") and self.line.endswith("]")

    def get_key_value(self) -> Tuple[str, str, int]:
        """Get the key and value from the line."""
        if self.is_comment() or self.is_section_header():
            key = None
            value = None
            equal_sign_position = None
        else:
            if "=" in self.line:
                key, value = self.line.split("=", 1)
                key = key.strip()
                value = value.strip()
                equal_sign_position = self.line.find("=")
            else:
                raise ValueError(f"Line '{self.line}' does not contain an '='")

        return key, value, equal_sign_position

    def get_leading_spaces(self) -> int:
        """Get the number of leading spaces in the line."""
        return len(self.line) - len(self.line.lstrip())

    def recenter_equal_sign(self, equal_sign_position: int = None, leading_spaces: int = None) -> str:
        """Recenter Equal Sign.

        Recenter the equal sign to a specific target column.

        Args:
            equal_sign_position (int, optional):
                location of the equal sign in the line, if None, it will use the position of the equal sign in the line.
            leading_spaces (int, optional):
                number of leading spaces in the line, if None, it will use the number of leading spaces in the line.

        Returns:
            str:
                Re-aligned line with equal sign at target_pos

        Notes:
            - If the line does not contain an equal sign, it will raise a ValueError.
            - The function preserves the leading spaces and aligns the key to the specified equal sign position.
        """
        key, value, old_equal_sign_position = self.get_key_value()

        if equal_sign_position is None:
            equal_sign_position = old_equal_sign_position

        if leading_spaces is None:
            leading_spaces = self.leading_spaces

        aligned_key = key.ljust(equal_sign_position - leading_spaces)
        spaces = " " * leading_spaces
        return f"{spaces}{aligned_key}= {value}"

    def recenter_comments(self, comments_position: int = None) -> str:
        """Recenter Comments.

        Recenter the comments to a specific target column.

        Args:
            comments_position (int, optional):
                position of the comments in the line, if None, it will use the position of the comments in the line.

        Returns:
            str:
                Re-aligned line with comments at target_pos
        """
        if comments_position is None:
            comments_position = self.comment_position

        if self.comment_position is not None:
            aligned = self.line[:self.comment_position].ljust(comments_position)
            return f"{aligned}{self.comments}"
        else:
            return self.line

class MDUParser:
    """A class to update the ExtForceFileNew entry in an MDU file."""

    def __init__(self, mdu_path: PathOrStr):
        """Initialize the MDUParser.

        Args:
            mdu_path: Path to the MDU file to update
        """
        mdu_path = Path(mdu_path) if not isinstance(mdu_path, Path) else mdu_path
        if not mdu_path.exists():
            raise FileNotFoundError(f"File not found: {mdu_path}")

        self.mdu_path = mdu_path
        self.updated_lines = []
        self.inside_external_forcing = False
        self.found_extforcefilenew = False
        self._content = self._read_file()
        self.loaded_fm_data = self._load_with_fm_model()
        self.extforce_block = ExternalForcingBlock(**self.external_forcing)
        self.extforce_block.root_dir = self.mdu_path.parent
        self.temperature_salinity_data = self.get_temperature_salinity_data()
        self._geometry = self.loaded_fm_data.get("geometry")
        self.file_style_properties = FileStyleProperties(self._content)

    def _load_with_fm_model(self) -> Dict[str, Any]:
        """Load the MDU file using the FMModel class.

        Returns:
            data (Dict[str, str]):
                all the data inside the mdu file, with each section in the file as a key and the data of that section is
                the value of that key.
        """
        data = FMModel._load(FMModel, self.mdu_path)
        return data

    @property
    def external_forcing(self) -> Dict[str, Any]:
        return self.loaded_fm_data.get("external_forcing")

    @property
    def geometry(self) -> Dict[str, Any]:
        """Get the geometry data from the MDU file."""
        return self._geometry

    @property
    def new_forcing_file(self) -> Union[Path, str]:
        """Get the filename for the ExtForceFileNew entry."""
        if not hasattr(self, "_new_forcing_file"):
            raise AttributeError("new_forcing_file not set")
        return self._new_forcing_file

    @new_forcing_file.setter
    def new_forcing_file(self, file_name: Union[Path, str]) -> None:
        """Set the new filename for the ExtForceFileNew entry.

        Args:
            file_name(PathOrStr):
                New filename for the ExtForceFileNew entry
        """
        if not isinstance(file_name, (Path, str)):
            raise ValueError("new_forcing_filename must be a str or Path")
        self._new_forcing_file = file_name

    def _read_file(self) -> List[str]:
        """Read the MDU file into a list of strings.

        Returns:
            List of strings, one for each line in the file
        """
        with open(self.mdu_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return lines

    def save(self, backup: bool = False) -> None:
        """Save the updated MDU file."""
        if backup:
            backup_file(self.mdu_path)

        with open(self.mdu_path, "w", encoding="utf-8") as file:
            file.writelines(self.content)

    @property
    def content(self) -> List[str]:
        """Get the content of the MDU file.

        Returns:
            List of strings, one for each line in the file
        """
        return self._content

    @content.setter
    def content(self, new_content: List[str]) -> None:
        """Set the content of the MDU file.

        Args:
            new_content: New content for the MDU file
        """
        self._content = new_content

    def has_inifield_file(self) -> bool:
        """Check if the MDU file has an inifield file defined.

        Returns:
            bool: True if an inifield file is defined, False otherwise
        """
        return self.has_field("IniFieldFile")

    def has_structure_file(self) -> bool:
        """Check if the MDU file has an inifield file defined.

        Returns:
            bool: True if an inifield file is defined, False otherwise
        """
        return self.has_field("StructureFile")

    def has_field(self, field_name: str) -> bool:
        """Check if the MDU file has a given file defined.

        Returns:
            bool:
                True if an inifield file is defined, False otherwise
        """
        return True if self.find_keyword_lines(field_name) is not None else False

    def update_extforce_file_new(self) -> List[str]:
        """Update the ExtForceFileNew entry in the MDU file.

        Update the 'ExtForceFileNew' entry under the '[external forcing]' section
        of an MDU file. Writes the updated content to output_path if provided,
        or overwrites the original file otherwise.

        Returns:
            List[str]:
                The updated lines of the .mdu file.

        Notes:
            - This function is a workaround for updating the ExtForceFileNew entry in an MDU file.
            - The function reads the entire file into memory, updates the line containing ExtForceFileNew, and writes the
                updated content back to disk.
            - The function removes the `extforcefile` from the mdu file, and only keeps the new updated `ExtForceFileNew`
            entry, as all the old forcing quantities in the old forcing file are converted to the new format.
            - after fixing the issue with mdu files having `Unkown keyword` error, this function will be removed,
            and the `LegacyFMModel` will be the only way to read/update the mdu file

        """
        lines = self.content
        for line in lines:
            stripped = line.strip()
            # Check if we've hit the [external forcing] header
            if stripped.lower().startswith("[external forcing]"):
                self.inside_external_forcing = True
                self.found_extforcefilenew = False
                self.updated_lines.append(line)
                continue

            # If we are inside the [external forcing] section, look for ExtForceFileNew
            if self.inside_external_forcing:
                # If we find another section header, it means [external forcing] section ended
                self._handle_external_forcing_section(stripped)
                continue

            # Default: write the line unmodified
            self.updated_lines.append(line)

        # If we ended the file while still in [external forcing] with no ExtForceFileNew found, add it
        if self.inside_external_forcing and not self.found_extforcefilenew:
            new_line = (
                f"ExtForceFileNew                           = {self.new_forcing_file}\n"
            )
            self.updated_lines.append(new_line)
            self.updated_lines.append("\n")

        return self.updated_lines

    def update_inifield_file(self, file_name: str) -> None:
        """Update the IniFieldFile entry in the MDU file.

        Args:
            file_name (str):
                The path to the new inifield file to set

        Notes:
            - The method adds the IniFieldFile entry at the end-1 of the geometry section, as some mdu files has
            decorative lines (i.e. "#=========") around the section headers, and the function that detects the end of
            the section detects the end of the section by looking for the next section header. and then this
            decorative line will be considered as the last line in the section and adding the inifield file at
            end_ind - 1 will leave an empty line between the actual last line in the section and the newely added
            inifield file line.
            - If the inifield file already exists, it will be updated with the new file name.
        """
        if not self.has_inifield_file():
            line = f"{INIFIELD_FILE_LINE} = {file_name}\n"
            _, end_ind = self.find_section_bounds("geometry")
            # put the inifield file at the end of the geometry section
            line_number = end_ind - 1
        else:
            # find the line number of the existing inifield file
            inifield_file_line_number = self.find_keyword_lines(INIFIELD_FILE_LINE)

            # if the inifield file already exists, we update it
            line = f"{INIFIELD_FILE_LINE} = {file_name}\n"

            if inifield_file_line_number is not None:
                # remove the old inifield file line
                self.content.pop(inifield_file_line_number)

            line_number = inifield_file_line_number

        line = self.file_style_properties.recenter_equal_sign(line)
        self.insert_line(line, line_number)

    def update_structure_file(self, file_name: str) -> None:
        """Update the IniFieldFile entry in the MDU file.

        Args:
            file_name (str):
                The path to the new inifield file to set

        Notes:
            - The method adds the IniFieldFile entry at the end-1 of the geometry section, as some mdu files has
            decorative lines (i.e. "#=========") around the section headers, and the function that detects the end of
            the section detects the end of the section by looking for the next section header. and then this
            decorative line will be considered as the last line in the section and adding the inifield file at
            end_ind - 1 will leave an empty line between the actual last line in the section and the newely added
            inifield file line.
        """
        line = f"{STRUCTURE_FILE_LINE} = {file_name}\n"
        line = self.file_style_properties.recenter_equal_sign(line)
        # put the structure file at the end of the geometry section
        _, end_ind = self.find_section_bounds("geometry")
        self.insert_line(line, end_ind - 1)

    @staticmethod
    def is_section_header(line: str) -> bool:
        """Check if the line is a section header (e.g., '[...]').

        Args:
            line: The line to check

        Returns:
            True if the line is a section header (excluding '[external forcing]'), False otherwise
        """
        return (
            line.startswith("[")
            and line.endswith("]")
            and "external forcing" not in line.lower()
        )

    def replace_extforcefilenew(self, line: str) -> str:
        """Replace the ExtForceFileNew line with the new filename.

        Args:
            line: The line containing the ExtForceFileNew entry

        Returns:
            The updated line with the new filename

        Notes:
            - This method preserves the formatting of the original line, including comments
            - If the line doesn't contain an '=' character, it's returned unchanged
            - If the new filename would overflow into a comment, the comment is preserved
        """
        # Find the '=' character
        eq_index = line.find("=")
        if eq_index == -1:
            return line
        # Everything up to and including '='
        left_part = line[: eq_index + 1]
        # Remainder of the line (after '=')
        right_part = line[eq_index + 1 :].strip("\n")  # noqa: E203
        name_len = len(str(self.new_forcing_file))
        # Protect against filename overflow into the comment
        right_part_clipped = right_part[name_len + 1 :]
        if right_part_clipped.find("#") == -1 and right_part_clipped != "":
            right_part_clipped = f" {right_part.lstrip()}"
        # Insert new filename immediately after '=' + a space
        return f"{left_part} {self.new_forcing_file}{right_part_clipped}\n"

    def _handle_external_forcing_section(self, stripped: str) -> None:
        """Handle a line within the [external forcing] section.

        Args:
            stripped: The stripped line to process

        Notes:
            - If the line is a section header, it means we're leaving the [external forcing] section
            - If we're leaving the section and haven't found ExtForceFileNew, add it
            - If the line starts with ExtForceFileNew, replace it with the new filename
            - If the line starts with ExtForceFile, skip it (remove it from the output)
            - Otherwise, add the line to the output unchanged
        """
        if self.is_section_header(stripped):
            # If we never found ExtForceFileNew before leaving, add it now
            if not self.found_extforcefilenew:
                new_line = f"ExtForceFileNew                           = {self.new_forcing_file}\n"
                self.updated_lines.extend([new_line, "\n"])

            self.inside_external_forcing = False
            # fall through to just append the line below

        # If the line has ExtForceFileNew, replace it
        # The simplest way is to check if it starts with or contains ExtForceFileNew
        # ignoring trailing spaces. You can refine the logic as needed.
        if stripped.lower().startswith("extforcefilenew"):
            self.found_extforcefilenew = True
            self.updated_lines.append(self.replace_extforcefilenew(stripped))
            return
        elif stripped.lower().startswith("extforcefile"):
            return
        self.updated_lines.append(f"{stripped}\n")

    def get_temperature_salinity_data(self) -> Dict[str, Any]:
        """Get the info needed from the mdu to process and convert the old external forcing files.

        Returns:
            temperature_and_salinity_info (Dict[str, str]):
                dictionary with the information needed for the conversion tool to convert the `SourceSink` and
                `Boundary` quantities. The dictionary will have three keys `temperature`, `salinity`, and `refdate`.

        Examples:
            ```python
            >>> mdu_info = { #doctest: +SKIP
            ...     "refdate": "minutes since 2015-01-01 00:00:00",
            ...     "temperature": True,
            ...     "salinity": True,
            ... }
            ```
        """
        # read sections of the mdu file.
        time_data = self.loaded_fm_data.get("time")
        physics_data = self.loaded_fm_data.get("physics")
        mdu_time = IgnoreUnknownKeyWordClass(Time, **time_data)
        mdu_physics = IgnoreUnknownKeyWordClass(Physics, **physics_data)

        ref_time = get_ref_time(mdu_time.refdate)
        temperature_and_salinity_info = {
            "file_path": self.mdu_path,
            "refdate": ref_time,
            "temperature": False if mdu_physics.temperature == 0 else True,
            "salinity": mdu_physics.salinity,
        }
        return temperature_and_salinity_info

    def find_keyword_lines(
        self, keyword: str, case_sensitive: bool = False
    ) -> Union[int, None]:
        """Find line numbers in the MDU file where the keyword appears.

        Args:
            keyword: The keyword to search for.
            case_sensitive: Whether the search should be case-sensitive.

        Returns:
            A list of line number where the keyword is found.
        """
        if not case_sensitive:
            keyword = keyword.lower()
        line_number = None
        for i, line in enumerate(self.content, start=0):
            haystack = line if case_sensitive else line.lower()
            stripped_line = haystack.lstrip()
            if_exist = (
                stripped_line.startswith(keyword)
                if case_sensitive
                else stripped_line.lower().startswith(keyword.lower())
            )
            if if_exist:
                line_number = i
                break

        return line_number

    def insert_line(self, line: str, index: int) -> None:
        """Insert a line at the specified index in the MDU file content.

        Args:
            index: The 0-based index where the line should be inserted.
            line: The line to insert (a newline `\n` will be added if not present).

        Raises:
            IndexError: If the index is out of bounds.
        """
        if not line.endswith("\n"):
            line += "\n"

        if index < 0 or index > len(self.content):
            raise IndexError("Index out of bounds for inserting line.")

        self.content.insert(index, line)

    def find_section_bounds(self, section_name: str) -> Tuple[int, int]:
        """Find the start and end line indices of a section.

        Args:
            section_name: The name of the section, e.g., "geometry".

        Returns:
            A tuple (start_index, end_index):
                - start_index is the index of the section header line.
                - end_index is the index just before the next section header or end of file(index to the empty line).

        Raises:
            ValueError: If the section is not found.
        """
        section_start = -1
        section_end = len(self.content)

        header = f"[{section_name.lower()}]"

        for i, line in enumerate(self.content):
            stripped = line.strip().lower()
            if stripped.startswith("[") and stripped.endswith("]"):
                if stripped == header:
                    section_start = i
                elif section_start != -1:
                    # We hit the start of a new section after finding our target
                    section_end = i - 1
                    break

        if section_start == -1:
            section_start = None
            section_end = None

        return section_start, section_end

    def get_inifield_file(
        self,
        inifield_file: Optional[PathOrStr],
    ) -> Path:
        inifieldfile_mdu = self.geometry.get("inifieldfile")

        root_dir = self.mdu_path.parent
        if inifield_file is not None:
            # user defined initial field file
            inifield_file = root_dir / inifield_file
        elif isinstance(inifieldfile_mdu, Path):
            # from the LegacyFMModel
            inifield_file = inifieldfile_mdu.resolve()
        elif isinstance(inifieldfile_mdu, str):
            # from reading the geometry section
            inifield_file = root_dir / inifieldfile_mdu
        else:
            print(
                f"The initial field file is not found in the mdu file, and not provided by the user. \n "
                f"given: {inifield_file}."
            )
        return inifield_file

    def get_structure_file(
        self,
        structure_file: Optional[PathOrStr],
    ) -> Path:
        structurefile_mdu = self.geometry.get("structurefile")
        if structure_file is not None:
            # user defined structure file
            structure_file = self.mdu_path / structure_file
        elif isinstance(structurefile_mdu, Path):
            # from the LegacyFMModel
            structure_file = structurefile_mdu.resolve()
        elif isinstance(structurefile_mdu, str):
            # from reading the geometry section
            structure_file = self.mdu_path / structurefile_mdu
        else:
            print(
                "The structure file is not found in the mdu file, and not provide by the user. \n"
                f"given: {structure_file}."
            )
        return structure_file


def save_mdu_file(content: List[str], output_path: PathOrStr) -> None:
    """Save the updated MDU file content to disk.

    Args:
        content: The updated content of the MDU file
        output_path: The path where the updated MDU file should be saved
    """
    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(content)


def get_ref_time(input_date: str, date_format: str = "%Y%m%d"):
    """Convert a date string to a datetime object."""
    date_object = datetime.strptime(f"{input_date}", date_format)
    return f"MINUTES SINCE {date_object}"
