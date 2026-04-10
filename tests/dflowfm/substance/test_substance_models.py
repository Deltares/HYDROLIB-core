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
        """Test creating a Substance with all fields.

        Test scenario:
            All fields provided, type should map to SubstanceType.Active enum.
        """
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
        """Test creating an inactive substance.

        Test scenario:
            Type 'inactive' should map to SubstanceType.Inactive.
        """
        substance = Substance(
            name="DetCS1",
            type="inactive",
            description="DetC in layer S1",
            concentration_unit="(gC/m2)",
        )
        assert substance.type == SubstanceType.Inactive

    def test_default_waste_load_unit(self):
        """Test that waste_load_unit defaults to '-' when not provided.

        Test scenario:
            Omitting waste_load_unit should default to '-'.
        """
        substance = Substance(
            name="OXY",
            description="Dissolved Oxygen",
            concentration_unit="(g/m3)",
        )
        assert (
            substance.waste_load_unit == "-"
        ), f"Expected '-', got '{substance.waste_load_unit}'"

    def test_default_type_is_active(self):
        """Test that type defaults to 'active' when not provided.

        Test scenario:
            Omitting type should default to SubstanceType.Active.
        """
        substance = Substance(
            name="OXY",
            description="Dissolved Oxygen",
            concentration_unit="(g/m3)",
        )
        assert (
            substance.type == SubstanceType.Active
        ), f"Expected Active, got {substance.type}"

    def test_is_active_returns_true_for_active_substance(self):
        """Test is_active returns True for an active substance.

        Test scenario:
            A substance with default type (active) should return True.
        """
        substance = Substance(
            name="OXY",
            description="Dissolved Oxygen",
            concentration_unit="(g/m3)",
        )
        assert substance.is_active() is True, (
            f"Expected is_active()=True for active substance, got {substance.is_active()}"
        )

    def test_is_active_returns_false_for_inactive_substance(self):
        """Test is_active returns False for an inactive substance.

        Test scenario:
            A substance with type='inactive' should return False.
        """
        substance = Substance(
            name="DetCS1",
            type="inactive",
            description="DetC in layer S1",
            concentration_unit="(gC/m2)",
        )
        assert substance.is_active() is False, (
            f"Expected is_active()=False for inactive substance, got {substance.is_active()}"
        )

    def test_is_active_with_explicit_active_type(self):
        """Test is_active returns True when type is explicitly set to 'active'.

        Test scenario:
            Explicitly passing type='active' should behave identically to the default.
        """
        substance = Substance(
            name="NH4",
            type="active",
            description="Ammonium",
            concentration_unit="(g/m3)",
        )
        assert substance.is_active() is True, (
            f"Expected is_active()=True for explicitly active substance, got {substance.is_active()}"
        )


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
        """Test that save creates the output file."""
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

    def test_load_empty_file(self, input_files_dir: Path):
        """Test loading an empty .sub file produces empty model.

        Test scenario:
            An empty file should load successfully with empty lists.
        """
        path = input_files_dir / "substances" / "empty-file.sub"
        model = SubstanceModel(filepath=path)
        assert (
            len(model.substances) == 0
        ), f"Expected 0 substances, got {len(model.substances)}"
        assert (
            len(model.parameters) == 0
        ), f"Expected 0 parameters, got {len(model.parameters)}"

    def test_load_inactive_substances(self, input_files_dir: Path):
        """Test loading file with active and inactive substances.

        Test scenario:
            First substance should be active, second inactive.
        """
        path = input_files_dir / "substances" / "inactive-substances.sub"
        model = SubstanceModel(filepath=path)
        assert model.substances[0].type == SubstanceType.Active
        assert model.substances[1].type == SubstanceType.Inactive

    def test_roundtrip_inactive_type(
        self, input_files_dir: Path, output_files_dir: Path
    ):
        """Test that inactive substance type survives roundtrip.

        Test scenario:
            Load → save → reload should preserve 'inactive' type.
        """
        input_path = input_files_dir / "substances" / "inactive-substances.sub"
        output_path = output_files_dir / "substances" / "inactive-roundtrip.sub"

        model = SubstanceModel(filepath=input_path)
        model.save(filepath=output_path)
        reloaded = SubstanceModel(filepath=output_path)

        assert (
            reloaded.substances[1].type == SubstanceType.Inactive
        ), f"Expected inactive, got {reloaded.substances[1].type}"

    def test_roundtrip_parameter_precision(
        self, input_files_dir: Path, output_files_dir: Path
    ):
        """Test that parameter values maintain precision through roundtrip.

        Test scenario:
            Scientific notation values should be numerically equivalent after roundtrip.
        """
        input_path = input_files_dir / "substances" / "only-parameters.sub"
        output_path = output_files_dir / "substances" / "precision-roundtrip.sub"

        model = SubstanceModel(filepath=input_path)
        model.save(filepath=output_path)
        reloaded = SubstanceModel(filepath=output_path)

        for orig, rt in zip(model.parameters, reloaded.parameters):
            assert orig.value == pytest.approx(
                rt.value
            ), f"Parameter {orig.name}: {orig.value} != {rt.value}"

    def test_load_nonexistent_file_raises(self):
        """Test that loading a non-existent file raises ValueError.

        Test scenario:
            Path pointing to a file that doesn't exist should raise.
        """
        with pytest.raises(ValueError, match="not found"):
            SubstanceModel(filepath=Path("nonexistent_dir/missing.sub"))

    def test_model_ext(self):
        """Test that SubstanceModel._ext returns '.sub'."""
        assert (
            SubstanceModel._ext() == ".sub"
        ), f"Expected '.sub', got '{SubstanceModel._ext()}'"

    def test_model_filename(self):
        """Test that SubstanceModel._filename returns 'substance'."""
        assert (
            SubstanceModel._filename() == "substance"
        ), f"Expected 'substance', got '{SubstanceModel._filename()}'"

    def test_get_active_substances_empty_model(self):
        """Test get_active_substances on an empty model.

        Test scenario:
            A model with no substances should return an empty list.
        """
        model = SubstanceModel()
        result = model.get_active_substances()
        assert result == [], f"Expected empty list, got {result}"

    def test_get_active_substances_all_active(self):
        """Test get_active_substances when all substances are active.

        Test scenario:
            A model with only active substances should return all of them.
        """
        substances = [
            Substance(name="OXY", description="Oxygen", concentration_unit="(g/m3)"),
            Substance(name="NH4", description="Ammonium", concentration_unit="(g/m3)"),
        ]
        model = SubstanceModel()
        model.substances = substances
        result = model.get_active_substances()
        assert len(result) == 2, f"Expected 2 active substances, got {len(result)}"

    def test_get_active_substances_all_inactive(self):
        """Test get_active_substances when all substances are inactive.

        Test scenario:
            A model with only inactive substances should return an empty list.
        """
        substances = [
            Substance(
                name="DetCS1", type="inactive",
                description="DetC S1", concentration_unit="(gC/m2)",
            ),
            Substance(
                name="DetCS2", type="inactive",
                description="DetC S2", concentration_unit="(gC/m2)",
            ),
        ]
        model = SubstanceModel()
        model.substances = substances
        result = model.get_active_substances()
        assert result == [], f"Expected empty list, got {len(result)} substances"

    def test_get_active_substances_mixed(self):
        """Test get_active_substances with a mix of active and inactive.

        Test scenario:
            Only active substances should be returned, preserving order.
        """
        substances = [
            Substance(name="OXY", description="Oxygen", concentration_unit="(g/m3)"),
            Substance(
                name="DetCS1", type="inactive",
                description="DetC S1", concentration_unit="(gC/m2)",
            ),
            Substance(name="NH4", description="Ammonium", concentration_unit="(g/m3)"),
        ]
        model = SubstanceModel()
        model.substances = substances
        result = model.get_active_substances()
        assert len(result) == 2, f"Expected 2 active substances, got {len(result)}"
        assert result[0].name == "OXY", f"Expected 'OXY', got '{result[0].name}'"
        assert result[1].name == "NH4", f"Expected 'NH4', got '{result[1].name}'"

    def test_get_active_substances_from_file(self, input_files_dir: Path):
        """Test get_active_substances on a model loaded from file.

        Test scenario:
            inactive-substances.sub has 1 active + 1 inactive substance.
            Only the active one should be returned.
        """
        path = input_files_dir / "substances" / "inactive-substances.sub"
        model = SubstanceModel(filepath=path)
        result = model.get_active_substances()
        assert len(result) == 1, f"Expected 1 active substance, got {len(result)}"
        assert result[0].name == "ActiveSub", f"Expected 'ActiveSub', got '{result[0].name}'"
