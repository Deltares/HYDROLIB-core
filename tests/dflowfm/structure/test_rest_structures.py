import inspect
from typing import Any, Dict

import pytest

from hydrolib.core.dflowfm.ini.parser import Parser, ParserConfig
from hydrolib.core.dflowfm.structure.models import (
    Bridge,
    Culvert,
    CulvertSubType,
    DambreakAlgorithm,
    FlowDirection,
    FrictionType,
    LongCulvert,
    Orifice,
    Structure,
    Weir,
)
from tests.dflowfm.structure.test_structure import (
    _get_allowedflowdir_cases,
    create_structure_values,
    uniqueid_str,
)
from tests.utils import WrapperTest


class TestBridge:
    """
    Wrapper class to test all the methods and subclasses in:
    hydrolib.core.dflowfm.structure.models.py Bridge class
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
            frictiontype=FrictionType.strickler,
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
        assert bridge.chainage == pytest.approx(5.0)
        assert bridge.allowedflowdir == FlowDirection.both
        assert bridge.csdefid == "W_980.1S_0"
        assert bridge.shift == -1.23
        assert bridge.inletlosscoeff == 1
        assert bridge.outletlosscoeff == 1
        assert bridge.frictiontype == FrictionType.strickler
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

        wrapper = WrapperTest[Bridge].model_validate({"val": document.sections[0]})
        bridge = wrapper.val

        assert isinstance(
            bridge, Structure
        ), "Bridge should also be an instance of a Structure"

        assert bridge.id == "RS1-KBR31"
        assert bridge.name == "RS1-KBR31name"
        assert bridge.branchid == "riv_RS1_264"
        assert bridge.chainage == pytest.approx(104.184)
        assert bridge.type == "bridge"
        assert bridge.allowedflowdir == FlowDirection.both
        assert bridge.csdefid == "W_980.1S_0"
        assert bridge.shift == pytest.approx(0.0)
        assert bridge.inletlosscoeff == 1
        assert bridge.outletlosscoeff == 1
        assert bridge.frictiontype == FrictionType.strickler
        assert bridge.friction == 70
        assert bridge.length == pytest.approx(9.75)

    def test_bridge_with_unknown_parameter_is_ignored(self):
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
            unknown           = 10.0        # A deliberately added unknown property
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

        wrapper = WrapperTest[Bridge].model_validate({"val": document.sections[0]})
        bridge = wrapper.val

        assert bridge.model_dump().get("unknown") is None  # type: ignore

        assert bridge.id == "RS1-KBR31"
        assert bridge.name == "RS1-KBR31name"
        assert bridge.branchid == "riv_RS1_264"
        assert bridge.chainage == pytest.approx(104.184)
        assert bridge.type == "bridge"
        assert bridge.allowedflowdir == FlowDirection.both
        assert bridge.csdefid == "W_980.1S_0"
        assert bridge.shift == pytest.approx(0.0)
        assert bridge.inletlosscoeff == 1
        assert bridge.outletlosscoeff == 1
        assert bridge.frictiontype == FrictionType.strickler
        assert bridge.friction == 70
        assert bridge.length == pytest.approx(9.75)

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
            wrapper = WrapperTest[Bridge].model_validate({"val": document.sections[0]})
            bridge = wrapper.val
        assert expected_message in str(exc_err.value)

        assert "bridge" not in locals()  # Bridge structure should not have been created


class TestDambreakAlgorithm:
    """
    Wrapper class to test all the methods in:
    hydrolib.core.dflowfm.structure.models.py DambreakAlgorithm enum class.
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


