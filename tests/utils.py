import difflib
import filecmp
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Generator, Generic, List, Optional, TypeVar

from pydantic.v1.generics import GenericModel

from hydrolib.core.basemodel import PathOrStr

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

    with file.open(encoding="utf8") as af:
        actual_lines = af.readlines()

    with reference_file.open(encoding="utf8") as rf:
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


def assert_objects_equal(
    obj_cmp: object, obj_ref: object, exclude_fields: List[str] = []
):
    """Assert that two objects are equal with possibility to exclude
    certain object fields.

    If the input values are lists they will be checked element-wise for
    equality.
    If the input values are no objects, nor lists, this will fall back
    to the standard equality operator.

    Args:
        obj_cmp (object): Object to be compared with reference object.
        obj_ref (object): Reference object to compare with.
        exclude_fields (List[str], optional): Optional list of key names
            that should be excluded from the comparison of object fields.
    Raises:
        AssertionError: if objects are of different type, different list
            lengths, or if objects have different field values.
    """
    assert type(obj_cmp) == type(obj_ref)

    if isinstance(obj_cmp, list):
        # Input is a list
        assert len(obj_cmp) == len(obj_ref)

        for a, b in zip(obj_cmp, obj_ref):
            assert_objects_equal(a, b, exclude_fields)

    elif isinstance(obj_cmp, object) and hasattr(obj_cmp, "__dict__"):
        # Input is an object
        check_keys = [
            key for key in obj_cmp.__dict__.keys() if key not in exclude_fields
        ]
        assert all(
            [getattr(obj_cmp, key) == getattr(obj_ref, key) for key in check_keys]
        )
    else:
        # Input is more basic/something else
        assert obj_cmp == obj_ref


def error_occurs_only_once(error_message: str, full_error: str) -> bool:
    """Check if the given error message occurs exactly once in the full error string.

    Args:
        error_message (str): The error to check for.
        full_error (str): The full error as a string.

    Returns:
        bool: Return True if the error message occurs exactly once in the full error.
            Returns False otherwise.
    """
    if error_message is None or full_error is None:
        return False

    return full_error.count(error_message) == 1


@contextmanager
def create_temp_file(content: str, filename: str) -> Generator[Path, None, None]:
    """Create a file in a temporary directory with the specified file name and the provided content.

    Args:
        content (str): The content of the file as string.
        filename (str): The file name.

    Example:
        >>>     with create_temp_file("some_file_content", "some_file_name") as temp_file:
        >>>         print(f"Do something with {temp_file}")

    Yields:
        Generator[Path, None, None]: Generator with the path to the file in the temporary directory as yield type.
    """
    with get_temp_file(filename) as file:
        with open(file, "w", encoding="utf8") as f:
            f.write(content)
        yield file


@contextmanager
def create_temp_file_from_lines(
    lines: List[str], filename: str
) -> Generator[Path, None, None]:
    """Create a file in a temporary directory with the specified file name and the provided content.

    Args:
        content (str): The content of the file as list of string (lines of the file).
        filename (str): The file name.

    Example:
        >>>     with create_temp_file_from_lines(["some_file_content"], "some_file_name") as temp_file:
        >>>         print(f"Do something with {temp_file}")

    Yields:
        Generator[Path, None, None]: Generator with the path to the file in the temporary directory as yield type.
    """
    content = "\n".join(lines)
    with create_temp_file(content, filename) as file:
        yield file


@contextmanager
def get_temp_file(filename: str) -> Generator[Path, None, None]:
    """Gets a path to a file in a temporary directory with the specified file name.

    Args:
        filename (str): The file name.

    Example:
        >>>     with get_temp_file("some_file_name") as temp_file:
        >>>         print(f"Do something with {temp_file}")

    Yields:
        Generator[Path, None, None]: Generator with the path to the file in the temporary directory as yield type.
    """
    with TemporaryDirectory() as temp_dir:
        yield Path(temp_dir, filename)


def compare_two_files(path1: PathOrStr, path2: PathOrStr) -> List[str]:
    """Compare two files and return the differences.

    Args:
        path1 (PathOrStr): The path to the first file.
        path2 (PathOrStr): The path to the second file.

    Returns:
        List[str]: The differences between the two files.

    Examples:
        ```python
        >>> compare_two_files("file1.txt", "file2.txt") # doctest +SKIP
        ```
    Notes:
        - The function ignores the trailing blank lines.
    """
    if isinstance(path1, str):
        path1 = Path(path1)
    if isinstance(path2, str):
        path2 = Path(path2)

    if not path1.exists():
        raise FileNotFoundError(f"File {path1} does not exist.")
    if not path2.exists():
        raise FileNotFoundError(f"File {path2} does not exist.")

    file1_lines = path1.read_text(encoding="utf-8").replace("\r\n", "\n").splitlines()
    file2_lines = path2.read_text(encoding="utf-8").replace("\r\n", "\n").splitlines()

    # Remove trailing blank lines (if any)
    while file1_lines and not file1_lines[-1].strip():
        file1_lines.pop()
    while file2_lines and not file2_lines[-1].strip():
        file2_lines.pop()

    diff = difflib.unified_diff(
        file1_lines, file2_lines, lineterm="", fromfile=str(path1), tofile=str(path2)
    )
    return list(diff)
