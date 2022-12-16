from pathlib import Path
from typing import Dict, List, Optional

import pytest
from pydantic import ValidationError

from hydrolib.core.dflowfm.bc.models import Constant, ForcingModel, RealTime
from hydrolib.core.dflowfm.ext.models import Boundary, ExtModel, Lateral
from hydrolib.core.dflowfm.ini.models import INIBasedModel

from ..utils import test_data_dir


class TestModels:
    """Test class to test all classes and methods contained in the
    hydrolib.core.dflowfm.ext.models.py module"""

    class TestLateral:
        """Class to test all methods contained in the
        hydrolib.core.dflowfm.ext.models.Lateral class"""

        location_error: str = "nodeId or branchId and chainage or xCoordinates, yCoordinates and numCoordinates should be provided"

        class TestValidateCoordinates:
            """
            Class to test the paradigms for validate_coordinates.
            """

            def _create_valid_lateral_values(self) -> Dict:
                values = dict(
                    id="randomId",
                    name="randomName",
                    numcoordinates=2,
                    xcoordinates=[1.1, 2.2],
                    ycoordinates=[1.1, 2.2],
                    discharge=1.234,
                )

                return values

            def test_given_no_numcoordinates_raises_valueerror(self):
                values = self._create_valid_lateral_values()
                del values["numcoordinates"]

                with pytest.raises(ValueError):
                    Lateral(**values)

            def test_given_wrong_numcoordinates_raises_assertionerror(self):
                values = self._create_valid_lateral_values()
                values["numcoordinates"] = 999

                with pytest.raises(ValueError):
                    Lateral(**values)

            def test_given_correct_numcoordinates(self):
                xcoordinates = [1, 2]
                ycoordinates = [2, 3]

                values = self._create_valid_lateral_values()
                values["xcoordinates"] = xcoordinates
                values["ycoordinates"] = ycoordinates
                values["numcoordinates"] = len(xcoordinates)

                lateral = Lateral(**values)

                assert lateral.xcoordinates == xcoordinates
                assert lateral.ycoordinates == ycoordinates

            def test_given_fewer_coordinates_than_minimum_required_throws_valueerror(
                self,
            ):
                values = self._create_valid_lateral_values()
                values["numcoordinates"] = 0
                values["xcoordinates"] = []
                values["ycoordinates"] = []

                with pytest.raises(ValueError):
                    Lateral(**values)

        class TestValidateLocationType:
            """
            Class to test the paradigms for validate_location_type
            """

            @pytest.mark.parametrize(
                "value",
                [
                    pytest.param(""),
                    pytest.param("  "),
                    pytest.param("notAValidType"),
                ],
            )
            def test_given_wrong_location_type_raises_valueerror(self, value: str):
                with pytest.raises(ValueError) as exc_mssg:
                    Lateral.validate_location_type(value)
                assert (
                    str(exc_mssg.value)
                    == f"Value given ({value}) not accepted, should be one of: 1d, 2d, all"
                )

            @pytest.mark.parametrize(
                "location_type",
                [
                    pytest.param("1d"),
                    pytest.param("1D"),
                    pytest.param("2d"),
                    pytest.param("2D"),
                    pytest.param("all"),
                    pytest.param("All"),
                    pytest.param("ALL"),
                ],
            )
            def test_given_correct_locationtype(self, location_type: str):
                return_value = Lateral.validate_location_type(location_type)
                assert return_value == location_type

        class TestValidateLocationTypeDependencies:
            """
            Class to test the paradigms of validate_location_dependencies
            """

            @pytest.mark.parametrize(
                "dict_values",
                [
                    pytest.param(
                        dict(nodeid=None, branchid=None, chainage=None),
                        id="All None",
                    ),
                    pytest.param(
                        dict(nodeid="", branchid="", chainage=None),
                        id="All Empty",
                    ),
                ],
            )
            def test_given_no_values_raises_valueerror(self, dict_values: dict):
                with pytest.raises(ValueError) as exc_err:
                    Lateral.validate_that_location_specification_is_correct(
                        values=dict_values
                    )
                assert str(exc_err.value) == TestModels.TestLateral.location_error

            @pytest.mark.parametrize(
                "missing_coordinates", [("xCoordinates"), ("yCoordinates")]
            )
            def test_given_numcoords_but_missing_coordinates(
                self, missing_coordinates: str
            ):
                test_dict = dict(
                    nodeid=None,
                    branchid=None,
                    chainage=None,
                    numcoordinates=2,
                    xcoordinates=[42, 24],
                    ycoordinates=[24, 42],
                )
                test_dict[missing_coordinates.lower()] = None
                with pytest.raises(ValueError) as exc_error:
                    Lateral.validate_that_location_specification_is_correct(test_dict)
                assert str(exc_error.value) == TestModels.TestLateral.location_error

            def test_given_numcoordinates_and_valid_coordinates(self):
                test_dict = dict(
                    nodeid=None,
                    branchid=None,
                    chainage=None,
                    numcoordinates=2,
                    xcoordinates=[42, 24],
                    ycoordinates=[24, 42],
                )
                return_value = Lateral.validate_that_location_specification_is_correct(
                    test_dict
                )
                assert return_value == test_dict

            def test_given_branchid_and_no_chainage_raises_valueerror(self):
                with pytest.raises(ValueError) as exc_err:
                    Lateral.validate_that_location_specification_is_correct(
                        dict(
                            nodeid=None,
                            branchid="aBranchId",
                            chainage=None,
                        )
                    )
                assert str(exc_err.value) == TestModels.TestLateral.location_error

            @pytest.mark.parametrize(
                "dict_values",
                [
                    pytest.param(dict(nodeid="42"), id="Given nodeid"),
                    pytest.param(
                        dict(branchid="aBranchId", chainage=4.2),
                        id="Given branchid and chainage",
                    ),
                ],
            )
            def test_given_1d_args_and_location_type_other_then_raises_valueerror(
                self, dict_values: dict
            ):
                test_values = dict(
                    locationtype="wrongType",
                )
                test_dict = {**dict_values, **test_values}
                with pytest.raises(ValueError) as exc_err:
                    Lateral.validate_that_location_specification_is_correct(test_dict)
                assert (
                    str(exc_err.value) == "locationType should be 1d but was wrongType"
                )

            @pytest.mark.parametrize(
                "dict_values",
                [
                    pytest.param(dict(nodeid="24"), id="Given nodeid"),
                    pytest.param(
                        dict(branchid="aBranchId", chainage=4.2),
                        id="Given branchid and chainage.",
                    ),
                ],
            )
            def test_given_1d_args_and_1d_location_type(self, dict_values: dict):
                test_values = dict(
                    locationtype="1d",
                )
                test_dict = {**dict_values, **test_values}
                return_value = Lateral.validate_that_location_specification_is_correct(
                    test_dict
                )
                assert return_value == test_dict

            @pytest.mark.parametrize(
                "test_dict",
                [
                    pytest.param(dict(nodeid="aNodeId"), id="With NodeId"),
                    pytest.param(
                        dict(branchid="aBranchId", chainage=42),
                        id="Witch branchid and chainage",
                    ),
                ],
            )
            @pytest.mark.parametrize(
                "location_type",
                [
                    pytest.param("", id="Empty string"),
                    pytest.param(None, id="None string"),
                ],
            )
            def test_given_1d_args_but_no_locationtype_then_sets_value(
                self, test_dict: dict, location_type: str
            ):
                test_dict["locationtype"] = location_type
                return_value = Lateral.validate_that_location_specification_is_correct(
                    test_dict
                )
                assert return_value["locationtype"] == "1d"

        class TestValidateFromCtor:
            @pytest.mark.parametrize(
                "x_coord, y_coord",
                [
                    pytest.param(None, [42, 24], id="Only y-coord."),
                    pytest.param([42, 24], None, id="Only x-coord."),
                ],
            )
            def test_given_coordinates_but_no_numcoordinates_raises(
                self, x_coord: Optional[List[int]], y_coord: Optional[List[int]]
            ):
                with pytest.raises(ValidationError) as exc_mssg:
                    Lateral(
                        id="42",
                        discharge=1.23,
                        numcoordinates=None,
                        xcoordinates=x_coord,
                        ycoordinates=y_coord,
                    )

                expected_error_mssg = TestModels.TestLateral.location_error
                assert expected_error_mssg in str(exc_mssg.value)

            @pytest.mark.parametrize(
                "x_coord, y_coord",
                [
                    pytest.param([42, 24], [24], id="Y coord not matching."),
                    pytest.param([24], [42, 24], id="X coord not matching."),
                ],
            )
            def test_given_coordinates_not_matching_numcoordinates_raises(
                self, x_coord: List[int], y_coord: List[int]
            ):
                with pytest.raises(ValidationError):
                    Lateral(
                        id="42",
                        discharge=1.23,
                        numcoordinates=2,
                        xcoordinates=x_coord,
                        ycoordinates=y_coord,
                    )

            @pytest.mark.parametrize(
                "missing_coord", [("xCoordinates"), ("yCoordinates")]
            )
            def test_given_partial_coordinates_raises(self, missing_coord: str):
                lateral_dict = dict(
                    id="42",
                    discharge=1.23,
                    numcoordinates=2,
                    xcoordinates=[42, 24],
                    ycoordinates=[24, 42],
                    locationtype="all",
                )
                lateral_dict[missing_coord.lower()] = None
                with pytest.raises(ValidationError) as exc_mssg:
                    Lateral(**lateral_dict)
                expected_error_mssg = TestModels.TestLateral.location_error
                assert expected_error_mssg in str(exc_mssg.value)

            def test_given_unknown_locationtype_raises(self):
                with pytest.raises(ValidationError) as exc_mssg:
                    location_type = "loremIpsum"
                    Lateral(
                        id="42",
                        discharge=1.23,
                        numcoordinates=2,
                        xcoordinates=[42, 24],
                        ycoordinates=[24, 42],
                        locationtype=location_type,
                    )
                expected_error_mssg = f"Value given ({location_type}) not accepted, should be one of: 1d, 2d, all"
                assert expected_error_mssg in str(exc_mssg.value)

            @pytest.mark.parametrize(
                "location_values",
                [
                    pytest.param(dict(nodeid="aNodeId"), id="nodeid given."),
                    pytest.param(
                        dict(branchid="aBranchId", chainage=42),
                        id="branchid + chainage given.",
                    ),
                    pytest.param(
                        dict(nodeid="", branchid="aBranchId", chainage=42),
                        id="Empty nodeid.",
                    ),
                ],
            )
            def test_given_valid_location_args_constructs_lateral(
                self, location_values: dict
            ):
                # 1. Define test data.
                default_values = dict(
                    id="42",
                    discharge=1.23,
                    locationtype="1d",
                )
                test_dict = {**default_values, **location_values}

                # 2. Run test.
                new_lateral = Lateral(**test_dict)

                # 3. Validate final expectations.
                for key, value in location_values.items():
                    assert new_lateral.dict()[key] == value

            @pytest.mark.parametrize(
                "location_dict",
                [
                    pytest.param(
                        dict(locationtype="1d", nodeid="aNodeId"), id="1D-With NodeId"
                    ),
                    pytest.param(
                        dict(locationtype="1d", branchid="aBranchId", chainage=4.2),
                        id="1D-With BranchId and Chainage",
                    ),
                    pytest.param(
                        dict(
                            locationtype="2d",
                            xcoordinates=[42, 24],
                            ycoordinates=[24, 42],
                            numcoordinates=2,
                        ),
                        id="2D-With coordinates",
                    ),
                    pytest.param(
                        dict(
                            locationtype="all",
                            xcoordinates=[42, 24],
                            ycoordinates=[24, 42],
                            numcoordinates=2,
                        ),
                        id="All-With coordinates",
                    ),
                ],
            )
            def test_given_valid_args_validates_locationtype(self, location_dict: str):
                # 1. Define test data.
                default_values = dict(
                    id="42",
                    discharge="realtime",
                )
                lateral_dict = {**default_values, **location_dict}
                # 2. Run test.
                lateral_cls = Lateral(**lateral_dict)

                # 3. Validate expectations.
                assert isinstance(lateral_cls, INIBasedModel)
                for key, value in lateral_dict.items():
                    assert lateral_cls.dict()[key] == value

        class TestValidateForcingData:
            """
            Class to test the different types of discharge forcings.
            """

            def test_dischargeforcings_fromfile(self):

                filepath = (
                    test_data_dir / "input/dflowfm_individual_files/FlowFM_bnd.ext"
                )
                m = ExtModel(filepath)
                assert len(m.lateral) == 72
                assert m.lateral[0].discharge == RealTime.realtime
                assert m.lateral[1].discharge == 1.23
                assert isinstance(m.lateral[3].discharge, ForcingModel)
                assert isinstance(m.lateral[3].discharge.forcing[0], Constant)
                assert m.lateral[3].discharge.forcing[0].name == "10637"

    class TestBoundary:
        """Class to test all methods contained in the
        hydrolib.core.dflowfm.ext.models.Boundary class"""

        def test_given_args_expected_values(self):
            # 1. Explicit declaration of parameters (to validate keys as they are written)
            dict_values = {
                "quantity": "42",
                "nodeid": "aNodeId",
                "locationfile": Path("aLocationFile"),
                "forcingfile": ForcingModel(),
                "bndwidth1d": 4.2,
                "bndbldepth": 2.4,
            }

            # 2. Create boundary.
            created_boundary = Boundary(**dict_values)

            # 3. Verify boundary values as expected.
            created_boundary_dict = created_boundary.dict()

            compare_data = dict(dict_values)
            expected_location_path = compare_data.pop("locationfile")

            for key, value in compare_data.items():
                assert created_boundary_dict[key] == value

            assert (
                created_boundary_dict["locationfile"]["filepath"]
                == expected_location_path
            )

        def test_given_args_as_alias_expected_values(self):
            # 1. Explicit declaration of parameters (to validate keys as they are written)
            dict_values = {
                "quantity": "42",
                "nodeid": "aNodeId",
                "locationfile": Path("aLocationFile"),
                "forcingFile": ForcingModel(),
                "bndWidth1D": 4.2,
                "bndBlDepth": 2.4,
            }

            # 2. Create boundary.
            created_boundary = Boundary(**dict_values)
            boundary_as_dict = created_boundary.dict()
            # 3. Verify boundary values as expected.
            assert boundary_as_dict["quantity"] == dict_values["quantity"]
            assert boundary_as_dict["nodeid"] == dict_values["nodeid"]
            assert (
                boundary_as_dict["locationfile"]["filepath"]
                == dict_values["locationfile"]
            )
            assert boundary_as_dict["forcingfile"] == dict_values["forcingFile"]
            assert boundary_as_dict["bndwidth1d"] == dict_values["bndWidth1D"]
            assert boundary_as_dict["bndbldepth"] == dict_values["bndBlDepth"]

        class TestValidateRootValidator:
            """
            Test class to validate the paradigms when evaluating
            check_nodeid_or_locationfile_present.
            """

            @pytest.mark.parametrize(
                "dict_values",
                [
                    pytest.param(dict(), id="No entries."),
                    pytest.param(
                        dict(nodeid=None, locationfile=None), id="Entries are None."
                    ),
                    pytest.param(
                        dict(nodeid="", locationfile=""), id="Entries are Empty."
                    ),
                ],
            )
            def test_given_no_values_raises_valueerror(self, dict_values: dict):
                with pytest.raises(ValueError) as exc_mssg:
                    Boundary.check_nodeid_or_locationfile_present(dict_values)

                # 3. Verify final expectations.
                expected_error_mssg = (
                    "Either nodeId or locationFile fields should be specified."
                )
                assert str(exc_mssg.value) == expected_error_mssg

            @pytest.mark.parametrize(
                "dict_values",
                [
                    pytest.param(dict(nodeid="aNodeId"), id="NodeId present."),
                    pytest.param(
                        dict(locationfile=Path("aLocationFile")),
                        id="LocationFile present.",
                    ),
                    pytest.param(
                        dict(nodeid="bNodeId", locationfile="bLocationFile"),
                        id="Both present.",
                    ),
                ],
            )
            def test_given_dict_values_doesnot_raise(self, dict_values: dict):
                return_values = Boundary.check_nodeid_or_locationfile_present(
                    dict_values
                )
                assert dict_values == return_values

        class TestValidateFromCtor:
            """
            Test class to validate the validation during default object creation.
            """

            @pytest.mark.parametrize(
                "dict_values",
                [
                    pytest.param(dict(), id="No entries."),
                    pytest.param(
                        dict(nodeid=None, locationfile=None), id="Entries are None."
                    ),
                    pytest.param(dict(nodeid=""), id="NodeId is empty."),
                ],
            )
            def test_given_no_values_raises_valueerror(self, dict_values: dict):
                required_values = dict(quantity="aQuantity")
                test_values = {**dict_values, **required_values}
                with pytest.raises(ValueError) as exc_mssg:
                    Boundary(**test_values)

                # 3. Verify final expectations.
                expected_error_mssg = (
                    "Either nodeId or locationFile fields should be specified."
                )
                assert expected_error_mssg in str(exc_mssg.value)

            @pytest.mark.parametrize(
                "dict_values",
                [
                    pytest.param(dict(nodeid="aNodeId"), id="NodeId present."),
                    pytest.param(
                        dict(locationfile=Path("aLocationFile")),
                        id="LocationFile present.",
                    ),
                    pytest.param(
                        dict(nodeid="bNodeId", locationfile=Path("bLocationFile")),
                        id="Both present.",
                    ),
                ],
            )
            def test_given_dict_values_doesnot_raise(self, dict_values: dict):
                required_values = dict(quantity="aQuantity", forcingfile=ForcingModel())
                test_values = {**dict_values, **required_values}
                created_boundary = Boundary(**test_values)

                expected_locationfile = test_values.pop("locationfile", None)

                for key, value in test_values.items():
                    if key == "forcing_file":
                        value = value.dict()
                    assert created_boundary.dict()[key] == value

                assert (
                    created_boundary.dict()["locationfile"]["filepath"]
                    == expected_locationfile
                )

    class TestExtModel:
        def test_ext_model_correct_default_serializer_config(self):
            model = ExtModel()

            assert model.serializer_config.section_indent == 0
            assert model.serializer_config.property_indent == 0
            assert model.serializer_config.datablock_indent == 8
            assert model.serializer_config.float_format == ""
            assert model.serializer_config.datablock_spacing == 2
            assert model.serializer_config.comment_delimiter == "#"
            assert model.serializer_config.skip_empty_properties == True
