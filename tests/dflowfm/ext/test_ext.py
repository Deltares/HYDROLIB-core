from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pytest
from pydantic import ValidationError

from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm.bc.models import (
    ForcingBase,
    ForcingModel,
    Harmonic,
    QuantityUnitPair,
)
from hydrolib.core.dflowfm.ext.models import (
    Boundary,
    ExtModel,
    Meteo,
    MeteoForcingFileType,
    MeteoInterpolationMethod,
    SourceSink,
)
from hydrolib.core.dflowfm.polyfile.models import PolyFile
from hydrolib.core.dflowfm.tim.models import TimModel
from tests.utils import invalid_test_data_dir, test_data_dir
from tests.test_utils import enum_checker


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

    def test_model_with_duplicate_file_references_use_same_instances(self):
        file_path = (
                test_data_dir
                / "input/e02/c11_korte-woerden-1d/dimr_model/dflowfm/FlowFM_bnd.ext"
        )
        model = ExtModel(filepath=file_path)

        boundary1 = model.boundary[0]
        boundary2 = model.boundary[1]

        # Set a field for first boundary
        boundary1.forcingfile[0].forcing[0].name = "some_new_value"

        # Field for second boundary is also updated (same instance)
        assert boundary2.forcingfile[0].forcing[0].name == "some_new_value"

    @pytest.mark.filterwarnings("ignore:File.*not found:UserWarning")
    def test_read_ext_missing_boundary_field_raises_correct_error(self):
        file = "missing_boundary_field.ext"

        filepath = invalid_test_data_dir / file

        with pytest.raises(ValidationError) as error:
            ExtModel(filepath)

        expected_message = f"`{file}`.general.filetype"
        assert expected_message in str(error.value)

    def test_read_ext_missing_lateral_field_raises_correct_error(self):
        file = "missing_lateral_field.ext"

        filepath = invalid_test_data_dir / file

        with pytest.raises(ValidationError) as error:
            ExtModel(filepath)

        expected_message = f"`{file}`.lateral.1.Lateral2.discharge"
        assert expected_message in str(error.value)

    def test_boundary_with_forcing_file_returns_forcing(self):
        forcing1 = self._create_forcing("bnd1", "waterlevelbnd")
        forcing2 = self._create_forcing("bnd2", "dischargebnd")
        forcing3 = self._create_forcing("bnd3", "qhbnd discharge")

        forcing_file = ForcingModel(forcing=[forcing1, forcing2, forcing3])

        boundary2 = Boundary(
            nodeid="bnd2", quantity="dischargebnd", forcingfile=forcing_file
        )

        assert boundary2.forcing is forcing2

    def test_boundary_with_forcing_file_without_match_returns_none(self):
        forcing1 = self._create_forcing("bnd1", "waterlevelbnd")
        forcing2 = self._create_forcing("bnd2", "dischargebnd")

        forcing_file = ForcingModel(forcing=[forcing1, forcing2])

        boundary = Boundary(nodeid="bnd3", quantity="qhbnd", forcingfile=forcing_file)

        assert boundary.forcing is None
        assert boundary.nodeid == "bnd3"
        assert boundary.quantity == "qhbnd"

    def _create_forcing(self, name: str, quantity: str) -> ForcingBase:
        return Harmonic(
            name=name,
            quantityunitpair=[QuantityUnitPair(quantity=quantity, unit="")],
            function="harmonic",
            datablock=[],
        )


class TestMeteo:

    def test_meteo_interpolation_methods(self):
        enum_checker(MeteoInterpolationMethod)

    def test_meteo_forcing_file_type(self):
        enum_checker(MeteoForcingFileType)

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
            ("quantity", "quantity"),
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

        expected_message = f"meteo\n{alias_field}\n  field required "
        assert expected_message.lower() in str(error.value).lower()

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
            forcingfiletype=MeteoForcingFileType.uniform,
        )
        assert isinstance(meteo.forcingfile, TimModel)
        assert meteo.forcingfile.filepath == time_series_file
        assert meteo.forcingfiletype == MeteoForcingFileType.uniform

    def test_polyfile_as_forcingfile(self, polylines_dir: Path):
        poly_file_path = polylines_dir / "boundary-polyline-no-z-no-label.pli"
        meteo = Meteo(
            quantity="rainfall",
            forcingfile=poly_file_path,
            forcingfiletype=MeteoForcingFileType.polygon,
        )
        assert isinstance(meteo.forcingfile, PolyFile)
        assert meteo.forcingfile.filepath == poly_file_path
        assert meteo.forcingfiletype == MeteoForcingFileType.polygon


