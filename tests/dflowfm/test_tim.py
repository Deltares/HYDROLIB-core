from hydrolib.core.basemodel import SerializerConfig
from hydrolib.core.dflowfm.tim.models import TimModel
from hydrolib.core.dflowfm.tim.serializer import TimSerializer
from hydrolib.core.dflowfm.tim.parser import TimParser, TimTimeSerie
from tests.utils import assert_files_equal, test_output_dir, test_input_dir, test_reference_dir
from pathlib import Path
import pytest

TRIPLE_DATA = "triple_data_for_timeseries.tim"
SINGLE_DATA = "single_data_for_timeseries.tim"

def _get_triple_data_for_timeseries():
    data = []
    data.append(TimTimeSerie(time=10.0, series=[1.232,  2.343,  3.454]))
    data.append(TimTimeSerie(time=20.0, series=[4.565,   5.676,  6.787]))
    data.append(TimTimeSerie(time=30.0, series=[1.5,     2.6,    3.7]))   
    return data

def _get_triple_data_with_comments_for_timeseries():
    data = []
    data.append(TimTimeSerie(comment="#comments\n"))
    data.append(TimTimeSerie(time=10.0, series=[1.232,  2.343,  3.454]))
    data.append(TimTimeSerie(time=20.0, series=[4.565,   5.676,  6.787]))
    data.append(TimTimeSerie(time=30.0, series=[1.5,     2.6,    3.7]))     
    data.append(TimTimeSerie(comment="* 40 1.5 2.6 3.7\n"))
    data.append(TimTimeSerie(comment="# 50 1.5 2.6 3.7"))  
    return data

def _get_single_data_for_timeseries():
    data = []
    data.append(TimTimeSerie(time=0.0, series=[0.0000000]))
    data.append(TimTimeSerie(time=10.0, series=[0.0100000]))
    data.append(TimTimeSerie(time=20.0, series=[0.0000000]))   
    data.append(TimTimeSerie(time=30.0, series=[-0.0100000]))
    data.append(TimTimeSerie(time=40.0, series=[0.0000000]))
    data.append(TimTimeSerie(time=50.0, series=[0.0100000] ))
    data.append(TimTimeSerie(time=60.0, series=[0.0000000]))
    data.append(TimTimeSerie(time=70.0, series=[-0.0100000]))
    data.append(TimTimeSerie(time=80.0, series=[0.0000000]))
    data.append(TimTimeSerie(time=90.0, series=[0.0100000]))
    data.append(TimTimeSerie(time=100.0, series=[0.0000000]))
    data.append(TimTimeSerie(time=110.0, series=[-0.0100000]))
    data.append(TimTimeSerie(time=120.0, series=[0.0000000]))
    return data

class TestTimSerializer:
    def test_serialize_triple_data_for_timeseries(self): 
        input_data = _get_triple_data_for_timeseries()
        output_path = Path(test_output_dir / "tim" / "test_serialize.tim")
        reference_path = Path(test_reference_dir / "tim" / TRIPLE_DATA)
        config = SerializerConfig(float_format=".3f")
        TimSerializer.serialize(output_path, input_data, config)
        assert_files_equal(output_path, reference_path)

    def test_serialize_single_data_for_timeseries(self):
        input_data = _get_single_data_for_timeseries()

        output_path = Path(test_output_dir / "tim" / "test_serialize.tim")
        reference_path = Path(test_reference_dir / "tim" / SINGLE_DATA)
        config = SerializerConfig(float_format=".6f")

        TimSerializer.serialize(output_path, input_data, config)
        assert_files_equal(output_path, reference_path)

class TestTimModel:
    def test_save_triple_data_for_timeseries(self):
        model = TimModel(timeseries=_get_triple_data_for_timeseries())
        output_path = Path(test_output_dir / "tim" / "test_save.tim")
        reference_path = Path(test_reference_dir / "tim" / TRIPLE_DATA)
        model.filepath = output_path
        model.serializer_config.float_format = ".3f"
        model.save()
        assert_files_equal(output_path, reference_path)

    def test_save_single_data_for_timeseries(self):
        model = TimModel(timeseries=_get_single_data_for_timeseries())
        output_path = Path(test_output_dir / "tim" / "test_save.tim")
        reference_path = Path(test_reference_dir / "tim" / SINGLE_DATA)
        model.filepath = output_path
        model.serializer_config.float_format = ".6f"
        model.save()
        assert_files_equal(output_path, reference_path)

class TestTimParser:
    @pytest.mark.parametrize(
        "input_path",
        [
            Path(test_input_dir / "tim" / TRIPLE_DATA),
            Path(test_input_dir / "tim" / "triple_data_for_timeseries_different_whitespaces_between_data.tim"),
            Path(test_input_dir / "tim" / "triple_data_for_timeseries_with_one_line_with_not_enough_information.tim"),
            Path(test_input_dir / "tim" / "triple_data_for_timeseries_with_comments_after_data.tim"),
        ],
    )
    def test_parse_with_triple_data_for_timeseries(self, input_path):        
        data = TimParser.parse(input_path)

        expected_output = _get_triple_data_for_timeseries() 

        for i in range(len(expected_output)):
            assert(data[i].time == expected_output[i].time)
            assert(data[i].series == expected_output[i].series)
            assert(data[i].comment == expected_output[i].comment)

    def test_parse_with_single_data_for_timeseries(self):
        input_path = Path(test_input_dir / "tim" / SINGLE_DATA)
        data = TimParser.parse(input_path)

        expected_output = _get_single_data_for_timeseries() 

        for i in range(len(expected_output)):
            assert(data[i].time == expected_output[i].time)
            assert(data[i].series == expected_output[i].series)
            assert(data[i].comment == expected_output[i].comment)

    def test_parse_with_comments(self):
        input_path = Path(test_input_dir / "tim" / "triple_data_for_timeseries_with_comments.tim")   
        data = TimParser.parse(input_path)

        expected_output = _get_triple_data_with_comments_for_timeseries() 

        for i in range(len(expected_output)):
            assert(data[i].time == expected_output[i].time)
            assert(data[i].series == expected_output[i].series)
            assert(data[i].comment == expected_output[i].comment)