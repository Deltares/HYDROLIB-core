import inspect
from pathlib import Path
from typing import List

import numpy as np
import pytest
from pydantic.v1.error_wrappers import ValidationError

from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm.common.models import Operand
from hydrolib.core.dflowfm.ini.parser import Parser, ParserConfig
from hydrolib.core.dflowfm.inifield.models import (
    AveragingType,
    DataFileType,
    IniFieldModel,
    InitialField,
    InterpolationMethod,
    LocationType,
    ParameterField,
)
from tests.utils import (
    WrapperTest,
    assert_files_equal,
    test_output_dir,
    test_reference_dir,
)


class TestIniField:
    _datafiletype_cases = [
        ("dataFileType", "ARCINFO", "arcinfo"),
        ("dataFileType", "geotiff", "GeoTIFF"),
        ("dataFileType", "samPLE", "sample"),
        ("dataFileType", "1dfield", "1dField"),
        ("dataFileType", "poLYGOn", "polygon"),
    ]

    _interpolationmethod_cases = [
        ("interpolationMethod", "conSTant", "constant"),
        ("interpolationMethod", "trianguLATION", "triangulation"),
        ("interpolationMethod", "averAGING", "averaging"),
    ]

    _operand_cases = [
        ("operand", "o", "O"),
        ("operand", "a", "A"),
        ("operand", "x", "X"),
        ("operand", "N", "N"),
    ]

    _averagingtype_cases = [
        ("averagingType", "MEAN", "mean"),
        ("averagingType", "nearestnb", "nearestNb"),
        ("averagingType", "MAX", "max"),
        ("averagingType", "MIN", "min"),
        ("averagingType", "invdist", "invDist"),
        ("averagingType", "minabs", "minAbs"),
    ]

    _locationtype_cases = [
        ("locationType", "1D", "1d"),
        ("locationType", "2D", "2d"),
        ("locationType", "All", "all"),
    ]

    def _create_required_inifield_values(self) -> dict:
        inifield_values = dict(
            quantity="waterlevel",
            datafile="iniwlev.xyz",
            datafiletype="sample",
        )

        return inifield_values

    @pytest.mark.parametrize(
        "attribute,input,expected",
        _datafiletype_cases
        + _interpolationmethod_cases
        + _operand_cases
        + _averagingtype_cases
        + _locationtype_cases,
    )
    def test_initialfield_parses_flowdirection_case_insensitive(
        self, attribute: str, input, expected
    ):
        inifield_values = self._create_required_inifield_values()
        inifield_values[attribute.lower()] = input

        datafiletype = inifield_values.get("datafiletype")
        if datafiletype and datafiletype.lower() == DataFileType.polygon.lower():
            inifield_values["value"] = 1.23  # optionally required

        inifield = InitialField(**inifield_values)

        assert getattr(inifield, attribute.lower()) == expected

    def test_inifield_model(self, input_files_dir: Path):
        filepath = input_files_dir.joinpath(
            "dflowfm_individual_files/initialFields.ini"
        )
        m = IniFieldModel(filepath)

        assert len(m.initial) == 2
        assert isinstance(m.initial[0], InitialField)
        assert m.initial[0].quantity == "waterlevel"
        assert m.initial[0].datafile.filepath == Path("iniwaterlevels.asc")
        assert m.initial[0].datafiletype == DataFileType.arcinfo
        assert m.initial[0].interpolationmethod == InterpolationMethod.triangulation
        assert m.initial[0].locationtype == LocationType.twod

        assert isinstance(m.initial[1], InitialField)
        assert m.initial[1].quantity == "bedlevel"
        assert m.initial[1].datafile.filepath == Path("inibedlevel.ini")
        assert m.initial[1].datafiletype == DataFileType.onedfield

        assert len(m.parameter) == 2
        assert isinstance(m.parameter[0], ParameterField)
        assert m.parameter[0].quantity == "frictioncoefficient"
        assert m.parameter[0].datafile.filepath == Path("manning.xyz")
        assert m.parameter[0].datafiletype == DataFileType.sample
        assert m.parameter[0].interpolationmethod == InterpolationMethod.triangulation

        assert isinstance(m.parameter[1], ParameterField)
        assert m.parameter[1].quantity == "frictioncoefficient"
        assert m.parameter[1].datafile.filepath == Path("calibration1.pol")
        assert m.parameter[1].datafiletype == DataFileType.polygon
        assert m.parameter[1].interpolationmethod == InterpolationMethod.constant
        assert m.parameter[1].value == pytest.approx(0.03)
        assert m.parameter[1].operand == Operand.mult

    def test_load_and_save(self, input_files_dir: Path):
        """Test whether a model loaded from file is serialized correctly.
        Particularly intended to test writing of default enum values."""

        filepath = input_files_dir.joinpath(
            "dflowfm_individual_files/initialFields.ini"
        )
        m = IniFieldModel(filepath)

        output_file = Path(test_output_dir / "fm" / "serialize_initialFields.ini")
        reference_file = Path(test_reference_dir / "fm" / "serialize_initialFields.ini")

        m.filepath = output_file
        m.save()

        assert_files_equal(output_file, reference_file, [0])

    def test_initialfield_construction_with_parser(self):
        parser = Parser(ParserConfig())

        input_str = inspect.cleandoc(
            """
            [Initial]
            quantity          = waterDepth
            dataFile          = depth.xyz
            dataFileType      = sample
            """
        )

        for line in input_str.splitlines():
            parser.feed_line(line)

        document = parser.finalize()

        wrapper = WrapperTest[InitialField].parse_obj({"val": document.sections[0]})
        inifield = wrapper.val

        assert inifield.quantity == "waterDepth"
        assert inifield.datafile.filepath == Path("depth.xyz")
        assert inifield.datafiletype == DataFileType.sample

        # Check for auto-set default values:
        assert inifield.operand == Operand.override
        assert inifield.interpolationmethod == None
        assert inifield.extrapolationmethod == False

    def test_initialfield_value_with_wrong_datafiletype(self):
        inifield_values = self._create_required_inifield_values()
        inifield_values["value"] = 1.23
        inifield_values["datafiletype"] = DataFileType.sample

        with pytest.raises(ValidationError) as error:
            _ = InitialField(**inifield_values)

        expected_message = f"When value=1.23 is given, dataFileType={DataFileType.polygon} is required."

        assert expected_message in str(error.value)

    def test_initialfield_value_with_missing_value(self):
        inifield_values = self._create_required_inifield_values()
        inifield_values["datafiletype"] = DataFileType.polygon

        with pytest.raises(ValidationError) as error:
            _ = InitialField(**inifield_values)

        expected_message = (
            f"value should be provided when datafiletype is {DataFileType.polygon}"
        )

        assert expected_message in str(error.value)


