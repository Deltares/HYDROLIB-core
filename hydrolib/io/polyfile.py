"""polyfily.py defines all classes and functions related to handling pol/pli(z) files.
"""

from enum import Enum
from pathlib import Path

from attr import field
from hydrolib.io.common import LineReader, ParseMsg, BaseModel
from typing import Callable, Dict, List, Optional, Sequence, Tuple, Union


class Description(BaseModel):
    """Description of a single PolyObject.

    The Description will be prepended to a block. Each line will
    start with a '*'.
    """

    content: str


class Metadata(BaseModel):
    """Metadata of a single PolyObject."""

    name: str
    n_rows: int
    n_columns: int


class Point(BaseModel):
    """Point consisting of a x and y coordinate, an optional z coordinate and data."""

    x: float
    y: float
    z: Optional[float]
    data: Sequence[float]


class PolyObject(BaseModel):
    """PolyObject describing a single block in a poly file.

    The metadata should be consistent with the points:
    - The number of points should be equal to number of rows defined in the metadata
    - The data of each point should be equal to the number of columns defined in the
      metadata.
    """

    description: Optional[Description]
    metadata: Metadata
    points: List[Point]


class Block(BaseModel):
    """Block is a temporary object which will be converted into a PolyObject."""

    start_line: int

    description: Optional[List[str]] = None
    name: Optional[str] = None
    dimensions: Optional[Tuple[int, int]] = None
    points: Optional[List[Point]] = None

    ws_warnings: List[ParseMsg] = []
    empty_lines: List[int] = []

    def finalise(self) -> Optional[Tuple[PolyObject, List[ParseMsg]]]:
        metadata = self._get_metadata()

        if metadata is None or self.points is None:
            return None

        obj = PolyObject(
            description=self._get_description(), metadata=metadata, points=self.points
        )

        return obj, self.ws_warnings + self._get_empty_line_warnings()

    def _get_description(self) -> Optional[Description]:
        if self.description is not None:
            return Description(content="\n".join(self.description))
        else:
            return None

    def _get_metadata(self) -> Optional[Metadata]:
        if self.name is None or self.dimensions is None:
            return None

        (n_rows, n_columns) = self.dimensions
        return Metadata(name=self.name, n_rows=n_rows, n_columns=n_columns)

    def _get_empty_line_warnings(self):
        if len(self.empty_lines) == 0:
            return []

        warnings = []
        empty_line = (self.empty_lines[0], self.empty_lines[0])

        for line in self.empty_lines[1:]:
            if line == empty_line[1] + 1:
                empty_line = (empty_line[0], line)
            else:
                warnings.append(Block._get_empty_line_msg(empty_line))
                empty_line = (line, line)
        warnings.append(Block._get_empty_line_msg(empty_line))

        return warnings

    @staticmethod
    def _get_empty_line_msg(line_range: Tuple[int, int]) -> ParseMsg:
        return ParseMsg(
            line=line_range, reason="White space at the start of the line is ignored."
        )


class StateType(Enum):
    """The types of state of a Parser."""

    NEW_BLOCK = 0
    PARSED_DESCRIPTION = 1
    PARSED_NAME = 2
    PARSING_POINTS = 3
    INVALID_STATE = 4


