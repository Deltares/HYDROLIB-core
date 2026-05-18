"""Tests for the `_resolve_forcing_data` helper in `hydrolib.core.dflowfm.ext.models`.

The helper coerces raw INI/user-supplied values into a member of
`ForcingData = float | RealTime | ForcingModel` so that fields typed `ForcingData`
on `Lateral` and `SourceSink` accept the full set of representations that the
D-Flow FM external-forcings format allows.
"""

from pathlib import Path

import pytest

from hydrolib.core.dflowfm.bc.models import ForcingModel, RealTime
from hydrolib.core.dflowfm.ext.models import _resolve_forcing_data
from tests.utils import test_data_dir

BC_FIXTURE = test_data_dir / "input" / "source-sink" / "BoundaryConditions.bc"


class TestResolveForcingData:
    """Direct tests of the `_resolve_forcing_data` helper."""

    @pytest.mark.parametrize(
        "value, expected",
        [
            ("1.23", 1.23),
            ("0", 0.0),
            ("-5.5", -5.5),
            ("1e3", 1000.0),
        ],
    )
    def test_str_numeric_returns_float(self, value: str, expected: float) -> None:
        """Numeric strings are parsed as floats before any other branch.

        Args:
            value: Numeric string passed to the helper.
            expected: Expected float result.

        Test scenario:
            Covers nominal, zero boundary, negative, and scientific-notation
            float representations that appear in INI files.
        """
        result = _resolve_forcing_data(value)
        assert isinstance(result, float), (
            f"Numeric string {value!r} should yield a float, got {type(result).__name__}"
        )
        assert result == expected, f"Expected {expected}, got {result}"

    @pytest.mark.parametrize("value", ["realtime", "RealTime", "REALTIME", "Realtime"])
    def test_str_realtime_is_case_insensitive(self, value: str) -> None:
        """Any case of the literal "realtime" maps to `RealTime.realtime`.

        Args:
            value: Realtime keyword in varying letter cases.

        Test scenario:
            The helper lower-cases the string before constructing the
            `RealTime` enum, which is necessary because the enum itself is
            case-sensitive in Pydantic's default coercion.
        """
        result = _resolve_forcing_data(value)
        assert result is RealTime.realtime, (
            f"Realtime keyword {value!r} should yield RealTime.realtime, got {result!r}"
        )

    def test_str_filepath_returns_forcingmodel(self) -> None:
        """A string path to an existing `.bc` file is loaded as a `ForcingModel`.

        Test scenario:
            The string is not numeric and not the realtime keyword, so it
            falls through to `resolve_file_model(...)` which loads the `.bc`
            file via the standard file-load context.
        """
        result = _resolve_forcing_data(str(BC_FIXTURE))
        assert isinstance(result, ForcingModel), (
            f"Expected ForcingModel, got {type(result).__name__}"
        )
        assert len(result.forcing) > 0, "Loaded ForcingModel should contain forcing blocks"

    def test_path_returns_forcingmodel(self) -> None:
        """A `pathlib.Path` is always treated as a file to load.

        Test scenario:
            Unlike strings, a Path is never numeric or an enum value, so the
            helper short-circuits to file resolution.
        """
        result = _resolve_forcing_data(BC_FIXTURE)
        assert isinstance(result, ForcingModel), (
            f"Expected ForcingModel from Path, got {type(result).__name__}"
        )

    def test_dict_constructs_forcingmodel(self) -> None:
        """A dict is unpacked into the `ForcingModel` constructor.

        Test scenario:
            Empty dict is sufficient since all `ForcingModel` fields have
            defaults — the result is an in-memory model with no forcing blocks.
        """
        result = _resolve_forcing_data({})
        assert isinstance(result, ForcingModel), (
            f"Expected ForcingModel from dict, got {type(result).__name__}"
        )
        assert result.forcing == [], (
            f"Empty dict should yield an empty forcing list, got {result.forcing}"
        )

    def test_none_passthrough(self) -> None:
        """`None` is passed through unchanged for use with `Optional[ForcingData]` fields.

        Test scenario:
            Optional fields like `SourceSink.salinitydelta` rely on this
            passthrough so they can remain unset.
        """
        result = _resolve_forcing_data(None)
        assert result is None, f"None should pass through unchanged, got {result!r}"

    def test_float_passthrough(self) -> None:
        """A float input is returned unchanged.

        Test scenario:
            Already-validated values must not be transformed (e.g. when the
            validator runs on an already-instantiated dict from Pydantic).
        """
        result = _resolve_forcing_data(3.14)
        assert result == 3.14, f"Float should pass through unchanged, got {result!r}"

    def test_realtime_enum_roundtrips(self) -> None:
        """A `RealTime` enum value yields the same enum.

        Test scenario:
            `RealTime` inherits from `StrEnum`, so `isinstance(v, str)` is
            True and the value re-enters the string branch. The lowercase
            conversion still resolves to `RealTime.realtime`, so the result
            is identical to the input.
        """
        result = _resolve_forcing_data(RealTime.realtime)
        assert result is RealTime.realtime, (
            f"RealTime input should round-trip to RealTime.realtime, got {result!r}"
        )

    def test_forcingmodel_passthrough(self) -> None:
        """An existing `ForcingModel` instance is returned unchanged.

        Test scenario:
            Avoids re-loading or re-parsing when the validator runs on a
            value that already matches the target union member.
        """
        model = ForcingModel()
        result = _resolve_forcing_data(model)
        assert result is model, (
            "Existing ForcingModel should be returned by identity, not re-created"
        )

    def test_int_passthrough_for_pydantic_to_coerce(self) -> None:
        """A bare `int` is passed through; Pydantic coerces it to float downstream.

        Test scenario:
            The helper handles only str/Path/dict; other types fall through
            untouched so Pydantic's union validation can run its own coercion
            (e.g. int → float for the `float` member of `ForcingData`).
        """
        result = _resolve_forcing_data(42)
        assert result == 42, f"int should pass through unchanged, got {result!r}"
        assert type(result) is int, (
            f"Helper must not coerce int to float — that is Pydantic's job, got {type(result).__name__}"
        )
