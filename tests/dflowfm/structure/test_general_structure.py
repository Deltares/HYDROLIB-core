import inspect

import pytest

from hydrolib.core.dflowfm.bc.models import ForcingModel
from hydrolib.core.dflowfm.ini.parser import Parser, ParserConfig
from hydrolib.core.dflowfm.structure.models import (
    FlowDirection,
    GateOpeningHorizontalDirection,
    GeneralStructure,
)
from hydrolib.core.dflowfm.tim.models import TimModel
from tests.dflowfm.structure.test_structure import create_structure_values, uniqueid_str
from tests.utils import WrapperTest, test_input_dir


class TestGeneralStructure:
    def test_initialize_gateopeningwidth_with_timfile_initializes_timmodel(self):
        gateloweredgelevel = test_input_dir / "tim" / "single_data_for_timeseries.tim"
        values = self._create_general_structure_values()
        values["gateloweredgelevel"] = gateloweredgelevel
        structure = GeneralStructure(**values)

        assert isinstance(structure.gateloweredgelevel, TimModel)

    def test_initialize_gateopeningwidth_with_bcfile_initializes_forcingmodel(self):
        gateloweredgelevel = (
            test_input_dir
            / "dflowfm_individual_files"
            / "FlowFM_boundaryconditions2d_and_vectors.bc"
        )
        values = self._create_general_structure_values()
        values["gateloweredgelevel"] = gateloweredgelevel
        structure = GeneralStructure(**values)

        assert isinstance(structure.gateloweredgelevel, ForcingModel)

    def test_initialize_gateopeningwidth_with_float_value_initializes_float(self):
        gateloweredgelevel = 123.456
        values = self._create_general_structure_values()
        values["gateloweredgelevel"] = gateloweredgelevel
        structure = GeneralStructure(**values)

        assert isinstance(structure.gateloweredgelevel, float)

    def test_create_a_general_structure_from_scratch(self):
        name_comment = "Generic name comment"
        struct = GeneralStructure(
            **self._create_general_structure_values(),
            comments=GeneralStructure.Comments(name=name_comment),
        )

        assert struct.id == "structure_id"
        assert struct.name == "structure_name"
        assert struct.branchid == "branch_id"
        assert struct.chainage == pytest.approx(1.23)

        assert struct.allowedflowdir == FlowDirection.positive
        assert struct.upstream1width == pytest.approx(1.0)
        assert struct.upstream1level == pytest.approx(2.0)
        assert struct.upstream2width == pytest.approx(3.0)
        assert struct.upstream2level == pytest.approx(4.0)
        assert struct.crestwidth == pytest.approx(5.0)
        assert struct.crestlevel == pytest.approx(6.0)
        assert struct.crestlength == pytest.approx(7.0)
        assert struct.downstream1width == pytest.approx(8.0)
        assert struct.downstream1level == pytest.approx(9.0)
        assert struct.downstream2width == pytest.approx(9.1)
        assert struct.downstream2level == pytest.approx(9.2)
        assert struct.gateloweredgelevel == pytest.approx(9.3)
        assert struct.posfreegateflowcoeff == pytest.approx(9.4)
        assert struct.posdrowngateflowcoeff == pytest.approx(9.5)
        assert struct.posfreeweirflowcoeff == pytest.approx(9.6)
        assert struct.posdrownweirflowcoeff == pytest.approx(9.7)
        assert struct.poscontrcoeffreegate == pytest.approx(9.8)
        assert struct.negfreegateflowcoeff == pytest.approx(9.9)
        assert struct.negdrowngateflowcoeff == pytest.approx(8.1)
        assert struct.negfreeweirflowcoeff == pytest.approx(8.2)
        assert struct.negdrownweirflowcoeff == pytest.approx(8.3)
        assert struct.negcontrcoeffreegate == pytest.approx(8.4)
        assert struct.extraresistance == pytest.approx(8.5)
        assert struct.gateheight == pytest.approx(8.6)
        assert struct.gateopeningwidth == pytest.approx(8.7)
        assert (
            struct.gateopeninghorizontaldirection
            == GateOpeningHorizontalDirection.from_left
        )
        assert struct.usevelocityheight == False

        assert struct.comments is not None
        assert struct.comments.name == name_comment

        assert struct.comments.id == uniqueid_str

    def test_id_comment_has_correct_default(self):
        struct = GeneralStructure(**self._create_general_structure_values())
        assert struct.comments is not None
        assert struct.comments.id == uniqueid_str

    def test_add_comment_to_general_structure(self):
        struct = GeneralStructure(**self._create_general_structure_values())

        assert struct.comments is not None

        new_comment = "a very different value"

        struct.comments.usevelocityheight = new_comment
        assert struct.comments.usevelocityheight == new_comment

    def test_general_structure_construction_with_parser(self):
        parser = Parser(ParserConfig())

        input_str = inspect.cleandoc(
            """
            [Structure]
            id                             = potato_id        # Unique structure id (max. 256 characters).
            name                           = structure_potato # Given name in the user interface.
            type                           = generalStructure # Structure type; must read generalStructure
            branchId                       = branch           # Branch on which the structure is located.
            chainage                       = 3.53             # Chainage on the branch (m).
            allowedFlowDir                 = positive         # Possible values: both, positive, negative, none.
            upstream1Width                 = 11.0             # w_u1 [m]
            upstream1Level                 = 12.0             # z_u1 [m AD]
            upstream2Width                 = 13.0             # w_u2 [m]
            upstream2Level                 = 14.0             # z_u2 [m D]
            crestWidth                     = 15.0             # w_s [m]
            crestLevel                     = 16.0             # z_s [m AD]
            crestLength                    = 17.0             # The crest length across the general structure [m]. When the crest length > 0, the extra resistance for this structure will be ls * g/(C2 * waterdepth)
            downstream1Width               = 18.0             # w_d1 [m]
            downstream1Level               = 19.0             # z_d1 [m AD]
            downstream2Width               = 19.1             # w_d1 [m]
            downstream2Level               = 19.2             # z_d1 [m AD]
            gateLowerEdgeLevel             = 19.3             # Position of gate door’s lower edge [m AD]
            posFreeGateFlowCoeff           = 19.4             # Positive free gate flow corr.coeff. cgf [-]
            posDrownGateFlowCoeff          = 19.5             # Positive drowned gate flow corr.coeff. cgd [-]
            posFreeWeirFlowCoeff           = 19.6             # Positive free weir flow corr.coeff. cwf [-]
            posDrownWeirFlowCoeff          = 19.7             # Positive drowned weir flow corr.coeff. cwd [-]
            posContrCoefFreeGate           = 19.8             # Positive gate flow contraction coefficient µgf [-]
            negFreeGateFlowCoeff           = 19.9             # Negative free gate flow corr.coeff. cgf [-]
            negDrownGateFlowCoeff          = 18.1             # Negative drowned gate flow corr.coeff. cgd [-]
            negFreeWeirFlowCoeff           = 18.2             # Negative free weir flow corr.coeff. cwf [-]
            negDrownWeirFlowCoeff          = 18.3             # Negative drowned weir flow corr.coeff. cwd [-]
            negContrCoefFreeGate           = 18.4             # Negative gate flow contraction coefficient mu gf [-]
            extraResistance                = 18.5             # Extra resistance [-]
            gateHeight                     = 18.6
            gateOpeningWidth               = 18.7             # Opening width between gate doors [m], should be smaller than (or equal to) crestWidth
            gateOpeningHorizontalDirection = fromLeft         # Horizontal opening direction of gate door[s]. Possible values are: symmetric, fromLeft, fromRight
            useVelocityHeight              = 0                # Flag indicates whether the velocity height is to be calculated or not
            """
        )

        for line in input_str.splitlines():
            parser.feed_line(line)

        document = parser.finalize()

        wrapper = WrapperTest[GeneralStructure].model_validate(
            {"val": document.sections[0]}
        )
        struct = wrapper.val

        assert struct.id == "potato_id"
        assert struct.name == "structure_potato"
        assert struct.branchid == "branch"
        assert struct.chainage == pytest.approx(3.53)
        assert struct.type == "generalstructure"
        assert struct.allowedflowdir == FlowDirection.positive
        assert struct.upstream1width == pytest.approx(11.0)
        assert struct.upstream1level == pytest.approx(12.0)
        assert struct.upstream2width == pytest.approx(13.0)
        assert struct.upstream2level == pytest.approx(14.0)
        assert struct.crestwidth == pytest.approx(15.0)
        assert struct.crestlevel == pytest.approx(16.0)
        assert struct.crestlength == pytest.approx(17.0)
        assert struct.downstream1width == pytest.approx(18.0)
        assert struct.downstream1level == pytest.approx(19.0)
        assert struct.downstream2width == pytest.approx(19.1)
        assert struct.downstream2level == pytest.approx(19.2)
        assert struct.gateloweredgelevel == pytest.approx(19.3)
        assert struct.posfreegateflowcoeff == pytest.approx(19.4)
        assert struct.posdrowngateflowcoeff == pytest.approx(19.5)
        assert struct.posfreeweirflowcoeff == pytest.approx(19.6)
        assert struct.posdrownweirflowcoeff == pytest.approx(19.7)
        assert struct.poscontrcoeffreegate == pytest.approx(19.8)
        assert struct.negfreegateflowcoeff == pytest.approx(19.9)
        assert struct.negdrowngateflowcoeff == pytest.approx(18.1)
        assert struct.negfreeweirflowcoeff == pytest.approx(18.2)
        assert struct.negdrownweirflowcoeff == pytest.approx(18.3)
        assert struct.negcontrcoeffreegate == pytest.approx(18.4)
        assert struct.extraresistance == pytest.approx(18.5)
        assert struct.gateheight == pytest.approx(18.6)
        assert struct.gateopeningwidth == pytest.approx(18.7)
        assert (
            struct.gateopeninghorizontaldirection
            == GateOpeningHorizontalDirection.from_left
        )
        assert struct.usevelocityheight == False

    def test_weir_comments_construction_with_parser(self):
        parser = Parser(ParserConfig())

        input_str = inspect.cleandoc(
            """
            [Structure]
            id                             = potato_id        
            name                           = structure_potato 
            type                           = generalStructure 
            branchId                       = branch           
            chainage                       = 3.53   # My own special comment 1
            allowedFlowDir                 = positive         
            upstream1Width                 = 11.0             
            upstream1Level                 = 12.0             
            upstream2Width                 = 13.0             
            upstream2Level                 = 14.0             
            crestWidth                     = 15.0             
            crestLevel                     = 16.0             
            crestLength                    = 17.0             
            downstream1Width               = 18.0             
            downstream1Level               = 19.0             
            downstream2Width               = 19.1             
            downstream2Level               = 19.2             
            gateLowerEdgeLevel             = 19.3             
            posFreeGateFlowCoeff           = 19.4             
            posDrownGateFlowCoeff          = 19.5             
            posFreeWeirFlowCoeff           = 19.6             
            posDrownWeirFlowCoeff          = 19.7             
            posContrCoefFreeGate           = 19.8             
            negFreeGateFlowCoeff           = 19.9             
            negDrownGateFlowCoeff          = 18.1             
            negFreeWeirFlowCoeff           = 18.2             
            negDrownWeirFlowCoeff          = 18.3             
            negContrCoefFreeGate           = 18.4             
            extraResistance                = 18.5             
            gateHeight                     = 18.6
            gateOpeningWidth               = 18.7              
            gateOpeningHorizontalDirection = fromLeft         
            useVelocityHeight              = 0    # My own special comment 2            
            """
        )

        for line in input_str.splitlines():
            parser.feed_line(line)

        document = parser.finalize()

        wrapper = WrapperTest[GeneralStructure].model_validate(
            {"val": document.sections[0]}
        )
        struct = wrapper.val

        assert struct.comments is not None
        assert struct.comments.id is None
        assert struct.comments.name is None
        assert struct.comments.branchid is None
        assert struct.comments.chainage == "My own special comment 1"
        assert struct.comments.type is None

        assert struct.comments.allowedflowdir is None
        assert struct.comments.upstream1width is None
        assert struct.comments.upstream1level is None
        assert struct.comments.upstream2width is None
        assert struct.comments.upstream2level is None
        assert struct.comments.crestwidth is None
        assert struct.comments.crestlevel is None
        assert struct.comments.crestlength is None
        assert struct.comments.downstream1width is None
        assert struct.comments.downstream1level is None
        assert struct.comments.downstream2width is None
        assert struct.comments.downstream2level is None
        assert struct.comments.gateloweredgelevel is None
        assert struct.comments.posfreegateflowcoeff is None
        assert struct.comments.posdrowngateflowcoeff is None
        assert struct.comments.posfreeweirflowcoeff is None
        assert struct.comments.posdrownweirflowcoeff is None
        assert struct.comments.poscontrcoeffreegate is None
        assert struct.comments.negfreegateflowcoeff is None
        assert struct.comments.negdrowngateflowcoeff is None
        assert struct.comments.negfreeweirflowcoeff is None
        assert struct.comments.negdrownweirflowcoeff is None
        assert struct.comments.negcontrcoeffreegate is None
        assert struct.comments.extraresistance is None
        assert struct.comments.gateheight is None
        assert struct.comments.gateopeningwidth is None
        assert struct.comments.usevelocityheight == "My own special comment 2"

    def test_general_structure_with_unknown_parameter_is_ignored(self):
        parser = Parser(ParserConfig())

        input_str = inspect.cleandoc(
            """
            [Structure]
            id                             = id        
            name                           = extravagante_waarde

            # ----------------------------------------------------------------------
            unknown           = 10.0        # A deliberately added unknown property
            # ----------------------------------------------------------------------

            type                           = generalStructure 
            branchId                       = stump
            chainage                       = 13.53  
            allowedFlowDir                 = positive         
            upstream1Width                 = 111.0             
            upstream1Level                 = 112.0             
            upstream2Width                 = 113.0             
            upstream2Level                 = 114.0             
            crestWidth                     = 115.0             
            crestLevel                     = 116.0             
            crestLength                    = 117.0             
            downstream1Width               = 118.0             
            downstream1Level               = 119.0             
            downstream2Width               = 119.1             
            downstream2Level               = 119.2             
            gateLowerEdgeLevel             = 119.3             
            posFreeGateFlowCoeff           = 119.4             
            posDrownGateFlowCoeff          = 119.5             
            posFreeWeirFlowCoeff           = 119.6             
            posDrownWeirFlowCoeff          = 119.7             
            posContrCoefFreeGate           = 119.8             
            negFreeGateFlowCoeff           = 119.9             
            negDrownGateFlowCoeff          = 118.1             
            negFreeWeirFlowCoeff           = 118.2             
            negDrownWeirFlowCoeff          = 118.3             
            negContrCoefFreeGate           = 118.4             
            extraResistance                = 118.5             
            gateHeight                     = 118.6
            gateOpeningWidth               = 118.7              
            gateOpeningHorizontalDirection = fromRight
            useVelocityHeight              = 0
            """
        )

        for line in input_str.splitlines():
            parser.feed_line(line)

        document = parser.finalize()

        wrapper = WrapperTest[GeneralStructure].model_validate(
            {"val": document.sections[0]}
        )
        struct = wrapper.val

        assert struct.model_dump().get("unknown") is None  # type: ignore

        assert struct.id == "id"
        assert struct.name == "extravagante_waarde"
        assert struct.branchid == "stump"
        assert struct.chainage == pytest.approx(13.53)
        assert struct.type == "generalstructure"
        assert struct.allowedflowdir == FlowDirection.positive
        assert struct.upstream1width == pytest.approx(111.0)
        assert struct.upstream1level == pytest.approx(112.0)
        assert struct.upstream2width == pytest.approx(113.0)
        assert struct.upstream2level == pytest.approx(114.0)
        assert struct.crestwidth == pytest.approx(115.0)
        assert struct.crestlevel == pytest.approx(116.0)
        assert struct.crestlength == pytest.approx(117.0)
        assert struct.downstream1width == pytest.approx(118.0)
        assert struct.downstream1level == pytest.approx(119.0)
        assert struct.downstream2width == pytest.approx(119.1)
        assert struct.downstream2level == pytest.approx(119.2)
        assert struct.gateloweredgelevel == pytest.approx(119.3)
        assert struct.posfreegateflowcoeff == pytest.approx(119.4)
        assert struct.posdrowngateflowcoeff == pytest.approx(119.5)
        assert struct.posfreeweirflowcoeff == pytest.approx(119.6)
        assert struct.posdrownweirflowcoeff == pytest.approx(119.7)
        assert struct.poscontrcoeffreegate == pytest.approx(119.8)
        assert struct.negfreegateflowcoeff == pytest.approx(119.9)
        assert struct.negdrowngateflowcoeff == pytest.approx(118.1)
        assert struct.negfreeweirflowcoeff == pytest.approx(118.2)
        assert struct.negdrownweirflowcoeff == pytest.approx(118.3)
        assert struct.negcontrcoeffreegate == pytest.approx(118.4)
        assert struct.extraresistance == pytest.approx(118.5)
        assert struct.gateheight == pytest.approx(118.6)
        assert struct.gateopeningwidth == pytest.approx(118.7)
        assert (
            struct.gateopeninghorizontaldirection
            == GateOpeningHorizontalDirection.from_right
        )
        assert struct.usevelocityheight == False

    def _create_required_general_structure_values(self) -> dict:
        general_structure_values = dict()
        general_structure_values.update(create_structure_values("generalStructure"))
        return general_structure_values

    def _create_general_structure_values(self) -> dict:
        general_structure_values = dict(
            allowedflowdir=FlowDirection.positive,
            upstream1width=1.0,
            upstream1level=2.0,
            upstream2width=3.0,
            upstream2level=4.0,
            crestwidth=5.0,
            crestlevel=6.0,
            crestlength=7.0,
            downstream1width=8.0,
            downstream1level=9.0,
            downstream2width=9.1,
            downstream2level=9.2,
            gateloweredgelevel=9.3,
            posfreegateflowcoeff=9.4,
            posdrowngateflowcoeff=9.5,
            posfreeweirflowcoeff=9.6,
            posdrownweirflowcoeff=9.7,
            poscontrcoeffreegate=9.8,
            negfreegateflowcoeff=9.9,
            negdrowngateflowcoeff=8.1,
            negfreeweirflowcoeff=8.2,
            negdrownweirflowcoeff=8.3,
            negcontrcoeffreegate=8.4,
            extraresistance=8.5,
            gateheight=8.6,
            gateopeningwidth=8.7,
            gateopeninghorizontaldirection=GateOpeningHorizontalDirection.from_left,
            usevelocityheight=False,
        )

        general_structure_values.update(
            self._create_required_general_structure_values()
        )
        return general_structure_values
