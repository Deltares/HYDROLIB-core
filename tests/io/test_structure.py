import inspect
from contextlib import nullcontext as does_not_raise
from pathlib import Path
from typing import Any, Callable, List, Union

import pytest
from attr.validators import optional
from pydantic.error_wrappers import ValidationError

from hydrolib.core.io.ini.parser import Parser, ParserConfig
from hydrolib.core.io.structure.models import (
    Bridge,
    Compound,
    Culvert,
    Dambreak,
    DambreakAlgorithm,
    FlowDirection,
    Orifice,
    Pump,
    Structure,
    StructureModel,
    UniversalWeir,
    Weir,
)

from ..utils import WrapperTest, invalid_test_data_dir, test_data_dir

uniqueid_str = "Unique structure id (max. 256 characters)."


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
    assert universal_weir.chainage == 6.0
    assert universal_weir.allowedflowdir == FlowDirection.positive
    assert universal_weir.numlevels == 2
    assert universal_weir.yvalues == [1.0, 2.0]
    assert universal_weir.zvalues == [3.0, 4.0]
    assert universal_weir.crestlevel == 10.5
    assert universal_weir.dischargecoeff == 0.5


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

    with pytest.raises(ValidationError) as error:
        StructureModel(filepath)

    expected_message = f"{file} -> structure -> 1 -> {identifier} -> {field}"
    assert expected_message in str(error.value)


@pytest.mark.parametrize(
    "input,expected",
    [
        ("WEIR", "weir"),
        ("UniversalWeir", "universalWeir"),
        ("Culvert", "culvert"),
        ("Pump", "pump"),
        ("Compound", "compound"),
        ("Orifice", "orifice"),
    ],
)
def test_parses_type_case_insensitive(input, expected):
    structure = Structure(type=input, branchid="branchid", chainage="1")

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
        relopening=[],
        losscoeff=[],
        bedfrictiontype="",
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
        relopening=[],
        losscoeff=[],
        bedfrictiontype="",
        bedfriction="1",
        bendlosscoeff="1",
    )

    assert structure.subtype == expected


