import pytest

from hydrolib.core.io.ini.models import INIBasedModel, INIGeneral
from hydrolib.core.io.obscrosssection.models import (
    ObservationPointCrossSection,
    ObservationPointCrossSectionGeneral,
)


class TestObservationPointCrossSectionGeneral:
    def test_create(self):
        general = ObservationPointCrossSectionGeneral()

        assert isinstance(general, INIGeneral)
        assert general.fileversion == "2.00"
        assert general.filetype == "obsCross"


class TestObservationPointCrossSection:
    def test_create(self):
        pass
