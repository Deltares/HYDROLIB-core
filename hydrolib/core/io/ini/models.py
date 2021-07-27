from abc import ABC
from hydrolib.core.basemodel import BaseModel
from pydantic.main import Extra
from typing import Any, Dict, List, Optional, Sequence, Type, Union


class CommentBlock(BaseModel):
    """CommentBlock defines a comment block within a deltares ini file.

    Attributes:
        start_line (int): The start line index of the CommentBlock within the file
        end_line (int): The end line index of the CommentBlock within the file
        lines (List[str]): The actual lines of the CommentBlock
    """

    start_line: int
    end_line: int
    lines: List[str]


class Property(BaseModel):
    """Property defines a deltares ini property

    Attributes:
        line (int): The line index on which this Property is defined
        key (str): The key of this Property
        value (Optional[str]): The value associated with this Property
        comment (Optional[str]): The comment associated with this Property
    """

    line: int
    key: str
    value: Optional[str]
    comment: Optional[str]


class Section(BaseModel):
    """Section defines a deltares ini section

    A deltares ini section consists of a header and an ordered list of
    properties and comments.

    For example:

    ```
    [header-title]
    a=1
    b=2
    # and a comment
    c=4
    ```

    An optional datablock can be defined (used in for example .bc files).

    Attributes:
        header (str): The header (without brackets) of this Section
        start_line (int): The starting line index of this Section block
        end_line (int): The end line index of this Section block
        content (List[Union[Property, CommentBlock]]):
            The ordered list of Property and CommentBlock objects
        datablock (Optional[Sequence[Sequence[str]]]):
            An optional data block associated with this Section
    """

    header: str
    start_line: int
    end_line: int
    content: List[Union[Property, CommentBlock]]

    # these are primarily relevant for bc files
    datablock: Optional[Sequence[Sequence[str]]]


class Document(BaseModel):
    """Document defines a Deltares ini document

    Attributes:
        header_comment (List[CommentBlock]):
            An ordered list of comment blocks defined in the header of the Document
        sections (List[Section]):
            An ordered list of sections defined in this Document
    """

    header_comment: List[CommentBlock] = []
    sections: List[Section] = []


class IniBasedModel(BaseModel, ABC):
    """IniBasedModel defines the base model for ini models

    IniBasedModel instances can be created from Section instances
    obtained through parsing ini documents. It further supports
    adding arbitrary fields to it, which will be written to file.
    Lastly, no arbitrary types are allowed for the defined fields.

    Attributes:
        comments (Optional[Comments]):
            Optional Comments if defined by the user.
    """

    class Config:
        extra = Extra.allow
        allow_population_by_field_name = True
        arbitrary_types_allowed = False

    class Comments(BaseModel, ABC):
        class Config:
            extra = Extra.allow
            allow_population_by_field_name = True
            arbitrary_types_allowed = False

    comments: Optional[Comments] = None

    @classmethod
    def validate(cls: Type["IniBasedModel"], value: Any) -> "IniBasedModel":
        if isinstance(value, Section):
            converted_content = cls._convert_section_content(value.content)
            underlying_dict = cls._convert_section_to_dict(value)
            value = {**underlying_dict, **converted_content}

        return super().validate(value)

    @classmethod
    def _convert_section_to_dict(cls, value: Section) -> Dict:
        return value.dict(
            exclude={
                "start_line",
                "end_line",
                "datablock",
                "content",
            }
        )

    @classmethod
    def _convert_section_content(cls, content: List):
        # TODO add comment here
        return dict((v.key, v.value) for v in content if isinstance(v, Property))


class DataBlockIniBasedModel(IniBasedModel):
    @classmethod
    def _convert_section_to_dict(cls, value: Section) -> Dict:
        return value.dict(
            exclude={
                "start_line",
                "end_line",
                "content",
            }
        )
