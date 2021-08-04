from functools import reduce
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union
from xmlrpc.client import Boolean

from pydantic import Field, validator

from hydrolib.core.basemodel import BaseModel
from hydrolib.core.utils import to_key


class CommentBlock(BaseModel):
    """CommentBlock defines a comment block within a deltares ini file.

    Attributes:
        lines (List[str]): The actual lines of the CommentBlock
    """

    lines: List[str]


class Property(BaseModel):
    """Property defines a deltares ini property

    Attributes:
        key (str): The key of this Property
        value (Optional[str]): The value associated with this Property
        comment (Optional[str]): The comment associated with this Property
    """

    key: str
    value: Optional[str]
    comment: Optional[str]

    def get_item(self):
        return {self.key: self.value}

    def get_comment(self):
        return {self.key: self.comment}


ContentElement = Union[Property, CommentBlock]
DatablockRow = Sequence[str]
Datablock = Sequence[DatablockRow]


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
        content (List[ContentElement]):
            The ordered list of Property and CommentBlock objects
        datablock (Optional[Datablock]):
            An optional data block associated with this Section. The datablock is
            structured as a sequence of rows, i.e. datablock[2][1] refers to the third
            row, second column.
    """

    header: str = Field(alias="_header")
    content: List[ContentElement]

    # these are primarily relevant for bc files
    datablock: Optional[Datablock]

    def dict(self, *args, **kwargs):
        kwargs["by_alias"] = True
        return super().dict(*args, **kwargs)

    def flatten(self, duplicate_key_as_list=True, with_comments=True) -> Dict:
        converted_content = self._convert_section_content(
            duplicate_key_as_list, with_comments
        )
        underlying_dict = self._convert_section_to_dict()
        return {**underlying_dict, **converted_content}

    def _convert_section_to_dict(self) -> Dict:
        return self.dict(
            exclude={
                "start_line",
                "end_line",
                "content",
            }
        )

    def _convert_section_content(
        self, duplicate_key_as_list: bool, with_comments: bool
    ) -> Dict:
        def group_and_flatten(l: Iterable[Tuple[str, Any]]) -> Dict[str, Any]:
            if duplicate_key_as_list:
                return reduce(_combine_in_dict, l, {})
            else:
                return dict(l)

        values = group_and_flatten(
            (to_key(v.key), v.value) for v in self.content if isinstance(v, Property)
        )

        if with_comments:
            values["comments"] = group_and_flatten(
                (to_key(v.key), v.comment)
                for v in self.content
                if isinstance(v, Property)
            )

        return values


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

    def flatten(self, duplicate_key_as_list=True, with_comments=True):
        data = {}
        for v in self.sections:
            key = to_key(v.header)
            value = v.flatten(duplicate_key_as_list, with_comments)
            if key in data and not isinstance(data[key], list):
                data[key] = [data[key], value]
            elif key in data:
                data[key].append(value)
            else:
                data[key] = value
        return data


def _combine_in_dict(
    dictionary: Dict[str, Any], key_value_pair: Tuple[str, Any]
) -> Dict[str, Any]:
    key, value = key_value_pair

    if key in dictionary:
        if not isinstance(dictionary[key], List):
            dictionary[key] = [
                dictionary[key],
            ]
        dictionary[key].append(value)
    else:
        dictionary[key] = value

    return dictionary
