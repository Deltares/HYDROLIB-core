import inspect
from pathlib import Path
from typing import Dict, List, Literal

import pytest
from pydantic.error_wrappers import ValidationError

from hydrolib.core.io.dflowfm.bc.models import (
    T3D,
    Astronomic,
    AstronomicCorrection,
    Constant,
    ForcingBase,
    ForcingModel,
    Harmonic,
    HarmonicCorrection,
    QHTable,
    QuantityUnitPair,
    TimeInterpolation,
    TimeSeries,
    VectorForcingBase,
    VectorQuantityUnitPairs,
    VerticalInterpolation,
    VerticalPositionType,
)
from hydrolib.core.io.dflowfm.ini.models import BaseModel
from hydrolib.core.io.dflowfm.ini.parser import Parser, ParserConfig

from ...utils import (
    assert_files_equal,
    invalid_test_data_dir,
    test_data_dir,
    test_input_dir,
    test_output_dir,
    test_reference_dir,
)

TEST_BC_FILE = "test.bc"
TEST_BC_FILE_KEYWORDS_WITH_SPACES = "t3d_backwards_compatibility.bc"

TEST_TIME_UNIT = "minutes since 2015-01-01 00:00:00"

INCORRECT_NUMBER_QUP_IN_VECTOR_WITH_THREE_LAYERS_ERROR = (
    "Incorrect number of quantity unit pairs were found; "
    + "should match the elements in vectordefinition for uxuyadvectionvelocitybnd, "
    + "and 3 vertical layers."
)


class TestQuantityUnitPair:
    def test_create_quantityunitpair(self):
        pair = QuantityUnitPair(quantity="some_quantity", unit="some_unit")
        assert isinstance(pair, BaseModel)
        assert pair.quantity == "some_quantity"
        assert pair.unit == "some_unit"
        assert pair.vertpositionindex is None

    def test_create_quantityunitpair_with_verticalpositionindex(self):
        pair = QuantityUnitPair(
            quantity="some_quantity", unit="some_unit", vertpositionindex=123
        )
        assert isinstance(pair, BaseModel)
        assert pair.quantity == "some_quantity"
        assert pair.unit == "some_unit"
        assert pair.vertpositionindex == 123


class TestTimeSeries:
    def test_create_a_forcing_from_scratch(self):
        forcing = TimeSeries(**_create_time_series_values())

        assert isinstance(forcing, TimeSeries)
        assert isinstance(forcing, VectorForcingBase)
        assert forcing.name == "boundary_timeseries"
        assert forcing.offset == 1.23
        assert forcing.factor == 2.34
        assert forcing.timeinterpolation == TimeInterpolation.block_to
        assert len(forcing.quantityunitpair) == 2
        assert forcing.quantityunitpair[0].quantity == "time"
        assert forcing.quantityunitpair[0].unit == TEST_TIME_UNIT
        assert forcing.quantityunitpair[1].quantity == "dischargebnd"
        assert forcing.quantityunitpair[1].unit == "m³/s"
        assert len(forcing.datablock) == 3
        assert forcing.datablock[0] == [0, 1.23]
        assert forcing.datablock[1] == [60, 2.34]
        assert forcing.datablock[2] == [120, 3.45]

    def test_read_bc_expected_result(self):
        input_str = inspect.cleandoc(
            """
            [Forcing]
                name              = right01_0001
                function          = timeseries  # what about casing?
                timeInterpolation = linear
                quantity          = time
                unit              = minutes since 2001-01-01
                quantity          = waterlevelbnd
                unit              = m
                   0.000000 2.50
                1440.000000 2.50
            """
        )

        parser = Parser(ParserConfig(parse_comments=True, parse_datablocks=True))

        for line in input_str.splitlines():
            parser.feed_line(line)

        document = parser.finalize()
        sec = document.sections[0].flatten()
        forcing = TimeSeries.parse_obj(sec)

        assert forcing.name == "right01_0001"
        assert forcing.function == "timeseries"
        assert isinstance(forcing, TimeSeries)
        assert forcing.quantityunitpair[0].quantity == "time"
        assert forcing.quantityunitpair[0].unit == "minutes since 2001-01-01"
        assert forcing.datablock[0] == [0.0, 2.5]
        assert forcing.quantityunitpair[1].quantity == "waterlevelbnd"
        assert forcing.quantityunitpair[1].unit == "m"
        assert forcing.datablock[1] == [1440.0, 2.5]

    def test_load_timeseries_model_with_old_keyword_that_contain_spaces(self):
        bc_file = Path(test_reference_dir / "bc" / TEST_BC_FILE_KEYWORDS_WITH_SPACES)
        forcingmodel = ForcingModel(bc_file)

        timeseries = next(
            (x for x in forcingmodel.forcing if x.function == "timeseries"), None
        )
        assert timeseries is not None
        assert timeseries.name == "boundary_timeseries"
        assert timeseries.timeinterpolation == TimeInterpolation.block_to
        assert timeseries.offset == 1.23
        assert timeseries.factor == 2.34

        quantityunitpairs = timeseries.quantityunitpair
        assert len(quantityunitpairs) == 2
        assert quantityunitpairs[0].quantity == "time"
        assert quantityunitpairs[0].unit == TEST_TIME_UNIT
        assert quantityunitpairs[1].quantity == "dischargebnd"

        assert timeseries.datablock == [
            [0.0, 1.23],
            [60.0, 2.34],
            [120.0, 3.45],
        ]

    def test_initialize_timeseries_with_vectorvalues(self):
        values = _create_time_series_vectorvalues()

        ts = TimeSeries(**values)

        assert ts.name == values["name"]

        assert len(ts.quantityunitpair) == 2
        assert ts.quantityunitpair[0] == values["quantityunitpair"][0]
        assert isinstance(ts.quantityunitpair[1], VectorQuantityUnitPairs)
        assert ts.quantityunitpair[1].vectorname == "uxuyadvectionvelocitybnd"
        assert ts.quantityunitpair[1].elementname == ["ux", "uy"]
        assert len(ts.quantityunitpair[1].quantityunitpair) == 2
        assert ts.quantityunitpair[1].quantityunitpair[0] == QuantityUnitPair(
            quantity="ux", unit="m s-1", vertpositionindex=None
        )
        assert ts.quantityunitpair[1].quantityunitpair[1] == QuantityUnitPair(
            quantity="uy", unit="m s-1", vertpositionindex=None
        )
        assert len(ts.datablock) == 3
        assert ts.datablock == [list(map(float, row)) for row in values["datablock"]]

    def test_initialize_timeseries_with_wrong_amount_vectorquantities(
        self,
    ):
        values = _create_time_series_vectorvalues()
        del values["quantityunitpair"][1].quantityunitpair[1]

        with pytest.raises(ValueError) as error:
            TimeSeries(**values)

        expected_error_mssg = (
            "Incorrect number of quantity unit pairs were found; "
            + "should match the elements in vectordefinition for uxuyadvectionvelocitybnd."
        )

        assert expected_error_mssg in str(error.value)


