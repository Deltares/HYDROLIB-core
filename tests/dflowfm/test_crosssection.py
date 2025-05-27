from pathlib import Path

import pytest
from pydantic import ValidationError

from hydrolib.core.dflowfm.crosssection.models import (
    CircleCrsDef,
    CrossDefModel,
    CrossLocModel,
    CrossSection,
    RectangleCrsDef,
    XYZCrsDef,
    YZCrsDef,
    ZWCrsDef,
    ZWRiverCrsDef,
)
from hydrolib.core.dflowfm.friction.models import FrictionType
from hydrolib.core.dflowfm.ini.util import (
    LocationValidationConfiguration,
    LocationValidationFieldNames,
    validate_location_specification,

)
from tests.utils import (
    assert_files_equal,
    test_data_dir,
    test_output_dir,
    test_reference_dir,
)


class TestCrossSectionDefinition:
    def test_crossdef_model(self):
        filepath = test_data_dir / "input/dflowfm_individual_files/crsdef1.ini"
        m = CrossDefModel(filepath)
        assert len(m.definition) == 4

        assert isinstance(m.definition[0], CircleCrsDef)
        assert m.definition[0].id == "Prof1"
        assert m.definition[0].thalweg == 0.0
        assert m.definition[0].diameter == pytest.approx(2.0)
        assert m.definition[0].frictionid == "Brick"

    def test_crossdef_list_delimiters(self):
        filepath = test_data_dir / "input/dflowfm_individual_files/crsdef1.ini"
        m = CrossDefModel(filepath)

        output_file = Path(test_output_dir / "fm" / "serialize_crsdef1.ini")
        m.filepath = output_file
        m.save()

        m2 = CrossDefModel(output_file)

        assert isinstance(m.definition[3], XYZCrsDef)
        assert isinstance(m2.definition[3], XYZCrsDef)
        assert m.definition[3].frictionids == m2.definition[3].frictionids
        assert m.definition[3].ycoordinates == m2.definition[3].ycoordinates

    circledef = {
        "id": "Prof1",
        "diameter": 3.14,
        "frictiontype": FrictionType.walllawnikuradse,
        "frictionvalue": 1.5,
    }

    rectangledef = {
        "id": "Prof1",
        "width": 3.14,
        "height": 2.718,
        "frictiontype": FrictionType.walllawnikuradse,
        "frictionvalue": 1.5,
    }

    zwdef = {
        "id": "Prof1",
        "numlevels": 2,
        "levels": [-2, 3],
        "flowwidths": [11, 44],
        "frictiontype": FrictionType.manning,
        "frictionvalue": 0.03,
    }

    zwriverdef = {
        "id": "Prof1",
        "numlevels": 2,
        "levels": [-2, 3],
        "flowwidths": [11, 44],
        "frictiontypes": [FrictionType.manning],
        "frictionvalues": [0.03],
    }

    yzdef = {
        "id": "Prof1",
        "yzcount": 4,
        "ycoordinates": [-10, -2, 3, 12],
        "zcoordinates": [1, -4, -4.1, 2],
        "frictiontypes": [FrictionType.manning],
        "frictionvalues": [0.03],
    }

    xyzdef = {
        "id": "Prof1",
        "xyzcount": 4,
        "xcoordinates": [10, 20, 30, 40],
        "ycoordinates": [-10, -2, 3, 12],
        "zcoordinates": [1, -4, -4.1, 2],
        "frictiontypes": [FrictionType.manning],
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
                frictiontype=FrictionType.walllawnikuradse,
                frictionvalue=1.5,
            )
        expected_message = f"Cross section has duplicate friction specification"

        assert expected_message in str(error.value)

    def test_create_a_rectanglecrsdef_without_frictionspec(self):
        csdefid = "Prof1"
        crsdef = RectangleCrsDef(
            id=csdefid,
            width=3.14,
            height=2.718,
        )
        assert crsdef.id == csdefid
        assert crsdef.width == 3.14
        assert crsdef.height == 2.718

    def test_create_a_zwrivercrsdef_with_wrong_list_lengths(self):
        csdefid = "Prof1"
        with pytest.raises(ValidationError) as error:
            _ = ZWRiverCrsDef(
                id=csdefid,
                numlevels=2,
                levels=[-2, 3, 13],  # Intentional wrong list length
                flowwidths=[11, 44],
                frictiontypes=[FrictionType.manning],
                frictionvalues=[0.03],
            )
        expected_message = (
            f"Number of values for levels should be equal to the numlevels value."
        )

        assert expected_message in str(error.value)

    def test_create_a_zwrivercrsdef_without_frictionspec(self):
        csdefid = "Prof1"
        crsdef = ZWRiverCrsDef(
            id=csdefid,
            numlevels=2,
            levels=[-2, 3],
            flowwidths=[11, 44],
        )
        assert crsdef.id == csdefid
        assert crsdef.numlevels == 2
        assert crsdef.levels == [-2, 3]
        assert crsdef.flowwidths == [11, 44]
        assert crsdef.frictionids == None
        assert crsdef.frictiontypes == None
        assert crsdef.frictionvalues == None

    def test_create_a_yzcrsdef_with_wrong_list_length_yz(self):
        csdefid = "Prof1"
        with pytest.raises(ValidationError) as error:
            _ = YZCrsDef(
                id=csdefid,
                yzcount=4,
                ycoordinates=[-10, -2, 3, 12],
                zcoordinates=[1, -4, -4.1],  # Intentional wrong list length
                frictiontypes=[FrictionType.manning],
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
                frictiontypes=[FrictionType.manning, FrictionType.manning],
                frictionvalues=[0.03],  # Intentional wrong list length
            )
        expected_message0 = f"Number of values for frictionvalues should be equal to the sectioncount value."
        expected_message1 = f"Number of values for frictionpositions should be equal to the sectioncount value + 1."

        assert expected_message0 in str(error.value)
        assert expected_message1 in str(error.value)

    def test_create_a_yzcrsdef_without_frictionspec(self):
        csdefid = "Prof1"
        crsdef = YZCrsDef(
            id=csdefid,
            yzcount=4,
            ycoordinates=[-10, -2, 3, 12],
            zcoordinates=[1, -4, -4.1, 2],
        )
        assert crsdef.id == csdefid
        assert crsdef.yzcount == 4
        assert crsdef.ycoordinates == [-10, -2, 3, 12]
        assert crsdef.zcoordinates == [1, -4, -4.1, 2]
        assert crsdef.sectioncount == 1
        assert crsdef.frictionpositions == None
        assert crsdef.frictionids == None
        assert crsdef.frictiontypes == None
        assert crsdef.frictionvalues == None

    def test_create_a_xyzcrsdef_with_wrong_list_length_yz(self):
        csdefid = "Prof1"
        with pytest.raises(ValidationError) as error:
            _ = XYZCrsDef(
                id=csdefid,
                xyzcount=4,
                xcoordinates=[10, 20, 30, 40],
                ycoordinates=[-10, -2, 3, 12],
                zcoordinates=[1, -4, -4.1],  # Intentional wrong list length
                frictiontypes=[FrictionType.manning],
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
                frictiontypes=[FrictionType.manning],
                frictionvalues=[0.03],
            )
        expected_message = (
            f"Number of values for xcoordinates should be equal to the xyzcount value."
        )

        assert expected_message in str(error.value)


