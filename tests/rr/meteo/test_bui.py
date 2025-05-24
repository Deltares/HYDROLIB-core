import inspect
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from hydrolib.core.base.model import ModelSaveSettings, SerializerConfig
from hydrolib.core.rr.meteo.models import BuiModel, BuiPrecipitationEvent
from hydrolib.core.rr.meteo.parser import BuiEventListParser, BuiEventParser, BuiParser
from hydrolib.core.rr.meteo.serializer import (
    BuiEventSerializer,
    BuiSerializer,
    write_bui_file,
)
from tests.utils import test_input_dir, test_output_dir


class BuiTestData:
    """
    Wrapper class to contain all the test data that can be used
    within the test modules to validate bui data.
    """

    @staticmethod
    def default_bui_file() -> Path:
        """
        Gets a default bui file path (which is used in the default_bui_model).
        Wrapped in a method to avoid pytest failing to discover tests.

        Returns:
            Path: File location of the default.bui
        """
        default_path = test_input_dir / "rr_sample_trimmed" / "rr" / "default.bui"
        assert default_path.is_file(), "Test file not found."
        return default_path

    @staticmethod
    def default_bui_station() -> str:
        """Just a wrapper to return the default value for the default station name"""
        return "Station1"

    @staticmethod
    def bui_model() -> BuiModel:
        """
        Gets a well-tested basic BuiModel.
        Wrapped in a method to avoid pytest failing to discover tests
        in case some code has been changed.

        Returns:
            BuiModel: Default bui model.
        """
        event_list = [
            BuiPrecipitationEvent(
                start_time=datetime(1996, 1, 1),  # "1996 1 1 0 0 0 1 3 0 0"
                timeseries_length=timedelta(1, 10800),
                precipitation_per_timestep=[[0.2]] * 9,
            )
        ]

        return BuiModel(
            filepath=BuiTestData.default_bui_file(),
            default_dataset="1",
            number_of_stations=1,
            name_of_stations=[BuiTestData.default_bui_station()],
            number_of_events=1,
            seconds_per_timestep=10800,
            precipitation_events=event_list,
        )


