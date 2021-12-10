from typing import Any, List, Optional

from pydantic import validator, Field
from semantic_version import Version as SemVer


def example(a: float, b: float = 1.0) -> float:
    """[summary]

    Args:
        a (float): [description]
        b (float): [description]

    Returns:
        float: [description]
    """
    return a * b


def to_key(string: str) -> str:
    return string.lower().replace(" ", "_").replace("-", "")


def to_list(item: Any) -> List[Any]:
    """Puts the specified item in a list if it is an instance of `dict`.

    Attributes:
        item: The item to put in a list.

    Returns:
        List: A list with the specified item.
    """

    if not isinstance(item, list):
        return [item]
    return item


def str_is_empty_or_none(str_field: str) -> bool:
    """
    Verifies whether a string is empty or None.

    Args:
        str_field (str): String to validate.

    Returns:
        bool: Evaluation result.
    """
    return str_field is None or not str_field or str_field.isspace()


def get_substring_between(source: str, start: str, end: str) -> Optional[str]:
    """Finds the substring between two other strings.

    Args:
        source (str): The source string.
        start (str): The starting string from where to create the substring.
        end (str): The end string to where to create the substring.

    Returns:
        str: The substring if found; otherwise, `None`.
    """

    index_start = source.find(start)
    if index_start == -1:
        return None

    index_start += len(start)

    index_end = source.find(end, index_start)
    if index_end == -1:
        return None

    return source[index_start:index_end]


class HVersion(SemVer):
    @classmethod
    def coerce(cls, *args, **kwargs):
        version = super().coerce(*args, **kwargs)
        return cls(**version.__dict__)


class FMVersion(HVersion):
    def __str__(self) -> str:
        """Add zero to minor version if it is less than 10."""
        version = f"{self.major}"
        if self.minor is not None:
            version = f"{version}.{self.minor:02d}"

        return version


class DIMRVersion(HVersion):
    def __str__(self) -> str:
        """Strip patch version."""
        version = f"{self.major}"
        if self.minor is not None:
            version = f"{version}.{self.minor}"

        return version


def get_version_validator(*field_name: str):
    """Get a validator to check the Version number."""

    def check_version(cls, v: Any, field: Field):
        """Validate (semantic) version numbers."""

        if isinstance(v, str):
            version = field.default.__class__.coerce(v)
        elif isinstance(v, (FMVersion, DIMRVersion)):
            version = v
        elif v is None:
            return field.default
        else:
            raise ValueError(f"Invalid version specified: {v}")

        if version < field.default or version >= field.default.next_major():
            raise ValueError(
                f"Input with version {v} isn't a version support by HYDROLIB-core, which supports >={field.default}"
            )

        return version

    return validator(*field_name, allow_reuse=True, pre=True)(check_version)
