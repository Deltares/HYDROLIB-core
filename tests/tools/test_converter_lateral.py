from pathlib import Path
import shutil
from unittest.mock import MagicMock

import pytest

from hydrolib.core.dflowfm.common.models import Operand
from hydrolib.core.dflowfm.ext.models import ForcingModel, Lateral, LateralError
from hydrolib.core.dflowfm.extold.models import ExtOldFileType, ExtOldForcing, ExtOldMethod
from hydrolib.core.dflowfm.tim.models import TimModel
from hydrolib.tools.extforce_convert.converters import LateralConverter
from hydrolib.tools.extforce_convert.main_converter import ExternalForcingConverter
from hydrolib.tools.extforce_convert.mdu_parser import MDUParser
from tests.utils import compare_two_files, ignore_version_lines


@pytest.fixture
def start_date() -> str:
	return "minutes since 2015-01-01 00:00:00"


@pytest.fixture
def mdu_parser_mock(start_date: str) -> MagicMock:
	mock = MagicMock(spec=MDUParser)
	mock.temperature_salinity_data = {"refdate": start_date}
	return mock


@pytest.fixture
def lateral_files_dir(input_files_dir: Path) -> Path:
	return (input_files_dir / "lateral").resolve()


@pytest.fixture(autouse=True)
def set_working_directory(monkeypatch: pytest.MonkeyPatch, lateral_files_dir: Path):
	monkeypatch.chdir(lateral_files_dir)


@pytest.fixture
def lateral_poly_file(lateral_files_dir: Path) -> Path:
	return Path("lateral.pli")


@pytest.fixture
def lateral_tim_file(lateral_files_dir: Path) -> Path:
	return Path("lateral.tim")


@pytest.fixture
def lateral_ext_file(lateral_files_dir: Path) -> Path:
	return lateral_files_dir / "lateral.ext"


@pytest.fixture
def lateral_expected_ext_file(lateral_files_dir: Path) -> Path:
	return lateral_files_dir / "lateral-new.ext"


@pytest.fixture
def river_poly_file(lateral_files_dir: Path) -> Path:
	return Path("river.pli")


@pytest.fixture
def river_tim_files(lateral_files_dir: Path) -> list[Path]:
	return [
		Path("river_0001.tim"),
		Path("river_0002.tim"),
	]


@pytest.fixture
def missing_poly_file(lateral_files_dir: Path) -> Path:
	return Path("missing.pli")


@pytest.fixture
def converter(lateral_files_dir: Path, mdu_parser_mock: MagicMock) -> LateralConverter:
	converter = LateralConverter(mdu_parser=mdu_parser_mock)
	converter.root_dir = lateral_files_dir
	return converter


def _make_poly_forcing(quantity: str, poly_path: Path, value: float | None = None) -> ExtOldForcing:
	kwargs = dict(
		quantity=quantity,
		filename=poly_path,
		filetype=ExtOldFileType.Polyline,
		method=(ExtOldMethod.InterpolateSpace if value is not None else ExtOldMethod.PassThrough),
		operand=Operand.override,
	)
	if value is not None:
		kwargs["value"] = value
	return ExtOldForcing(**kwargs)


@pytest.mark.parametrize(
	"quantity",
	[
		pytest.param("lateraldischarge", id="all"),
		pytest.param("LATERALDISCHARGE1D", id="1d-uppercase"),
		pytest.param("lateraldischarge2d", id="2d"),
	],
)
def test_check_lateral_quantity_accepts_supported_values(quantity: str):
	LateralConverter.check_lateral_quantity(quantity)


@pytest.mark.parametrize(
	"quantity",
	[
		pytest.param("waterlevelbnd", id="boundary"),
		pytest.param("lateral", id="partial-name"),
		pytest.param("unsupported", id="unknown"),
	],
)
def test_check_lateral_quantity_raises_for_unsupported_values(quantity: str):
	with pytest.raises(LateralError, match="Unsupported lateral quantity"):
		LateralConverter.check_lateral_quantity(quantity)


def test_convert_tim_to_bc(start_date: str, lateral_tim_file: Path):
	tim_model = TimModel(lateral_tim_file, quantities_names=["discharge"])

	result = LateralConverter.convert_tim_to_bc(
		tim_model,
		start_date,
		user_defined_names=["lat_001"],
	)

	assert isinstance(result, ForcingModel)
	assert [forcing.name for forcing in result.forcing] == ["lat_001"]
	assert result.forcing[0].quantityunitpair[0].unit == start_date
	assert result.forcing[0].quantityunitpair[1].quantity == "discharge"
	assert result.forcing[0].datablock == [[0.0, 1.0], [60.0, 2.0]]


