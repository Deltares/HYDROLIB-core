from hydrolib.core.dflowfm.t3d.models import LayerType


class TestT3DModelAtrributes:

    def test_layer_type(self):
        layer_name = "SIGMA"
        layer_type = LayerType(layer_name)
        assert layer_type == "SIGMA"
