from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm.common.models import Operand
from hydrolib.core.dflowfm.ext.models import (
    Meteo,
    MeteoForcingFileType,
    MeteoInterpolationMethod,
)
from hydrolib.core.dflowfm.extold.models import ExtOldForcing, ExtOldQuantity
from hydrolib.tools.extforce_convert.converters import ConverterFactory, MeteoConverter


class TestConvertMeteo:
    def test_default(self):
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.WindX,
            filename="windtest.amu",
            filetype=4,
            method="2",
            operand="O",
        )

        new_quantity_block = MeteoConverter().convert(forcing)
        assert isinstance(new_quantity_block, Meteo)
        assert new_quantity_block.quantity == "windx"
        assert new_quantity_block.operand == Operand.override
        assert new_quantity_block.forcingfile == DiskOnlyFileModel("windtest.amu")
        assert new_quantity_block.forcingfiletype == MeteoForcingFileType.arcinfo
        assert (
            new_quantity_block.interpolationmethod
            == MeteoInterpolationMethod.linearSpaceTime
        )

    def test_nudge_salinity_temperature_uses_meteo_converter(self):
        """Test that nudge_salinity_temperature is converted to a Meteo block in the ext file."""
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.NudgeSalinityTemperature,
            filename="nudge_salinity_temperature.nc",
            filetype=11,
            method="3",
            operand="O",
        )

        converter = ConverterFactory.create_converter(forcing.quantity)
        assert isinstance(converter, MeteoConverter)

        new_quantity_block = converter.convert(forcing)
        assert isinstance(new_quantity_block, Meteo)
        assert new_quantity_block.quantity == "nudge_salinity_temperature"
        assert new_quantity_block.forcingfiletype == MeteoForcingFileType.netcdf
