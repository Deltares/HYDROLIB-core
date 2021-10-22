import inspect
from contextlib import nullcontext as does_not_raise
from typing import List, Union

import pytest
from pydantic.error_wrappers import ValidationError

from hydrolib.core.io.ini.parser import Parser, ParserConfig
from hydrolib.core.io.structure.models import (
    Bridge,
    Compound,
    FlowDirection,
    Orifice,
    Pump,
    Structure,
    StructureModel,
    UniversalWeir,
    Weir,
)

from ..utils import WrapperTest, test_data_dir


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


def test_create_a_weir_from_scratch():
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

    assert weir.comments.id == "Unique structure id (max. 256 characters)."


def test_id_comment_has_correct_default():
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

    assert weir.comments.id == "Unique structure id (max. 256 characters)."


def test_add_comment_to_weir():
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


def test_weir_construction_with_parser():
    parser = Parser(ParserConfig())

    input_str = inspect.cleandoc(
        """
        [Structure]
        id                = weir_id     # Unique structure id (max. 256 characters).
        name              = weir        # Given name in the user interface.
        branchId          = branch      # (optional) Branch on which the structure is located.
        chainage          = 3.0         # (optional) Chainage on the branch (m)
        type              = weir        # Structure type
        allowedFlowdir    = positive    # Possible values: both, positive, negative, none.
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
    assert weir.structure_type == "weir"
    assert weir.allowedflowdir == FlowDirection.positive
    assert weir.crestlevel == 10.5
    assert weir.crestwidth is None
    assert weir.usevelocityheight == False


def test_weir_comments_construction_with_parser():
    parser = Parser(ParserConfig())

    input_str = inspect.cleandoc(
        """
        [Structure]
        id                = weir_id     
        name              = weir        
        branchId          = branch      
        chainage          = 3.0         # My own special comment 1
        type              = weir        
        allowedFlowdir    = positive    
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
    assert weir.comments.structure_type is None
    assert weir.comments.allowedflowdir is None
    assert weir.comments.crestlevel is None
    assert weir.comments.crestwidth is None
    assert weir.comments.usevelocityheight == "My own special comment 2"


def test_weir_with_unknown_parameters():
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
        allowedFlowdir    = positive    # Possible values: both, positive, negative, none.
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
    assert weir.structure_type == "weir"
    assert weir.allowedflowdir == FlowDirection.positive
    assert weir.crestlevel == 10.5
    assert weir.crestwidth is None
    assert weir.usevelocityheight == False


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
        allowedFlowdir    = positive         # Possible values: both, positive, negative, none.
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
        allowedFlowdir    = positive    # Possible values: both, positive, negative, none.
        crestLevel        = 10.5        # Crest level of weir (m AD).
        crestWidth        =             # Width of the weir (m).
        useVelocityHeight = false       # Flag indicating whether the velocity height is to be calculated or not.

        [Structure]
        id                = uweir_id         # Unique structure id (max. 256 characters).
        name              = W002             # Given name in the user interface.
        branchId          = branch           # Branch on which the structure is located.
        chainage          = 6.0              # Chainage on the branch (m).
        type              = universalWeir    # Structure type; must read universalWeir
        allowedFlowdir    = positive         # Possible values: both, positive, negative, none.
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

    filepath = test_data_dir / "input/invalid_files" / file

    with pytest.raises(ValidationError) as error:
        StructureModel(filepath)

    expected_message = f"{file} -> structure -> 1 -> {identifier} -> {field}"
    assert expected_message in str(error.value)


def test_create_a_bridge_from_scratch():
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

    assert isinstance(bridge, Structure), "Bridge should also be an instance of a Structure"

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

    assert bridge.comments.id == "Unique structure id (max. 256 characters)."


def test_bridge_construction_with_parser():
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

    assert bridge.id == "RS1-KBR31"
    assert bridge.name == "RS1-KBR31name"
    assert bridge.branchid == "riv_RS1_264"
    assert bridge.chainage == 104.184
    assert bridge.structure_type == "bridge"
    assert bridge.allowedflowdir == FlowDirection.both
    assert bridge.csdefid == "W_980.1S_0"
    assert bridge.shift == 0.0
    assert bridge.inletlosscoeff == 1
    assert bridge.outletlosscoeff == 1
    assert bridge.frictiontype == "Strickler"
    assert bridge.friction == 70
    assert bridge.length == 9.75


def test_bridge_with_unknown_parameters():
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
    assert bridge.structure_type == "bridge"
    assert bridge.allowedflowdir == FlowDirection.both
    assert bridge.csdefid == "W_980.1S_0"
    assert bridge.shift == 0.0
    assert bridge.inletlosscoeff == 1
    assert bridge.outletlosscoeff == 1
    assert bridge.frictiontype == "Strickler"
    assert bridge.friction == 70
    assert bridge.length == 9.75


def test_bridge_with_missing_required_parameters():
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
    hydrolib.core.io.structure.models.py Structure class
    """

    class TestRootValidator:
        """
        Wrapper class to validate the paradigms that point to root_validators
        in the Structure class
        """

        long_culvert_err = (
            "`num/x/yCoordinates` are mandatory for a LongCulvert structure."
        )
        structure_err = "Specify location either by setting `branchId` and `chainage` or `num/x/yCoordinates` fields."

        @pytest.mark.parametrize(
            "structure_type, expectation, error_mssg",
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
                    structure_err,
                    id="Dambreak raises.",
                ),
                pytest.param(
                    "compound", does_not_raise(), None, id="Compound DOES NOT raise."
                ),
            ],
        )
        def test_check_location_given_no_values_raises_expectation(
            self, structure_type: str, expectation, error_mssg: str
        ):
            with expectation as exc_err:
                input_dict = dict(
                    notAValue="Not a relevant value",
                    structure_type=structure_type,
                    n_coordinates=None,
                    x_coordinates=None,
                    y_coordinates=None,
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
                n_coordinates=None,
                x_coordinates=None,
                y_coordinates=None,
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
                == "A valid value for branchId and chainage is required when branchid key is specified."
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
                        n_coordinates=n_coords,
                        x_coordinates=x_coords,
                        y_coordinates=y_coords,
                    )
                )
            assert (
                str(exc_err.value)
                == f"Expected {n_coords} coordinates, given {len(x_coords)} for x and {len(y_coords)} for y coordinates."
            )

        @pytest.mark.parametrize(
            "dict_values",
            [
                pytest.param(
                    dict(
                        n_coordinates=0,
                        x_coordinates=[],
                        y_coordinates=[],
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
                == "A valid value for branchId and chainage is required when branchid key is specified."
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
                    dict(n_coordinates=None), False, id="Missing x_y_coordinates"
                ),
                pytest.param(
                    dict(n_coordinates=None, y_coordinates=None),
                    False,
                    id="Missing x_coordinates",
                ),
                pytest.param(
                    dict(n_coordinates=None, x_coordinates=None),
                    False,
                    id="Missing y_coordinates",
                ),
                pytest.param(
                    dict(n_coordinates=0, x_coordinates=None, y_coordinates=None),
                    True,
                    id="None coordinates.",
                ),
                pytest.param(
                    dict(n_coordinates=0, x_coordinates=[], y_coordinates=[]),
                    True,
                    id="Empty list coordinates.",
                ),
                pytest.param(
                    dict(
                        n_coordinates=2, x_coordinates=[42, 24], y_coordinates=[24, 42]
                    ),
                    True,
                    id="With coordinates.",
                ),
            ],
        )
        def test_given_valid_values_returns_expectation(
            self, dict_values: dict, expectation: bool
        ):
            validation = Structure.validate_coordinates_in_model(dict_values)
            assert validation == expectation

        def test_given_invalid_values_raises_value_error(self):
            with pytest.raises(ValueError) as exc_err:
                Structure.validate_coordinates_in_model(
                    dict(
                        n_coordinates=1,
                        x_coordinates=[42, 24],
                        y_coordinates=[24, 42, 66],
                    )
                )
            assert (
                str(exc_err.value)
                == "Expected 1 coordinates, given 2 for x and 3 for y coordinates."
            )
