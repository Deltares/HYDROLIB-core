from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import yaml
from pydantic import ValidationError

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
    CONVERTER_DATA,
    CONVERTER_DATA_PATH,
    ExternalForcingConfigs,
    IgnoreUnknownKeyWordClass,
    MDUConfig,
    UnSupportedQuantitiesError,
    construct_filemodel_new_or_existing,
    convert_interpolation_data,
    find_temperature_salinity_in_quantities,
    parse_substance_file,
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
        averagingtype="1",
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
            unsupported_prefixes=[" p1 ", "p2"],
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
        unsupported = next(
            iter(CONVERTER_DATA.external_forcing.unsupported_quantity_names)
        )

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
    unsupported_quantity_names = data.get("external_forcing", {}).get(
        "unsupported_quantity_names", []
    )
    # only consider strings; strip to avoid whitespace duplicates
    unsupported_quantity_names = [
        s.strip() for s in unsupported_quantity_names if isinstance(s, str)
    ]
    dupes = [k for k, c in Counter(unsupported_quantity_names).items() if c > 1]
    assert not dupes, f"Duplicate entries in external_forcing: {dupes}"

    unsupported_prefixes = data.get("external_forcing", {}).get(
        "unsupported_prefixes", []
    )
    # only consider strings; strip to avoid whitespace duplicates
    unsupported_prefixes = [
        s.strip() for s in unsupported_prefixes if isinstance(s, str)
    ]
    dupes = [k for k, c in Counter(unsupported_prefixes).items() if c > 1]
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


class TestParseSubstanceFile:
    """Tests for parse_substance_file."""

    def test_single_active_substance(self, tmp_path):
        """One active substance: returns a list with that substance name."""
        sub_file = tmp_path / "test.sub"
        sub_file.write_text(
            "substance 'NH4' active\n"
            "   description        'Ammonium (NH4)'\n"
            "   concentration-unit '(gN/m3)'\n"
            "end-substance\n"
        )
        assert parse_substance_file(sub_file) == ["NH4"]

    def test_single_inactive_substance(self, tmp_path):
        """One inactive substance: returns an empty list."""
        sub_file = tmp_path / "test.sub"
        sub_file.write_text(
            "substance 'NO3' inactive\n"
            "   description        'Nitrate'\n"
            "end-substance\n"
        )
        assert parse_substance_file(sub_file) == []

    def test_multiple_active_substances(self, tmp_path):
        """Multiple active substances: returns all names in order."""
        sub_file = tmp_path / "test.sub"
        sub_file.write_text(
            "substance 'NH4' active\n"
            "end-substance\n"
            "substance 'NO3' active\n"
            "end-substance\n"
            "substance 'PO4' active\n"
            "end-substance\n"
        )
        assert parse_substance_file(sub_file) == ["NH4", "NO3", "PO4"]

    def test_mixed_active_and_inactive_substances(self, tmp_path):
        """Mix of active and inactive: only active names are returned, in order."""
        sub_file = tmp_path / "test.sub"
        sub_file.write_text(
            "substance 'NH4' active\n"
            "end-substance\n"
            "substance 'NO3' inactive\n"
            "end-substance\n"
            "substance 'PO4' active\n"
            "end-substance\n"
        )
        assert parse_substance_file(sub_file) == ["NH4", "PO4"]

    def test_empty_file(self, tmp_path):
        """Empty file: returns an empty list."""
        sub_file = tmp_path / "test.sub"
        sub_file.write_text("")
        assert parse_substance_file(sub_file) == []

    def test_no_substance_lines(self, tmp_path):
        """File with no substance declarations: returns an empty list."""
        sub_file = tmp_path / "test.sub"
        sub_file.write_text(
            "# some header comment\n"
            "description 'WAQ substance file'\n"
        )
        assert parse_substance_file(sub_file) == []

    def test_active_keyword_not_in_substance_line_is_ignored(self, tmp_path):
        """'active' appearing inside the substance body does not cause a match."""
        sub_file = tmp_path / "test.sub"
        sub_file.write_text(
            "substance 'NH4' inactive\n"
            "   description 'active tracer'\n"
            "end-substance\n"
        )
        assert parse_substance_file(sub_file) == []

    def test_order_is_preserved(self, tmp_path):
        """Active substances are returned in file order."""
        sub_file = tmp_path / "test.sub"
        sub_file.write_text(
            "substance 'C' active\n"
            "end-substance\n"
            "substance 'A' active\n"
            "end-substance\n"
            "substance 'B' active\n"
            "end-substance\n"
        )
        assert parse_substance_file(sub_file) == ["C", "A", "B"]

    def test_substance_name_with_spaces(self, tmp_path):
        """Substance names containing spaces are parsed correctly."""
        sub_file = tmp_path / "test.sub"
        sub_file.write_text("substance 'total N' active\nend-substance\n")
        assert parse_substance_file(sub_file) == ["total N"]
