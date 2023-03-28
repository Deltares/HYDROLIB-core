import pytest

from hydrolib.core.basemodel import ModelSaveSettings, SerializerConfig
from hydrolib.core.dflowfm.xyz.models import XYZModel, XYZPoint
from hydrolib.core.dflowfm.xyz.parser import XYZParser
from hydrolib.core.dflowfm.xyz.serializer import XYZSerializer
from tests.utils import (
    assert_files_equal,
    test_input_dir,
    test_output_dir,
    test_reference_dir,
)


class TestXYZSerializer:
    def test_serialize(self):
        output_file = test_output_dir / "test_serialize.xyz"
        reference_file = test_reference_dir / "xyz" / "test.xyz"

        data = {
            "points": [
                XYZPoint(x=1.232, y=2.343, z=3.454),
                XYZPoint(x=4.565, y=5.676, z=6.787, comment="Some comment"),
            ]
        }

        config = SerializerConfig(float_format=".2f")

        XYZSerializer.serialize(output_file, data, config, ModelSaveSettings())

        assert_files_equal(output_file, reference_file)


class TestXYZModel:
    def test_save(self):
        output_file = test_output_dir / "test_save.xyz"
        reference_file = test_reference_dir / "xyz" / "test.xyz"

        points = [
            XYZPoint(x=1.232, y=2.343, z=3.454),
            XYZPoint(x=4.565, y=5.676, z=6.787, comment="Some comment"),
        ]
        model = XYZModel(points=points)

        if output_file.is_file():
            output_file.unlink()

        model.filepath = output_file
        model.serializer_config.float_format = ".2f"

        assert not model.filepath.is_file()
        model.save()
        assert model.filepath.is_file()

        assert_files_equal(output_file, reference_file)

    def test_xyz_parser_correct_amount_of_points(self):
        fn = test_input_dir / "dflowfm_individual_files" / "test.xyz"
        data = XYZParser.parse(fn)
        assert "points" in data
        assert len(data.get("points", [])) == 7

    def test_load_correct_file(self):
        input_file = test_input_dir / "dflowfm_individual_files" / "sample.xyz"
        model = XYZModel(filepath=input_file)

        points = [
            XYZPoint(x=37115.2500000, y=419886.6875000, z=500.0000000),
            XYZPoint(x=1, y=10, z=100),
            XYZPoint(x=2, y=20, z=200),
            XYZPoint(x=3, y=30, z=300),
            XYZPoint(x=4, y=40, z=400, comment="fourth sample point"),
        ]

        assert len(model.points) == len(points)
        assert model.points == points

    def test_load_wrong_file(self):
        input_file = test_input_dir / "invalid_files" / "invalidsample.xyz"

        with pytest.raises(ValueError) as error:
            _ = XYZModel(filepath=input_file)

        expected_message = f"Error parsing XYZ file '{input_file}', line 3."
        assert expected_message in str(error.value)
