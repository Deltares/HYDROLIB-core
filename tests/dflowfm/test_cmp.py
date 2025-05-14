import re
from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from hydrolib.core.basemodel import ModelSaveSettings
from hydrolib.core.dflowfm.cmp.models import AstronomicRecord, CMPModel, HarmonicRecord
from hydrolib.core.dflowfm.cmp.parser import CMPParser
from hydrolib.core.dflowfm.cmp.serializer import CMPSerializer

# Cmp file content and expected data
cmp_test_parameters = [
    pytest.param(
        {
            "comments": [],
            "component": {},
        },
        "",
        id="empty",
    ),
    pytest.param(
        {
            "comments": ["test content"],
            "component": {
                "harmonics": [{"period": "0.0", "amplitude": "1.0", "phase": "2.0"}],
            },
        },
        "#test content\n0.0   1.0  2.0",
        id="single harmonics",
    ),
    pytest.param(
        {
            "comments": ["test content"],
            "component": {
                "astronomics": [{"name": "M12", "amplitude": "1.0", "phase": "2.0"}],
            },
        },
        "#test content\nM12   1.0  2.0",
        id="single astronomics",
    ),
    pytest.param(
        {
            "comments": ["test content"],
            "component": {
                "harmonics": [
                    {"period": "0.0", "amplitude": "1.0", "phase": "2.0"},
                    {"period": "1.0", "amplitude": "3.0", "phase": "4.0"},
                ],
            },
        },
        "#test content\n0.0   1.0  2.0\n1.0   3.0  4.0",
        id="multiple harmonics",
    ),
    pytest.param(
        {
            "comments": ["test content"],
            "component": {
                "astronomics": [
                    {"name": "M12", "amplitude": "1.0", "phase": "2.0"},
                    {"name": "4MSN12", "amplitude": "3.0", "phase": "4.0"},
                ],
            },
        },
        "#test content\nM12   1.0  2.0\n4MSN12   3.0  4.0",
        id="multiple astronomics",
    ),
    pytest.param(
        {
            "comments": ["test content", "second test content"],
            "component": {
                "harmonics": [
                    {"period": "0.0", "amplitude": "1.0", "phase": "2.0"},
                ],
            },
        },
        "#test content\n#second test content\n0.0   1.0  2.0",
        id="multiple comments",
    ),
    pytest.param(
        {
            "comments": ["test content"],
            "component": {
                "harmonics": [
                    {"period": "0.0", "amplitude": "1.0", "phase": "2.0"},
                ],
                "astronomics": [
                    {"name": "2(MS)N10", "amplitude": "3.0", "phase": "4.0"},
                ],
            },
        },
        "#test content\n0.0   1.0  2.0\n2(MS)N10   3.0  4.0",
        id="mixed components",
    ),
    pytest.param(
        {
            "comments": ["test content", "", "second test content"],
            "component": {
                "harmonics": [
                    {"period": "0.0", "amplitude": "1.0", "phase": "2.0"},
                    {"period": "1.0", "amplitude": "3.0", "phase": "4.0"},
                ],
                "astronomics": [
                    {"name": "M12", "amplitude": "1.0", "phase": "2.0"},
                    {"name": "4MSN12", "amplitude": "3.0", "phase": "4.0"},
                ],
            },
        },
        "#test content\n\n#second test content\n0.0   1.0  2.0\n1.0   3.0  4.0\n\nM12   1.0  2.0\n4MSN12   3.0  4.0",
        id="multiple with empty line",
    ),
]


