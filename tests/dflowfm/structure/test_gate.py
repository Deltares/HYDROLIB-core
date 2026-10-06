import pytest
import inspect

from hydrolib.core.dflowfm.ini.parser import Parser, ParserConfig

from hydrolib.core.dflowfm.bc.models import ForcingModel
from hydrolib.core.dflowfm.tim.models import TimModel
from hydrolib.core.dflowfm.structure.models import (
    Gate,
    GateOpeningHorizontalDirection,
    Structure,
)
from tests.dflowfm.structure.test_structure import (
    create_structure_values,
    uniqueid_str,
)
from tests.utils import (
    WrapperTest,
    test_input_dir
)


class TestGate:
    """
    Wrapper class to test all the methods and subclasses in:
    hydrolib.core.dflowfm.structure.models.py Gate class
    """

    def test_create_a_gate_from_scratch(self):
        gate = Gate(
            **self._create_gate_values(),
            comments=Gate.Comments(
                name="G stands for Gate"
            ),
        )

        assert gate.id == "structure_id"
        assert gate.name == "structure_name"
        assert gate.branchid == "branch_id"
        assert gate.chainage == pytest.approx(1.23)
        assert gate.type == "gate"
        assert gate.crestwidth == pytest.approx(2.34)
        assert gate.crestlevel == pytest.approx(2.34)
        assert gate.gateloweredgelevel == pytest.approx(3.45)
        assert gate.gateheight == pytest.approx(4.56)
        assert gate.gateopeningwidth == pytest.approx(1.23)
        assert gate.gateopeninghorizontaldirection == GateOpeningHorizontalDirection.from_left
        assert gate.comments.name == "G stands for Gate"
        assert gate.comments.id == uniqueid_str

    def test_gate_construction_with_parser(self):
        parser = Parser(ParserConfig())

        input_str = inspect.cleandoc(
            """
            [Structure]
            type = gate                         # Structure type; must read gate
            id = gate_001                       # Unique structure id (max. 256 characters).
            name = Gate_001name                 # Given name in the user interface.
            branchid = gate_branch              # (optional) Branch on which the structure is located.
            chainage = 50.5                     # (optional) Chainage on the branch (m)
            crestLevel = 10.5                   # Crest level of gate (m AD)
            gateLowerEdgeLevel = 8.5            # Position of gate door's lower edge (m AD)
            gateHeight = 2.0                    # Height of the gate door (m)
            gateOpeningWidth = 1.5              # Width of the gate opening (m)
            gateOpeningHorizontalDirection = fromLeft  # Horizontal opening direction
            """
        )

        for line in input_str.splitlines():
            parser.feed_line(line)

        document = parser.finalize()

        wrapper = WrapperTest[Gate].model_validate({"val": document.sections[0]})
        gate = wrapper.val

        assert isinstance(gate, Structure), "Gate should also be an instance of a Structure"
        assert gate.id == "gate_001"
        assert gate.name == "Gate_001name"
        assert gate.branchid == "gate_branch"
        assert gate.chainage == pytest.approx(50.5)
        assert gate.type == "gate"
        assert gate.crestlevel == pytest.approx(10.5)
        assert gate.gateloweredgelevel == pytest.approx(8.5)
        assert gate.gateheight == pytest.approx(2.0)
        assert gate.gateopeningwidth == pytest.approx(1.5)
        assert gate.gateopeninghorizontaldirection == GateOpeningHorizontalDirection.from_left

    def test_gate_with_unknown_parameter_is_ignored(self):
        parser = Parser(ParserConfig())

        input_str = inspect.cleandoc(
            """
            [Structure]
            type = gate                         # Structure type; must read gate
            id = gate_001                       # Unique structure id (max. 256 characters).
            name = Gate_001name                 # Given name in the user interface.
            branchid = gate_branch              # (optional) Branch on which the structure is located.
            chainage = 50.5                     # (optional) Chainage on the branch (m)

            # ----------------------------------------------------------------------
            unknown           = 10.0            # A deliberately added unknown property
            # ----------------------------------------------------------------------

            crestLevel = 10.5                   # Crest level of gate (m AD)
            gateLowerEdgeLevel = 8.5            # Position of gate door's lower edge (m AD)
            gateHeight = 2.0                    # Height of the gate door (m)
            gateOpeningWidth = 1.5              # Width of the gate opening (m)
            gateOpeningHorizontalDirection = fromLeft  # Horizontal opening direction
            """
        )

        for line in input_str.splitlines():
            parser.feed_line(line)

        document = parser.finalize()

        wrapper = WrapperTest[Gate].model_validate({"val": document.sections[0]})
        gate = wrapper.val

        assert gate.model_dump().get("unknown") is None  # type: ignore
        assert gate.id == "gate_001"
        assert gate.name == "Gate_001name"
        assert gate.branchid == "gate_branch"
        assert gate.chainage == pytest.approx(50.5)
        assert gate.type == "gate"
        assert gate.crestlevel == pytest.approx(10.5)
        assert gate.gateloweredgelevel == pytest.approx(8.5)
        assert gate.gateheight == pytest.approx(2.0)

    def test_gate_with_missing_required_parameters(self):
        parser = Parser(ParserConfig())

        input_str = inspect.cleandoc(
            """
            [Structure]
            type = gate                         # Structure type; must read gate
            id = gate_001                       # Unique structure id (max. 256 characters).
            name = Gate_001name                 # Given name in the user interface.
            branchid = gate_branch              # (optional) Branch on which the structure is located.
            chainage = 50.5                     # (optional) Chainage on the branch (m)
            # crestLevel = 10.5                   # Crest level of gate (m AD)
            # gateLowerEdgeLevel = 8.5            # Position of gate door's lower edge (m AD)
            # gateHeight = 2.0                    # Height of the gate door (m)
            """
        )

        for line in input_str.splitlines():
            parser.feed_line(line)

        document = parser.finalize()

        expected_message = "3 validation errors for WrapperTest[Gate]"
        with pytest.raises(ValueError) as exc_err:
            wrapper = WrapperTest[Gate].model_validate({"val": document.sections[0]})
            gate = wrapper.val
        assert expected_message in str(exc_err.value)

        assert "gate" not in locals()  # Gate structure should not have been created


    def test_gate_opening_direction_defaults_to_symmetric(self):
        structure = Gate(**self._create_required_gate_values())

        assert structure.gateopeninghorizontaldirection == GateOpeningHorizontalDirection.symmetric

    def test_gate_opening_width_defaults_to_zero(self):
        structure = Gate(**self._create_required_gate_values())

        assert structure.gateopeningwidth == pytest.approx(0.0)

    def test_optional_fields_have_correct_defaults(self):
        structure = Gate(**self._create_required_gate_values())

        assert structure.crestwidth is None
        assert structure.gateopeningwidth == pytest.approx(0.0)
        assert structure.gateopeninghorizontaldirection == GateOpeningHorizontalDirection.symmetric

    @pytest.mark.parametrize(
        "direction_input, expected_direction",
        [
            pytest.param(GateOpeningHorizontalDirection.symmetric, GateOpeningHorizontalDirection.symmetric),
            pytest.param(GateOpeningHorizontalDirection.from_left, GateOpeningHorizontalDirection.from_left),
            pytest.param(GateOpeningHorizontalDirection.from_right, GateOpeningHorizontalDirection.from_right),
            pytest.param("symmetric", GateOpeningHorizontalDirection.symmetric),
            pytest.param("fromLeft", GateOpeningHorizontalDirection.from_left),
            pytest.param("fromRight", GateOpeningHorizontalDirection.from_right),
        ],
    )
    def test_gate_parses_opening_direction_correctly(self, direction_input, expected_direction):
        structure = Gate(
            **self._create_required_gate_values(),
            gateopeninghorizontaldirection=direction_input,
        )

        assert structure.gateopeninghorizontaldirection == expected_direction

    def test_gate_with_all_fields(self):
        gate = Gate(
            **self._create_gate_values(),
        )

        assert isinstance(gate, Structure), "Gate should also be an instance of a Structure"
        assert gate.id == "structure_id"
        assert gate.name == "structure_name"
        assert gate.type == "gate"
        assert gate.branchid == "branch_id"
        assert gate.chainage == pytest.approx(1.23)
        assert gate.crestwidth == pytest.approx(2.34)
        assert gate.crestlevel == pytest.approx(2.34)
        assert gate.gateloweredgelevel == pytest.approx(3.45)
        assert gate.gateheight == pytest.approx(4.56)
        assert gate.gateopeningwidth == pytest.approx(1.23)
        assert gate.gateopeninghorizontaldirection == GateOpeningHorizontalDirection.from_left

    def _create_required_gate_values(self) -> dict:
        """Create a dict with required field values for a Gate structure."""
        gate_values = dict(
            crestlevel="2.34",
            gateloweredgelevel="3.45",
            gateheight="4.56",
        )

        gate_values.update(create_structure_values("gate"))

        return gate_values

    def _create_gate_values(self) -> dict:
        """Create a dict with all field values for a Gate structure."""
        gate_values = dict(
            crestwidth="2.34",
            gateopeningwidth="1.23",
            gateopeninghorizontaldirection="fromLeft",
        )

        gate_values.update(self._create_required_gate_values())

        return gate_values


