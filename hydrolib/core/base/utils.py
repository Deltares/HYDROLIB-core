import platform
import re
from enum import Enum, auto
from hashlib import md5
from operator import eq, ge, gt, le, lt, ne
from pathlib import Path
from typing import Any, Callable, List, Optional

from strenum import StrEnum


def to_key(string: str) -> str:
    """
    Construct a key name from a given field name.
    The given field name may be a Pydantic Field alias, and the key name
    is intended to be used as a BaseModel class member variable name.

    Args:
        string (str): input field name

    """
    # First replace any leading digits, because those are undesirable
    # in variable names.
    digitdict = {
        "0": "zero",
        "1": "one",
        "2": "two",
        "3": "three",
        "4": "four",
        "5": "five",
        "6": "six",
        "7": "seven",
        "8": "eight",
        "9": "nine",
    }
    m = re.search(r"^\d+", string)
    if m:
        digitstring = string[0 : m.end()]  # noqa: E203
        for key, val in digitdict.items():
            digitstring = digitstring.replace(key, val)
        string = digitstring + string[m.end() :]  # noqa: E203

    # Next, replace spaces and hyphens in the potential variable name.
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


def get_str_len(str_field: Optional[str]) -> int:
    """
    Get string length or 0 if input is None.

    Args:
        str_field (str): String to measure.

    Returns:
        int: Length of passed input.
    """
    return len(str_field) if str_field else 0


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

    index_end = source.rfind(end, index_start)
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


class OperatingSystem(Enum):
    """Enum represting an operating system."""

    WINDOWS = auto()
    """The Windows operating system."""
    LINUX = auto()
    """The Linux operating system."""
    MACOS = auto()
    """The MacOS operating system."""


def get_operating_system() -> OperatingSystem:
    """Gets the currently running operating system.

    Raises:
        NotImplementedError: When the current operating system is anything other than Windows, Linux or MacOS.

    Returns:
        OperatingSystem: The operating system.
    """
    operating_system = platform.system()

    if operating_system == "Windows":
        return OperatingSystem.WINDOWS
    if operating_system == "Linux":
        return OperatingSystem.LINUX
    if operating_system == "Darwin":
        return OperatingSystem.MACOS

    raise NotImplementedError(f"Operating system {operating_system} is not supported.")


class PathStyle(StrEnum):
    """Path style format."""

    UNIXLIKE = "unix"
    """Unix-like path style."""
    WINDOWSLIKE = "windows"
    """Windows-like path style."""


def get_path_style_for_current_operating_system() -> PathStyle:
    """Gets the file path style for the currently running operating system.

    Returns:
        OperatingSystem: The OS path style.
    """
    operating_system = get_operating_system()

    if operating_system == OperatingSystem.WINDOWS:
        return PathStyle.WINDOWSLIKE
    else:
        return PathStyle.UNIXLIKE


