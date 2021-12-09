from datetime import datetime, timedelta
from typing import Callable, Dict, List, Tuple

from hydrolib.core.basemodel import BaseModel, FileModel

from .parser import BuiParser
from .serializer import write_bui_file


class BuiPrecipitationEvent(BaseModel):
    start_time: datetime
    timeseries_length: timedelta
    precipitation_per_timestep: List[List[float]]

    def get_station_precipitations(
        self, station_idx: int
    ) -> Tuple[datetime, List[float]]:
        """
        Returns all the precipitations related to the given station index (column).

        Args:
            station_idx (int): Index of the column which values need to be retrieved.

        Raises:
            ValueError: If the station index does not exist.

        Returns:
            Tuple[datetime, List[float]]: Tuple with the start time and its precipitations.
        """
        number_of_stations = len(self.precipitation_per_timestep[0])
        if station_idx >= number_of_stations:
            raise ValueError(
                "Station index not found, number of stations: {}".format(
                    number_of_stations
                )
            )
        return (
            self.start_time,
            [
                ts_precipitations[station_idx]
                for ts_precipitations in self.precipitation_per_timestep
            ],
        )


class BuiModel(FileModel):
    """
    Model that represents the file structure of a .bui file.
    """

    default_dataset: int = 1  # Default value (always)
    number_of_stations: int
    name_of_stations: List[str]
    number_of_events: int
    seconds_per_timestep: int
    precipitation_events: List[BuiPrecipitationEvent]

    @classmethod
    def _filename(cls):
        return "bui_file"

    @classmethod
    def _ext(cls) -> str:
        return ".bui"

    @classmethod
    def _get_serializer(cls) -> Callable:
        return write_bui_file

    @classmethod
    def _get_parser(cls) -> Callable:
        return BuiParser.parse

    def get_station_events(self, station: str) -> Dict[datetime, List[float]]:
        """
        Returns all the events (start time and precipitations) related to a given station.

        Args:
            station (str): Name of the station to retrieve.

        Raises:
            ValueError: If the station name does not exist in the BuiModel.

        Returns:
            Dict[datetime, List[float]]: Dictionary with the start time and its precipitations.
        """
        if station not in self.name_of_stations:
            raise ValueError("Station {} not found BuiModel.".format(station))
        station_idx = self.name_of_stations.index(station)
        station_events = {}
        for event in self.precipitation_events:
            start_time, precipitations = event.get_station_precipitations(station_idx)
            station_events[start_time] = precipitations
        return station_events
