from typing import Type, Union, get_args, get_origin
from pydantic import FilePath


def example(a: float, b: float = 1.0) -> float:
    """[summary]

    Args:
        a (float): [description]
        b (float): [description]

    Returns:
        float: [description]
    """
    return a * b


def get_model_type_from_union(type: Type):
    """
    `Union[None, FilePath, Model]` becomes `Model`
    """
    if get_origin(type) is Union:
        for type_ in get_args(type):
            if type_ is not None.__class__ and type_ is not FilePath:
                return type_
    else:
        return None
