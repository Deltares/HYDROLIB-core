import pytest

from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm import Operand
from hydrolib.core.dflowfm.ext.models import Spatial
from hydrolib.core.dflowfm.extold.models import (
    ExtOldForcing,
    ExtOldInitialConditionQuantity,
    ExtOldMeteoQuantity,
    ExtOldParametersQuantity,
    ExtOldQuantity,
)
from hydrolib.core.dflowfm.inifield import DataFileType, InterpolationMethod
from hydrolib.tools.extforce_convert.converters import (
    ConverterFactory,
    SpatialConverter,
)


class TestConvertSpatial:
    def test_default(self):
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.WindX,
            filename="windtest.amu",
            filetype=4,
            method="2",
            operand="O",
        )

        new_quantity_block = SpatialConverter().convert(forcing, forcing.filename.filepath)
        assert isinstance(new_quantity_block, Spatial)
        assert new_quantity_block.quantity == "windx"
        assert new_quantity_block.operand == Operand.override
        assert new_quantity_block.datafile == DiskOnlyFileModel("windtest.amu")
        assert new_quantity_block.datafiletype == DataFileType.arcinfo
        assert (
            new_quantity_block.interpolationmethod
            == InterpolationMethod.linear_space_time
        )

    @pytest.mark.parametrize(
        "quantity",
        list(
            dict.fromkeys(
                [q.value for q in ExtOldInitialConditionQuantity]
                + [q.value for q in ExtOldParametersQuantity]
                + [q.value for q in ExtOldMeteoQuantity]
            )
        ),
    )
    def test_all_spatial_quantities_use_spatial_converter(self, quantity):
        """All InitialCondition, Parameter, and Meteo quantities are routed to
        SpatialConverter by the factory and produce a Spatial block when converted."""
        forcing = ExtOldForcing(
            quantity=quantity,
            filename="dummy.xyz",
            filetype=7,
            method="5",
            operand="O",
        )

        converter = ConverterFactory.create_converter(forcing.quantity)
        assert isinstance(converter, SpatialConverter)

        result = converter.convert(forcing, forcing.filename.filepath)
        assert isinstance(result, Spatial)