class TestBridge:
    """
    Wrapper class to test all the methods and subclasses in:
    hydrolib.core.io.structure.models.py Bridge class
    """

    def test_create_a_bridge_from_scratch(self):
        bridge = Bridge(
            id="b003",
            name="B003",
            branchid="B1",
            chainage=5.0,
            allowedflowdir=FlowDirection.both,
            csdefid="W_980.1S_0",
            shift=-1.23,
            inletlosscoeff=1,
            outletlosscoeff=1,
            frictiontype="Strickler",
            friction=70,
            length=100,
            comments=Bridge.Comments(
                name="B stands for Bridge, 003 because we expect to have at most 999 weirs"
            ),
        )

        assert isinstance(
            bridge, Structure
        ), "Bridge should also be an instance of a Structure"

        assert bridge.id == "b003"
        assert bridge.name == "B003"
        assert bridge.branchid == "B1"
        assert bridge.chainage == 5.0
        assert bridge.allowedflowdir == FlowDirection.both
        assert bridge.csdefid == "W_980.1S_0"
        assert bridge.shift == -1.23
        assert bridge.inletlosscoeff == 1
        assert bridge.outletlosscoeff == 1
        assert bridge.frictiontype == "Strickler"
        assert bridge.friction == 70
        assert bridge.length == 100
        assert (
            bridge.comments.name
            == "B stands for Bridge, 003 because we expect to have at most 999 weirs"
        )

        assert bridge.comments.id == uniqueid_str

    def test_bridge_construction_with_parser(self):
        parser = Parser(ParserConfig())

        input_str = inspect.cleandoc(
            """
            [Structure]
            type = bridge                   # Structure type; must read bridge
            id = RS1-KBR31                  # Unique structure id (max. 256 characters).
            name = RS1-KBR31name            # Given name in the user interface.
            branchid = riv_RS1_264          # (optional) Branch on which the structure is located.
            chainage = 104.184              # (optional) Chainage on the branch (m)
            allowedFlowDir = both           # Possible values: both, positive, negative, none.
            csDefId = W_980.1S_0            # Id of Cross-Section Definition.
            shift = 0.0                     # Vertical shift of the cross section definition [m]. Defined positive upwards.
            inletLossCoeff = 1              # Inlet loss coefficient [-], ?_i.
            outletLossCoeff = 1
            frictionType = Strickler        # Friction type
            friction = 70
            length = 9.75
            """
        )

        for line in input_str.splitlines():
            parser.feed_line(line)

        document = parser.finalize()

        wrapper = WrapperTest[Bridge].parse_obj({"val": document.sections[0]})
        bridge = wrapper.val

        assert isinstance(
            bridge, Structure
        ), "Bridge should also be an instance of a Structure"

        assert bridge.id == "RS1-KBR31"
        assert bridge.name == "RS1-KBR31name"
        assert bridge.branchid == "riv_RS1_264"
        assert bridge.chainage == 104.184
        assert bridge.type == "bridge"
        assert bridge.allowedflowdir == FlowDirection.both
        assert bridge.csdefid == "W_980.1S_0"
        assert bridge.shift == 0.0
        assert bridge.inletlosscoeff == 1
        assert bridge.outletlosscoeff == 1
        assert bridge.frictiontype == "Strickler"
        assert bridge.friction == 70
        assert bridge.length == 9.75

    def test_bridge_with_unknown_parameters(self):
        parser = Parser(ParserConfig())

        input_str = inspect.cleandoc(
            """
            [Structure]
            type = bridge                   # Structure type; must read bridge
            id = RS1-KBR31                  # Unique structure id (max. 256 characters).
            name = RS1-KBR31name            # Given name in the user interface.
            branchid = riv_RS1_264          # (optional) Branch on which the structure is located.
            chainage = 104.184              # (optional) Chainage on the branch (m)
            allowedFlowDir = both           # Possible values: both, positive, negative, none.
            csDefId = W_980.1S_0            # Id of Cross-Section Definition.

            # ----------------------------------------------------------------------
            bedLevel           = 10.0        # A deliberately added unknown (in fact: old, unsupported) property
            # ----------------------------------------------------------------------

            shift = 0.0                     # Vertical shift of the cross section definition [m]. Defined positive upwards.
            inletLossCoeff = 1              # Inlet loss coefficient [-], ?_i.
            outletLossCoeff = 1
            frictionType = Strickler        # Friction type
            friction = 70
            length = 9.75
            """
        )

        for line in input_str.splitlines():
            parser.feed_line(line)

        document = parser.finalize()

        wrapper = WrapperTest[Bridge].parse_obj({"val": document.sections[0]})
        bridge = wrapper.val

        assert bridge.bedlevel == "10.0"  # type: ignore (note: deliberately lowercase key here)

        assert bridge.id == "RS1-KBR31"
        assert bridge.name == "RS1-KBR31name"
        assert bridge.branchid == "riv_RS1_264"
        assert bridge.chainage == 104.184
        assert bridge.type == "bridge"
        assert bridge.allowedflowdir == FlowDirection.both
        assert bridge.csdefid == "W_980.1S_0"
        assert bridge.shift == 0.0
        assert bridge.inletlosscoeff == 1
        assert bridge.outletlosscoeff == 1
        assert bridge.frictiontype == "Strickler"
        assert bridge.friction == 70
        assert bridge.length == 9.75

    def test_bridge_with_missing_required_parameters(self):
        parser = Parser(ParserConfig())

        input_str = inspect.cleandoc(
            """
            [Structure]
            type = bridge                   # Structure type; must read bridge
            id = RS1-KBR31                  # Unique structure id (max. 256 characters).
            name = RS1-KBR31name            # Given name in the user interface.
            branchid = riv_RS1_264          # (optional) Branch on which the structure is located.
            chainage = 104.184              # (optional) Chainage on the branch (m)
            allowedFlowDir = both           # Possible values: both, positive, negative, none.
            # csDefId = W_980.1S_0            # Id of Cross-Section Definition.
            # shift = 0.0                     # Vertical shift of the cross section definition [m]. Defined positive upwards.
            # inletLossCoeff = 1              # Inlet loss coefficient [-], ?_i.
            # outletLossCoeff = 1
            # frictionType = Strickler        # Friction type
            # friction = 70
            # length = 9.75
            """
        )

        for line in input_str.splitlines():
            parser.feed_line(line)

        document = parser.finalize()

        expected_message = "7 validation errors for WrapperTest[Bridge]"
        with pytest.raises(ValueError) as exc_err:
            wrapper = WrapperTest[Bridge].parse_obj({"val": document.sections[0]})
            bridge = wrapper.val
        assert expected_message in str(exc_err.value)

        assert "bridge" not in locals()  # Bridge structure should not have been created


