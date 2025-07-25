"""MDU Parser."""

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from hydrolib.core.base.file_manager import PathOrStr
from hydrolib.core.dflowfm.mdu.models import FMModel, Physics, Time
from hydrolib.tools.extforce_convert.utils import IgnoreUnknownKeyWordClass, backup_file

STRUCTURE_FILE_LINE = "StructureFile"
INIFIELD_FILE_LINE = "IniFieldFile"


@dataclass
class Section:
    """Information about a section in an MDU file.

    Attributes:
        start (int):
            The index of the section header line (0-index).
        end (int):
            The index of the last line in the section (0-index), the last line in the section is the line before the
            header of the next section.
        non_key_value_lines_at_end (int):
            number of empty or non-key-value lines at the end of the section.
        last_key_value_line_index (int):
            index of the last key-value line in the section (0-based index), use this index to append any key-value
            to the end of the section.
    Notes:
        - The section header is expected to be in the format "[section_name]".
        - The section is defined as starting from the section header line and ending at the line before the header of
        the next section.
        - If all the lines in the section are empty lines or comments, the `start` and `last_key_value_line_index`
        will be the same.
        - if the section is not found, `start` and `end` will be set to None.
        - if the section exists twice in the file, the first occurrence will be used.
    """

    start: Optional[int]
    end: Optional[int]
    non_key_value_lines_at_end: Optional[int]
    last_key_value_line_index: Optional[int]

    def __init__(self, section_name: str, content: List[str]):
        """Initialize SectionBounds with content and section indices."""
        section_start = -1
        section_end = len(content) - 1

        header = f"[{section_name.lower()}]"

        # Find section start and end
        for i, line in enumerate(content):
            stripped = line.strip().lower()
            if stripped.startswith("[") and stripped.endswith("]"):
                if stripped == header:
                    section_start = i
                elif section_start != -1:
                    # We hit the start of a new section after finding our target
                    section_end = i - 1
                    break

        if section_start == -1:
            # Section not found
            section_start = None
            section_end = None

        self.start = section_start
        self.end = section_end
        self.non_key_value_lines_at_end = (
            None
            if section_start is None
            else (
                self.get_empty_and_non_key_value_lines(
                    content, section_start, section_end
                )
            )
        )
        self.last_key_value_line_index = (
            None
            if section_start is None
            else (self.end - self.non_key_value_lines_at_end)
        )

    @staticmethod
    def get_empty_and_non_key_value_lines(
        content, section_start: int, section_end: int
    ):
        # Find empty lines at the end of the section and non-key-value lines within the section
        empty_lines_at_end = []

        if section_start is not None and section_end is not None:
            # Check for empty lines at the end of the section
            for i in range(section_end, section_start, -1):
                line_obj = Line(content[i])
                if line_obj.is_empty() or line_obj.is_comment():
                    empty_lines_at_end.append(i)
                else:
                    break

        return len(empty_lines_at_end)


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
                if ext_file.exists():
                    raise FileExistsError(
                        "The converter detected that there is no new extforce file in the mdu file, \n"
                        f"But there is an extforce file with the name {ext_file} that already exists. \n"
                        "Please either remove/rename the file or add it to the mdu file. in the section [external forcing]"
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
        position = self._locate(content, "#")

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


class Line:

    def __init__(self, line: str):
        self._content = line
        self.validate()

    def __str__(self):
        """String representation of the Line object."""
        return self.content

    @property
    def content(self) -> str:
        """Get the content of the line."""
        return self._content

    def validate(self):
        """Validate the line content."""
        if not (self.is_empty() or self.is_comment() or self.is_section_header()):
            if self.equal_sign_position is None:
                raise ValueError(
                    f"Invalid line content: '{self._content}'. Line must contain an equal sign '=' for key-value pairs."
                )

    @property
    def key_value(self) -> Tuple[str, str]:
        """Get the key of the line."""
        if self.is_comment() or self.is_section_header():
            key = None
            value = None
        else:
            key, value = self.get_key_value()

        return key, value

    @property
    def key(self) -> str:
        """Get the key of the line."""
        key, _ = self.key_value
        return key

    @property
    def value(self) -> str:
        """Get the value of the line."""
        _, value = self.key_value
        return value

    @property
    def equal_sign_position(self) -> int:
        """Get the position of the equal sign in the line."""
        return self.content.find("=") if "=" in self.content else None

    @property
    def comments(self) -> str:
        _, comment = self._get_comments()
        return comment

    @property
    def comment_position(self) -> Optional[int]:
        """Get the position of the comments in the line."""
        comment_index = self.content.find("#")
        if comment_index == -1:
            comment_index = None

        return comment_index

    @property
    def leading_spaces(self) -> int:
        """Get the number of leading spaces in the line."""
        return self.get_leading_spaces()

    def _get_comments(self) -> Tuple[int, str]:
        """Get comments from the line."""
        comment_index = self.content.find("#")
        if comment_index != -1:
            comments = self.content[comment_index:].strip()
            comments += "\n"
        else:
            comment_index = None
            comments = ""

        return comment_index, comments

    def is_comment(self) -> bool:
        """Check if the line is a comment."""
        return self.content.strip().startswith("#")

    def is_section_header(self) -> bool:
        """Check if the line is a section header (e.g., '[...]')."""
        return self.content.startswith("[") and self.content.endswith("]")

    def is_empty(self) -> bool:
        """Check if the line is empty or contains only whitespace."""
        return not self.content.strip()

    def get_key_value(self) -> Tuple[str, str]:
        """Get the key and value from the line."""
        if self.is_comment() or self.is_section_header() or self.is_empty():
            key = None
            value = None
        else:
            if "=" in self.content:
                key, value = self.content.split("=", 1)
                key = key.strip()
                value = value.strip()
                if "#" in value:
                    value = value.split("#", 1)[0].strip()
                    if value == "":
                        value = None
            else:
                raise ValueError(f"Line '{self.content}' does not contain an '='")

        return key, value

    def get_leading_spaces(self) -> int:
        """Get the number of leading spaces in the line."""
        return len(self.content) - len(self.content.lstrip())

    def recenter_equal_sign(
        self, equal_sign_position: int = None, leading_spaces: int = None
    ) -> str:
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
        key, _ = self.get_key_value()

        if equal_sign_position is None:
            equal_sign_position = self.equal_sign_position

        if leading_spaces is None:
            leading_spaces = self.leading_spaces

        aligned_key = key.ljust(equal_sign_position - leading_spaces)
        spaces = " " * leading_spaces
        all_after_equal_sign = self._content[self.equal_sign_position + 1 :]
        self._content = f"{spaces}{aligned_key}= {all_after_equal_sign.lstrip()}"

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
            aligned = self.content[: self.comment_position].ljust(comments_position)
            self._content = f"{aligned}{self.comments}"

    @classmethod
    def from_key_value(
        cls,
        key: str,
        value: str,
        equal_sign_position: int = None,
        leading_spaces: int = 0,
        comment: str = None,
    ) -> "Line":
        """Create a Line instance from a key-value pair.

        Args:
            key (str): The key to set in the line. Must not be empty.
            value (str): The value to set in the line. Can be empty.
            equal_sign_position (int, optional): Position of the equal sign. Defaults to None.
            leading_spaces (int, optional): Number of leading spaces. Defaults to 0.
            comment (str, optional): Comment to append to the line. Defaults to None.

        Returns:
            Line: A new Line instance with the specified key and value.

        Raises:
            ValueError: If key is not a string or is empty, or if positions are negative.

        Examples:
            >>> Line.from_key_value('Param', 'value')
            Line('Param= value')
            >>> Line.from_key_value('Param', '', comment='# no value')
            Line('Param=  # no value')
        """
        if not isinstance(key, str):
            raise ValueError("Key and value must be strings.")
        if key == "":
            raise ValueError("Key must not be empty.")
        if equal_sign_position is not None and equal_sign_position < 0:
            raise ValueError("equal_sign_position cannot be negative.")
        if leading_spaces < 0:
            raise ValueError("leading_spaces cannot be negative.")
        if equal_sign_position is None:
            equal_sign_position = len(key) + leading_spaces + 1

        aligned_key = key.ljust(equal_sign_position - leading_spaces)
        spaces = " " * leading_spaces
        line_content = (
            f"{spaces}{aligned_key}= {value}"
            if value != ""
            else f"{spaces}{aligned_key}= "
        )

        if comment:
            stripped = comment.strip()
            if not stripped.endswith("\n"):
                stripped += "\n"
            line_content = f"{line_content} {stripped}"
        else:
            line_content += "\n"

        return cls(line_content)

    def update_value(self, new_value: str):
        """Update the value of the line, preserving key and formatting."""
        if self.is_comment() or self.is_section_header() or self.is_empty():
            raise ValueError("Cannot update value for comment or section header lines.")

        key, _ = self.get_key_value()

        # Rebuild the line
        return Line.from_key_value(
            key,
            new_value,
            equal_sign_position=self.equal_sign_position,
            leading_spaces=self.leading_spaces,
            comment=self.comments,
        )


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

    def update_file_entry(
        self, field_name: str, file_name: str, section_name: str
    ) -> None:
        leading_spaces = self.file_style_properties.leading_spaces
        equal_sign_position = self.file_style_properties.equal_sign_position

        if not self.has_field(field_name):
            # if the field does not exist, we create a new line for it and add it to the end of the section
            line = Line.from_key_value(
                field_name,
                file_name,
                leading_spaces=leading_spaces,
                equal_sign_position=equal_sign_position,
            )
            section = self.get_section(section_name)
            # put the inifield file at the end of the geometry section
            line_number = section.last_key_value_line_index + 1
        else:
            # if the field already exists, we update it
            # find the line number of the existing field
            existing_field_line_num = self.find_keyword_lines(field_name)
            line = Line(self.content[existing_field_line_num])
            line = line.update_value(file_name)
            line.recenter_comments(self.file_style_properties.comments_position)
            line.recenter_equal_sign(
                equal_sign_position=equal_sign_position,
                leading_spaces=leading_spaces,
            )

            if existing_field_line_num is not None:
                # remove the old line
                self.content.pop(existing_field_line_num)

            line_number = existing_field_line_num

        self.insert_line(line.content, line_number)

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
        self.update_file_entry(INIFIELD_FILE_LINE, file_name, "geometry")

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
        self.update_file_entry(STRUCTURE_FILE_LINE, file_name, "geometry")

    def update_extforce_file_new(self, file_name: str, num_quantities: int) -> None:
        if num_quantities > 0:
            self.update_file_entry("ExtForceFileNew", file_name, "external forcing")
        else:
            ext_force_line = self.find_keyword_lines("ExtForceFileNew")
            if ext_force_line is not None:
                self.content.pop(ext_force_line)

        old_ext_force_line = self.find_keyword_lines("ExtForceFile")
        if old_ext_force_line is not None:
            self.content.pop(old_ext_force_line)

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

    def get_section(self, section_name: str) -> Section:
        """Get Mdu Section.

        Returns:
            Section:
                Section object.
                    start (int):
                        The index of the section header line (0-index).
                    end (int):
                        The index of the last line in the section (0-index), the last line in the section is the line before the
                        header of the next section.
                    non_key_value_lines_at_end (int):
                        number of empty or non-key-value lines at the end of the section.
                    last_key_value_line_index (int):
                        index of the last key-value line in the section (0-based index), use this index to append any key-value
                        to the end of the section.
        """
        return Section(section_name, self.content)

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
