import platform
from pathlib import Path

import pytest

from hydrolib.core.dflowfm.mdu.models import Geometry, Output
from hydrolib.core.utils import (
    FileChecksumCalculator,
    FilePathStyleConverter,
    PathStyle,
    get_substring_between,
    str_is_empty_or_none,
)

from .utils import test_input_dir


def runs_on_windows() -> bool:
    """Check to see if we are running on Windows."""
    return platform.system() == "Windows"


class TestSplitString:
    def test_split_string_strip_whitespace(self):
        string_with_multiple_floats = "1.0     5.0"
        output = Output(statsinterval=string_with_multiple_floats)

        assert output.statsinterval == [1.0, 5.0]

    def test_split_string_strip_semicolon(self):
        e02 = test_input_dir / "e02"

        file1 = (
            e02 / "c11_korte-woerden-1d" / "dimr_model" / "dflowfm" / "structures.ini"
        )

        file2 = (
            e02
            / "f152_1d2d_projectmodels_rhu"
            / "c04_DHydamo-MGB-initialisation"
            / "fm"
            / "structure.ini"
        )

        string_with_multiple_files = f"{file1} ; {file2}"
        output = Geometry(structurefile=string_with_multiple_files)

        assert output.structurefile[0].filepath == Path(file1)
        assert output.structurefile[1].filepath == Path(file2)


class TestStrIsEmptyOrNone:
    @pytest.mark.parametrize(
        "input_str",
        [
            pytest.param("", id="No spaces"),
            pytest.param(" ", id="Spaces"),
            pytest.param(None, id="None"),
            pytest.param("\t", id="Tabulator"),
        ],
    )
    def test_given_args_expected_result(self, input_str: str):
        assert str_is_empty_or_none(input_str)

    def test_given_valid_args_returns_true(self):
        assert str_is_empty_or_none("aValue") is False


class TestGetSubstringBetween:
    @pytest.mark.parametrize(
        "start, end, exp_result",
        [
            pytest.param("", "brown", "The quick "),
            pytest.param("brown", "lazy", " fox jumps over the "),
            pytest.param("lazy", "brown", None),
            pytest.param("brown", "cat", None),
        ],
    )
    def test_get_substring_between_expected_result(
        self, start: str, end: str, exp_result: str
    ):
        source = "The quick brown fox jumps over the lazy dog"
        result = get_substring_between(source, start, end)

        assert result == exp_result


