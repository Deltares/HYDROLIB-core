import inspect
from typing import Any, Dict, List, Union

import pytest
from pydantic import ValidationError
from unittest.mock import MagicMock
from hydrolib.core.dflowfm.friction.models import FrictionType
from hydrolib.core.dflowfm.ini.parser import Parser, ParserConfig
from hydrolib.core.dflowfm.structure.models import (
    Compound,
    Culvert,
    FlowDirection,
    Orifice,
    Pump,
    Structure,
    StructureModel,
    UniversalWeir,
    Weir,
)

from tests.utils import (
    WrapperTest,
    invalid_test_data_dir,
    test_data_dir,
)

uniqueid_str = "Unique structure id (max. 256 characters)."


def mock_structure_check_location(dict_values: Dict[str, Any], structure_type=Structure) -> MagicMock:
    mock_structure = MagicMock(spec=structure_type)
    mock_structure.model_dump.return_value = dict_values
    mock_structure.check_location = Structure.check_location.__get__(mock_structure, Structure)
    mock_structure.validate_coordinates_in_model = Structure.validate_coordinates_in_model
    mock_structure.validate_branch_and_chainage_in_model = Structure.validate_branch_and_chainage_in_model
    mock_structure.__class__ = structure_type  # Ensure the mock is treated as a Structure instance
    return mock_structure


def test_structure_model():
    filepath = (
        test_data_dir
        / "input/e02/c11_korte-woerden-1d/dimr_model/dflowfm/structures.ini"
    )
    m = StructureModel(filepath)
    assert len(m.structure) == 12
    assert isinstance(m.structure[-1], Compound)
    assert isinstance(m.structure[0], Orifice)
    assert isinstance(m.structure[2], Weir)
    assert isinstance(m.structure[5], Pump)


def test_universal_construction_with_parser():
    parser = Parser(ParserConfig())

    input_str = inspect.cleandoc(
        """
        [Structure]
        id                = uweir_id         # Unique structure id (max. 256 characters).
        name              = W002             # Given name in the user interface.
        branchId          = branch           # (optional) Branch on which the structure is located.
        chainage          = 6.0              # (optional) Chainage on the branch (m).
        type              = universalWeir    # Structure type
        allowedFlowDir    = positive         # Possible values: both, positive, negative, none.
        numLevels         = 2                # Number of yz-Values.
        yValues           = 1.0 2.0          # y-values of the cross section (m) 
        zValues           = 3.0 4.0          # z-values of the cross section (m). (number of values = numLevels)
        crestLevel        = 10.5             # Crest level of weir (m AD)
        dischargeCoeff    = 0.5              # Discharge coefficient c_e (-)
        """
    )

    for line in input_str.splitlines():
        parser.feed_line(line)

    document = parser.finalize()

    wrapper = WrapperTest[UniversalWeir].parse_obj({"val": document.sections[0]})
    universal_weir = wrapper.val

    assert universal_weir.id == "uweir_id"
    assert universal_weir.name == "W002"
    assert universal_weir.branchid == "branch"
    assert universal_weir.chainage == pytest.approx(6.0)
    assert universal_weir.allowedflowdir == FlowDirection.positive
    assert universal_weir.numlevels == 2
    assert universal_weir.yvalues == [1.0, 2.0]
    assert universal_weir.zvalues == [3.0, 4.0]
    assert universal_weir.crestlevel == pytest.approx(10.5)
    assert universal_weir.dischargecoeff == pytest.approx(0.5)