forcing_base_list = [
    {
        "name": "user_defined_name_1",
        "function": "timeseries",
        "timeinterpolation": "linear",
        "quantity": ["time", "discharge"],
        "unit": ["minutes since 2015-01-01 00:00:00", "m3/s"],
        "datablock": [[1], [1.1234]],
    },
    {
        "name": "user_defined_name_1",
        "function": "timeseries",
        "timeinterpolation": "linear",
        "quantity": ["time", "salinitydelta"],
        "unit": ["minutes since 2015-01-01 00:00:00", "ppt"],
        "datablock": [[1, 2, 3, 4, 5], [3.0, 5.0, 12.0, 9.0, 23.0]],
    },
    {
        "name": "user_defined_name_2",
        "function": "timeseries",
        "timeinterpolation": "linear",
        "quantity": ["time", "temperaturedelta"],
        "unit": ["minutes since 2015-01-01 00:00:00", "C"],
        "datablock": [[1, 2, 3, 4, 5], [2.0, 2.0, 5.0, 8.0, 10.0]],
    },
]


class TestSourceSink:

    @pytest.fixture
    def source_sink_data(self) -> Dict[str, Any]:
        forcing_model_list = [
            ForcingModel(**{"forcing": [force]}) for force in forcing_base_list
        ]
        forcing = {
            key["quantity"][1]: value
            for key, value in zip(forcing_base_list, forcing_model_list)
        }
        data = {
            "id": "L1",
            "name": "discharge_salinity_temperature_sorsin",
            "locationfile": Path("tests/data/input/source-sink/leftsor.pliz"),
            "numcoordinates": 2,
            "xcoordinates": [63.350456, 45.200344],
            "ycoordinates": [12.950216, 6.350155],
            "zsource": -3.0,
            "zsink": -4.2,
            "area": 5,
        }
        data = data | forcing
        return data

    def test_default(self, source_sink_data: Dict[str, Any]):
        """
        Test construct the SourceSink class with all the attributes.
        """

        source_sink = SourceSink(**source_sink_data)

        # only the comments key is added by default here
        assert source_sink.__dict__.keys() - source_sink_data.keys() == {"comments"}

    def test_extra_tracer(self, source_sink_data: Dict[str, Any]):
        """
        Test construct the SourceSink class with an extra initialtracer-*** dynamically assigned field.
        """
        source_sink_data["initialtracer_any_name"] = [1, 2, 3]
        source_sink = SourceSink(**source_sink_data)

        # only the comments key is added by default here
        assert source_sink.__dict__.keys() - source_sink_data.keys() == {"comments"}
        assert source_sink.initialtracer_any_name == [1, 2, 3]

    def test_multiple_dynamic_fields(self, source_sink_data: Dict[str, Any]):
        """
        Test construct the SourceSink class with an extra initialtracer-*** dynamically assigned field.
        """
        source_sink_data["initialtracer_any_name"] = [1, 2, 3]
        source_sink_data["tracerbndanyname"] = [1, 2, 3]
        source_sink_data["sedfracbnd_any_name"] = [1, 2, 3]
        source_sink = SourceSink(**source_sink_data)

        # only the comments key is added by default here
        assert source_sink.__dict__.keys() - source_sink_data.keys() == {"comments"}
        assert source_sink.initialtracer_any_name == [1, 2, 3]
        assert source_sink.tracerbndanyname == [1, 2, 3]
        assert source_sink.sedfracbnd_any_name == [1, 2, 3]

    def test_time_series_discharge_case(self):
        """

        Returns:

        """
        forcing_model_list = [
            ForcingModel(**{"forcing": [force]}) for force in forcing_base_list
        ]
        forcing = {
            key["quantity"][1]: value
            for key, value in zip(forcing_base_list, forcing_model_list)
        }
        data = {
            "id": "L1",
            "name": "discharge_salinity_temperature_sorsin",
            "locationfile": "tests/data/input/source-sink/leftsor.pliz",
            "numcoordinates": 2,
            "xcoordinates": [63.350456, 45.200344],
            "ycoordinates": [12.950216, 6.350155],
            "zsource": -3.0,
            "zsink": -4.2,
            "discharge": [1.0, 2.0, 3.0, 5.0, 8.0],
            "temperaturedelta": [2.0, 2.0, 5.0, 8.0, 10.0],
            "salinitydelta": [3.0, 5.0, 12.0, 9.0, 23.0],
        }
        data = data | forcing

        assert SourceSink(**data)
