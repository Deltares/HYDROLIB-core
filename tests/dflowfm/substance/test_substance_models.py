from hydrolib.core.dflowfm.substance import Substance


def test_instantiation():
    substance_data = {
        "name": "substance1",
        "type": "Active",
        "description": "This is a test substance.",
        "concentration_unit": "mg/L",
        "waste_load_unit": "kg/day",
    }
    substance = Substance(**substance_data)
    assert substance.name == "substance1"