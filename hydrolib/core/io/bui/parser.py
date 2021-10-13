from pathlib import Path
from typing import Dict, List
from datetime import datetime

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

        def get_precipitations_per_ts(line: str) -> List[str]:
            return [prec for prec in line.split()]

        def get_first_recorded_event(line: str) -> datetime:
            # Still not clear what the last three items represent.
            first_recorded = line.split()
            return datetime.strptime("-".join(first_recorded[:6]), "%Y-%m-%d-%H-%M-%S")

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
            first_recorded_event=get_first_recorded_event(bui_lines[4]),
            precipitation_per_timestep=list(map(get_precipitations_per_ts, bui_lines[5:]))
        )
