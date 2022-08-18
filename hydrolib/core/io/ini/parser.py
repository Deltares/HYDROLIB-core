import re
from enum import IntEnum
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Union

from pydantic import validator

from hydrolib.core.basemodel import BaseModel
from hydrolib.core.io.ini.io_models import CommentBlock, Document, Property, Section


class ParserConfig(BaseModel):
    """ParserConfig defines the configuration options of the Parser

    Note that we cannot set both allow_only_keywords and parse_datablocks to True
    because we cannot distinguish between datablocks and key only properties. As
    such this will lead to a validation error.

    Attributes:
        allow_only_keywords (bool):
            Whether to allow properties with only keys (no '=' or value).
            Defaults to True.
        parse_datablocks (bool):
            Whether to allow parsing of datablocks at the bottom of sections.
            Defaults to False.
        parse_comments (bool):
            Whether we allow parsing of comments defined with the comment_delimeter.
            Defaults to True.
        comment_delimiter (str):
            The character or sequence of character used to define a comment.
            Defaults to '#'.
    """

    allow_only_keywords: bool = False
    parse_datablocks: bool = False
    parse_comments: bool = True
    comment_delimiter: str = "#"

    @validator("parse_datablocks")
    def allow_only_keywods_and_parse_datablocks_leads_should_not_both_be_true(
        cls, parse_datablocks, values
    ):
        # if both allow_only_keywords and parse_datablocks is true, we cannot
        # distinguish between the two, and the parsing will not recognise either
        # properly
        if (
            parse_datablocks
            and "allow_only_keywords" in values
            and values["allow_only_keywords"]
        ):
            raise ValueError(
                "Both parse_datablocks and allow_only_keywords should not be both True."
            )
        return parse_datablocks


class _IntermediateCommentBlock(BaseModel):
    # _IntermediateCommentBlock used to construct CommentBlock objects within
    # this Parser.
    start_line: int
    lines: List[str] = []

    def add_comment_line(self, line: str) -> None:
        self.lines.append(line)

    def finalize(self) -> CommentBlock:
        return CommentBlock(
            lines=self.lines,
        )


class _IntermediateSection(BaseModel):
    # _IntermediateSection used to construct section objects within
    # this Parser.
    header: str
    start_line: int

    content: List[Union[Property, CommentBlock]] = []
    datablock: List[List[str]] = []
    curr_comment_block: Optional[_IntermediateCommentBlock] = None

    def add_property(self, property: Property) -> None:
        self._finalize_comment_block()
        self.content.append(property)

    def add_comment(self, comment: str, line: int) -> None:
        if self.curr_comment_block is None:
            self.curr_comment_block = _IntermediateCommentBlock(start_line=line)

        self.curr_comment_block.add_comment_line(comment)

    def add_datarow(self, row: List[str]) -> None:
        self.datablock.append(row)

    def _finalize_comment_block(self) -> None:
        if self.curr_comment_block is None:
            return

        self.content.append(self.curr_comment_block.finalize())
        self.curr_comment_block = None

    def finalize(self) -> Section:
        self._finalize_comment_block()
        return Section(
            header=self.header,
            content=self.content,
            datablock=self.datablock if self.datablock else None,
        )


