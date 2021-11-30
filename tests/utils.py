from pathlib import Path
from typing import Generic, TypeVar

import pytest
from pydantic.generics import GenericModel

TWrapper = TypeVar("TWrapper")


class WrapperTest(GenericModel, Generic[TWrapper]):
    val: TWrapper


test_data_dir = Path(__file__).parent / "data"
test_input_dir = test_data_dir / "input"
test_output_dir = test_data_dir / "output"
test_reference_dir = test_data_dir / "reference"


def assert_files_equal(file: str, reference_file: str):
    """Asserts that two files are equal based on content.

    Args:
        file (str): The path to the input file.
        reference_file (str): The path to the reference file.
    """

    with file.open() as af:
        actual_lines = af.readlines()

    with reference_file.open() as rf:
        reference_lines = rf.readlines()

    assert len(actual_lines) == len(reference_lines)

    for i in range(len(reference_lines)):
        assert actual_lines[i] == reference_lines[i]
