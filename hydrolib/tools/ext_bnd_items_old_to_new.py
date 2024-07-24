from pathlib import Path

from hydrolib.core.dflowfm.ext.models import Boundary, ExtModel
from hydrolib.core.dflowfm.extold.models import ExtOldModel
from hydrolib.tools.bnd_old_to_new import bnd_old_to_new


def ext_bnd_items_old_to_new(
    ext_force_old_filename: Path, ext_force_new_filename: Path, supported_quantities
):
    ext_old_force_model = ExtOldModel(ext_force_old_filename)
    if ext_force_new_filename.exists():
        ext_force_new_model = ExtModel(ext_force_new_filename)
    else:
        ext_force_new_model = ExtModel()
        ext_force_new_model.filepath = ext_force_new_filename

    forcingList = [
        item
        for item in ext_old_force_model.forcing
        if supported_quantities.get(item.quantity, -1) != -1
    ]
    for forcing in forcingList:
        bc_file = bnd_old_to_new(
            ext_force_old_filename.parent / forcing.filename.filepath,
            forcing.quantity,
            supported_quantities,
        )
        boundary_data = {}
        boundary_data["quantity"] = forcing.quantity
        boundary_data["forcingFile"] = str(bc_file)
        boundary_data["locationFile"] = str(forcing.filename.filepath)
        ext_force_new_model.boundary.append(Boundary(**boundary_data))
    ext_force_new_model.save()
    ext_old_force_model.forcing = [
        item
        for item in ext_old_force_model.forcing
        if supported_quantities.get(item.quantity, -1) == -1
    ]
    ext_old_force_model.save()
    return 0
