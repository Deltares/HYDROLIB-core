from pathlib import Path

from hydrolib.tools.ext_bnd_items_old_to_new import ext_bnd_items_old_to_new


class TestOldBndToNew:
    def test_convert_old_bnd_to_new(self):
        supported_quantities = {
            "waterlevelbnd": "m",
            "dischargebnd": "m3/s",
            "salinitybnd": "ppt",
            "temperaturebnd": "°C",
        }
        ext_force_old_filename = Path(
            "c:/checkouts/delft3d/test/deltares_testbench/data/cases/c01_harlingen/001.ext"
        )
        ext_force_new_filename = Path(
            "c:/checkouts/delft3d/test/deltares_testbench/data/cases/c01_harlingen/001_new.ext"
        )
        ext_bnd_items_old_to_new(
            ext_force_old_filename, ext_force_new_filename, supported_quantities
        )
        assert 0 == 0

    #   pair = QuantityUnitPair(quantity="some_quantity", unit="some_unit")
    #   assert isinstance(pair, BaseModel)
    #   assert pair.quantity == "some_quantity"
    #   assert pair.vertpositionindex is None