class TestForcingBase:
    @pytest.mark.parametrize(
        "input,expected",
        [
            ("TimeSeries", "timeseries"),
            ("haRmoniC", "harmonic"),
            ("ASTRONOMIC", "astronomic"),
            ("harmonic-Correction", "harmonic-correction"),
            ("Astronomic-Correction", "astronomic-correction"),
            ("t3D", "t3d"),
            ("QHtable", "qhtable"),
            ("Constant", "constant"),
            ("DOESNOTEXIST", "DOESNOTEXIST"),
            ("doesnotexist", "doesnotexist"),
        ],
    )
    def test_parses_function_case_insensitive(self, input, expected):
        forcing = ForcingBase(function=input, name="somename", quantityunitpair=[])

        assert forcing.function == expected

    @pytest.mark.parametrize(
        "missing_field",
        [
            "quantity",
            "unit",
        ],
    )
    def test_create_forcingbase_missing_field_raises_correct_error(
        self, missing_field: str
    ):
        values = dict(
            name="Boundary2",
            function="constant",
            quantity="dischargebnd",
            unit="m³/s",
            datablock=[["100"]],
        )

        del values[missing_field]

        with pytest.raises(ValidationError) as error:
            ForcingBase(**values)

        expected_message = f"{missing_field} is not provided"
        assert expected_message in str(error.value)

    @pytest.mark.parametrize(
        "quantities,units",
        [
            (["time", "dischargebnd"], "m³/s"),
            (
                ["time", "dischargebnd", "extra"],
                ["minutes since 2021-01-01 00:00:00", "m³/s"],
            ),
        ],
    )
    def test_create_forcingbase_mismatch_number_of_quantities_units_raises_correct_error(
        self, quantities, units
    ):
        values = dict(
            name="Boundary2",
            function="constant",
            quantity=quantities,
            unit=units,
            datablock=[["100"]],
        )

        with pytest.raises(ValidationError) as error:
            ForcingBase(**values)

        expected_message = "Number of quantities should be equal to number of units"
        assert expected_message in str(error.value)


class TestForcingModel:
    """
    Wrapper class to test the logic of the ForcingModel class in hydrolib.core.io.dflowfm.bc.models.py.
    """

    def test_forcing_model(self):
        filepath = (
            test_data_dir
            / "input/e02/f101_1D-boundaries/c01_steady-state-flow/BoundaryConditions.bc"
        )
        m = ForcingModel(filepath)
        assert len(m.forcing) == 13
        assert isinstance(m.forcing[-1], TimeSeries)

    def test_read_bc_missing_field_raises_correct_error(self):
        bc_file = "missing_field.bc"
        identifier = "Boundary2"

        filepath = invalid_test_data_dir / bc_file

        with pytest.raises(ValidationError) as error:
            ForcingModel(filepath)

        expected_message1 = f"{bc_file} -> forcing -> 1 -> {identifier}"
        expected_message2 = "quantity is not provided"
        assert expected_message1 in str(error.value)
        assert expected_message2 in str(error.value)

    def test_save_forcing_model(self):
        bc_file = Path(test_output_dir / TEST_BC_FILE)
        reference_file = Path(test_reference_dir / "bc" / TEST_BC_FILE)
        forcingmodel = ForcingModel()
        forcingmodel.filepath = bc_file

        timeseries = TimeSeries(**_create_time_series_values())
        harmonic = Harmonic(**_create_harmonic_values(False))
        harmoniccorrection = HarmonicCorrection(**_create_harmonic_values(True))
        t3d = T3D(**_create_t3d_values())
        qhtable = QHTable(**_create_qhtable_values())
        constant = Constant(**_create_constant_values())

        forcingmodel.forcing.append(timeseries)
        forcingmodel.forcing.append(harmonic)
        forcingmodel.forcing.append(harmoniccorrection)
        forcingmodel.forcing.append(t3d)
        forcingmodel.forcing.append(qhtable)
        forcingmodel.forcing.append(constant)
        forcingmodel.save()

        assert bc_file.is_file() == True
        assert_files_equal(bc_file, reference_file, skip_lines=[0, 3])

    @pytest.mark.parametrize("cls", [Astronomic, AstronomicCorrection])
    def test_astronomic_values_with_strings_in_datablock_are_parsed_correctly(
        self, cls
    ):
        try:
            is_correction = cls == AstronomicCorrection
            _ = cls(**_create_astronomic_values(is_correction))
        except ValidationError:
            pytest.fail(
                f"No validation error should be raised when creating an {cls.__name__}"
            )

    def test_representation_is_correct(self):
        forcing = ForcingBase(
            name="some_name",
            function="some_function",
            quantityunitpair=[
                QuantityUnitPair(quantity="some_quantity", unit="some_unit")
            ],
            datablock=[[1.2, 2.3]],
        )

        str_representation_as_single = str(forcing)
        str_representation_in_list = str([forcing])

        # datablock should be omitted when a `ForcingBase` is represented from within a list
        expected_result = "comments=Comments() datablock={0} name='some_name' function='some_function' quantityunitpair=[QuantityUnitPair(quantity='some_quantity', unit='some_unit', vertpositionindex=None)]"
        assert str_representation_as_single == expected_result.format("[[1.2, 2.3]]")
        assert str_representation_in_list == "[{0}]".format(
            expected_result.format("'<omitted>'")
        )


