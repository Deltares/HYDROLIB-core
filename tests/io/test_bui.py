from tests.utils import test_input_dir, test_output_dir, test_reference_dir
from hydrolib.core.io.bui.parser import BuiParser

class TestModel:
    pass

class TestBuiParser:
    def test_given_valid_file_parses_values(self):
        test_file = test_input_dir / "rr_sample_trimmed" / "rr" / "default.bui"
        assert test_file.is_file(), "Test File not found."
        dict_values = BuiParser.parse(test_file)
        assert dict_values is not None
        assert dict_values["default_dataset"] == "1"
        assert dict_values["number_of_stations"] == "1"
        assert dict_values["name_of_stations"] == ["’Station1’"]
        assert dict_values["number_of_events"] == "1"
        assert dict_values["observation_timestep"] == "10800"
        assert dict_values["first_recorded_event"] == "1996 1 1 0 0 0 1 3 0 0"
        assert dict_values["precipitation_per_timestep"] == ["0.2","0.2","0.2","0.2","0.2","0.2","0.2","0.2","0.2",]


class TestSerializer:
    pass