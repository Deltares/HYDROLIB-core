from typing import List, Tuple


class BaseParser:
    @staticmethod
    def _read_header_comments(lines: List[str]) -> Tuple[List[str], int]:
        """Read the header comments of the lines from the .tim file.
        The comments are only expected at the start of the .tim file.
        When a non comment line is encountered, all comments from the header will be retuned together with the start index of the timeseries data.

        Args:
            lines (List[str]): Lines from the the .tim file which is read.

        Returns:
            Tuple of List[str] and int, the List[str] contains the commenst from the header, the int is the start index of the timeseries.
        """
        comments: List[str] = []
        start_timeseries_index = 0
        for line_index in range(len(lines)):

            line = lines[line_index].strip()

            if len(line) == 0:
                comments.append(line)
                continue

            if line.startswith("#") or line.startswith("*"):
                comments.append(line[1:])
                continue

            start_timeseries_index = line_index
            break

        return comments, start_timeseries_index