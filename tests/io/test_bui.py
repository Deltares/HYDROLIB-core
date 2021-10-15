import inspect
import pytest
from datetime import datetime, timedelta
from tests.utils import test_input_dir, test_output_dir
from hydrolib.core.io.bui.parser import BuiEventListParser, BuiParser, BuiEventParser
from hydrolib.core.io.bui.serializer import BuiEventSerializer, BuiSerializer, write_bui_file
from hydrolib.core.io.bui.models import BuiModel, BuiPrecipitationEvent, BuiPrecipitationEventList

def get_default_bui_model() -> BuiModel:
    """
    Gets a well-tested basic BuiModel.
    Wrapped in a method to avoid pytest failing to discover tests
    in case some code has been changed.

    Returns:
        BuiModel: Default bui model.
    """
    event_list = [BuiPrecipitationEvent(
        start_time = datetime(1996, 1, 1), # "1996 1 1 0 0 0 1 3 0 0"
        timeseries_length= timedelta(1, 10800),
        precipitation_per_timestep= [[0.2]]*9,
    )]
    precipitation_list = BuiPrecipitationEventList(
        precipitation_event_list=event_list
    )
    return BuiModel(
        filepath=test_input_dir / "rr_sample_trimmed" / "rr" / "default.bui",
        default_dataset = "1",
        number_of_stations= 1,
        name_of_stations= ["’Station1’"],
        number_of_events= 1,
        seconds_per_timestep = 10800,
        precipitation_events = precipitation_list)

class TestModel:
    """
    Test class pointing to hydrolib.core.io.bui.models to test
    all its classes and methods.
    """

    class TestBuiModel:
        """
        Test class pointing to hydrolib.core.io.bui.models to test
        all the methods in the BuiModel class.
        """

        def test_given_filepath_all_properties_loaded(self):
            test_file = test_input_dir / "rr_sample_trimmed" / "rr" / "default.bui"
            model = BuiModel(filepath=test_file)
            assert model == get_default_bui_model()
            assert model.filepath == test_file

        def test_save_default_and_load_returns_same_model(self):
            default_bui_model = get_default_bui_model()
            save_path = default_bui_model.save(test_output_dir)
            assert save_path.is_file()
            new_model = BuiModel(save_path)
            assert default_bui_model == new_model

            def filtered_dict(input_dict: dict) -> dict:
                return {k:v for k,v in input_dict.items() if k != "filepath"}
            assert filtered_dict(default_bui_model.dict()) == filtered_dict(new_model.dict())

        def test_get_station_events_given_valid_station(self):
            default_bui_model = get_default_bui_model()
            station_name = "’Station1’"
            station_events = default_bui_model.get_station_events(station_name)
            assert len(station_events.items()) == 1
            event_found = list(station_events.items())[0]
            assert event_found[0] == datetime(1996, 1, 1)
            assert event_found[1] == [0.2] * 9
        
        def test_get_station_events_given_invalid_station_raises(self):
            station_name = "Not a Station"
            with pytest.raises(ValueError) as exc:
                get_default_bui_model().get_station_events(station_name)
            assert str(exc.value) == f"Station {station_name} not found BuiModel."

    class TestBuiPrecipitationEvent:
        """
        Test class pointing to hydrolib.core.io.bui.models to test
        all the methods in the BuiPrecipitationEvent class.
        """
        def test_get_station_precipitations_given_valid_station(self):
            default_bui_model = get_default_bui_model()
            precipitation_event = default_bui_model.precipitation_events.precipitation_event_list[0]
            start_time, precipitations = precipitation_event.get_station_precipitations(0)
            assert start_time == datetime(1996, 1, 1)
            assert precipitations == [0.2] * 9
        
        def test_get_station_precipitations_given_invalid_station_raises(self):
            default_bui_model = get_default_bui_model()
            precipitation_event = default_bui_model.precipitation_events.precipitation_event_list[0]
            with pytest.raises(ValueError) as exc:
                precipitation_event.get_station_precipitations(42)
            assert str(exc.value) == "Station index not found, number of stations: 1"

