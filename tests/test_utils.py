from pathlib import Path

from hydrolib.core.io.mdu.models import Output


class TestSplitString:
    def test_split_string_strip_whitespace(self):
        string_with_multiple_floats = "1.0     5.0"
        output = Output(statsinterval=string_with_multiple_floats)

        assert output.statsinterval == [1.0, 5.0]

    def test_split_string_strip_semicolon(self):
        string_with_multiple_files = "file1 ; file2"
        output = Output(obsfile=string_with_multiple_files)

        assert output.obsfile == [Path("file1"), Path("file2")]
