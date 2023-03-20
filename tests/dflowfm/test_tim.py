from hydrolib.core.basemodel import SerializerConfig
from hydrolib.core.dflowfm.tim.models import TimModel
from hydrolib.core.dflowfm.tim.serializer import TimSerializer
from hydrolib.core.dflowfm.tim.parser import TimParser, TimTimeSerie
from tests.utils import assert_files_equal, test_output_dir, test_input_dir, test_reference_dir

from pathlib import Path
import pytest

class TestTimSerializer:
    @pytest.mark.parametrize(
        "input, output_path, reference_path, config",
        [
            (
                {10:[1.232, 2.343, 3.454],
                20:[4.565, 5.676, 6.787],
                30:[1.5, 2.6, 3.7]},
                Path(test_output_dir / "tim" / "test_serialize.tim"),
                Path(test_reference_dir / "tim" / "triple_data_for_timeseries.tim"),
                SerializerConfig(float_format=".3f")
            ),
            (
                {0.000000   :[0.0000000],
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
                Path(test_output_dir / "tim" / "test_serialize.tim"),
                Path(test_reference_dir / "tim" / "single_data_for_timeseries.tim"),
                SerializerConfig(float_format=".6f")
            ),
        ],
    )
    def test_serialize(self, input: dict[float, list[float]], output_path, reference_path, config):
        TimSerializer.serialize(output_path, input, config)
        assert_files_equal(output_path, reference_path)


class TestTimModel:
    @pytest.mark.parametrize(
        "input, output_path, reference_path, float_format",
        [
            (
                {10:[1.232, 2.343, 3.454],
                20:[4.565, 5.676, 6.787],
                30:[1.5, 2.6, 3.7]},
                Path(test_output_dir / "tim" / "test_save.tim"),
                Path(test_reference_dir / "tim" / "triple_data_for_timeseries.tim"),
                ".3f"
            ),
            (
                {0.000000   :[0.0000000],
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
                Path(test_output_dir / "tim" / "test_save.tim"),
                Path(test_reference_dir / "tim" / "single_data_for_timeseries.tim"),
                ".6f"
            ),
        ],
    )
    def test_save(self, input: dict[float, list[float]], output_path, reference_path, float_format):
        model = TimModel(timeseries=input)
        model.filepath = output_path
        model.serializer_config.float_format = float_format
        model.save()
        assert_files_equal(output_path, reference_path)

class TestTimParser:
    @pytest.mark.parametrize(
        "input_path",
        [
            Path(test_input_dir / "tim" / "triple_data_for_timeseries.tim"),
            Path(test_input_dir / "tim" / "triple_data_for_timeseries_different_whitespaces_between_data.tim"),
            Path(test_input_dir / "tim" / "triple_data_for_timeseries_with_one_line_with_not_enough_information.tim"),
            Path(test_input_dir / "tim" / "triple_data_for_timeseries_with_comments_after_data.tim"),
        ],
    )
    def test_parse_with_triple_data_for_timeseries(self, input_path):        
        data = TimParser.parse(input_path)

        expected_output = []
        expected_output.append(TimTimeSerie(time=10.0, series=[1.232,  2.343,  3.454]))
        expected_output.append(TimTimeSerie(time=20.0, series=[4.565,   5.676,  6.787]))
        expected_output.append(TimTimeSerie(time=30.0, series=[1.5,     2.6,    3.7]))     

        for i in range(len(expected_output)):
            assert(data[i].time == expected_output[i].time)
            assert(data[i].series == expected_output[i].series)
            assert(data[i].comment == expected_output[i].comment)

    def test_parse_with_single_data_for_timeseries(self):
        input_path = Path(test_input_dir / "tim" / "single_data_for_timeseries.tim")
        data = TimParser.parse(input_path)

        expected_output = []
        expected_output.append(TimTimeSerie(time=0.0, series=[0.0000000]))
        expected_output.append(TimTimeSerie(time=10.0, series=[0.0100000]))
        expected_output.append(TimTimeSerie(time=20.0, series=[0.0000000]))   
        expected_output.append(TimTimeSerie(time=30.0, series=[-0.0100000]))
        expected_output.append(TimTimeSerie(time=40.0, series=[0.0000000]))
        expected_output.append(TimTimeSerie(time=50.0, series=[0.0100000] ))
        expected_output.append(TimTimeSerie(time=60.0, series=[0.0000000]))
        expected_output.append(TimTimeSerie(time=70.0, series=[-0.0100000]))
        expected_output.append(TimTimeSerie(time=80.0, series=[0.0000000]))
        expected_output.append(TimTimeSerie(time=90.0, series=[0.0100000]))
        expected_output.append(TimTimeSerie(time=100.0, series=[0.0000000]))
        expected_output.append(TimTimeSerie(time=110.0, series=[-0.0100000]))
        expected_output.append(TimTimeSerie(time=120.0, series=[0.0000000]))


        for i in range(len(expected_output)):
            assert(data[i].time == expected_output[i].time)
            assert(data[i].series == expected_output[i].series)
            assert(data[i].comment == expected_output[i].comment)

    def test_parse_with_comments(self):
        input_path = Path(test_input_dir / "tim" / "triple_data_for_timeseries_with_comments.tim")   
        data = TimParser.parse(input_path)

        expected_output = []
        expected_output.append(TimTimeSerie(comment="#comments\n"))
        expected_output.append(TimTimeSerie(time=10.0, series=[1.232,  2.343,  3.454]))
        expected_output.append(TimTimeSerie(time=20.0, series=[4.565,   5.676,  6.787]))
        expected_output.append(TimTimeSerie(time=30.0, series=[1.5,     2.6,    3.7]))     
        expected_output.append(TimTimeSerie(comment="* 40 1.5 2.6 3.7\n"))
        expected_output.append(TimTimeSerie(comment="# 50 1.5 2.6 3.7"))

        for i in range(len(expected_output)):
            assert(data[i].time == expected_output[i].time)
            assert(data[i].series == expected_output[i].series)
            assert(data[i].comment == expected_output[i].comment)