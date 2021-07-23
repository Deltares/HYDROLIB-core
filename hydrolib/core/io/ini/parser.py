from enum import IntEnum
from hydrolib.core.basemodel import BaseModel
from pydantic import validator
from typing import Callable, Dict, List, Optional, Sequence, Tuple, Union


class StateType(IntEnum):
    NO_SECTION_FOUND = 0
    PARSING_PROPERTIES = 1
    PARSING_DATABLOCK = 2


# DataAccess objects
class CommentBlock(BaseModel):
    start_line: int
    end_line: int
    lines: List[str]


class Property(BaseModel):
    line: int
    key: str
    value: Optional[str]
    comment: Optional[str]


class Section(BaseModel):
    header: str
    start_line: int
    end_line: int
    content: List[Union[Property, CommentBlock]]

    # these are primarily relevant for bc files
    datablock: Optional[Sequence[Sequence[str]]]


class IntermediateCommentBlock(BaseModel):
    start_line: int
    _lines: List[str] = []

    def add_comment_line(self, line: str) -> None:
        self._lines.append(line)

    def finalize(self) -> CommentBlock:
        return CommentBlock(
            start_line=self.start_line,
            end_line=self.start_line + len(self._lines) - 1,
            lines=self._lines,
        )


# Intermediate objects
class IntermediateSection(BaseModel):
    header: str
    start_line: int
    _content: List[Union[Property, CommentBlock]] = []
    _datablock: List[List[str]] = []
    _curr_comment_block: Optional[IntermediateCommentBlock]

    def add_property(self, property: Property) -> None:
        self._finalize_comment_block()
        self._content.append(property)

    def add_comment(self, comment: str, line: int) -> None:
        if self._curr_comment_block is None:
            self._curr_comment_block = IntermediateCommentBlock(start_line=line)
        self._curr_comment_block.add_comment_line(comment)

    def add_datarow(self, row: List[str]) -> None:
        self._datablock.append(row)

    def _finalize_comment_block(self) -> None:
        if self._curr_comment_block is None:
            return

        self._content.append(self._curr_comment_block.finalize())
        self._curr_comment_block = None

    def finalize(self, end_line) -> Section:
        self._finalize_comment_block()
        return Section(
            header=self.header,
            start_line=self.start_line,
            end_line=end_line,
            content=self._content,
            datablock=self._datablock if self._datablock else None,
        )


class Document(BaseModel):
    header_comment: List[CommentBlock] = []
    sections: List[Section] = []


class RuleSet(BaseModel):
    allow_recurrent_section_names: bool = True
    allow_recurrent_properties: bool = True
    comment_character: str = "#"  # this should be moved to the parser


class ParserConfig(BaseModel):
    """ParserConfig defines the configuration options of the Parser"""

    allow_only_keywords: bool = True
    parse_datablocks: bool = False
    parse_comments: bool = True
    comment_delimeter: str = "#"

    @validator("parse_datablocks")
    def allow_only_keywods_and_parse_datablocks_leads_should_not_both_be_true(
        cls, parse_data_blocks, values
    ):
        # if both allow_only_keywords and parse_datablocks is true, we cannot
        # distinguish between the two, and the parsing will not recognise either
        # properly
        if (
            parse_data_blocks
            and "allow_only_keywords" in values
            and values["allow_only_keywords"]
        ):
            raise ValueError(
                "Both parse_datablocks and allow_only_keywords should not be both True."
            )


