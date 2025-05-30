import inspect
import pytest
from pathlib import Path
from typing import Any, List
from hydrolib.core.dflowfm.ini.parser import Parser, ParserConfig
from hydrolib.core.dflowfm.structure import Dambreak, Pump, Orientation, Structure
from tests.dflowfm.structure.test_structure import uniqueid_str, create_structure_values
from tests.utils import WrapperTest, create_temp_file
from unittest.mock import MagicMock


class DambreakTestCases:
    """Just a wrapper so it can be referenced from other classes."""

    check_location_err = "Specify location either by setting `num/x/yCoordinates` or `polylinefile` fields for a Dambreak structure."
    check_upstream_waterlevel_location_err = "Either `waterLevelUpstreamNodeId` should be specified or `waterLevelUpstreamLocationX` and `waterLevelUpstreamLocationY`."
    check_downstream_waterlevel_location_err = "Either `waterLevelDownstreamNodeId` should be specified or `waterLevelDownstreamLocationX` and `waterLevelDownstreamLocationY`."
    too_few_coords = "Expected at least 2 coordinates, but only {} declared."
    mismatch_coords = (
        "Expected {} coordinates, given {} for xCoordinates and {} for yCoordinates."
    )


def _get_orientation_cases() -> List:
    return [
        ("Positive", "positive"),
        ("NEGATIVE", "negative"),
    ]


