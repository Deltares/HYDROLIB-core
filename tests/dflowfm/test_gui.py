import pytest
from pydantic import ValidationError

from hydrolib.core.dflowfm.gui.models import Branch, BranchModel


def _create_branch_values():

    return dict(
        name="some_branch_name",
        branchtype="2",
        islengthcustom="true",
        sourcecompartmentname="some_source_comp_name",
        targetcompartmentname="some_target_comp_name",
        material="3",
    )


class TestBranch:
    def test_create_branch(self):
        branch = Branch(**_create_branch_values())

        assert branch.name == "some_branch_name"
        assert branch.branchtype == 2
        assert branch.islengthcustom == True
        assert branch.sourcecompartmentname == "some_source_comp_name"
        assert branch.targetcompartmentname == "some_target_comp_name"
        assert branch.material == 3

    def test_create_branch_invalid_material_raises_error(self):
        values = _create_branch_values()
        values["material"] = 10

        with pytest.raises(ValidationError) as error:
            _ = Branch(**values)

        expected_message = f"material (10) is not allowed. Allowed values: 0, 1, 2, 3, 4, 5, 6, 7, 8, 9"

        assert expected_message in str(error.value)

    def test_create_branch_invalid_branchtype_raises_error(self):
        values = _create_branch_values()
        values["branchtype"] = 3

        with pytest.raises(ValidationError) as error:
            _ = Branch(**values)

        expected_message = f"branchType (3) is not allowed. Allowed values: 0, 1, 2"

        assert expected_message in str(error.value)

    def test_create_branch_with_branchtype_2_without_compartment_data_raises_error(
        self,
    ):
        values = _create_branch_values()
        del values["sourcecompartmentname"]
        del values["targetcompartmentname"]

        with pytest.raises(ValidationError) as error:
            _ = Branch(**values)

        expected_message = "Either sourceCompartmentName or targetCompartmentName should be provided when branchType is 2."

        assert expected_message in str(error.value)


class TestBranchModelValidator:

    def test_branchmodel_single_branch_dict(self):
        single_branch_input = {
            "branch": {
                "name": "b1",
                "branchType": 1,
                "isLengthCustom": True,
                "material": 2,
            }
        }

        model = BranchModel(**single_branch_input)
        assert isinstance(model.branch, list)
        assert len(model.branch) == 1
        assert model.branch[0].name == "b1"

    def test_branchmodel_list_of_branches(self):
        multi_branch_input = {
            "branch": [
                {"name": "b1", "branchType": 0, "material": 1},
                {
                    "name": "b2",
                    "branchType": 2,
                    "sourceCompartmentName": "sc1",
                    "material": 3,
                },
            ]
        }

        model = BranchModel(**multi_branch_input)
        assert isinstance(model.branch, list)
        assert len(model.branch) == 2
        assert model.branch[1].name == "b2"

    def test_branchmodel_invalid_branch_type(self):
        with pytest.raises(ValidationError):
            BranchModel(branch={"name": "b1", "branchType": 99})

    def test_branchmodel_invalid_branch_type_not_list_not_dict(self):
        with pytest.raises(TypeError):
            BranchModel(branch="anything else than a dict or list of dicts")