class TestVectorForcingBase:
    class VectorForcingTest(VectorForcingBase):
        function: Literal["testfunction"] = "testfunction"

        @classmethod
        def get_number_of_repetitions(cls, values: Dict):
            return 2

    incorrect_number_of_qups_error = (
        "Incorrect number of quantity unit pairs were found; should match the elements"
        + " in vectordefinition for uxuyadvectionvelocitybnd, and 2 vertical layers."
    )

    def test_valid_vectorquantityunitpair_does_not_throw(self):
        values = _create_valid_vectorforcingtest_values()

        vector_forcing = TestVectorForcingBase.VectorForcingTest(**values)

        assert len(vector_forcing.quantityunitpair) == 2

        vectorquantityunitpairs = vector_forcing.quantityunitpair[1]
        assert vectorquantityunitpairs.elementname == ["ux", "uy"]
        assert vectorquantityunitpairs.vectorname == "uxuyadvectionvelocitybnd"
        assert len(vectorquantityunitpairs.quantityunitpair) == 4

    def test_too_few_quantityunitpairs_raises_error(self):
        values = _create_valid_vectorforcingtest_values()

        values["quantityunitpair"][1].quantityunitpair.pop(0)

        with pytest.raises(ValidationError) as error:
            TestVectorForcingBase.VectorForcingTest(**values)

        assert TestVectorForcingBase.incorrect_number_of_qups_error in str(error.value)

    def test_too_many_quantityunitpairs_raises_error(self):
        values = _create_valid_vectorforcingtest_values()

        qup = _create_quantityunitpair("ux", "randomUnit", 3)
        values["quantityunitpair"][1].quantityunitpair.append(qup)

        with pytest.raises(ValidationError) as error:
            TestVectorForcingBase.VectorForcingTest(**values)

        assert TestVectorForcingBase.incorrect_number_of_qups_error in str(error.value)

    def test_too_few_quanityunitpairs_with_vector_raises_error(self):
        values = _create_valid_vectorforcingtest_values_that_still_have_to_be_parsed()

        values["quantity"].pop(0)
        values["unit"].pop(0)

        with pytest.raises(ValidationError) as error:
            TestVectorForcingBase.VectorForcingTest(**values)

        assert TestVectorForcingBase.incorrect_number_of_qups_error in str(error.value)

    def test_multiple_vectors_are_parsed_correctly(self):
        values = (
            _create_valid_vectorforcingtest_values_with_multiple_vectors_that_still_have_to_be_parsed()
        )

        vector_forcing = TestVectorForcingBase.VectorForcingTest(**values)

        first_vector_qup = vector_forcing.quantityunitpair[0]
        assert len(first_vector_qup.quantityunitpair) == 4
        assert first_vector_qup.elementname == ["ux", "uy"]
        assert first_vector_qup.vectorname == "uxuyadvectionvelocitybnd"
        assert first_vector_qup.quantityunitpair[0].quantity == "ux"
        assert first_vector_qup.quantityunitpair[0].unit == "m s-1"
        assert first_vector_qup.quantityunitpair[1].quantity == "ux"
        assert first_vector_qup.quantityunitpair[1].unit == "m s-1"
        assert first_vector_qup.quantityunitpair[2].quantity == "uy"
        assert first_vector_qup.quantityunitpair[2].unit == "m s-1"
        assert first_vector_qup.quantityunitpair[3].quantity == "uy"
        assert first_vector_qup.quantityunitpair[3].unit == "m s-1"

        second_vector_qup = vector_forcing.quantityunitpair[1]
        assert len(second_vector_qup.quantityunitpair) == 4
        assert second_vector_qup.elementname == ["salinity", "waterlevelbnd"]
        assert second_vector_qup.vectorname == "randomvector"
        assert second_vector_qup.quantityunitpair[0].quantity == "salinity"
        assert second_vector_qup.quantityunitpair[0].unit == "ppt"
        assert second_vector_qup.quantityunitpair[1].quantity == "salinity"
        assert second_vector_qup.quantityunitpair[1].unit == "ppt"
        assert second_vector_qup.quantityunitpair[2].quantity == "waterlevelbnd"
        assert second_vector_qup.quantityunitpair[2].unit == "m"
        assert second_vector_qup.quantityunitpair[3].quantity == "waterlevelbnd"
        assert second_vector_qup.quantityunitpair[3].unit == "m"

    @pytest.mark.parametrize(
        "bc_file_name",
        [
            "FlowFM_boundaryconditions2d_and_vectors.bc",
            "FlowFM_boundaryconditions3d_and_vectors.bc",
        ],
    )
    def test_load_and_save_model_with_vector_quantities(self, bc_file_name: str):
        bc_file = test_input_dir / "dflowfm_individual_files" / bc_file_name
        output_file = test_output_dir / "fm" / ("serialize_" + bc_file_name)
        reference_file = test_reference_dir / "bc" / bc_file_name

        forcingmodel = ForcingModel(bc_file)

        forcingmodel.filepath = output_file
        forcingmodel.save()

        assert_files_equal(output_file, reference_file, [0])

    def test_unexpected_quantityunitpair_raises_error(self):
        values = _create_valid_vectorforcingtest_values()
        values["quantityunitpair"][1].quantityunitpair[
            0
        ].quantity = "unit_not_part_of_vector"

        with pytest.raises(ValidationError) as error:
            TestVectorForcingBase.VectorForcingTest(**values)

        expected_message = "Invalid quantity `unit_not_part_of_vector` found in vector `uxuyadvectionvelocitybnd`."
        assert expected_message in str(error.value)


