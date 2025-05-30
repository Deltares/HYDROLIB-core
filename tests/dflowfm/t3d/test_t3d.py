import pytest
from pydantic.v1.error_wrappers import ValidationError

from hydrolib.core.base.models import ModelSaveSettings
from hydrolib.core.dflowfm.t3d.models import LayerType, T3DModel, T3DTimeRecord
from hydrolib.core.dflowfm.t3d.parser import T3DParser
from hydrolib.core.dflowfm.t3d.serializer import T3DSerializer, T3DSerializerConfig
from tests.utils import assert_files_equal, test_input_dir

t3d_file_path = test_input_dir / "dflowfm_individual_files/t3d"


class TestT3DModelAtrributes:

    def test_layer_type(self):
        layer_name = "SIGMA"
        layer_type = LayerType(layer_name)
        assert layer_type == "SIGMA"


class TestT3DTimeRecord:
    @pytest.mark.parametrize(
        "time,data,should_fail",
        [
            ("0 seconds since 2006-01-01 00:00:00 +00:00", [1, 2, 3, 4, 5], False),
            ("any string", [1, 2, 3, 4, 5], True),
            ("1e9 seconds since 2001-01-01 00:00:00 +00:00", [1, 2, 3, 4, 5], False),
        ],
        ids=["Valid time format", "Invalid time format", "Scientific notation in time"],
    )
    def test_time_record_initialization(self, time, data, should_fail):
        """
        Test various T3DTimeRecord initialization scenarios.

        * When `should_fail` is False, the T3DTimeRecord should initialize
          successfully and its fields should match the inputs.
        * When `should_fail` is True, a ValidationError is expected,
          indicating the time format is invalid or cannot be parsed.
        """
        if should_fail:
            with pytest.raises(ValidationError):
                T3DTimeRecord(time=time, data=data)
        else:
            record = T3DTimeRecord(time=time, data=data)
            assert record.data == data
            assert record.time == time

    def test_properties(self):
        record = T3DTimeRecord(
            time="0 seconds since 2006-01-01 00:00:00 +00:00", data=[1, 2, 3, 4, 5]
        )
        assert record.time_unit == "seconds"
        assert record.time_offset == 0
        assert record.reference_date == "2006-01-01 00:00:00 +00:00"


class TestT3DModel:
    data = {
        "comments": [],
        "layer_type": "SIGMA",
        "layers": [0.0, 0.2, 0.6, 0.8, 1.0],
        "records": [
            {"time": "0 seconds since 2006-01-01 00:00:00 +00:00", "data": [1.0] * 5},
            {"time": "180 seconds since 2001-01-01 00:00:00 +00:00", "data": [2.0] * 5},
        ],
    }

    @pytest.mark.parametrize(
        "quantities_names, should_fail",
        [
            (["quantity1", "quantity2", "quantity3", "quantity4", "quantity5"], False),
            (["quantity1", "quantity2"], True),
        ],
        ids=["Correct quantities", "Incorrect quantities"],
    )
    def test_model_initialization(self, quantities_names, should_fail):
        if should_fail:
            with pytest.raises(ValueError):
                T3DModel(**self.data, quantities_names=quantities_names)
        else:
            model = T3DModel(**self.data, quantities_names=quantities_names)
            assert model.size == (2, 5)

    def test_get_units(self):
        model = T3DModel(**self.data)
        model.quantities_names = [
            "quantity1",
            "quantity2",
            "quantity3",
            "quantity4",
            "quantity5",
        ]
        assert model.get_units() == ["-", "-", "-", "-", "-"]

        model.quantities_names = [
            "waterlevel",
            "temperature",
            "salinity",
            "discharge",
            "any quantity",
        ]
        assert model.get_units() == ["m", "degC", "1e-3", "m3/s", "-"]

    @pytest.mark.parametrize(
        "record_data, should_fail",
        [
            (
                [
                    {
                        "time": "0 seconds since 2006-01-01 00:00:00 +00:00",
                        "data": [5.0] * 4,
                    },
                    {
                        "time": "1e9 seconds since 2001-01-01 00:00:00 +00:00",
                        "data": [5.0] * 5,
                    },
                ],
                True,
            ),
        ],
        ids=["Different record lengths"],
    )
    def test_different_record_length(self, record_data, should_fail):
        if should_fail:
            with pytest.raises(ValidationError):
                T3DModel(
                    comments=[],
                    layer_type="SIGMA",
                    layers=[1, 2, 3, 4, 5],
                    records=record_data,
                )

    def test_initialize_with_dict(self):
        model = T3DModel(**self.data)
        assert model.comments == self.data["comments"]
        assert model.layer_type == self.data["layer_type"]
        assert model.layers == self.data["layers"]
        assert model.records == self.data["records"]

    def test_initialize_with_file_path(self):
        filepath = t3d_file_path / "sigma-5-layers-3-times.t3d"
        model = T3DModel(filepath=filepath)
        assert model.filepath == filepath
        assert model.serializer_config.float_format == ""

    def test_as_dict(self):
        model = T3DModel(**self.data)
        data = model.as_dict()
        assert isinstance(data, dict)
        records = self.data["records"]
        assert list(data.values()) == [record["data"] for record in records]
        assert list(data.keys()) == [
            int(record["time"].split(" ")[0]) for record in records
        ]


