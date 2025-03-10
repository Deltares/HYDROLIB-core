import math
from pathlib import Path

import pytest

from hydrolib.core.basemodel import ModelSaveSettings
from hydrolib.core.dflowfm.tim.models import TimModel, TimRecord
from hydrolib.core.dflowfm.tim.parser import TimParser
from hydrolib.core.dflowfm.tim.serializer import TimSerializer, TimSerializerConfig
from tests.utils import (
    assert_files_equal,
    test_input_dir,
    test_output_dir,
    test_reference_dir,
)


class TestTimSerializer:
    triple_data_for_timeseries_floats = [
        {"time": 10, "data": [1.232, 2.343, 3.454]},
        {"time": 20, "data": [4.565, 5.676, 6.787]},
        {"time": 30, "data": [1.5, 2.6, 3.7]},
    ]

    single_data_for_timeseries_floats = [
        {"time": 0.000000, "data": [0.0000000]},
        {"time": 10.000000, "data": [0.0100000]},
        {"time": 20.000000, "data": [0.0000000]},
        {"time": 30.000000, "data": [-0.0100000]},
        {"time": 40.000000, "data": [0.0000000]},
        {"time": 50.000000, "data": [0.0100000]},
        {"time": 60.000000, "data": [0.0000000]},
        {"time": 70.000000, "data": [-0.0100000]},
        {"time": 80.000000, "data": [0.0000000]},
        {"time": 90.000000, "data": [0.0100000]},
        {"time": 100.000000, "data": [0.0000000]},
        {"time": 110.000000, "data": [-0.0100000]},
        {"time": 120.000000, "data": [0.0000000]},
    ]

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
    triple_data_for_timeseries_floats = [
        TimRecord(time=10, data=[1.232, 2.343, 3.454]),
        TimRecord(time=20, data=[4.565, 5.676, 6.787]),
        TimRecord(time=30, data=[1.5, 2.6, 3.7]),
    ]

    single_data_for_timeseries_floats = [
        TimRecord(time=0.0000000, data=[0.0000000]),
        TimRecord(time=10.000000, data=[0.0100000]),
        TimRecord(time=20.000000, data=[0.0000000]),
        TimRecord(time=30.000000, data=[-0.0100000]),
        TimRecord(time=40.000000, data=[0.0000000]),
        TimRecord(time=50.000000, data=[0.0100000]),
        TimRecord(time=60.000000, data=[0.0000000]),
        TimRecord(time=70.000000, data=[-0.0100000]),
        TimRecord(time=80.000000, data=[0.0000000]),
        TimRecord(time=90.000000, data=[0.0100000]),
        TimRecord(time=100.00000, data=[0.0000000]),
        TimRecord(time=110.00000, data=[-0.0100000]),
        TimRecord(time=120.00000, data=[0.0000000]),
    ]

    def test_initialization(self):
        model = TimModel()
        assert len(model.comments) == 0
        assert len(model.timeseries) == 0
        assert model.as_dataframe().empty

    def test_initialize_with_quantities_names(self, input_files_dir: Path):
        """
        Test Initializing the `TimModel` from a file and provide the name of the quantities in the files.

        The initialization should initizline the super class `BaseModel` with the file path.
        The `quantities_names` is used to initialize the `quantities_names` attribute.
        """
        path = input_files_dir / "tim/single_data_for_timeseries.tim"
        model = TimModel(path, quantities_names=["a"])
        assert model.quantities_names == ["a"]
        assert len(model.timeseries) == 13

    def test_get_units(self, input_files_dir: Path):
        """
        Test the `get_units` method. The method should return the units of the quantities in the timeseries.
        """
        path = input_files_dir / "tim/single_data_for_timeseries.tim"
        model = TimModel(path, quantities_names=["discharge"])
        assert model.get_units() == ["m3/s"]
        model.quantities_names = ["waterlevel"]
        assert model.get_units() == ["m"]
        model.quantities_names = ["temperature"]
        assert model.get_units() == ["degC"]
        model.quantities_names = ["salinity"]
        assert model.get_units() == ["1e-3"]
        model.quantities_names = ["initialtracerAnyname"]
        assert model.get_units() == ["-"]

    def test_as_dataframe(self):
        model = TimModel(
            timeseries=self.single_data_for_timeseries_floats,
            comments=["this file", "contains", "stuff"],
        )
        df = model.as_dataframe()
        assert all(
            df.index
            == [
                self.single_data_for_timeseries_floats[i].time
                for i in range(len(self.single_data_for_timeseries_floats))
            ]
        )
        assert df.shape == (13, 1)
        assert df.columns.to_list() == [0]
        vals = [
            self.single_data_for_timeseries_floats[i].data[0]
            for i in range(len(self.single_data_for_timeseries_floats))
        ]
        assert df.loc[:, 0].to_list() == vals

        df = model.as_dataframe(columns=["data"])
        assert df.columns.to_list() == ["data"]

    def test_with_quantities_names(self):
        model = TimModel(
            timeseries=self.single_data_for_timeseries_floats, quantities_names=["a"]
        )
        assert model.quantities_names == ["a"]
        with pytest.raises(ValueError):
            TimModel(
                timeseries=self.single_data_for_timeseries_floats,
                quantities_names=["a", "b"],
            )

    def test_with_extra_un_needed_parameters(self):
        with pytest.raises(ValueError):
            TimModel(
                timeseries=self.single_data_for_timeseries_floats,
                extra_param="extra",
            )
            print("Extra parameters are not allowed")

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
                    "timeseries": [
                        {"time": 10, "data": [1.232, "text shouldn't be here", 3.454]},
                        {"time": 20, "data": [4.565, 5.676, 6.787]},
                        {"time": 30, "data": [1.5, 2.6, 3.7]},
                    ],
                },
                "value is not a valid float",
                id="value is not a valid float",
            ),
            pytest.param(
                {
                    "comments": [],
                    "timeseries": [
                        TimRecord(time=10, data=[1.232, 2.343, 3.454]),
                        TimRecord(time=20, data=[4.565]),
                        TimRecord(time=30, data=[1.5, 2.6, 3.7]),
                    ],
                },
                f"Time {20.0}: Expected {3} columns, but was {1}",
                id="Problem with values in timeseries, for time, values missing",
            ),
            pytest.param(
                {
                    "comments": [],
                    "timeseries": [
                        TimRecord(time=10, data=[1.232, 2.343, 3.454]),
                        TimRecord(time=20, data=[4.565, 5.676, 6.787, 3.454]),
                        TimRecord(time=30, data=[1.5, 2.6, 3.7]),
                    ],
                },
                f"Time {20.0}: Expected {3} columns, but was {4}",
                id="Problem with values in timeseries, for time, too many values",
            ),
            pytest.param(
                {
                    "comments": [],
                    "timeseries": [
                        TimRecord(time=10, data=[]),
                        TimRecord(time=20, data=[]),
                        TimRecord(time=30, data=[]),
                    ],
                },
                "Time series cannot be empty.",
                id="Problem with values in timeseries, no timeseries",
            ),
            pytest.param(
                {
                    "comments": [],
                    "timeseries": [
                        TimRecord(time=10, data=[1.232, 2.343, 3.454]),
                        TimRecord(time=20, data=[1.232, 2.343, 3.454]),
                        TimRecord(time=10, data=[4.565, 5.676, 6.787]),
                    ],
                },
                f"Timeseries cannot contain duplicate times. Time: {10.0} is duplicate.",
                id="Problem with time in timeseries, duplicate times",
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

    def test_test_fortran_d_exponent_supported(self):
        input_path = Path(test_input_dir / "tim" / "unimagdir.wnd")
        tim_model = TimModel(input_path)
        assert tim_model.timeseries[0].time == 0
        assert tim_model.timeseries[0].data == [1.0, 270.0]
        assert math.isclose(tim_model.timeseries[1].time, 9e9)
        assert tim_model.timeseries[1].data == [1.0, 270.0]

    def test_add_location_values(self):
        model = TimModel(
            timeseries=[
                TimRecord(time=0.0, data=[1.0, 2.0]),
                TimRecord(time=1.0, data=[3.0, 4.0]),
            ],
            comments=["this file", "contains", "stuff"],
            quantities_names=["discharge", "waterlevel"],
        )

        model.add_column([5.0, 6.0], "location")

        assert model.timeseries[0].data == [1.0, 2.0, 5.0]
        assert model.timeseries[1].data == [3.0, 4.0, 6.0]
        assert model.quantities_names == ["discharge", "waterlevel", "location"]
        model.as_dict()["location"] = [5.0, 6.0]

        # Test with mismatched lengths
        with pytest.raises(ValueError):
            model.add_column([7.0])

        # test when quantities_names is not provided
        model.add_column([7.0, 8.0])
        assert model.as_dict()["quantity-4"] == [7.0, 8.0]


class TestTimRecord:
    def test_initialization(self):
        record = TimRecord(time=0)
        assert len(record.data) == 0


class TestTimParser:
    triple_data_for_timeseries = [
        {"time": "10", "data": ["1.232", "2.343", "3.454"]},
        {"time": "20", "data": ["4.565", "5.676", "6.787"]},
        {"time": "30", "data": ["1.5", "2.6", "3.7"]},
    ]

    single_data_for_timeseries = [
        {"time": "0.000000", "data": ["0.0000000"]},
        {"time": "10.000000", "data": ["0.0100000"]},
        {"time": "20.000000", "data": ["0.0000000"]},
        {"time": "30.000000", "data": ["-0.0100000"]},
        {"time": "40.000000", "data": ["0.0000000"]},
        {"time": "50.000000", "data": ["0.0100000"]},
        {"time": "60.000000", "data": ["0.0000000"]},
        {"time": "70.000000", "data": ["-0.0100000"]},
        {"time": "80.000000", "data": ["0.0000000"]},
        {"time": "90.000000", "data": ["0.0100000"]},
        {"time": "100.000000", "data": ["0.0000000"]},
        {"time": "110.000000", "data": ["-0.0100000"]},
        {"time": "120.000000", "data": ["0.0000000"]},
    ]

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

    @pytest.mark.parametrize(
        "input_path",
        [
            pytest.param(
                Path(
                    test_input_dir
                    / "tim"
                    / "triple_data_for_timeseries_with_empty_data.tim"
                ),
                id="triple_data_for_timeseries_with_empty_data",
            ),
            pytest.param(
                Path(
                    test_input_dir / "tim" / "bc_file_format_incorrect_for_timmodel.bc"
                ),
                id="bc_file_format_incorrect_for_timmodel",
            ),
        ],
    )
    def test_parse_data_throws_exception_error_parsing_tim_file_values_is_empty(
        self, input_path
    ):
        with pytest.raises(ValueError) as error:
            TimParser.parse(input_path)

        expected_error_msg = f"Line {0}: Time series cannot be empty."
        assert expected_error_msg in str(error.value)
