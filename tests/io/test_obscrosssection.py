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
        "use_branchid, numCoordinates, xCoordinates, yCoordinates, should_validate",
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
        numCoordinates: int,
        xCoordinates: List[float],
        yCoordinates: List[float],
        should_validate: bool,
    ):
        values = _create_observation_point_cross_section_values()

        if not use_branchid:
            del values["branchid"]
            del values["chainage"]

        values.update(
            {
                "numcoordinates": numCoordinates,
                "xcoordinates": xCoordinates,
                "ycoordinates": yCoordinates,
            }
        )

        if not should_validate:
            with pytest.raises(ValidationError):
                ObservationPointCrossSection(**values)
        else:
            obsPointCrossSection = ObservationPointCrossSection(**values)

            assert isinstance(obsPointCrossSection, INIBasedModel)
            assert isinstance(obsPointCrossSection.comments, INIBasedModel.Comments)
            assert obsPointCrossSection._header == "ObservationCrossSection"
            assert obsPointCrossSection.name == values["name"]
            assert obsPointCrossSection.branchid == values.get("branchid", None)
            assert obsPointCrossSection.chainage == values.get("chainage", None)
            assert obsPointCrossSection.numcoordinates == values["numcoordinates"]
            assert obsPointCrossSection.xcoordinates == values["xcoordinates"]
            assert obsPointCrossSection.ycoordinates == values["ycoordinates"]


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
