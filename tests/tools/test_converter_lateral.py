from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock

import pytest

from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm import Operand
from hydrolib.core.dflowfm.bc.models import (
    ForcingModel,
    QuantityUnitPair,
    RealTime,
    TimeSeries,
    TimeInterpolation,
)
from hydrolib.core.dflowfm.ext.models import Lateral, LateralError
from hydrolib.core.dflowfm.extold.models import (
    ExtOldForcing,
    ExtOldLateralQuantity,
)
from hydrolib.tools.extforce_convert.converters import LateralConverter
from hydrolib.tools.extforce_convert.mdu_parser import MDUParser


TIME_UNIT = "minutes since 2015-01-01 00:00:00"
TIM_CONTENT = "0.0   1.0\n60.0   2.0\n120.0  3.0\n"
PLI_CONTENT = "lateral\n    1    2\n  0.0  0.0\n"


def _make_tim_file(directory: Path, stem: str = "lateral") -> Path:
    path = directory / f"{stem}.tim"
    path.write_text(TIM_CONTENT)
    return path


def _make_pli_file(directory: Path, stem: str = "lateral") -> Path:
    path = directory / f"{stem}.pli"
    path.write_text(PLI_CONTENT)
    return path


def _make_pli_forcing(
    path: Path,
    quantity=ExtOldLateralQuantity.LateralDischarge,
    *,
    value: Optional[float] = None,
) -> ExtOldForcing:
    """PolyFile-based forcing. VALUE requires METHOD=4; no VALUE uses METHOD=1."""
    method = "4" if value is not None else "1"
    return ExtOldForcing(
        quantity=quantity,
        filename=path,
        filetype=9,
        method=method,
        operand=Operand.override,
        value=value,
    )


def _make_tim_forcing(
    path: Path,
    quantity=ExtOldLateralQuantity.LateralDischarge,
) -> ExtOldForcing:
    """TimModel-based forcing (filetype=1, method=1, no VALUE)."""
    return ExtOldForcing(
        quantity=quantity,
        filename=path,
        filetype=1,
        method="1",
        operand=Operand.override,
    )


def _make_diskonly_forcing(
    path: Optional[Path],
    quantity=ExtOldLateralQuantity.LateralDischarge,
    *,
    value: float = 5.0,
) -> ExtOldForcing:
    """DiskOnlyFileModel-based forcing (filetype=4, method=4 required for VALUE)."""
    return ExtOldForcing(
        quantity=quantity,
        filename=DiskOnlyFileModel(path),
        filetype=4,
        method="4",
        operand=Operand.override,
        value=value,
    )


def _minimal_forcing_model(tmp_path: Path) -> ForcingModel:
    ts = TimeSeries(
        name="lateral",
        quantityunitpair=[
            QuantityUnitPair(quantity="time", unit=TIME_UNIT),
            QuantityUnitPair(quantity="discharge", unit="m3/s"),
        ],
        datablock=[[0.0, 1.0], [60.0, 2.0]],
        timeinterpolation=TimeInterpolation.linear,
    )
    fm = ForcingModel(forcing=[ts])
    fm.filepath = tmp_path / "lateral.bc"
    return fm


@pytest.fixture
def converter(tmp_path: Path) -> LateralConverter:
    c = LateralConverter()
    c.root_dir = tmp_path
    return c


@pytest.fixture
def mdu_parser_mock() -> MagicMock:
    mock = MagicMock(spec=MDUParser)
    mock.temperature_salinity_data = {"refdate": TIME_UNIT}
    return mock


@pytest.fixture
def converter_with_mdu(tmp_path: Path, mdu_parser_mock: MagicMock) -> LateralConverter:
    return LateralConverter(root_dir=tmp_path, mdu_parser=mdu_parser_mock)


@pytest.fixture
def tim_file(tmp_path: Path) -> Path:
    return _make_tim_file(tmp_path, stem="lateral")


@pytest.fixture
def pli_file(tmp_path: Path) -> Path:
    return _make_pli_file(tmp_path, stem="lateral")