class Parser:
    """Parser provides the functionality to parse a polyfile line by line."""

    def __init__(self, has_z_value: bool = False) -> None:
        """Create a new Parser

        Args:
            has_z_value (bool, optional): Whether to interpret the third column as
                                          z-coordinates. Defaults to False.
        """
        self._has_z_value = has_z_value

        self._line = 0
        self._new_block()

        self._poly_objects: List[PolyObject] = []
        self._warnings: List[ParseMsg] = []
        self._errors: List[ParseMsg] = []

        self._current_point: int = 0

        self._feed_line: Dict[StateType, Callable[[str], None]] = {
            StateType.NEW_BLOCK: self._parse_name_or_new_description,
            StateType.PARSED_DESCRIPTION: self._parse_name_or_next_description,
            StateType.PARSED_NAME: self._parse_dimensions,
            StateType.PARSING_POINTS: self._parse_next_point,
        }

        self._finalise: Dict[StateType, Callable[[], None]] = {
            StateType.NEW_BLOCK: self._noop,
            StateType.PARSED_DESCRIPTION: self._add_current_block_as_incomplete_error,
            StateType.PARSED_NAME: self._add_current_block_as_incomplete_error,
            StateType.PARSING_POINTS: self._add_current_block_as_incomplete_error,
        }

        self._handle_ws: Dict[StateType, Callable[[str], None]] = {
            StateType.NEW_BLOCK: self._log_ws_warning,
            StateType.PARSED_DESCRIPTION: self._log_ws_warning,
            StateType.PARSED_NAME: self._log_ws_warning,
            StateType.PARSING_POINTS: self._noop,
        }

    def feed_line(self, line: str) -> None:
        """Parse the next line with this Parser.

        Args:
            line (str): The line to parse
        """

        if not Parser._is_empty_line(line):
            self._handle_ws[self._state](line)
            self._feed_line[self._state](line)
        else:
            self._handle_empty_line()

        self._increment_line()

    def finalise(
        self,
    ) -> Tuple[Sequence[PolyObject], Sequence[ParseMsg], Sequence[ParseMsg]]:
        """Finalise parsing and return the constructed objects.

        Returns:
            Tuple[Sequence[PolyObject], Sequence[ParseMsg], Sequence[ParseMsg]]:
                A tuple consisting of the constructed PolyObject instances, error
                ParseMsg objects and warning ParseMsg objects.
        """
        self._finalise[self._state]
        return self._poly_objects, self._errors, self._warnings

    @property
    def line(self) -> int:
        """Current line index."""
        return self._line

    def _new_block(self) -> None:
        self._state = StateType.NEW_BLOCK
        self._current_block = Block(start_line=self.line)

    def _finish_block(self):
        (obj, warnings) = self._current_block.finalise()  # type: ignore
        self._poly_objects.append(obj)
        self._warnings.extend(warnings)
        # handle error here

    def _increment_line(self) -> None:
        self._line += 1

    def _noop(self, *_, **__) -> None:
        # no operation
        pass

    def _add_current_block_as_incomplete_error(self) -> None:
        self._errors.append(
            ParseMsg(
                line=(self._current_block.start_line, self.line),
                reason="EoF encountered before the block is finished.",
            )
        )

    def _parse_name_or_new_description(self, line: str) -> None:
        if Parser._is_comment(line):
            self._handle_new_description(line)
        elif Parser._is_name(line):
            self._handle_parse_name(line)
        else:
            # Handle exception here
            pass

    def _parse_name_or_next_description(self, line: str) -> None:
        if Parser._is_comment(line):
            self._handle_next_description(line)
        elif Parser._is_name(line):
            self._handle_parse_name(line)
        else:
            # Handle exception here
            pass

    def _parse_dimensions(self, line: str) -> None:
        dimensions = Parser._convert_to_dimensions(line)

        if dimensions is not None:
            self._current_block.dimensions = dimensions
            self._current_block.points = []
            self._current_point = 0
            self._state = StateType.PARSING_POINTS
        else:
            # Handle exception here
            pass

    def _parse_next_point(self, line: str) -> None:
        point = Parser._convert_to_point(
            line, self._current_block.dimensions[1], self._has_z_value  # type: ignore
        )

        if point is not None:
            self._current_block.points.append(point)  # type: ignore
            self._current_point += 1

            if self._current_block.dimensions[0] == self._current_point:  # type: ignore
                self._finish_block()
                self._new_block()

        else:
            # Handle exception here
            pass

    def _handle_parse_name(self, line: str) -> None:
        self._current_block.name = Parser._convert_to_name(line)
        self._state = StateType.PARSED_NAME

    def _handle_new_description(self, line: str) -> None:
        comment = Parser._convert_to_comment(line)
        self._current_block.description = [
            comment,
        ]
        self._state = StateType.PARSED_DESCRIPTION

    def _handle_next_description(self, line: str) -> None:
        comment = Parser._convert_to_comment(line)
        self._current_block.description.append(comment)  # type: ignore

    def _handle_empty_line(self) -> None:
        if self._state != StateType.INVALID_STATE:
            self._current_block.empty_lines.append(self.line)

    def _log_ws_warning(self, line: str) -> None:
        if line[0] != " ":
            return

        end_column = len(line) - len(line.lstrip()) - 1
        self._current_block.ws_warnings.append(
            ParseMsg(
                line=(self.line, self.line),
                column=(0, end_column),
                reason="White space at the start of the line is ignored.",
            )
        )

    @staticmethod
    def _is_empty_line(line: str) -> bool:
        return len(line.strip()) == 0

    @staticmethod
    def _is_name(line: str) -> bool:
        stripped = line.strip()
        return len(stripped) >= 1 and line[0] != "*" and not (" " in stripped)

    @staticmethod
    def _convert_to_name(line: str) -> str:
        return line.strip()

    @staticmethod
    def _is_comment(line: str) -> bool:
        return len(line) >= 1 and line[0] == "*"

    @staticmethod
    def _convert_to_comment(line: str) -> str:
        return line.rstrip()[1:]

    @staticmethod
    def _convert_to_dimensions(line: str) -> Optional[Tuple[int, int]]:
        stripped = line.strip()
        elems = stripped.split()

        if len(elems) != 2:
            return None

        try:
            n_rows = int(elems[0])
            n_cols = int(elems[1])

            if n_rows <= 0 or n_cols <= 0:
                return None

            return (n_rows, n_cols)
        except ValueError:
            return None

    @staticmethod
    def _convert_to_point(
        line: str, expected_n_points: int, has_z: bool
    ) -> Optional[Point]:
        stripped = line.strip()
        elems = stripped.split()

        if len(elems) != expected_n_points:
            return None

        try:
            values = list(float(x) for x in elems)
            return Point(
                x=values[0],
                y=values[1],
                z=values[2] if has_z else None,
                data=values[(3 if has_z else 2) :],
            )

        except ValueError:
            return None


