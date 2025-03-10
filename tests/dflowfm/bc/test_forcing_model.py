from pathlib import Path

import numpy as np
import pytest
from pydantic.v1.error_wrappers import ValidationError

from hydrolib.core.dflowfm.bc.models import (
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
)
from tests.utils import assert_files_equal


def quantityunitpair(quantity, unit, verticalpositionindex=None):
    return QuantityUnitPair(
        quantity=quantity, unit=unit, vertpositionindex=verticalpositionindex
    )


def harmonic_values(iscorrection: bool):
    function = "harmonic-correction" if iscorrection else "harmonic"
    return dict(
        name=f"boundary_{function}",
        function=function,
        quantityunitpair=[
            quantityunitpair("harmonic component", "minutes"),
            quantityunitpair("waterlevelbnd amplitude", "m"),
            quantityunitpair("waterlevelbnd phase", "deg"),
        ],
        datablock=[
            ["0", "1.23", "2.34"],
            ["60", "3.45", "4.56"],
        ],
    )


def qhtable_values():
    return dict(
        name="boundary_qhtable",
        function="qhtable",
        quantityunitpair=[
            quantityunitpair("qhbnd discharge", "m3/s"),
            quantityunitpair("qhbnd waterlevel", "m"),
        ],
        datablock=[
            ["1.23", "2.34"],
            ["3.45", "4.56"],
        ],
    )


def constant_values():
    return dict(
        name="boundary_constant",
        function="constant",
        offset="1.23",
        factor="2.34",
        timeinterpolation=TimeInterpolation.linear,
        quantityunitpair=[
            quantityunitpair("waterlevelbnd", "m"),
        ],
        datablock=[
            ["3.45"],
        ],
    )


def astronomic_values(iscorrection: bool, quantityunitpair):
    function = "astronomic-correction" if iscorrection else "astronomic"
    return dict(
        name=f"boundary_{function}",
        function=function,
        quantityunitpair=[
            quantityunitpair("astronomic component", "-"),
            quantityunitpair("waterlevelbnd amplitude", "m"),
            quantityunitpair("waterlevelbnd phase", "deg"),
        ],
        datablock=[
            ["A0", "1.23", "2.34"],
            ["M4", "3.45", "4.56"],
            ["N2", "5.67", "6.78"],
        ],
    )


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
    Wrapper class to test the logic of the ForcingModel class in hydrolib.core.dflowfm.bc.models.py.
    """

    def test_forcing_model(self, input_files_dir):
        filepath = (
            input_files_dir
            / "e02/f101_1D-boundaries/c01_steady-state-flow/BoundaryConditions.bc"
        )

        m = ForcingModel(filepath)
        assert len(m.forcing) == 13
        assert isinstance(m.forcing[-1], TimeSeries)

    def test_read_bc_missing_field_raises_correct_error(self, invalid_data_dir):
        bc_file = "missing_field.bc"
        identifier = "Boundary2"

        filepath = invalid_data_dir / bc_file

        with pytest.raises(ValidationError) as error:
            ForcingModel(filepath)

        expected_message1 = f"{bc_file} -> forcing -> 1 -> {identifier}"
        expected_message2 = "quantity is not provided"
        assert expected_message1 in str(error.value)
        assert expected_message2 in str(error.value)

    def test_save_forcing_model(
        self, time_series_values, t3d_values, output_files_dir, reference_files_dir
    ):
        bc_file = output_files_dir / "test.bc"
        reference_file = reference_files_dir / "bc/test.bc"
        forcingmodel = ForcingModel()
        forcingmodel.filepath = bc_file

        timeseries = TimeSeries(**time_series_values)
        harmonic = Harmonic(**harmonic_values(False))
        harmoniccorrection = HarmonicCorrection(**harmonic_values(True))
        t3d = T3D(**t3d_values)
        qhtable = QHTable(**qhtable_values())
        constant = Constant(**constant_values())

        forcingmodel.forcing.append(timeseries)
        forcingmodel.forcing.append(harmonic)
        forcingmodel.forcing.append(harmoniccorrection)
        forcingmodel.forcing.append(t3d)
        forcingmodel.forcing.append(qhtable)
        forcingmodel.forcing.append(constant)

        forcingmodel.serializer_config.float_format = ".3f"
        forcingmodel.serializer_config.float_format_datablock = ".4f"
        forcingmodel.save()

        assert bc_file.is_file() == True
        assert_files_equal(bc_file, reference_file, skip_lines=[0, 3])

    @pytest.mark.parametrize("cls", [Astronomic, AstronomicCorrection])
    def test_astronomic_values_with_strings_in_datablock_are_parsed_correctly(
        self, cls
    ):
        try:
            is_correction = cls == AstronomicCorrection
            _ = cls(**astronomic_values(is_correction, quantityunitpair))
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

    def test_forcing_model_correct_default_serializer_config(self):
        model = ForcingModel()

        assert model.serializer_config.section_indent == 0
        assert model.serializer_config.property_indent == 0
        assert model.serializer_config.datablock_indent == 0
        assert model.serializer_config.float_format == ""
        assert model.serializer_config.datablock_spacing == 2
        assert model.serializer_config.comment_delimiter == "#"
        assert model.serializer_config.skip_empty_properties == True

    def test_forcing_model_with_datablock_that_has_nan_values_should_raise_error(self):
        datablock = np.random.uniform(low=-40, high=130.3, size=(4, 2)) * np.nan
        datablock_list = datablock.tolist()

        with pytest.raises(ValidationError) as error:
            TimeSeries(
                name="east2_0001",
                quantityunitpair=[
                    QuantityUnitPair(
                        quantity="time", unit="seconds since 2022-01-01 00:00:00 +00:00"
                    ),
                    QuantityUnitPair(quantity="waterlevel", unit="m"),
                ],
                timeInterpolation=TimeInterpolation.linear,
                datablock=datablock_list,
            )

        expected_message = "NaN is not supported in datablocks."
        assert expected_message in str(error.value)
