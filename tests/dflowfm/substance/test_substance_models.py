from pathlib import Path

import pytest

from hydrolib.core.dflowfm.substance import (
    ActiveProcess,
    ActiveProcesses,
    Output,
    Parameter,
    Substance,
    SubstanceModel,
    SubstanceType,
)


class TestSubstance:
    def test_instantiation(self):
        substance_data = {
            "name": "substance1",
            "type": "active",
            "description": "This is a test substance.",
            "concentration_unit": "mg/L",
            "waste_load_unit": "kg/day",
        }
        substance = Substance(**substance_data)
        assert substance.name == "substance1"
        assert substance.type == SubstanceType.Active

    def test_inactive_substance(self):
        substance = Substance(
            name="DetCS1",
            type="inactive",
            description="DetC in layer S1",
            concentration_unit="(gC/m2)",
        )
        assert substance.type == SubstanceType.Inactive


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
        assert parameter.value == 99.0


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

    def test_active_processes_container(self):
        procs = ActiveProcesses(
            processes=[
                ActiveProcess(name="proc1", description="desc1"),
                ActiveProcess(name="proc2", description="desc2"),
            ]
        )
        assert len(procs.processes) == 2


class TestSubstanceModel:
    def test_initialization_empty(self):
        model = SubstanceModel()
        assert len(model.substances) == 0
        assert len(model.parameters) == 0
        assert len(model.outputs) == 0
        assert len(model.active_processes.processes) == 0

    def test_load_from_file(self, input_files_dir: Path):
        path = input_files_dir / "substances" / "substance-file.sub"
        model = SubstanceModel(filepath=path)
        assert len(model.substances) == 2
        assert len(model.parameters) == 2
        assert len(model.outputs) == 2
        assert len(model.active_processes.processes) == 2

    def test_substance_values(self, input_files_dir: Path):
        path = input_files_dir / "substances" / "substance-file.sub"
        model = SubstanceModel(filepath=path)
        sub = model.substances[0]
        assert sub.name == "Any-substance-name-1"
        assert sub.type == SubstanceType.Active
        assert sub.description == "Any description here"
        assert sub.concentration_unit == "Any Unit"
        assert sub.waste_load_unit == "-"

    def test_parameter_fortran_notation(self, input_files_dir: Path):
        path = input_files_dir / "substances" / "substance-file.sub"
        model = SubstanceModel(filepath=path)
        param = model.parameters[0]
        assert param.name == "Any-Parameter-name-1"
        assert param.value == pytest.approx(-999.0)

    def test_output_values(self, input_files_dir: Path):
        path = input_files_dir / "substances" / "substance-file.sub"
        model = SubstanceModel(filepath=path)
        out = model.outputs[0]
        assert out.name == "Any-output-name-1"
        assert out.description == "Any description"

    def test_active_processes_values(self, input_files_dir: Path):
        path = input_files_dir / "substances" / "substance-file.sub"
        model = SubstanceModel(filepath=path)
        proc = model.active_processes.processes[0]
        assert proc.name == "Any-name-1"
        assert proc.description == "any description 1"

    def test_roundtrip(self, input_files_dir: Path, output_files_dir: Path):
        input_path = input_files_dir / "substances" / "substance-file.sub"
        output_path = output_files_dir / "substances" / "substance-file.sub"

        model = SubstanceModel(filepath=input_path)
        model.save(filepath=output_path)

        reloaded = SubstanceModel(filepath=output_path)
        assert len(reloaded.substances) == len(model.substances)
        assert len(reloaded.parameters) == len(model.parameters)
        assert len(reloaded.outputs) == len(model.outputs)
        assert len(reloaded.active_processes.processes) == len(
            model.active_processes.processes
        )

        # Verify values survive roundtrip
        for orig, rt in zip(model.substances, reloaded.substances):
            assert orig.name == rt.name
            assert orig.type == rt.type
            assert orig.concentration_unit == rt.concentration_unit

        for orig, rt in zip(model.parameters, reloaded.parameters):
            assert orig.name == rt.name
            assert orig.value == pytest.approx(rt.value)

    def test_save_creates_file(self, output_files_dir: Path):
        model = SubstanceModel()
        model.substances = [
            Substance(
                name="OXY",
                description="Dissolved Oxygen",
                concentration_unit="(g/m3)",
            )
        ]
        output_path = output_files_dir / "substances" / "test_save.sub"
        model.save(filepath=output_path)
        assert output_path.exists()
