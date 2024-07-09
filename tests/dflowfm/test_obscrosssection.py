from pathlib import Path
from typing import List

import pytest
from pydantic.v1.error_wrappers import ValidationError

from hydrolib.core.dflowfm.ini.models import INIBasedModel, INIGeneral
from hydrolib.core.dflowfm.obscrosssection.models import (
    ObservationCrossSection,
    ObservationCrossSectionGeneral,
    ObservationCrossSectionModel,
)
from hydrolib.core.dflowfm.polyfile.models import (
    Description,
    Metadata,
    Point,
    PolyFile,
    PolyObject,
)
from tests.utils import assert_files_equal, test_input_dir, test_output_dir


class TestObservationCrossSectionGeneral:
    def test_create(self):
        general = ObservationCrossSectionGeneral()

        assert isinstance(general, INIGeneral)
        assert isinstance(general.comments, INIBasedModel.Comments)
        assert general.fileversion == "2.00"
        assert general.filetype == "obsCross"


class TestObservationCrossSection:
    @pytest.mark.parametrize(
        "use_branchid, numcoordinates, xcoordinates, ycoordinates, should_validate",
        [
            pytest.param(
                True,
                None,
                None,
                None,
                True,
                id="Using branchId without specifying numCoordinates should validate.",
            ),
            pytest.param(
                True,
                2,
                [],
                [],
                False,
                id="Using branchId with incorrect number of coordinates should not validate.",
            ),
            pytest.param(
                False,
                2,
                [1.1, 2.2],
                [1.1, 2.2],
                True,
                id="Using numCoordinates with correct number of coordinates should validate.",
            ),
            pytest.param(
                False,
                2,
                [1],
                [1, 2],
                False,
                id="Using numCoordinates with too few xCoordinates should not validate.",
            ),
            pytest.param(
                False,
                2,
                [1, 2],
                [1],
                False,
                id="Using numCoordinates with too few yCoordinates should not validate.",
            ),
            pytest.param(
                False,
                2,
                [1, 2, 3],
                [1, 2],
                False,
                id="Using numCoordinates with too many xCoordinates should not validate.",
            ),
            pytest.param(
                False,
                2,
                [1, 2],
                [1, 2, 3],
                False,
                id="Using numCoordinates with too many yCoordinates should not validate.",
            ),
            pytest.param(
                False,
                0,
                [],
                [],
                False,
                id="Using zero numCoordinates should not validate.",
            ),
            pytest.param(
                False,
                1,
                [1.23],
                [4.56],
                False,
                id="Using fewer than 2 coordinates should not validate.",
            ),
        ],
    )
    def test_create(
        self,
        use_branchid: bool,
        numcoordinates: int,
        xcoordinates: List[float],
        ycoordinates: List[float],
        should_validate: bool,
    ):
        values = _create_observation_cross_section_values()

        if not use_branchid:
            del values["branchid"]
            del values["chainage"]

        values.update(
            {
                "numcoordinates": numcoordinates,
                "xcoordinates": xcoordinates,
                "ycoordinates": ycoordinates,
            }
        )

        if not should_validate:
            with pytest.raises(ValidationError):
                ObservationCrossSection(**values)
        else:
            obs_crosssection = ObservationCrossSection(**values)

            assert isinstance(obs_crosssection, INIBasedModel)
            assert isinstance(obs_crosssection.comments, INIBasedModel.Comments)
            assert obs_crosssection._header == "ObservationCrossSection"
            assert obs_crosssection.name == values["name"]
            assert obs_crosssection.branchid == values.get("branchid", None)
            assert obs_crosssection.chainage == values.get("chainage", None)
            assert obs_crosssection.numcoordinates == values["numcoordinates"]
            assert obs_crosssection.xcoordinates == values["xcoordinates"]
            assert obs_crosssection.ycoordinates == values["ycoordinates"]


