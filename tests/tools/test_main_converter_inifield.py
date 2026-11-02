import warnings
from pathlib import Path

import pytest

from hydrolib.core.dflowfm.ext.models import ExtModel
from hydrolib.tools.extforce_convert.main_converter import ExternalForcingConverter

MDU_TEMPLATE = """\
[General]
fileVersion = 1.09
fileType = modelDef

[geometry]
NetFile = net.nc
{inifield}
[time]
RefDate = 20200101
Tunit = S
DtUser = 60
TStart = 0
TStop = 3600

[physics]
Salinity = 0
Temperature = 0

[external forcing]
{extforce}
"""

INIFIELD = """\
[General]
fileVersion = 2.00
fileType = iniField

[Parameter]
quantity = frictionCoefficient
dataFile = a.xyz
dataFileType = sample
interpolationMethod = triangulation

[Initial]
quantity = waterlevel
dataFile = region.pol
dataFileType = polygon
interpolationMethod = constant
value = 1.5

[Parameter]
quantity = frictionCoefficient
dataFile = c.xyz
dataFileType = sample
interpolationMethod = triangulation
operand = *
"""

OLD_EXT = """\
QUANTITY     =initialtracerdTR1
FILENAME     =tracer.pol
FILETYPE     =10
METHOD       =4
OPERAND      =O
VALUE        =0
"""

POLYGON = """L1
     4     2
    -244.151184    1790.310059
    -228.566650    -617.508057
   10065.006836    -251.270264
    9994.876953    1868.232910
"""

NEW_EXT = """\
[General]
fileVersion = 2.01
fileType = extForce

[Spatial]
quantity = windspeedfactor
dataFile = wind.xyz
dataFileType = sample
"""


INIFIELD_TRACER = """[General]
fileVersion = 2.00
fileType = iniField

[Initial]
quantity = initialtracerX
dataFile = a.xyz
dataFileType = sample
interpolationMethod = triangulation
"""

NEW_EXT_BOUNDARY_TRACER = """[General]
fileVersion = 2.01
fileType = extForce

[Boundary]
quantity = tracerbndA
locationFile = a.pli
forcingFile = a.bc
"""


def _write_model(
    root: Path,
    *,
    inifield: bool = True,
    old_ext: bool = False,
    new_ext: bool = False,
    inifield_text: str = INIFIELD,
    new_ext_text: str = NEW_EXT,
) -> Path:
    extforce = []
    if old_ext:
        (root / "old.ext").write_text(OLD_EXT)
        (root / "tracer.pol").write_text(POLYGON)
        extforce.append("ExtForceFile = old.ext")
    if new_ext:
        (root / "new.ext").write_text(new_ext_text)
        extforce.append("ExtForceFileNew = new.ext")
    if inifield:
        (root / "inifield.ini").write_text(inifield_text)
    mdu = root / "model.mdu"
    mdu.write_text(
        MDU_TEMPLATE.format(
            inifield="IniFieldFile = inifield.ini\n" if inifield else "",
            extforce="\n".join(extforce),
        )
    )
    return mdu


def _convert(mdu: Path) -> ExternalForcingConverter:
    converter = ExternalForcingConverter.from_mdu(mdu)
    converter.update()
    converter.save(backup=False)
    return converter


def _spatial_blocks(ext_path: Path) -> list:
    return ExtModel(filepath=ext_path, recurse=False).spatial


class TestInifieldOnly:
    """The MDU has an inifield file and no old external forcings file."""

    def test_blocks_are_written_to_a_new_ext_file(self, tmp_path):
        converter = _convert(_write_model(tmp_path))

        blocks = _spatial_blocks(converter.ext_model.filepath)
        assert [b.quantity for b in blocks] == [
            "frictionCoefficient",
            "waterlevel",
            "frictionCoefficient",
        ]

    def test_file_order_of_initial_and_parameter_blocks_is_kept(self, tmp_path):
        converter = _convert(_write_model(tmp_path))

        blocks = _spatial_blocks(converter.ext_model.filepath)
        assert [b.operand for b in blocks] == ["override", "override", "multiply"]

    def test_polygon_value_block_uses_data_value(self, tmp_path):
        converter = _convert(_write_model(tmp_path))

        water_level = _spatial_blocks(converter.ext_model.filepath)[1]
        assert water_level.datavalue == 1.5
        assert water_level.targetmaskfile.filepath == Path("region.pol")

    def test_mdu_points_to_the_new_ext_file_and_drops_the_inifield(self, tmp_path):
        mdu = _write_model(tmp_path)

        converter = _convert(mdu)

        text = mdu.read_text().lower()
        assert "inifieldfile" not in text
        assert f"extforcefilenew" in text
        assert converter.ext_model.filepath.name in mdu.read_text()

    def test_the_inifield_file_itself_is_left_on_disk(self, tmp_path):
        _convert(_write_model(tmp_path))

        assert (tmp_path / "inifield.ini").is_file()

    def test_clean_removes_the_inifield_file(self, tmp_path):
        converter = _convert(_write_model(tmp_path))

        converter.clean()

        assert not (tmp_path / "inifield.ini").exists()


