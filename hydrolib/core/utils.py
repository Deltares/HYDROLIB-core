from typing import Any, List


def example(a: float, b: float = 1.0) -> float:
    """[summary]

    Args:
        a (float): [description]
        b (float): [description]

    Returns:
        float: [description]
    """
    return a * b


def to_lowercase(string: str) -> str:
    """Coverts the specified string to a lowercase string.

    Attributes:
        string: The string to be lowered.

    Returns:
        str: The lowered string.
    """
    return string.lower()


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
