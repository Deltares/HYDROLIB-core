from pathlib import Path

import pytest

from hydrolib.core.dflowfm.ext.models import ExtModel
from hydrolib.core.dflowfm.extold.models import ExtOldForcing, ExtOldQuantity
from hydrolib.core.dflowfm.inifield.models import IniFieldModel
from hydrolib.core.dflowfm.structure.models import StructureModel
from hydrolib.tools.ext_old_to_new.utils import (
    construct_filemodel_new_or_existing,
    convert_interpolation_data,
    find_temperature_salinity_in_quantities,
)


@pytest.mark.parametrize("model", [ExtModel, IniFieldModel, StructureModel])
def test_construct_filemodel_new(model):
    file = Path("tests/data/new-file")
    ext_model = construct_filemodel_new_or_existing(model, file)
    assert isinstance(ext_model, model)
    assert ext_model.filepath == file


def test_convert_interpolation_data():
    data = {}
    forcing = ExtOldForcing(
        quantity=ExtOldQuantity.WindX,
        filename="windtest.amu",
        filetype=4,
        method="6",
        operand="O",
    )
    data = convert_interpolation_data(forcing, data)
    assert data["interpolationmethod"] == "averaging"
    assert data["averagingnummin"] is None
    assert data["averagingtype"] == "mean"
    assert data["averagingrelsize"] is None
    assert data["averagingpercentile"] is None


@pytest.mark.parametrize(
    "strings, expected",
    [
        (["temperature", "Salinity"], {"temperaturedelta": 3, "salinitydelta": 4}),
        (["Temperature"], {"temperaturedelta": 3}),
        (["Salinity"], {"salinitydelta": 3}),
        (["tracers"], {}),
        (["TEMPERATURE", "salInity"], {"temperaturedelta": 3, "salinitydelta": 4}),
        ([], {}),
        (["No relevant data here.", "Nothing to match."], {}),
    ],
)
def test_find_keywords_with_values(strings, expected):
    assert find_temperature_salinity_in_quantities(strings) == expected
