from typing import List

import pytest
from pydantic.error_wrappers import ValidationError

from hydrolib.core.io.ini.models import INIBasedModel, INIGeneral
from hydrolib.core.io.obscrosssection.models import (
    ObservationPointCrossSection,
    ObservationPointCrossSectionGeneral,
    ObservationPointCrossSectionModel,
)


class TestObservationPointCrossSectionGeneral:
    def test_create(self):
        general = ObservationPointCrossSectionGeneral()

        assert isinstance(general, INIGeneral)
        assert isinstance(general.comments, INIBasedModel.Comments)
        assert general.fileversion == "2.00"
        assert general.filetype == "obsCross"


class TestObservationPointCrossSection:
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
                [1.1, 2.2],
                [1.1, 2.2],
                True,
                id="Using branchId while also specifying numCoordinates should validate.",
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
        values = _create_observation_point_cross_section_values()

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
                ObservationPointCrossSection(**values)
        else:
            obspoint_crosssection = ObservationPointCrossSection(**values)

            assert isinstance(obspoint_crosssection, INIBasedModel)
            assert isinstance(obspoint_crosssection.comments, INIBasedModel.Comments)
            assert obspoint_crosssection._header == "ObservationCrossSection"
            assert obspoint_crosssection.name == values["name"]
            assert obspoint_crosssection.branchid == values.get("branchid", None)
            assert obspoint_crosssection.chainage == values.get("chainage", None)
            assert obspoint_crosssection.numcoordinates == values["numcoordinates"]
            assert obspoint_crosssection.xcoordinates == values["xcoordinates"]
            assert obspoint_crosssection.ycoordinates == values["ycoordinates"]


class TestObservationPointCrossSectionModel:
    def test_create(self):
        model = ObservationPointCrossSectionModel()

        assert isinstance(model.general, ObservationPointCrossSectionGeneral)
        assert isinstance(model.crosssections, List)
        assert len(model.crosssections) == 0


def _create_observation_point_cross_section_values() -> dict:
    values = dict(
        name="randomName",
        branchid="randomBranchName",
        chainage=1.234,
        numcoordinates=None,
        xcoordinates=None,
        ycoordinates=None,
    )

    return values
