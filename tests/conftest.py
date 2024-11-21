from pathlib import Path
from typing import List, Dict

import pytest


@pytest.fixture
def initial_condition_quantities() -> List[str]:
    return [
        "initialwaterlevel",
        "initialsalinity",
        "initialsalinitytop",
        "initialtemperature",
        "initialverticaltemperatureprofile",
        "initialverticalsalinityprofile",
        "initialvelocityx",
        "initialvelocityy",
        "initialvelocity",
        "initialsalinitytopuse",
    ]


@pytest.fixture
def initial_condition_interpolation_methods() -> List[str]:
    return [
        "constant",
        "averaging",
        "triangulation",
        "Possible values: constant, triangulation, averaging.",
    ]


@pytest.fixture
def initial_condition_file_type() -> List[str]:
    return [
        "arcinfo",
        "GeoTIFF",
        "sample",
        "1dField",
        "polygon",
        "Possible values: arcinfo, GeoTIFF, sample, 1dField, polygon.",
    ]


@pytest.fixture
def meteo_forcing_file_type() -> List[str]:
    return [
        "bcAscii",
        "uniform",
        "uniMagDir",
        "meteoGridEqui",
        "spiderweb",
        "meteoGridCurvi",
        "netcdf",
        "Possible values: bcAscii, netcdf, uniform.",
    ]


@pytest.fixture
def meteo_interpolation_methods() -> List[str]:
    return [
        "nearestNb",
        "linearSpaceTime",
        "Possible values: nearestNb (only with station data in forcingFileType=netcdf ). ",
    ]


@pytest.fixture
def initial_cond_averaging_type() -> List[str]:
    return [
        "mean",
        "nearestNb",
        "max",
        "min",
        "invDist",
        "minAbs",
        "median",
        "Possible values: mean, nearestNb, max, min, invDist, minAbs.",
    ]


@pytest.fixture
def input_files_dir() -> Path:
    return Path("tests/data/input")


@pytest.fixture
def time_series_file(input_files_dir: Path) -> Path:
    return input_files_dir.joinpath("tim/single_data_for_timeseries.tim")


@pytest.fixture
def boundary_condition_file(input_files_dir: Path) -> Path:
    return input_files_dir.joinpath(
        "dflowfm_individual_files/FlowFM_boundaryconditions2d_and_vectors.bc"
    )


@pytest.fixture
def old_forcing_file() -> Path:
    return Path("tests/data/input/old-external-forcing.ext")


@pytest.fixture(scope="function")
def old_forcing_file_initial_condition() -> Dict[str, Path]:
    return {
        "path": Path("tests/data/input/old-external-forcing-initial-contitions-only.ext"),
        "quantities": ["initialwaterlevel","initialwaterlevel", "initialsalinity"],
        "file_type": ["polygon", "sample", "sample"],
        "file_path": ["iniwaterlevel1.pol", "iniwaterlevel.xyz", "inisalinity.xyz"],

    }


@pytest.fixture
def old_forcing_file_quantities() -> List[str]:
    return [
        "windx",
        "windy",
        "initialwaterlevel",
        "initialwaterlevel",
        "initialsalinity",
        "bedlevel",
        "bedlevel",
        "waterlevelbnd",
        "horizontaleddyviscositycoefficient",
        "horizontaleddyviscositycoefficient",
        "horizontaleddyviscositycoefficient",
        "horizontaleddyviscositycoefficient",
        "salinitybnd",
    ]


@pytest.fixture
def old_forcing_comment_len() -> int:
    return 63