class TestModel:
    """
    Test class pointing to hydrolib.core.rr.meteo.models to test
    all its classes and methods.
    """

    class TestRksModel:
        """
        Acceptance tests to verify we can load .rks files, which contain
        more than one precipitation event.
        """

        def test_given_nwrw_file_loads_model(self):
            test_file = test_input_dir / "rr_bui_rks" / "nwrw.RKS"
            assert test_file.is_file()
            model = BuiModel(filepath=test_file)
            event_list = model.precipitation_events
            assert len(event_list) == 404
            station_events = model.get_station_events("De Bilt")
            first_event = station_events[datetime(1955, 1, 15, 16, 45)]
            assert first_event[0] == pytest.approx(0.30)
            assert first_event[-1] == pytest.approx(0)
            last_event = station_events[datetime(1979, 12, 29, 7)]
            assert last_event[0] == pytest.approx(0.14)
            assert last_event[-1] == pytest.approx(0.03)

        def test_given_t_sewer_file_loads_model(self):
            test_file = test_input_dir / "rr_bui_rks" / "T_SEWER.rks"
            assert test_file.is_file()
            model = BuiModel(filepath=test_file)
            event_list = model.precipitation_events
            assert len(event_list) == 10
            station_events = model.get_station_events("De Bilt")
            first_event = station_events[datetime(2000, 1, 10)]
            assert first_event[0] == pytest.approx(0.30)
            assert first_event[-1] == 0
            last_event = station_events[datetime(2000, 12, 9)]
            assert last_event[0] == pytest.approx(0.15)
            assert last_event[-1] == 0

    class TestBuiModel:
        """
        Test class pointing to hydrolib.core.rr.meteo.models to test
        all the methods in the BuiModel class.
        """

        def test_given_bui_file_loads_model(self):
            test_file = test_input_dir / "rr_individual_files" / "DEFAULT_rr.BUI"
            expected_number_of_events = 1
            expected_number_of_stations = 7
            expected_timeseries_length = 168

            assert test_file.is_file()
            model = BuiModel(filepath=test_file)
            event_list = model.precipitation_events

            assert len(event_list) == expected_number_of_events
            assert model.number_of_events == expected_number_of_events

            assert len(model.name_of_stations) == expected_number_of_stations
            assert model.number_of_stations == expected_number_of_stations

            assert event_list[0].start_time == datetime(2021, 4, 20, 7, 0)
            assert model.precipitation_events[0].timeseries_length == timedelta(days=7)
            assert (
                len(event_list[0].precipitation_per_timestep)
                == expected_timeseries_length
            )

            assert model.name_of_stations == [
                "De Bilt",
                "Cabauw",
                "Den Helder",
                "Texelhors",
                "Berkhout",
                "IJmuiden",
                "Wijk aan Zee",
            ]

        def test_given_filepath_all_properties_loaded(self):
            test_file = BuiTestData.default_bui_file()
            model = BuiModel(filepath=test_file)
            assert model == BuiTestData.bui_model()
            assert model.filepath == test_file

        def test_save_default_verify_expected_text(self):
            # 1. Define test data.
            default_bui_model = BuiTestData.bui_model()
            expected_text = inspect.cleandoc(
                """
                *Name of this file: {}
                *Date and time of construction: 15-10-21 14:48:13
                *Comments are following an * (asterisk) and written above variables
                1
                *Number of stations
                1
                *Station Name
                'Station1'
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
                0.2
                0.2
                0.2
                0.2
                0.2
            """
            )

            # 2. Save file and read its content.
            save_path = (
                test_output_dir
                / self.test_save_default_verify_expected_text.__name__
                / BuiModel._generate_name()
            )

            default_bui_model.save(save_path, recurse=True)
            assert save_path.is_file()
            text_read = save_path.read_text(encoding="utf8")

            # 3. Verify texts are equal.
            lines_read = text_read.splitlines()
            expected_lines = expected_text.format(save_path).splitlines()
            # Remove the second line of the text as the datetime might differ (even by seconds)
            build_datetime_line = lines_read.pop(1)
            expected_lines.pop(1)
            # But still verify they start the same way.
            assert build_datetime_line.startswith("*Date and time of construction: ")
            assert lines_read == expected_lines

        def test_save_default_and_load_returns_same_model(self):
            default_bui_model = BuiTestData.bui_model()

            save_path = (
                test_output_dir
                / self.test_save_default_and_load_returns_same_model.__name__
                / BuiModel._generate_name()
            )

            default_bui_model.save(filepath=save_path, recurse=True)
            assert save_path.is_file()

            new_model = BuiModel(save_path)
            assert default_bui_model == new_model

            def filtered_dict(input_dict: dict) -> dict:
                return {k: v for k, v in input_dict.items() if k != "filepath"}

            assert filtered_dict(default_bui_model.dict()) == filtered_dict(
                new_model.dict()
            )

        def test_get_station_events_given_valid_station(self):
            default_bui_model = BuiTestData.bui_model()
            station_name = BuiTestData.default_bui_station()
            station_events = default_bui_model.get_station_events(station_name)
            assert len(station_events.items()) == 1
            event_found = list(station_events.items())[0]
            assert event_found[0] == datetime(1996, 1, 1)
            assert event_found[1] == [0.2] * 9

        def test_get_station_events_given_invalid_station_raises(self):
            station_name = "Not a Station"
            with pytest.raises(ValueError) as exc:
                BuiTestData.bui_model().get_station_events(station_name)
            assert str(exc.value) == f"Station {station_name} not found BuiModel."

    class TestBuiPrecipitationEvent:
        """
        Test class pointing to hydrolib.core.rr.meteo.models to test
        all the methods in the BuiPrecipitationEvent class.
        """

        def test_get_station_precipitations_given_valid_station(self):
            default_bui_model = BuiTestData.bui_model()
            precipitation_event = default_bui_model.precipitation_events[0]
            start_time, precipitations = precipitation_event.get_station_precipitations(
                0
            )
            assert start_time == datetime(1996, 1, 1)
            assert precipitations == [0.2] * 9

        def test_get_station_precipitations_given_invalid_station_raises(self):
            default_bui_model = BuiTestData.bui_model()
            precipitation_event = default_bui_model.precipitation_events[0]
            with pytest.raises(ValueError) as exc:
                precipitation_event.get_station_precipitations(42)
            assert str(exc.value) == "Station index not found, number of stations: 1"


