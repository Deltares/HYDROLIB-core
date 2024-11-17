import pytest
from typing import List


@pytest.fixture
def initial_condition_quantities() -> List[str]:
    return [
        "initialwaterlevel", "initialsalinity", "initialsalinitytop", "initialtemperature",
        "initialverticaltemperatureprofile", "initialverticalsalinityprofile", "initialvelocityx",
        "initialvelocityy", "initialvelocity", "initialsalinitytopuse"
    ]


@pytest.fixture
def initial_condition_interpolation_methods() -> List[str]:
    return ["constant", "averaging", "triangulation", "allowedvaluestext"]


@pytest.fixture
def initial_condition_file_type() -> List[str]:
    return ["arcinfo", "GeoTIFF", "sample", "1dField", "polygon", "Possible values: arcinfo, GeoTIFF, sample, 1dField, polygon."]
    return ["arcinfo", "geotiff", "sample", "d1fiels", "polygon", "allowedvaluestext"]
