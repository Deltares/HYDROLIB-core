"""parser.py defines all classes and functions related to parsing pol/pli(z) files.
"""

import warnings
from enum import IntEnum
from pathlib import Path
from typing import Callable, Dict, Iterator, List, Optional, Sequence, Tuple, Union

from hydrolib.core.basemodel import BaseModel
from hydrolib.core.io.polyfile.models import Description, Metadata, Point, PolyObject


class ParseMsg(BaseModel):
    """ParseMsg defines a single message indicating a significant parse event.

    Attributes:
        line_start (int): The start line of the block to which this ParseMsg refers.
        line_end (int): The end line of the block to which this ParseMsg refers.
        column (Optional[Tuple[int, int]]):
            An optional begin and end column to which this ParseMsg refers.
        reason (str): A human-readable string detailing the reason of the ParseMsg.
    """

    line_start: int
    line_end: int

    column: Optional[Tuple[int, int]]
    reason: str

    def notify_as_warning(self, file_path: Optional[Path] = None):
        """Call warnings.warn with a formatted string describing this ParseMsg

        Args:
            file_path (Optional[Path], optional):
                The file path mentioned in the warning if specified. Defaults to None.
        """
        if self.line_start != self.line_end:
            block_suffix = f"\nInvalid block {self.line_start}:{self.line_end}"
        else:
            block_suffix = f"\nInvalid line {self.line_start}"

        col_suffix = (
            f"\nColumns {self.column[0]}:{self.column[1]}"
            if self.column is not None
            else ""
        )
        file_suffix = f"\nFile: {file_path}" if file_path is not None else ""

        warnings.warn(f"{self.reason}{block_suffix}{col_suffix}{file_suffix}")


class Block(BaseModel):
    """Block is a temporary object which will be converted into a PolyObject.

    The fields are supposed to be set during the lifetime of this object.
    When all fields are set, finalize can be called.

    Attributes:
        start_line (int): The starting line of this current block.
        name (Optional[str]): The name of this block. Defaults to None.
        dimensions (Optional[Tuple[int, int]]):
            The dimensions (n_rows, n_columns) of this Block. Defaults to None.
        points (Optional[List[Point]]):
            The points of this block. Defaults to None.
        ws_warnings (List[ParseMsg]):
            The whitespace warnings associated with this block.
            Defaults to an empty list.
        empty_lines (List[int]):
            The line numbers of the empty lines. Defaults to an empty list.
    """

    start_line: int

    description: Optional[List[str]] = None
    name: Optional[str] = None
    dimensions: Optional[Tuple[int, int]] = None
    points: Optional[List[Point]] = None

    ws_warnings: List[ParseMsg] = []
    empty_lines: List[int] = []

    def finalize(self) -> Optional[Tuple[PolyObject, List[ParseMsg]]]:
        """Finalise this Block and return the constructed PolyObject and warnings

        If the metadata or the points are None, then None is returned.

        Returns:
            Optional[Tuple[PolyObject, List[ParseMsg]]]:
                The constructed PolyObject and warnings encountered while parsing it.
        """
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
            line_start=line_range[0],
            line_end=line_range[1],
            reason="Empty lines are ignored.",
        )


class InvalidBlock(BaseModel):
    """InvalidBlock is a temporary object which will be converted into a ParseMsg.

    Attributes:
        start_line (int): The start line of this InvalidBlock
        end_line (Optional[int]):
            The end line of this InvalidBlock if it is set. Defaults to None.
        invalid_line (int): The line which is causing this block to be invalid.
        reason (str): A human-readable string detailing the reason of the ParseMsg.
    """

    start_line: int
    end_line: Optional[int] = None
    invalid_line: int
    reason: str

    def to_msg(self) -> ParseMsg:
        """Convert this InvalidBlock to the corresponding ParseMsg

        Returns:
            ParseMsg: The ParseMsg corresponding with this InvalidBlock
        """
        return ParseMsg(
            line_start=self.start_line,
            line_end=self.end_line,
            reason=f"{self.reason} at line {self.invalid_line}.",
        )