class TestDambreak:
    """
    Wrapper class to test all the methods and sublcasses in:
    hydrolib.core.dflowfm.structure.models.py Dambreak class.
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
        test_values = {**default_dambreak_values, **location_dict}

        with pytest.raises(ValueError) as exc_err:
            Dambreak(**test_values)

        assert err_mssg in str(exc_err.value)

    def test_given_valid_values_creates_dambreak(self, valid_dambreak_values: dict):
        dambreak = Dambreak(**valid_dambreak_values)
        self.validate_valid_default_dambreak(dambreak)

    def test_given_structure_text_with_num_x_y_coordinates_parses_structure(self):

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
            waterLevelUpstreamNodeId = anUpstreamNodeId # Node Id of custom upstream water level point.
            waterLevelDownstreamNodeId = aDownstreamNodeId # Node Id of custom downstream water level point.
            """
        )

        dambreak_obj = self.parse_dambreak_from_text(structure_text)
        self.validate_valid_default_dambreak(dambreak_obj)

    # def test_given_structure_text_with_polylinefile_parses_structure(self):
    #     structure_text = inspect.cleandoc(
    #         """
    #         [structure]
    #         type                       = dambreak
    #         id                         = dambreak
    #         polylinefile               = dambreak2ddrybreach.pli
    #         startLocationX             = 1.2
    #         startLocationY             = 4.0
    #         algorithm                  = 3             # 1 VdKnaap ,2 Verheij-vdKnaap
    #         crestLevelIni              = 0.4
    #         breachWidthIni             = 1
    #         crestLevelMin              = 0.2
    #         timeToBreachToMaximumDepth = 0.1           #in seconds
    #         f1                         = 1
    #         f2                         = 1
    #         ucrit                      = 0.001
    #         t0                         = 0.0001        # make it a boolean
    #         dambreakLevelsAndWidths    = {}  #used only in algorithm 3
    #         waterLevelUpstreamLocationX = 1.2 # x-coordinate of custom upstream water level point.
    #         waterLevelUpstreamLocationY = 2.3 # y-coordinate of custom upstream water level point.
    #         waterLevelDownstreamLocationX = 3.4 # x-coordinate of custom downstream water level point.
    #         waterLevelDownstreamLocationY = 4.5 # y-coordinate of custom downstream water level point.
    #         """
    #     )
    #
    #     with create_temp_file("", "dambreak.tim") as tim_file:
    #         structure_text = structure_text.format(tim_file)
    #
    #         dambreak_obj = self.parse_dambreak_from_text(structure_text)
    #
    #     assert dambreak_obj
    #     assert isinstance(dambreak_obj, Structure)
    #     assert dambreak_obj.type == "dambreak"
    #     assert dambreak_obj.id == "dambreak"
    #     assert dambreak_obj.polylinefile.filepath == Path("dambreak2ddrybreach.pli")
    #     assert dambreak_obj.startlocationx == pytest.approx(1.2)
    #     assert dambreak_obj.startlocationy == pytest.approx(4.0)
    #     assert dambreak_obj.algorithm == 3
    #     assert dambreak_obj.crestlevelini == pytest.approx(0.4)
    #     assert dambreak_obj.breachwidthini == 1
    #     assert dambreak_obj.crestlevelmin == pytest.approx(0.2)
    #     assert dambreak_obj.timetobreachtomaximumdepth == pytest.approx(0.1)
    #     assert dambreak_obj.f1 == 1
    #     assert dambreak_obj.f2 == 1
    #     assert dambreak_obj.ucrit == pytest.approx(0.001)
    #     assert dambreak_obj.t0 == pytest.approx(0.0001)
    #     assert dambreak_obj.dambreaklevelsandwidths.filepath.name == "dambreak.tim"
    #     assert dambreak_obj.waterlevelupstreamlocationx == pytest.approx(1.2)
    #     assert dambreak_obj.waterlevelupstreamlocationy == pytest.approx(2.3)
    #     assert dambreak_obj.waterleveldownstreamlocationx == pytest.approx(3.4)
    #     assert dambreak_obj.waterleveldownstreamlocationy == pytest.approx(4.5)
    #     assert dambreak_obj.waterlevelupstreamnodeid == None
    #     assert dambreak_obj.waterleveldownstreamnodeid == None

    def parse_dambreak_from_text(self, structure_text: str) -> Dambreak:
        """
        Method just to simplify how the tests can parse a dambreak without having to
        repeat the same code for each test.

        Args:
            structure_text (str): Text containing Dambreak structure.

        Returns:
            Dambreak: Parsed object.
        """
        parser = Parser(ParserConfig())
        for line in structure_text.splitlines():
            parser.feed_line(line)
        document = parser.finalize()

        return WrapperTest[Dambreak].model_validate({"val": document.sections[0]}).val

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
        assert dambreak.startlocationx == pytest.approx(4.2)
        assert dambreak.startlocationy == pytest.approx(2.4)
        assert dambreak.algorithm == 1
        assert dambreak.crestlevelini == 1
        assert dambreak.breachwidthini == 24
        assert dambreak.crestlevelmin == 42
        assert dambreak.t0 == pytest.approx(2.2)
        assert dambreak.timetobreachtomaximumdepth == pytest.approx(4.4)
        assert dambreak.f1 == pytest.approx(22.4)
        assert dambreak.f2 == pytest.approx(44.2)
        assert dambreak.ucrit == pytest.approx(44.22)
        assert dambreak.numcoordinates == 2
        assert dambreak.xcoordinates == [4.2, 2.4]
        assert dambreak.ycoordinates == [2.4, 4.2]
        assert dambreak.waterlevelupstreamlocationx == None
        assert dambreak.waterlevelupstreamlocationy == None
        assert dambreak.waterleveldownstreamlocationx == None
        assert dambreak.waterleveldownstreamlocationy == None
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
                    dict(
                        numcoordinates=2,
                        xcoordinates=[0, 1],
                        ycoordinates=[2, 3],
                        waterlevelupstreamnodeid="anUpstreamNodeId",
                        waterleveldownstreamnodeid="aDownstreamNodeId",
                    ),
                    id="With 2 coordinates and waterlevelupstreamnodeid and waterleveldownstreamnodeid",
                ),
                pytest.param(
                    dict(
                        numcoordinates=3,
                        xcoordinates=[0, 1, 2],
                        ycoordinates=[2, 3, 4],
                        waterlevelupstreamnodeid="anUpstreamNodeId",
                        waterleveldownstreamlocationx=3.4,
                        waterleveldownstreamlocationy=4.5,
                    ),
                    id="With 3 coordinates and waterlevelupstreamnodeid and waterleveldownstreamlocationx and waterleveldownstreamlocationy",
                ),
                pytest.param(
                    dict(
                        polylinefile=Path(),
                        waterlevelupstreamlocationx=1.2,
                        waterlevelupstreamlocationy=2.3,
                        waterleveldownstreamnodeid="aDownstreamNodeId",
                    ),
                    id="Empty path and waterlevelupstreamlocationx and waterlevelupstreamlocationy and waterleveldownstreamnodeid",
                ),
                pytest.param(
                    dict(
                        polylinefile=Path("aFilePath"),
                        waterlevelupstreamlocationx=1.2,
                        waterlevelupstreamlocationy=2.3,
                        waterleveldownstreamlocationx=3.4,
                        waterleveldownstreamlocationy=4.5,
                    ),
                    id="Path with file name and waterlevelupstreamlocationx and waterlevelupstreamlocationy and waterleveldownstreamlocationx and waterleveldownstreamlocationy",
                ),
            ],
        )
        def test_given_valid_values_returns_values(self, dict_values: dict):
            # with patch("hydrolib.core.dflowfm.structure.models.Dambreak.model_dump") as mock_model_dump:
            mock_dambreak = MagicMock(spec=Dambreak)
            mock_dambreak.model_dump.return_value = dict_values
            mock_dambreak.check_location_dambreak = Dambreak.check_location_dambreak.__get__(mock_dambreak, Dambreak)
            mock_dambreak._validate_waterlevel_location = Dambreak._validate_waterlevel_location
            assert mock_dambreak.check_location_dambreak()

        @pytest.mark.parametrize(
            "invalid_values, expected_err",
            [
                pytest.param(
                    dict(
                        numcoordinates=None,
                        xcoordinates=None,
                        ycoordinates=None,
                        polylinefile=None,
                        waterlevelupstreamnodeid="anUpstreamNodeId",
                        waterleveldownstreamnodeid="aDownstreamNodeId",
                    ),
                    DambreakTestCases.check_location_err,
                    id="Specified locations None",
                ),
                pytest.param(
                    dict(
                        waterleveldownstreamnodeid="aDownstreamNodeId",
                        waterlevelupstreamnodeid=None,
                    ),
                    DambreakTestCases.check_upstream_waterlevel_location_err,
                    id="No upstream water level locations specified",
                ),
                pytest.param(
                    dict(
                        waterleveldownstreamnodeid="aDownstreamNodeId",
                        waterlevelupstreamlocationx=1.2,
                    ),
                    DambreakTestCases.check_upstream_waterlevel_location_err,
                    id="Only upstream water level location x specified",
                ),
                pytest.param(
                    dict(
                        waterleveldownstreamnodeid="aDownstreamNodeId",
                        waterlevelupstreamlocationy=2.3,
                    ),
                    DambreakTestCases.check_upstream_waterlevel_location_err,
                    id="Only upstream water level location y specified",
                ),
                pytest.param(
                    dict(
                        waterleveldownstreamnodeid="aDownstreamNodeId",
                        waterlevelupstreamnodeid="anUpstreamNodeId",
                        waterlevelupstreamlocationx=1.2,
                    ),
                    DambreakTestCases.check_upstream_waterlevel_location_err,
                    id="Upstream water level location node id and x specified",
                ),
                pytest.param(
                    dict(
                        waterleveldownstreamnodeid="aDownstreamNodeId",
                        waterlevelupstreamnodeid="anUpstreamNodeId",
                        waterlevelupstreamlocationy=2.3,
                    ),
                    DambreakTestCases.check_upstream_waterlevel_location_err,
                    id="Upstream water level location node id and y specified",
                ),
                pytest.param(
                    dict(
                        waterleveldownstreamnodeid="aDownstreamNodeId",
                        waterlevelupstreamnodeid="anUpstreamNodeId",
                        waterlevelupstreamlocationx=1.2,
                        waterlevelupstreamlocationy=2.3,
                    ),
                    DambreakTestCases.check_upstream_waterlevel_location_err,
                    id="Upstream water level location node id, x and y specified",
                ),
                pytest.param(
                    dict(
                        waterlevelupstreamnodeid="anUpstreamNodeId",
                        waterleveldownstreamnodeid=None,
                    ),
                    DambreakTestCases.check_downstream_waterlevel_location_err,
                    id="No downstream water level locations specified",
                ),
                pytest.param(
                    dict(
                        waterlevelupstreamnodeid="anUpstreamNodeId",
                        waterleveldownstreamlocationx=3.4,
                    ),
                    DambreakTestCases.check_downstream_waterlevel_location_err,
                    id="Only downstream water level location x specified",
                ),
                pytest.param(
                    dict(
                        waterlevelupstreamnodeid="anUpstreamNodeId",
                        waterleveldownstreamlocationy=4.5,
                    ),
                    DambreakTestCases.check_downstream_waterlevel_location_err,
                    id="Only downstream water level location y specified",
                ),
                pytest.param(
                    dict(
                        waterlevelupstreamnodeid="anUpstreamNodeId",
                        waterleveldownstreamnodeid="aDownstreamNodeId",
                        waterleveldownstreamlocationx=3.4,
                    ),
                    DambreakTestCases.check_downstream_waterlevel_location_err,
                    id="Downstream water level location node id and x specified",
                ),
                pytest.param(
                    dict(
                        waterlevelupstreamnodeid="anUpstreamNodeId",
                        waterleveldownstreamnodeid="aDownstreamNodeId",
                        waterleveldownstreamlocationy=4.5,
                    ),
                    DambreakTestCases.check_downstream_waterlevel_location_err,
                    id="Downstream water level location node id and y specified",
                ),
                pytest.param(
                    dict(
                        waterlevelupstreamnodeid="anUpstreamNodeId",
                        waterleveldownstreamnodeid="aDownstreamNodeId",
                        waterleveldownstreamlocationx=3.4,
                        waterleveldownstreamlocationy=4.5,
                    ),
                    DambreakTestCases.check_downstream_waterlevel_location_err,
                    id="Downstream water level location node id, x and y specified",
                ),
            ],
        )
        def test_given_invalid_values_raises_expectation(
                self, invalid_values: dict, expected_err: str, valid_dambreak_values: dict
        ):
            init_values = valid_dambreak_values
            init_values.update(invalid_values)
            with pytest.raises(ValueError) as exc_err:
                _ = Dambreak(**init_values)
            assert expected_err in str(exc_err.value)


