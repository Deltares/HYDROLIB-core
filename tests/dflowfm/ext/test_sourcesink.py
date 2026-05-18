"""
Class to test all methods contained in the
hydrolib.core.dflowfm.ext.models.SourceSink class
"""

from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError

from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm.bc.models import ForcingModel, RealTime
from hydrolib.core.dflowfm.ext.models import ExtModel, SourceSink
from tests.utils import test_data_dir


class TestSourceSink:
    """
    Class to test the different types of source/sink forcings.
    """

    def test_sourcesink_fromfile(self):

        filepath = test_data_dir / "input/source-sink/source-sink-new.ext"
        m = ExtModel(filepath)
        assert len(m.sourcesink) == 2
        assert m.sourcesink[0].id == "L1"
        assert np.isclose(m.sourcesink[0].discharge, 10)
        assert np.isclose(m.sourcesink[1].discharge, 20)

    def test_sourcesink_fromdict(self):

        data = {
            "sourcesink": [
                {
                    "id": "L1",
                    "name": "L1",
                    "locationFile": "foobar.pli",
                    "zSink": 0.0,
                    "zSource": 0.0,
                    "area": 1.0,
                    "discharge": 1.23,
                    "salinitydelta": 4.0,
                    "temperatureDelta": 5.0,
                }
            ]
        }
        m = ExtModel(**data)
        assert len(m.sourcesink) == 1
        assert np.isclose(m.sourcesink[0].discharge, 1.23)


class TestSourceSinkValidator:
    """
    class to test the validate_location_specification validator.
    """

    def test_source_sink_with_locationfile(self):
        """Test SourceSink creation with locationfile provided."""
        source_sink = SourceSink(
            id="test1",
            locationfile=DiskOnlyFileModel(filepath=Path("locationfile.pli")),
            discharge=5,
        )
        assert source_sink.locationfile is not None
        assert source_sink.numcoordinates is None
        assert source_sink.xcoordinates is None
        assert source_sink.ycoordinates is None

    def test_source_sink_with_coordinates(self):
        """Test SourceSink creation with coordinates provided."""
        source_sink = SourceSink(
            id="test2",
            numcoordinates=2,
            xcoordinates=[1.0, 2.0],
            ycoordinates=[3.0, 4.0],
            discharge=5,
        )
        assert source_sink.numcoordinates == 2
        assert source_sink.xcoordinates == [1.0, 2.0]
        assert source_sink.ycoordinates == [3.0, 4.0]
        assert source_sink.locationfile.filepath is None

    def test_source_sink_without_locationfile_or_coordinates(self):
        """Test that creating a SourceSink without locationfile or coordinates raises an error."""
        with pytest.raises(
            ValueError,
            match="Either `locationFile` or the combination of `numCoordinates`, `xCoordinates`, and `yCoordinates` must be provided.",
        ):
            SourceSink(id="test3", discharge=None)

    def test_source_sink_with_incomplete_coordinates(self):
        """Test that creating a SourceSink with incomplete coordinates raises an error."""
        with pytest.raises(
            ValueError,
            match="Either `locationFile` or the combination of `numCoordinates`, `xCoordinates`, and `yCoordinates` must be provided.",
        ):
            SourceSink(
                id="test4",
                numcoordinates=2,
                xcoordinates=[1.0, 2.0],  # ycoordinates missing
                discharge=None,
            )

    def test_source_sink_with_mismatched_coordinates(self):
        """Test that creating a SourceSink with mismatched coordinate lengths raises an error."""
        with pytest.raises(
            ValueError,
            match="Either `locationFile` or the combination of `numCoordinates`, `xCoordinates`, and `yCoordinates` must be provided.",
        ):
            SourceSink(
                id="test5",
                numcoordinates=2,
                xcoordinates=[1.0, 2.0, 3.0],  # Too many x-coordinates
                ycoordinates=[3.0, 4.0],
                discharge=None,
            )


SOURCESINK_BC_BODY = """[General]
fileVersion = 1.01
fileType    = boundConds

[Forcing]
name              = Q_W
function          = constant
quantity          = sourcesink_discharge
unit              = m3/s
4.5
"""