class TestStructure:
    """
    Wrapper class to test all the methods and subclasses in:
    hydrolib.core.io.structure.models.py Structure class.
    """

    class TestRootValidator:
        """
        Wrapper class to validate the paradigms that point to root_validators
        in the Structure class
        """

        long_culvert_err = (
            "`num/x/yCoordinates` are mandatory for a LongCulvert structure."
        )
        dambreak_err = "`num/x/yCoordinates` are mandatory for a Dambreak structure."
        structure_err = "Specify location either by setting `branchId` and `chainage` or `num/x/yCoordinates` fields."

        @pytest.mark.parametrize(
            "type, expectation, error_mssg",
            [
                pytest.param(
                    "",
                    pytest.raises(AssertionError),
                    structure_err,
                    id="No structure raises.",
                ),
                pytest.param(
                    None,
                    pytest.raises(AssertionError),
                    structure_err,
                    id="None structure raises.",
                ),
                pytest.param(
                    "weir",
                    pytest.raises(AssertionError),
                    structure_err,
                    id="Weir raises.",
                ),
                pytest.param(
                    "universalWeir",
                    pytest.raises(AssertionError),
                    structure_err,
                    id="UniversalWeir raises.",
                ),
                pytest.param(
                    "culvert",
                    pytest.raises(AssertionError),
                    structure_err,
                    id="Culvert raises.",
                ),
                pytest.param(
                    "longCulvert",
                    pytest.raises(AssertionError),
                    long_culvert_err,
                    id="LongCulvert raises.",
                ),
                pytest.param(
                    "orifice",
                    pytest.raises(AssertionError),
                    structure_err,
                    id="Orifice raises.",
                ),
                pytest.param(
                    "bridge",
                    pytest.raises(AssertionError),
                    structure_err,
                    id="Bridge raises.",
                ),
                pytest.param(
                    "gate",
                    pytest.raises(AssertionError),
                    structure_err,
                    id="Gate raises.",
                ),
                pytest.param(
                    "generalStructure",
                    pytest.raises(AssertionError),
                    structure_err,
                    id="GeneralStructure raises.",
                ),
                pytest.param(
                    "dambreak",
                    pytest.raises(AssertionError),
                    dambreak_err,
                    id="Dambreak raises.",
                ),
                pytest.param(
                    "compound", does_not_raise(), None, id="Compound DOES NOT raise."
                ),
            ],
        )
        def test_check_location_given_no_values_raises_expectation(
            self, type: str, expectation, error_mssg: str
        ):
            with expectation as exc_err:
                input_dict = dict(
                    notAValue="Not a relevant value",
                    type=type,
                    numcoordinates=None,
                    xcoordinates=None,
                    ycoordinates=None,
                    branchid=None,
                    chainage=None,
                )
                return_value = Structure.check_location(input_dict)
                if not error_mssg:
                    assert return_value == input_dict
                    return
            assert str(exc_err.value) == error_mssg

        def test_check_location_given_compound_structure_raises_nothing(self):
            input_dict = dict(
                notAValue="Not a relevant value",
                numcoordinates=None,
                xcoordinates=None,
                ycoordinates=None,
                branchid=None,
                chainage=None,
            )
            return_value = Compound.check_location(input_dict)
            assert return_value == input_dict

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
            with pytest.raises(ValueError) as exc_err:
                Structure.check_location(
                    dict(
                        numcoordinates=n_coords,
                        xcoordinates=x_coords,
                        ycoordinates=y_coords,
                    )
                )
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
            return_value = Structure.check_location(dict_values)
            assert return_value == dict_values

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


class TestDambreakAlgorithm:
    """
    Wrapper class to test all the methods in:
    hydrolib.core.io.structure.models.py DambreakAlgorithm enum class.
    """

    @pytest.mark.parametrize(
        "enum_value, enum_description",
        [
            pytest.param(1, "van der Knaap, 2000"),
            pytest.param(2, "Verheij-van der Knaap, 2002"),
            pytest.param(3, "Predefined time series, dambreakLevelsAndWidths"),
        ],
    )
    def test_get_enum_as_str_returns_description(
        self, enum_value: int, enum_description: str
    ):
        assert DambreakAlgorithm(enum_value).description == enum_description


class DambreakTestCases:
    """Just a wrapper so it can be referenced from other classes."""

    check_location_err = (
        "`num/x/yCoordinates` or `polylineFile` are mandatory for a Dambreak structure."
    )
    too_few_coords = "Expected at least 2 coordinates, but only {} declared."
    mismatch_coords = (
        "Expected {} coordinates, given {} for xCoordinates and {} for yCoordinates."
    )


