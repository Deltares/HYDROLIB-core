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
    construct_filemodel_new_or_existing,
    convert_interpolation_data,
    find_temperature_salinity_in_quantities,
    ExternalForcingConfigs,
    UnSupportedQuantitiesError,
    CONVERTER_DATA,
    MDUConfig
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
        mq = ExternalForcingConfigs(
            unsupported_quantity_names=[" A ", "a", "B", None, 123, " b "],
            unsupported_prefixes=[" p1 ", "p2"]
        )
        # stripped, lowercased, deduped
        assert mq.unsupported_quantity_names == ["a", "b"]
        # unchanged (no validator on Prefixes)
        assert mq.unsupported_prefixes == ["p1", "p2"]

    def test_empty_input_defaults(self):
        mq = ExternalForcingConfigs()
        assert mq.unsupported_quantity_names == []
        assert mq.unsupported_prefixes == []

    def test_from_yaml_file(self, tmp_path):
        yaml_text = """
    external_forcing:
      unsupported_quantity_names:
        - " x "
        - "X"
        - y
      unsupported_prefixes:
        - pre
    """
        data = yaml.safe_load(yaml_text)
        mq = ExternalForcingConfigs(**(data.get("external_forcing") or {}))
        assert mq.unsupported_quantity_names == ["x", "y"]
        assert mq.unsupported_prefixes == ["pre"]



class TestCheckUnsupportedQuantities:
    def test_check_no_raise_when_all_supported(self):
        model = MagicMock(spec=ExtOldModel)
        model.forcing = [
            SimpleNamespace(quantity="supported_quantity_a"),
            SimpleNamespace(quantity="supported_quantity_b"),
        ]
        CONVERTER_DATA.check_unsupported_quantities(model)  # should not raise

    def test_check_raises_on_unsupported(self):
        if not CONVERTER_DATA.external_forcing.unsupported_quantity_names:
            pytest.skip("No unsupported quantities configured.")
        unsupported = next(iter(CONVERTER_DATA.external_forcing.unsupported_quantity_names))

        model = MagicMock(spec=ExtOldModel)
        model.forcing = [
            SimpleNamespace(quantity="supported_quantity"),
            SimpleNamespace(quantity=unsupported),
        ]

        with pytest.raises(UnSupportedQuantitiesError) as exc:
            CONVERTER_DATA.check_unsupported_quantities(model)
        assert str(unsupported) in str(exc.value)

    def test_check_raises_on_unsupported_with_prefix(self):
        if not CONVERTER_DATA.external_forcing.unsupported_prefixes:
            pytest.skip("No unsupported quantities configured.")
        unsupported = next(iter(CONVERTER_DATA.external_forcing.unsupported_prefixes))

        model = MagicMock(spec=ExtOldModel)
        model.forcing = [
            SimpleNamespace(quantity="supported_quantity"),
            SimpleNamespace(quantity=f"{unsupported}any-suffix"),
        ]

        with pytest.raises(UnSupportedQuantitiesError) as exc:
            CONVERTER_DATA.check_unsupported_quantities(model)
        assert str(unsupported) in str(exc.value)


def test_missing_quantities_are_unique():
    path = Path(CONVERTER_DATA_PATH)
    data = yaml.safe_load(path.read_text()) or {}
    items = data.get("external_forcing") or []
    # only consider strings; strip to avoid whitespace duplicates
    items = [s.strip() for s in items if isinstance(s, str)]
    dupes = [k for k, c in Counter(items).items() if c > 1]
    assert not dupes, f"Duplicate entries in external_forcing: {dupes}"