class TestParser:
    """
    Test class pointing to hydrolib.core.io.bui.parser to test
    all its classes and methods.
    """

    class TestBuiParser:
        """
        Test class pointing to hydrolib.core.io.bui.parser to test
        all the methods in the BuiParser class.
        """

        def test_given_valid_file_parses_values(self):
            # 1. Define initial data.
            test_file = test_input_dir / "rr_sample_trimmed" / "rr" / "default.bui"
            assert test_file.is_file(), "Test File not found."

            # 2. Run test.
            dict_values = BuiParser.parse(test_file)

            # 3. Verify final expectations.
            default_bui_model = get_default_bui_model()
            assert dict_values is not None
            assert dict_values["default_dataset"] == str(default_bui_model.default_dataset)
            assert dict_values["number_of_stations"] == str(default_bui_model.number_of_stations)
            assert dict_values["name_of_stations"] == default_bui_model.name_of_stations
            assert dict_values["number_of_events"] == default_bui_model.number_of_events
            assert dict_values["seconds_per_timestep"] == default_bui_model.seconds_per_timestep
            precipitation_event = dict_values["precipitation_events"]["precipitation_event_list"][0]
            default_event = default_bui_model.precipitation_events.precipitation_event_list[0]
            assert precipitation_event["start_time"] == default_event.start_time
            assert precipitation_event["timeseries_length"] == default_event.timeseries_length
            assert precipitation_event["precipitation_per_timestep"] == [list(map(str, v)) for v in default_event.precipitation_per_timestep]

    class TestBuiEventParser:
        """
        Test class pointing to hydrolib.core.io.bui.parser to test
        all the methods in the BuiEventParser class.
        """

        def test_given_valid_text(self):
            raw_text = inspect.cleandoc("""
                2021 12 20 0 0 0 1 0 4 20
                4.2
                4.2
            """)
            parsed_dict = BuiEventParser.parse(raw_text)
            assert parsed_dict["start_time"] == datetime(2021, 12, 20)
            assert parsed_dict["timeseries_length"] == timedelta(days=1, minutes=4, seconds=20)
            assert parsed_dict["precipitation_per_timestep"] == [["4.2"], ["4.2"]]

        def test_given_multiple_stations(self):
            raw_text = inspect.cleandoc("""
                2021 12 20 0 0 0 1 0 4 20
                4.2 2.4
                4.2 2.4
            """)
            parsed_dict = BuiEventParser.parse(raw_text)
            assert parsed_dict["start_time"] == datetime(2021, 12, 20)
            assert parsed_dict["timeseries_length"] == timedelta(days=1, minutes=4, seconds=20)
            assert parsed_dict["precipitation_per_timestep"] == [["4.2", "2.4"], ["4.2", "2.4"]]

        def test_parse_event_time_reference(self):
            raw_text = "2021 12 20 0 0 0 0 0 2 0"
            parsed_dict = BuiEventParser.parse_event_time_reference(raw_text)
            assert parsed_dict["start_time"] == datetime(2021, 12, 20)
            assert parsed_dict["timeseries_length"] == timedelta(minutes=2)

    class TestBuiEventListParser:
        """
        Test class pointing to hydrolib.core.io.bui.parser to test
        all the methods in the BuiEventListParser class.
        """

        def test_given_single_event(self):
            raw_text = inspect.cleandoc("""
                2021 12 20 0 0 0 0 0 2 00
                4.2
                4.2
            """)
            parsed_dict = BuiEventListParser.parse(raw_text, 1, 60)
            assert len(parsed_dict["precipitation_event_list"]) == 1
            parsed_event = parsed_dict["precipitation_event_list"][0]
            assert parsed_event["start_time"] == datetime(2021, 12, 20)
            assert parsed_event["timeseries_length"] == timedelta(seconds=120)
            assert parsed_event["precipitation_per_timestep"] == [["4.2"], ["4.2"]]

        def test_given_mulitple_events(self):
            # 1. Define test data.
            number_of_events = 2
            timestep = 60 # 60 seconds timestep.
            # The first event has 2 minutes timestep = 2 precipitations
            first_event_text = inspect.cleandoc("""
            2021 12 20 0 0 0 0 0 2 0
            4.2
            4.2""")
            # The second event has 3 minutes timestep = 2 precipitations
            second_event_text = inspect.cleandoc("""
            2021 12 20 0 0 0 0 0 3 0
            2.4
            2.4
            2.4""")
            raw_text = inspect.cleandoc(f"""
                {first_event_text}
                {second_event_text}""")

            # 2. Run test.
            parsed_dict = BuiEventListParser.parse(raw_text, number_of_events, timestep)

            # 3. Verify final expectations.
            assert len(parsed_dict["precipitation_event_list"]) == 2

            # Evaluate first event.
            first_event = parsed_dict["precipitation_event_list"][0]
            assert first_event["start_time"] == datetime(2021, 12, 20)
            assert first_event["timeseries_length"] == timedelta(minutes=2)
            assert first_event["precipitation_per_timestep"] == [["4.2"], ["4.2"]]
            # Evaluate second event.
            second_event = parsed_dict["precipitation_event_list"][1]
            assert second_event["start_time"] == datetime(2021, 12, 20)
            assert second_event["timeseries_length"] == timedelta(minutes=3)
            assert second_event["precipitation_per_timestep"] == [["2.4"], ["2.4"], ["2.4"]]