class TestQuantityToLocationTypeMapping:
    """Verify that each lateral quantity produces the correct locationtype."""

    @pytest.mark.parametrize(
        "quantity, expected_location_type",
        [
            pytest.param(
                ExtOldLateralQuantity.LateralDischarge,
                None,
                id="lateraldischarge_no_location_type",
            ),
            pytest.param(
                ExtOldLateralQuantity.LateralDischarge1D,
                "1d",
                id="lateraldischarge1d_location_type_1d",
            ),
            pytest.param(
                ExtOldLateralQuantity.LateralDischarge2D,
                "2d",
                id="lateraldischarge2d_location_type_2d",
            ),
        ],
    )
    def test_quantity_maps_to_location_type(
        self,
        converter: LateralConverter,
        pli_file: Path,
        quantity,
        expected_location_type: Optional[str],
    ):
        """Each lateral quantity maps to the correct locationtype on the Lateral block."""
        forcing = _make_pli_forcing(pli_file, quantity, value=5.0)
        lateral = converter.convert(forcing, time_unit=TIME_UNIT)
        assert isinstance(lateral, Lateral)
        assert lateral.locationtype == expected_location_type


class TestScalarDischarge:
    """``_get_discharge`` returns the VALUE float for non-PolyFile filenames."""

    @pytest.mark.parametrize(
        "discharge_value",
        [0.0, 10.5, -3.0, 1e-3],
        ids=["zero", "positive", "negative", "small"],
    )
    def test_scalar_from_diskonly(
        self,
        converter: LateralConverter,
        tmp_path: Path,
        discharge_value: float,
    ):
        """A numeric VALUE with a non-PolyFile filename is returned as-is."""
        dummy = tmp_path / "dummy.xyz"
        dummy.write_text("")
        forcing = _make_diskonly_forcing(dummy, value=discharge_value)
        result = converter._get_discharge(forcing, TIME_UNIT)
        assert result == discharge_value

    @pytest.mark.parametrize(
        "quantity, discharge_value",
        [
            pytest.param(ExtOldLateralQuantity.LateralDischarge, 7.0, id="lateraldischarge"),
            pytest.param(ExtOldLateralQuantity.LateralDischarge1D, 7.0, id="lateraldischarge1d"),
            pytest.param(ExtOldLateralQuantity.LateralDischarge2D, 7.0, id="lateraldischarge2d"),
        ],
    )
    def test_scalar_all_quantities(
        self,
        converter: LateralConverter,
        tmp_path: Path,
        quantity,
        discharge_value: float,
    ):
        """Scalar discharge works for all three lateral quantities."""
        dummy = tmp_path / "dummy.xyz"
        dummy.write_text("")
        forcing = _make_diskonly_forcing(dummy, quantity, value=discharge_value)
        result = converter._get_discharge(forcing, TIME_UNIT)
        assert result == discharge_value


class TestDischargeFromTimFile:
    """``_get_discharge`` converts a TimModel filename to a ForcingModel."""

    @pytest.mark.parametrize(
        "quantity",
        [
            pytest.param(ExtOldLateralQuantity.LateralDischarge, id="lateraldischarge"),
            pytest.param(ExtOldLateralQuantity.LateralDischarge1D, id="lateraldischarge1d"),
            pytest.param(ExtOldLateralQuantity.LateralDischarge2D, id="lateraldischarge2d"),
        ],
    )
    def test_produces_forcing_model(
        self,
        converter: LateralConverter,
        tim_file: Path,
        quantity,
    ):
        """A TimModel filename is converted to a ForcingModel."""
        forcing = _make_tim_forcing(tim_file, quantity)
        result = converter._get_discharge(forcing, TIME_UNIT)
        assert isinstance(result, ForcingModel)

    def test_bc_path_uses_tim_stem(self, converter: LateralConverter, tim_file: Path):
        """The output .bc file is named after the TIM file stem."""
        forcing = _make_tim_forcing(tim_file)
        result = converter._get_discharge(forcing, TIME_UNIT)
        assert result.filepath.suffix == ".bc"
        assert result.filepath.stem == tim_file.stem

    def test_contains_one_time_series(self, converter: LateralConverter, tim_file: Path):
        """The produced ForcingModel contains exactly one time-series block."""
        forcing = _make_tim_forcing(tim_file)
        result = converter._get_discharge(forcing, TIME_UNIT)
        assert len(result.forcing) == 1
        # time column + discharge column
        assert len(result.forcing[0].quantityunitpair) == 2

    def test_marks_legacy_file(self, converter: LateralConverter, tim_file: Path):
        """The source TIM file is added to legacy_files."""
        forcing = _make_tim_forcing(tim_file)
        converter._get_discharge(forcing, TIME_UNIT)
        assert tim_file in converter.legacy_files

    def test_raises_without_time_unit(self, converter: LateralConverter, tim_file: Path):
        """Omitting ``time_unit`` when the discharge is a TIM file raises ValueError."""
        forcing = _make_tim_forcing(tim_file)
        with pytest.raises(ValueError, match="time_unit"):
            converter._get_discharge(forcing, time_unit=None)

    def test_uses_mdu_refdate_as_time_unit(
        self,
        converter_with_mdu: LateralConverter,
        tim_file: Path,
    ):
        """When time_unit resolved from MDU, the TIM is still converted."""
        forcing = _make_tim_forcing(tim_file)
        resolved_time_unit = converter_with_mdu._get_time_unit(None)
        result = converter_with_mdu._get_discharge(forcing, resolved_time_unit)
        assert isinstance(result, ForcingModel)