# TODO: generalise StateBasedLineParser, and let both Ini.Parser and Polyfile.Parser inherit
class Parser:
    def __init__(self, config: ParserConfig) -> None:
        self._config = config
        self._document = Document()
        self._current_section: Optional[IntermediateSection] = None
        self._current_header_block: Optional[IntermediateCommentBlock] = None

        self._state = StateType.NO_SECTION_FOUND
        self._line_index = 0

        # TODO add invalid blocks
        self._feed_line: Dict[
            StateType, List[Tuple[Callable[[str], bool], Callable[[str], None]]]
        ] = {
            StateType.NO_SECTION_FOUND: [
                (self._is_comment, self._handle_header_comment),
                (self._is_section_header, self._handle_next_section_header),
            ],
            StateType.PARSING_PROPERTIES: [
                (self._is_comment, self._handle_section_comment),
                (self._is_section_header, self._handle_next_section_header),
                (self._is_property, self._handle_property),
                (self._is_datarow, self._handle_new_datarow),
            ],
            StateType.PARSING_DATABLOCK: [
                (self._is_section_header, self._handle_next_section_header),
                (self._is_datarow, self._handle_datarow),
            ],
        }

        self._handle_emptyline: Dict[StateType, Callable[[], None]] = {
            StateType.NO_SECTION_FOUND: self._handle_emptyline_header,
            StateType.PARSING_PROPERTIES: self._noop,
            StateType.PARSING_DATABLOCK: self._noop,
        }

    def feed_line(self, line: str) -> None:
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
        # TODO handle invalid block
        self._finalise_current_section()
        return self._document

    def _increment_line(self) -> None:
        self._line_index += 1

    def _handle_next_section_header(self, line: str) -> None:
        self._finalise_current_section()
        self._handle_new_section_header(line)

        self._state = StateType.PARSING_PROPERTIES

    def _handle_new_section_header(self, line: str) -> None:
        section_header = line.strip()[1:-1].strip()
        self._current_section = IntermediateSection(
            header=section_header, line=self._line_index
        )

    def _finalise_current_section(self) -> None:
        if self._current_section is not None:
            self._document.sections.append(
                self._current_section.finalize(self._line_index)
            )

    def _handle_header_comment(self, line: str) -> None:
        if self._current_header_block is None:
            self._current_header_block = IntermediateCommentBlock(
                start_line=self._line_index
            )

        comment = self._convert_to_comment(line)
        self._current_header_block.add_comment_line(comment)

    def _handle_section_comment(self, line: str) -> None:
        comment = self._convert_to_comment(line)
        self._current_section.add_comment(comment, self._line_index)  # type: ignore

    def _handle_property(self, line: str) -> None:
        comment, line = self._retrieve_property_comment(line.strip())
        key, value = self._retrieve_key_value(line)

        prop = Property(key=key, value=value, comment=comment, line=self._line_index)
        self._current_section.add_property(prop)  # type: ignore

    def _handle_new_datarow(self, line: str) -> None:
        self._handle_datarow(line)
        self._state = StateType.PARSING_DATABLOCK

    def _handle_datarow(self, line: str) -> None:
        self._current_section.add_datarow(line.split(" "))  # type: ignore

    def _retrieve_property_comment(self, line: str) -> Tuple[Optional[str], str]:
        if self._config.parse_comments and self._config.comment_delimeter in line:
            key_value, comment = line.split(self._config.comment_delimeter, 1)
            return comment, key_value.strip()
        else:
            return None, line.strip()

    def _retrieve_key_value(self, line: str) -> Tuple[str, Optional[str]]:
        if "=" in line:
            key, value = line.split("=", 1)
            return key.strip(), value.strip()
        else:
            # if no = exists, due to the previous check we know it will just be a
            # single value
            return line, None

    def _handle_emptyline_header(self) -> None:
        if self._current_header_block is not None:
            self._document.header_comment.append(self._current_header_block.finalize())
            self._current_description_header_block = None

    def _noop(self, *_, **__) -> None:
        # no operation
        pass

    def _is_empty_line(self, line: str) -> bool:
        return len(line.strip()) == 0

    def _is_comment(self, line: str) -> bool:
        return line.strip().startswith(self._config.comment_delimeter)

    def _convert_to_comment(self, line: str) -> str:
        return line.strip()[1:]

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