class TestDambreak:
    """
    Wrapper class to test all the methods and sublcasses in:
    hydrolib.core.io.structure.models.py Dambreak class.
    """

    @pytest.fixture
    def default_dambreak_values(self) -> dict:
        return dict(
            id="NLNJ-2021",
            name="NederlandNaranjito2021",
            type="dambreak",
            startlocationx=4.2,
            startlocationy=2.4,
            algorithm=1,
            crestlevelini=1,
            breachwidthini=24,
            crestlevelmin=42,
            t0=2.2,
            timetobreachtomaximumdepth=4.4,
            f1=22.4,
            f2=44.2,
            ucrit=44.22,
            waterlevelupstreamlocationx=1.2,
            waterlevelupstreamlocationy=2.3,
            waterleveldownstreamlocationx=3.4,
            waterleveldownstreamlocationy=4.5,
            waterlevelupstreamnodeid="anUpstreamNodeId",
            waterleveldownstreamnodeid="aDownstreamNodeId",
        )

    @pytest.fixture
    def valid_dambreak_values(self, default_dambreak_values: dict) -> dict:
        coordinates_dict = dict(
            numcoordinates=2,
            xcoordinates=[4.2, 2.4],
            ycoordinates=[2.4, 4.2],
        )
        return {**default_dambreak_values, **coordinates_dict}

    @pytest.mark.parametrize(
        "location_dict, err_mssg",
        [
            pytest.param(
                dict(),
                DambreakTestCases.check_location_err,
                id="No values.",
            ),
            pytest.param(
                dict(numcoordinates=None),
                DambreakTestCases.check_location_err,
                id="Missing x_y_coordinates",
            ),
            pytest.param(
                dict(numcoordinates=None, ycoordinates=None),
                DambreakTestCases.check_location_err,
                id="Missing xcoordinates",
            ),
            pytest.param(
                dict(numcoordinates=None, xcoordinates=None),
                DambreakTestCases.check_location_err,
                id="Missing ycoordinates",
            ),
            pytest.param(
                dict(numcoordinates=0, xcoordinates=None, ycoordinates=None),
                DambreakTestCases.check_location_err,
                id="None coordinates.",
            ),
            pytest.param(
                dict(numcoordinates=0, xcoordinates=[], ycoordinates=[]),
                DambreakTestCases.too_few_coords.format(0),
                id="Empty list coordinates.",
            ),
            pytest.param(
                dict(numcoordinates=1, xcoordinates=[], ycoordinates=[]),
                DambreakTestCases.too_few_coords.format(1),
                id="One coordinate.",
            ),
            pytest.param(
                dict(numcoordinates=2, xcoordinates=[4.2], ycoordinates=[]),
                DambreakTestCases.mismatch_coords.format(2, 1, 0),
                id="Mismatch coordinates.",
            ),
        ],
    )
    def test_given_invalid_location_raises_validation_error(
        self,
        location_dict: dict,
        err_mssg: str,
        default_dambreak_values: dict,
    ):
        # 1. Define test data
        test_values = {**default_dambreak_values, **location_dict}

        # 2. Run test
        with pytest.raises(ValidationError) as exc_err:
            Dambreak(**test_values)

        # 3. Verify final expectations.
        assert err_mssg in str(exc_err.value)

    def test_given_valid_values_creates_dambreak(self, valid_dambreak_values: dict):
        dambreak = Dambreak(**valid_dambreak_values)
        self.validate_valid_default_dambreak(dambreak)

    def test_given_structure_text_with_num_x_y_coordinates_parses_structure(self):
        # 1. Define structure text.
        structure_text = inspect.cleandoc(
            """
            [Structure]
            type = dambreak                 # Structure type; must read dambreak
            id = NLNJ-2021                  # Unique structure id (max. 256 characters).
            name = NederlandNaranjito2021   # Given name in the user interface.
            numCoordinates = 2              # Number of values in xCoordinates and yCoordinates. This value should be greater or equal 2.
            xCoordinates = 4.2 2.4       # x-coordinates of the link selection polygon.
            yCoordinates = 2.4 4.2       # y-coordinates of the link selection polygon.
            startLocationX = 4.2            # x-coordinate of breach starting point.
            startLocationY = 2.4            # y-coordinate of breach starting point.
            algorithm = 1                   # Breach growth algorithm.

            crestLevelIni = 1               # Initial breach level.
            breachWidthIni = 24             # Initial breach width.
            crestLevelMin = 42              # Minimal breach level.
            t0 = 2.2                        # Breach start time.
            timeToBreachToMaximumDepth = 4.4    # tphase 1.
            f1 = 22.4                       # Factor f1.
            f2 = 44.2                       # Factor f2.
            uCrit = 44.22                   # Critical flow velocity uc for erosion [m/s].
            waterLevelUpstreamLocationX = 1.2 # x-coordinate of custom upstream water level point.
            waterLevelUpstreamLocationY = 2.3 # y-coordinate of custom upstream water level point.
            waterLevelDownstreamLocationX = 3.4 # x-coordinate of custom downstream water level point.
            waterLevelDownstreamLocationY = 4.5 # y-coordinate of custom downstream water level point.
            waterLevelUpstreamNodeId = anUpstreamNodeId # Node Id of custom upstream water level point.
            waterLevelDownstreamNodeId = aDownstreamNodeId # Node Id of custom downstream water level point.
            """
        )
        # 2. Parse data.
        dambreak_obj = self.parse_dambreak_from_text(structure_text)
        self.validate_valid_default_dambreak(dambreak_obj)

    def test_given_structure_text_with_polylinefile_parses_structure(self):
        structure_text = inspect.cleandoc(
            """
            [structure]
            type                       = dambreak  
            id                         = dambreak  
            polylinefile               = dambreak2ddrybreach.pli
            startLocationX             = 1.2 
            startLocationY             = 4.0
            algorithm                  = 3             # 1 VdKnaap ,2 Verheij-vdKnaap
            crestLevelIni              = 0.4
            breachWidthIni             = 1
            crestLevelMin              = 0.2
            timeToBreachToMaximumDepth = 0.1           #in seconds 
            f1                         = 1
            f2                         = 1
            ucrit                      = 0.001
            t0                         = 0.0001        # make it a boolean
            dambreakLevelsAndWidths    = dambreak.tim  #used only in algorithm 3            
            materialtype               = 1             #1 clay 2 sand, used only in algorithm 1 
            """
        )

        # 2. Parse data.
        dambreak_obj = self.parse_dambreak_from_text(structure_text)
        assert dambreak_obj
        assert isinstance(dambreak_obj, Structure)
        assert dambreak_obj.type == "dambreak"
        assert dambreak_obj.id == "dambreak"
        assert dambreak_obj.startlocationx == 1.2
        assert dambreak_obj.startlocationy == 4.0
        assert dambreak_obj.algorithm == 3
        assert dambreak_obj.crestlevelini == 0.4
        assert dambreak_obj.breachwidthini == 1
        assert dambreak_obj.crestlevelmin == 0.2
        assert dambreak_obj.timetobreachtomaximumdepth == 0.1
        assert dambreak_obj.f1 == 1
        assert dambreak_obj.f2 == 1
        assert dambreak_obj.ucrit == 0.001
        assert dambreak_obj.t0 == 0.0001
        assert dambreak_obj.dambreaklevelsandwidths == Path("dambreak.tim")
        assert dambreak_obj.dict()["materialtype"] == "1"

    def parse_dambreak_from_text(self, structure_text: str) -> Dambreak:
        """
        Method just to simplify how the tests can parse a dambreak without having to
        repeat the same code for each test.

        Args:
            structure_text (str): Text containing Dambreak structure.

        Returns:
            Dambreak: Parsed object.
        """
        # 1. Parse data.
        parser = Parser(ParserConfig())
        for line in structure_text.splitlines():
            parser.feed_line(line)
        document = parser.finalize()

        # 2. Parse object
        return WrapperTest[Dambreak].parse_obj({"val": document.sections[0]}).val

    def validate_valid_default_dambreak(self, dambreak: Dambreak):
        """
        Method to validate the default (valid) test case for a Dambreak.

        Args:
            dambreak (Dambreak): Instance that needs to be verified for its expected values.
        """

        assert isinstance(dambreak, Structure), "A dambreak should be a structure."
        assert dambreak.id == "NLNJ-2021"
        assert dambreak.name == "NederlandNaranjito2021"
        assert dambreak.type == "dambreak"
        assert dambreak.startlocationx == 4.2
        assert dambreak.startlocationy == 2.4
        assert dambreak.algorithm == 1
        assert dambreak.crestlevelini == 1
        assert dambreak.breachwidthini == 24
        assert dambreak.crestlevelmin == 42
        assert dambreak.t0 == 2.2
        assert dambreak.timetobreachtomaximumdepth == 4.4
        assert dambreak.f1 == 22.4
        assert dambreak.f2 == 44.2
        assert dambreak.ucrit == 44.22
        assert dambreak.numcoordinates == 2
        assert dambreak.xcoordinates == [4.2, 2.4]
        assert dambreak.ycoordinates == [2.4, 4.2]
        assert dambreak.waterlevelupstreamlocationx == 1.2
        assert dambreak.waterlevelupstreamlocationy == 2.3
        assert dambreak.waterleveldownstreamlocationx == 3.4
        assert dambreak.waterleveldownstreamlocationy == 4.5
        assert dambreak.waterlevelupstreamnodeid == "anUpstreamNodeId"
        assert dambreak.waterleveldownstreamnodeid == "aDownstreamNodeId"

    class TestValidateAlgorithm:
        """
        Wrapper to validate all paradigms of validate_algorithm
        """

        @pytest.mark.parametrize(
            "value",
            [pytest.param("", id="Empty string."), pytest.param(None, id="None")],
        )
        def test_given_not_int_raises_value_error(self, value: Any):
            with pytest.raises(ValueError) as exc_err:
                Dambreak.validate_algorithm(value)
            assert (
                str(exc_err.value) == "Dambreak algorithm value should be of type int."
            )

        @pytest.mark.parametrize(
            "value",
            [pytest.param(0), pytest.param(4), pytest.param(-1)],
        )
        def test_given_value_out_of_range_raises_value_error(self, value: int):
            with pytest.raises(ValueError) as exc_err:
                Dambreak.validate_algorithm(value)
            assert str(exc_err.value) == "Dambreak algorithm value should be 1, 2 or 3."

        @pytest.mark.parametrize(
            "value",
            [pytest.param(1), pytest.param(2), pytest.param(3)],
        )
        def test_given_valid_value_returns_value(self, value: int):
            assert Dambreak.validate_algorithm(value) == value

    class TestValidateDambreakLevelsAndWidths:
        """
        Wrapper to validate all paradigms of
        validate_dambreak_leels_and_widths
        """

        algorithm_values = [(-1), (0), (1), (2), (4)]

        @pytest.mark.parametrize(
            "algorithm_value",
            algorithm_values,
        )
        @pytest.mark.parametrize(
            "field_value",
            [
                pytest.param("", id="Empty string"),
                pytest.param(Path(""), id="Empty Path"),
                pytest.param("JustAValue", id="String value"),
                pytest.param(Path("JustAValue"), id="Path value"),
            ],
        )
        def test_given_field_value_but_no_algorithm_3_raises_value_error(
            self, field_value: str, algorithm_value: int
        ):
            with pytest.raises(ValueError) as exc_err:
                Dambreak.validate_dambreak_levels_and_widths(
                    field_value,
                    dict(
                        algorithm=algorithm_value,
                    ),
                )
            assert (
                str(exc_err.value)
                == f"Dambreak field dambreakLevelsAndWidths can only be set when algorithm = 3, current value: {algorithm_value}."
            )

        def test_given_algorithm_value_3_returns_field_value(self):
            field_value = "justAValue"
            return_value = Dambreak.validate_dambreak_levels_and_widths(
                field_value, dict(algorithm=3)
            )
            assert return_value == field_value

        @pytest.mark.parametrize("algorithm_value", algorithm_values)
        def test_given_none_field_value_and_algorithm_value_not_3_returns_field_value(
            self, algorithm_value: int
        ):
            return_value = Dambreak.validate_dambreak_levels_and_widths(
                None, dict(algorithm=algorithm_value)
            )
            assert return_value is None

    class TestCheckLocation:
        """
        Wrapper to validate all paradigms of check_location
        """

        @pytest.mark.parametrize(
            "dict_values",
            [
                pytest.param(
                    dict(numcoordinates=2, xcoordinates=[0, 1], ycoordinates=[2, 3]),
                    id="With 2 coordinates",
                ),
                pytest.param(
                    dict(
                        numcoordinates=3, xcoordinates=[0, 1, 2], ycoordinates=[2, 3, 4]
                    ),
                    id="With 3 coordinates",
                ),
                pytest.param(dict(polylinefile=Path()), id="Empty path"),
                pytest.param(
                    dict(polylinefile=Path("aFilePath")), id="Path with file name"
                ),
            ],
        )
        def test_given_valid_values_returns_values(self, dict_values: dict):
            return_value = Dambreak.check_location(dict_values)
            assert return_value == dict_values

        @pytest.mark.parametrize(
            "invalid_values, expected_err",
            [
                pytest.param(
                    dict(), DambreakTestCases.check_location_err, id="Empty dict."
                ),
                pytest.param(
                    dict(
                        numcoordinates=None,
                        xcoordinates=None,
                        ycoordinates=None,
                        polylinefile=None,
                    ),
                    DambreakTestCases.check_location_err,
                    id="Dict with Nones.",
                ),
            ],
        )
        def test_given_invalid_values_raises_expectation(
            self, invalid_values: dict, expected_err: str
        ):
            with pytest.raises(ValueError) as exc_err:
                Dambreak.check_location(invalid_values)
            assert str(exc_err.value) == expected_err


