from typing import Any, List, Optional

from hydrolib.core.basemodel import BaseModel


class IniProperty(BaseModel):
    """Property from an INI file.

    Attributes:
        key: The key of the property
        value: The value of the propery
        comment: The comment of the property
    """

    key: str
    value: Optional[Any]
    comment: Optional[str]


class IniSection(BaseModel):
    """Section from an INI file.

    Attributes:
        properties: List of [`IniProperty`][hydrolib.core.io.ini.models.IniProperty] that are contained by this section.
    """

    properties: List[IniProperty]
