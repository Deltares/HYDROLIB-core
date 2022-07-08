from itertools import chain, count, repeat
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence

from hydrolib.core.basemodel import BaseModel
from hydrolib.core.io.ini.io_models import (
    CommentBlock,
    ContentElement,
    Datablock,
    DatablockRow,
    Document,
    Property,
    Section,
)


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
            The character used to delimit comments. Defaults to '#'.
    """

    section_indent: int = 0
    property_indent: int = 4
    datablock_indent: int = 8
    datablock_spacing: int = 4
    comment_delimiter: str = "#"

    @property
    def total_property_indent(self) -> int:
        """The combined property indentation, i.e. section_indent + property_indent"""
        return self.section_indent + self.property_indent

    @property
    def total_datablock_indent(self) -> int:
        """The combined datablock indentation, i.e. section_indent + datablock_indent"""
        return self.section_indent + self.datablock_indent


class MaxLengths(BaseModel):
    """MaxLengths defines the maxmimum lengths of the parts of a section

    Attributes:
        key (int):
            The maximum length of all the keys of the properties within a section.
            If no properties are present it should be 0.
        value (int):
            The maximum length of all the non None values of the properties within a
            section. If no properties are present, or all values are None, it should
            be 0.
        datablock (Optional[Sequence[int]]):
            The maximum length of the values of each column of the Datablock.
            If no datablock is present it defaults to None.
    """

    key: int
    value: int
    datablock: Optional[Sequence[int]] = None

    @classmethod
    def from_section(cls, section: Section) -> "MaxLengths":
        """Generate a MaxLengths instance from the given Section

        Args:
            section (Section): The section of which the MaxLengths are calculated

        Returns:
            MaxLengths: The MaxLengths corresponding with the provided section
        """
        properties = list(p for p in section.content if isinstance(p, Property))

        keys = (prop.key for prop in properties)
        values = (prop.value for prop in properties if prop.value is not None)

        max_key_length = max((len(k) for k in keys), default=0)
        max_value_length = max((len(v) for v in values), default=0)
        max_datablock_lengths = MaxLengths._of_datablock(section.datablock)

        return cls(
            key=max_key_length,
            value=max_value_length,
            datablock=max_datablock_lengths,
        )

    @staticmethod
    def _of_datablock(datablock: Optional[Datablock]) -> Optional[Sequence[int]]:
        if datablock is None or len(datablock) < 1:
            return None

        datablock_columns = map(list, zip(*datablock))
        datablock_column_lengths = (map(len, column) for column in datablock_columns)  # type: ignore
        max_lengths = (max(column) for column in datablock_column_lengths)

        return tuple(max_lengths)


Lines = Iterable[str]


def _serialize_comment_block(
    block: CommentBlock,
    delimiter: str = "#",
    indent_size: int = 0,
) -> Lines:
    indent = " " * indent_size
    return (f"{indent}{delimiter} {l}" for l in block.lines)


def _get_offset_whitespace(key: Optional[str], max_length: int) -> str:
    key_length = len(key) if key is not None else 0
    return " " * max(max_length - key_length, 0)


class SectionSerializer:
    """SectionSerializer provides the serialize method to serialize a Section

    The entrypoint of this method is the serialize method, which will construct
    an actual instance and serializes the Section with it.
    """

    def __init__(self, config: SerializerConfig, max_length: MaxLengths):
        """Create a new SectionSerializer

        Args:
            config (SerializerConfig): The config describing the serialization options
            max_length (MaxLengths): The max lengths of the section being serialized
        """
        self._config = config
        self._max_length = max_length

    @classmethod
    def serialize(cls, section: Section, config: SerializerConfig) -> Lines:
        """Serialize the provided section with the given config

        Args:
            section (Section): The section to serialize
            config (SerializerConfig): The config describing the serialization options

        Returns:
            Lines: The iterable lines of the serialized section
        """
        serializer = cls(config, MaxLengths.from_section(section))
        return serializer._serialize_section(section)

    @property
    def config(self) -> SerializerConfig:
        """The SerializerConfig used while serializing the section."""
        return self._config

    @property
    def max_length(self) -> MaxLengths:
        """The MaxLengths of the Section being serialized by this SectionSerializer."""
        return self._max_length

    def _serialize_section(self, section: Section) -> Lines:
        header_iterable = self._serialize_section_header(section.header)
        properties = self._serialize_content(section.content)
        datablock = self._serialize_datablock(section.datablock)

        return chain(header_iterable, properties, datablock)

    def _serialize_section_header(self, section_header: str) -> Lines:
        indent = " " * (self.config.section_indent)
        yield f"{indent}[{section_header}]"

    def _serialize_content(self, content: Iterable[ContentElement]) -> Lines:
        elements = (self._serialize_content_element(elem) for elem in content)
        return chain.from_iterable(elements)

    def _serialize_content_element(self, elem: ContentElement) -> Lines:
        if isinstance(elem, Property):
            return self._serialize_property(elem)
        else:
            indent = self.config.total_property_indent
            delimiter = self.config.comment_delimiter
            return _serialize_comment_block(elem, delimiter, indent)

    def _serialize_property(self, property: Property) -> Lines:
        indent = " " * (self._config.total_property_indent)
        key_ws = _get_offset_whitespace(property.key, self.max_length.key)
        key = f"{property.key}{key_ws} = "

        value_ws = _get_offset_whitespace(property.value, self.max_length.value)

        if property.value is not None:
            value = f"{property.value}{value_ws}"
        else:
            value = value_ws

        comment = f" # {property.comment}" if property.comment is not None else ""

        yield f"{indent}{key}{value}{comment}".rstrip()

    def _serialize_datablock(self, datablock: Optional[Datablock]) -> Lines:
        if datablock is None or self.max_length.datablock is None:
            return []

        indent = " " * self._config.total_datablock_indent
        return (self._serialize_row(row, indent) for row in datablock)

    def _serialize_row(self, row: DatablockRow, indent: str) -> str:
        elem_spacing = " " * self.config.datablock_spacing
        elems = (self._serialize_row_element(elem, i) for elem, i in zip(row, count()))

        return indent + elem_spacing.join(elems).rstrip()

    def _serialize_row_element(self, elem: str, index: int) -> str:
        max_length = self.max_length.datablock[index]  # type: ignore
        whitespace = _get_offset_whitespace(elem, max_length)
        return elem + whitespace


class Serializer:
    """Serializer serializes Document to its corresponding lines."""

    def __init__(self, config: SerializerConfig):
        """Creates a new Serializer with the provided configuration.

        Args:
            config (SerializerConfig): The configuration of this Serializer.
        """
        self._config = config

    def serialize(self, document: Document) -> Lines:
        """Serialize the provided document into an iterable of lines.

        Args:
            document (Document): The Document to serialize.

        Returns:
            Lines: An iterable returning each line of the serialized Document.
        """
        header_iterable = self._serialize_document_header(document.header_comment)

        serialize_section = lambda s: SectionSerializer.serialize(s, self._config)
        sections = (serialize_section(section) for section in document.sections)
        sections_with_spacing = Serializer._interweave(sections, [""])
        sections_iterable = chain.from_iterable(sections_with_spacing)

        return chain(header_iterable, sections_iterable)

    def _serialize_document_header(self, header: Iterable[CommentBlock]) -> Lines:
        delimiter = self._config.comment_delimiter
        serialize = lambda cb: _serialize_comment_block(cb, delimiter)
        blocks = (serialize(block) for block in header)
        blocks_with_spacing = Serializer._interweave(blocks, [""])

        return chain.from_iterable(blocks_with_spacing)

    @staticmethod
    def _interweave(iterable: Iterable, val: Any) -> Iterable:
        # Interweave the provided iterable with the provided value:
        # iterable_element, val, iterable_element, val, ...

        # Note that this will interweave with val without making copies
        # as such it is the same object being interweaved.
        return chain.from_iterable(zip(iterable, repeat(val)))


def write_ini(
    path: Path,
    document: Document,
    config: Optional[SerializerConfig] = None,
) -> None:
    """Write the provided document to the specified path

    If the provided path already exists, it will be overwritten. If the parent folder
    do not exist, they will be created.

    Args:
        path (Path): The path to which the document should be written.
        document (Document): The document to serialize to the specified path.
        config (Optional[SerializerConfig], optional):
            An optional configuration of the serializer. If none provided, it will
            default to the standard SerializerConfig. Defaults to None.
    """
    if config is None:
        config = SerializerConfig()

    serializer = Serializer(config)

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("wb") as f:

        for line in serializer.serialize(document):
            f.write((line + "\n").encode("utf8"))
