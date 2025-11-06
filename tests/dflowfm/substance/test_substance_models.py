from hydrolib.core.dflowfm.substance import Substance, Parameter, Output
from hydrolib.core.dflowfm.substance import ActiveProcesses, ActiveProcess


class TestSubstance:
    def test_instantiation(self):
        substance_data = {
            "name": "substance1",
            "type": "Active",
            "description": "This is a test substance.",
            "concentration_unit": "mg/L",
            "waste_load_unit": "kg/day",
        }
        substance = Substance(**substance_data)
        assert substance.name == "substance1"


class TestParameter:
    def test_instantiation(self):
        parameter_data = {
            "name": "parameter1",
            "description": "This is a test parameter.",
            "unit": "mg/L",
            "value": "99",
        }
        parameter = Parameter(**parameter_data)
        assert parameter.name == "parameter1"


class TestOutput:
    def test_instantiation(self):
        output_data = {
            "name": "output1",
            "description": "This is a test output.",
        }
        output = Output(**output_data)
        assert output.name == "output1"


class TestActiveProcesses:

    def test_instantiation(self):
        active_process_data = {
            "name": "active_processes1",
            "description": "This is a test active processes.",
        }
        active_process = ActiveProcess(**active_process_data)
        assert active_process.name == "active_processes1"