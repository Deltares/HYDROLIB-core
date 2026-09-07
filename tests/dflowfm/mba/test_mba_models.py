from pathlib import Path

import pytest
from pydantic import ValidationError

from hydrolib.core.dflowfm.mba.models import (
    MassBalanceArea,
    MassBalanceAreaGeneral,
    MassBalanceAreaModel,
)


class TestMassBalanceAreaGeneral:
    def test_defaults(self):
        """Test that the [General] section carries the fixed version and file type.

        Test scenario:
            A default MassBalanceAreaGeneral must report fileVersion '1.00' and
            fileType 'massBalanceAreas' as required by Manual F.2.5.
        """
        general = MassBalanceAreaGeneral()
        assert general.fileversion == "1.00", f"Got {general.fileversion}"
        assert general.filetype == "massBalanceAreas", f"Got {general.filetype}"

    def test_filetype_is_fixed(self):
        """Test that fileType only accepts the canonical 'massBalanceAreas' value.

        Test scenario:
            The fileType is a fixed identifier for the kernel, so any other value
            must be rejected.
        """
        with pytest.raises(ValidationError):
            MassBalanceAreaGeneral(fileType="somethingElse")


class TestMassBalanceArea:
    def test_instantiation_with_location_file(self):
        """Test creating an area defined by a polygon file.

        Test scenario:
            A locationFile-only area keeps its name and resolves the polygon path.
        """
        area = MassBalanceArea(name="EstruaryWest", locationFile="EstruaryWest.pol")
        assert area.name == "EstruaryWest", f"Got {area.name}"
        assert area.locationfile.filepath == Path(
            "EstruaryWest.pol"
        ), f"Got {area.locationfile.filepath}"

    def test_instantiation_with_coordinates(self):
        """Test creating an area defined by inline polygon coordinates.

        Test scenario:
            A coordinate area keeps numCoordinates and the x/y lists.
        """
        area = MassBalanceArea(
            name="poly",
            numCoordinates=3,
            xCoordinates=[0.0, 1.0, 2.0],
            yCoordinates=[0.0, 1.0, 0.0],
        )
        assert area.numcoordinates == 3, f"Got {area.numcoordinates}"
        assert area.xcoordinates == [0.0, 1.0, 2.0], f"Got {area.xcoordinates}"
        assert area.ycoordinates == [0.0, 1.0, 0.0], f"Got {area.ycoordinates}"

    def test_coordinates_from_space_separated_strings(self):
        """Test that space-separated coordinate strings are parsed into float lists.

        Test scenario:
            When read from file, coordinates arrive as a delimited string; the
            before-validator must split them into a list of floats.
        """
        area = MassBalanceArea(
            name="poly",
            numCoordinates=3,
            xCoordinates="0.0 1.0 2.0",
            yCoordinates="0.0 1.0 0.0",
        )
        assert area.xcoordinates == [0.0, 1.0, 2.0], f"Got {area.xcoordinates}"
        assert area.ycoordinates == [0.0, 1.0, 0.0], f"Got {area.ycoordinates}"

    def test_name_at_max_length_is_valid(self):
        """Test that a name of exactly 255 characters is accepted (boundary).

        Test scenario:
            Manual Table F.3 caps the name at 255 characters; exactly 255 is valid.
        """
        area = MassBalanceArea(name="x" * 255, locationFile="a.pol")
        assert len(area.name) == 255, f"Got length {len(area.name)}"

    def test_get_identifier_returns_name(self):
        """Test that _get_identifier returns the area name.

        Test scenario:
            The identifier is used to label validation errors; it must be the name.
        """
        area = MassBalanceArea(name="AreaX", locationFile="a.pol")
        assert (
            area._get_identifier({"name": "AreaX"}) == "AreaX"
        ), f"Got {area._get_identifier({'name': 'AreaX'})}"

    def test_name_exceeding_max_length_raises(self):
        """Test that a name longer than 255 characters is rejected.

        Test scenario:
            Manual Table F.3 limits the area name to 255 characters.
        """
        with pytest.raises(ValidationError):
            MassBalanceArea(name="x" * 256, locationFile="a.pol")

    def test_no_location_specification_raises(self):
        """Test that an area with neither location form is rejected.

        Test scenario:
            A block with only a name specifies no polygon and must fail.
        """
        with pytest.raises(ValidationError, match="either locationFile"):
            MassBalanceArea(name="bad")

    def test_both_location_forms_raise(self):
        """Test that supplying both a location file and coordinates is rejected.

        Test scenario:
            The two location forms are mutually exclusive.
        """
        with pytest.raises(ValidationError, match="not both"):
            MassBalanceArea(
                name="bad",
                locationFile="a.pol",
                numCoordinates=3,
                xCoordinates=[0.0, 1.0, 2.0],
                yCoordinates=[0.0, 1.0, 2.0],
            )

    def test_incomplete_coordinates_raise(self):
        """Test that the coordinate form must supply all three keywords.

        Test scenario:
            numCoordinates without xCoordinates/yCoordinates is incomplete.
        """
        with pytest.raises(ValidationError, match="together"):
            MassBalanceArea(name="bad", numCoordinates=3)

    def test_coordinate_count_mismatch_raises(self):
        """Test that numCoordinates must match the coordinate list lengths.

        Test scenario:
            numCoordinates=3 but only 2 x-coordinates should fail.
        """
        with pytest.raises(ValidationError, match="equal to the number"):
            MassBalanceArea(
                name="bad",
                numCoordinates=3,
                xCoordinates=[0.0, 1.0],
                yCoordinates=[0.0, 1.0, 2.0],
            )

    def test_fewer_than_three_coordinates_raise(self):
        """Test that a polygon requires at least 3 coordinates.

        Test scenario:
            A 2-point polygon is not an area and must fail.
        """
        with pytest.raises(ValidationError, match="at least 3 coordinates"):
            MassBalanceArea(
                name="bad",
                numCoordinates=2,
                xCoordinates=[0.0, 1.0],
                yCoordinates=[0.0, 1.0],
            )