class TestObservationCrossSectionModel:
    def test_create(self):
        model = ObservationCrossSectionModel()

        assert isinstance(model.general, ObservationCrossSectionGeneral)
        assert isinstance(model.observationcrosssection, List)
        assert len(model.observationcrosssection) == 0

    def test_locationtype_is_not_written_for_observationcrosssection(
        self, tmp_path: Path
    ):
        model = ObservationCrossSectionModel()
        model.observationcrosssection.append(
            ObservationCrossSection(
                name="testName",
                branchId="testbranch",
                chainage=123,
            )
        )

        obs_crs_file = tmp_path / "obs_crs.ini"
        model.save(filepath=obs_crs_file)

        with open(obs_crs_file, "r") as file:
            content = file.read()

        assert "locationtype" not in content


def _create_observation_cross_section_values() -> dict:
    values = dict(
        name="randomName",
        branchid="randomBranchName",
        chainage=1.234,
        numcoordinates=None,
        xcoordinates=None,
        ycoordinates=None,
    )

    return values


class TestObservationCrossSectionModelPli:
    """Test class for the legacy polyline format for observation cross
    sections (*_crs.pli).

    These legacy observation cross sections have no own model class,
    they can completely be represented by the generic PolyFile class.
    """

    def _get_crs_data(self):
        """Returns test data for constructing the contents of a PolyFile object"""

        crs_data = {
            "CrossSection_00": (
                None,
                [
                    [3.147458984400000e004, 3.863195937500000e005],
                    [2.874086718800000e004, 3.783987812500000e005],
                    [2.374086718800000e004, 3.703987812500000e005],
                    [2.154086718800000e004, 3.683987812500000e005],
                    [1.874086718800000e004, 3.682187812500000e005],
                ],
            ),
            "L1": (
                "\n Comment for L1\n",
                [
                    [3.147458984400000e004, 3.863195937500000e005],
                    [2.874086718800000e004, 3.783987812500000e005],
                ],
            ),
            "L2": (
                None,
                [
                    [4.605445312500000e004, 3.812025937500000e005],
                    [5.019008593800000e004, 3.720901562500000e005],
                ],
            ),
            "L3": (
                None,
                [
                    [6.701300781200000e004, 3.806418437500000e005],
                    [6.484004687500000e004, 3.739827187500000e005],
                ],
            ),
            "L4": (
                None,
                [
                    [7.836847656200000e004, 3.666226562500000e005],
                    [7.970028906200000e004, 3.690059375000000e005],
                ],
            ),
        }
        return crs_data

    def _construct_crs_objects_from_dict(self, data):
        """Returns a list of PolyObject items, based on input dict,
        where each dict item contains a tuple (description, [[x,y]] point list).
        """
        crs_objects = [
            PolyObject(
                description=Description(content=desc) if desc else None,
                metadata=Metadata(
                    name=key, n_rows=len(points), n_columns=len(points[0])
                ),
                points=[Point(x=x, y=y, data=[]) for [x, y] in points],
            )
            for key, (desc, points) in data.items()
        ]

        return crs_objects

    def test_load(self):
        input_file = (
            test_input_dir / "dflowfm_individual_files" / "crosssections_crs.pli"
        )
        model = PolyFile(filepath=input_file)

        crs_data = self._get_crs_data()
        crs_objects = self._construct_crs_objects_from_dict(crs_data)

        assert len(model.objects) == len(crs_objects)
        assert model.objects == crs_objects

    def test_construct_and_serialize(self):
        reference_file = (
            test_input_dir / "dflowfm_individual_files" / "crosssections_crs.pli"
        )
        output_file = test_output_dir / "fm" / "serialize_crosssections_crs.pli"

        crs_data = self._get_crs_data()
        crs_objects = self._construct_crs_objects_from_dict(crs_data)

        model = PolyFile(objects=crs_objects)
        model.filepath = output_file
        model.serializer_config.float_format = "25.15E"
        model.save()

        assert_files_equal(output_file, reference_file)
