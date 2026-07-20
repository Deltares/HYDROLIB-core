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
    ConverterData,
    ExternalForcingConfigs,
    IgnoreUnknownKeyWordClass,
    MDUConfig,
    UnSupportedQuantitiesError,
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


class TestOldToNewQuantityNames:
    """Tests for the `old_to_new_quantity_names` rename table on `ExternalForcingConfigs`."""

    def test_keys_are_normalized_and_values_kept_verbatim(self):
        """
        Input: an entry padded with whitespace and spelled in mixed case.
        Expect: the old name is trimmed and lowercased, while the new name is only
            trimmed. The new name is written straight into the initial and parameter
            fields file, so lowercasing it would defeat the table's purpose.
        """
        configs = ExternalForcingConfigs(
            old_to_new_quantity_names={"  Sea_Ice_Thickness ": " seaIceThickness "}
        )
        assert configs.old_to_new_quantity_names == {
            "sea_ice_thickness": "seaIceThickness"
        }

    def test_defaults_to_empty_when_omitted(self):
        """
        Input: no `old_to_new_quantity_names` at all.
        Expect: an empty mapping, so a config without the section renames nothing.
        """
        assert ExternalForcingConfigs().old_to_new_quantity_names == {}

    def test_none_becomes_empty_mapping(self):
        """
        Input: an explicit `None`, as an empty YAML key produces.
        Expect: an empty mapping rather than a validation error.
        """
        assert (
            ExternalForcingConfigs(
                old_to_new_quantity_names=None
            ).old_to_new_quantity_names
            == {}
        )

    def test_from_yaml_file(self):
        """
        Input: the section as it is spelled in `data.yaml`.
        Expect: it survives a `yaml.safe_load` round trip into the model.
        """
        yaml_text = """
    external_forcing:
      old_to_new_quantity_names:
        sea_ice_thickness: seaIceThickness
        BedRock_Surface_Elevation: bedrockSurfaceElevation
    """
        data = yaml.safe_load(yaml_text)
        configs = ExternalForcingConfigs(**(data.get("external_forcing") or {}))
        assert configs.old_to_new_quantity_names == {
            "sea_ice_thickness": "seaIceThickness",
            "bedrock_surface_elevation": "bedrockSurfaceElevation",
        }

    @pytest.mark.parametrize(
        "quantity, expected",
        [
            pytest.param("sea_ice_thickness", "seaIceThickness", id="mapped"),
            pytest.param("SEA_ICE_THICKNESS", "seaIceThickness", id="mapped-uppercase"),
            pytest.param(
                "frictioncoefficient", "frictioncoefficient", id="unmapped-passthrough"
            ),
        ],
    )
    def test_rename_quantity(self, quantity, expected):
        """
        Input: a quantity name, mapped or not, in assorted casings.
        Expect: mapped names resolve case-insensitively; unmapped names pass through
            unchanged so the converter can keep using the old name.

        Note: the lookup lowercases but does not trim, matching `find_unsupported`.
        """
        configs = ExternalForcingConfigs(
            old_to_new_quantity_names={"sea_ice_thickness": "seaIceThickness"}
        )
        assert configs.rename_quantity(quantity) == expected

    def test_rename_quantity_accepts_an_ext_old_quantity_member(self):
        """
        Input: an `ExtOldQuantity` member rather than a plain string.
        Expect: the member resolves to its value and the lookup hits.

        `ExtOldQuantity` is built on the third-party `strenum.StrEnum`, whose `str()`
        returns the member value. The converter passes `forcing.quantity` (a member)
        straight in, so a base class whose `str()` returned `ExtOldQuantity.X` instead
        would make every lookup silently miss.
        """
        configs = ExternalForcingConfigs(
            old_to_new_quantity_names={
                ExtOldQuantity.SeaIceThickness.value: "seaIceThickness"
            }
        )
        assert (
            configs.rename_quantity(ExtOldQuantity.SeaIceThickness) == "seaIceThickness"
        )

    def test_configured_renames_are_loaded_from_data_yaml(self):
        """
        Input: the `CONVERTER_DATA` singleton built from `data.yaml` at import time.
        Expect: the sea ice entries documented in UM Sec.15.8.1 are present, and adding
            the section left the unsupported lists untouched.
        """
        configs = CONVERTER_DATA.external_forcing
        assert (
            configs.old_to_new_quantity_names["sea_ice_thickness"] == "seaIceThickness"
        )
        assert (
            configs.old_to_new_quantity_names["sea_ice_area_fraction"]
            == "seaIceAreaFraction"
        )
        assert configs.unsupported_quantity_names
        assert configs.unsupported_prefixes

    @pytest.mark.parametrize(
        "invalid",
        [
            pytest.param(["a", "b"], id="list-not-mapping"),
            pytest.param("sea_ice_thickness", id="string-not-mapping"),
            pytest.param({"sea_ice_thickness": 1}, id="non-string-value"),
            pytest.param({1: "seaIceThickness"}, id="non-string-key"),
            pytest.param({"sea_ice_thickness": "   "}, id="blank-value"),
            pytest.param({"   ": "seaIceThickness"}, id="blank-key"),
        ],
    )
    def test_invalid_entries_are_rejected(self, invalid):
        """
        Input: a table that is not a mapping, or holds a non-string or empty name.
        Expect: a validation error at load time rather than a silently broken table.
        """
        with pytest.raises(ValidationError):
            ExternalForcingConfigs(old_to_new_quantity_names=invalid)

    def test_unknown_old_quantity_name_is_rejected(self):
        """
        Input: a key that is not a quantity of the old external forcings file.
        Expect: a validation error at load time.

        A mistyped key would otherwise pass validation and then silently never fire,
        since `rename_quantity` falls back to returning its input unchanged. The
        converter would emit the old name and the kernel would reject the model far
        from the cause.
        """
        with pytest.raises(ValidationError) as exc:
            ExternalForcingConfigs(
                old_to_new_quantity_names={"sea_ice_thicknes": "seaIceThickness"}
            )
        assert "not a known" in str(exc.value)

    def test_keys_colliding_once_lowercased_are_rejected(self):
        """
        Input: two old names that differ only in casing, mapped to different new names.
        Expect: a validation error. Normalizing would collapse them and let the last
            entry win silently, so the ambiguity is reported instead.
        """
        with pytest.raises(ValidationError) as exc:
            ExternalForcingConfigs(
                old_to_new_quantity_names={
                    "Sea_Ice_Thickness": "seaIceThickness",
                    "sea_ice_thickness": "somethingElse",
                }
            )
        assert "more than once" in str(exc.value)


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