class ErrorBuilder:
    """ErrorBuilder provides the functionality to the Parser to keep track of errors."""

    def __init__(self) -> None:
        """Create a new ErorrorBuilder"""
        self._current_block: Optional[InvalidBlock] = None

    def start_invalid_block(
        self, block_start: int, invalid_line: int, reason: str
    ) -> None:
        """Start a new invalid block if none exists at the moment

        If we are already in an invalid block, or the previous one
        was never finalised, we will not log the reason, and assume
        it is one long invalid block.

        Args:
            block_start (int): The start of the invalid block.
            invalid_line (int): The actual offending line number.
            reason (str): The reason why this block is invalid.
        """
        if self._current_block is None:
            self._current_block = InvalidBlock(
                start_line=block_start, invalid_line=invalid_line, reason=reason
            )

    def end_invalid_block(self, line: int) -> None:
        """Store the end line of the current block

        If no invalid block currently exists, nothing will be done.

        Args:
            line (int): the final line of this invalid block
        """
        if self._current_block is not None:
            self._current_block.end_line = line

    def finalize_previous_error(self) -> Optional[ParseMsg]:
        """Finalize the current invalid block if it exists

        If no current invalid block exists, None will be returned, and nothing will
        change. If a current block exists, it will be converted into a ParseMsg and
        returned. The current invalid block will be reset.

        Returns:
            Optional[ParseMsg]: The corresponding ParseMsg if an InvalidBlock exists.
        """
        if self._current_block is not None:
            msg = self._current_block.to_msg()
            self._current_block = None

            return msg
        else:
            return None


class StateType(IntEnum):
    """The types of state of a Parser."""

    NEW_BLOCK = 0
    PARSED_DESCRIPTION = 1
    PARSED_NAME = 2
    PARSING_POINTS = 3
    INVALID_STATE = 4