def _make_sourcesink_kwargs(**overrides):
    """Return baseline kwargs for constructing a `SourceSink` directly.

    Args:
        **overrides: Field overrides merged on top of the defaults.

    Returns:
        dict: Constructor arguments with location data already filled in so
            that the location validator is satisfied for every test scenario.
    """
    base = {
        "id": "ss_test",
        "numcoordinates": 1,
        "xcoordinates": [104.048386],
        "ycoordinates": [1.411220],
        "discharge": 1.0,
    }
    base.update(overrides)
    return base


def _write_ext_with_bc(tmp_path: Path, fields: dict) -> Path:
    """Write a minimal `.ext` referencing a generated `.bc` and return its path.

    Args:
        tmp_path: Pytest-supplied temporary directory.
        fields: Mapping of forcing-data field names (`discharge`,
            `salinitydelta`, `temperaturedelta`) to the `.bc` filename
            string that should appear on the wire.

    Returns:
        Path: Filesystem path to the generated `.ext` file.
    """
    bc_path = tmp_path / "sourcesink.bc"
    bc_path.write_text(SOURCESINK_BC_BODY, encoding="utf-8")

    lines = [
        "[SourceSink]",
        "id             = Q_S",
        "numCoordinates = 1",
        "xCoordinates   = 104.048386",
        "yCoordinates   = 1.411220",
    ]
    for key, value in fields.items():
        lines.append(f"{key:<14} = {value}")
    ext_path = tmp_path / "sourcesink.ext"
    ext_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ext_path


