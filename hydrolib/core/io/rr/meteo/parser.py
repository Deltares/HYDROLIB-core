from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterator, List, Tuple


class BuiEventParser:
    """
    A parser for the precipitation event section within a .bui file.
    It resembles something like this:
    StartTime (YYYY mm dd HH MM SS) TimeSeriesLength (dd HH MM SS)
    PrecipitationPerTimestep
    Example given:
    2021 12 20 0 0 0 1 0 4 20
    4.2 2.4
    4.2 2.4
    4.2 2.4
    (it should match the timeseries length based on the seconds per timstep.)
    Each column of the last three lines represents a station.
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

        event_lines = raw_text.splitlines(keepends=False)
        time_reference = BuiEventParser.parse_event_time_reference(event_lines[0])
        return dict(
            start_time=time_reference["start_time"],
            timeseries_length=time_reference["timeseries_length"],
            precipitation_per_timestep=list(
                map(get_precipitations_per_ts, event_lines[1:])
            ),
        )

    @staticmethod
    def parse_event_time_reference(raw_text: str) -> Dict:
        """
        Parses a single event time reference line containing both the start time
        and the timeseries length into a dictionary.

        Args:
            raw_text (str): Line representing both start time and timeseries length.

        Returns:
            Dict: Resulting dictionary with keys start_time and timeseries_length.
        """

        def get_start_time(line: str) -> datetime:
            return datetime.strptime(line, "%Y %m %d %H %M %S")

        def get_timeseries_length(line: str) -> timedelta:
            time_fields = line.split()
            return timedelta(
                days=int(time_fields[0]),
                hours=int(time_fields[1]),
                minutes=int(time_fields[2]),
                seconds=int(time_fields[3]),
            )

        timeref = raw_text.split()
        return dict(
            start_time=get_start_time(" ".join(timeref[:6])),
            timeseries_length=get_timeseries_length(" ".join(timeref[6:])),
        )


class BuiEventListParser:
    """
    A parser for .bui events which are like this:
    StartTime (YYYY mm dd HH MM SS) TimeSeriesLength (dd HH MM SS)
    PrecipitationPerTimestep
    StartTime (YYYY mm dd HH MM SS) TimeSeriesLength (dd HH MM SS)
    PrecipitationPerTimestep
    Example given:
    2021 12 20 0 0 0 1 0 4 20
    4.2
    4.2
    4.2
    2021 12 21 0 0 0 1 0 4 20
    2.4
    2.4
    2.4
    """

    @staticmethod
    def parse(raw_text: str, n_events: int, timestep: int) -> List[Dict]:
        """
        Parses a given raw text containing 0 to many text blocks representing a precipitation event.

        Args:
            raw_text (str): Text blocks representing precipitation events.
            n_events (int): Number of events contained in the text block.
            timestep (int): Number of seconds conforming a timestep.

        Returns:
            List[Dict]: List containing all the events represented as dictionaries.
        """

        def get_event_timestep_length(raw_line: str) -> int:
            timereference = BuiEventParser.parse_event_time_reference(raw_line)
            ts_length: timedelta = timereference["timeseries_length"]
            return ts_length.total_seconds()

        def get_multiple_events(raw_lines: List[str]) -> Iterator[BuiEventParser]:
            n_line = 0
            while n_line < len(raw_lines):
                ts_seconds = get_event_timestep_length(raw_lines[n_line])
                event_lines = int(ts_seconds / timestep) + 1
                yield BuiEventParser.parse("\n".join(raw_lines[n_line:][:event_lines]))
                n_line += event_lines

        event_list = []
        if n_events == 1:
            event_list.append(BuiEventParser.parse(raw_text))
        elif n_events > 1:
            raw_lines = raw_text.splitlines(keepends=False)
            event_list = list(get_multiple_events(raw_lines))

        return event_list


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

        def parse_events_and_timestep(line: str) -> Tuple[int, int]:
            n_events_timestep = line.split()
            return (int(n_events_timestep[0]), int(n_events_timestep[1]))

        bui_lines = [
            line
            for line in filepath.read_text(encoding="utf8").splitlines()
            if not line.startswith("*")
        ]

        n_events, timestep = parse_events_and_timestep(bui_lines[3])

        return dict(
            default_dataset=bui_lines[0],
            number_of_stations=bui_lines[1],
            name_of_stations=get_station_ids(bui_lines[2]),
            number_of_events=n_events,
            seconds_per_timestep=timestep,
            precipitation_events=BuiEventListParser.parse(
                "\n".join(bui_lines[4:]), n_events, timestep
            ),
        )