def test_weir_and_universal_weir_resolve_from_parsed_document():
    parser = Parser(ParserConfig())

    input_str = inspect.cleandoc(
        """
        [Structure]
        id                = weir_id     # Unique structure id (max. 256 characters).
        name              = W001        # Given name in the user interface.
        branchId          = branch      # Branch on which the structure is located.
        chainage          = 3.0         # Chainage on the branch (m).
        type              = weir        # Structure type; must read weir
        allowedFlowDir    = positive    # Possible values: both, positive, negative, none.
        crestLevel        = 10.5        # Crest level of weir (m AD).
        crestWidth        =             # Width of the weir (m).
        useVelocityHeight = false       # Flag indicating whether the velocity height is to be calculated or not.

        [Structure]
        id                = uweir_id         # Unique structure id (max. 256 characters).
        name              = W002             # Given name in the user interface.
        branchId          = branch           # Branch on which the structure is located.
        chainage          = 6.0              # Chainage on the branch (m).
        type              = universalWeir    # Structure type; must read universalWeir
        allowedFlowDir    = positive         # Possible values: both, positive, negative, none.
        numLevels         = 2                # Number of yz-Values.
        yValues           = 1.0 2.0          # y-values of the cross section (m). (number of values = numLevels) 
        zValues           = 3.0 4.0          # z-values of the cross section (m). (number of values = numLevels)
        crestLevel        = 10.5             # Crest level of weir (m AD).
        dischargeCoeff    = 0.5              # Discharge coefficient c_e (-).
        """
    )

    for line in input_str.splitlines():
        parser.feed_line(line)

    document = parser.finalize()

    wrapper = WrapperTest[List[Union[Weir, UniversalWeir]]].parse_obj(
        {"val": document.sections}
    )
    expected_structures = [
        Weir(
            id="weir_id",
            name="W001",
            branchid="branch",
            chainage=3.0,
            allowedflowdir=FlowDirection.positive,
            crestlevel=10.5,
            crestwidth=None,
            usevelocityheight=False,
            _header="Structure",
        ),
        UniversalWeir(
            id="uweir_id",
            name="W002",
            branchid="branch",
            chainage=6.0,
            allowedflowdir=FlowDirection.positive,
            numlevels=2,
            yvalues=[1.0, 2.0],
            zvalues=[3.0, 4.0],
            crestlevel=10.5,
            dischargecoeff=0.5,
            _header="Structure",
        ),
    ]

    for val, expected in zip(wrapper.val, expected_structures):
        # TODO Make sure datablock never ends up in these structures!
        assert val.dict(exclude={"datablock"}) == expected.dict()


def test_read_structures_missing_structure_field_raises_correct_error():
    file = "missing_structure_field.ini"
    identifier = "Structure2"
    field = "crestLevel"

    filepath = invalid_test_data_dir / file

    with pytest.raises(ValueError) as error:
        StructureModel(filepath)

    expected_message = f"{file} -> structure -> 1 -> {identifier} -> {field}"
    assert expected_message in str(error.value)


@pytest.fixture
def locfields_structure():
    """example location fields for creating a regular Structure"""
    return {"branchid": "branch", "chainage": 10}


def test_create_structure_without_id(locfields_structure):
    field = "id"
    with pytest.raises(ValueError) as error:
        _ = Structure(**locfields_structure)  # Intentionally no id+type

    expected_message = f"{field}"
    assert expected_message in str(error.value)
    assert error.value.errors()[0]["type"] == "value_error.missing"


def test_create_structure_without_type(locfields_structure):
    identifier = "structA"
    field = "type"
    with pytest.raises(ValueError) as error:
        _ = Structure(id=identifier, **locfields_structure)  # Intentionally no type

    expected_message = f"{identifier} -> {field}"
    assert expected_message in str(error.value)
    assert error.value.errors()[0]["type"] == "value_error.missing"


@pytest.mark.parametrize(
    "structure_type,expected",
    [
        ("WEIR", "weir"),
        ("UniversalWeir", "universalweir"),
        ("Culvert", "culvert"),
        ("Pump", "pump"),
        ("Orifice", "orifice"),
    ],
)
def test_parses_structure_type_case_insensitive(locfields_structure, structure_type, expected):
    structure = Structure(type=structure_type, **locfields_structure)

    assert structure.type == expected


@pytest.mark.parametrize(
    "input,expected",
    [
        ("Compound", "compound"),
    ],
)
def test_parses_compound_type_case_insensitive(input, expected):
    structure = Structure(type=input)

    assert structure.type == expected


def _get_allowedflowdir_cases() -> List:
    return [
        ("None", "none"),
        ("Positive", "positive"),
        ("NEGATIVE", "negative"),
        ("Both", "both"),
    ]