class TestSourceSinkForcingData:
    """Validator coverage for `discharge`, `salinitydelta`, and `temperaturedelta`.

    These three fields share a single `mode="before"` field validator that
    delegates to `_resolve_forcing_data`, so each of float / RealTime /
    `.bc` ForcingModel / dict inputs must reach the field as the right
    union member.
    """

    def test_discharge_numeric_string_is_coerced_to_float(self):
        """Numeric string on `discharge` produces a float on the model.

        Test scenario:
            INI parsers hand strings to Pydantic; the validator must
            convert "1.23" to 1.23 so that the float branch of `ForcingData`
            matches.
        """
        source_sink = SourceSink(**_make_sourcesink_kwargs(discharge="1.23"))
        assert isinstance(source_sink.discharge, float), (
            f"Expected float, got {type(source_sink.discharge).__name__}"
        )
        assert np.isclose(source_sink.discharge, 1.23), (
            f"Expected 1.23, got {source_sink.discharge}"
        )

    @pytest.mark.parametrize("value", ["realtime", "RealTime", "REALTIME"])
    def test_discharge_realtime_keyword_is_case_insensitive(self, value: str):
        """Any case of "realtime" maps to `RealTime.realtime` on `discharge`.

        Args:
            value: Realtime keyword spelled in different cases.

        Test scenario:
            Mirrors the case-insensitive contract already present on
            `Lateral.discharge` so the two ext blocks behave the same.
            Compared with `==` because Pydantic stores the canonical
            string value once the union resolves; `StrEnum.__eq__`
            makes the equality hold against `RealTime.realtime`.
        """
        source_sink = SourceSink(**_make_sourcesink_kwargs(discharge=value))
        assert source_sink.discharge == RealTime.realtime, (
            f"Expected value equal to RealTime.realtime for input {value!r},"
            f" got {source_sink.discharge!r}"
        )

    def test_discharge_bc_path_loads_forcingmodel_via_extmodel(self, tmp_path: Path):
        """A `.bc` filename in the `.ext` becomes a `ForcingModel` on `discharge`.

        Args:
            tmp_path: Pytest temporary directory fixture.

        Test scenario:
            This is the regression for issue #1083 — before the fix, the
            raw `discharge = sourcesink.bc` string failed all three union
            branches with a validation error. After the fix it must load
            and parse the .bc file into a `ForcingModel`.
        """
        ext_path = _write_ext_with_bc(tmp_path, {"discharge": "sourcesink.bc"})
        model = ExtModel(ext_path)
        discharge = model.sourcesink[0].discharge
        assert isinstance(discharge, ForcingModel), (
            f"Expected ForcingModel from .bc path, got {type(discharge).__name__}"
        )
        assert discharge.forcing[0].name == "Q_W", (
            f"Expected forcing block 'Q_W', got {discharge.forcing[0].name!r}"
        )

    def test_discharge_dict_builds_forcingmodel(self):
        """A dict input on `discharge` is unpacked into `ForcingModel`.

        Test scenario:
            Empty dict is sufficient because all `ForcingModel` fields have
            defaults — the result is an in-memory model with no forcings.
        """
        source_sink = SourceSink(**_make_sourcesink_kwargs(discharge={}))
        assert isinstance(source_sink.discharge, ForcingModel), (
            f"Expected ForcingModel from dict, got {type(source_sink.discharge).__name__}"
        )
        assert source_sink.discharge.forcing == [], (
            f"Expected empty forcing list, got {source_sink.discharge.forcing}"
        )

    @pytest.mark.parametrize("field", ["salinitydelta", "temperaturedelta"])
    def test_optional_delta_defaults_to_none(self, field: str):
        """`salinitydelta` and `temperaturedelta` default to `None` when omitted.

        Args:
            field: Either `salinitydelta` or `temperaturedelta`.

        Test scenario:
            Ensures the new validator does not interfere with the optional
            nature of these fields — the helper passes `None` through.
        """
        source_sink = SourceSink(**_make_sourcesink_kwargs())
        assert getattr(source_sink, field) is None, (
            f"Field {field} should default to None, got {getattr(source_sink, field)!r}"
        )

    @pytest.mark.parametrize("field", ["salinitydelta", "temperaturedelta"])
    def test_optional_delta_accepts_float(self, field: str):
        """`salinitydelta` and `temperaturedelta` accept a numeric value.

        Args:
            field: Either `salinitydelta` or `temperaturedelta`.

        Test scenario:
            Nominal use-case mirroring `discharge` numeric handling.
        """
        source_sink = SourceSink(**_make_sourcesink_kwargs(**{field: 4.0}))
        assert getattr(source_sink, field) == 4.0, (
            f"Field {field} should be 4.0, got {getattr(source_sink, field)!r}"
        )

    @pytest.mark.parametrize("field", ["salinitydelta", "temperaturedelta"])
    def test_optional_delta_accepts_realtime_keyword(self, field: str):
        """`salinitydelta` and `temperaturedelta` accept the realtime keyword.

        Args:
            field: Either `salinitydelta` or `temperaturedelta`.

        Test scenario:
            Same union semantics as `discharge`, since all three share the
            `ForcingData` type and the same validator.
        """
        source_sink = SourceSink(**_make_sourcesink_kwargs(**{field: "realtime"}))
        assert getattr(source_sink, field) == RealTime.realtime, (
            f"Field {field} should equal RealTime.realtime,"
            f" got {getattr(source_sink, field)!r}"
        )

    @pytest.mark.parametrize("field", ["salinityDelta", "temperatureDelta"])
    def test_optional_delta_loads_bc_file_via_extmodel(
        self, tmp_path: Path, field: str
    ):
        """`salinityDelta` / `temperatureDelta` accept a `.bc` filename in the `.ext`.

        Args:
            tmp_path: Pytest temporary directory fixture.
            field: Wire alias (`salinityDelta` or `temperatureDelta`).

        Test scenario:
            The fix extended `.bc`-file support to these two optional
            forcing-data fields. The validator must turn the filename
            into a loaded `ForcingModel` just like for `discharge`.
        """
        ext_path = _write_ext_with_bc(
            tmp_path, {"discharge": "1.0", field: "sourcesink.bc"}
        )
        model = ExtModel(ext_path)
        value = getattr(model.sourcesink[0], field.lower())
        assert isinstance(value, ForcingModel), (
            f"Expected ForcingModel on {field.lower()}, got {type(value).__name__}"
        )