class TestCMPModel:
    def test_cmp_model_initialization(self):
        model = CMPModel()
        assert len(model.comments) == 0
        assert len(model.component) == 0

    def test_astronomic_record_initialization(self):
        record = AstronomicRecord(name="3MS2", amplitude=1.0, phase=2.0)
        assert record.name == "3MS2"

    def test_harmonic_record_initialization(self):
        record = HarmonicRecord(period=0.0, amplitude=1.0, phase=2.0)
        assert record.period == pytest.approx(0.0)

    def test_cmp_model_initialization_with_data(self):
        model = CMPModel(
            comments=["test content"],
            component={
                "harmonics": [{"period": 0.0, "amplitude": 1.0, "phase": 2.0}],
                "astronomics": [{"name": "4MS10", "amplitude": 1.0, "phase": 2.0}],
            },
        )
        assert model.comments == ["test content"]
        assert len(model.component.harmonics) == 1
        assert len(model.component.astronomics) == 1

    def test_cmp_model_initialization_with_invalid_data(self):
        with pytest.raises(ValueError) as error:
            CMPModel(
                comments=["test content"],
                component={
                    "harmonics": [{"period": 0.0, "amplitude": 1.0, "phase": 2.0}],
                    "astronomics": [{"name": "4MS10", "amplitude": 1.0}],
                },
            )

        expected_error_msg = "phase\n  field required (type=value_error.missing)"
        assert expected_error_msg in str(error.value)

    def test_cmp_model_parse(self):
        model = CMPModel._get_parser()
        assert model == CMPParser.parse

    def test_cmp_model_parse_file_error(self):
        with pytest.raises(Exception) as error:
            CMPModel._get_parser()()

        expected_error_msg = "missing 1 required positional argument: 'filepath'"
        assert expected_error_msg in str(error.value)


class TestCmpParser:
    def test_cmp_parser_initialization(self):
        parser = CMPParser()
        assert isinstance(parser, CMPParser)

    @pytest.mark.parametrize("expected, content", cmp_test_parameters)
    def test_cmp_parser_parse(self, expected, content, fs: FakeFilesystem):
        cmp_file = Path("input.cmp")
        fs.create_file(cmp_file, contents=content)

        parser = CMPParser()
        model = parser.parse(cmp_file)
        assert model == expected

    def test_cmp_parser_parse_comment_error(self, fs: FakeFilesystem):
        cmp_file = Path("input.cmp")
        fs.create_file(
            cmp_file, contents="#test content\n0.0   1.0  2.0\n#comment\n1.0   3.0  4.0"
        )

        with pytest.raises(ValueError) as error:
            CMPParser.parse(cmp_file)

        expected_error_msg = "Line 3: comments are only supported at the start of the file, before the data."
        assert expected_error_msg in str(error.value)

    def test_cmp_parser_parse_too_few_values(self, fs: FakeFilesystem):
        cmp_file = Path("input.cmp")
        fs.create_file(cmp_file, contents="#test content\n0.0   1.0  ")

        with pytest.raises(ValueError) as error:
            CMPParser.parse(cmp_file)

        expected_error_msg = "not enough values to unpack (expected 3, got 2)"
        assert expected_error_msg in str(error.value)

    def test_cmp_parser_parse_too_many_values(self, fs: FakeFilesystem):
        cmp_file = Path("input.cmp")
        fs.create_file(cmp_file, contents="#test content\n0.0   1.0  2.0 3.0")

        with pytest.raises(ValueError) as error:
            CMPParser.parse(cmp_file)

        expected_error_msg = "too many values to unpack (expected 3)"
        assert expected_error_msg in str(error.value)

    def test__is_float_value_none(self):
        assert not CMPParser._is_float(None)


class TestCmpSerializer:
    # Filter out the "multiple with empty line" test case for the serializer test
    cmp_test_parameters_for_serializer = [
        param for param in cmp_test_parameters if param.id != "multiple with empty line"
    ]

    def normalize_expected_content(self, content: str) -> str:
        # Remove extra spaces
        stripped = re.sub(" +", " ", content)
        return stripped

    def test_cmp_serializer_initialization(self):
        serializer = CMPSerializer()
        assert isinstance(serializer, CMPSerializer)

    @pytest.mark.parametrize("data, expected", cmp_test_parameters_for_serializer)
    def test_cmp_serializer_serialize(self, data, expected, fs: FakeFilesystem):

        serializer = CMPModel._get_serializer()
        cmp_file = Path("/fake/output.cmp")
        save_settings = ModelSaveSettings()

        serializer(cmp_file, data, save_settings)

        assert fs.exists(cmp_file)
        with open(cmp_file, "r", encoding="utf8") as file:
            content = file.read()
            assert content == self.normalize_expected_content(expected)