class TestGateCrestWidthValidator:
    def test_gate_with_gateopeningwidth_less_than_crestwidth_passes(self):
        """Test that gate with gateOpeningWidth < crestWidth passes validation."""
        gate = Gate(
            id="gate_id",
            name="Gate 01",
            branchid="branch",
            chainage=12.5,
            crestlevel=1.5,
            gateloweredgelevel=0.5,
            gateheight=2.0,
            crestwidth=5.0,
            gateopeningwidth=3.0,
        )
        assert gate.gateopeningwidth == 3.0
        assert gate.crestwidth == 5.0

    def test_gate_with_gateopeningwidth_equal_to_crestwidth_passes(self):
        """Test that gate with gateOpeningWidth == crestWidth passes validation."""
        gate = Gate(
            id="gate_id",
            name="Gate 01",
            branchid="branch",
            chainage=12.5,
            crestlevel=1.5,
            gateloweredgelevel=0.5,
            gateheight=2.0,
            crestwidth=5.0,
            gateopeningwidth=5.0,
        )
        assert gate.gateopeningwidth == 5.0
        assert gate.crestwidth == 5.0

    def test_gate_with_gateopeningwidth_greater_than_crestwidth_raises_error(self):
        """Test that gate with gateOpeningWidth > crestWidth raises validation error."""
        with pytest.raises(ValueError) as exc_err:
            Gate(
                id="gate_id",
                name="Gate 01",
                branchid="branch",
                chainage=12.5,
                crestlevel=1.5,
                gateloweredgelevel=0.5,
                gateheight=2.0,
                crestwidth=3.0,
                gateopeningwidth=5.0,
            )
        assert "`gateOpeningWidth` should be smaller than or equal to `crestWidth`." in str(exc_err.value)

    def test_gate_with_default_gateopeningwidth_passes(self):
        """Test that gate with default gateOpeningWidth (0.0) passes validation."""
        gate = Gate(
            id="gate_id",
            name="Gate 01",
            branchid="branch",
            chainage=12.5,
            crestlevel=1.5,
            gateloweredgelevel=0.5,
            gateheight=2.0,
            crestwidth=3.0,
            # gateopeningwidth not specified, defaults to 0.0
        )
        assert gate.gateopeningwidth == 0.0
        assert gate.crestwidth == 3.0

    def test_gate_with_none_crestwidth_passes(self):
        """Test that gate with None crestWidth skips validation."""
        gate = Gate(
            id="gate_id",
            name="Gate 01",
            branchid="branch",
            chainage=12.5,
            crestlevel=1.5,
            gateloweredgelevel=0.5,
            gateheight=2.0,
            crestwidth=None,
            gateopeningwidth=5.0,
        )
        assert gate.crestwidth is None
        assert gate.gateopeningwidth == 5.0

    def test_gate_with_timmodel_gateopeningwidth_skips_validation(self):
        """Test that gate with TimModel gateOpeningWidth skips validation."""
        tim_file = test_input_dir / "tim" / "single_data_for_timeseries.tim"
        gate = Gate(
            id="gate_id",
            name="Gate 01",
            branchid="branch",
            chainage=12.5,
            crestlevel=1.5,
            gateloweredgelevel=0.5,
            gateheight=2.0,
            crestwidth=3.0,
            gateopeningwidth=tim_file,
        )
        assert isinstance(gate.gateopeningwidth, TimModel)

    def test_gate_with_forcingmodel_gateopeningwidth_skips_validation(self):
        """Test that gate with ForcingModel gateOpeningWidth skips validation."""
        bc_file = (
            test_input_dir
            / "dflowfm_individual_files"
            / "FlowFM_boundaryconditions2d_and_vectors.bc"
        )
        gate = Gate(
            id="gate_id",
            name="Gate 01",
            branchid="branch",
            chainage=12.5,
            crestlevel=1.5,
            gateloweredgelevel=0.5,
            gateheight=2.0,
            crestwidth=3.0,
            gateopeningwidth=bc_file,
        )
        assert isinstance(gate.gateopeningwidth, ForcingModel)