class TestOrifice:
    """
    Wrapper class to test all the methods and sublcasses in:
    hydrolib.core.io.structure.models.py Orifice class.
    """

    def test_create_orifice(self):
        structure = Orifice(**self._create_orifice_values())

        assert structure.id == "structure_id"
        assert structure.name == "structure_name"
        assert structure.type == "orifice"
        assert structure.branchid == "branch_id"
        assert structure.chainage == 1.23
        assert structure.allowedflowdir == FlowDirection.positive
        assert structure.crestlevel == 2.34
        assert structure.crestwidth == 3.45
        assert structure.gateloweredgelevel == 4.56
        assert structure.corrcoeff == 5.67
        assert structure.usevelocityheight == True
        assert structure.uselimitflowpos == True
        assert structure.limitflowpos == 6.78
        assert structure.uselimitflowneg == True
        assert structure.limitflowneg == 7.89

    @pytest.mark.parametrize(
        "limitflow, uselimitflow",
        [
            pytest.param("limitFlowPos", "useLimitFlowPos"),
            pytest.param("limitFlowNeg", "useLimitFlowNeg"),
        ],
    )
    def test_validate_limitflow(self, limitflow: str, uselimitflow: str):
        values = self._create_orifice_values()
        del values[limitflow.lower()]

        with pytest.raises(ValidationError) as error:
            Orifice(**values)

        expected_message = f"1 validation error for Orifice\n\
structure_id -> {limitflow}\n  \
{limitflow} should be defined when {uselimitflow} is true"

        assert expected_message in str(error.value)

    @pytest.mark.parametrize(
        "input,expected",
        _get_allowedflowdir_cases(),
    )
    def test_orifice_parses_flowdirection_case_insensitive(self, input, expected):
        structure = Orifice(
            allowedflowdir=input,
            id="strucid",
            branchid="branchid",
            chainage="1",
            crestlevel="1",
            corrcoeff="1",
            gateloweredgelevel="1",
            usevelocityheight="0",
            uselimitflowpos="0",
            uselimitflowneg="0",
        )

        assert structure.allowedflowdir == expected

    def test_optional_fields_have_correct_defaults(self):
        structure = Orifice(**self._create_required_orifice_values())

        assert structure.allowedflowdir == FlowDirection.both
        assert structure.crestwidth == None
        assert structure.uselimitflowpos == False
        assert structure.limitflowpos == None
        assert structure.uselimitflowneg == False
        assert structure.limitflowneg == None

    def _create_required_orifice_values(self) -> dict:
        return dict(
            id="structure_id",
            name="structure_name",
            type="orifice",
            branchid="branch_id",
            chainage="1.23",
            crestlevel="2.34",
            gateloweredgelevel="4.56",
            corrcoeff="5.67",
            usevelocityheight="true",
        )

    def _create_orifice_values(self) -> dict:
        orifice_values = dict(
            allowedflowdir="positive",
            crestwidth="3.45",
            uselimitflowpos="true",
            limitflowpos="6.78",
            uselimitflowneg="true",
            limitflowneg="7.89",
        )

        orifice_values.update(self._create_required_orifice_values())

        return orifice_values


