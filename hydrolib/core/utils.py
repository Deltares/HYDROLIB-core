from operator import eq, ge, gt, le, lt, ne
from typing import Any, Callable, List, Optional


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


def operator_str(operator_func: Callable) -> str:
    """
    Make string representation of some of operator's built-in operator
    functions, for use in prettyprinting.

    Args:
        operator_func (Callable): Typically one of operator's built-in
            operator functions. When unsupported, the standard __str__
            representation is returned.
    """
    if operator_func == eq:
        return "is"
    elif operator_func == ne:
        return "is not"
    elif operator_func == lt:
        return "is less than"
    elif operator_func == le:
        return "is less than or equal to"
    elif operator_func == gt:
        return "is greater than"
    elif operator_func == ge:
        return "is greater than or equal to"
    else:
        return str(operator_func)
