from pathlib import Path
from typing import Generic, TypeVar

import pytest
from numpy import array
from pydantic.generics import GenericModel

TWrapper = TypeVar("TWrapper")


class WrapperTest(GenericModel, Generic[TWrapper]):
    val: TWrapper


test_data_dir = Path(__file__).parent / "data"
invalid_test_data_dir = test_data_dir / "input/invalid_files"
test_input_dir = test_data_dir / "input"
test_output_dir = test_data_dir / "output"
test_reference_dir = test_data_dir / "reference"


def assert_files_equal(file: str, reference_file: str, skip_lines: list = []):
    """Asserts that two files are equal based on content.

    Args:
        file (str): The path to the input file.
        reference_file (str): The path to the reference file.
        skip_lines (list): Optional parameter; the line indices to skip for comparison. Default is an empty list.
    """

    with file.open() as af:
        actual_lines = af.readlines()

    with reference_file.open() as rf:
        reference_lines = rf.readlines()

    assert len(actual_lines) == len(
        reference_lines
    ), f"<{len(actual_lines)}> not equal to <{len(reference_lines)}>"

    for i in range(len(reference_lines)):
        if i in skip_lines:
            continue

        actual = actual_lines[i]
        reference = reference_lines[i]
        assert actual == reference, f"<{actual}> not equal to <{reference}>"
