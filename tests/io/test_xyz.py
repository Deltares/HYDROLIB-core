from hydrolib.core.io.xyz.models import XYZModel, XYZPoint


class TestXYZModel:
    def test_xyz_values_returns_correct_result(self):
        xyz_model = XYZModel(
            points=[
                XYZPoint(x=1.0, y=1.0, z=1.0),
                XYZPoint(x=2.0, y=1.0, z=2.0),
                XYZPoint(x=2.0, y=2.0, z=3.0),
                XYZPoint(x=1.5, y=2.5, z=4.0),
                XYZPoint(x=1.0, y=2.0, z=5.0),
            ],
        )

        values = xyz_model.xyz_values

        assert values.x == [1.0, 2.0, 2.0, 1.5, 1.0]
        assert values.y == [1.0, 1.0, 2.0, 2.5, 2.0]
        assert values.z == [1.0, 2.0, 3.0, 4.0, 5.0]