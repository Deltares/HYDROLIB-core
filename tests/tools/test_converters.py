from hydrolib.core.dflowfm.extold.models import ExtOldForcing, ExtOldQuantity
from hydrolib.tools.ext_old_to_new.initial_condition_converter import (
    InitialConditionConverter,
)


def test_initial_condition_converter():
    forcing = ExtOldForcing(
        quantity=ExtOldQuantity.InitialWaterLevel,
        filename="iniwaterlevel.pol",
        filetype=10,  # "Polyline"
        method="4",  # "Interpolate space",
        operand="O",
    )

    new_quantity_block = InitialConditionConverter().convert(forcing)
    new_quantity_block.datafiletype = "polygon"
    new_quantity_block.interpolationmethod = "constant"