class TestParser:
    """
    Test class pointing to hydrolib.core.rr.meteo.parser to test
    all its classes and methods.
    """

    class TestBuiParser:
        """
        Test class pointing to hydrolib.core.rr.meteo.parser to test
        all the methods in the BuiParser class.
        """

        def test_given_valid_file_parses_values(self):
            # 1. Define initial data.
            test_file = BuiTestData.default_bui_file()

            # 2. Run test.
            dict_values = BuiParser.parse(test_file)

            # 3. Verify final expectations.
            default_bui_model = BuiTestData.bui_model()
            assert dict_values is not None
            assert dict_values["default_dataset"] == str(
                default_bui_model.default_dataset
            )
            assert dict_values["number_of_stations"] == str(
                default_bui_model.number_of_stations
            )
            assert dict_values["name_of_stations"] == default_bui_model.name_of_stations
            assert dict_values["number_of_events"] == default_bui_model.number_of_events
            assert (
                dict_values["seconds_per_timestep"]
                == default_bui_model.seconds_per_timestep
            )
            precipitation_event = dict_values["precipitation_events"][0]
            default_event = default_bui_model.precipitation_events[0]
            assert precipitation_event["start_time"] == default_event.start_time
            assert (
                precipitation_event["timeseries_length"]
                == default_event.timeseries_length
            )
            assert precipitation_event["precipitation_per_timestep"] == [
                list(map(str, v)) for v in default_event.precipitation_per_timestep
            ]

    class TestBuiEventParser:
        """
        Test class pointing to hydrolib.core.rr.meteo.parser to test
        all the methods in the BuiEventParser class.
        """

        def test_given_valid_text(self):
            raw_text = inspect.cleandoc(
                """
                2021 12 20 0 0 0 1 0 4 20
                4.2
                4.2
            """
            )
            parsed_dict = BuiEventParser.parse(raw_text)
            assert parsed_dict["start_time"] == datetime(2021, 12, 20)
            assert parsed_dict["timeseries_length"] == timedelta(
                days=1, minutes=4, seconds=20
            )
            assert parsed_dict["precipitation_per_timestep"] == [["4.2"], ["4.2"]]

        def test_given_multiple_stations(self):
            raw_text = inspect.cleandoc(
                """
                2021 12 20 0 0 0 1 0 4 20
                4.2 2.4
                4.2 2.4
            """
            )
            parsed_dict = BuiEventParser.parse(raw_text)
            assert parsed_dict["start_time"] == datetime(2021, 12, 20)
            assert parsed_dict["timeseries_length"] == timedelta(
                days=1, minutes=4, seconds=20
            )
            assert parsed_dict["precipitation_per_timestep"] == [
                ["4.2", "2.4"],
                ["4.2", "2.4"],
            ]

        def test_parse_event_time_reference(self):
            raw_text = "2021 12 20 0 0 0 0 0 2 0"
            parsed_dict = BuiEventParser.parse_event_time_reference(raw_text)
            assert parsed_dict["start_time"] == datetime(2021, 12, 20)
            assert parsed_dict["timeseries_length"] == timedelta(minutes=2)

    class TestBuiEventListParser:
        """
        Test class pointing to hydrolib.core.rr.meteo.parser to test
        all the methods in the BuiEventListParser class.
        """

        def test_given_single_event(self):
            raw_text = inspect.cleandoc(
                """
                2021 12 20 0 0 0 0 0 2 00
                4.2
                4.2
            """
            )
            parsed_list = BuiEventListParser.parse(raw_text, 1, 60)
            assert len(parsed_list) == 1
            parsed_event = parsed_list[0]
            assert parsed_event["start_time"] == datetime(2021, 12, 20)
            assert parsed_event["timeseries_length"] == timedelta(seconds=120)
            assert parsed_event["precipitation_per_timestep"] == [["4.2"], ["4.2"]]

        def test_given_mulitple_events(self):
            # 1. Define test data.
            number_of_events = 2
            timestep = 60  # 60 seconds timestep.
            # The first event has 2 minutes timestep = 2 precipitations
            first_event_text = inspect.cleandoc(
                """
            2021 12 20 0 0 0 0 0 2 0
            4.2
            4.2"""
            )
            # The second event has 3 minutes timestep = 2 precipitations
            second_event_text = inspect.cleandoc(
                """
            2021 12 20 0 0 0 0 0 3 0
            2.4
            2.4
            2.4"""
            )
            raw_text = inspect.cleandoc(
                f"""
                {first_event_text}
                {second_event_text}"""
            )

            # 2. Run test.
            parsed_list = BuiEventListParser.parse(raw_text, number_of_events, timestep)

            # 3. Verify final expectations.
            assert len(parsed_list) == 2

            # Evaluate first event.
            first_event = parsed_list[0]
            assert first_event["start_time"] == datetime(2021, 12, 20)
            assert first_event["timeseries_length"] == timedelta(minutes=2)
            assert first_event["precipitation_per_timestep"] == [["4.2"], ["4.2"]]
            # Evaluate second event.
            second_event = parsed_list[1]
            assert second_event["start_time"] == datetime(2021, 12, 20)
            assert second_event["timeseries_length"] == timedelta(minutes=3)
            assert second_event["precipitation_per_timestep"] == [
                ["2.4"],
                ["2.4"],
                ["2.4"],
            ]


