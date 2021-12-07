import inspect
from contextlib import nullcontext as does_not_raise
from pathlib import Path
from typing import Any, Callable, List, Union

import pytest
from pydantic.error_wrappers import ValidationError

from hydrolib.core.io.ini.models import (
    CircleCrsDef,
    CrossDefModel,
    CrossSectionDefinition,
    RectangleCrsDef,
    XYZCrsDef,
    YZCrsDef,
    ZWCrsDef,
    ZWRiverCrsDef,
)
from hydrolib.core.io.ini.parser import Parser, ParserConfig

from ..utils import WrapperTest, test_data_dir


class TestCrossSection:
    def test_crossdef_model(self):
        filepath = test_data_dir / "input/dflowfm_individual_files/crsdef1.ini"
        m = CrossDefModel(filepath)
        assert len(m.definition) == 4

        assert isinstance(m.definition[0], CircleCrsDef)
        assert m.definition[0].id == "Prof1"
        assert m.definition[0].thalweg == 0.0
        assert m.definition[0].diameter == 2.0
        assert m.definition[0].frictionid == "Brick"

    circledef = {
        "id": "Prof1",
        "diameter": 3.14,
        "frictiontype": "wallLawNikuradse",
        "frictionvalue": 1.5,
    }

    rectangledef = {
        "id": "Prof1",
        "width": 3.14,
        "height": 2.718,
        "frictiontype": "wallLawNikuradse",
        "frictionvalue": 1.5,
    }

    zwdef = {
        "id": "Prof1",
        "numlevels": 2,
        "levels": [-2, 3],
        "flowwidths": [11, 44],
        "frictiontype": "Manning",
        "frictionvalue": 0.03,
    }

    zwriverdef = {
        "id": "Prof1",
        "numlevels": 2,
        "levels": [-2, 3],
        "flowwidths": [11, 44],
        "frictiontypes": ["Manning"],
        "frictionvalues": [0.03],
    }

    yzdef = {
        "id": "Prof1",
        "yzcount": 4,
        "ycoordinates": [-10, -2, 3, 12],
        "zcoordinates": [1, -4, -4.1, 2],
        "frictiontypes": ["Manning"],
        "frictionvalues": [0.03],
    }

    xyzdef = {
        "id": "Prof1",
        "xyzcount": 4,
        "xcoordinates": [10, 20, 30, 40],
        "ycoordinates": [-10, -2, 3, 12],
        "zcoordinates": [1, -4, -4.1, 2],
        "frictiontypes": ["Manning"],
        "frictionvalues": [0.03],
    }

    @pytest.mark.parametrize(
        "crscls, crsdict, expected_type",
        [
            pytest.param(CircleCrsDef, circledef, "circle"),
            pytest.param(RectangleCrsDef, rectangledef, "rectangle"),
            pytest.param(ZWCrsDef, zwdef, "zw"),
            pytest.param(ZWRiverCrsDef, zwriverdef, "zwRiver"),
            pytest.param(YZCrsDef, yzdef, "yz"),
            pytest.param(XYZCrsDef, xyzdef, "xyz"),
        ],
    )
    def test_create_a_crsdef_from_scratchs(
        self, crscls, crsdict: dict, expected_type: str
    ):
        """
        Test that creates a cross section definition from dict, and asserts that
        all fields are correcty set in the object.

        Args:
            crscls: the subclass of CrossSectionDefinition that will be instantiated.
            crsdict: the key-value pairs for the class's attributes.
            expected_type: the expected value of the object's type attribute.
        """
        cd = crscls(**crsdict)
        assert cd.type == expected_type
        for key, value in crsdict.items():
            assert getattr(cd, key) == value

    def test_create_a_circlecrsdef_with_duplicate_frictionspec(self):
        csdefid = "Prof1"
        with pytest.raises(ValidationError) as error:
            _ = CircleCrsDef(
                id=csdefid,
                diameter=3.14,
                frictionid="Brick",
                frictiontype="wallLawNikuradse",
                frictionvalue=1.5,
            )
        expected_message = f"Cross section has duplicate friction specification"

        assert expected_message in str(error.value)

    def test_create_a_rectanglecrsdef_without_frictionspec(self):
        csdefid = "Prof1"
        with pytest.raises(ValidationError) as error:
            _ = RectangleCrsDef(
                id=csdefid,
                width=3.14,
                height=2.718,
            )
        expected_message = f"Cross section is missing any friction specification."

        assert expected_message in str(error.value)

    def test_create_a_zwrivercrsdef_with_wrong_list_lengths(self):
        csdefid = "Prof1"
        with pytest.raises(ValidationError) as error:
            _ = ZWRiverCrsDef(
                id=csdefid,
                numlevels=2,
                levels=[-2, 3, 13],  # Intentional wrong list length
                flowwidths=[11, 44],
                frictiontypes=["Manning"],
                frictionvalues=[0.03],
            )
        expected_message = (
            f"Number of values for levels should be equal to the numlevels value."
        )

        assert expected_message in str(error.value)

    def test_create_a_zwrivercrsdef_without_frictionspec(self):
        csdefid = "Prof1"
        with pytest.raises(ValidationError) as error:
            _ = ZWRiverCrsDef(
                id=csdefid,
                numlevels=2,
                levels=[-2, 3],
                flowwidths=[11, 44],
            )
        expected_message = f"Cross section is missing any friction specification."

        assert expected_message in str(error.value)

    def test_create_a_yzcrsdef_with_wrong_list_length_yz(self):
        csdefid = "Prof1"
        with pytest.raises(ValidationError) as error:
            _ = YZCrsDef(
                id=csdefid,
                yzcount=4,
                ycoordinates=[-10, -2, 3, 12],
                zcoordinates=[1, -4, -4.1],  # Intentional wrong list length
                frictiontypes=["Manning"],
                frictionvalues=[0.03],
            )
        expected_message = (
            f"Number of values for zcoordinates should be equal to the yzcount value."
        )

        assert expected_message in str(error.value)

    def test_create_a_yzcrsdef_with_wrong_list_length_frict(self):
        csdefid = "Prof1"
        with pytest.raises(ValidationError) as error:
            _ = YZCrsDef(
                id=csdefid,
                yzcount=4,
                ycoordinates=[-10, -2, 3, 12],
                zcoordinates=[1, -4, -4.1, 2],
                sectioncount=2,
                frictionpositions=[1, 2],  # Intentional wrong list length
                frictiontypes=["Manning", "Manning"],
                frictionvalues=[0.03],  # Intentional wrong list length
            )
        expected_message0 = f"Number of values for frictionvalues should be equal to the sectioncount value."
        expected_message1 = f"Number of values for frictionpositions should be equal to the sectioncount value + 1."

        assert expected_message0 in str(error.value)
        assert expected_message1 in str(error.value)

    def test_create_a_yzcrsdef_without_frictionspec(self):
        csdefid = "Prof1"
        with pytest.raises(ValidationError) as error:
            _ = YZCrsDef(
                id=csdefid,
                yzcount=4,
                ycoordinates=[-10, -2, 3, 12],
                zcoordinates=[1, -4, -4.1, 2],
            )
        expected_message = f"Cross section is missing any friction specification."

        assert expected_message in str(error.value)

    def test_create_a_xyzcrsdef_with_wrong_list_length_yz(self):
        csdefid = "Prof1"
        with pytest.raises(ValidationError) as error:
            _ = XYZCrsDef(
                id=csdefid,
                xyzcount=4,
                xcoordinates=[10, 20, 30, 40],
                ycoordinates=[-10, -2, 3, 12],
                zcoordinates=[1, -4, -4.1],  # Intentional wrong list length
                frictiontypes=["Manning"],
                frictionvalues=[0.03],
            )
        expected_message = (
            f"Number of values for zcoordinates should be equal to the xyzcount value."
        )

        assert expected_message in str(error.value)

    def test_create_a_xyzcrsdef_with_wrong_list_length_x(self):
        csdefid = "Prof1"
        with pytest.raises(ValidationError) as error:
            _ = XYZCrsDef(
                id=csdefid,
                xyzcount=4,
                xcoordinates=[10, 20, 30],  # Intentional wrong list length
                ycoordinates=[-10, -2, 3, 12],
                zcoordinates=[1, -4, -4.1, 2],
                frictiontypes=["Manning"],
                frictionvalues=[0.03],
            )
        expected_message = (
            f"Number of values for xcoordinates should be equal to the xyzcount value."
        )

        assert expected_message in str(error.value)