class TestWeir:
    def test_create_a_weir_from_scratch(self):
        weir = Weir(
            id="w003",
            name="W003",
            branchid="B1",
            chainage=5.0,
            allowedflowdir=FlowDirection.none,
            crestlevel=0.5,
            usevelocityheight=False,
            comments=Weir.Comments(
                name="W stands for weir, 003 because we expect to have at most 999 weirs"
            ),
        )

        assert weir.id == "w003"
        assert weir.name == "W003"
        assert weir.branchid == "B1"
        assert weir.chainage == 5.0
        assert weir.allowedflowdir == FlowDirection.none
        assert weir.crestlevel == 0.5
        assert weir.crestwidth == None
        assert weir.usevelocityheight == False
        assert (
            weir.comments.name
            == "W stands for weir, 003 because we expect to have at most 999 weirs"
        )

        assert weir.comments.id == uniqueid_str

    def test_id_comment_has_correct_default(self):
        weir = Weir(
            id="weir_id",
            name="W001",
            branchid="branch",
            chainage=3.0,
            allowedflowdir=FlowDirection.positive,
            crestlevel=10.5,
            crestwidth=None,
            usevelocityheight=False,
        )

        assert weir.comments.id == uniqueid_str

    def test_add_comment_to_weir(self):
        weir = Weir(
            id="weir_id",
            name="W001",
            branchid="branch",
            chainage=3.0,
            allowedflowdir=FlowDirection.positive,
            crestlevel=10.5,
            crestwidth=None,
            usevelocityheight=False,
        )

        weir.comments.usevelocityheight = "a different value"
        assert weir.comments.usevelocityheight == "a different value"

    def test_weir_construction_with_parser(self):
        parser = Parser(ParserConfig())

        input_str = inspect.cleandoc(
            """
            [Structure]
            id                = weir_id     # Unique structure id (max. 256 characters).
            name              = weir        # Given name in the user interface.
            branchId          = branch      # (optional) Branch on which the structure is located.
            chainage          = 3.0         # (optional) Chainage on the branch (m)
            type              = weir        # Structure type
            allowedFlowDir    = positive    # Possible values: both, positive, negative, none.
            crestLevel        = 10.5        # Crest level of weir (m AD)
            crestWidth        =             # Width of weir (m)
            useVelocityHeight = false       # Flag indicates whether the velocity height is to be calculated or not.
            """
        )

        for line in input_str.splitlines():
            parser.feed_line(line)

        document = parser.finalize()

        wrapper = WrapperTest[Weir].parse_obj({"val": document.sections[0]})
        weir = wrapper.val

        assert weir.id == "weir_id"
        assert weir.name == "weir"
        assert weir.branchid == "branch"
        assert weir.chainage == 3.0
        assert weir.type == "weir"
        assert weir.allowedflowdir == FlowDirection.positive
        assert weir.crestlevel == 10.5
        assert weir.crestwidth is None
        assert weir.usevelocityheight == False

    def test_weir_comments_construction_with_parser(self):
        parser = Parser(ParserConfig())

        input_str = inspect.cleandoc(
            """
            [Structure]
            id                = weir_id     
            name              = weir        
            branchId          = branch      
            chainage          = 3.0         # My own special comment 1
            type              = weir        
            allowedFlowDir    = positive    
            crestLevel        = 10.5        
            crestWidth        =             
            useVelocityHeight = false       # My own special comment 2
            """
        )

        for line in input_str.splitlines():
            parser.feed_line(line)

        document = parser.finalize()

        wrapper = WrapperTest[Weir].parse_obj({"val": document.sections[0]})
        weir = wrapper.val

        assert weir.comments.id is None
        assert weir.comments.name is None
        assert weir.comments.branchid is None
        assert weir.comments.chainage == "My own special comment 1"
        assert weir.comments.type is None
        assert weir.comments.allowedflowdir is None
        assert weir.comments.crestlevel is None
        assert weir.comments.crestwidth is None
        assert weir.comments.usevelocityheight == "My own special comment 2"

    def test_weir_with_unknown_parameters(self):
        parser = Parser(ParserConfig())

        input_str = inspect.cleandoc(
            """
            [Structure]
            id                = weir_id     # Unique structure id (max. 256 characters).
            name              = weir        # Given name in the user interface.
            branchId          = branch      # (optional) Branch on which the structure is located.
            chainage          = 3.0         # (optional) Chainage on the branch (m)

            # ----------------------------------------------------------------------
            unknown           = 10.0        # A deliberately added unknown property
            # ----------------------------------------------------------------------

            type              = weir        # Structure type
            allowedFlowDir    = positive    # Possible values: both, positive, negative, none.
            crestLevel        = 10.5        # Crest level of weir (m AD)
            crestWidth        =             # Width of weir (m)
            useVelocityHeight = false       # Flag indicates whether the velocity height is to be calculated or not.
            """
        )

        for line in input_str.splitlines():
            parser.feed_line(line)

        document = parser.finalize()

        wrapper = WrapperTest[Weir].parse_obj({"val": document.sections[0]})
        weir = wrapper.val

        assert weir.unknown == "10.0"  # type: ignore

        assert weir.id == "weir_id"
        assert weir.name == "weir"
        assert weir.branchid == "branch"
        assert weir.chainage == 3.0
        assert weir.type == "weir"
        assert weir.allowedflowdir == FlowDirection.positive
        assert weir.crestlevel == 10.5
        assert weir.crestwidth is None
        assert weir.usevelocityheight == False

    @pytest.mark.parametrize(
        "input,expected",
        _get_allowedflowdir_cases(),
    )
    def test_weir_parses_flowdirection_case_insensitive(self, input, expected):
        structure = Weir(
            allowedflowdir=input,
            id="strucid",
            branchid="branchid",
            chainage="1",
            crestlevel="1",
        )

        assert structure.allowedflowdir == expected
