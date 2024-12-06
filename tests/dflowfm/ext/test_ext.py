from pathlib import Path
from typing import List

import numpy as np
import pytest
from pydantic.v1 import ValidationError

from hydrolib.core.basemodel import DiskOnlyFileModel
from hydrolib.core.dflowfm.bc.models import Constant, ForcingModel, RealTime
from hydrolib.core.dflowfm.ext.models import (
    ExtModel,
    Meteo,
    MeteoForcingFileType,
    MeteoInterpolationMethod,
)
from hydrolib.core.dflowfm.tim.models import TimModel


class TestExtModel:
    """Class to test all methods contained in the
    hydrolib.core.dflowfm.ext.models.ExtModel class"""

    def test_construct_from_file_with_tim(self, input_files_dir: Path):
        input_ext = input_files_dir.joinpath(
            "e02/f006_external_forcing/c063_rain_tim/rainschematic.ext"
        )

        ext_model = ExtModel(input_ext)

        assert isinstance(ext_model, ExtModel)
        assert len(ext_model.meteo) == 1
        assert ext_model.meteo[0].quantity == "rainfall_rate"
        assert isinstance(ext_model.meteo[0].forcingfile, TimModel)
        assert ext_model.meteo[0].forcingfiletype == MeteoForcingFileType.uniform

        assert len(ext_model.meteo[0].forcingfile.timeseries) == 14

    def test_construct_from_file_with_bc(self, input_files_dir: Path):
        input_ext = input_files_dir.joinpath(
            "e02/f006_external_forcing/c069_rain_bc/rainschematic.ext"
        )
        ext_model = ExtModel(input_ext)

        assert isinstance(ext_model, ExtModel)
        assert len(ext_model.meteo) == 1
        assert ext_model.meteo[0].quantity == "rainfall_rate"
        assert isinstance(ext_model.meteo[0].forcingfile, ForcingModel)
        assert ext_model.meteo[0].forcingfiletype == MeteoForcingFileType.bcascii

    def test_construct_from_file_with_netcdf(self, input_files_dir: Path):
        input_ext = input_files_dir.joinpath(
            "e02/f006_external_forcing/c067_rain_netcdf_stations/rainschematic.ext"
        )
        ext_model = ExtModel(input_ext)

        assert isinstance(ext_model, ExtModel)
        assert len(ext_model.meteo) == 1
        assert ext_model.meteo[0].quantity == "rainfall"
        assert isinstance(ext_model.meteo[0].forcingfile, DiskOnlyFileModel)
        assert ext_model.meteo[0].forcingfiletype == MeteoForcingFileType.netcdf

    def test_ext_model_correct_default_serializer_config(self):
        model = ExtModel()

        assert model.serializer_config.section_indent == 0
        assert model.serializer_config.property_indent == 0
        assert model.serializer_config.datablock_indent == 8
        assert model.serializer_config.float_format == ""
        assert model.serializer_config.datablock_spacing == 2
        assert model.serializer_config.comment_delimiter == "#"
        assert model.serializer_config.skip_empty_properties == True


