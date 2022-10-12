from hydrolib.core.io.common.models import XYZValues


class TestXYZValues:
    def test_constructor(self):
        values = XYZValues()

        assert values.x is not None
        assert len(values.x) == 0
        assert values.y is not None
        assert len(values.y) == 0
        assert values.z is not None
        assert len(values.z) == 0