@pytest.mark.parametrize(
    "input,expected",
    _get_allowedflowdir_cases(),
)
def test_universalweir_parses_flowdirection_case_insensitive(input, expected):
    structure = UniversalWeir(
        allowedflowdir=input,
        id="strucid",
        branchid="branchid",
        chainage="1",
        crestlevel="1",
        numlevels=0,
        yvalues=[],
        zvalues=[],
        dischargecoeff="1",
    )

    assert structure.allowedflowdir == expected


@pytest.mark.parametrize(
    "input,expected",
    _get_allowedflowdir_cases(),
)
def test_culvert_parses_flowdirection_case_insensitive(input, expected):

    structure = Culvert(
        allowedflowdir=input,
        id="strucid",
        branchid="branchid",
        chainage="1",
        leftlevel="1",
        rightlevel="1",
        csdefid="",
        length="1",
        inletlosscoeff="1",
        outletlosscoeff="1",
        inletlosvalveonoffscoeff="1",
        valveonoff="1",
        valveopeningheight="1",
        numlosscoeff="1",
        relopening=[1],
        losscoeff=[1],
        bedfrictiontype=FrictionType.manning,
        bedfriction="1",
        subtype="invertedSiphon",
        bendlosscoeff="1",
    )

    assert structure.allowedflowdir == expected


@pytest.mark.parametrize(
    "input,expected",
    [("Culvert", "culvert"), ("INVERTEDSiphon", "invertedSiphon")],
)
def test_culvert_parses_subtype_case_insensitive(input, expected):

    structure = Culvert(
        subtype=input,
        allowedflowdir="both",
        id="strucid",
        branchid="branchid",
        chainage="1",
        leftlevel="1",
        rightlevel="1",
        csdefid="",
        length="1",
        inletlosscoeff="1",
        outletlosscoeff="1",
        inletlosvalveonoffscoeff="1",
        valveonoff="1",
        valveopeningheight="1",
        numlosscoeff="1",
        relopening=[1],
        losscoeff=[1],
        bedfrictiontype=FrictionType.manning,
        bedfriction="1",
        bendlosscoeff="1" if input.lower() == "invertedsiphon" else None,
    )

    assert structure.subtype == expected


def create_structure_values(struture_type: str) -> dict:
    """Create a dict with example field values for all common structure attributes."""
    return dict(
        id="structure_id",
        name="structure_name",
        type=struture_type,
        branchid="branch_id",
        chainage="1.23",
    )



