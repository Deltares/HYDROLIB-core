import os
from pathlib import Path

from hydrolib.core.dflowfm.bc.models import (
    ForcingModel,
    QuantityUnitPair,
    TimeInterpolation,
    TimeSeries,
)
from hydrolib.core.dflowfm.extold.models import ExtOldForcing
from hydrolib.core.dflowfm.polyfile.models import PolyFile
from hydrolib.core.dflowfm.tim.models import TimModel


def bnd_old_to_new(pli_file_name: Path, bnd_quantity: str, supported_quantities):
    poly_file = PolyFile(pli_file_name)
    print(poly_file)
    num_points = len(poly_file.objects[0].points)
    base_name = pli_file_name.stem
    bc_model = ForcingModel()
    for i in range(num_points):
        pli_point_label = f"{base_name}_{i+1:04}"
        tim_file_name = pli_file_name.parent / (pli_point_label + ".tim")
        if tim_file_name.is_file():
            tim_model = TimModel(tim_file_name)
            time_data = {}
            time_data["timeInterpolation"] = TimeInterpolation.linear
            time_data["name"] = pli_point_label
            time_data["quantityunitpair"] = [
                QuantityUnitPair(quantity="time", unit="minutes since 2000-01-01"),
                QuantityUnitPair(
                    quantity=bnd_quantity,
                    unit=supported_quantities.get(bnd_quantity, "-"),
                ),
            ]
            time_data["datablock"] = [
                [str(record.time), str(record.data[0])]
                for record in tim_model.timeseries
            ]
            bc_model.forcing.append(TimeSeries(**time_data))
    bc_model.filepath = pli_file_name.parent / (base_name + "_" + bnd_quantity + ".bc")
    bc_file = bc_model.filepath
    bc_model.save()
    return bc_file
