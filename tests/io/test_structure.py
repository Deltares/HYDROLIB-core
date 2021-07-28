from hydrolib.core.io.structure.models import FlowDirection, UniversalWeir, Weir
from hydrolib.core.io.ini.parser import Parser, ParserConfig
from pydantic.generics import GenericModel
from typing import Generic, List, TypeVar, Union

import inspect


TWrapper = TypeVar("TWrapper")


class TestWrapper(GenericModel, Generic[TWrapper]):
    val: TWrapper


def test_create_a_weir_from_scratch():
    weir = Weir(
        id="w003",
        name="W003",
        branch_id="B1",
        chainage=5.0,
        allowed_flow_direction=FlowDirection.none,
        crest_level=0.5,
        use_velocity_height=False,
        comments=Weir.Comments(
            name="W stands for weir, 003 because we expect to have at most 999 weirs"
        ),
    )

    assert weir.id == "w003"
    assert weir.name == "W003"
    assert weir.branch_id == "B1"
    assert weir.chainage == 5.0
    assert weir.allowed_flow_direction == FlowDirection.none
    assert weir.crest_level == 0.5
    assert weir.crest_width == None
    assert weir.use_velocity_height == False
    assert (
        weir.comments.name
        == "W stands for weir, 003 because we expect to have at most 999 weirs"
    )

    assert weir.comments.id == "Unique structure id (max. 256 characters)."


def test_id_comment_has_correct_default():
    weir = Weir(
        id="weir_id",
        name="W001",
        branch_id="branch",
        chainage=3.0,
        allowed_flow_direction=FlowDirection.positive,
        crest_level=10.5,
        crest_width=None,
        use_velocity_height=False,
    )

    assert weir.comments.id == "Unique structure id (max. 256 characters)."


def test_add_comment_to_weir():
    weir = Weir(
        id="weir_id",
        name="W001",
        branch_id="branch",
        chainage=3.0,
        allowed_flow_direction=FlowDirection.positive,
        crest_level=10.5,
        crest_width=None,
        use_velocity_height=False,
    )

    weir.comments.use_velocity_height = "a different value"
    assert weir.comments.use_velocity_height == "a different value"


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

    wrapper = TestWrapper[Weir].parse_obj({"val": document.sections[0]})
    weir = wrapper.val

    assert weir.id == "weir_id"
    assert weir.name == "weir"
    assert weir.branch_id == "branch"
    assert weir.chainage == 3.0
    assert weir.structure_type == "weir"
    assert weir.allowed_flow_direction == FlowDirection.positive
    assert weir.crest_level == 10.5
    assert weir.crest_width is None
    assert weir.use_velocity_height == False


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

    wrapper = TestWrapper[Weir].parse_obj({"val": document.sections[0]})
    weir = wrapper.val

    assert weir.comments.id is None
    assert weir.comments.name is None
    assert weir.comments.branch_id is None
    assert weir.comments.chainage == "My own special comment 1"
    assert weir.comments.structure_type is None
    assert weir.comments.allowed_flow_direction is None
    assert weir.comments.crest_level is None
    assert weir.comments.crest_width is None
    assert weir.comments.use_velocity_height == "My own special comment 2"


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

    wrapper = TestWrapper[Weir].parse_obj({"val": document.sections[0]})
    weir = wrapper.val

    assert weir.unknown == "10.0"  # type: ignore

    assert weir.id == "weir_id"
    assert weir.name == "weir"
    assert weir.branch_id == "branch"
    assert weir.chainage == 3.0
    assert weir.structure_type == "weir"
    assert weir.allowed_flow_direction == FlowDirection.positive
    assert weir.crest_level == 10.5
    assert weir.crest_width is None
    assert weir.use_velocity_height == False


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

    wrapper = TestWrapper[UniversalWeir].parse_obj({"val": document.sections[0]})
    universal_weir = wrapper.val

    assert universal_weir.id == "uweir_id"
    assert universal_weir.name == "W002"
    assert universal_weir.branch_id == "branch"
    assert universal_weir.chainage == 6.0
    assert universal_weir.allowed_flow_direction == FlowDirection.positive
    assert universal_weir.number_of_levels == 2
    assert universal_weir.y_values == [1.0, 2.0]
    assert universal_weir.z_values == [3.0, 4.0]
    assert universal_weir.crest_level == 10.5
    assert universal_weir.discharge_coefficient == 0.5


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

    wrapper = TestWrapper[List[Union[Weir, UniversalWeir]]].parse_obj(
        {"val": document.sections}
    )
    expected_structures = [
        Weir(
            id="weir_id",
            name="W001",
            branch_id="branch",
            chainage=3.0,
            allowed_flow_direction=FlowDirection.positive,
            crest_level=10.5,
            crest_width=None,
            use_velocity_height=False,
        ),
        UniversalWeir(
            id="uweir_id",
            name="W002",
            branch_id="branch",
            chainage=6.0,
            allowed_flow_direction=FlowDirection.positive,
            number_of_levels=2,
            y_values=[1.0, 2.0],
            z_values=[3.0, 4.0],
            crest_level=10.5,
            discharge_coefficient=0.5,
        ),
    ]

    assert wrapper.val == expected_structures