class TestStructure:
    """
    Wrapper class to test all the methods and subclasses in:
    hydrolib.core.dflowfm.structure.models.py Structure class.
    """

    class TestRootValidator:
        """
        Wrapper class to validate the paradigms that point to root_validators
        in the Structure class
        """

        long_culvert_err = "Specify location by setting `num/x/yCoordinates` for a LongCulvert structure."
        dambreak_err = "Specify location either by setting `num/x/yCoordinates` or `polylinefile` fields for a Dambreak structure."
        structure_err = "Specify location either by setting `branchId` and `chainage` or `num/x/yCoordinates` or `polylinefile` fields."

        @pytest.mark.parametrize(
            "structure_type, error_mssg",
            [
                pytest.param(
                    "",
                    structure_err,
                    id="No structure raises.",
                ),
                pytest.param(
                    None,
                    structure_err,
                    id="None structure raises.",
                ),
                pytest.param(
                    "weir",
                    structure_err,
                    id="Weir raises.",
                ),
                pytest.param(
                    "universalWeir",
                    structure_err,
                    id="UniversalWeir raises.",
                ),
                pytest.param(
                    "culvert",
                    structure_err,
                    id="Culvert raises.",
                ),
                pytest.param(
                    "longCulvert",
                    long_culvert_err,
                    id="LongCulvert raises.",
                ),
                pytest.param(
                    "orifice",
                    structure_err,
                    id="Orifice raises.",
                ),
                pytest.param(
                    "bridge",
                    structure_err,
                    id="Bridge raises.",
                ),
                pytest.param(
                    "gate",
                    structure_err,
                    id="Gate raises.",
                ),
                pytest.param(
                    "generalStructure",
                    structure_err,
                    id="GeneralStructure raises.",
                ),
                pytest.param(
                    "dambreak",
                    dambreak_err,
                    id="Dambreak raises.",
                ),
                pytest.param(
                    "compound", None, id="Compound DOES NOT raise." # does_not_raise(),
                ),
            ],
        )
        def test_check_location_given_no_values_raises_expectation(
            self, structure_type, error_mssg: str
        ):
            input_dict = dict(
                notAValue="Not a relevant value 1",
                type=structure_type,
                numcoordinates=None,
                xcoordinates=None,
                ycoordinates=None,
                branchid=None,
                chainage=None,
            )
            mock_structure = mock_structure_check_location(input_dict)
            if error_mssg is None:
                assert mock_structure.check_location()
            else:
                with pytest.raises(ValueError) as exc_err:
                    mock_structure.check_location()

                assert str(exc_err.value) == error_mssg

        def test_check_nolocation_given_compound_structure_raises_nothing(self):
            input_dict = dict(
                notAValue="Not a relevant value 2",
                numcoordinates=None,
                xcoordinates=None,
                ycoordinates=None,
                branchid=None,
                chainage=None,
            )
            mock_structure = mock_structure_check_location(input_dict)
            assert mock_structure.check_location()


        def test_check_location_given_compound_structure_raises_error(self):
            input_dict = dict(
                notAValue="Not a relevant value 3",
                numcoordinates=None,
                xcoordinates=None,
                ycoordinates=None,
                branchid="branch01",
                chainage=123.4,
            )
            mock_structure = mock_structure_check_location(input_dict)
            assert mock_structure.check_location(input_dict)

            # TODO: issue 214: replace the above test code by the test
            # code below once the D-HYDRO Suite 1D2D has fixed issue
            # FM1D2D-1935 for compound structures.
            # with pytest.raises(AssertionError) as exc_err:
            #     _ = Compound.check_location(input_dict)
            #     assert (
            #         str(exc_err.value)
            #         == "No `num/x/yCoordinates` nor `branchId+chainage` are allowed for a compound structure."
            #     )

        @pytest.mark.parametrize(
            "dict_values",
            [
                pytest.param(
                    dict(branchid="", chainage=None),
                    id="Empty branchid, Chainage is None.",
                ),
                pytest.param(
                    dict(branchid="aValue", chainage=None), id="Chainage is None."
                ),
                pytest.param(
                    dict(branchid="", chainage=2.4), id="Only chainage value."
                ),
            ],
        )
        def test_check_location_given_invalid_branchid_chainage_raises_value_error(
            self, dict_values: dict
        ):
            with pytest.raises(ValueError) as exc_err:
                Structure.check_location(dict_values)
            assert (
                str(exc_err.value)
                == "A valid value for branchId and chainage is required when branchId key is specified."
            )

        wrong_coord_test_cases = [
            pytest.param(
                [],
                id="Empty list",
            ),
            pytest.param(
                [2, 4, 4, 2],
                id="Too many coords",
            ),
        ]

        @pytest.mark.parametrize(
            "x_coords",
            wrong_coord_test_cases,
        )
        @pytest.mark.parametrize(
            "y_coords",
            wrong_coord_test_cases,
        )
        def test_check_location_given_invalid_coordinates_raises_assertion_error(
            self, x_coords: List[float], y_coords: List[float]
        ):
            n_coords = 2
            dict_values = dict(
                numcoordinates=n_coords,
                xcoordinates=x_coords,
                ycoordinates=y_coords,
            )
            mock_structure = mock_structure_check_location(dict_values)

            with pytest.raises(ValueError) as exc_err:
                mock_structure.check_location()

            assert (
                str(exc_err.value)
                == f"Expected {n_coords} coordinates, given {len(x_coords)} for xCoordinates and {len(y_coords)} for yCoordinates."
            )

        @pytest.mark.parametrize(
            "dict_values",
            [
                pytest.param(
                    dict(
                        numcoordinates=2,
                        xcoordinates=[4.2, 2.4],
                        ycoordinates=[2.4, 4.2],
                    ),
                    id="Coordinates given.",
                ),
                pytest.param(
                    dict(branchid="aBranchid", chainage="aChainage"),
                    id="branchid + chainage.",
                ),
            ],
        )
        def test_check_location_given_valid_values(self, dict_values: dict):
            mock_structure = mock_structure_check_location(dict_values)
            assert mock_structure.check_location()


    class TestValidateBranchAndChainageInModel:
        """
        Class to validate the paradigms of validate_branch_and_chainage_in_model
        """

        @pytest.mark.parametrize(
            "branch_id, chainage, expectation",
            [
                pytest.param(None, None, False, id="Both None"),
                pytest.param("aValue", 42, True, id="Both Valid"),
            ],
        )
        def test_given_valid_values_returns_expectation(
            self, branch_id: str, chainage: float, expectation: bool
        ):
            dict_values = dict(branchid=branch_id, chainage=chainage)
            validation = Structure.validate_branch_and_chainage_in_model(dict_values)
            assert validation == expectation

        @pytest.mark.parametrize(
            "dict_values",
            [
                pytest.param(
                    dict(branchid="aBranchId", chainage=None), id="No valid chainage"
                ),
                pytest.param(dict(branchid="", chainage=None), id="No valid branchId"),
            ],
        )
        def test_given_invalid_values_raises_expectations(self, dict_values: dict):
            with pytest.raises(ValueError) as exc_err:
                Structure.validate_branch_and_chainage_in_model(dict_values)
            assert (
                str(exc_err.value)
                == "A valid value for branchId and chainage is required when branchId key is specified."
            )

    class TestValidateCoordinatesInModel:
        """
        Class to validate the paradigms of validate_coordinates_in_model
        """

        @pytest.mark.parametrize(
            "dict_values, expectation",
            [
                pytest.param(dict(), False, id="No values."),
                pytest.param(
                    dict(numcoordinates=None), False, id="Missing x_y_coordinates"
                ),
                pytest.param(
                    dict(numcoordinates=None, ycoordinates=None),
                    False,
                    id="Missing xcoordinates",
                ),
                pytest.param(
                    dict(numcoordinates=None, xcoordinates=None),
                    False,
                    id="Missing ycoordinates",
                ),
                pytest.param(
                    dict(
                        numcoordinates=2,
                        xcoordinates=[4.2, 2.4],
                        ycoordinates=[2.4, 4.2],
                    ),
                    True,
                    id="With 2 coordinates.",
                ),
                pytest.param(
                    dict(
                        numcoordinates=3,
                        xcoordinates=[4.2, 2.4, 4.4],
                        ycoordinates=[2.4, 4.2, 2.2],
                    ),
                    True,
                    id="With 3 coordinates.",
                ),
            ],
        )
        def test_given_valid_values_returns_expectation(
            self, dict_values: dict, expectation: bool
        ):
            validation = Structure.validate_coordinates_in_model(dict_values)
            assert validation == expectation

        def test_given_different_coordinate_length_values_raises_value_error(self):
            with pytest.raises(ValueError) as exc_err:
                Structure.validate_coordinates_in_model(
                    dict(
                        numcoordinates=2,
                        xcoordinates=[10, 20, 30],
                        ycoordinates=[10, 20, 30, 50],
                    )
                )
            assert (
                str(exc_err.value)
                == "Expected 2 coordinates, given 3 for xCoordinates and 4 for yCoordinates."
            )

        @pytest.mark.parametrize("n_coords", [(0), (1)])
        def test_given_less_than_2_coordinates_raises_value_error(self, n_coords: int):
            with pytest.raises(ValueError) as exc_err:
                Structure.validate_coordinates_in_model(
                    dict(
                        numcoordinates=n_coords,
                        xcoordinates=[10, 20, 30],
                        ycoordinates=[10, 20, 30, 50],
                    )
                )
            assert (
                str(exc_err.value)
                == f"Expected at least 2 coordinates, but only {n_coords} declared."
            )

