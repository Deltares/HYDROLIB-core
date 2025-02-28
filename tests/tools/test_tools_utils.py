from pathlib import Path

import pytest
from pydantic.v1.error_wrappers import ValidationError

from hydrolib.core.dflowfm.ext.models import ExtModel
from hydrolib.core.dflowfm.extold.models import ExtOldForcing, ExtOldQuantity
from hydrolib.core.dflowfm.inifield.models import IniFieldModel
from hydrolib.core.dflowfm.mdu.models import Time
from hydrolib.core.dflowfm.structure.models import StructureModel
from hydrolib.tools.ext_old_to_new.utils import (
    IgnoreUnknownKeyWordClass,
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
        (["discharge_salinity_temperature_sorsin"], {}),
        (["temperature", "Salinity"], {"temperaturedelta": 4, "salinitydelta": 3}),
        (["Temperature"], {"temperaturedelta": 3}),
        (["Salinity"], {"salinitydelta": 3}),
        (["tracers"], {}),
        (["TEMPERATURE", "salInity"], {"temperaturedelta": 4, "salinitydelta": 3}),
        ([], {}),
        (["No relevant data here.", "Nothing to match."], {}),
    ],
)
def test_find_keywords_with_values(strings, expected):
    assert find_temperature_salinity_in_quantities(strings) == expected


def test_ignore_unknown_keyword_class():
    time_data = {
        "_header": "time",
        "datablock": None,
        "refdate": "20010101",
        "tzone": "0.",
        "dtuser": "10.",
        "dtnodal": "21600.",
        "dtmax": "10.",
        "dtfacmax": "1.1",
        "dtinit": "1.",
        "timestepanalysis": "0",
        "tunit": "S",
        "tstart": "0.",
        "tstop": "86400.",
    }
    try:
        Time(**time_data)
    except ValidationError:
        from hydrolib.tools.ext_old_to_new.utils import IgnoreUnknownKeyWord

        mdu_time = IgnoreUnknownKeyWordClass(Time, **time_data)
        assert mdu_time.__class__.__name__ == "DynamicClass"
        assert mdu_time.refdate == 20010101
        assert mdu_time.tzone == pytest.approx(0.0)
        assert mdu_time.dtuser == pytest.approx(10.0)
