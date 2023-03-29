from pathlib import Path

import pytest

from hydrolib.core.basemodel import SerializerConfig
from hydrolib.core.dflowfm.tim.models import TimModel
from hydrolib.core.dflowfm.tim.parser import TimParser, TimTimeData
from hydrolib.core.dflowfm.tim.serializer import TimSerializer, TimSerializerConfig
from tests.utils import (
    assert_files_equal,
    test_input_dir,
    test_output_dir,
    test_reference_dir,
)

TRIPLE_DATA = "triple_data_for_timeseries.tim"
SINGLE_DATA = "single_data_for_timeseries.tim"


def _get_triple_data_for_timeseries():
    data = []
    data.append(TimTimeData(time=10.0, series=[1.232, 2.343, 3.454]))
    data.append(TimTimeData(time=20.0, series=[4.565, 5.676, 6.787]))
    data.append(TimTimeData(time=30.0, series=[1.5, 2.6, 3.7]))

    data = dict()
    return data


def _get_triple_data_with_comments_for_timeseries():
    data = []
    data.append(TimTimeData(comment="#comments\n"))
    data.append(TimTimeData(time=10.0, series=[1.232, 2.343, 3.454]))
    data.append(TimTimeData(time=20.0, series=[4.565, 5.676, 6.787]))
    data.append(TimTimeData(time=30.0, series=[1.5, 2.6, 3.7]))
    data.append(TimTimeData(comment="* 40 1.5 2.6 3.7\n"))
    data.append(TimTimeData(comment="# 50 1.5 2.6 3.7"))
    return data


def _get_single_data_for_timeseries():
    data = []
    data.append(TimTimeData(time=0.0, series=[0.0000000]))
    data.append(TimTimeData(time=10.0, series=[0.0100000]))
    data.append(TimTimeData(time=20.0, series=[0.0000000]))
    data.append(TimTimeData(time=30.0, series=[-0.0100000]))
    data.append(TimTimeData(time=40.0, series=[0.0000000]))
    data.append(TimTimeData(time=50.0, series=[0.0100000]))
    data.append(TimTimeData(time=60.0, series=[0.0000000]))
    data.append(TimTimeData(time=70.0, series=[-0.0100000]))
    data.append(TimTimeData(time=80.0, series=[0.0000000]))
    data.append(TimTimeData(time=90.0, series=[0.0100000]))
    data.append(TimTimeData(time=100.0, series=[0.0000000]))
    data.append(TimTimeData(time=110.0, series=[-0.0100000]))
    data.append(TimTimeData(time=120.0, series=[0.0000000]))
    return data


class TestTimSerializer:
    @pytest.mark.parametrize(
        "input_data, reference_path",
        [
            pytest.param(
                {"comments":[str,"this file\n", " contains\n", " stuff\n"],
                10:[1.232, 2.343, 3.454],
                20:[4.565, 5.676, 6.787],
                30:[1.5, 2.6, 3.7]},
                Path(test_reference_dir / "tim" / "triple_data_for_timeseries_with_comments.tim"),
                id="triple_data_for_timeseries_with_comments"
            ),
            pytest.param(
                {"comments":[],
                10:[1.232, 2.343, 3.454],
                20:[4.565, 5.676, 6.787],
                30:[1.5, 2.6, 3.7]},
                Path(test_reference_dir / "tim" / "triple_data_for_timeseries.tim"),
                id="triple_data_for_timeseries"
            ),
            pytest.param(
                {"comments":[],
                0.000000   :[0.0000000],
                10.000000   :[0.0100000],
                20.000000   :[0.0000000],
                30.000000   :[-0.0100000],
                40.000000   :[0.0000000],
                50.000000   :[0.0100000],
                60.000000   :[0.0000000],
                70.000000   :[-0.0100000],
                80.000000   :[0.0000000],
                90.000000   :[0.0100000],
                100.000000  :[0.0000000],
                110.000000  :[-0.0100000],
                120.000000  :[0.0000000]},
                Path(test_reference_dir/ "tim"/ "single_data_for_timeseries.tim"),
                id="single_data_for_timeseries"
            ),
        ]
    )
    def test_serialize_data(self, input_data, reference_path):
        output_path = Path(test_output_dir/ "tim"/ "test_serialize.tim")
        config = TimSerializerConfig(float_format=".3f")
        TimSerializer.serialize(output_path, input_data, config)
        assert_files_equal(output_path, reference_path)

