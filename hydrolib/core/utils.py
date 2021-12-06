from typing import Any, List
from warnings import warn


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


def get_list_index_safely(list: list, item, start: int, end: int) -> int:
    """Gets the index of `item` in `list` safely.

    Args:
        list (list): The list in which to search.
        item ([type]): he item to search.
        start (int): The included index to start searching.
        end (int): The included index to end searching.

    Returns:
        int: The index of `item` if found; otherwise, -1.
    """

    try:
        return list.index(item, start, end + 1)

    except ValueError:
        warn(f"Could not find {item} between indices {start} and {end}.")
        return -1
