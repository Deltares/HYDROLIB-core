import pytest
from pydantic.v1.error_wrappers import ValidationError

from hydrolib.core.dflowfm.t3d.models import LayerType, T3DModel, T3DTimeRecord


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


# class TestParser:
#     def test