# TODO: generalise StateBasedLineParser, and let both Ini.Parser and Polyfile.Parser inherit
class Parser:
    """Parser defines a generic Parser for Deltares ini files.

    The Parser can be configured with a ParserConfig object.
    """

    class _StateType(IntEnum):
        NO_SECTION_FOUND = 0
        PARSING_PROPERTIES = 1
        PARSING_DATABLOCK = 2

    def __init__(self, config: ParserConfig) -> None:
        """Creates a new Parser configured with the provided config

        Args:
            config (ParserConfig): The configuration of this Parser
        """
        self._config = config
        self._document = Document()
        self._current_section: Optional[_IntermediateSection] = None
        self._current_header_block: Optional[_IntermediateCommentBlock] = None

        self._state = self._StateType.NO_SECTION_FOUND
        self._line_index = 0

        # TODO add invalid blocks
        self._feed_line: Dict[
            Parser._StateType, List[Tuple[Callable[[str], bool], Callable[[str], None]]]
        ] = {
            Parser._StateType.NO_SECTION_FOUND: [
                (self._is_comment, self._handle_header_comment),
                (self._is_section_header, self._handle_next_section_header),
            ],
            Parser._StateType.PARSING_PROPERTIES: [
                (self._is_comment, self._handle_section_comment),
                (self._is_section_header, self._handle_next_section_header),
                (self._is_property, self._handle_property),
                (self._is_datarow, self._handle_new_datarow),
            ],
            Parser._StateType.PARSING_DATABLOCK: [
                (self._is_section_header, self._handle_next_section_header),
                (self._is_datarow, self._handle_datarow),
            ],
        }

        self._handle_emptyline: Dict[Parser._StateType, Callable[[], None]] = {
            self._StateType.NO_SECTION_FOUND: self._finish_current_header_block,
            self._StateType.PARSING_PROPERTIES: self._noop,
            self._StateType.PARSING_DATABLOCK: self._noop,
        }

    def feed_line(self, line: str) -> None:
        """Parse the next line with this Parser.

        Args:
            line (str): The line to parse
        """
        if not self._is_empty_line(line):
            for (is_line_type, handle_line_type) in self._feed_line[self._state]:
                if is_line_type(line):
                    handle_line_type(line)
                    break
            else:
                # handle exception
                pass
        else:
            self._handle_emptyline[self._state]()

        self._increment_line()

    def finalize(self) -> Document:
        """Finalize parsing and return the constructed Document.

        Returns:
            Document:
                A Document describing the parsed ini file.
        """
        # TODO handle invalid block
        self._finish_current_header_block()
        self._finalise_current_section()
        return self._document

    def _increment_line(self) -> None:
        self._line_index += 1

    def _handle_next_section_header(self, line: str) -> None:
        self._finalise_current_section()
        self._handle_new_section_header(line)

        self._state = Parser._StateType.PARSING_PROPERTIES

    def _handle_new_section_header(self, line: str) -> None:
        section_header = line.strip()[1:-1].strip()
        self._current_section = _IntermediateSection(
            header=section_header, start_line=self._line_index
        )

    def _finalise_current_section(self) -> None:
        if self._current_section is not None:
            self._document.sections.append(self._current_section.finalize())

    def _handle_header_comment(self, line: str) -> None:
        if self._current_header_block is None:
            self._current_header_block = _IntermediateCommentBlock(
                start_line=self._line_index
            )

        comment = self._convert_to_comment(line)
        self._current_header_block.add_comment_line(comment)

    def _handle_section_comment(self, line: str) -> None:
        comment = self._convert_to_comment(line)
        self._current_section.add_comment(comment, self._line_index)  # type: ignore

    def _handle_property(self, line: str) -> None:
        key, valuepart = self._retrieve_key_value(line)
        if valuepart is not None:
            comment, value = self._retrieve_property_comment(valuepart.strip())
        else:
            comment, value = None, None

        prop = Property(key=key, value=value, comment=comment)
        self._current_section.add_property(prop)  # type: ignore

    def _handle_new_datarow(self, line: str) -> None:
        self._handle_datarow(line)
        self._state = Parser._StateType.PARSING_DATABLOCK

    def _handle_datarow(self, line: str) -> None:
        self._current_section.add_datarow(line.split())  # type: ignore

    def _retrieve_property_comment(self, line: str) -> Tuple[Optional[str], str]:
        """Retrieve the comment and value part from the valuestring of a key-value pair.

        The comment retrieval is complicated by the fact that in the Deltares-INI
        dialect, the comment delimiter '#' plays a double role: it may also be used
        to quote string values (for example if the contain spaces).

        Example lines that are supported:
        key = valueAndNoComment
        key = valueA  # and a simple comment
        key = #valueA with possible spaces#
        key = #valueA#  # and a simple comment
        key = #valueA# # and a complicated comment with hashes #1 example
        key = value # and a complicated comment with hashes #2.

        Keywords arguments:
            line (str) -- the partial string of the line containing both value and
                possibly a comment at the end. Note that the "key =" part must already
                have been split off, for example by _retrieve_key_value

        Returns:
            Tuple with the comment and string value, respectively. If no comment is
            present, the first tuple element is None.
        """

        if self._config.parse_comments and self._config.comment_delimiter in line:
            line = line.strip()
            parts = line.split(self._config.comment_delimiter)
            numhash = line.count(self._config.comment_delimiter)
            if numhash == 1:
                # normal value, simple comment: "key =  somevalue # and a comment "
                comment = parts[-1]
                value = parts[0]
            elif line.startswith(self._config.comment_delimiter):
                # hashed value, possible with comment: "key = #somevalue# ..."
                comment = (
                    self._config.comment_delimiter.join(parts[3:])
                    if numhash >= 3
                    else ""
                )

                value = self._config.comment_delimiter.join(parts[0:3])
            else:
                # normal value, comment with maybe more hashes: "key = somevalue #This is comment #2, or two "
                comment = self._config.comment_delimiter.join(parts[1:])
                value = parts[0]
        else:
            comment = ""
            value = line

        return (
            comment if len(comment := comment.strip()) > 0 else None,
            value if len(value := value.strip()) > 0 else None,
        )

    def _retrieve_key_value(self, line: str) -> Tuple[str, Optional[str]]:
        if "=" in line:
            key, value = line.split("=", 1)
            return key.strip(), value if len(value := value.strip()) > 0 else None
        else:
            # if no = exists, due to the previous check we know it will just be a
            # single value
            return line, None

    def _finish_current_header_block(self) -> None:
        if self._current_header_block is not None:
            self._document.header_comment.append(self._current_header_block.finalize())
            self._current_header_block = None

    def _noop(self, *_, **__) -> None:
        # no operation
        pass

    def _is_empty_line(self, line: str) -> bool:
        return len(line.strip()) == 0

    def _is_comment(self, line: str) -> bool:
        return line.strip().startswith(self._config.comment_delimiter)

    def _convert_to_comment(self, line: str) -> str:
        return line.strip()[1:].strip()

    def _is_section_header(self, line: str) -> bool:
        # a header is defined as "[ any-value ]"
        stripped = line.strip()
        return stripped.startswith("[") and stripped.endswith("]")

    def _is_property(self, line: str) -> bool:
        # we assume that we already checked wether it is a comment or
        # a section header.
        return self._config.allow_only_keywords or "=" in line

    def _is_datarow(self, _: str) -> bool:
        # we assume that we already checked whether it is either a comment,
        # section header or a property
        return self._config.parse_datablocks

    @classmethod
    def parse_as_dict(cls, filepath: Path, config: ParserConfig = None) -> dict:
        """
        Parses an INI file without a specific model type and returns it as a dictionary.

        Args:
            filepath (Path): File path to the INI-format file.
            config (ParserConfig, optional): Parser configuration to use. Defaults to None.

        Returns:
            dict: Representation of the parsed INI-file.
        """
        return cls.parse(filepath, config).flatten()

    @classmethod
    def parse(cls, filepath: Path, config: ParserConfig = None) -> Document:
        """
        Parses an INI file without a specific model type and returns it as a Document.

        Args:
            filepath (Path): File path to the INI-format file.
            config (ParserConfig, optional): Parser configuration to use. Defaults to None.

        Returns:
            Document: Representation of the parsed INI-file.
        """
        if not config:
            config = ParserConfig()
        parser = cls(config)

        progline = re.compile(
            r"^([^#]*=\s*)([^#]*)(#.*)?"
        )  # matches whole line: "Field = Value Maybe more # optional comment"
        progfloat = re.compile(
            r"([\d.]+)([dD])([+\-]?\d+)"
        )  # matches a float value: 1d9, 1D-3, 1.D+4, etc.

        with filepath.open() as f:
            for line in f:
                # Replace Fortran scientific notation for doubles
                # Match number d/D +/- number (e.g. 1d-05 or 1.23D+01 or 1.d-4)
                match = progline.match(line)
                if match:  # Only process value
                    line = (
                        match.group(1)
                        + progfloat.sub(r"\1e\3", match.group(2))
                        + str(match.group(3) or "")
                    )
                else:  # Process full line
                    line = progfloat.sub(r"\1e\3", line)

                parser.feed_line(line)

        return parser.finalize()