class TestT3D:
    @pytest.mark.parametrize(
        "vertical_position_type, exp_vertical_position_type",
        [
            ("percBed", VerticalPositionType.percentage_bed),
            ("percentage from bed", VerticalPositionType.percentage_bed),
            ("ZBed", VerticalPositionType.z_bed),
            ("ZDatum", VerticalPositionType.z_datum),
            ("ZSurf", VerticalPositionType.z_surf),
        ],
    )
    def test_initialize_t3d(
        self,
        vertical_position_type: str,
        exp_vertical_position_type: VerticalPositionType,
    ):
        values = _create_t3d_values()
        values["vertpositiontype"] = vertical_position_type

        t3d = T3D(**values)

        assert isinstance(t3d, VectorForcingBase)
        assert t3d.name == "boundary_t3d"
        assert t3d.function == "t3d"
        assert t3d.offset == 1.23
        assert t3d.factor == 2.34
        assert t3d.timeinterpolation == TimeInterpolation.linear

        assert len(t3d.vertpositions) == 3
        assert t3d.vertpositions[0] == 3.45
        assert t3d.vertpositions[1] == 4.56
        assert t3d.vertpositions[2] == 5.67

        assert t3d.vertinterpolation == VerticalInterpolation.log
        assert t3d.vertpositiontype == exp_vertical_position_type

        assert len(t3d.quantityunitpair) == 4
        assert t3d.quantityunitpair[0] == QuantityUnitPair(
            quantity="time", unit=TEST_TIME_UNIT
        )
        assert t3d.quantityunitpair[1] == QuantityUnitPair(
            quantity="salinitybnd", unit="ppt", vertpositionindex=1
        )
        assert t3d.quantityunitpair[2] == QuantityUnitPair(
            quantity="salinitybnd", unit="ppt", vertpositionindex=2
        )
        assert t3d.quantityunitpair[3] == QuantityUnitPair(
            quantity="salinitybnd", unit="ppt", vertpositionindex=3
        )

        assert len(t3d.datablock) == 3
        assert t3d.datablock[0] == [0, 1, 2, 3]
        assert t3d.datablock[1] == [60, 4, 5, 6]
        assert t3d.datablock[2] == [120, 7, 8, 9]

    def test_create_t3d_first_quantity_not_time_raises_error(self):
        values = _create_t3d_values()

        values["quantityunitpair"] = [
            _create_quantityunitpair("salinitybnd", "ppt"),
            _create_quantityunitpair("time", TEST_TIME_UNIT),
        ]

        with pytest.raises(ValidationError) as error:
            T3D(**values)

        expected_message = "First quantity should be `time`"
        assert expected_message in str(error.value)

    def test_create_t3d_time_quantity_with_verticalpositionindex_raises_error(self):
        values = _create_t3d_values()

        values["quantityunitpair"] = [
            _create_quantityunitpair("time", TEST_TIME_UNIT, 1),
        ]

        with pytest.raises(ValidationError) as error:
            T3D(**values)

        expected_message = "`time` quantity cannot have vertical position index"
        assert expected_message in str(error.value)

    def test_create_t3d_verticalpositionindex_missing_for_non_time_unit_raises_error(
        self,
    ):
        values = _create_t3d_values()

        values["quantityunitpair"] = [
            _create_quantityunitpair("time", TEST_TIME_UNIT),
            _create_quantityunitpair("salinitybnd", "ppt", None),
        ]

        with pytest.raises(ValidationError) as error:
            T3D(**values)

        expected_maximum_index = len(values["vertpositions"].split())
        expected_message = (
            f"Vertical position index should be between 1 and {expected_maximum_index}"
        )
        assert expected_message in str(error.value)

    @pytest.mark.parametrize(
        "vertpositions, verticalpositionindexes",
        [
            pytest.param([1.23, 4.56], [0, 1], id="vertpositionindex is one-based"),
            pytest.param(
                [1.23, 4.56],
                [1, 3],
                id="vertpositionindex bigger than vertpositions length",
            ),
            pytest.param([1.23, 4.56], [1, None], id="too few vertpositionindex"),
            pytest.param([1.23, 4.56], [1, 2, 3], id="too many vertpositionindex"),
        ],
    )
    def test_create_t3d_verticalposition_in_quantityunitpair_has_invalid_value_raises_error(
        self,
        vertpositions: List[float],
        verticalpositionindexes: List[int],
    ):
        values = _create_t3d_values()

        time_quantityunitpair = [_create_quantityunitpair("time", TEST_TIME_UNIT)]
        other_quantutyunitpairs = []
        for i in range(len(verticalpositionindexes)):
            other_quantutyunitpairs.append(
                _create_quantityunitpair(
                    "randomQuantity", "randomUnit", verticalpositionindexes[i]
                )
            )

        values["quantityunitpair"] = time_quantityunitpair + other_quantutyunitpairs
        values["vertpositions"] = vertpositions

        with pytest.raises(ValidationError) as error:
            T3D(**values)

        maximum_verticalpositionindex = len(vertpositions)
        expected_message = f"Vertical position index should be between 1 and {maximum_verticalpositionindex}"
        assert expected_message in str(error.value)

    @pytest.mark.parametrize(
        "number_of_quantities_and_units, number_of_verticalpositionindexes",
        [
            pytest.param(4, 2, id="4 quantities, but 2 verticalpositionindexes"),
            pytest.param(2, 3, id="2 quantities, but 3 verticalpositionindexes"),
        ],
    )
    def test_create_t3d_number_of_verticalindexpositions_not_as_expected_raises_error(
        self,
        number_of_quantities_and_units: int,
        number_of_verticalpositionindexes: int,
    ):
        values = _create_t3d_values()

        del values["quantityunitpair"]

        onebased_index_offset = 1

        values["quantity"] = ["time"] + [
            str(i + onebased_index_offset)
            for i in range(number_of_quantities_and_units)
        ]
        values["unit"] = [TEST_TIME_UNIT] + [
            str(i + onebased_index_offset)
            for i in range(number_of_quantities_and_units)
        ]
        values["vertpositionindex"] = [
            str(i + onebased_index_offset)
            for i in range(number_of_verticalpositionindexes)
        ]

        with pytest.raises(ValidationError) as error:
            T3D(**values)

        expected_message = "Number of vertical position indexes should be equal to the number of quantities/units - 1"
        assert expected_message in str(error.value)

    @pytest.mark.parametrize(
        "verticalpositionindexes",
        [
            pytest.param([0], id="vertpositionindex is one-based"),
            pytest.param([None], id="vertpositionindex cannot be None"),
            pytest.param(
                [4],
                id="vertpositionindex cannot be larger than number of vertical positions",
            ),
        ],
    )
    def test_create_t3d_verticalpositionindex_has_invalid_value_raises_error(
        self, verticalpositionindexes: List[int]
    ):
        values = _create_t3d_values()

        del values["quantityunitpair"]

        values["quantity"] = ["time", "randomQuantity"]
        values["unit"] = ["randomUnit", "randomUnit"]
        values["vertpositionindex"] = verticalpositionindexes

        with pytest.raises(ValidationError) as error:
            T3D(**values)

        number_of_vertical_positions = len(values["vertpositions"].split())
        expected_message = f"Vertical position index should be between 1 and {number_of_vertical_positions}"
        assert expected_message in str(error.value)

    def test_create_t3d_creates_correct_quantityunitpairs(self):
        values = _create_t3d_values()

        t3d = T3D(**values)

        quantityunitpairs = t3d.quantityunitpair
        expected_quantityunitpairs = values["quantityunitpair"]

        TestT3D._validate_that_correct_quantityunitpairs_are_created(
            quantityunitpairs, expected_quantityunitpairs
        )

    def test_create_t3d_creates_correct_quantityunitpairs_using_verticalpositionindexes(
        self,
    ):
        values = _create_t3d_values()

        del values["quantityunitpair"]

        values["quantity"] = ["time", "randomQuantity1", "randomQuantity2"]
        values["unit"] = ["randomUnit", "randomUnit", "randomUnit"]
        values["vertpositionindex"] = [2, 3]

        t3d = T3D(**values)

        quantityunitpairs = t3d.quantityunitpair
        expected_quantityunitpairs = []

        for quantity, unit, verticalpositionindex in zip(
            values["quantity"], values["unit"], [None] + values["vertpositionindex"]
        ):
            expected_quantityunitpairs.append(
                _create_quantityunitpair(quantity, unit, verticalpositionindex)
            )

        TestT3D._validate_that_correct_quantityunitpairs_are_created(
            quantityunitpairs, expected_quantityunitpairs
        )

    def test_create_t3d_timeinterpolation_defaults_to_linear(self):
        values = _create_t3d_values()

        del values["timeinterpolation"]

        t3d = T3D(**values)

        assert t3d.timeinterpolation == TimeInterpolation.linear

    def test_create_t3d_verticalinterpolation_defaults_to_linear(self):
        values = _create_t3d_values()

        del values["vertinterpolation"]

        t3d = T3D(**values)

        assert t3d.vertinterpolation == VerticalInterpolation.linear

    def test_create_t3d_without_specifying_vertpositions_raises_error(self):
        values = _create_t3d_values()

        del values["vertpositions"]

        with pytest.raises(ValidationError) as error:
            T3D(**values)

        expected_message = "vertPositions is not provided"
        assert expected_message in str(error.value)

    def test_initialize_t3d_with_vectorquantities(
        self,
    ):
        values = _create_t3d_vectorvalues()

        t3d = T3D(**values)

        assert t3d.name == "boundary_t3d"

        assert len(t3d.quantityunitpair) == 2
        assert t3d.quantityunitpair[0] == QuantityUnitPair(
            quantity="time", unit=TEST_TIME_UNIT
        )
        assert isinstance(t3d.quantityunitpair[1], VectorQuantityUnitPairs)
        assert t3d.quantityunitpair[1].vectorname == "uxuyadvectionvelocitybnd"
        assert t3d.quantityunitpair[1].elementname == ["ux", "uy"]
        assert t3d.quantityunitpair[1].quantityunitpair[0] == QuantityUnitPair(
            quantity="ux", unit="m s-1", vertpositionindex=1
        )
        assert t3d.quantityunitpair[1].quantityunitpair[1] == QuantityUnitPair(
            quantity="uy", unit="m s-1", vertpositionindex=1
        )
        assert t3d.quantityunitpair[1].quantityunitpair[4] == QuantityUnitPair(
            quantity="ux", unit="m s-1", vertpositionindex=3
        )

        assert len(t3d.datablock) == 3
        assert t3d.datablock[0] == [0, 1, 2, 3, 10, 20, 30]
        assert t3d.datablock[1] == [60, 4, 5, 6, 40, 50, 60]
        assert t3d.datablock[2] == [120, 7, 8, 9, 70, 80, 90]

    def test_initialize_t3d_with_wrong_amount_vectorquantities_but_multiple_of_number_of_elements_in_vector(
        self,
    ):
        values = _create_t3d_vectorvalues()

        # We have a vector with 2 elements and 6 quantityunitpairs.
        # If we delete 2 pairs, we still have a multiple of the number of elements,
        # so it should pass the vectorbase validation.
        # But we no longer have the expected number of pairs, so it should fail the T3D validation.
        del values["quantityunitpair"][1].quantityunitpair[5]
        del values["quantityunitpair"][1].quantityunitpair[4]

        with pytest.raises(ValueError) as error:
            T3D(**values)

        assert INCORRECT_NUMBER_QUP_IN_VECTOR_WITH_THREE_LAYERS_ERROR in str(
            error.value
        )

    def test_initialize_t3d_with_wrong_amount_vectorquantities(
        self,
    ):
        values = _create_t3d_vectorvalues()
        del values["quantityunitpair"][1].quantityunitpair[3]

        with pytest.raises(ValueError) as error:
            T3D(**values)

        assert INCORRECT_NUMBER_QUP_IN_VECTOR_WITH_THREE_LAYERS_ERROR in str(
            error.value
        )

    def test_load_forcing_model(self):
        bc_file = Path(test_reference_dir / "bc" / TEST_BC_FILE)
        forcingmodel = ForcingModel(bc_file)

        t3d = next((x for x in forcingmodel.forcing if x.function == "t3d"), None)
        assert t3d is not None
        assert t3d.name == "boundary_t3d"
        assert t3d.offset == 1.23
        assert t3d.factor == 2.34
        assert t3d.vertpositions == [3.45, 4.56, 5.67]
        assert t3d.vertinterpolation == VerticalInterpolation.log
        assert t3d.vertpositiontype == VerticalPositionType.percentage_bed
        assert t3d.timeinterpolation == TimeInterpolation.linear

        quantityunitpairs = t3d.quantityunitpair
        assert len(quantityunitpairs) == 4
        assert quantityunitpairs[0].quantity == "time"
        assert quantityunitpairs[0].unit == TEST_TIME_UNIT
        assert quantityunitpairs[0].vertpositionindex == None
        assert quantityunitpairs[1].quantity == "salinitybnd"
        assert quantityunitpairs[1].unit == "ppt"
        assert quantityunitpairs[1].vertpositionindex == 1
        assert quantityunitpairs[2].quantity == "salinitybnd"
        assert quantityunitpairs[2].unit == "ppt"
        assert quantityunitpairs[2].vertpositionindex == 2
        assert quantityunitpairs[3].quantity == "salinitybnd"
        assert quantityunitpairs[3].unit == "ppt"
        assert quantityunitpairs[3].vertpositionindex == 3

        assert t3d.datablock == [
            [0.0, 1.0, 2.0, 3.0],
            [60.0, 4.0, 5.0, 6.0],
            [120.0, 7.0, 8.0, 9.0],
        ]

    def test_load_t3d_model_with_old_keyword_that_contains_spaces(self):
        bc_file = Path(test_reference_dir / "bc" / TEST_BC_FILE_KEYWORDS_WITH_SPACES)
        forcingmodel = ForcingModel(bc_file)

        t3d = next((x for x in forcingmodel.forcing if x.function == "t3d"), None)
        assert t3d is not None
        assert t3d.name == "boundary_t3d"
        assert t3d.offset == 1.23
        assert t3d.factor == 2.34
        assert t3d.vertpositions == [3.45, 4.56, 5.67]
        assert t3d.vertinterpolation == VerticalInterpolation.log
        assert t3d.vertpositiontype == VerticalPositionType.percentage_bed
        assert t3d.timeinterpolation == TimeInterpolation.linear

        quantityunitpairs = t3d.quantityunitpair
        assert len(quantityunitpairs) == 4
        assert quantityunitpairs[0].quantity == "time"
        assert quantityunitpairs[0].unit == TEST_TIME_UNIT
        assert quantityunitpairs[0].vertpositionindex == None
        assert quantityunitpairs[1].quantity == "salinitybnd"
        assert quantityunitpairs[1].unit == "ppt"
        assert quantityunitpairs[1].vertpositionindex == 1
        assert quantityunitpairs[2].quantity == "salinitybnd"
        assert quantityunitpairs[2].unit == "ppt"
        assert quantityunitpairs[2].vertpositionindex == 2
        assert quantityunitpairs[3].quantity == "salinitybnd"
        assert quantityunitpairs[3].unit == "ppt"
        assert quantityunitpairs[3].vertpositionindex == 3

        assert t3d.datablock == [
            [0.0, 1.0, 2.0, 3.0],
            [60.0, 4.0, 5.0, 6.0],
            [120.0, 7.0, 8.0, 9.0],
        ]

    @staticmethod
    def _validate_that_correct_quantityunitpairs_are_created(
        quantityunitpairs: List[QuantityUnitPair],
        expected_quantityunitpairs: List[QuantityUnitPair],
    ):
        assert len(quantityunitpairs) == len(expected_quantityunitpairs)

        for quantityunitpair, expected_quantityunitpair in zip(
            quantityunitpairs, expected_quantityunitpairs
        ):
            assert quantityunitpair.quantity == expected_quantityunitpair.quantity
            assert quantityunitpair.unit == expected_quantityunitpair.unit
            assert (
                quantityunitpair.vertpositionindex
                == expected_quantityunitpair.vertpositionindex
            )

    def test_load_t3d_model_with_vector_quantities(self):
        bc_file = (
            test_input_dir
            / "dflowfm_individual_files"
            / "FlowFM_boundaryconditions3d_and_vectors.bc"
        )
        forcingmodel = ForcingModel(bc_file)

        t3d = next((x for x in forcingmodel.forcing if x.function == "t3d"), None)
        assert isinstance(t3d, T3D)
        assert t3d is not None
        assert t3d.name == "zuiduxuy_0002"
        assert t3d.vertpositions == [0, 0.2, 1.0]
        assert t3d.vertinterpolation == VerticalInterpolation.linear
        assert t3d.vertpositiontype == VerticalPositionType.percentage_bed
        assert t3d.timeinterpolation == TimeInterpolation.linear

        quantityunitpairs = t3d.quantityunitpair
        assert len(quantityunitpairs) == 2
        assert quantityunitpairs[0].quantity == "time"
        assert quantityunitpairs[0].unit == "MINUTES SINCE 1992-08-31 00:00:00 +00:00"
        assert quantityunitpairs[0].vertpositionindex == None

        assert isinstance(quantityunitpairs[1], VectorQuantityUnitPairs)
        assert quantityunitpairs[1].vectorname == "uxuyadvectionvelocitybnd"
        assert quantityunitpairs[1].elementname == ["ux", "uy"]
        assert quantityunitpairs[1].quantityunitpair[0].vertpositionindex == 1
        assert quantityunitpairs[1].quantityunitpair[0].quantity == "ux"
        assert quantityunitpairs[1].quantityunitpair[0].unit == "-"
        assert quantityunitpairs[1].quantityunitpair[1].vertpositionindex == 1
        assert quantityunitpairs[1].quantityunitpair[1].quantity == "uy"
        assert quantityunitpairs[1].quantityunitpair[1].unit == "-"
        assert quantityunitpairs[1].quantityunitpair[4].vertpositionindex == 3
        assert quantityunitpairs[1].quantityunitpair[4].quantity == "ux"
        assert quantityunitpairs[1].quantityunitpair[4].unit == "-"


