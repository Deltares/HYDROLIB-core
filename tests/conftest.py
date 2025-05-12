from pathlib import Path
from typing import Any, Dict, List

import pytest

from hydrolib.core.dflowfm.bc.models import (
    QuantityUnitPair,
    TimeInterpolation,
    VerticalInterpolation,
    VerticalPositionType,
)


@pytest.fixture
def input_files_dir() -> Path:
    return Path("tests/data/input")


@pytest.fixture
def output_files_dir() -> Path:
    return Path("tests/data/output")


@pytest.fixture
def reference_files_dir() -> Path:
    return Path("tests/data/reference")


@pytest.fixture
def invalid_data_dir() -> Path:
    return Path("tests/data/input/invalid_files")


@pytest.fixture
def initial_condition_quantities() -> List[str]:
    return [
        "bedlevel",
        "bedlevel1D",
        "bedlevel2D",
        "initialwaterlevel",
        "initialwaterlevel1d",
        "initialwaterlevel2d",
        "initialsalinity",
        "initialsalinitytop",
        "initialsalinitybot",
        "initialverticalsalinityprofile",
        "initialtemperature",
        "initialverticaltemperatureprofile",
        "initialunsaturatedzonethickness",
        "initialvelocityx",
        "initialvelocityy",
        "initialvelocity",
        "initialwaqbot",
    ]


@pytest.fixture
def initial_condition_interpolation_methods() -> List[str]:
    return [
        "constant",
        "averaging",
        "triangulation",
        "linearSpaceTime",
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
        "uniform",
        "netcdf",
        "Possible values: arcinfo, GeoTIFF, sample, 1dField, polygon.",
    ]


@pytest.fixture
def meteo_forcing_file_type() -> List[str]:
    return [
        "bcAscii",
        "uniform",
        "uniMagDir",
        "arcInfo",
        "spiderweb",
        "curviGrid",
        "netcdf",
        "Possible values: bcAscii, uniform, uniMagDir, arcInfo, spiderweb, curviGrid, netcdf.",
    ]


@pytest.fixture
def meteo_interpolation_methods() -> List[str]:
    return [
        "nearestNb",
        "linearSpaceTime",
        "Possible values: nearestNb, linearSpaceTime.",
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
def polylines_dir() -> Path:
    return Path("tests/data/input/dflowfm_individual_files/polylines")


@pytest.fixture
def tim_files_dir() -> Path:
    return Path("tests/data/input/tim")


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
        "path": Path(
            "tests/data/input/old-external-forcing-initial-contitions-only.ext"
        ),
        "quantities": ["initialwaterlevel", "initialwaterlevel", "initialsalinity"],
        "file_type": ["arcinfo", "arcinfo", "arcinfo"],
        "file_path": ["iniwaterlevel1.pol", "iniwaterlevel.xyz", "inisalinity.xyz"],
    }


@pytest.fixture(scope="function")
def old_forcing_file_meteo() -> Dict[str, Path]:
    return {
        "path": Path("tests/data/input/old-external-meteo-only.ext"),
        "quantities": ["windx", "windy"],
        "file_type": ["arcInfo", "arcInfo"],
        "file_path": ["windtest.amu", "windtest.amv"],
    }


@pytest.fixture(scope="function")
def old_forcing_file_boundary() -> Dict[str, Path]:
    return {
        "path": Path(
            "tests/data/input/boundary-conditions/old-external-boundary_condition_only.ext"
        ),
        "quantities": [
            "waterlevelbnd",
        ],
        "locationfile": [
            "tfl_01.pli",
        ],
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


@pytest.fixture
def parameter_quantities() -> List[str]:
    return [
        "frictioncoefficient",
        "horizontaleddyviscositycoefficient",
        "horizontaleddydiffusivitycoefficient",
        "advectiontype",
        "infiltrationcapacity",
        "bedrock_surface_elevation",
        "wavedirection",
        "xwaveforce",
        "ywaveforce",
        "waveperiod",
        "wavesignificantheight",
        "internaltidesfrictioncoefficient",
    ]


def quantityunitpair(quantity, unit, verticalpositionindex=None):
    return QuantityUnitPair(
        quantity=quantity, unit=unit, vertpositionindex=verticalpositionindex
    )


@pytest.fixture
def time_series_values() -> Dict[str, Any]:
    return dict(
        name="boundary_timeseries",
        function="timeseries",
        timeinterpolation=TimeInterpolation.block_to,
        offset="1.23",
        factor="2.34",
        quantityunitpair=[
            quantityunitpair("time", "minutes since 2015-01-01 00:00:00"),
            quantityunitpair("dischargebnd", "m³/s"),
        ],
        datablock=[["0", "1.23"], ["60", "2.34"], ["120", "3.45"]],
    )


@pytest.fixture
def t3d_values():
    return dict(
        name="boundary_t3d",
        function="t3d",
        offset="1.23",
        factor="2.34",
        vertpositions="3.45 4.56 5.67",
        vertinterpolation=VerticalInterpolation.log,
        vertpositiontype=VerticalPositionType.percentage_bed,
        timeinterpolation=TimeInterpolation.linear,
        quantityunitpair=[
            quantityunitpair("time", "minutes since 2015-01-01 00:00:00"),
            quantityunitpair("salinitybnd", "ppt", 1),
            quantityunitpair("salinitybnd", "ppt", 2),
            quantityunitpair("salinitybnd", "ppt", 3),
        ],
        datablock=[
            ["0", "1", "2", "3"],
            ["60", "4", "5", "6"],
            ["120", "7", "8", "9"],
        ],
    )