class TestCrossSectionLocation:
    """
    Class to test the cross section (location) input
    """

    def test_one_crosssection(self):
        """test whether a CrossLocModel can be created with one cross-section"""
        data = {
            "id": "99",
            "branchId": "9",
            "chainage": 403.089709,
            "shift": 0.0,
            "definitionId": "99",
        }
        cross_section = CrossSection(**data)

        crossloc = CrossLocModel(crosssection=cross_section)
        assert len(crossloc.crosssection) == 1

    def test_crossdef_model_from_file(self):
        filepath = test_data_dir / "input/dflowfm_individual_files/crsloc.ini"
        m = CrossLocModel(filepath)
        assert len(m.crosssection) == 2

        assert isinstance(m.crosssection[0], CrossSection)
        assert m.crosssection[0].id == "Channel1_50.000"
        assert m.crosssection[0].branchid == "Channel1"
        assert m.crosssection[0].shift == pytest.approx(1.0)
        assert m.crosssection[0].definitionid == "Prof1"

        assert isinstance(m.crosssection[1], CrossSection)
        assert m.crosssection[1].id == "Channel2_300.000"
        assert m.crosssection[1].branchid == "Channel2"
        assert m.crosssection[1].shift == pytest.approx(0.0)
        assert m.crosssection[1].definitionid == "Prof2"

    @pytest.mark.parametrize(
        "dict_values",
        [
            pytest.param(
                dict(branchid=None, chainage=None, x=None, y=None),
                id="All None",
            ),
            pytest.param(
                dict(branchid="", chainage=None, x=None, y=None),
                id="All Empty",
            ),
            pytest.param(
                dict(branchid="some_branchid", chainage=None, x=None, y=None),
                id="Only branchid given",
            ),
            pytest.param(
                dict(branchid=None, chainage=1.0, x=None, y=None),
                id="Only chainage given",
            ),
            pytest.param(
                dict(branchid=None, chainage=None, x=[1, 2, 3], y=None),
                id="Only x given",
            ),
            pytest.param(
                dict(branchid=None, chainage=None, x=None, y=[1, 2, 3]),
                id="Only y given",
            ),
            pytest.param(
                dict(branchid="some_branchid", chainage=1.0, x=[1, 2, 3], y=None),
                id="branchid and chainage given, but with something else",
            ),
            pytest.param(
                dict(branchid="some_branchid", chainage=None, x=[1, 2, 3], y=[1, 2, 3]),
                id="x and y given, but with something else",
            ),
        ],
    )
    def test_wrong_values_raises_valueerror(self, dict_values: dict):
        with pytest.raises(ValueError) as exc_err:
            validate_location_specification(
                dict_values,
                config=LocationValidationConfiguration(
                    validate_node=False,
                    validate_num_coordinates=False,
                    validate_location_type=False,
                ),
                fields=LocationValidationFieldNames(x_coordinates="x", y_coordinates="y"),
            )
        assert (
            str(exc_err.value) == "branchId and chainage or x and y should be provided"
        )

    def test_given_valid_coordinates(self):
        test_dict = dict(
            branchid=None,
            chainage=None,
            x=42,
            y=24,
        )

        assert validate_location_specification(
            test_dict,
            config=LocationValidationConfiguration(
                validate_node=False,
                validate_num_coordinates=False,
                validate_location_type=False,
            ),
            fields=LocationValidationFieldNames(x_coordinates="x", y_coordinates="y"),
        )