class TestSerializer:
    """
    Test class pointing to hydrolib.core.io.bui.serializer to test
    all its classes and methods.
    """

    class TestBuiSerializer:
        """
        Test class pointing to hydrolib.core.io.bui.serializer to test
        all the methods in the BuiSerializer class.
        """

        def test_given_dict_serialize_into_text(self):
            # 1. Define test data.
            dict_values = dict(
                filepath="my/custom/path",
                default_dataset = "1",
                number_of_stations= "1",
                name_of_stations= ["’Station1’"],
                number_of_events= "1",
                seconds_per_timestep= 10800,
                precipitation_events=dict(
                    precipitation_event_list=[
                        dict(
                            start_time= datetime(1996, 1, 1),
                            timeseries_length=timedelta(1, 10800),
                            precipitation_per_timestep= [[0.2],[0.2],[0.2],[0.2],]
                            )
                        ]
                    )
                )
            # Define expected datetime (it could fail by a second in a rare occasion)
            expected_datetime = datetime.now().strftime("%d-%m-%y %H:%M:%S")

            # 2. Do test.
            serialized_text = BuiSerializer.serialize(dict_values)

            # 3. Verify expectations.
            expected_serialized =  inspect.cleandoc("""
                *Name of this file: my/custom/path
                *Date and time of construction: {}
                *Comments are following an * (asterisk) and written above variables
                1
                *Number of stations
                1
                *Station Name
                ’Station1’
                *Number_of_events seconds_per_timestamp
                1 10800
                * Event 1 duration days:1 hours:3 minutes:0 seconds:0
                * Start date and time of the event: yyyy mm dd hh mm ss
                * Duration of the event           : dd hh mm ss
                * Rainfall value per time step [mm/time step]
                1996 1 1 0 0 0 1 3 0 0
                0.2
                0.2
                0.2
                0.2
                """.format(expected_datetime))
            assert serialized_text == expected_serialized

        def test_given_station_ids_serialize_into_text(self):
            stations_ids = ["Hello", "World", "’Station1’"]
            serialized_text = BuiSerializer.serialize_stations_ids(stations_ids)
            assert serialized_text == "Hello World ’Station1’"

        def test_given_precipitation_serialize_into_text(self):
            precipitation_per_timestep= [["0.2"],["0.2"],["0.2"],["0.2"]]
            serialized_text = BuiEventSerializer.serialize_precipitation_per_timestep(precipitation_per_timestep)
            assert serialized_text == "0.2\n0.2\n0.2\n0.2"

        def test_given_start_time_serialize_into_text(self):
            first_event = datetime(2021, 12, 20, 0, 42, 24)
            expected_string = "2021 12 20 0 42 24"
            serialized_text = BuiEventSerializer.serialize_start_time(first_event)
            assert serialized_text == expected_string

        def test_given_timeseries_length_serialize_into_text(self):
            timeseries_length = timedelta(4, 2000)
            expected_string = "4 0 33 20"
            serialized_text = BuiEventSerializer.serialize_timeseries_length(timeseries_length)
            assert serialized_text == expected_string

    class TestBuiEventSerializer:
        """
        Test class pointing to hydrolib.core.io.bui.serializer to test
        all the methods in the BuiEventSerializer class.
        """
        def test_given_dict_serialize_into_text(self):
            precipitation_event_list=dict(
                start_time= datetime(1996, 1, 1),
                timeseries_length=timedelta(1, 10800),
                precipitation_per_timestep= [[0.2],[0.2],[0.2],[0.2],]
                )
            serialized_text = BuiEventSerializer.serialize(precipitation_event_list)
            expected_string = inspect.cleandoc("""
                * Event 1 duration days:1 hours:3 minutes:0 seconds:0
                * Start date and time of the event: yyyy mm dd hh mm ss
                * Duration of the event           : dd hh mm ss
                * Rainfall value per time step [mm/time step]
                1996 1 1 0 0 0 1 3 0 0
                0.2
                0.2
                0.2
                0.2
            """)
            assert serialized_text == expected_string

    def test_write_bui_file_given_valid_file(self):
        default_bui_model = get_default_bui_model()
        new_path = test_output_dir / "new_path.bui"
        write_bui_file(new_path, default_bui_model.dict())
        assert new_path.is_file()
        written_text = new_path.read_text(encoding="utf8")
        assert str(new_path) in written_text
        assert str(default_bui_model.filepath) not in written_text
        new_path.unlink()