class TestSourceSinkDynamicForcingDeltas:
    """Coverage for dynamic `tracer<...>Delta` / `sedFrac<...>Delta` Delta-suffix fields.

    Per D-Flow FM User Manual Table C.8 (§C.6.2.4), these dynamic fields on a
    `[SourceSink]` block accept the same forcing-data forms as the named delta
    fields (scalar Double or `.bc` file path). The `_resolve_dynamic_forcing_deltas`
    model-validator extends the `_resolve_forcing_data` coercion to them via the
    `extra="allow"` mechanism, while leaving the existing non-Delta dynamic fields
    (`initialtracer_*`, `tracerbnd*`, `sedfracbnd_*`) untouched.
    """

    @pytest.mark.parametrize(
        "field, raw, expected",
        [
            ("tracerSaltDelta", "3.5", 3.5),
            ("sedFracClayDelta", "0.25", 0.25),
        ],
    )
    def test_numeric_string_is_coerced_to_float(
        self, field: str, raw: str, expected: float
    ):
        """Numeric string on a dynamic Delta-suffix field is coerced to `float`.

        Args:
            field: Dynamic Delta-suffix wire key.
            raw: Numeric string as it would arrive from the INI parser.
            expected: Float value the helper should produce.

        Test scenario:
            Before the validator existed, these dynamic fields received the
            raw string from the INI parser. The new model-validator routes
            them through `_resolve_forcing_data`, which parses numeric
            strings as floats.
        """
        source_sink = SourceSink(**_make_sourcesink_kwargs(**{field: raw}))
        assert source_sink.model_extra[field] == expected, (
            f"Expected {expected} on dynamic field {field},"
            f" got {source_sink.model_extra[field]!r}"
        )

    @pytest.mark.parametrize("field", ["tracerSaltDelta", "sedFracClayDelta"])
    def test_bc_file_loads_forcingmodel_via_extmodel(
        self, tmp_path: Path, field: str
    ):
        """Dynamic Delta-suffix field accepts a `.bc` filename in the `.ext`.

        Args:
            tmp_path: Pytest temporary directory fixture.
            field: Dynamic Delta-suffix wire key.

        Test scenario:
            Closes the M2 gap from PR review: per the D-Flow FM User Manual,
            `tracer<...>Delta` and `sedFrac<...>Delta` can be a `.bc` path.
            The model-validator must turn that path into a loaded `ForcingModel`,
            the same way `validate_forcing_data` does for the named Delta fields.
        """
        ext_path = _write_ext_with_bc(
            tmp_path, {"discharge": "1.0", field: "sourcesink.bc"}
        )
        model = ExtModel(ext_path)
        value = model.sourcesink[0].model_extra[field.lower()]
        assert isinstance(value, ForcingModel), (
            f"Expected ForcingModel on {field.lower()}, got {type(value).__name__}"
        )

    def test_legacy_non_delta_dynamic_fields_are_untouched(self):
        """Legacy non-Delta dynamic fields keep their raw value (no `_resolve_forcing_data`).

        Test scenario:
            `initialtracer_*`, `tracerbnd*`, `sedfracbnd_*` are pre-existing
            extra-allowed attributes that historically receive arbitrary list
            payloads (e.g. initial-condition arrays). The new model-validator
            must restrict its action to `*delta`-suffixed keys so that this
            legacy data flow is preserved unchanged.
        """
        legacy = {
            "initialtracer_any_name": [1, 2, 3],
            "tracerbndanyname": [4, 5, 6],
            "sedfracbnd_any_name": [7, 8, 9],
        }
        source_sink = SourceSink(**_make_sourcesink_kwargs(**legacy))
        for key, expected in legacy.items():
            actual = getattr(source_sink, key)
            assert actual == expected, (
                f"Legacy dynamic field {key} should be untouched;"
                f" expected {expected}, got {actual!r}"
            )

    @pytest.mark.parametrize("field", ["tracerSaltDelta", "sedFracClayDelta"])
    def test_realtime_keyword_rejected_on_dynamic_delta_fields(self, field: str):
        """`realtime` on a dynamic Delta-suffix field raises a clear `ValueError`.

        Args:
            field: Dynamic Delta-suffix wire key.

        Test scenario:
            Per D-Flow FM User Manual Table C.8 (§C.6.2.4), `realtime` is "not
            (yet) available for sediment fractions and tracers". The
            `_resolve_dynamic_forcing_deltas` validator passes
            `allow_realtime=False` to `_resolve_forcing_data` so hydrolib-core
            rejects the keyword early with a clear error, rather than
            producing an ext file that the D-Flow FM engine will reject at
            runtime.
        """
        with pytest.raises(
            ValidationError, match="'realtime' keyword is not supported"
        ):
            SourceSink(**_make_sourcesink_kwargs(**{field: "realtime"}))
