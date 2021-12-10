import inspect
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List


class BuiEventSerializer:
    """
    Serializer class to transform a bui event into a text block.
    """

    bui_event_template = inspect.cleandoc(
        """
        * Event {event_idx} duration days:{d_days} hours:{d_hours} minutes:{d_minutes} seconds:{d_seconds}
        * Start date and time of the event: yyyy mm dd hh mm ss
        * Duration of the event           : dd hh mm ss
        * Rainfall value per time step [mm/time step]
        {start_time} {timeseries_length}
        {precipitation_per_timestep}
    """
    )

    @staticmethod
    def serialize(event_data: Dict) -> str:
        """
        Serializes a dictionary representing an event into a text block.

        Args:
            event_data (Dict): Dictionary representing precipitation event.

        Returns:
            str: Formatted string.
        """
        event_data["start_time"] = BuiEventSerializer.serialize_start_time(
            event_data["start_time"]
        )
        ts_duration = event_data["timeseries_length"]
        event_data = {
            **event_data,
            **BuiEventSerializer.get_timedelta_fields(ts_duration),
        }
        event_data[
            "timeseries_length"
        ] = BuiEventSerializer.serialize_timeseries_length(
            event_data["timeseries_length"]
        )
        event_data[
            "precipitation_per_timestep"
        ] = BuiEventSerializer.serialize_precipitation_per_timestep(
            event_data["precipitation_per_timestep"]
        )
        if "event_idx" not in event_data.keys():
            event_data["event_idx"] = 1
        return BuiEventSerializer.bui_event_template.format(**event_data)

    @staticmethod
    def get_timedelta_fields(duration: timedelta) -> Dict:
        """
        Gets a dictionary containing the time delta in days, hours, minutes and seconds.
        This means that the seconds field does not contain the accumulative value of days
        hours and minutes.

        Args:
            duration (timedelta): Timedelta to convert.

        Returns:
            Dict: Dictionary containing all fields.
        """
        total_hours = int(duration.seconds / (60 * 60))
        total_minutes = int((duration.seconds / 60) - (total_hours * 60))
        total_seconds = int(
            duration.seconds - ((total_hours * 60 + total_minutes) * 60)
        )
        return dict(
            d_seconds=total_seconds,
            d_minutes=total_minutes,
            d_hours=total_hours,
            d_days=duration.days,
        )

    @staticmethod
    def serialize_start_time(data_to_serialize: datetime) -> str:
        """
        Serializes a datetime into the expected .bui format.

        Args:
            data_to_serialize (datetime): Datetime representing reference time.

        Returns:
            str: Converted datetime into string.
        """
        # Not using the following format because we only want one digit instead of
        # double (day 1 -> 1, instead of 01).
        # data_to_serialize.strftime("%Y %m %d %H %M %S")
        dt = data_to_serialize
        return f"{dt.year} {dt.month} {dt.day} {dt.hour} {dt.minute} {dt.second}"

    @staticmethod
    def serialize_timeseries_length(data_to_serialize: timedelta) -> str:
        """
        Serializes a given timedelta into the .bui format.

        Args:
            data_to_serialize (timedelta): Reference timespan to serialize.

        Returns:
            str: Converted timedelta in string.
        """
        fields_dict = BuiEventSerializer.get_timedelta_fields(data_to_serialize)
        total_hours = fields_dict["d_hours"]
        total_minutes = fields_dict["d_minutes"]
        total_seconds = fields_dict["d_seconds"]
        return f"{data_to_serialize.days} {total_hours} {total_minutes} {total_seconds}"

    @staticmethod
    def serialize_precipitation_per_timestep(data_to_serialize: List[List[str]]) -> str:
        """
        Serialized the data containing all the precipitations per timestep (and station)
        into a single string ready to be mapped.

        Args:
            data_to_serialize (List[List[str]]): Data to be mapped.

        Returns:
            str: Serialized string in .bui format.
        """
        serialized_data = str.join(
            "\n",
            [str.join(" ", map(str, listed_data)) for listed_data in data_to_serialize],
        )
        return serialized_data


class BuiSerializer:
    """
    Serializer class to transform an object into a .bui file text format.
    """

    bui_template = inspect.cleandoc(
        """
        *Name of this file: {filepath}
        *Date and time of construction: {datetime_now}
        *Comments are following an * (asterisk) and written above variables
        {default_dataset}
        *Number of stations
        {number_of_stations}
        *Station Name
        {name_of_stations}
        *Number_of_events seconds_per_timestamp
        {number_of_events} {seconds_per_timestep}
        {precipitation_events}
        """
    )

    @staticmethod
    def serialize(bui_data: Dict) -> str:
        """
        Formats the bui_template with the content of the given data.
        NOTE: It requires that caller injects file_path into bui_data prior to this call.
        Otherwise it will crash.

        Args:
            bui_data (Dict): Data to serialize.
        """
        bui_data["datetime_now"] = datetime.now().strftime("%d-%m-%y %H:%M:%S")
        bui_data["name_of_stations"] = BuiSerializer.serialize_stations_ids(
            bui_data["name_of_stations"]
        )
        bui_data["precipitation_events"] = BuiSerializer.serialize_event_list(
            bui_data["precipitation_events"]
        )
        return BuiSerializer.bui_template.format(**bui_data)

    @staticmethod
    def serialize_event_list(data_to_serialize: List[Dict]) -> str:
        """
        Serializes a event list dictionary into a single text block.

        Args:
            data_to_serialize (Dict): Dictionary containing list of events.

        Returns:
            str: Text block representing all precipitation events.
        """
        serialized_list = []
        for n_event, event in enumerate(data_to_serialize):
            event["event_idx"] = n_event + 1
            serialized_list.append(BuiEventSerializer.serialize(event))
        return "\n".join(serialized_list)

    @staticmethod
    def serialize_stations_ids(data_to_serialize: List[str]) -> str:
        """
        Serializes the stations ids into a single string as expected in a .bui file.

        Args:
            data_to_serialize (List[str]): List of station ids.

        Returns:
            str: Serialized string.
        """
        return str.join(" ", data_to_serialize)


def write_bui_file(path: Path, data: Dict) -> None:
    """
    Writes a .bui file in the given path based on the data given in a dictionary.

    Args:
        path (Path): Path where to output the text.
        data (Dict): Data to serialize into the file.
    """
    data["filepath"] = path  # This is redundant as already exists in the data.
    serialized_bui_data = BuiSerializer.serialize(data)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialized_bui_data, encoding="utf8")