class TestMeteo:

    def test_meteo_interpolation_methods(self, meteo_interpolation_methods: List[str]):
        assert len(MeteoInterpolationMethod) == 3
        assert all(
            quantity.value in meteo_interpolation_methods
            for quantity in MeteoInterpolationMethod.__members__.values()
        )

    def test_meteo_forcing_file_type(self, meteo_forcing_file_type: List[str]):
        assert len(MeteoForcingFileType) == 8
        assert all(
            quantity.value in meteo_forcing_file_type
            for quantity in MeteoForcingFileType.__members__.values()
        )

    def test_meteo_initialization(self):
        data = {
            "quantity": "rainfall",
            "forcingfile": ForcingModel(),
            "forcingfiletype": MeteoForcingFileType.bcascii,
            "targetmaskfile": None,
            "targetmaskinvert": False,
            "interpolationmethod": None,
        }
        meteo = Meteo(**data)
        assert meteo.quantity == "rainfall"
        assert isinstance(meteo.forcingfile, ForcingModel)
        assert meteo.forcingfiletype == MeteoForcingFileType.bcascii

    def test_default_values(self):
        meteo = Meteo(
            quantity="rainfall",
            forcingfile=ForcingModel(),
            forcingfiletype=MeteoForcingFileType.uniform,
        )
        assert meteo.targetmaskfile is None
        assert meteo.targetmaskinvert is None
        assert meteo.interpolationmethod is None
        assert meteo.operand == "O"
        assert meteo.extrapolationAllowed is None
        assert meteo.extrapolationSearchRadius is None
        assert meteo.averagingType is None
        assert meteo.averagingNumMin is None
        assert meteo.averagingPercentile is None

    def test_setting_optional_fields(self):
        meteo = Meteo(
            quantity="rainfall",
            forcingfile=ForcingModel(),
            forcingfiletype=MeteoForcingFileType.uniform,
            targetmaskfile=None,
            targetmaskinvert=True,
            interpolationmethod=MeteoInterpolationMethod.nearestnb,
            operand="O",
            extrapolationAllowed=True,
            extrapolationSearchRadius=10,
            averagingType=1,
            averagingNumMin=0.5,
            averagingPercentile=90,
        )
        assert meteo.targetmaskfile is None
        assert meteo.targetmaskinvert is True
        assert meteo.interpolationmethod == MeteoInterpolationMethod.nearestnb
        assert meteo.operand == "O"
        assert meteo.extrapolationAllowed is True
        assert meteo.extrapolationSearchRadius == 10
        assert meteo.averagingType == 1
        assert np.isclose(meteo.averagingNumMin, 0.5)
        assert meteo.averagingPercentile == 90

    def test_invalid_forcingfiletype(self):
        with pytest.raises(ValueError):
            Meteo(
                quantity="rainfall",
                forcingfile=ForcingModel(),
                forcingfiletype="invalidType",
            )

    def test_invalid_interpolation_method(self):
        with pytest.raises(ValueError):
            Meteo(
                quantity="rainfall",
                forcingfile=ForcingModel(),
                forcingfiletype=MeteoForcingFileType.uniform,
                interpolationmethod="invalidMethod",
            )

    @pytest.mark.parametrize(
        ("missing_field", "alias_field"),
        [
            ("quantity", "QUANTITY"),
            ("forcingfile", "forcingFile"),
            ("forcingfiletype", "forcingFileType"),
        ],
    )
    def test_missing_required_fields(self, missing_field, alias_field):
        dict_values = {
            "quantity": "rainfall",
            "forcingfile": ForcingModel(),
            "forcingfiletype": MeteoForcingFileType.bcascii,
            "targetmaskfile": None,
            "targetmaskinvert": False,
            "interpolationmethod": None,
        }
        del dict_values[missing_field]

        with pytest.raises(ValidationError) as error:
            Meteo(**dict_values)

        expected_message = f"{alias_field}\n  field required "
        assert expected_message in str(error.value)

    def test_is_intermediate_link(self):
        meteo = Meteo(
            quantity="rainfall",
            forcingfile=ForcingModel(),
            forcingfiletype=MeteoForcingFileType.uniform,
        )
        assert meteo.is_intermediate_link() is True

    def test_initialize_with_boundary_condition_file(
        self, boundary_condition_file: Path
    ):
        meteo = Meteo(
            quantity="rainfall",
            forcingfile=boundary_condition_file,
            forcingfiletype=MeteoForcingFileType.bcascii,
        )
        assert isinstance(meteo.forcingfile, ForcingModel)
        assert meteo.forcingfile.filepath == boundary_condition_file
        assert meteo.forcingfiletype == MeteoForcingFileType.bcascii

    def test_initialize_with_time_series_file(self, time_series_file: Path):
        meteo = Meteo(
            quantity="rainfall",
            forcingfile=time_series_file,
            forcingfiletype=MeteoForcingFileType.bcascii,
        )
        assert isinstance(meteo.forcingfile, TimModel)
        assert meteo.forcingfile.filepath == time_series_file
        assert meteo.forcingfiletype == MeteoForcingFileType.bcascii
