from typing import List


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
    return string.lower()


def to_list(item) -> List:
    """Puts the specified item in a list if it is an instance of `dict`.

    Attributes:
        item: The item to put in a list.

    Returns:
        List: If the item is a dictionary, a list with the specified item; otherwise, the item.
    """

    if isinstance(item, dict):
        return [item]
    return item
