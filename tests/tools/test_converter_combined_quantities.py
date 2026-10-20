import shutil
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from hydrolib.core.dflowfm.bc.models import ForcingModel, TimeInterpolation
from hydrolib.core.dflowfm.ext.models import Spatial, SpatialError
from hydrolib.core.dflowfm.extold.models import ExtOldForcing
from hydrolib.core.dflowfm.inifield import DataFileType
from hydrolib.tools.extforce_convert.converters import (
    CombinedQuantityConverter,
    ConverterFactory,
    SpatialConverter,
)
from hydrolib.tools.extforce_convert.main_converter import ExternalForcingConverter
from hydrolib.tools.extforce_convert.mdu_parser import MDUParser

HUMIDITY_COMPONENTS = ["humidity", "airtemperature", "cloudiness"]


@pytest.fixture
def mdu_parser_mock() -> MagicMock:
    mock = MagicMock(spec=MDUParser)
    mock.temperature_salinity_data = {"refdate": "minutes since 2001-01-01 00:00:00"}
    return mock


def _write_forcing(tmp_path: Path, quantity: str, rows: str, method: int = 0):
    tim_file = tmp_path / "meteo.tim"
    tim_file.write_text(rows)
    return ExtOldForcing(
        quantity=quantity,
        filename=tim_file,
        filetype=1,
        method=method,
        operand="O",
    )


class TestConverterFactory:
    @pytest.mark.parametrize(
        "quantity",
        [
            "humidity_airtemperature_cloudiness",
            "humidity_airtemperature_cloudiness_solarradiation",
            "dewpoint_airtemperature_cloudiness",
            "dewpoint_airtemperature_cloudiness_solarradiation",
            "airpressure_windx_windy",
            "airpressure_windx_windy_charnock",
            "airpressure_stressx_stressy",
        ],
    )
    def test_combined_quantity_gets_the_combined_converter(
        self, quantity: str, mdu_parser_mock: MagicMock
    ):
        converter = ConverterFactory.create_converter(
            quantity, mdu_parser=mdu_parser_mock
        )
        assert isinstance(converter, CombinedQuantityConverter)

    def test_other_meteo_quantity_keeps_the_spatial_converter(
        self, mdu_parser_mock: MagicMock
    ):
        converter = ConverterFactory.create_converter(
            "atmosphericpressure", mdu_parser=mdu_parser_mock
        )
        assert type(converter) is SpatialConverter


class TestCombinedQuantityUniformTim:
    def test_tim_is_kept_as_uniform(
        self, tmp_path: Path, mdu_parser_mock: MagicMock
    ):
        # The kernel's own new-style cases (e.g. test bench c176, c401_katwijk) keep the
        # uniform .tim/.tem and set dataFileType=uniform -- no .bc conversion.
        forcing = _write_forcing(
            tmp_path,
            "humidity_airtemperature_cloudiness",
            "0.0 80.0 15.0 60.0\n60.0 82.0 16.5 62.0\n",
        )

        converter = CombinedQuantityConverter(
            mdu_parser=mdu_parser_mock, root_dir=tmp_path
        )
        block = converter.convert(forcing, tmp_path / "meteo.tim")

        assert isinstance(block, Spatial)
        assert block.quantity == "humidity_airtemperature_cloudiness"
        assert block.datafiletype == DataFileType.uniform
        # the original .tim is kept as the data file, not converted to a ForcingModel/.bc
        assert not isinstance(block.datafile, ForcingModel)
        assert block.datafile.filepath == tmp_path / "meteo.tim"
        # the .tim is NOT removed, since the new ext still references it
        assert converter.legacy_files == []

    def test_tem_extension_is_kept(
        self, tmp_path: Path, mdu_parser_mock: MagicMock
    ):
        tem_file = tmp_path / "meteo.tem"
        tem_file.write_text("0.0 80.0 15.0 60.0\n60.0 82.0 16.5 62.0\n")
        forcing = ExtOldForcing(
            quantity="humidity_airtemperature_cloudiness",
            filename=tem_file,
            filetype=1,
            method=0,
            operand="O",
        )

        converter = CombinedQuantityConverter(
            mdu_parser=mdu_parser_mock, root_dir=tmp_path
        )
        block = converter.convert(forcing, tem_file)

        assert block.datafiletype == DataFileType.uniform
        assert block.datafile.filepath == tem_file

    def test_four_column_tim_is_accepted(
        self, tmp_path: Path, mdu_parser_mock: MagicMock
    ):
        forcing = _write_forcing(
            tmp_path,
            "dewpoint_airtemperature_cloudiness_solarradiation",
            "0.0 10.0 15.0 60.0 300.0\n60.0 11.0 16.5 62.0 310.0\n",
        )

        converter = CombinedQuantityConverter(
            mdu_parser=mdu_parser_mock, root_dir=tmp_path
        )
        block = converter.convert(forcing, tmp_path / "meteo.tim")

        assert block.datafiletype == DataFileType.uniform
        assert block.datafile.filepath == tmp_path / "meteo.tim"

    def test_wrong_column_count_raises_clear_error(
        self, tmp_path: Path, mdu_parser_mock: MagicMock
    ):
        forcing = _write_forcing(
            tmp_path,
            "humidity_airtemperature_cloudiness",
            "0.0 80.0 15.0\n60.0 82.0 16.5\n",
        )

        converter = CombinedQuantityConverter(
            mdu_parser=mdu_parser_mock, root_dir=tmp_path
        )
        with pytest.raises(SpatialError, match="expects 3 data columns"):
            converter.convert(forcing, tmp_path / "meteo.tim")

    def test_empty_tim_raises_clear_error(
        self, tmp_path: Path, mdu_parser_mock: MagicMock
    ):
        forcing = _write_forcing(tmp_path, "humidity_airtemperature_cloudiness", "")

        converter = CombinedQuantityConverter(
            mdu_parser=mdu_parser_mock, root_dir=tmp_path
        )
        with pytest.raises(SpatialError, match="contains no data rows"):
            converter.convert(forcing, tmp_path / "meteo.tim")