class TestSerializer:
    """
    Test class pointing to hydrolib.core.rr.meteo.serializer to test
    all its classes and methods.
    """

    class TestBuiSerializer:
        """
        Test class pointing to hydrolib.core.rr.meteo.serializer to test
        all the methods in the BuiSerializer class.
        """

        def test_given_dict_serialize_into_text(self):
            # 1. Define test data.
            dict_values = dict(
                filepath="my/custom/path",
                default_dataset="1",
                number_of_stations="1",
                name_of_stations=[BuiTestData.default_bui_station()],
                number_of_events="1",
                seconds_per_timestep=10800,
                precipitation_events=[
                    dict(
                        start_time=datetime(1996, 1, 1),
                        timeseries_length=timedelta(1, 10800),
                        precipitation_per_timestep=[
                            [0.2],
                            [0.2],
                            [0.2],
                            [0.2],
                        ],
                    )
                ],
            )
            # Define expected datetime (it could fail by a second in a rare occasion)
            expected_datetime = datetime.now().strftime("%d-%m-%y %H:%M:%S")

            # 2. Do test.
            config = SerializerConfig(float_format=".2f")
            serialized_text = BuiSerializer.serialize(dict_values, config)

            # 3. Verify expectations.
            expected_serialized = inspect.cleandoc(
                """
                *Name of this file: my/custom/path
                *Date and time of construction: {}
                *Comments are following an * (asterisk) and written above variables
                1
                *Number of stations
                1
                *Station Name
                'Station1'
                *Number_of_events seconds_per_timestamp
                1 10800
                * Event 1 duration days:1 hours:3 minutes:0 seconds:0
                * Start date and time of the event: yyyy mm dd hh mm ss
                * Duration of the event           : dd hh mm ss
                * Rainfall value per time step [mm/time step]
                1996 1 1 0 0 0 1 3 0 0
                0.20
                0.20
                0.20
                0.20
                """.format(
                    expected_datetime
                )
            )
            assert serialized_text == expected_serialized

        def test_given_station_ids_serialize_into_text(self):
            stations_ids = ["Hello", "World", BuiTestData.default_bui_station()]
            serialized_text = BuiSerializer.serialize_stations_ids(stations_ids)
            assert serialized_text == "'Hello'\n'World'\n'Station1'"

        def test_given_precipitation_serialize_into_text(self):
            precipitation_per_timestep = [[1.23], [2.34], [3.45], [4.56]]
            config = SerializerConfig(float_format=".1f")
            serialized_text = BuiEventSerializer.serialize_precipitation_per_timestep(
                precipitation_per_timestep, config
            )
            assert serialized_text == "1.2\n2.3\n3.5\n4.6"

        def test_given_start_time_serialize_into_text(self):
            first_event = datetime(2021, 12, 20, 0, 42, 24)
            expected_string = "2021 12 20 0 42 24"
            serialized_text = BuiEventSerializer.serialize_start_time(first_event)
            assert serialized_text == expected_string

        def test_given_timeseries_length_serialize_into_text(self):
            timeseries_length = timedelta(4, 2000)
            expected_string = "4 0 33 20"
            serialized_text = BuiEventSerializer.serialize_timeseries_length(
                timeseries_length
            )
            assert serialized_text == expected_string

        def test_given_multiple_events_serialize_event_list_into_text(self):
            # 1. Define test data.
            event_list_data = [
                dict(
                    start_time=datetime(1996, 1, 1),
                    timeseries_length=timedelta(seconds=120),
                    precipitation_per_timestep=[[0.24]] * 2,
                ),
                dict(
                    start_time=datetime(1996, 1, 1),
                    timeseries_length=timedelta(seconds=180),
                    precipitation_per_timestep=[[0.42]] * 3,
                ),
            ]

            # 2. Do test.
            config = SerializerConfig(float_format=".3f")
            serialized_text = BuiSerializer.serialize_event_list(
                event_list_data, config
            )

            # 3. Verify final expectations.
            expected_string = inspect.cleandoc(
                """
                * Event 1 duration days:0 hours:0 minutes:2 seconds:0
                * Start date and time of the event: yyyy mm dd hh mm ss
                * Duration of the event           : dd hh mm ss
                * Rainfall value per time step [mm/time step]
                1996 1 1 0 0 0 0 0 2 0
                0.240
                0.240
                * Event 2 duration days:0 hours:0 minutes:3 seconds:0
                * Start date and time of the event: yyyy mm dd hh mm ss
                * Duration of the event           : dd hh mm ss
                * Rainfall value per time step [mm/time step]
                1996 1 1 0 0 0 0 0 3 0
                0.420
                0.420
                0.420
            """
            )
            assert serialized_text == expected_string

    class TestBuiEventSerializer:
        """
        Test class pointing to hydrolib.core.rr.meteo.serializer to test
        all the methods in the BuiEventSerializer class.
        """

        def test_given_dict_serialize_into_text(self):
            precipitation_event_list = dict(
                start_time=datetime(1996, 1, 1),
                timeseries_length=timedelta(1, 10800),
                precipitation_per_timestep=[
                    [0.2],
                    [0.2],
                    [0.2],
                    [0.2],
                ],
            )
            config = SerializerConfig(float_format=".2f")
            serialized_text = BuiEventSerializer.serialize(
                precipitation_event_list, config
            )
            expected_string = inspect.cleandoc(
                """
                * Event 1 duration days:1 hours:3 minutes:0 seconds:0
                * Start date and time of the event: yyyy mm dd hh mm ss
                * Duration of the event           : dd hh mm ss
                * Rainfall value per time step [mm/time step]
                1996 1 1 0 0 0 1 3 0 0
                0.20
                0.20
                0.20
                0.20
            """
            )
            assert serialized_text == expected_string

        def test_given_duration_get_timedelta_fields(self):
            duration = timedelta(days=4, hours=2, minutes=2, seconds=4)
            dict_duration = BuiEventSerializer.get_timedelta_fields(duration)
            assert dict_duration["d_seconds"] == 4
            assert dict_duration["d_minutes"] == 2
            assert dict_duration["d_hours"] == 2
            assert dict_duration["d_days"] == 4

        def test_given_datetime_serialize_start_time(self):
            starttime = datetime(2021, 12, 20, 4, 2, 24)
            serialized_st = BuiEventSerializer.serialize_start_time(starttime)
            expected_string = "2021 12 20 4 2 24"
            assert serialized_st == expected_string

        def test_given_timedelta_serialize_timeseries_length(self):
            duration = timedelta(days=4, hours=2, minutes=2, seconds=4)
            serialized_td = BuiEventSerializer.serialize_timeseries_length(duration)
            expected_string = "4 2 2 4"
            assert serialized_td == expected_string

        def test_given_precipitationlist_serialize_precipitation_per_timestep(self):
            precipitation_list = [[2.4]] * 4
            config = SerializerConfig(float_format=".2f")
            serialzied_pl = BuiEventSerializer.serialize_precipitation_per_timestep(
                precipitation_list, config
            )
            expected_string = "2.40\n2.40\n2.40\n2.40"
            assert serialzied_pl == expected_string

    def test_write_bui_file_given_valid_file(self):
        default_bui_model = BuiTestData.bui_model()
        new_path = test_output_dir / "new_path.bui"
        write_bui_file(
            new_path,
            default_bui_model.dict(),
            config=SerializerConfig(),
            save_settings=ModelSaveSettings(),
        )
        assert new_path.is_file()
        written_text = new_path.read_text(encoding="utf8")
        assert str(new_path) in written_text
        assert str(default_bui_model.filepath) not in written_text
        new_path.unlink()