class TestPump:
    _pumplists = [
        ("startlevelsuctionside", "numstages"),
        ("stoplevelsuctionside", "numstages"),
        ("startleveldeliveryside", "numstages"),
        ("stopleveldeliveryside", "numstages"),
        ("head", "numreductionlevels"),
        ("reductionfactor", "numreductionlevels"),
    ]

    def test_create_a_pump_from_scratch(self):
        pump = Pump(
            **self._create_pump_values(),
            comments=Pump.Comments(
                name="P stands for pump, 003 because we expect to have at most 999 pumps"
            ),
        )

        assert pump.id == "structure_id"
        assert pump.name == "structure_name"
        assert pump.branchid == "branch_id"
        assert pump.capacity == pytest.approx(2.34)
        assert pump.orientation == Orientation.negative
        assert pump.numreductionlevels == 2
        assert pump.head == [0, 2]
        assert pump.reductionfactor == [0, 0.1]
        assert (
                pump.comments.name
                == "P stands for pump, 003 because we expect to have at most 999 pumps"
        )

        assert pump.comments.id == uniqueid_str

    def test_pump_construction_with_parser(self):
        parser = Parser(ParserConfig())

        input_str = inspect.cleandoc(
            """
            [Structure]
            id                = pump_id     # Unique structure id (max. 256 characters).
            name              = pump_nm     # Given name in the user interface.
            branchId          = branch      # (optional) Branch on which the structure is located.
            chainage          = 3.0         # (optional) Chainage on the branch (m)
            type              = pump        # Structure type
            orientation       = positive    # Possible values: positive, negative.
            capacity          = 10.5        # Crest level of weir (m AD)
            """
        )

        for line in input_str.splitlines():
            parser.feed_line(line)

        document = parser.finalize()

        wrapper = WrapperTest[Pump].model_validate({"val": document.sections[0]})
        structure = wrapper.val

        assert structure.id == "pump_id"
        assert structure.name == "pump_nm"
        assert structure.branchid == "branch"
        assert structure.chainage == pytest.approx(3.0)
        assert structure.type == "pump"
        assert structure.orientation == Orientation.positive
        assert structure.capacity == pytest.approx(10.5)

    @pytest.mark.parametrize(
        "input,expected",
        _get_orientation_cases(),
    )
    def test_pump_parses_orientation_case_insensitive(self, input, expected):
        structure = Pump(
            **self._create_required_pump_values(),
            orientation=input,
        )

        assert structure.orientation == expected

    @pytest.mark.parametrize(
        "listname,lengthname",
        _pumplists,
    )
    def test_create_a_pump_with_wrong_list_lengths(
            self, listname: str, lengthname: str
    ):
        """Creates a pump with one start/stop/reduction attribute with wrong list length
        and checks for correct error detection."""
        correctlength = 3  # just a test value
        correctlist = list(range(correctlength))
        listargs = {key: correctlist for (key, _) in self._pumplists}
        listargs[listname] = list(
            range(correctlength + 1)
        )  # Intentional wrong list length
        listargs[lengthname] = correctlength
        listargs["controlside"] = "both"

        with pytest.raises(ValueError) as error:

            _ = Pump(
                **self._create_required_pump_values(),
                **listargs,
            )

        expected_message = f"Number of values for {listname} should be equal to the {lengthname} value."

        assert expected_message in str(error.value)

    @pytest.mark.parametrize(
        "control_side,missing_list_name,present_list_names,should_raise_error",
        [
            ("suctionSide", "startlevelsuctionside", [], True),
            (
                    "deliverySide",
                    "startlevelsuctionside",
                    ["startleveldeliveryside", "stopleveldeliveryside"],
                    False,
            ),
            ("both", "startlevelsuctionside", [], True),
            ("suctionSide", "stoplevelsuctionside", [], True),
            (
                    "deliverySide",
                    "stoplevelsuctionside",
                    ["startleveldeliveryside", "stopleveldeliveryside"],
                    False,
            ),
            ("both", "stoplevelsuctionside", [], True),
            (
                    "suctionSide",
                    "startleveldeliveryside",
                    ["startlevelsuctionside", "stoplevelsuctionside"],
                    False,
            ),
            ("deliverySide", "startleveldeliveryside", [], True),
            ("both", "startleveldeliveryside", [], True),
            (
                    "suctionSide",
                    "stopleveldeliveryside",
                    ["startlevelsuctionside", "stoplevelsuctionside"],
                    False,
            ),
            ("deliverySide", "stopleveldeliveryside", [], True),
            ("both", "stopleveldeliveryside", [], True),
        ],
    )
    def test_dont_validate_unneeded_pump_lists(
            self,
            control_side: str,
            missing_list_name: str,
            present_list_names: List[str],
            should_raise_error: bool,
    ):
        """Creates a pump with one particular list attribute missing
        and checks for correct (i.e., no unneeded) error detection,
        depending on the controlside attribute."""

        values = self._create_required_pump_values()
        values["id"] = "pump_controlside_" + (control_side or "none")

        if control_side is not None:
            values["controlside"] = control_side
        else:
            values.pop("controlside", None)

        values["numstages"] = 1
        values.pop(missing_list_name, None)
        values.update({ln: [1.1] for ln in present_list_names})

        if should_raise_error:
            with pytest.raises(ValueError):
                _ = Pump(**values)
        else:
            # Simply create the Pump and accept no Error raised.
            _ = Pump(**values)

    @pytest.mark.parametrize(
        "listname,lengthname",
        _pumplists,
    )
    def test_create_a_pump_with_missing_list(self, listname: str, lengthname: int):
        """Creates a pump with one start/stop/reduction attribute list missing
        and checks for correct error detection."""
        correctlength = 3  # just a test value
        correctlist = list(range(correctlength))
        listargs = {key: correctlist for (key, _) in self._pumplists}
        listargs.pop(listname)  # Remove one list argument
        for _, _lengthname in self._pumplists:
            listargs[_lengthname] = correctlength
        listargs["controlside"] = "both"

        with pytest.raises(ValueError) as error:

            _ = Pump(
                **self._create_required_pump_values(),
                **listargs,
            )

        expected_message = (
            f"List {listname} cannot be missing if {lengthname} is given."
        )

        assert expected_message in str(error.value)

    def _create_required_pump_values(self) -> dict:
        pump_values = dict(
            capacity="2.34",
        )

        pump_values.update(create_structure_values("pump"))
        return pump_values

    def _create_pump_values(self) -> dict:
        pump_values = dict(
            orientation="negative",
            numreductionlevels=2,
            head=[0, 2],
            reductionfactor=[0, 0.1],
        )

        pump_values.update(self._create_required_pump_values())
        return pump_values