class TestMDUConfigToSetValidator:
    """Tests for the @validator('deprecated_keywords', pre=True) -> _to_set."""

    def test_single_string(self):
        """
        Input: deprecated_keywords=' AllowCoolingBelowZero '
        Expect: {'allowcoolingbelowzero'} after strip+lower and dedup.
        Checks: normalization of a single string value.
        """
        cfg = MDUConfig(deprecated_keywords=" AllowCoolingBelowZero ")
        assert cfg.deprecated_keywords == {"allowcoolingbelowzero"}

    def test_list_of_strings_normalization_and_dedup(self):
        """
        Input: deprecated_keywords=[' A ', 'a', 'B', ' b ']
        Expect: {'a', 'b'} after strip+lower+dedup.
        Checks: list normalization and deduplication.
        """
        cfg = MDUConfig(deprecated_keywords=[" A ", "a", "B", " b "])
        assert cfg.deprecated_keywords == {"a", "b"}

    def test_mixed_types_in_list(self):
        """
        Input: deprecated_keywords=[' A ', None, 123, ' b ']
        Expect: {'a', '123', 'b'} after coercing non-strings via str(), strip+lower, dedup, and filtering falsy.
        Checks: robustness to mixed-type inputs.
        """
        cfg = MDUConfig(deprecated_keywords=[" A ", None, 123, " b "])
        assert cfg.deprecated_keywords == {"a", "b"}

    def test_duplicates_with_casing_and_whitespace(self):
        """
        Input: deprecated_keywords=['X', ' x ', 'X ', 'x']
        Expect: {'x'} after normalization.
        Checks: duplicates collapse to a single normalized entry.
        """
        cfg = MDUConfig(deprecated_keywords=["X", " x ", "X ", "x"])
        assert cfg.deprecated_keywords == {"x"}

    def test_iterable_other_than_list(self):
        """
        Input: deprecated_keywords as a set-like {' A ', 'b'}
        Expect: {'a', 'b'} after normalization.
        Checks: non-list iterables are accepted and normalized consistently.
        """
        cfg = MDUConfig(deprecated_keywords={" A ", "b"})
        assert cfg.deprecated_keywords == {"a", "b"}

    def test_tuple_input(self):
        """
        Input: deprecated_keywords=(' A ', 'B ')
        Expect: {'a', 'b'} after normalization.
        Checks: tuple input handling.
        """
        cfg = MDUConfig(deprecated_keywords=(" A ", "B "))
        assert cfg.deprecated_keywords == {"a", "b"}

    def test_falsy_values_filtered(self):
        """
        Input: deprecated_keywords=['', '   ', None]
        Expect: set() since all normalize to empty/falsy.
        Checks: empty and None are filtered out after normalization.
        """
        cfg = MDUConfig(deprecated_keywords=["", "   ", None])
        assert cfg.deprecated_keywords == set()


class TestMDUConfigDeprecatedValue:
    """Tests for the 'deprecated_value' field type and defaults (Union[int, float])."""

    def test_default_value_is_zero(self):
        """
        Input: omit deprecated_value.
        Expect: deprecated_value == 0 (int).
        Checks: defaulting behavior when value is not provided.
        """
        cfg = MDUConfig()
        assert cfg.deprecated_value == 0
        assert isinstance(cfg.deprecated_value, int)

    def test_accepts_int(self):
        """
        Input: deprecated_value=5
        Expect: deprecated_value == 5 (int).
        Checks: integer is stored as-is.
        """
        cfg = MDUConfig(deprecated_value=5)
        assert cfg.deprecated_value == 5
        assert isinstance(cfg.deprecated_value, int)

    def test_accepts_float(self):
        """
        Input: deprecated_value=3.14
        Expect: deprecated_value == 3.14 (float).
        Checks: float is stored as-is.
        """
        cfg = MDUConfig(deprecated_value=3.14)
        assert isinstance(cfg.deprecated_value, float)
        assert cfg.deprecated_value == pytest.approx(3.14)

    def test_rejects_string(self):
        """
        Input: deprecated_value='invalid'
        Expect: pydantic validation error since value must be int or float.
        Checks: strict typing enforced by the annotated field type.
        """
        with pytest.raises(Exception):
            MDUConfig(deprecated_value="invalid")

    def test_rejects_list(self):
        """
        Input: deprecated_value=[1, 2]
        Expect: pydantic validation error since lists are no longer allowed.
        Checks: only scalar int/float are valid.
        """
        with pytest.raises(Exception):
            MDUConfig(deprecated_value=[1, 2])

    def test_rejects_dict(self):
        """
        Input: deprecated_value={'a': 1}
        Expect: pydantic validation error since dicts are not allowed.
        Checks: only scalar int/float are valid.
        """
        with pytest.raises(Exception):
            MDUConfig(deprecated_value={"a": 1})


# class TestConverterData:
#     def test_1(self):
#         from hydrolib.tools.extforce_convert.utils import ConverterData, CONVERTER_DATA
#         cfg = ConverterData(**CONVERTER_DATA)
#         print(cfg)
