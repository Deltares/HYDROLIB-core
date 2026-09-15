from pathlib import Path

from hydrolib.core.dflowfm.bc.models import ForcingModel
from hydrolib.core.dflowfm.tim.models import TimModel
from hydrolib.tools.extforce_convert.converters import TimToForcingConverter
from tests.utils import compare_two_files, ignore_version_lines


def test_tim_to_bc_converter(input_files_dir: Path, reference_files_dir: Path):
    filepath = input_files_dir / "source-sink/tim-5-columns.tim"
    user_defined_names = [
        "any-name-1",
        "any-name-2",
        "any-name-3",
        "any-name-4",
        "any-name-5",
    ]
    tim_model = TimModel(filepath, user_defined_names)

    units = ["m³/s", "m", "C", "ppt", "-"]
    time_unit = "minutes since 2015-01-01 00:00:00"
    df = tim_model.as_dataframe()
    converter = TimToForcingConverter()
    time_series_list = converter.convert(
        tim_model=tim_model,
        time_unit=time_unit,
        units=units,
        user_defined_names=user_defined_names,
    )

    assert len(time_series_list) == 5
    assert [time_series_list[i].name for i in range(5)] == user_defined_names
    assert [time_series_list[i].quantityunitpair[1].unit for i in range(5)] == units
    forcing = time_series_list[0]
    forcing_df = forcing.as_dataframe()
    assert forcing_df.index.tolist() == df.index.tolist()
    assert forcing_df.iloc[:, 0].tolist() == df.iloc[:, 0].tolist()
    # test saving to bc file.
    converted_bc_path = Path("tests/data/output/convert-tim-to-bc.bc")

    # convert the list of TimeSeries to Forcing Model to save to bc file, and check the saved file.
    forcing_model = ForcingModel(forcing=time_series_list)
    forcing_model.save(converted_bc_path)
    reference_bc = reference_files_dir / "bc/convert-tim-to-bc.bc"
    diff = compare_two_files(
        str(converted_bc_path), str(reference_bc), ignore_line=ignore_version_lines
    )
    assert diff == []
    converted_bc_path.unlink()


def test_tim_to_bc_converter_writes_vector_block(tmp_path: Path):
    tim_path = tmp_path / "seauxuy_0001.tim"
    tim_path.write_text("0 1 2\n123456 3 4\n")

    tim_model = TimModel(tim_path)
    tim_model.quantities_names = ["ux", "uy"]

    converter = TimToForcingConverter()
    forcing_list = converter.convert(
        tim_model=tim_model,
        time_unit="minutes since 2000-01-01 00:00:00 +00:00",
        units=["unused", "unused"],
        user_defined_names=["seauxuy"],
        vector_quantities={"uxuyadvectionvelocitybnd": {"ux": "m s-1", "uy": "m s-1"}},
    )

    forcing_model = ForcingModel(forcing=forcing_list)
    bc_path = tmp_path / "seauxuy.bc"
    forcing_model.save(bc_path)
    content = bc_path.read_text()

    assert "name              = seauxuy" in content
    assert "function          = timeseries" in content
    assert "vector            = uxuyadvectionvelocitybnd:ux,uy" in content
    assert "quantity          = ux" in content
    assert "unit              = m s-1" in content
    assert "quantity          = uy" in content
    assert "0.0       1.0  2.0" in content
    assert "123456.0  3.0  4.0" in content