class TestDischargeFromPolyFileWithTim:
    """``_get_discharge`` finds and converts adjacent TIM files for PolyFile laterals."""

    def test_single_adjacent_tim(
        self,
        converter: LateralConverter,
        tmp_path: Path,
        pli_file: Path,
    ):
        """A PolyFile + adjacent .tim produces a ForcingModel discharge."""
        (tmp_path / "lateral.tim").write_text(TIM_CONTENT)
        forcing = _make_pli_forcing(pli_file)
        result = converter._get_discharge(forcing, TIME_UNIT)
        assert isinstance(result, ForcingModel)

    def test_multiple_adjacent_tims_are_merged(
        self,
        converter: LateralConverter,
        tmp_path: Path,
        pli_file: Path,
    ):
        """Multiple numbered TIM files are merged into a ForcingModel."""
        (tmp_path / "lateral_0001.tim").write_text(TIM_CONTENT)
        (tmp_path / "lateral_0002.tim").write_text(TIM_CONTENT)
        forcing = _make_pli_forcing(pli_file)
        result = converter._get_discharge(forcing, TIME_UNIT)
        assert isinstance(result, ForcingModel)
        assert len(result.forcing) == 2

    def test_marks_legacy_files(
        self,
        converter: LateralConverter,
        tmp_path: Path,
        pli_file: Path,
    ):
        """TIM files adjacent to the PolyFile are recorded in legacy_files."""
        tim_path = tmp_path / "lateral.tim"
        tim_path.write_text(TIM_CONTENT)
        forcing = _make_pli_forcing(pli_file)
        converter._get_discharge(forcing, TIME_UNIT)
        assert tim_path in converter.legacy_files

    def test_raises_without_time_unit(
        self,
        converter: LateralConverter,
        tmp_path: Path,
        pli_file: Path,
    ):
        """Omitting time_unit when PolyFile+TIM pair is used raises ValueError."""
        (tmp_path / "lateral.tim").write_text(TIM_CONTENT)
        forcing = _make_pli_forcing(pli_file)
        with pytest.raises(ValueError, match="time_unit"):
            converter._get_discharge(forcing, time_unit=None)

    def test_uses_mdu_refdate(
        self,
        converter_with_mdu: LateralConverter,
        tmp_path: Path,
        pli_file: Path,
    ):
        """When time_unit is None, MDU refdate drives the TIM-to-ForcingModel conversion."""
        (tmp_path / "lateral.tim").write_text(TIM_CONTENT)
        forcing = _make_pli_forcing(pli_file)
        resolved = converter_with_mdu._get_time_unit(None)
        result = converter_with_mdu._get_discharge(forcing, resolved)
        assert isinstance(result, ForcingModel)


class TestDischargeFromPolyFileScalar:
    """When no adjacent TIM exists, ``_get_discharge`` falls back to forcing.value."""

    @pytest.mark.parametrize(
        "discharge_value",
        [0.0, 5.0, -2.5, 100.0],
        ids=["zero", "positive", "negative", "large"],
    )
    def test_scalar_fallback(
        self,
        converter: LateralConverter,
        pli_file: Path,
        discharge_value: float,
    ):
        """When a PolyFile has no adjacent TIM, forcing.value is returned as discharge."""
        forcing = _make_pli_forcing(pli_file, value=discharge_value)
        result = converter._get_discharge(forcing, TIME_UNIT)
        assert result == discharge_value

    def test_no_tim_no_value_raises(self, converter: LateralConverter, pli_file: Path):
        """When a PolyFile has no adjacent TIM and no VALUE, ValueError is raised."""
        forcing = _make_pli_forcing(pli_file, value=None)
        with pytest.raises(ValueError, match="Could not determine"):
            converter._get_discharge(forcing, time_unit=TIME_UNIT)


