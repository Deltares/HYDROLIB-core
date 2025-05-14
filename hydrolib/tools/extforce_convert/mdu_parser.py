from typing import List

from hydrolib.core.basemodel import PathOrStr


class MDUParser:
    """A class to update the ExtForceFileNew entry in an MDU file."""

    def __init__(self, mdu_path: PathOrStr, new_forcing_filename: PathOrStr):
        self.mdu_path = mdu_path
        self.new_forcing_filename = new_forcing_filename
        self.updated_lines = []
        self.inside_external_forcing = False
        self.found_extforcefilenew = False

    def update_extforce_file_new(self) -> List[str]:
        """
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
        with open(self.mdu_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

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
                self._handle_external_forcing_section(line, stripped)
                continue

            # Default: write the line unmodified
            self.updated_lines.append(line)

        # If we ended the file while still in [external forcing] with no ExtForceFileNew found, add it
        if self.inside_external_forcing and not self.found_extforcefilenew:
            new_line = f"ExtForceFileNew                           = {self.new_forcing_filename}\n"
            self.updated_lines.append(new_line)
            self.updated_lines.append("\n")

        return self.updated_lines

    def is_section_header(self, line: str) -> bool:
        """Check if the line is a section header (e.g., '[...]')."""
        return (
            line.startswith("[")
            and line.endswith("]")
            and "external forcing" not in line.lower()
        )

    def replace_extforcefilenew(self, line: str) -> str:
        """Replace the ExtForceFileNew line with the new filename."""
        # Find the '=' character
        eq_index = line.find("=")
        if eq_index == -1:
            return line
        # Everything up to and including '='
        left_part = line[: eq_index + 1]
        # Remainder of the line (after '=')
        right_part = line[eq_index + 1 :].strip("\n")  # noqa: E203
        name_len = len(self.new_forcing_filename)
        # Protect against filename overflow into the comment
        right_part_clipped = right_part[name_len + 1 :]
        if right_part_clipped.find("#") == -1:
            right_part_clipped = f" {right_part.lstrip()}"
        # Insert new filename immediately after '=' + a space
        return f"{left_part} {self.new_forcing_filename}{right_part_clipped}\n"

    def _handle_external_forcing_section(self, line: str, stripped: str) -> None:
        if self.is_section_header(stripped):
            # If we never found ExtForceFileNew before leaving, add it now
            if not self.found_extforcefilenew:
                new_line = f"ExtForceFileNew                           = {self.new_forcing_filename}\n"
                self.updated_lines.extend([new_line, "\n"])

            self.inside_external_forcing = False
            # fall through to just append the line below

        # If the line has ExtForceFileNew, replace it
        # The simplest way is to check if it starts with or contains ExtForceFileNew
        # ignoring trailing spaces. You can refine the logic as needed.
        if stripped.lower().startswith("extforcefilenew"):
            self.found_extforcefilenew = True
            self.updated_lines.append(self.replace_extforcefilenew(line))
            return
        elif stripped.lower().startswith("extforcefile"):
            return
        self.updated_lines.append(line)


def save_mdu_file(content: List[str], output_path: PathOrStr) -> None:
    # Finally, write the updated lines to disk
    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(content)
