"""MDU Parser."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Union

from hydrolib.core.base.file_manager import PathOrStr
from hydrolib.core.dflowfm.mdu.models import FMModel, Physics, Time
from hydrolib.tools.extforce_convert.utils import IgnoreUnknownKeyWordClass, backup_file


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
        self.temperature_salinity_data = self.get_temperature_salinity_data()

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