class TestConvertPolyFile:
    """Full ``convert()`` with PolyFile-based forcings."""

    @pytest.mark.parametrize(
        "quantity, expected_location_type",
        [
            pytest.param(ExtOldLateralQuantity.LateralDischarge, None, id="gen"),
            pytest.param(ExtOldLateralQuantity.LateralDischarge1D, "1d", id="1d"),
            pytest.param(ExtOldLateralQuantity.LateralDischarge2D, "2d", id="2d"),
        ],
    )
    def test_scalar_discharge(
        self,
        converter: LateralConverter,
        pli_file: Path,
        quantity,
        expected_location_type: Optional[str],
    ):
        """convert() with a PolyFile + scalar value produces a valid Lateral."""
        forcing = _make_pli_forcing(pli_file, quantity, value=5.0)
        lateral = converter.convert(forcing, time_unit=TIME_UNIT)
        assert isinstance(lateral, Lateral)
        assert lateral.discharge == 5.0
        assert lateral.locationtype == expected_location_type
        assert lateral.locationfile is not None

    @pytest.mark.parametrize(
        "discharge_value",
        [0.0, 5.0, -2.5],
        ids=["zero", "positive", "negative"],
    )
    def test_various_scalar_values(
        self,
        converter: LateralConverter,
        pli_file: Path,
        discharge_value: float,
    ):
        """Various scalar discharge values are preserved in the resulting Lateral."""
        forcing = _make_pli_forcing(pli_file, value=discharge_value)
        lateral = converter.convert(forcing, time_unit=TIME_UNIT)
        assert lateral.discharge == discharge_value

    def test_scalar_sets_id_and_locationfile(
        self,
        converter: LateralConverter,
        pli_file: Path,
    ):
        """The id is derived from the PolyFile object name (equals the stem here); locationfile is set."""
        forcing = _make_pli_forcing(pli_file, value=3.0)
        lateral = converter.convert(forcing, time_unit=TIME_UNIT)
        # PLI_CONTENT uses "lateral" as both object name and file stem
        assert lateral.id == pli_file.stem
        assert lateral.locationfile is not None

    def test_adjacent_tim_produces_forcing_model(
        self,
        converter: LateralConverter,
        tmp_path: Path,
        pli_file: Path,
    ):
        """convert() with PolyFile + adjacent TIM produces a ForcingModel discharge."""
        (tmp_path / "lateral.tim").write_text(TIM_CONTENT)
        forcing = _make_pli_forcing(pli_file)
        lateral = converter.convert(forcing, time_unit=TIME_UNIT)
        assert isinstance(lateral, Lateral)
        assert isinstance(lateral.discharge, ForcingModel)
        assert lateral.locationfile is not None

    def test_multiple_tims_merged_into_forcing_model(
        self,
        converter: LateralConverter,
        tmp_path: Path,
        pli_file: Path,
    ):
        """Multiple adjacent TIM files are merged into a single ForcingModel."""
        (tmp_path / "lateral_0001.tim").write_text(TIM_CONTENT)
        (tmp_path / "lateral_0002.tim").write_text(TIM_CONTENT)
        forcing = _make_pli_forcing(pli_file)
        lateral = converter.convert(forcing, time_unit=TIME_UNIT)
        assert isinstance(lateral.discharge, ForcingModel)
        assert len(lateral.discharge.forcing) == 2

    def test_tim_raises_without_time_unit(
        self,
        converter: LateralConverter,
        tmp_path: Path,
        pli_file: Path,
    ):
        """Missing time_unit during convert() with adjacent TIM raises ValueError."""
        (tmp_path / "lateral.tim").write_text(TIM_CONTENT)
        forcing = _make_pli_forcing(pli_file)
        with pytest.raises(ValueError, match="time_unit"):
            converter.convert(forcing, time_unit=None)

    def test_named_object_id(self, converter: LateralConverter, tmp_path: Path):
        """The PolyFile object name overrides the file stem as the Lateral id."""
        pli_path = tmp_path / "myfile.pli"
        pli_path.write_text("my_named_lateral\n    1    2\n  0.0  0.0\n")
        forcing = _make_pli_forcing(pli_path, value=1.0)
        lateral = converter.convert(forcing, time_unit=TIME_UNIT)
        assert lateral.id == "my_named_lateral"

    def test_bc_path_derived_from_pli_stem(
        self,
        converter: LateralConverter,
        tmp_path: Path,
        pli_file: Path,
    ):
        """The output .bc path for a PolyFile-based TIM conversion uses the pli stem."""
        (tmp_path / "lateral.tim").write_text(TIM_CONTENT)
        forcing = _make_pli_forcing(pli_file)
        lateral = converter.convert(forcing, time_unit=TIME_UNIT)
        assert lateral.discharge.filepath.stem == pli_file.stem
        assert lateral.discharge.filepath.suffix == ".bc"


