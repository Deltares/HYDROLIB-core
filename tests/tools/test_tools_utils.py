from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import yaml
from pydantic.v1.error_wrappers import ValidationError
from hydrolib.core.dflowfm.ext.models import ExtModel
from hydrolib.core.dflowfm.extold.models import (
    ExtOldForcing,
    ExtOldModel,
    ExtOldQuantity,
)
from hydrolib.core.dflowfm.inifield.models import IniFieldModel
from hydrolib.core.dflowfm.mdu.models import Time
from hydrolib.core.dflowfm.structure.models import StructureModel
from hydrolib.tools.extforce_convert.utils import (
    CONVERTER_DATA_PATH,
    IgnoreUnknownKeyWordClass,
    check_unsupported_quantities,
    construct_filemodel_new_or_existing,
    convert_interpolation_data,
    find_temperature_salinity_in_quantities,
    UnsupportedQuantities,
    UnSupportedQuantitiesError,
    unsupported_quantities
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
        (
            ["temperature", "Salinity"],
            {"sourcesink_temperaturedelta": 4, "sourcesink_salinitydelta": 3},
        ),
        (["Temperature"], {"sourcesink_temperaturedelta": 3}),
        (["Salinity"], {"sourcesink_salinitydelta": 3}),
        (["tracers"], {}),
        (
            ["TEMPERATURE", "salInity"],
            {"sourcesink_temperaturedelta": 4, "sourcesink_salinitydelta": 3},
        ),
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
        from hydrolib.tools.extforce_convert.utils import IgnoreUnknownKeyWord

        mdu_time = IgnoreUnknownKeyWordClass(Time, **time_data)
        assert mdu_time.__class__.__name__ == "DynamicClass"
        assert mdu_time.refdate == 20010101
        assert mdu_time.tzone == pytest.approx(0.0)
        assert mdu_time.dtuser == pytest.approx(10.0)


class TestMissingQuantities:

    def test_missing_quantities_normalization(self):
        mq = UnsupportedQuantities(
            name=[" A ", "a", "B", None, 123, " b "],
            prefix=[" p1 ", "p2"]
        )
        # stripped, lowercased, deduped
        assert mq.name == ["a", "b"]
        # unchanged (no validator on Prefixes)
        assert mq.prefix == [" p1 ", "p2"]

    def test_empty_input_defaults(self):
        mq = UnsupportedQuantities()
        assert mq.name == []
        assert mq.prefix == []

    def test_from_yaml_file(self, tmp_path):
        yaml_text = """
    external_forcing:
      name:
        - " x "
        - "X"
        - y
      prefix:
        - pre
    """
        data = yaml.safe_load(yaml_text)
        mq = UnsupportedQuantities(**(data.get("external_forcing") or {}))
        assert mq.name == ["x", "y"]
        assert mq.prefix == ["pre"]



class TestCheckUnsupportedQuantities:
    def test_check_no_raise_when_all_supported(self):
        model = MagicMock(spec=ExtOldModel)
        model.forcing = [
            SimpleNamespace(quantity="supported_quantity_a"),
            SimpleNamespace(quantity="supported_quantity_b"),
        ]
        check_unsupported_quantities(model)  # should not raise

    def test_check_raises_on_unsupported(self):
        if not unsupported_quantities.name:
            pytest.skip("No unsupported quantities configured.")
        unsupported = next(iter(unsupported_quantities.name))

        model = MagicMock(spec=ExtOldModel)
        model.forcing = [
            SimpleNamespace(quantity="supported_quantity"),
            SimpleNamespace(quantity=unsupported),
        ]

        with pytest.raises(UnSupportedQuantitiesError) as exc:
            check_unsupported_quantities(model)
        assert str(unsupported) in str(exc.value)


def test_missing_quantities_are_unique():
    path = Path(CONVERTER_DATA_PATH)
    data = yaml.safe_load(path.read_text()) or {}
    items = data.get("external_forcing") or []
    # only consider strings; strip to avoid whitespace duplicates
    items = [s.strip() for s in items if isinstance(s, str)]
    dupes = [k for k, c in Counter(items).items() if c > 1]
    assert not dupes, f"Duplicate entries in external_forcing: {dupes}"