def _determine_has_z_value(input: Union[Path, LineReader]) -> bool:
    return isinstance(input, Path) and input.suffix == ".pliz"


def _read_poly_file(
    input: LineReader, has_z_values: bool
) -> Tuple[Sequence[PolyObject], Sequence[ParseMsg], Sequence[ParseMsg]]:
    parser = Parser(has_z_value=has_z_values)

    while True:
        next_line = input.readline()
        if next_line is None:
            break

        parser.feed_line(next_line)

    return parser.finalise()


def read_polyfile(
    input_data: Union[str, Path, LineReader], has_z_values: Optional[bool] = None
) -> Tuple[Sequence[PolyObject], Sequence[ParseMsg], Sequence[ParseMsg]]:
    """Read the specified file and return the corresponding data.

    The file is expected to follow the .pli(z) / .pol convention. A .pli(z) or .pol
    file is defined as consisting of a number of blocks of lines adhering to the
    following format:

    - Optional description record consisting of one or more lines starting with '*'.
        These will be ignored.
    - Name consisting of a non-blank character string
    - Two integers, Nr and Nc, representing the numbers of rows and columns respectively
    - Nr number of data points, consisting of Nc floats separated by whitespace

    For example:
    ```
    ...
    *
    * Polyline L008
    *
    L008
    4 2
        131595.0 549685.0
        131750.0 549865.0
        131595.0 550025.0
        131415.0 550175.0
    ...
    ```

    Note that the points can be arbitrarily indented, and the comments are optional.

    if no has_z_value has been defined, it will be based on the file path
    extensions:
    - pliz will default to True
    - pli and poll will default to False
    - LineReader objects will default to False

    Empty lines will be flagged by warning ParseMsg objects, and ignored. Whitespace
    before comments, names, and dimensions will be flagged by warning ParseMsg objects
    as well, and ignored.

    If invalid syntax is detected within a block, an error will be created. This block
    will be ignored for the purpose of create PolyObject instances.
    Once an error is encountered, any following lines will be marked as part of the
    invalid block, until a new block is found. Note that this means that sequential
    invalid blocks will be reported as a single invalid block.

    Args:
        input_data (Union[str, Path, LineReader]):
            Path to the pli(z)/pol convention structured file
        has_z_values (Optional[bool]):
            Whether to create points containing a z-value

    Returns:
        Tuple[Sequence[PolyObject], Sequence[ParseMsg], Sequence[ParseMsg]]:
            Three sequences containing respectively:
            - The constructed PolyObject instances
            - The error ParseMsg instances encountered during parsing
            - The warning ParseMsg instances encountered during parsing
    """

    if isinstance(input_data, str):
        input_data = Path(input_data)

    # TODO: add some common file verification.

    if has_z_values is None:
        has_z_values = _determine_has_z_value(input_data)

    if isinstance(input_data, Path):
        with input_data.open("r") as f:
            return _read_poly_file(f, has_z_values)
    else:
        return _read_poly_file(input_data, has_z_values)