class TestGetLocationData:
    """``_get_location_data`` returns the correct id and locationfile fields."""

    def test_polyfile_has_locationfile_key(
        self,
        converter: LateralConverter,
        pli_file: Path,
    ):
        """A PolyFile filename results in a 'locationfile' key in location data."""
        forcing = _make_pli_forcing(pli_file, value=1.0)
        data = converter._get_location_data(forcing)
        assert "locationfile" in data
        assert data["locationfile"] == pli_file

    def test_polyfile_id_matches_object_name_or_stem(
        self,
        converter: LateralConverter,
        pli_file: Path,
    ):
        """The id is the first polyline-object name when present (here it equals the stem)."""
        forcing = _make_pli_forcing(pli_file, value=1.0)
        data = converter._get_location_data(forcing)
        # PLI_CONTENT defines the object name as "lateral", same as the file stem
        assert data["id"] == pli_file.stem

    def test_polyfile_named_object_overrides_stem(
        self,
        converter: LateralConverter,
        tmp_path: Path,
    ):
        """A named first polyline object overrides the file stem as id."""
        pli_path = tmp_path / "myfile.pli"
        pli_path.write_text("named_node\n    1    2\n  0.0  0.0\n")
        forcing = _make_pli_forcing(pli_path, value=1.0)
        data = converter._get_location_data(forcing)
        assert data["id"] == "named_node"

    def test_tim_model_id_is_stem(
        self,
        converter: LateralConverter,
        tim_file: Path,
    ):
        """For a TimModel filename, the stem becomes the id; no locationfile key."""
        forcing = _make_tim_forcing(tim_file)
        data = converter._get_location_data(forcing)
        assert data["id"] == tim_file.stem
        assert "locationfile" not in data

    def test_diskonly_id_is_stem(self, converter: LateralConverter, tmp_path: Path):
        """For a DiskOnlyFileModel with a filepath, the stem becomes the id."""
        dummy = tmp_path / "mynode.xyz"
        dummy.write_text("")
        forcing = _make_diskonly_forcing(dummy, value=1.0)
        data = converter._get_location_data(forcing)
        assert data["id"] == dummy.stem

    def test_diskonly_none_falls_back_to_quantity(self, converter: LateralConverter):
        """A DiskOnlyFileModel with filepath=None falls back to the quantity string."""
        forcing = _make_diskonly_forcing(None, value=1.0)
        data = converter._get_location_data(forcing)
        assert data["id"] == str(ExtOldLateralQuantity.LateralDischarge)


class TestGetTimeUnit:
    """``_get_time_unit`` returns the explicit value, falls back to MDU refdate, or None."""

    @pytest.mark.parametrize(
        "explicit_time_unit, mdu_refdate, expected",
        [
            pytest.param(TIME_UNIT, None, TIME_UNIT, id="explicit_used"),
            pytest.param(None, TIME_UNIT, TIME_UNIT, id="mdu_fallback"),
            pytest.param(None, None, None, id="both_none"),
            pytest.param(
                "minutes since 2020-01-01",
                TIME_UNIT,
                "minutes since 2020-01-01",
                id="explicit_overrides_mdu",
            ),
        ],
    )
    def test_get_time_unit(
        self,
        explicit_time_unit: Optional[str],
        mdu_refdate: Optional[str],
        expected: Optional[str],
    ):
        """_get_time_unit returns explicit value, falls back to MDU refdate, or None."""
        if mdu_refdate is not None:
            mock_mdu = MagicMock(spec=MDUParser)
            mock_mdu.temperature_salinity_data = {"refdate": mdu_refdate}
            c = LateralConverter(mdu_parser=mock_mdu)
        else:
            c = LateralConverter()
        assert c._get_time_unit(explicit_time_unit) == expected