class TestVectorQuantityUnitPairs:
    def test_initialize_vectorqup_with_wrongly_named_vectorquantities(
        self,
    ):
        numlayers = 3
        values = _create_vectorvalues(numlayers)
        vQUP = VectorQuantityUnitPairs(**values)
        assert len(vQUP.quantityunitpair) == numlayers * 2

        with pytest.raises(ValueError) as error:
            # Now re-assign these qups such that last element has a wrong quantity name:
            vQUP.quantityunitpair = vQUP.quantityunitpair[:-1] + [
                _create_quantityunitpair(
                    quantity="wrongname", unit="-", verticalpositionindex=numlayers
                )
            ]
        expected_error_mssg = f"quantityunitpair[{2*numlayers-1}], quantity 'wrongname' must be in vectordefinition's element names: 'uxuyadvectionvelocitybnd:ux,uy'."
        assert expected_error_mssg in str(error.value)


def _create_quantityunitpair(quantity, unit, verticalpositionindex=None):
    return QuantityUnitPair(
        quantity=quantity, unit=unit, vertpositionindex=verticalpositionindex
    )


def _create_vectorqup(
    vectorname: str, elementname: List[str], quantityunitpair: List[QuantityUnitPair]
):
    return VectorQuantityUnitPairs(
        vectorname=vectorname,
        elementname=elementname,
        quantityunitpair=quantityunitpair,
    )