class TestInifieldWithOldAndNewExt:
    def test_inifield_blocks_come_before_the_converted_old_ext_blocks(self, tmp_path):
        converter = _convert(_write_model(tmp_path, old_ext=True))

        blocks = _spatial_blocks(converter.ext_model.filepath)
        assert [b.quantity for b in blocks] == [
            "frictionCoefficient",
            "waterlevel",
            "frictionCoefficient",
            "initialtracerdTR1",
        ]

    def test_inifield_blocks_come_before_pre_existing_new_ext_blocks(self, tmp_path):
        converter = _convert(_write_model(tmp_path, new_ext=True))

        blocks = _spatial_blocks(converter.ext_model.filepath)
        assert [b.quantity for b in blocks] == [
            "frictionCoefficient",
            "waterlevel",
            "frictionCoefficient",
            "windspeedfactor",
        ]

    def test_all_three_sources_follow_the_kernel_order(self, tmp_path):
        converter = _convert(_write_model(tmp_path, old_ext=True, new_ext=True))

        quantities = [
            b.quantity for b in _spatial_blocks(converter.ext_model.filepath)
        ]
        assert quantities[3:] == ["windspeedfactor", "initialtracerdTR1"]
        assert quantities[:3] == [
            "frictionCoefficient",
            "waterlevel",
            "frictionCoefficient",
        ]


class TestWithoutInifield:
    def test_the_old_ext_conversion_is_unchanged(self, tmp_path):
        converter = _convert(_write_model(tmp_path, inifield=False, old_ext=True))

        blocks = _spatial_blocks(converter.ext_model.filepath)
        assert [b.quantity for b in blocks] == ["initialtracerdTR1"]

    def test_nothing_to_convert_writes_no_ext_file(self, tmp_path):
        mdu = _write_model(tmp_path, inifield=False)

        with pytest.raises(ValueError):
            ExternalForcingConverter.from_mdu(mdu)


class TestTracerOrderWarning:
    """Inifield tracers move behind the `[Boundary]` tracers of the new ext file."""

    def test_warns_when_an_inifield_tracer_meets_a_boundary_tracer(self, tmp_path):
        mdu = _write_model(
            tmp_path,
            inifield_text=INIFIELD_TRACER,
            new_ext=True,
            new_ext_text=NEW_EXT_BOUNDARY_TRACER,
        )
        converter = ExternalForcingConverter.from_mdu(mdu)

        with pytest.warns(UserWarning, match="initialtracerX.*tracerbndA"):
            converter.update()

    def test_no_warning_without_a_boundary_tracer(self, tmp_path):
        mdu = _write_model(tmp_path, inifield_text=INIFIELD_TRACER)
        converter = ExternalForcingConverter.from_mdu(mdu)

        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            converter.update()

    def test_no_warning_without_an_inifield_tracer(self, tmp_path):
        mdu = _write_model(
            tmp_path, new_ext=True, new_ext_text=NEW_EXT_BOUNDARY_TRACER
        )
        converter = ExternalForcingConverter.from_mdu(mdu)

        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            converter.update()


class TestEmptyOrMissingInifieldEntry:
    """An `IniFieldFile` entry that gives nothing to convert counts as no inifield file."""

    @pytest.mark.parametrize("entry", ["IniFieldFile =", "IniFieldFile = nothere.ini"])
    def test_without_an_old_ext_file_the_missing_old_ext_error_is_kept(
        self, tmp_path, entry
    ):
        mdu = tmp_path / "model.mdu"
        mdu.write_text(MDU_TEMPLATE.format(inifield=entry + "\n", extforce=""))

        with pytest.raises(ValueError, match="old formatted external forcing file"):
            ExternalForcingConverter.from_mdu(mdu)

    def test_the_old_ext_file_is_still_converted_when_the_entry_is_empty(
        self, tmp_path
    ):
        mdu = _write_model(tmp_path, inifield=False, old_ext=True)
        text = mdu.read_text().replace("[geometry]\n", "[geometry]\nIniFieldFile =\n", 1)
        mdu.write_text(text)

        converter = _convert(mdu)

        blocks = _spatial_blocks(converter.ext_model.filepath)
        assert [b.quantity for b in blocks] == ["initialtracerdTR1"]


