import pytest
from pydantic.v1.error_wrappers import ValidationError

from hydrolib.core.dflowfm.t3d.models import LayerType, T3DModel, T3DTimeRecord


class TestT3DModelAtrributes:

    def test_layer_type(self):
        layer_name = "SIGMA"
        layer_type = LayerType(layer_name)
        assert layer_type == "SIGMA"


class TestT3DTimeRecord:
    def test_initialization(self):
        time = "0 seconds since 2006-01-01 00:00:00 +00:00"
        data = [1, 2, 3, 4, 5]
        record = T3DTimeRecord(time=time, data=data)
        assert record.data == data
        assert record.time == time

    def test_wrong_time_format(self):
        time = "any string"
        data = [1, 2, 3, 4, 5]
        with pytest.raises(ValidationError):
            T3DTimeRecord(time=time, data=data)

    def test_scientific_notation(self):
        time = "1e9 seconds since 2001-01-01 00:00:00 +00:00"
        data = [1, 2, 3, 4, 5]
        record = T3DTimeRecord(time=time, data=data)
        assert record.data == data
        assert record.time == time


class TestT3DModel:

    def test_default(self):
        layer_name = "SIGMA"
        comments = ["comment1", "comment2"]
        layers = [1, 2, 3, 4, 5]
        record = [
            T3DTimeRecord(
                time="0 seconds since 2006-01-01 00:00:00 +00:00",
                data=[5.0, 5.0, 10.0, 10.0],
            ),
            T3DTimeRecord(
                time="1e9 seconds since 2001-01-01 00:00:00 +00:00",
                data=[5.0, 5.0, 10.0, 10.0],
            ),
        ]
        model = T3DModel(
            comments=comments, layer_type=layer_name, layers=layers, records=record
        )
        assert model.comments == comments
        assert model.layer_type == layer_name
        assert model.layers == layers
        assert model.records == record