def test_initial_conditions_interpolation_methods(
    initial_condition_interpolation_methods: List[str],
):
    assert len(InterpolationMethod) == 5
    assert all(
        quantity.value in initial_condition_interpolation_methods
        for quantity in InterpolationMethod.__members__.values()
    )


def test_initial_condition_file_type(initial_condition_file_type: List[str]):
    assert len(DataFileType) == 8
    assert all(
        quantity.value in initial_condition_file_type
        for quantity in DataFileType.__members__.values()
    )


def test_averaging_type_file_type(initial_cond_averaging_type: List[str]):
    assert len(AveragingType) == 7
    assert all(
        quantity.value in initial_cond_averaging_type
        for quantity in AveragingType.__members__.values()
    )


class TestInitialConditions:

    def test_initialization(self):
        data = {
            "quantity": "waterlevel",
            "datafile": Path("anyfile.pli"),
            "datafiletype": DataFileType.arcinfo,
            "interpolationmethod": InterpolationMethod.constant,
            "operand": "O",
            "averagingtype": AveragingType.mean,
            "averagingnummin": 2,
            "averagingpercentile": 95.0,
        }
        initial_conditions = InitialField(**data)
        assert initial_conditions.quantity == "waterlevel"
        assert isinstance(initial_conditions.datafile, DiskOnlyFileModel)
        assert initial_conditions.datafiletype == DataFileType.arcinfo
        assert initial_conditions.interpolationmethod == InterpolationMethod.constant
        assert initial_conditions.operand == "O"
        assert initial_conditions.averagingtype == AveragingType.mean
        assert initial_conditions.averagingnummin == 2
        assert np.isclose(initial_conditions.averagingpercentile, 95.0)

    def test_default_values(self):
        initial_conditions = InitialField(
            quantity="waterlevel",
            datafile=DiskOnlyFileModel(),
            datafiletype=DataFileType.arcinfo,
        )
        assert initial_conditions.interpolationmethod is None
        assert initial_conditions.operand == "O"
        assert initial_conditions.averagingtype == "mean"
        assert np.isclose(initial_conditions.averagingrelsize, 1.01)
        assert initial_conditions.averagingnummin == 1
        assert initial_conditions.extrapolationmethod is False
        assert initial_conditions.locationtype == "all"
        assert np.isclose(initial_conditions.averagingpercentile, 0.0)

    def test_setting_optional_fields(self):
        initial_conditions = InitialField(
            quantity="waterlevel",
            datafile=DiskOnlyFileModel(),
            datafiletype=DataFileType.arcinfo,
            interpolationmethod=InterpolationMethod.constant,
            operand="O",
            averagingtype=AveragingType.mean,
            averagingnummin=2,
            averagingpercentile=95.0,
        )
        assert initial_conditions.interpolationmethod == InterpolationMethod.constant
        assert initial_conditions.operand == "O"
        assert initial_conditions.averagingtype == AveragingType.mean
        assert initial_conditions.averagingnummin == 2
        assert np.isclose(initial_conditions.averagingpercentile, 95.0)

    def test_invalid_datafiletype(self):
        with pytest.raises(ValueError):
            InitialField(
                quantity="waterlevel",
                datafile=DiskOnlyFileModel(),
                datafiletype="invalidType",
            )

    def test_invalid_interpolationmethod(self):
        with pytest.raises(ValueError):
            InitialField(
                quantity="waterlevel",
                datafile=DiskOnlyFileModel(),
                datafiletype=DataFileType.arcinfo,
                interpolationmethod="invalidMethod",
            )

    @pytest.mark.parametrize(
        ("missing_field", "alias_field"),
        [
            ("quantity", "quantity"),
            ("datafile", "dataFile"),
            ("datafiletype", "dataFileType"),
        ],
    )
    def test_missing_required_fields(self, missing_field, alias_field):
        dict_values = {
            "quantity": "rainfall",
            "datafile": DiskOnlyFileModel(),
            "datafiletype": DataFileType.arcinfo,
        }
        del dict_values[missing_field]

        with pytest.raises(ValidationError) as error:
            InitialField(**dict_values)

        expected_message = f"{alias_field}\n  field required "
        assert expected_message in str(error.value)


class TestExcludeFromValidation:
    def test_exclude_tracer_prefix_fields(self):
        """
        Test that the tracer prefix fields are excluded from validation and creating the InitialField will succeed
        with the `tracerdecaytime` attribute even that it is not a field in the class.
        """
        data = {
            "quantity": "initialtracerdTR1",
            "datafile": "domain.pol",
            "datafiletype": DataFileType.polygon,
            "value": 0.0,
            "interpolationmethod": InterpolationMethod.constant,
            "operand": "O",
            "tracerdecaytime": "8640000",
        }

        model = InitialField(**data)
        assert model.tracerdecaytime == "8640000"
