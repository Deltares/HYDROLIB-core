from pathlib import Path
from typing import Generic, TypeVar

from pydantic.generics import GenericModel

TWrapper = TypeVar("TWrapper")


class WrapperTest(GenericModel, Generic[TWrapper]):
    val: TWrapper


test_data_dir = Path(__file__).parent / "data"
test_output_dir = test_data_dir / "output"