class TestTimModel:
    @pytest.mark.parametrize(
        "input_data, reference_path",
        [
            pytest.param(
                {"comments":[str,"this file\n", " contains\n", " stuff\n"],
                10:[1.232, 2.343, 3.454],
                20:[4.565, 5.676, 6.787],
                30:[1.5, 2.6, 3.7]},
                Path(test_reference_dir / "tim" / "triple_data_for_timeseries_with_comments.tim"),
                id="triple_data_for_timeseries_with_comments"
            ),
            pytest.param(
                {"comments":[],
                10:[1.232, 2.343, 3.454],
                20:[4.565, 5.676, 6.787],
                30:[1.5, 2.6, 3.7]},
                Path(test_reference_dir / "tim" / "triple_data_for_timeseries.tim"),
                id="triple_data_for_timeseries"
            ),
            pytest.param(
                {"comments":[],
                0.000000   :[0.0000000],
                10.000000   :[0.0100000],
                20.000000   :[0.0000000],
                30.000000   :[-0.0100000],
                40.000000   :[0.0000000],
                50.000000   :[0.0100000],
                60.000000   :[0.0000000],
                70.000000   :[-0.0100000],
                80.000000   :[0.0000000],
                90.000000   :[0.0100000],
                100.000000  :[0.0000000],
                110.000000  :[-0.0100000],
                120.000000  :[0.0000000]},
                Path(test_reference_dir/ "tim"/ "single_data_for_timeseries.tim"),
                id="single_data_for_timeseries"
            ),
        ]
    )
    def test_save_data_for_timeseries(self, input_data, reference_path):
        model = TimModel(timeseries=input_data)
        output_path = Path(test_output_dir / "tim" / "test_save.tim")
        model.filepath = output_path
        model.serializer_config.float_format = ".3f"
        model.save()
        assert_files_equal(output_path, reference_path)

class TestTimParser:
    @pytest.mark.parametrize(
        "expected_output, input_path",
        [
            pytest.param(
                {"comments":[str],
                10:[1.232, 2.343, 3.454],
                20:[4.565, 5.676, 6.787],
                30:[1.5, 2.6, 3.7]},
                Path(test_input_dir / "tim" / TRIPLE_DATA),
                id="triple_data_for_timeseries"
            ),
            pytest.param(
                {"comments":[str],
                10:[1.232, 2.343, 3.454],
                20:[4.565, 5.676, 6.787],
                30:[1.5, 2.6, 3.7]},
                Path(
                    test_input_dir
                    / "tim"
                    / "triple_data_for_timeseries_different_whitespaces_between_data.tim"
                ),
                id="triple_data_for_timeseries_different_whitespaces_between_data"
            ),
            pytest.param(
                {"comments":[str,"comments\n", " 40 1.5 2.6 3.7\n", " 50 1.5 2.6 3.7"],
                10:[1.232, 2.343, 3.454],
                20:[4.565, 5.676, 6.787],
                30:[1.5, 2.6, 3.7]},
                Path(
                    test_input_dir
                    / "tim"
                    / "triple_data_for_timeseries_with_comments.tim"
                ),
                id="triple_data_for_timeseries_with_comments"
            ),
            pytest.param(
                {"comments":[str],
                0.000000   :[0.0000000],
                10.000000   :[0.0100000],
                20.000000   :[0.0000000],
                30.000000   :[-0.0100000],
                40.000000   :[0.0000000],
                50.000000   :[0.0100000],
                60.000000   :[0.0000000],
                70.000000   :[-0.0100000],
                80.000000   :[0.0000000],
                90.000000   :[0.0100000],
                100.000000  :[0.0000000],
                110.000000  :[-0.0100000],
                120.000000  :[0.0000000]},
                Path(
                    test_input_dir
                    / "tim"
                    / "single_data_for_timeseries.tim"
                ),
                id="single_data_for_timeseries"
            ),
        ]
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
                    / "triple_data_for_timeseries_with_one_line_with_not_enough_information.tim"
                ),
                id="triple_data_for_timeseries_with_one_line_with_not_enough_information"
            ),
        ]
    )
    def test_parse_data_throws_exception(self, input_path):
        with pytest.raises(ValueError) as error:
            TimParser.parse(input_path)
        found_msg = error.value.args[0]

        expected_error_msg = f"Error parsing tim file '{input_path}'."
        assert found_msg == expected_error_msg

