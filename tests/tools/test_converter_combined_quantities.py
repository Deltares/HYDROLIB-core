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
    def test_uniform_tim_is_split_into_component_bc_blocks(
        self, tmp_path: Path, mdu_parser_mock: MagicMock
    ):
        # Strategy C: the combined quantity is split into one [Spatial] block per component,
        # each dataFileType=bcAscii, all sharing one .bc ForcingModel. Verified in D-Flow FM
        # on the Grevelingen model.
        forcing = _write_forcing(
            tmp_path,
            "humidity_airtemperature_cloudiness",
            "0.0 80.0 15.0 60.0\n60.0 82.0 16.5 62.0\n",
        )

        converter = CombinedQuantityConverter(
            mdu_parser=mdu_parser_mock, root_dir=tmp_path
        )
        blocks = converter.convert(forcing, tmp_path / "meteo.tim")

        assert isinstance(blocks, list)
        assert [b.quantity for b in blocks] == HUMIDITY_COMPONENTS
        assert all(b.datafiletype == DataFileType.bcascii for b in blocks)
        # all component blocks reference the one shared ForcingModel (.bc)
        shared = blocks[0].datafile
        assert isinstance(shared, ForcingModel)
        assert all(b.datafile is shared for b in blocks)
        assert shared.filepath == (tmp_path / "meteo.tim").with_suffix(".bc")

        # the shared .bc holds a single [Forcing] block: time + one column per component
        assert len(shared.forcing) == 1
        quantities = [qup.quantity for qup in shared.forcing[0].quantityunitpair]
        assert quantities == ["time", *HUMIDITY_COMPONENTS]
        # each .tim row is transposed to [time, *components] in declared order
        assert shared.forcing[0].datablock == [
            [0.0, 80.0, 15.0, 60.0],
            [60.0, 82.0, 16.5, 62.0],
        ]

        # the original .tim is converted away, so it is registered for removal
        assert (tmp_path / "meteo.tim") in converter.legacy_files

    def test_tem_extension_is_converted_to_bc(
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
        blocks = converter.convert(forcing, tem_file)

        assert [b.quantity for b in blocks] == HUMIDITY_COMPONENTS
        assert all(b.datafiletype == DataFileType.bcascii for b in blocks)
        assert blocks[0].datafile.filepath == tem_file.with_suffix(".bc")
        assert tem_file in converter.legacy_files

    def test_four_column_tim_is_split_into_four_blocks(
        self, tmp_path: Path, mdu_parser_mock: MagicMock
    ):
        components = [
            "dewpoint",
            "airtemperature",
            "cloudiness",
            "solarradiation",
        ]
        forcing = _write_forcing(
            tmp_path,
            "dewpoint_airtemperature_cloudiness_solarradiation",
            "0.0 10.0 15.0 60.0 300.0\n60.0 11.0 16.5 62.0 310.0\n",
        )

        converter = CombinedQuantityConverter(
            mdu_parser=mdu_parser_mock, root_dir=tmp_path
        )
        blocks = converter.convert(forcing, tmp_path / "meteo.tim")

        assert [b.quantity for b in blocks] == components
        assert all(b.datafiletype == DataFileType.bcascii for b in blocks)
        quantities = [qup.quantity for qup in blocks[0].datafile.forcing[0].quantityunitpair]
        assert quantities == ["time", *components]
        # each .tim row is transposed to [time, *components] in declared order
        assert blocks[0].datafile.forcing[0].datablock == [
            [0.0, 10.0, 15.0, 60.0, 300.0],
            [60.0, 11.0, 16.5, 62.0, 310.0],
        ]

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

    def test_old_ext_is_split_into_component_bc_blocks(self, model_copy: Path):
        converter = ExternalForcingConverter.from_mdu(model_copy / "model.mdu")
        ext_model, _ = converter.update()

        # the one combined quantity becomes one [Spatial] block per component
        assert [b.quantity for b in ext_model.spatial] == HUMIDITY_COMPONENTS
        assert all(b.datafiletype == DataFileType.bcascii for b in ext_model.spatial)
        # all blocks share one .bc ForcingModel carrying time + every component column
        shared = ext_model.spatial[0].datafile
        assert isinstance(shared, ForcingModel)
        assert all(b.datafile is shared for b in ext_model.spatial)
        quantities = [qup.quantity for qup in shared.forcing[0].quantityunitpair]
        assert quantities == ["time", *HUMIDITY_COMPONENTS]

    def test_saved_new_ext_writes_bc_and_drops_the_tim(self, model_copy: Path):
        converter = ExternalForcingConverter.from_mdu(model_copy / "model.mdu")
        converter.update()
        converter.save(backup=False)

        new_ext_text = (model_copy / "meteo_new.ext").read_text()
        assert "bcAscii" in new_ext_text
        for component in HUMIDITY_COMPONENTS:
            assert f"quantity             = {component}" in new_ext_text
        # a shared .bc was written next to the ext
        assert (model_copy / "meteo.bc").exists()

        # the .tim is converted away, so it is registered for removal
        assert (model_copy / "meteo.tim") in converter.legacy_files