class FilePathStyleConverter:
    """Class for converting file paths between different path styles."""

    def __init__(self):
        """Initialize the converter with the current operating system's path style."""
        self._os_path_style = get_path_style_for_current_operating_system()

    def convert_to_os_style(self, file_path: Path, source_path_style: PathStyle) -> str:
        """Convert the file path from the source path style to the path style of the current operating system.

        Args:
            file_path (Path):
                The file path to convert to the OS path style.
            source_path_style (PathStyle):
                The file path style of the given file path.

        Returns:
            str: The converted file path with OS path style.

        Raises:
            NotImplementedError: When this function is called with a PathStyle other than WINDOWSLIKE or UNIXLIKE.
        """

        return FilePathStyleConverter._convert(
            file_path, source_path_style, self._os_path_style
        )

    def convert_from_os_style(
        self, file_path: Path, target_path_style: PathStyle
    ) -> str:
        """Convert the file path from the path style of the current operating system to the target path style.

        Args:
            file_path (Path): The file path to convert to the target path style.
            target_path_style (PathStyle): The target path style to convert the file path to.

        Returns:
            str: The converted file path with the target path style.

        Raises:
            NotImplementedError: When this function is called with a PathStyle other than WINDOWSLIKE or UNIXLIKE.
        """

        return FilePathStyleConverter._convert(
            file_path, self._os_path_style, target_path_style
        )

    @classmethod
    def _convert(
        cls, file_path: Path, source_path_style: PathStyle, target_path_style: PathStyle
    ) -> str:
        if source_path_style == target_path_style:
            return file_path.as_posix()

        if (
            source_path_style == PathStyle.UNIXLIKE
            and target_path_style == PathStyle.WINDOWSLIKE
        ):
            return FilePathStyleConverter._from_posix_to_windows_path(file_path)
        elif (
            source_path_style == PathStyle.WINDOWSLIKE
            and target_path_style == PathStyle.UNIXLIKE
        ):
            return FilePathStyleConverter._from_windows_to_posix_path(file_path)
        else:
            raise NotImplementedError(
                f"Cannot convert {source_path_style} to {target_path_style}"
            )

    @classmethod
    def _from_posix_to_windows_path(cls, posix_path: Path) -> str:
        is_relative = not posix_path.as_posix().startswith("/")

        if is_relative:
            return posix_path.as_posix()

        root = posix_path.parts[1]
        windows_root = root + ":/"
        parts = posix_path.parts[2:]

        windows_path = windows_root + "/".join(parts)

        return windows_path

    @classmethod
    def _from_windows_to_posix_path(cls, windows_path: Path) -> str:
        windows_path_str = str(windows_path).replace("\\", "/")
        windows_path = Path(windows_path_str)

        root = windows_path.parts[0]
        is_relative = ":" not in root

        if is_relative:
            return windows_path_str

        posix_root = "/" + root.split(":")[0] + "/"
        parts = windows_path.parts[1:]

        posix_path = posix_root + "/".join(parts)

        return posix_path


class FileChecksumCalculator:
    """
    FileChecksumCalculator calculator used to calculate the checksum of a file.
    """

    @staticmethod
    def calculate_checksum(filepath: Path) -> Optional[str]:
        """Calculate the checksum of the file from the given filepath.

        Args:
            filepath (Path): The filepath to the file for which the checksum will be calculated.

        Returns:
            [Optional[str]]:
                The checksum of the file.
                When the filepath doesn't exist or the filepath isn't a file, None.
        """
        if not filepath.exists() or not filepath.is_file():
            return None

        return FileChecksumCalculator._calculate_md5_checksum(filepath)

    @staticmethod
    def _calculate_md5_checksum(filepath: Path) -> str:
        """Calculate the MD5 checksum of a file.

        This method uses the `hashlib.md5` function with the `usedforsecurity=False` parameter
        to indicate that the MD5 hash is not being used for security purposes. MD5 is considered
        cryptographically insecure and should not be used in security-sensitive contexts.

        Note:
            The `usedforsecurity` parameter was introduced in Python 3.9. This method requires
            Python 3.9 or later to function correctly.

        Args:
            filepath (Path): The path to the file for which the checksum will be calculated.

        Returns:
            str: The MD5 checksum of the file.
        """
        md5_hash = md5(usedforsecurity=False)
        with open(filepath, "rb") as file:
            for chunk in iter(lambda: file.read(4096), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()


class FortranUtils:
    """Utility class for Fortran specific conventions."""

    _scientific_exp_d_notation_regex = re.compile(
        r"([\d.]+)([dD])([+-]?\d{1,3})"
    )  # matches a float: 1d9, 1D-3, 1.D+4, etc.

    @staticmethod
    def replace_fortran_scientific_notation(value):
        """Replace Fortran scientific notation ("D" in exponent) with standard
        scientific notation ("e" in exponent).
        """
        if isinstance(value, str):
            return FortranUtils._scientific_exp_d_notation_regex.sub(r"\1e\3", value)
        elif isinstance(value, list):
            return list(map(FortranUtils.replace_fortran_scientific_notation, value))

        return value