class TestLateralConverter:
	@pytest.mark.parametrize(
		"quantity, expected_location_type",
		[
			pytest.param("lateraldischarge", "all", id="all"),
			pytest.param("lateraldischarge1d", "1d", id="1d"),
			pytest.param("lateraldischarge2d", "2d", id="2d"),
		],
	)
	def test_convert_constant_polyfile(
		self,
		converter: LateralConverter,
		lateral_poly_file: Path,
		quantity: str,
		expected_location_type: str,
	):
		forcing = _make_poly_forcing(quantity, lateral_poly_file, value=1.23)

		result = converter.convert(forcing)

		assert isinstance(result, Lateral)
		assert result.name == quantity
		assert result.id == "lat_node"
		assert result.locationtype == expected_location_type
		assert result.locationfile.filepath == lateral_poly_file
		assert result.discharge == pytest.approx(1.23)

	def test_convert_polyfile_with_single_tim_file(
		self,
		converter: LateralConverter,
		lateral_poly_file: Path,
		lateral_tim_file: Path,
	):
		forcing = _make_poly_forcing("lateraldischarge", lateral_poly_file)

		result = converter.convert(forcing)

		assert isinstance(result, Lateral)
		assert result.locationfile.filepath == lateral_poly_file
		assert isinstance(result.discharge, ForcingModel)
		assert result.discharge.filepath == lateral_poly_file.with_suffix(".bc")
		assert [series.name for series in result.discharge.forcing] == ["lateral"]
		assert result.discharge.forcing[0].quantityunitpair[0].unit == "minutes since 2015-01-01 00:00:00"
		assert result.discharge.forcing[0].datablock == [[0.0, 1.0], [60.0, 2.0]]
		assert [path.name for path in converter.legacy_files] == [lateral_tim_file.name]

	def test_convert_polyfile_with_multiple_tim_files_creates_multiple_series(
		self,
		converter: LateralConverter,
		river_poly_file: Path,
		river_tim_files: list[Path],
	):
		forcing = _make_poly_forcing("lateraldischarge", river_poly_file)

		result = converter.convert(forcing)

		assert isinstance(result.discharge, ForcingModel)
		assert [series.name for series in result.discharge.forcing] == [
			"river_0001",
			"river_0002",
		]
		assert result.discharge.forcing[0].datablock == [[0.0, 1.0], [60.0, 2.0]]
		assert result.discharge.forcing[1].datablock == [[0.0, 3.0], [60.0, 4.0]]
		assert [path.name for path in converter.legacy_files] == [
			path.name for path in river_tim_files
		]

	@pytest.mark.parametrize(
		"salinity, temperature, n_columns, expected_quantities",
		[
			pytest.param(1, True, 3, ["discharge", "salinity", "temperature"], id="salinity-and-temperature"),
			pytest.param(1, False, 2, ["discharge", "salinity"], id="salinity-only"),
			pytest.param(0, True, 2, ["discharge", "temperature"], id="temperature-only"),
		],
	)
	def test_convert_polyfile_with_transport_columns_preserves_transport_forcings(
		self,
		tmp_path: Path,
		lateral_files_dir: Path,
		mdu_parser_mock: MagicMock,
		salinity: int,
		temperature: bool,
		n_columns: int,
		expected_quantities: list[str],
	):
		shutil.copy2(lateral_files_dir / "lateral.pli", tmp_path / "lateral.pli")
		extra = " 10.0 25.0"[: 5 * (n_columns - 1)]
		(tmp_path / "lateral_0001.tim").write_text(
			f"0.0 1.0{extra}\n60.0 2.0{extra}\n"
		)
		mdu_parser_mock.temperature_salinity_data = {
			"refdate": "minutes since 2015-01-01 00:00:00",
			"salinity": salinity,
			"temperature": temperature,
		}
		converter = LateralConverter(mdu_parser=mdu_parser_mock, root_dir=tmp_path)
		forcing = _make_poly_forcing("lateraldischarge", Path("lateral.pli"))

		result = converter.convert(forcing)

		assert isinstance(result.discharge, ForcingModel)
		assert result.applytransport == 1
		assert [series.name for series in result.discharge.forcing] == ["lateral"] * len(expected_quantities)
		assert [series.quantityunitpair[1].quantity for series in result.discharge.forcing] == expected_quantities
		assert result.discharge.forcing[0].datablock == [[0.0, 1.0], [60.0, 2.0]]
		assert result.discharge.forcing[1].datablock == [[0.0, 10.0], [60.0, 10.0]]
		if "salinity" in expected_quantities:
			assert isinstance(result.salinity, ForcingModel)
		else:
			assert result.salinity is None
		if "temperature" in expected_quantities:
			index = expected_quantities.index("temperature")
			assert isinstance(result.temperature, ForcingModel)
			assert result.discharge.forcing[index].datablock == [[0.0, 25.0], [60.0, 25.0]]
		else:
			assert result.temperature is None

	def test_convert_polyfile_with_single_column_and_transport_enabled(
		self,
		tmp_path: Path,
		lateral_files_dir: Path,
		mdu_parser_mock: MagicMock,
	):
		shutil.copy2(lateral_files_dir / "lateral.pli", tmp_path / "lateral.pli")
		(tmp_path / "lateral_0001.tim").write_text("0.0 -1.0\n60.0 -2.0\n")
		mdu_parser_mock.temperature_salinity_data = {
			"refdate": "minutes since 2015-01-01 00:00:00",
			"salinity": 1,
			"temperature": True,
		}
		converter = LateralConverter(mdu_parser=mdu_parser_mock, root_dir=tmp_path)
		forcing = _make_poly_forcing("lateraldischarge", Path("lateral.pli"))

		result = converter.convert(forcing)

		assert result.discharge.forcing[0].datablock == [[0.0, -1.0], [60.0, -2.0]]
		assert result.salinity is None
		assert result.temperature is None
		assert result.applytransport is None

	def test_convert_polyfile_with_multiple_tim_files_and_transport_columns(
		self,
		tmp_path: Path,
		lateral_files_dir: Path,
		mdu_parser_mock: MagicMock,
	):
		shutil.copy2(lateral_files_dir / "river.pli", tmp_path / "river.pli")
		(tmp_path / "river_0001.tim").write_text("0.0 1.0 10.0 25.0\n60.0 2.0 11.0 26.0\n")
		(tmp_path / "river_0002.tim").write_text("0.0 3.0 30.0 45.0\n60.0 4.0 31.0 46.0\n")
		mdu_parser_mock.temperature_salinity_data = {
			"refdate": "minutes since 2015-01-01 00:00:00",
			"salinity": 1,
			"temperature": True,
		}
		converter = LateralConverter(mdu_parser=mdu_parser_mock, root_dir=tmp_path)
		forcing = _make_poly_forcing("lateraldischarge", Path("river.pli"))

		result = converter.convert(forcing)

		assert isinstance(result.discharge, ForcingModel)
		assert isinstance(result.salinity, ForcingModel)
		assert isinstance(result.temperature, ForcingModel)
		assert result.applytransport == 1
		assert [series.name for series in result.discharge.forcing] == [
			"river_0001",
			"river_0001",
			"river_0001",
			"river_0002",
			"river_0002",
			"river_0002",
		]
		assert [series.quantityunitpair[1].quantity for series in result.discharge.forcing] == [
			"discharge",
			"salinity",
			"temperature",
			"discharge",
			"salinity",
			"temperature",
		]
		assert result.discharge.forcing[0].datablock == [[0.0, 1.0], [60.0, 2.0]]
		assert result.discharge.forcing[1].datablock == [[0.0, 10.0], [60.0, 11.0]]
		assert result.discharge.forcing[2].datablock == [[0.0, 25.0], [60.0, 26.0]]
		assert result.discharge.forcing[3].datablock == [[0.0, 3.0], [60.0, 4.0]]
		assert result.discharge.forcing[4].datablock == [[0.0, 30.0], [60.0, 31.0]]
		assert result.discharge.forcing[5].datablock == [[0.0, 45.0], [60.0, 46.0]]

	def test_convert_polyfile_with_unexpected_number_of_columns_raises(
		self,
		tmp_path: Path,
		lateral_files_dir: Path,
		mdu_parser_mock: MagicMock,
	):
		shutil.copy2(lateral_files_dir / "lateral.pli", tmp_path / "lateral.pli")
		(tmp_path / "lateral_0001.tim").write_text("0.0 1.0 10.0 25.0\n60.0 2.0 10.0 25.0\n")
		mdu_parser_mock.temperature_salinity_data = {
			"refdate": "minutes since 2015-01-01 00:00:00",
			"salinity": 0,
			"temperature": False,
		}
		converter = LateralConverter(mdu_parser=mdu_parser_mock, root_dir=tmp_path)
		forcing = _make_poly_forcing("lateraldischarge", Path("lateral.pli"))

		with pytest.raises(LateralError, match="has 3 data columns"):
			converter.convert(forcing)

	def test_convert_polyfile_without_value_or_tim_raises_value_error(
		self,
		converter: LateralConverter,
		missing_poly_file: Path,
	):
		forcing = _make_poly_forcing("lateraldischarge", missing_poly_file)

		with pytest.raises(ValueError, match="Could not determine the discharge"):
			converter.convert(forcing)


