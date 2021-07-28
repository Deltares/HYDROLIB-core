from dataclasses import dataclass
from functools import reduce
from hydrolib.core.io.ini.models import CommentBlock, Document, Property, Section
from hydrolib.core.basemodel import BaseModel
from itertools import chain, count, repeat
from pathlib import Path
from typing import Any, Iterable, List, Optional, Sequence, Tuple, Union


class SerializerConfig(BaseModel):
    """SerializerConfig defines the configuration options of the Serializer

    Attributes:
        section_indent (int):
            The number of spaces with which whole sections should be indented.
            Defaults to 0.
        property_indent (int):
            The number of spaces with which properties should be indented relative to
            the section header (i.e. the full indent equals the section_indent plus
            property_indent). Defaults to 4.
        datablock_indent (int):
            The number of spaces with which datablock rows are indented relative to
            the section header (i.e. the full indent equals the section_indent plus
            datablock_indent). Defaults to 8.
        datablock_spacing (int):
            The number of spaces between datablock columns. Note that there might be
            additional offset to ensure . is lined out. Defaults to 4.
        comment_delimiter (str):
            The character used to delimit comments.
    """

    section_indent: int = 0
    property_indent: int = 4
    datablock_indent: int = 8
    datablock_spacing: int = 4
    comment_delimiter: str = "#"

    @property
    def total_property_indent(self):
        return self.section_indent + self.property_indent

    @property
    def total_datablock_indent(self):
        return self.section_indent + self.datablock_indent


@dataclass
class _Lengths:
    max_key_length: int
    max_value_length: int
    max_datablock_element_length: Optional[Sequence[int]] = None

    @staticmethod
    def _calculate_max_length_datablock(
        datablock: Optional[Sequence[Sequence[str]]],
    ) -> Optional[Sequence[int]]:
        if datablock is None or len(datablock) < 1:
            return None

        def folder(acc: Tuple, row: Sequence[str]) -> Tuple:
            return tuple(max(curr_max, len(elem)) for curr_max, elem in zip(acc, row))

        return reduce(folder, datablock, (0,) * len(datablock[0]))

    @classmethod
    def from_section(cls, section: Section):
        properties = list(
            prop for prop in section.content if isinstance(prop, Property)
        )

        max_key_length = max(len(prop.key) for prop in properties)
        max_value_length = max(
            len(prop.value) if prop.value is not None else 0 for prop in properties
        )

        return cls(
            max_key_length=max_key_length,
            max_value_length=max_value_length,
            max_datablock_element_length=_Lengths._calculate_max_length_datablock(
                section.datablock
            ),
        )


class Serializer:
    def __init__(self, config: SerializerConfig):
        self._config = config

    @staticmethod
    def _interweave(iterable: Iterable, val: Any) -> Iterable:
        # Note that this will interweave with val without making copies
        # as such it is the same object being interweaved.
        return chain.from_iterable(zip(iterable, repeat(val)))

    def _serialize_comment_block(
        self, block: CommentBlock, indent_size: int = 0
    ) -> Iterable[str]:
        indent = " " * indent_size
        return (f"{indent}{self._config.comment_delimiter} {l}" for l in block.lines)

    def _serialize_comment_header(
        self, header_blocks: Iterable[CommentBlock]
    ) -> Iterable[str]:
        blocks_as_lines = (
            self._serialize_comment_block(block) for block in header_blocks
        )
        blocks_as_lines = Serializer._interweave(blocks_as_lines, [""])  # type: ignore

        return chain.from_iterable(blocks_as_lines)

    def _serialize_section_header(self, section_header: str) -> Iterable[str]:
        return [
            f"{self._config.section_indent}[{section_header}]",
        ]

    @staticmethod
    def _get_offset(key: Optional[str], max_length: int) -> str:
        key_length = len(key) if key is not None else 0
        return " " * max(max_length - key_length, 0)

    def _serialize_property(
        self, property: Property, lengths: _Lengths
    ) -> Iterable[str]:
        indent = " " * (self._config.total_property_indent)
        key_offset = Serializer._get_offset(property.key, lengths.max_key_length)
        value_offset = Serializer._get_offset(property.value, lengths.max_key_length)

        return [
            f"{indent}{property.key}{key_offset} = {property.value}{value_offset} # {property.comment}"
        ]

    def _serialize_content(
        self, content: Iterable[Union[Property, CommentBlock]], lengths: _Lengths
    ) -> Iterable[str]:
        def serialize_element(elem: Union[Property, CommentBlock]) -> Iterable[str]:
            if isinstance(elem, Property):
                return self._serialize_property(elem, lengths)
            else:
                return self._serialize_comment_block(
                    elem, self._config.total_property_indent
                )

        return chain.from_iterable((serialize_element(elem) for elem in content))

    def _serialize_datablock(
        self, datablock: Optional[Iterable[Sequence[str]]], lengths: _Lengths
    ) -> Iterable[str]:
        if datablock is None or lengths.max_datablock_element_length is None:
            return []

        def serialize_row_element(elem: str, index: int) -> str:
            offset = Serializer._get_offset(elem, lengths.max_datablock_element_length[index])  # type: ignore
            return elem + offset

        indent = " " * self._config.total_datablock_indent

        def serialize_row(row: Sequence[str]) -> str:
            return indent + (" " * self._config.datablock_spacing).join(
                (serialize_row_element(elem, i)) for elem, i in zip(row, count())
            )

        return (serialize_row(row) for row in datablock)

    def _serialize_section(self, section: Section) -> Iterable[str]:
        lengths = _Lengths.from_section(section)
        header_iterable = self._serialize_section_header(section.header)
        properties = self._serialize_content(section.content, lengths)
        datablock = self._serialize_datablock(section.datablock, lengths)

        return chain(
            header_iterable,
            properties,
            datablock,
        )

    def serialize(self, document: Document) -> Iterable[str]:
        """Serialize the provided document into an iterable of lines."""
        header_iterable = self._serialize_comment_header(document.header_comment)
        sections_iterable = chain.from_iterable(
            (self._serialize_section(section) for section in document.sections)
        )
        sections_iterable = Serializer._interweave(sections_iterable, [""])  # type: ignore
        return chain(header_iterable, sections_iterable)


def write_ini(
    path: Path, document: Document, config: Optional[SerializerConfig] = None
) -> None:
    if config is None:
        config = SerializerConfig()

    serializer = Serializer(config)

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w") as f:

        for line in serializer.serialize(document):
            f.write(line)
            f.write("\n")
