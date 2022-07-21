import filecmp
from pathlib import Path
from typing import Generic, Optional, TypeVar

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


def assert_files_equal(file: Path, reference_file: Path, skip_lines: list = []) -> None:
    """Assert that two files are equal based on content.

    Args:
        file (Path): The path to the input file.
        reference_file (Path): The path to the reference file.
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


def assert_file_is_same_binary(
    input_directory: Path,
    input_filepath: Optional[Path],
    reference_directory: Path,
    reference_filepath: Path = ...,
) -> None:
    """Assert that input_directory / input_filepath is equal to
    reference_directory / reference_filepath

    If input_filepath is None, nothing will be compared.

    If no reference_filepath is specified it will be set to input_filepath.

    If the reference_directory / reference_filepath does not exist, we assert
    that input_directory / input_filepath does not exist.

    Args:
        input_directory (Path):
            The directory containing the input file.
        input_filepath (Optional[Path]):
            The input filename relative to input_directory
        reference_directory (Path):
            The directory containing the reference file.
        reference_filepath (Path, optional):
            The reference filename relative to reference_directory
            Defaults to ... which is then set to input_filepath.
    """
    if input_filepath is None:
        return
    if reference_filepath is ...:
        reference_filepath = input_filepath

    reference_path = reference_directory / reference_filepath

    input_path = input_directory / input_filepath

    if reference_path.exists():
        assert input_path.exists()
        assert filecmp.cmp(input_path, reference_path)
    else:
        assert not input_path.exists()