class TestOrifice:
    """
    Wrapper class to test all the methods and sublcasses in:
    hydrolib.core.dflowfm.structure.models.py Orifice class.
    """

    def test_create_orifice(self):
        structure = Orifice(**self._create_orifice_values())

        assert structure.id == "structure_id"
        assert structure.name == "structure_name"
        assert structure.type == "orifice"
        assert structure.branchid == "branch_id"
        assert structure.chainage == pytest.approx(1.23)
        assert structure.allowedflowdir == FlowDirection.positive
        assert structure.crestlevel == pytest.approx(2.34)
        assert structure.crestwidth == pytest.approx(3.45)
        assert structure.gateloweredgelevel == pytest.approx(4.56)
        assert structure.corrcoeff == pytest.approx(5.67)
        assert structure.usevelocityheight == True
        assert structure.uselimitflowpos == True
        assert structure.limitflowpos == pytest.approx(6.78)
        assert structure.uselimitflowneg == True
        assert structure.limitflowneg == pytest.approx(7.89)

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

        with pytest.raises(ValueError):
            Orifice(**values)

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
        orifice_values = dict(
            crestlevel="2.34",
            gateloweredgelevel="4.56",
            corrcoeff="5.67",
            usevelocityheight="true",
        )

        orifice_values.update(create_structure_values("orifice"))

        return orifice_values

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
            **self._create_weir_values(),
            comments=Weir.Comments(
                name="W stands for weir, 003 because we expect to have at most 999 weirs"
            ),
        )

        assert weir.id == "structure_id"
        assert weir.name == "structure_name"
        assert weir.branchid == "branch_id"
        assert weir.chainage == pytest.approx(1.23)
        assert weir.allowedflowdir == FlowDirection.positive
        assert weir.crestlevel == pytest.approx(2.34)
        assert weir.crestwidth == pytest.approx(3.45)
        assert weir.usevelocityheight == True
        assert (
            weir.comments.name
            == "W stands for weir, 003 because we expect to have at most 999 weirs"
        )

        assert weir.comments.id == uniqueid_str

    def test_id_comment_has_correct_default(self):
        weir = Weir(**self._create_weir_values())

        assert weir.comments.id == uniqueid_str

    def test_add_comment_to_weir(self):
        weir = Weir(**self._create_weir_values())

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

        wrapper = WrapperTest[Weir].model_validate({"val": document.sections[0]})
        weir = wrapper.val

        assert weir.id == "weir_id"
        assert weir.name == "weir"
        assert weir.branchid == "branch"
        assert weir.chainage == pytest.approx(3.0)
        assert weir.type == "weir"
        assert weir.allowedflowdir == FlowDirection.positive
        assert weir.crestlevel == pytest.approx(10.5)
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

        wrapper = WrapperTest[Weir].model_validate({"val": document.sections[0]})
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

    def test_weir_with_unknown_parameter_is_ignored(self):
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

        wrapper = WrapperTest[Weir].model_validate({"val": document.sections[0]})
        weir = wrapper.val

        assert weir.model_dump().get("unknown") is None  # type: ignore

        assert weir.id == "weir_id"
        assert weir.name == "weir"
        assert weir.branchid == "branch"
        assert weir.chainage == pytest.approx(3.0)
        assert weir.type == "weir"
        assert weir.allowedflowdir == FlowDirection.positive
        assert weir.crestlevel == pytest.approx(10.5)
        assert weir.crestwidth is None
        assert weir.usevelocityheight == False

    @pytest.mark.parametrize(
        "input,expected",
        _get_allowedflowdir_cases(),
    )
    def test_weir_parses_flowdirection_case_insensitive(self, input, expected):
        structure = Weir(
            **self._create_required_weir_values(),
            allowedflowdir=input,
        )

        assert structure.allowedflowdir == expected

    def test_optional_fields_have_correct_defaults(self):
        structure = Weir(**self._create_required_weir_values())

        assert structure.allowedflowdir == FlowDirection.both
        assert structure.crestwidth == None

    def _create_required_weir_values(self) -> dict:
        weir_values = dict(
            crestlevel="2.34",
            corrcoeff="5.67",
            usevelocityheight="true",
        )

        weir_values.update(create_structure_values("weir"))
        return weir_values

    def _create_weir_values(self) -> dict:
        weir_values = dict(
            allowedflowdir="positive",
            crestwidth="3.45",
        )

        weir_values.update(self._create_required_weir_values())
        return weir_values


