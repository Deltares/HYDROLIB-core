import pytest
from typing import List
from pathlib import Path


@pytest.fixture
def initial_condition_quantities() -> List[str]:
    return [
        "initialwaterlevel", "initialsalinity", "initialsalinitytop", "initialtemperature",
        "initialverticaltemperatureprofile", "initialverticalsalinityprofile", "initialvelocityx",
        "initialvelocityy", "initialvelocity", "initialsalinitytopuse"
    ]


@pytest.fixture
def initial_condition_interpolation_methods() -> List[str]:
    return ["constant", "averaging", "triangulation", "Possible values: const (only with dataFileType = polygon)."]


@pytest.fixture
def initial_condition_file_type() -> List[str]:
    return ["arcinfo", "GeoTIFF", "sample", "1dField", "polygon", "Possible values: arcinfo, GeoTIFF, sample, 1dField, polygon."]


@pytest.fixture
def meteo_forcing_file_type() -> List[str]:
    return [
        "bcAscii", "uniform", "uniMagDir", "meteoGridEqui", "spiderweb", "meteoGridCurvi", "netcdf",
        "Possible values: bcAscii, netcdf, uniform."
    ]


@pytest.fixture
def meteo_interpolation_methods() -> List[str]:
    return ["nearestNb", "linearSpaceTime", "Possible values: nearestNb (only with station data in forcingFileType=netcdf ). "]


@pytest.fixture
def input_files_dir() -> Path:
    return Path("tests/data/input")


@pytest.fixture
def time_series_file(input_files_dir: Path) -> Path:    return input_files_dir.joinpath("tim/single_data_for_timeseries.tim")

@pytest.fixture
def boundary_condition_file(input_files_dir: Path) -> Path:
    return input_files_dir.joinpath("dflowfm_individual_files/FlowFM_boundaryconditions2d_and_vectors.bc")

