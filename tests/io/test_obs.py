import pytest
from pydantic.error_wrappers import ValidationError

from hydrolib.core.io.common.models import LocationType
from hydrolib.core.io.obs.models import (
    ObservationPoint,
    ObservationPointGeneral,
    ObservationPointModel,
)

from ..utils import test_data_dir


class TestObservationPointGeneral:
    def test_create(self):
        general = ObservationPointGeneral()

        assert general.fileversion == "2.00"
        assert general.filetype == "obsPoints"


class TestObservationPoint:
    def test_create_observationpoint(self):
        obsvalues = _create_observation_point_values()
        obspoint = ObservationPoint(**obsvalues)

        assert obspoint.name == obsvalues["name"]
        assert obspoint.locationtype == None
        assert obspoint.branchid == obsvalues["branchid"]
        assert obspoint.chainage == obsvalues["chainage"]

    @pytest.mark.parametrize(
        "loctype, expected_type",
        [
            ("1d", LocationType.oned),
            ("2d", LocationType.twod),
        ],
    )
    def test_create_observationpoint_1or2d(
        self, loctype: str, expected_type: LocationType
    ):
        obsvalues = _create_observation_point_values()
        obsvalues.update({"locationType": loctype})
        obspoint = ObservationPoint(**obsvalues)

        assert obspoint.name == obsvalues["name"]
        assert obspoint.locationtype == expected_type
        assert obspoint.branchid == obsvalues["branchid"]
        assert obspoint.chainage == obsvalues["chainage"]


class TestObservationPointModel:
    def test_obspoint_file(self):
        filepath = test_data_dir / "input/dflowfm_individual_files/obsPoints_obs.ini"
        m = ObservationPointModel(filepath)
        assert len(m.observationpoint) == 5
        assert m.observationpoint[1].x == -2.73750000
        assert m.observationpoint[1].y == 5.15083334e01
        assert m.observationpoint[2].name == "#St Helier Jersey#"
        assert m.observationpoint[3].locationtype == None
        assert m.observationpoint[4].locationtype == LocationType.oned


def _create_observation_point_values() -> dict:
    values = dict(name="obs_name", branchid="branch_01", chainage=1.23)

    return values