class TestMassBalanceAreaModel:
    def test_initialization_empty(self):
        """Test that an empty model has the default general block and no areas."""
        model = MassBalanceAreaModel()
        assert model.general.filetype == "massBalanceAreas"
        assert model.massbalancearea == [], f"Got {model.massbalancearea}"

    def test_model_ext_and_filename(self):
        """Test the file extension and default filename base."""
        assert (
            MassBalanceAreaModel._ext() == ".ini"
        ), f"Got {MassBalanceAreaModel._ext()}"
        assert (
            MassBalanceAreaModel._filename() == "mba"
        ), f"Got {MassBalanceAreaModel._filename()}"

    def test_save_includes_general_block(self, tmp_path: Path):
        """Test that a saved mba file always carries its [General] fileType.

        Test scenario:
            The [General] block identifies the file to the kernel; it must be
            written out even though it holds only default values.
        """
        model = MassBalanceAreaModel(
            massbalancearea=[MassBalanceArea(name="A", locationFile="A.pol")]
        )
        path = tmp_path / "general_mba.ini"
        model.save(filepath=path)

        text = path.read_text()
        assert "[General]" in text, f"Missing [General] block:\n{text}"
        assert "massBalanceAreas" in text, f"Missing fileType:\n{text}"

    def test_roundtrip_location_file(self, tmp_path: Path):
        """Test that a locationFile-based model survives save and reload.

        Test scenario:
            Two areas defined by polygon files should reload with identical
            names and location file paths.
        """
        model = MassBalanceAreaModel(
            massbalancearea=[
                MassBalanceArea(name="EstruaryWest", locationFile="EstruaryWest.pol"),
                MassBalanceArea(name="River", locationFile="River.pol"),
            ]
        )
        path = tmp_path / "westernscheldt_mba.ini"
        model.save(filepath=path)
        assert path.exists(), "Expected the mba file to be written"

        reloaded = MassBalanceAreaModel(filepath=path)
        assert reloaded.general.filetype == "massBalanceAreas"
        assert [a.name for a in reloaded.massbalancearea] == [
            "EstruaryWest",
            "River",
        ], f"Got {[a.name for a in reloaded.massbalancearea]}"
        assert reloaded.massbalancearea[0].locationfile.filepath == Path(
            "EstruaryWest.pol"
        ), f"Got {reloaded.massbalancearea[0].locationfile.filepath}"

    def test_roundtrip_coordinates(self, tmp_path: Path):
        """Test that a coordinate-based model survives save and reload.

        Test scenario:
            An area defined by inline coordinates should reload with equal
            numCoordinates and coordinate lists.
        """
        model = MassBalanceAreaModel(
            massbalancearea=[
                MassBalanceArea(
                    name="poly",
                    numCoordinates=3,
                    xCoordinates=[0.0, 1.0, 2.0],
                    yCoordinates=[0.0, 1.0, 0.0],
                )
            ]
        )
        path = tmp_path / "coords_mba.ini"
        model.save(filepath=path)

        reloaded = MassBalanceAreaModel(filepath=path)
        area = reloaded.massbalancearea[0]
        assert area.numcoordinates == 3, f"Got {area.numcoordinates}"
        assert area.xcoordinates == [0.0, 1.0, 2.0], f"Got {area.xcoordinates}"
        assert area.ycoordinates == [0.0, 1.0, 0.0], f"Got {area.ycoordinates}"
