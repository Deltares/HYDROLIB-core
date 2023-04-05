from pathlib import Path

import pytest

from hydrolib.core.basemodel import ModelSaveSettings
from hydrolib.core.dflowfm.tim.models import TimModel
from hydrolib.core.dflowfm.tim.parser import TimParser
from hydrolib.core.dflowfm.tim.serializer import TimSerializer, TimSerializerConfig
from tests.utils import (
    assert_files_equal,
    test_input_dir,
    test_output_dir,
    test_reference_dir,
)

triple_data_for_timeseries_floats = {
    10: [1.232, 2.343, 3.454],
    20: [4.565, 5.676, 6.787],
    30: [1.5, 2.6, 3.7],
}

single_data_for_timeseries_floats = {
    0.000000: [0.0000000],
    10.000000: [0.0100000],
    20.000000: [0.0000000],
    30.000000: [-0.0100000],
    40.000000: [0.0000000],
    50.000000: [0.0100000],
    60.000000: [0.0000000],
    70.000000: [-0.0100000],
    80.000000: [0.0000000],
    90.000000: [0.0100000],
    100.000000: [0.0000000],
    110.000000: [-0.0100000],
    120.000000: [0.0000000],
}


class TestTimSerializer:
    @pytest.mark.parametrize(
        "input_data, reference_path",
        [
            pytest.param(
                {
                    "comments": ["this file", "contains", "stuff"],
                    "timeseries": triple_data_for_timeseries_floats,
                },
                Path(
                    test_reference_dir
                    / "tim"
                    / "triple_data_for_timeseries_with_comments.tim"
                ),
                id="triple_data_for_timeseries_with_comments",
            ),
            pytest.param(
                {
                    "comments": [],
                    "timeseries": triple_data_for_timeseries_floats,
                },
                Path(test_reference_dir / "tim" / "triple_data_for_timeseries.tim"),
                id="triple_data_for_timeseries",
            ),
            pytest.param(
                {
                    "comments": [],
                    "timeseries": single_data_for_timeseries_floats,
                },
                Path(test_reference_dir / "tim" / "single_data_for_timeseries.tim"),
                id="single_data_for_timeseries",
            ),
        ],
    )
    def test_serialize_data(self, input_data, reference_path):
        output_path = Path(test_output_dir / "tim" / "test_serialize.tim")
        config = TimSerializerConfig(float_format=".3f")
        TimSerializer.serialize(output_path, input_data, config, ModelSaveSettings())
        assert_files_equal(output_path, reference_path)


class TestTimModel:
    @pytest.mark.parametrize(
        "input_data, reference_path",
        [
            pytest.param(
                {
                    "comments": ["this file", "contains", "stuff"],
                    "timeseries": triple_data_for_timeseries_floats,
                },
                Path(
                    test_reference_dir
                    / "tim"
                    / "triple_data_for_timeseries_with_comments.tim"
                ),
                id="triple_data_for_timeseries_with_comments",
            ),
            pytest.param(
                {
                    "comments": [],
                    "timeseries": triple_data_for_timeseries_floats,
                },
                Path(test_reference_dir / "tim" / "triple_data_for_timeseries.tim"),
                id="triple_data_for_timeseries",
            ),
            pytest.param(
                {
                    "comments": [],
                    "timeseries": single_data_for_timeseries_floats,
                },
                Path(test_reference_dir / "tim" / "single_data_for_timeseries.tim"),
                id="single_data_for_timeseries",
            ),
        ],
    )
    def test_save_data_for_timeseries(self, input_data, reference_path):
        model = TimModel(
            timeseries=input_data["timeseries"], comments=input_data["comments"]
        )
        output_path = Path(test_output_dir / "tim" / "test_save.tim")
        model.filepath = output_path
        model.serializer_config.float_format = ".3f"
        model.save()
        assert_files_equal(output_path, reference_path)

    @pytest.mark.parametrize(
        "input_data, expected_error_msg",
        [
            pytest.param(
                {
                    "comments": [],
                    "timeseries": {
                        10: [1.232, "text shouldn't be here", 3.454],
                        20: [4.565, 5.676, 6.787],
                        30: [1.5, 2.6, 3.7],
                    },
                },
                "value is not a valid float",
                id="value is not a valid float",
            ),
            pytest.param(
                {
                    "comments": [],
                    "timeseries": {
                        10: [1.232, 2.343, 3.454],
                        20: [4.565],
                        30: [1.5, 2.6, 3.7],
                    },
                },
                f"Time {20.0}: Expected {3} columns, but was {1}",
                id="Problem with values in timeseries, for time, values missing",
            ),
            pytest.param(
                {
                    "comments": [],
                    "timeseries": {
                        10: [1.232, 2.343, 3.454],
                        20: [4.565, 5.676, 6.787, 3.454],
                        30: [1.5, 2.6, 3.7],
                    },
                },
                f"Time {20.0}: Expected {3} columns, but was {4}",
                id="Problem with values in timeseries, for time, too many values",
            ),
            pytest.param(
                {
                    "comments": [],
                    "timeseries": {
                        10: [],
                        20: [],
                        30: [],
                    },
                },
                "Time series cannot be empty.",
                id="Problem with values in timeseries, no timeseries",
            ),
        ],
    )
    def test_validate_data_for_timeseries_throws_exception_for_incorrect_data(
        self, input_data, expected_error_msg
    ):
        with pytest.raises(ValueError) as error:
            TimModel(
                timeseries=input_data["timeseries"], comments=input_data["comments"]
            )

        assert expected_error_msg in str(error.value)


