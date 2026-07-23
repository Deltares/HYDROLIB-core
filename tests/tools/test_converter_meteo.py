import pytest

from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm.common.models import Operand
from hydrolib.core.dflowfm.ext.models import (
    Meteo,
    MeteoForcingFileType,
    MeteoInterpolationMethod,
)
from hydrolib.core.dflowfm.extold.models import ExtOldForcing, ExtOldQuantity
from hydrolib.tools.extforce_convert.converters import MeteoConverter


class TestConvertMeteo:
    def test_default(self):
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.WindX,
            filename="windtest.amu",
            filetype=4,
            method="2",
            operand="override",
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


_LEGACY_OPERAND_CASES = [
    pytest.param("O", Operand.override, id="O->override"),
    pytest.param("A", Operand.override_if_missing, id="A->overrideIfMissing"),
    pytest.param("+", Operand.add, id="+->add"),
    pytest.param("*", Operand.multiply, id="*->multiply"),
    pytest.param("X", Operand.maximum, id="X->maximum"),
    pytest.param("N", Operand.minimum, id="N->minimum"),
]

class TestMeteoLegacyOperandConversion:
    """Tests that legacy single-character OPERAND values in old .ext files
    are correctly converted to modern Operand enum values when loading."""

    @pytest.mark.parametrize("legacy_operand, expected_operand", _LEGACY_OPERAND_CASES)
    def test_legacy_operand_in_file_is_converted_correctly(
            self,
            legacy_operand: str,
            expected_operand: Operand,
    ):
        """Loading an old ext file with a legacy OPERAND value yields the correct modern Operand."""
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.WindX,
            filename="windtest.amu",
            filetype=4,
            method="2",
            operand=legacy_operand,
        )
        new_quantity_block = MeteoConverter().convert(forcing)

        assert new_quantity_block.operand == expected_operand

