import platform
from pathlib import Path

import pytest

from hydrolib.core.dflowfm.mdu.models import Geometry, Output
from hydrolib.core.utils import (
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
    @pytest.mark.skipif(
        not runs_on_windows(),
        reason="Platform dependent test: should only succeed on Windows OS.",
    )
    class TestOnWindows:
        class TestConvertToOSStyle:
            def test_from_absolute_unixlike_filepath(self):
                converter = FilePathStyleConverter()
                source_path = "/c/path/to.file"
                target_path = converter.convert_to_os_style(
                    Path(source_path), PathStyle.UNIXLIKE
                )
                assert target_path == "c:/path/to.file"

            def test_from_relative_unixlike_filepath(self):
                converter = FilePathStyleConverter()
                source_path = "path/to.file"
                target_path = converter.convert_to_os_style(
                    Path(source_path), PathStyle.UNIXLIKE
                )
                assert target_path == "path/to.file"

            @pytest.mark.parametrize(
                "source_path, exp_target_path",
                [
                    pytest.param(
                        "c:\\path\\to.file", "c:/path/to.file", id="Backward slashes"
                    ),
                    pytest.param(
                        "c:/path/to.file", "c:/path/to.file", id="Forward slashes"
                    ),
                ],
            )
            def test_from_absolute_windowslike_filepath(
                self, source_path: str, exp_target_path: str
            ):
                converter = FilePathStyleConverter()
                target_path = converter.convert_to_os_style(
                    Path(source_path), PathStyle.WINDOWSLIKE
                )
                assert target_path == exp_target_path

            @pytest.mark.parametrize(
                "source_path, exp_target_path",
                [
                    pytest.param(
                        "path\\to.file", "path/to.file", id="Backward slashes"
                    ),
                    pytest.param("path/to.file", "path/to.file", id="Forward slashes"),
                ],
            )
            def test_from_relative_windowslike_filepath(
                self, source_path: str, exp_target_path: str
            ):
                converter = FilePathStyleConverter()
                target_path = converter.convert_to_os_style(
                    Path(source_path), PathStyle.WINDOWSLIKE
                )
                assert target_path == exp_target_path

        class TestConvertFromOSStyle:
            @pytest.mark.parametrize(
                "source_path, exp_target_path",
                [
                    pytest.param(
                        "c:\\path\\to.file", "/c/path/to.file", id="Backward slashes"
                    ),
                    pytest.param(
                        "c:/path/to.file", "/c/path/to.file", id="Forward slashes"
                    ),
                ],
            )
            def test_to_absolute_unixlike_filepath(
                self, source_path: str, exp_target_path: str
            ):
                converter = FilePathStyleConverter()
                target_path = converter.convert_from_os_style(
                    Path(source_path), PathStyle.UNIXLIKE
                )
                assert target_path == exp_target_path

            @pytest.mark.parametrize(
                "source_path, exp_target_path",
                [
                    pytest.param(
                        "path\\to.file", "path/to.file", id="Backward slashes"
                    ),
                    pytest.param("path/to.file", "path/to.file", id="Forward slashes"),
                ],
            )
            def test_to_relative_unixlike_filepath(
                self, source_path: str, exp_target_path: str
            ):
                converter = FilePathStyleConverter()
                target_path = converter.convert_from_os_style(
                    Path(source_path), PathStyle.UNIXLIKE
                )
                assert target_path == exp_target_path

            @pytest.mark.parametrize(
                "source_path, exp_target_path",
                [
                    pytest.param(
                        "c:\\path\\to.file", "c:/path/to.file", id="Backward slashes"
                    ),
                    pytest.param(
                        "c:/path/to.file", "c:/path/to.file", id="Forward slashes"
                    ),
                ],
            )
            def test_to_absolute_windowslike_filepath(
                self, source_path: str, exp_target_path: str
            ):
                converter = FilePathStyleConverter()
                target_path = converter.convert_from_os_style(
                    Path(source_path), PathStyle.WINDOWSLIKE
                )
                assert target_path == exp_target_path

            @pytest.mark.parametrize(
                "source_path, exp_target_path",
                [
                    pytest.param(
                        "path\\to.file", "path/to.file", id="Backward slashes"
                    ),
                    pytest.param("path/to.file", "path/to.file", id="Forward slashes"),
                ],
            )
            def test_to_relative_windowslike_filepath(
                self, source_path: str, exp_target_path: str
            ):
                converter = FilePathStyleConverter()
                target_path = converter.convert_from_os_style(
                    Path(source_path), PathStyle.WINDOWSLIKE
                )
                assert target_path == exp_target_path

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
                        "c:\\path\\to.file", "/c/path/to.file", id="Backward slashes"
                    ),
                    pytest.param(
                        "c:/path/to.file", "/c/path/to.file", id="Forward slashes"
                    ),
                ],
            )
            def test_from_absolute_windowslike_filepath(
                self, source_path: str, exp_target_path: str
            ):
                converter = FilePathStyleConverter()
                target_path = converter.convert_to_os_style(
                    Path(source_path), PathStyle.WINDOWSLIKE
                )
                assert target_path == exp_target_path

            @pytest.mark.parametrize(
                "source_path, exp_target_path",
                [
                    pytest.param(
                        "path\\to.file", "path/to.file", id="Backward slashes"
                    ),
                    pytest.param("path/to.file", "path/to.file", id="Forward slashes"),
                ],
            )
            def test_from_relative_windowslike_filepath(
                self, source_path: str, exp_target_path: str
            ):
                converter = FilePathStyleConverter()
                target_path = converter.convert_to_os_style(
                    Path(source_path), PathStyle.WINDOWSLIKE
                )
                assert target_path == exp_target_path

            def test_from_absolute_unixlike_filepath(self):
                converter = FilePathStyleConverter()
                source_path = "/c/path/to.file"
                target_path = converter.convert_to_os_style(
                    Path(source_path), PathStyle.UNIXLIKE
                )
                assert target_path == "/c/path/to.file"

            def test_from_relative_unixlike_filepath(self):
                converter = FilePathStyleConverter()
                source_path = "path/to.file"
                target_path = converter.convert_to_os_style(
                    Path(source_path), PathStyle.UNIXLIKE
                )
                assert target_path == "path/to.file"

        class TestConvertFromOSStyle:
            def test_to_absolute_windowslike_filepath(self):
                converter = FilePathStyleConverter()
                source_path = "/c/path/to.file"
                target_path = converter.convert_from_os_style(
                    Path(source_path), PathStyle.WINDOWSLIKE
                )
                assert target_path == "c:/path/to.file"

            def test_to_relative_windowslike_filepath(self):
                converter = FilePathStyleConverter()
                source_path = "path/to.file"
                target_path = converter.convert_from_os_style(
                    Path(source_path), PathStyle.WINDOWSLIKE
                )
                assert target_path == "path/to.file"

            def test_to_absolute_unixlike_filepath(self):
                converter = FilePathStyleConverter()
                source_path = "/c/path/to.file"
                target_path = converter.convert_from_os_style(
                    Path(source_path), PathStyle.UNIXLIKE
                )
                assert target_path == "/c/path/to.file"

            def test_to_relative_unixlike_filepath(self):
                converter = FilePathStyleConverter()
                source_path = "path/to.file"
                target_path = converter.convert_from_os_style(
                    Path(source_path), PathStyle.UNIXLIKE
                )
                assert target_path == "path/to.file"