def _create_time_series_values():
    return dict(
        name="boundary_timeseries",
        function="timeseries",
        timeinterpolation=TimeInterpolation.block_to,
        offset="1.23",
        factor="2.34",
        quantityunitpair=[
            _create_quantityunitpair("time", TEST_TIME_UNIT),
            _create_quantityunitpair("dischargebnd", "m³/s"),
        ],
        datablock=[["0", "1.23"], ["60", "2.34"], ["120", "3.45"]],
    )


def _create_harmonic_values(iscorrection: bool):
    function = "harmonic-correction" if iscorrection else "harmonic"
    return dict(
        name=f"boundary_{function}",
        function=function,
        quantityunitpair=[
            _create_quantityunitpair("harmonic component", "minutes"),
            _create_quantityunitpair("waterlevelbnd amplitude", "m"),
            _create_quantityunitpair("waterlevelbnd phase", "deg"),
        ],
        datablock=[
            ["0", "1.23", "2.34"],
            ["60", "3.45", "4.56"],
        ],
    )


def _create_astronomic_values(iscorrection: bool):
    function = "astronomic-correction" if iscorrection else "astronomic"
    return dict(
        name=f"boundary_{function}",
        function=function,
        quantityunitpair=[
            _create_quantityunitpair("astronomic component", "-"),
            _create_quantityunitpair("waterlevelbnd amplitude", "m"),
            _create_quantityunitpair("waterlevelbnd phase", "deg"),
        ],
        datablock=[
            ["A0", "1.23", "2.34"],
            ["M4", "3.45", "4.56"],
            ["N2", "5.67", "6.78"],
        ],
    )