def _write_nested_model(root: Path, *, relative_to_parent: bool, data_file: str) -> Path:
    """Write a model whose inifield is in `sub/` and whose new ext file is in `ext/`."""
    (root / "sub").mkdir()
    (root / "ext").mkdir()
    (root / "sub" / "inifield.ini").write_text(
        INIFIELD_TRACER.replace("a.xyz", data_file)
    )
    mdu = root / "model.mdu"
    mdu.write_text(
        MDU_TEMPLATE.format(
            inifield=(
                "IniFieldFile = sub/inifield.ini\n"
                f"PathsRelativeToParent = {int(relative_to_parent)}\n"
            ),
            extforce="ExtForceFileNew = ext/new.ext\n",
        )
    )
    return mdu


class TestInifieldDataPath:
    def _data_path(self, converter: ExternalForcingConverter) -> Path:
        converter.update()
        return converter.ext_model.spatial[0].datafile.filepath

    def test_paths_stay_as_they_are_without_paths_relative_to_parent(self, tmp_path):
        mdu = _write_nested_model(tmp_path, relative_to_parent=False, data_file="a.xyz")

        converter = ExternalForcingConverter.from_mdu(mdu)

        assert self._data_path(converter) == Path("a.xyz")

    def test_paths_are_made_relative_to_the_new_ext_file(self, tmp_path):
        mdu = _write_nested_model(tmp_path, relative_to_parent=True, data_file="a.xyz")

        converter = ExternalForcingConverter.from_mdu(mdu)

        assert self._data_path(converter) == Path("../sub/a.xyz")

    def test_an_absolute_path_is_kept(self, tmp_path):
        absolute = (tmp_path / "data" / "a.xyz").resolve()
        mdu = _write_nested_model(
            tmp_path, relative_to_parent=True, data_file=absolute.as_posix()
        )

        converter = ExternalForcingConverter.from_mdu(mdu)

        assert self._data_path(converter) == absolute

    def test_a_path_on_another_drive_falls_back_to_the_absolute_path(
        self, tmp_path, monkeypatch
    ):
        mdu = _write_nested_model(tmp_path, relative_to_parent=True, data_file="a.xyz")
        converter = ExternalForcingConverter.from_mdu(mdu)

        def other_drive(*_args, **_kwargs):
            raise ValueError("path is on mount 'C:', start on mount 'D:'")

        monkeypatch.setattr("os.path.relpath", other_drive)

        assert self._data_path(converter) == (tmp_path / "sub" / "a.xyz").resolve()


class TestRepeatedAndEmptyInifield:
    def test_a_second_update_adds_no_blocks(self, tmp_path):
        converter = ExternalForcingConverter.from_mdu(_write_model(tmp_path))
        converter.update()
        first = list(converter.ext_model.spatial)

        converter.update()

        assert converter.ext_model.spatial == first

    def test_an_inifield_without_blocks_writes_no_ext_file(self, tmp_path):
        mdu = _write_model(
            tmp_path,
            inifield_text="[General]\nfileVersion = 2.00\nfileType = iniField\n",
        )

        converter = _convert(mdu)

        assert not converter.ext_model.filepath.exists()
        assert "extforcefilenew" not in mdu.read_text().lower()


class TestInifieldOutsideMduDirectory:
    """A shared inifield file outside the MDU directory is converted but never removed."""

    def _converter(self, tmp_path: Path) -> tuple[ExternalForcingConverter, Path]:
        model_dir = tmp_path / "model"
        shared = tmp_path / "shared"
        model_dir.mkdir()
        shared.mkdir()
        (shared / "inifield.ini").write_text(INIFIELD_TRACER)
        mdu = model_dir / "model.mdu"
        mdu.write_text(
            MDU_TEMPLATE.format(
                inifield="IniFieldFile = ../shared/inifield.ini\n", extforce=""
            )
        )
        return ExternalForcingConverter.from_mdu(mdu), shared / "inifield.ini"

    def test_clean_keeps_the_file_and_update_warns(self, tmp_path):
        converter, inifield = self._converter(tmp_path)

        with pytest.warns(UserWarning, match="outside the MDU directory"):
            converter.update()
        converter.save(backup=False)
        converter.clean()

        assert inifield.is_file()
        assert [b.quantity for b in converter.ext_model.spatial] == ["initialtracerX"]

    def test_clean_keeps_a_symbolic_link_to_the_inifield(self, tmp_path):
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        target = tmp_path / "inifield-target.ini"
        target.write_text(INIFIELD_TRACER)
        try:
            (model_dir / "inifield.ini").symlink_to(target)
        except OSError:
            pytest.skip("symbolic links are not permitted here")
        mdu = model_dir / "model.mdu"
        mdu.write_text(
            MDU_TEMPLATE.format(inifield="IniFieldFile = inifield.ini\n", extforce="")
        )
        converter = ExternalForcingConverter.from_mdu(mdu)

        with pytest.warns(UserWarning, match="symbolic link"):
            converter.update()
        converter.save(backup=False)
        converter.clean()

        assert target.is_file()
        assert (model_dir / "inifield.ini").is_symlink()
