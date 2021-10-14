from pathlib import Path
from typing import Dict, List
from datetime import datetime, timedelta
import inspect

class BuiSerializer:
    """
    Serializer class to transform an object into a .bui file text format.
    """

    bui_template =  inspect.cleandoc("""
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
        *Start datetime and number of timestamps in the format: yyyy#m#d:#h#m#s:#d#h#m#s
        *Observations per timestamp (row) and per station (column)
        {start_time} {timeseries_length}
        {time_specs}
        """)

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
        bui_data["time_specs"] = BuiSerializer.serialize_precipitation_per_timestep(
            bui_data["precipitation_per_timestep"])
        bui_data["name_of_stations"] = BuiSerializer.serialize_stations_ids(
            bui_data["name_of_stations"]
        )
        bui_data["start_time"] = BuiSerializer.serialize_start_time(
            bui_data["start_time"]
        )
        bui_data["timeseries_length"] = BuiSerializer.serialize_timeseries_length(
            bui_data["timeseries_length"]
        )
        return BuiSerializer.bui_template.format(**bui_data)

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
        total_hours = int(data_to_serialize.seconds / (60 * 60))
        total_minutes = int((data_to_serialize.seconds / 60) - (total_hours * 60 ))
        total_seconds = int(data_to_serialize.seconds - ((total_hours * 60 + total_minutes) * 60))
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
        serialized_data = str.join("\n", [str.join(" ", map(str,listed_data)) for listed_data in data_to_serialize])
        return serialized_data


def write_bui_file(path: Path, data: Dict) -> None:
    """
    Writes a .bui file in the given path based on the data given in a dictionary.

    Args:
        path (Path): Path where to output the text.
        data (Dict): Data to serialize into the file.
    """
    data["filepath"] = path # This is redundant as already exists in the data.
    serialized_bui_data = BuiSerializer.serialize(data)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialized_bui_data, encoding="utf8")