class TestFilePathStyleConverter:
    @classmethod
    def run_and_assert_os_path_style_converter(
        cls, direction: str, input_path: str, path_style: PathStyle, expected_path: str
    ):
        """Create a PathStyleConverter and converts an input path to a
        given PathStyle convention, checking the expected path.

        Args:
            direction (str): direction of the conversion, can be either
                'from_os' or 'to_os'.
            input_path (str): path to convert.
            path_style (PathStyle): the style that must be assumed for the
                input string (when direction='to_os') or the output string
                (when direction='from_os).
            expected_path (str): expected result string for the converted path.

        Raises:
            AssertionError: if the assertion input_path == expected_path fails.
            ValueError: if a wrong value for direction was given.
        """
        converter = FilePathStyleConverter()
        if direction == "from_os":
            result_path = converter.convert_from_os_style(Path(input_path), path_style)
        elif direction == "to_os":
            result_path = converter.convert_to_os_style(Path(input_path), path_style)
        else:
            raise ValueError(
                "Wrong value for direction. Possible values: from_os, to_os."
            )

        assert result_path == expected_path

    @pytest.mark.skipif(
        not runs_on_windows(),
        reason="Platform dependent test: should only succeed on Windows OS.",
    )
    class TestOnWindows:
        class TestConvertToOSStyle:
            @pytest.mark.parametrize(
                "source_path, exp_target_path",
                [
                    pytest.param(
                        "/c/path/to.file",
                        "c:/path/to.file",
                        id="Absolute path, forward slashes",
                    ),
                    pytest.param(
                        "path/to.file",
                        "path/to.file",
                        id="Relative path, forward slashes",
                    ),
                ],
            )
            def test_from_unixlike_filepath(
                self, source_path: str, exp_target_path: str
            ):
                TestFilePathStyleConverter.run_and_assert_os_path_style_converter(
                    "to_os", source_path, PathStyle.UNIXLIKE, exp_target_path
                )

            @pytest.mark.parametrize(
                "source_path, exp_target_path",
                [
                    pytest.param(
                        "c:\\path\\to.file",
                        "c:/path/to.file",
                        id="Absolute path, backward slashes",
                    ),
                    pytest.param(
                        "c:/path/to.file",
                        "c:/path/to.file",
                        id="Absolute path, forward slashes",
                    ),
                    pytest.param(
                        "path\\to.file",
                        "path/to.file",
                        id="Relative path, backward slashes",
                    ),
                    pytest.param(
                        "path/to.file",
                        "path/to.file",
                        id="Relative path, forward slashes",
                    ),
                ],
            )
            def test_from_windowslike_filepath(
                self, source_path: str, exp_target_path: str
            ):
                TestFilePathStyleConverter.run_and_assert_os_path_style_converter(
                    "to_os", source_path, PathStyle.WINDOWSLIKE, exp_target_path
                )

        class TestConvertFromOSStyle:
            @pytest.mark.parametrize(
                "source_path, exp_target_path",
                [
                    pytest.param(
                        "c:\\path\\to.file",
                        "/c/path/to.file",
                        id="Absolute path, backward slashes",
                    ),
                    pytest.param(
                        "c:/path/to.file",
                        "/c/path/to.file",
                        id="Absolute path, forward slashes",
                    ),
                    pytest.param(
                        "path\\to.file",
                        "path/to.file",
                        id="Relative path, backward slashes",
                    ),
                    pytest.param(
                        "path/to.file",
                        "path/to.file",
                        id="Relative path, forward slashes",
                    ),
                ],
            )
            def test_to_unixlike_filepath(self, source_path: str, exp_target_path: str):
                TestFilePathStyleConverter.run_and_assert_os_path_style_converter(
                    "from_os", source_path, PathStyle.UNIXLIKE, exp_target_path
                )

            @pytest.mark.parametrize(
                "source_path, exp_target_path",
                [
                    pytest.param(
                        "c:\\path\\to.file",
                        "c:/path/to.file",
                        id="Absolute path, backward slashes",
                    ),
                    pytest.param(
                        "c:/path/to.file",
                        "c:/path/to.file",
                        id="Absolute path, forward slashes",
                    ),
                    pytest.param(
                        "path\\to.file",
                        "path/to.file",
                        id="Relative path, backward slashes",
                    ),
                    pytest.param(
                        "path/to.file",
                        "path/to.file",
                        id="Relative path, forward slashes",
                    ),
                ],
            )
            def test_to_windowslike_filepath(
                self, source_path: str, exp_target_path: str
            ):
                TestFilePathStyleConverter.run_and_assert_os_path_style_converter(
                    "from_os", source_path, PathStyle.WINDOWSLIKE, exp_target_path
                )

    @pytest.mark.skipif(
        runs_on_windows(),
        reason="Platform dependent tests: should only succeed on non-Windows OS.",
    )
    class TestNotOnWindows:
        class TestConvertToOSStyle:
            @pytest.mark.parametrize(
                "source_path, exp_target_path",
                [
                    pytest.param(
                        "c:\\path\\to.file",
                        "/c/path/to.file",
                        id="Absolute path, backward slashes",
                    ),
                    pytest.param(
                        "c:/path/to.file",
                        "/c/path/to.file",
                        id="Absolute path, forward slashes",
                    ),
                    pytest.param(
                        "path\\to.file",
                        "path/to.file",
                        id="Relative path, backward slashes",
                    ),
                    pytest.param(
                        "path/to.file",
                        "path/to.file",
                        id="Relative path, forward slashes",
                    ),
                ],
            )
            def test_from_windowslike_filepath(
                self, source_path: str, exp_target_path: str
            ):
                TestFilePathStyleConverter.run_and_assert_os_path_style_converter(
                    "to_os", source_path, PathStyle.WINDOWSLIKE, exp_target_path
                )

            @pytest.mark.parametrize(
                "source_path, exp_target_path",
                [
                    pytest.param(
                        "/c/path/to.file",
                        "/c/path/to.file",
                        id="Absolute path, forward slashes",
                    ),
                    pytest.param(
                        "path/to.file",
                        "path/to.file",
                        id="Relative path, forward slashes",
                    ),
                ],
            )
            def test_from_unixlike_filepath(
                self, source_path: str, exp_target_path: str
            ):
                TestFilePathStyleConverter.run_and_assert_os_path_style_converter(
                    "to_os", source_path, PathStyle.UNIXLIKE, exp_target_path
                )

        class TestConvertFromOSStyle:
            @pytest.mark.parametrize(
                "source_path, exp_target_path",
                [
                    pytest.param(
                        "/c/path/to.file",
                        "c:/path/to.file",
                        id="Absolute path, forward slashes",
                    ),
                    pytest.param(
                        "path/to.file",
                        "path/to.file",
                        id="Relative path, forward slashes",
                    ),
                ],
            )
            def test_to_windowslike_filepath(
                self, source_path: str, exp_target_path: str
            ):
                TestFilePathStyleConverter.run_and_assert_os_path_style_converter(
                    "from_os", source_path, PathStyle.WINDOWSLIKE, exp_target_path
                )

            @pytest.mark.parametrize(
                "source_path, exp_target_path",
                [
                    pytest.param(
                        "/c/path/to.file",
                        "/c/path/to.file",
                        id="Absolute path, forward slashes",
                    ),
                    pytest.param(
                        "path/to.file",
                        "path/to.file",
                        id="Relative path, forward slashes",
                    ),
                ],
            )
            def test_to_unixlike_filepath(self, source_path: str, exp_target_path: str):
                TestFilePathStyleConverter.run_and_assert_os_path_style_converter(
                    "from_os", source_path, PathStyle.UNIXLIKE, exp_target_path
                )


class TestFileChecksumCalculator:
    def test_calculating_checksum_of_default_file_gives_expected_checksum(
        self, tmp_path: Path
    ):
        default_file = tmp_path / "default_file.txt"
        default_file.write_text("Hello World")
        expected_checksum = (
            "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"
        )

        calculated_checksum = FileChecksumCalculator.calculate_checksum(default_file)
        assert calculated_checksum == expected_checksum

    def test_calculating_checksum_of_non_existing_file_gives_none(self, tmp_path: Path):
        non_existing_file = tmp_path / "non_existing_file.txt"

        calculated_checksum = FileChecksumCalculator.calculate_checksum(
            non_existing_file
        )
        assert calculated_checksum is None

    def test_calculating_checksum_of_folder_gives_none(self, tmp_path: Path):
        calculated_checksum = FileChecksumCalculator.calculate_checksum(tmp_path)
        assert calculated_checksum is None