class Parser:
    """Parser provides the functionality to parse a polyfile line by line.

    The Parser parses blocks describing PolyObject instances by relying on
    a rudimentary state machine. The states are encoded with the StateType.
    New lines are fed through the feed_line method. After each line the
    internal state will be updated. When a complete block is read, it will
    be converted into a PolyObject and stored internally.
    When finalise is called, the constructed objects, as well as any warnings
    and errors describing invalid blocks, will be returned.

    Each state defines a feed_line method, stored in the _feed_line dict,
    which consumes a line and potentially transitions the state into the next.
    Each state further defines a finalise method, stored in the _finalise dict,
    which is called upon finalising the parser.

    Invalid states are encoded with INVALID_STATE. In this state the Parser
    attempts to find a new block, and thus looks for a new description or
    name.

    Unexpected whitespace before comments, names, and dimensions, as well as
    empty lines will generate a warning, and will be ignored by the parser.
    """

    def __init__(self, file_path: Path, has_z_value: bool = False) -> None:
        """Create a new Parser

        Args:
            file_path (Path):
                Name of the file being parsed, only used for providing proper warnings.
            has_z_value (bool, optional):
                Whether to interpret the third column as z-coordinates.
                Defaults to False.
        """
        self._has_z_value = has_z_value
        self._file_path = file_path

        self._line = 0
        self._new_block()

        self._error_builder = ErrorBuilder()

        self._poly_objects: List[PolyObject] = []

        self._current_point: int = 0

        self._feed_line: Dict[StateType, Callable[[str], None]] = {
            StateType.NEW_BLOCK: self._parse_name_or_new_description,
            StateType.PARSED_DESCRIPTION: self._parse_name_or_next_description,
            StateType.PARSED_NAME: self._parse_dimensions,
            StateType.PARSING_POINTS: self._parse_next_point,
            StateType.INVALID_STATE: self._parse_name_or_new_description,
        }

        self._finalise: Dict[StateType, Callable[[], None]] = {
            StateType.NEW_BLOCK: self._noop,
            StateType.PARSED_DESCRIPTION: self._add_current_block_as_incomplete_error,
            StateType.PARSED_NAME: self._add_current_block_as_incomplete_error,
            StateType.PARSING_POINTS: self._add_current_block_as_incomplete_error,
            StateType.INVALID_STATE: self._noop,
        }

        self._handle_ws: Dict[StateType, Callable[[str], None]] = {
            StateType.NEW_BLOCK: self._log_ws_warning,
            StateType.PARSED_DESCRIPTION: self._log_ws_warning,
            StateType.PARSED_NAME: self._log_ws_warning,
            StateType.PARSING_POINTS: self._noop,
            StateType.INVALID_STATE: self._noop,
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

    def finalize(self) -> Sequence[PolyObject]:
        """Finalize parsing and return the constructed PolyObject.

        Returns:
            PolyObject:
                A PolyObject containing the constructed PolyObject instances.
        """
        self._error_builder.end_invalid_block(self._line)
        last_error_msg = self._error_builder.finalize_previous_error()
        if last_error_msg is not None:
            self._handle_parse_msg(last_error_msg)

        self._finalise[self._state]()

        return self._poly_objects

    def _new_block(self, offset: int = 0) -> None:
        self._state = StateType.NEW_BLOCK
        self._current_block = Block(start_line=(self._line + offset))

    def _finish_block(self):
        (obj, warnings) = self._current_block.finalize()  # type: ignore
        self._poly_objects.append(obj)

        for msg in warnings:
            self._handle_parse_msg(msg)

        last_error = self._error_builder.finalize_previous_error()
        if last_error is not None:
            self._handle_parse_msg(last_error)

    def _increment_line(self) -> None:
        self._line += 1

    def _noop(self, *_, **__) -> None:
        # no operation
        pass

    def _add_current_block_as_incomplete_error(self) -> None:
        msg = ParseMsg(
            line_start=self._current_block.start_line,
            line_end=self._line,
            reason="EoF encountered before the block is finished.",
        )
        self._handle_parse_msg(msg)

    def _parse_name_or_new_description(self, line: str) -> None:
        if Parser._is_comment(line):
            self._handle_new_description(line)
        elif Parser._is_name(line):
            self._handle_parse_name(line)
        elif self._state != StateType.INVALID_STATE:
            self._handle_new_error("Expected a valid name or description")
            return

        # If we come from an invalid state, and we started a correct new block
        # we will end the previous invalid block, if it exists.
        self._error_builder.end_invalid_block(self._line)

    def _parse_name_or_next_description(self, line: str) -> None:
        if Parser._is_comment(line):
            self._handle_next_description(line)
        elif Parser._is_name(line):
            self._handle_parse_name(line)
        else:
            self._handle_new_error("Expected a valid name or description")

    def _parse_dimensions(self, line: str) -> None:
        dimensions = Parser._convert_to_dimensions(line)

        if dimensions is not None:
            self._current_block.dimensions = dimensions
            self._current_block.points = []
            self._current_point = 0
            self._state = StateType.PARSING_POINTS
        else:
            self._handle_new_error("Expected valid dimensions")

    def _parse_next_point(self, line: str) -> None:
        point = Parser._convert_to_point(
            line, self._current_block.dimensions[1], self._has_z_value  # type: ignore
        )

        if point is not None:
            self._current_block.points.append(point)  # type: ignore
            self._current_point += 1

            if self._current_block.dimensions[0] == self._current_point:  # type: ignore
                self._finish_block()
                self._new_block(offset=1)

        else:
            self._handle_new_error("Expected a valid next point")
            # we parse the line again, as it might be the first line of a new valid
            # block. For example when the invalid block was missing points.
            self._feed_line[self._state](line)

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
            self._current_block.empty_lines.append(self._line)

    def _log_ws_warning(self, line: str) -> None:
        if line[0] != " ":
            return

        end_column = len(line) - len(line.lstrip()) - 1
        self._current_block.ws_warnings.append(
            ParseMsg(
                line_start=self._line,
                line_end=self._line,
                column=(0, end_column),
                reason="White space at the start of the line is ignored.",
            )
        )

    def _handle_new_error(self, reason: str) -> None:
        self._error_builder.start_invalid_block(
            self._current_block.start_line, self._line, reason
        )
        self._state = StateType.INVALID_STATE

    def _handle_parse_msg(self, msg: ParseMsg) -> None:
        msg.notify_as_warning(self._file_path)

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
        return line.strip().startswith("*")

    @staticmethod
    def _convert_to_comment(line: str) -> str:
        return line.strip()[1:]

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

            if has_z:
                x, y, z, *data = values
            else:
                x, y, *data = values
                z = None  # type: ignore

            return Point(x=x, y=y, z=z, data=data)

        except ValueError:
            return None


def _determine_has_z_value(input_val: Union[Path, Iterator[str]]) -> bool:
    return isinstance(input_val, Path) and input_val.suffix == ".pliz"


def read_polyfile(filepath: Path, has_z_values: bool) -> Dict:
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
    extensions of the filepath:
    - .pliz will default to True
    - .pli and .pol will default to False

    Empty lines and unexpected whitespace will be flagged as warnings, and ignored.

    If invalid syntax is detected within a block, an error will be created. This block
    will be ignored for the purpose of creating PolyObject instances.
    Once an error is encountered, any following lines will be marked as part of the
    invalid block, until a new valid block is found. Note that this means that sequential
    invalid blocks will be reported as a single invalid block. Such invalid blocks will
    be reported as warnings.

    Args:
        filepath:
            Path to the pli(z)/pol convention structured file.
        has_z_values:
            Whether to create points containing a z-value. Defaults to None.

    Returns:
        Dict: The dictionary describing the data of a PolyObject.
    """
    if has_z_values is None:
        has_z_values = _determine_has_z_value(filepath)

    parser = Parser(filepath, has_z_value=has_z_values)

    with filepath.open("r") as f:
        for line in f:
            parser.feed_line(line)

    objs = parser.finalize()

    return {"has_z_values": has_z_values, "objects": objs}