class TestCombinedQuantityOtherFileTypes:
    def test_netcdf_file_is_converted_like_any_spatial_quantity(
        self, tmp_path: Path, mdu_parser_mock: MagicMock
    ):
        nc_file = tmp_path / "meteo.nc"
        nc_file.write_text("")
        forcing = ExtOldForcing(
            quantity="humidity_airtemperature_cloudiness",
            filename=nc_file,
            filetype=11,
            method=3,
            operand="O",
        )

        converter = CombinedQuantityConverter(
            mdu_parser=mdu_parser_mock, root_dir=tmp_path
        )
        block = converter.convert(forcing, nc_file)

        assert block.datafiletype == DataFileType.netcdf
        assert block.datafile.filepath == nc_file
        assert converter.legacy_files == []

    def test_airpressure_netcdf_is_passed_through(
        self, tmp_path: Path, mdu_parser_mock: MagicMock
    ):
        # airpressure_* combined quantities are only ever supplied as curvi/spiderweb/netcdf
        # (never uniform), so the converter keeps the native file type and does not build a .bc.
        nc_file = tmp_path / "meteo.nc"
        nc_file.write_text("")
        forcing = ExtOldForcing(
            quantity="airpressure_windx_windy_charnock",
            filename=nc_file,
            filetype=11,
            method=3,
            operand="O",
        )

        converter = CombinedQuantityConverter(
            mdu_parser=mdu_parser_mock, root_dir=tmp_path
        )
        block = converter.convert(forcing, nc_file)

        assert block.quantity == "airpressure_windx_windy_charnock"
        assert block.datafiletype == DataFileType.netcdf
        assert block.datafile.filepath == nc_file
        assert not isinstance(block.datafile, ForcingModel)
        assert converter.legacy_files == []


@pytest.mark.e2e
class TestCombinedQuantityEndToEnd:
    @pytest.fixture
    def model_copy(self, tmp_path: Path, input_files_dir: Path) -> Path:
        """Copy the model to a temp dir so the conversion does not mutate the originals."""
        src = input_files_dir / "combined_quantities_tim"
        dst = tmp_path / src.name
        shutil.copytree(src, dst)
        return dst

    def test_old_ext_is_converted_to_one_uniform_spatial_block(self, model_copy: Path):
        converter = ExternalForcingConverter.from_mdu(model_copy / "model.mdu")
        ext_model, _ = converter.update()

        assert len(ext_model.spatial) == 1
        block = ext_model.spatial[0]
        assert block.quantity == "humidity_airtemperature_cloudiness"
        assert block.datafiletype == DataFileType.uniform
        assert block.datafile.filepath.name == "meteo.tim"

    def test_saved_new_ext_keeps_the_uniform_tim(self, model_copy: Path):
        converter = ExternalForcingConverter.from_mdu(model_copy / "model.mdu")
        converter.update()
        converter.save(backup=False)

        new_ext_text = (model_copy / "meteo_new.ext").read_text()
        assert "uniform" in new_ext_text
        assert "meteo.tim" in new_ext_text
        assert "bcAscii" not in new_ext_text

        # the .tim is still referenced by the new ext, so it must not be removed
        assert (model_copy / "meteo.tim").exists()
        assert (model_copy / "meteo.tim") not in converter.legacy_files
