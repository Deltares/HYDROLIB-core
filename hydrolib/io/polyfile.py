"""polyfily.py defines all classes and functions related to handling pol/pli(z) files.
"""

from enum import Enum
from hydrolib.io.common import ParseMsg, BaseModel
from functools import reduce
from typing import Callable, Dict, List, Optional, Sequence, Tuple


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

    def get_description(self) -> Optional[Description]:
        if self.description is not None:
            return Description(content="\n".join(self.description))
        else:
            return None

    def get_metadata(self) -> Optional[Metadata]:
        if self.name is None or self.dimensions is None:
            return None

        (n_rows, n_columns) = self.dimensions
        return Metadata(name=self.name, n_rows=n_rows, n_columns=n_columns)


class StateType(Enum):
    """The types of state of a Parser."""

    NEW_BLOCK = 0
    PARSED_DESCRIPTION = 1
    PARSED_NAME = 2
    PARSING_POINTS = 3


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

    def feed_line(self, line: str) -> None:
        """Parse the next line with this Parser.

        Args:
            line (str): The line to parse
        """
        self._feed_line[self._state](line)
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
        self._poly_objects.append(
            PolyObject(
                description=self._current_block.get_description(),
                metadata=self._current_block.get_metadata(),  # type: ignore
                points=self._current_block.points,
            )
        )
        # handle error here

    def _increment_line(self) -> None:
        self._line += 1

    def _noop(self) -> None:
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