class TestConverterData:
    """Tests for the `ConverterData` root config model."""

    def test_version_is_required(self):
        """
        Input: no fields at all.
        Expect: a validation error, since `version` has no default.
        """
        with pytest.raises(ValidationError):
            ConverterData()

    def test_nested_configs_default_when_omitted(self):
        """
        Input: only `version`.
        Expect: `mdu` and `external_forcing` are built from their default factories.
        """
        data = ConverterData(version=1.0)
        assert data.version == pytest.approx(1.0)
        assert isinstance(data.mdu, MDUConfig)
        assert isinstance(data.external_forcing, ExternalForcingConfigs)
        assert data.mdu.deprecated_keywords == set()
        assert data.mdu.deprecated_value == 0
        assert data.external_forcing.unsupported_quantity_names == []
        assert data.external_forcing.unsupported_prefixes == []

    def test_nested_dicts_are_coerced_and_normalized(self):
        """
        Input: raw nested dicts, as they come out of `yaml.safe_load`.
        Expect: sub-models are constructed and their own validators normalize the values.
        """
        data = ConverterData(
            version=1.0,
            mdu={"deprecated_keywords": [" A ", "a"], "deprecated_value": 0},
            external_forcing={
                "unsupported_quantity_names": [" WindX ", "windx", "PUMP"],
                "unsupported_prefixes": [" WAQfunction "],
            },
        )
        assert data.mdu.deprecated_keywords == {"a"}
        assert data.external_forcing.unsupported_quantity_names == ["windx", "pump"]
        assert data.external_forcing.unsupported_prefixes == ["waqfunction"]

    def test_check_unsupported_quantities_passes_when_all_supported(self):
        """
        Input: a model whose quantities are absent from the config.
        Expect: an empty set and no error.
        """
        data = ConverterData(
            version=1.0, external_forcing={"unsupported_quantity_names": ["pump"]}
        )
        model = MagicMock(spec=ExtOldModel)
        model.forcing = [SimpleNamespace(quantity="windx")]
        assert data.check_unsupported_quantities(model) == set()

    def test_check_unsupported_quantities_is_case_insensitive(self):
        """
        Input: a quantity that differs from the configured entry only in casing.
        Expect: it is still recognized as unsupported, since both sides are lowercased.
        """
        data = ConverterData(
            version=1.0, external_forcing={"unsupported_quantity_names": ["Pump"]}
        )
        model = MagicMock(spec=ExtOldModel)
        model.forcing = [SimpleNamespace(quantity="PUMP")]
        with pytest.raises(UnSupportedQuantitiesError):
            data.check_unsupported_quantities(model)

    def test_check_unsupported_quantities_without_raising(self):
        """
        Input: unsupported quantities with `raise_error=False`.
        Expect: the offending quantities are returned instead of raising.
        """
        data = ConverterData(
            version=1.0,
            external_forcing={
                "unsupported_quantity_names": ["pump"],
                "unsupported_prefixes": ["waqfunction"],
            },
        )
        model = MagicMock(spec=ExtOldModel)
        model.forcing = [
            SimpleNamespace(quantity="windx"),
            SimpleNamespace(quantity="pump"),
            SimpleNamespace(quantity="waqfunction_something"),
        ]
        assert data.check_unsupported_quantities(model, raise_error=False) == {
            "pump",
            "waqfunction_something",
        }

    def test_check_unsupported_quantities_on_empty_model(self):
        """
        Input: a model with no forcing blocks.
        Expect: an empty set, not an error.
        """
        data = ConverterData(
            version=1.0, external_forcing={"unsupported_quantity_names": ["pump"]}
        )
        model = MagicMock(spec=ExtOldModel)
        model.forcing = []
        assert data.check_unsupported_quantities(model) == set()

    def test_module_level_converter_data_is_loaded(self):
        """
        Input: the `CONVERTER_DATA` singleton built from `data.yaml` at import time.
        Expect: a fully constructed `ConverterData` with its nested configs in place.
        """
        assert isinstance(CONVERTER_DATA, ConverterData)
        assert isinstance(CONVERTER_DATA.mdu, MDUConfig)
        assert isinstance(CONVERTER_DATA.external_forcing, ExternalForcingConfigs)
        assert CONVERTER_DATA.version > 0


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
