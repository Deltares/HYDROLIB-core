from hydrolib.core.basemodel import SerializerConfig
from hydrolib.core.io.dflowfm.xyz.models import XYZPoint
from hydrolib.core.io.dflowfm.xyz.serializer import XYZSerializer
from tests.utils import assert_files_equal, test_output_dir, test_reference_dir


class TestXYZSerializer:
    def test_serialize(self):
        output_file = test_output_dir / "test.xyz"
        reference_file = test_reference_dir / "xyz" / "test.xyz"

        data = {
            "points": [
                XYZPoint(x=1.232, y=2.343, z=3.454),
                XYZPoint(x=4.565, y=5.676, z=6.787, comment="Some comment"),
            ]
        }

        config = SerializerConfig(float_format=".2f")

        XYZSerializer.serialize(output_file, data, config)

        assert_files_equal(output_file, reference_file)