class TestLongCulvert:
    @pytest.fixture
    def longculvert_values(self) -> Dict[str, Any]:
        return {
            "id": "lc1",
            "name": "Long Culvert 1",
            "type": "longCulvert",
            "branchid": "branch_id",
            "chainage": 3.53,
            "numcoordinates": 2,
            "xcoordinates": [6.515339, 44.636787],
            "ycoordinates": [25.151608, 25.727361],
            "zcoordinates": [-0.3, -0.3],
            "width": 0.4,
            "height": 0.2,
            "frictiontype": FrictionType.manning,
            "frictionvalue": 0.035,
            "valverelativeopening": 1.0,
        }

    def test_create_longculvert_minimal(self, longculvert_values: Dict[str, Any]):
        lc = LongCulvert(**longculvert_values)
        assert lc.id == "lc1"
        assert lc.name == "Long Culvert 1"
        assert lc.type == "longCulvert"
        assert lc.numcoordinates == 2
        assert lc.xcoordinates == [6.515339, 44.636787]
        assert lc.ycoordinates == [25.151608, 25.727361]
        assert lc.zcoordinates == [-0.3, -0.3]
        assert lc.width == pytest.approx(0.4)
        assert lc.height == pytest.approx(0.2)
        assert lc.frictiontype == FrictionType.manning
        assert lc.frictionvalue == pytest.approx(0.035)
        assert lc.valverelativeopening == pytest.approx(1.0)

    @pytest.mark.parametrize(
        "missing_field",
        ["numcoordinates", "xcoordinates", "ycoordinates"],
    )
    def test_missing_coordinates_raises(
        self, missing_field, longculvert_values: Dict[str, Any]
    ):
        del longculvert_values[missing_field]
        with pytest.raises(ValueError):
            LongCulvert(**longculvert_values)

    def test_invalid_coordinates_length_raises(
        self, longculvert_values: Dict[str, Any]
    ):
        longculvert_values["numcoordinates"] = 3
        with pytest.raises(ValueError):
            LongCulvert(**longculvert_values)

    def test_invalid_zcoordinates_length_raises(
        self, longculvert_values: Dict[str, Any]
    ):
        longculvert_values["zcoordinates"] = [-0.3, -0.3, -0.4]
        with pytest.raises(ValueError):
            LongCulvert(**longculvert_values)

    def test_create_longculvert_without_zcoordinates(
        self, longculvert_values: Dict[str, Any]
    ):
        del longculvert_values["zcoordinates"]

        lc = LongCulvert(**longculvert_values)
        assert lc.zcoordinates is None


class TestCulvert:
    @pytest.mark.parametrize(
        "missing_field",
        ["valveopeningheight", "numlosscoeff", "relopening", "losscoeff"],
    )
    def test_validate_required_fields_based_on_valveonoff(self, missing_field: str):
        values = self._create_culvert_values(valveonoff=True)
        del values[missing_field]

        with pytest.raises(ValueError) as error:
            Culvert(**values)

        expected_message = f"{missing_field} should be provided when valveonoff is True"
        assert expected_message in str(error.value)

    def test_validate_default_subtype(self):
        culvert = Culvert(**self._create_culvert_values(valveonoff=False))

        assert culvert.subtype == CulvertSubType.culvert

    def test_validate_bendlosscoeff_required_when_invertedsiphon_subtype(self):
        values = self._create_culvert_values(valveonoff=False)
        values["subtype"] = CulvertSubType.invertedSiphon

        with pytest.raises(ValueError) as error:
            Culvert(**values)

        expected_message = (
            "bendlosscoeff should be provided when subtype is invertedSiphon"
        )
        assert expected_message in str(error.value)

    def test_validate_bendlosscoeff_forbidden_when_culvert_subtype(self):
        values = self._create_culvert_values(valveonoff=False)
        values["subtype"] = CulvertSubType.culvert
        values["bendlosscoeff"] = 0.1

        with pytest.raises(ValueError) as error:
            Culvert(**values)

        expected_message = "bendlosscoeff is forbidden when subtype is culvert"
        assert expected_message in str(error.value)

    def _create_culvert_values(self, valveonoff: bool):
        values = create_structure_values("culvert")
        values.update(
            dict(
                allowedflowdir="both",
                leftlevel="1.23",
                rightlevel="2.34",
                csdefid="cs_def_id",
                length="3.45",
                inletlosscoeff="4.56",
                outletlosscoeff="5.67",
                valveonoff=valveonoff,
                bedfrictiontype=FrictionType.whitecolebrook,
                bedfriction="4.32",
            )
        )

        if valveonoff:
            values.update(
                dict(
                    valveopeningheight="6.78",
                    numlosscoeff="10",
                    relopening="7.89 9.87 8.76",
                    losscoeff="7.65 6.54 5.43",
                )
            )

        return values