def _create_t3d_values():
    return dict(
        name="boundary_t3d",
        function="t3d",
        offset="1.23",
        factor="2.34",
        vertpositions="3.45 4.56 5.67",
        vertinterpolation=VerticalInterpolation.log,
        vertpositiontype=VerticalPositionType.percentage_bed,
        timeinterpolation=TimeInterpolation.linear,
        quantityunitpair=[
            _create_quantityunitpair("time", TEST_TIME_UNIT),
            _create_quantityunitpair("salinitybnd", "ppt", 1),
            _create_quantityunitpair("salinitybnd", "ppt", 2),
            _create_quantityunitpair("salinitybnd", "ppt", 3),
        ],
        datablock=[
            ["0", "1", "2", "3"],
            ["60", "4", "5", "6"],
            ["120", "7", "8", "9"],
        ],
    )


def _create_vectorvalues(number_of_element_repetitions: int = None):
    element_names = ["ux", "uy"]
    layers = (
        range(1, number_of_element_repetitions + 1)
        if number_of_element_repetitions is not None
        else [None]
    )

    return dict(
        vectorname="uxuyadvectionvelocitybnd",
        elementname=element_names,
        quantityunitpair=[
            _create_quantityunitpair(elem, "m s-1", layer)
            for layer in layers
            for elem in element_names
        ],
    )


