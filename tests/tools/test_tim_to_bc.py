from pathlib import Path

from hydrolib.core.dflowfm.tim.models import TimModel
from hydrolib.tools.ext_old_to_new.converters import TimToForcingConverter


def test_tim_to_bc_converter(input_files_dir: Path):
    filepath = input_files_dir / "source-sink/tim-5-columns.tim"
    user_defined_names = [
        "any-name-1",
        "any-name-2",
        "any-name-3",
        "any-name-4",
        "any-name-5",
    ]
    tim_model = TimModel(filepath, user_defined_names)

    units = ["m³/s", "m", "C", "ppt", "check-later"]
    start_time = "minutes since 2015-01-01 00:00:00"
    df = tim_model.as_dataframe()
    converter = TimToForcingConverter()
    forcing_model = converter.convert(
        tim_model=tim_model,
        start_time=start_time,
        units=units,
        user_defined_names=user_defined_names,
    )

    assert len(forcing_model) == 5
    assert [forcing_model[i].forcing[0].name for i in range(5)] == user_defined_names
    assert [
        forcing_model[i].forcing[0].quantityunitpair[1].unit for i in range(5)
    ] == units
    forcing = forcing_model[0].forcing[0]
    assert forcing.datablock[0] == df.index.tolist()
    assert forcing.datablock[1] == df.iloc[:, 0].tolist()
