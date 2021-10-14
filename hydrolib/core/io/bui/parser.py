from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime, timedelta


class BuiEventParser:
    """
    A parser for the precipitation event section within a .bui file.
    It resembles something like this:
    StartTime (YYYY mm dd HH MM SS) TimeSeriesLength (dd HH MM SS)
    PrecipitationPerTimestep
    Example given:
    2021 12 20 0 0 0 1 0 4 20
    4.2
    4.2
    4.2
    (it should match the timeseries length based on the seconds per timstep.)
    """

    @staticmethod
    def parse(raw_text: str) -> Dict:
        """
        Given text representing a single BuiPrecipitationEvent parses it into a dictionary.

        Args:
            raw_text (str): Text containing a single precipitation event.

        Returns:
            Dict: Mapped contents of the text.
        """
        def get_precipitations_per_ts(line: str) -> List[str]:
            return [prec for prec in line.split()]

        def get_start_time(line: str) -> datetime:
            return datetime.strptime(line, "%Y %m %d %H %M %S")

        def get_timeseries_length(line: str) -> timedelta:
            td = line.split()
            return timedelta(days=int(td[0]), hours=int(td[1]), minutes=int(td[2]), seconds=int(td[3]))

        def get_event_time_reference(line: str) -> Tuple[datetime, timedelta]:
            timeref = line.split()
            start_time = get_start_time(" ".join(timeref[:6]))
            timeseries_length = get_timeseries_length(" ".join(timeref[6:]))
            return (start_time, timeseries_length)

        event_lines = raw_text.splitlines(keepends=False)
        start_time, timeseries_length = get_event_time_reference(event_lines[0])
        return dict(
            start_time=start_time,
            timeseries_length=timeseries_length,
            precipitation_per_timestep=list(map(get_precipitations_per_ts, event_lines[1:]))
        )


class BuiEventListParser:
    @staticmethod
    def parse(raw_text: str) -> Dict:
        """
        Parses a given raw text containing 0 to many text blocks representing a precipitation event.

        Args:
            raw_text (str): Text blocks representing precipitation events.

        Returns:
            Dict: resulting mapping ready to be parsed into BuiPrecipitationEventList.
        """
        return dict(
            precipitation_event_list=[BuiEventParser.parse(raw_text)]
        )


class BuiParser:
    """
    A parser for .bui files which are like this:
    * comments
    Dataset type to use (always 1).
    * comments
    Number of stations.
    * comments
    Name of stations
    * comments
    Number of events Number of seconds per timestep.
    * comments
    First datetime reference.
    Precipitation per timestep per station.
    """
    @staticmethod
    def parse(filepath: Path) -> Dict:
        """
        Parses a given file, in case valid, into a dictionary which can later be mapped
        to the BuiModel.

        Args:
            filepath (Path): Path to file containing the data to parse.

        Returns:
            Dict: Parsed values.
        """
        def get_station_ids(line: str) -> List[str]:
            return [s_id for s_id in line.split(",")]

        bui_lines = [
            line
            for line in filepath.read_text(encoding="utf8").splitlines()
            if not line.startswith("*")]

        n_events_and_timestep = bui_lines[3].split()

        return dict(
            default_dataset=bui_lines[0],
            number_of_stations=bui_lines[1],
            name_of_stations=get_station_ids(bui_lines[2]),
            number_of_events=n_events_and_timestep[0],
            seconds_per_timestep=n_events_and_timestep[1],
            precipitation_events=BuiEventListParser.parse("\n".join(bui_lines[4:]))
        )