class TestParser:
    @pytest.mark.parametrize(
        "input_path",
        [
            pytest.param(
                t3d_file_path / "sigma-5-layers-3-times.t3d",
                id="sigma-5-layers-3-times",
            ),
        ],
    )
    def test_parse_t3d_files(self, input_path):
        data = T3DParser.parse(input_path)
        keys = ["records", "layer_type", "layers"]
        assert all(key in data.keys() for key in keys)
        assert data["layer_type"] == "SIGMA"
        assert len(data["records"]) == 3
        assert len(data["layers"]) == 5

    def test_end_of_file_error(self):
        """test if there are empty lines at the end of the file the parser is able to exit the loop."""
        data = """
        LAYER_TYPE=SIGMA
        LAYERS=0.0 0.5 0.55 0.75 1
        TIME = 0 seconds since 2006-01-01 00:00:00 +00:00
        41 36.45455 36 34 31
        TIME = 180 seconds since 2006-01-01 00:00:00 +00:00
        41.00002 36.45456 36.00002 34.00002 31.00002
        TIME = 9999999 seconds since 2006-01-01 00:00:00 +00:00
        42 37.45455 37 35 32


        """
        lines = data.splitlines()
        assert T3DParser._read_data(lines, 0)


class TestT3DModelSerializer:
    data = {
        "comments": [],
        "layer_type": "SIGMA",
        "layers": [0.0, 0.2, 0.6, 0.8, 1.0],
        "records": [
            {"time": "0 seconds since 2006-01-01 00:00:00 +00:00", "data": [1.0] * 5},
            {"time": "180 seconds since 2006-01-01 00:00:00 +00:00", "data": [2.0] * 5},
            {
                "time": "9999999 seconds since 2006-01-01 00:00:00 +00:00",
                "data": [3.0] * 5,
            },
        ],
    }

    def test_serialize_data(self):
        reference_path = t3d_file_path / "sigma-5-layers-3-times.t3d"
        output_path = t3d_file_path / "test_serialize.t3d"
        config = T3DSerializerConfig(float_format=".1f")
        T3DSerializer.serialize(output_path, self.data, config, ModelSaveSettings())
        assert_files_equal(output_path, reference_path)
        output_path.unlink()

    def test_save_model(self):
        model = T3DModel(**self.data)
        output_path = t3d_file_path / "test_save.t3d"
        model.save(output_path)
        assert_files_equal(output_path, t3d_file_path / "sigma-5-layers-3-times.t3d")
        output_path.unlink()