def _create_t3d_vectorvalues():
    return dict(
        name="boundary_t3d",
        function="t3d",
        offset="1.23",
        factor="2.34",
        vertpositions="3.45 4.56 5.67",
        vertinterpolation=VerticalInterpolation.log,
        vertpositiontype=VerticalPositionType.percentage_bed,
        timeinterpolation=TimeInterpolation.linear,
        quantityunitpair=[
            _create_quantityunitpair("time", TEST_TIME_UNIT),
            _create_vectorqup(**_create_vectorvalues(3)),
        ],
        datablock=[
            ["0", "1", "2", "3", "10", "20", "30"],
            ["60", "4", "5", "6", "40", "50", "60"],
            ["120", "7", "8", "9", "70", "80", "90"],
        ],
    )


def _create_time_series_vectorvalues():
    return dict(
        name="boundary_timeseries",
        function="timeseries",
        timeinterpolation=TimeInterpolation.block_to,
        offset="1.23",
        factor="2.34",
        quantityunitpair=[
            _create_quantityunitpair("time", TEST_TIME_UNIT),
            _create_vectorqup(**_create_vectorvalues()),
        ],
        datablock=[
            ["0", "1.23", "12.3"],
            ["60", "2.34", "23.4"],
            ["120", "3.45", "34.5"],
        ],
    )


def _create_qhtable_values():
    return dict(
        name="boundary_qhtable",
        function="qhtable",
        quantityunitpair=[
            _create_quantityunitpair("qhbnd discharge", "m3/s"),
            _create_quantityunitpair("qhbnd waterlevel", "m"),
        ],
        datablock=[
            ["1.23", "2.34"],
            ["3.45", "4.56"],
        ],
    )


def _create_constant_values():
    return dict(
        name="boundary_constant",
        function="constant",
        offset="1.23",
        factor="2.34",
        timeinterpolation=TimeInterpolation.linear,
        quantityunitpair=[
            _create_quantityunitpair("waterlevelbnd", "m"),
        ],
        datablock=[
            ["3.45"],
        ],
    )


def _create_valid_vectorforcingtest_values():
    return dict(
        name="test",
        function="testfunction",
        quantityunitpair=[
            _create_quantityunitpair("time", TEST_TIME_UNIT),
            _create_vectorqup(**_create_vectorvalues(2)),
        ],
        datablock=[
            ["0", "1.23", "12.3"],
            ["60", "2.34", "23.4"],
            ["120", "3.45", "34.5"],
        ],
    )


def _create_valid_vectorforcingtest_values_that_still_have_to_be_parsed():
    return dict(
        name="test",
        function="testfunction",
        vector="uxuyadvectionvelocitybnd:ux,uy",
        quantity=["ux", "ux", "uy", "uy"],
        unit=["m s-1", "m s-1", "m s-1", "m s-1"],
        datablock=[
            ["0", "1.23", "12.3"],
            ["60", "2.34", "23.4"],
            ["120", "3.45", "34.5"],
        ],
    )


def _create_valid_vectorforcingtest_values_with_multiple_vectors_that_still_have_to_be_parsed():
    return dict(
        name="test",
        function="testfunction",
        vector=[
            "uxuyadvectionvelocitybnd:ux,uy",
            "randomvector:salinity,waterlevelbnd",
        ],
        quantity=[
            "ux",
            "ux",
            "uy",
            "uy",
            "salinity",
            "salinity",
            "waterlevelbnd",
            "waterlevelbnd",
        ],
        unit=["m s-1", "m s-1", "m s-1", "m s-1", "ppt", "ppt", "m", "m"],
        datablock=[
            ["0", "1.23", "12.3"],
            ["60", "2.34", "23.4"],
            ["120", "3.45", "34.5"],
        ],
    )