class TestCrossSectionModel:
    def test_create_and_save_crosslocmodel_correctly_saves_file_with_correct_enum_value(
        self,
    ):
        reference_file = Path(test_reference_dir / "crosssection" / "crsloc.ini")
        output_file = Path(
            test_output_dir
            / self.test_create_and_save_crosslocmodel_correctly_saves_file_with_correct_enum_value.__name__
        )

        crossloc_model = CrossLocModel()

        values = {
            "id": "testCrossSection",
            "branchid": "branch1",
            "chainage": 123,
            "definitionid": "randomDefinition",
        }
        crossloc_model.crosssection.append(CrossSection(**values))

        crossloc_model.serializer_config.float_format = ".2f"
        crossloc_model.save(filepath=output_file)

        assert_files_equal(output_file, reference_file, skip_lines=[0])

    def test_locationtype_is_not_written_for_crosssection(self, tmp_path: Path):
        model = CrossLocModel()
        model.crosssection.append(
            CrossSection(
                id="testCrossSection",
                branchid="branch1",
                chainage=1,
                definitionid="testDefinition",
            )
        )

        crs_file = tmp_path / "crsloc.ini"
        model.save(filepath=crs_file)

        with open(crs_file, "r") as file:
            content = file.read()

        assert "locationtype" not in content
