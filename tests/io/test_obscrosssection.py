from typing import List

import pytest
from pydantic.error_wrappers import ValidationError

from hydrolib.core.io.ini.models import INIBasedModel, INIGeneral
from hydrolib.core.io.obscrosssection.models import (
    ObservationCrossSection,
    ObservationCrossSectionGeneral,
    ObservationCrossSectionModel,
)


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