class TestMainConverter:
	def test_lateral_ext_conversion_matches_expected_results(
		self,
		tmp_path: Path,
		lateral_files_dir: Path,
		lateral_ext_file: Path,
		lateral_expected_ext_file: Path,
		mdu_parser_mock: MagicMock,
	):
		workspace = tmp_path / "lateral"
		workspace.mkdir()

		for name in [
			"lateral.ext",
			"afstroming.pol",
			"afstroming.tim",
			"rainfall_minus_evaporation.pol",
			"rainfall_minus_evaporation.tim",
		]:
			shutil.copy2(lateral_files_dir / name, workspace / name)

		input_file = workspace / lateral_ext_file.name
		output_file = workspace / "lateral-new.ext"
		mdu_parser_mock.mdu_path = workspace / "mock.mdu"

		converter = ExternalForcingConverter(
			extold_model=input_file,
			ext_file=output_file,
			mdu_parser=mdu_parser_mock,
		)
		result = converter.update()
		assert result is not None
		ext_model, structure_model = result
		converter.save(backup=False, recursive=True)

		assert len(ext_model.lateral) == 2
		assert len(structure_model.structure) == 0
		assert output_file.exists()
		diff = compare_two_files(
			lateral_expected_ext_file,
			output_file,
			ignore_line=ignore_version_lines,
		)
		assert diff == []