class TestTimParser:
    triple_data_for_timeseries = {
        "10": ["1.232", "2.343", "3.454"],
        "20": ["4.565", "5.676", "6.787"],
        "30": ["1.5", "2.6", "3.7"],
    }

    single_data_for_timeseries = {
        "0.000000": ["0.0000000"],
        "10.000000": ["0.0100000"],
        "20.000000": ["0.0000000"],
        "30.000000": ["-0.0100000"],
        "40.000000": ["0.0000000"],
        "50.000000": ["0.0100000"],
        "60.000000": ["0.0000000"],
        "70.000000": ["-0.0100000"],
        "80.000000": ["0.0000000"],
        "90.000000": ["0.0100000"],
        "100.000000": ["0.0000000"],
        "110.000000": ["-0.0100000"],
        "120.000000": ["0.0000000"],
    }

    @pytest.mark.parametrize(
        "expected_output, input_path",
        [
            pytest.param(
                {"comments": [], "timeseries": triple_data_for_timeseries},
                Path(test_input_dir / "tim" / "triple_data_for_timeseries.tim"),
                id="triple_data_for_timeseries",
            ),
            pytest.param(
                {"comments": [], "timeseries": triple_data_for_timeseries},
                Path(
                    test_input_dir
                    / "tim"
                    / "triple_data_for_timeseries_different_whitespaces_between_data.tim"
                ),
                id="triple_data_for_timeseries_different_whitespaces_between_data",
            ),
            pytest.param(
                {
                    "comments": [
                        "comments",
                        "this is another comment",
                    ],
                    "timeseries": triple_data_for_timeseries,
                },
                Path(
                    test_input_dir
                    / "tim"
                    / "triple_data_for_timeseries_with_comments.tim"
                ),
                id="triple_data_for_timeseries_with_comments",
            ),
            pytest.param(
                {"comments": [], "timeseries": single_data_for_timeseries},
                Path(test_input_dir / "tim" / "single_data_for_timeseries.tim"),
                id="single_data_for_timeseries",
            ),
        ],
    )
    def test_parse_data(self, expected_output, input_path):
        data = TimParser.parse(input_path)
        assert data == expected_output

    @pytest.mark.parametrize(
        "input_path",
        [
            pytest.param(
                Path(
                    test_input_dir
                    / "tim"
                    / "triple_data_for_timeseries_with_comments_between_data_hashtag.tim"
                ),
                id="triple_data_for_timeseries_with_comments_between_data_hashtag",
            ),
            pytest.param(
                Path(
                    test_input_dir
                    / "tim"
                    / "triple_data_for_timeseries_with_comments_between_data_star.tim"
                ),
                id="triple_data_for_timeseries_with_comments_between_data_star",
            ),
        ],
    )
    def test_parse_data_throws_exception_error_parsing_tim_file_comments_between_data_not_supported(
        self, input_path
    ):
        with pytest.raises(ValueError) as error:
            TimParser.parse(input_path)

        expected_error_msg = f"Line {5}: comments are only supported at the start of the file, before the time series data."
        assert expected_error_msg in str(error.value)
