import inspect
from typing import List, Union

import pytest
from pydantic.error_wrappers import ValidationError

from hydrolib.core.io.ini.parser import Parser, ParserConfig
from hydrolib.core.io.structure.models import (
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

    filepath = test_data_dir / "input/invalid_files" / file

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
        ("DOESNOTEXIST", "DOESNOTEXIST"),
        ("doesnotexist", "doesnotexist"),
    ],
)
def test_parses_type_case_insensitive(input, expected):
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
def test_weir_parses_flowdirection_case_insensitive(input, expected):
    structure = Weir(allowedflowdir=input, id="strucid", crestlevel="1")

    assert structure.allowedflowdir == expected


@pytest.mark.parametrize(
    "input,expected",
    _get_allowedflowdir_cases(),
)
def test_universalweir_parses_flowdirection_case_insensitive(input, expected):
    structure = UniversalWeir(
        allowedflowdir=input,
        id="strucid",
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
    _get_allowedflowdir_cases(),
)
def test_orifice_parses_flowdirection_case_insensitive(input, expected):
    structure = Orifice(
        allowedflowdir=input,
        id="strucid",
        crestlevel="1",
        corrcoeff="1",
        usevelocityheight="0",
        uselimitflowpos="0",
        uselimitflowneg="0",
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
