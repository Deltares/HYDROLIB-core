from hydrolib.core.dflowfm.t3d.models import T3DModel
from hydrolib.tools.extforce_convert.converters import T3DToForcingConverter
from tests.utils import test_input_dir

t3d_file_path = test_input_dir / "dflowfm_individual_files/t3d"


def test_convert():
    path = t3d_file_path / "sigma-5-layers-3-times.t3d"
    t3d_model = T3DModel(path)
    quantities_names = [
        "salinitybnd",
        "salinitybnd",
        "salinitybnd",
        "salinitybnd",
        "salinitybnd",
    ]
    units = ["ppt", "ppt", "ppt", "ppt", "ppt"]
    labels = ["sigma-5-layers-3-times"]
    t3d_forcing = T3DToForcingConverter.convert(
        [t3d_model], quantities_names, units, labels
    )
    t3d_forcing = t3d_forcing[0]
    units.insert(0, "seconds since 2006-01-01 00:00:00 +00:00")
    quantities_names.insert(0, "time")

    data_dict = t3d_model.as_dict()
    data_block = [[k] + v for k, v in data_dict.items()]

    assert t3d_forcing.name == "sigma-5-layers-3-times"
    assert t3d_forcing.vertpositions == t3d_model.layers
    assert t3d_forcing.vertpositiontype == "percBed"
    assert t3d_forcing.datablock == data_block
    quantities_list = t3d_forcing.quantityunitpair
    quantities_units = [quantity.unit for quantity in quantities_list]

    quantities_index = [quantity.vertpositionindex for quantity in quantities_list]
    quantities_names_1 = [quantity.quantity for quantity in quantities_list]

    assert len(quantities_list) == len(quantities_names)
    assert quantities_units == units
    assert quantities_index == [None, 1, 2, 3, 4, 5]
    assert quantities_names_1 == quantities_names
    assert t3d_forcing.timeinterpolation == "linear"
    assert t3d_forcing.vertinterpolation == "linear"
    assert t3d_forcing.offset == 0
    assert t3d_forcing.factor == 1
    assert t3d_forcing.function == "t3d"