class TestLateralDischargeFieldTypes:
    """The Lateral model accepts scalars, ForcingModel objects, and 'realtime' strings."""

    def test_accepts_scalar_float(self):
        """Lateral accepts a plain float as discharge."""
        lateral = Lateral(id="lat1", nodeid="node1", discharge=3.14)
        assert lateral.discharge == pytest.approx(3.14)

    def test_accepts_forcing_model(self, tmp_path: Path):
        """Lateral accepts a ForcingModel (bc-file) as discharge."""
        fm = _minimal_forcing_model(tmp_path)
        lateral = Lateral(id="lat1", nodeid="node1", discharge=fm)
        assert isinstance(lateral.discharge, ForcingModel)
        assert len(lateral.discharge.forcing) == 1

    def test_accepts_realtime_string(self):
        """The 'realtime' string is resolved to RealTime.realtime."""
        lateral = Lateral(id="lat1", nodeid="node1", discharge="realtime")
        assert lateral.discharge == RealTime.realtime

    @pytest.mark.parametrize(
        "realtime_str",
        ["REALTIME", "Realtime", "realtime", "RealTime"],
        ids=["upper", "mixed_lower", "lower", "mixed_upper"],
    )
    def test_realtime_case_insensitive(self, realtime_str: str):
        """The 'realtime' keyword is accepted regardless of capitalisation."""
        lateral = Lateral(id="lat1", nodeid="node1", discharge=realtime_str)
        assert lateral.discharge == RealTime.realtime

    def test_bc_file_from_converter_output(
        self,
        converter: LateralConverter,
        tmp_path: Path,
        pli_file: Path,
    ):
        """The ForcingModel produced by the converter is a valid 'bc file' discharge."""
        (tmp_path / "lateral.tim").write_text(TIM_CONTENT)
        forcing = _make_pli_forcing(pli_file)
        lateral = converter.convert(forcing, time_unit=TIME_UNIT)
        assert isinstance(lateral.discharge, ForcingModel)
        assert lateral.discharge.filepath.suffix == ".bc"


class TestLegacyFileTracking:
    """Verify that source files are added to ``legacy_files`` exactly when expected."""

    def test_after_tim_conversion(self, converter: LateralConverter, tim_file: Path):
        """The source TIM file appears in legacy_files after _get_discharge."""
        forcing = _make_tim_forcing(tim_file)
        converter._get_discharge(forcing, TIME_UNIT)
        assert tim_file in converter.legacy_files

    def test_after_polyfile_tim_conversion(
        self,
        converter: LateralConverter,
        tmp_path: Path,
        pli_file: Path,
    ):
        """Adjacent TIM files appear in legacy_files after full convert()."""
        tim_path = tmp_path / "lateral.tim"
        tim_path.write_text(TIM_CONTENT)
        forcing = _make_pli_forcing(pli_file)
        converter.convert(forcing, time_unit=TIME_UNIT)
        assert tim_path in converter.legacy_files

    def test_no_legacy_files_for_scalar_discharge(
        self,
        converter: LateralConverter,
        pli_file: Path,
    ):
        """Scalar-discharge conversions add no legacy files."""
        forcing = _make_pli_forcing(pli_file, value=5.0)
        converter.convert(forcing, time_unit=TIME_UNIT)
        assert converter.legacy_files == []


class TestErrorHandling:
    """Edge-case errors raised by ``convert()`` and ``_get_discharge()``."""

    def test_polyfile_no_tim_no_value_raises(
        self,
        converter: LateralConverter,
        pli_file: Path,
    ):
        """A PolyFile without a TIM and without a VALUE raises an error."""
        forcing = _make_pli_forcing(pli_file, value=None)
        with pytest.raises((ValueError, LateralError)):
            converter.convert(forcing, time_unit=TIME_UNIT)

    def test_polyfile_no_tim_no_value_error_message(
        self,
        converter: LateralConverter,
        pli_file: Path,
    ):
        """The error message for missing TIM / value references the file stem."""
        forcing = _make_pli_forcing(pli_file, value=None)
        with pytest.raises((ValueError, LateralError), match="lateral"):
            converter.convert(forcing, time_unit=TIME_UNIT)
