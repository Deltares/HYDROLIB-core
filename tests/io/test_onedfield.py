import inspect
from typing import List, Optional

import pytest
from pydantic.error_wrappers import ValidationError

from hydrolib.core.io.ini.parser import Parser, ParserConfig
from hydrolib.core.io.onedfield.models import (
    OneDFieldBranch,
    OneDFieldGlobal,
    OneDFieldModel,
)

from ..utils import WrapperTest, test_data_dir


class TestOneDField:
    def test_onedfield_model(self):
        filepath = test_data_dir / "input/dflowfm_individual_files/1dfield.ini"
        m = OneDFieldModel(filepath)
        assert len(m.branch) == 2

        assert isinstance(m.global_, OneDFieldGlobal)
        assert m.global_.quantity == "waterDepth"
        assert m.global_.unit == "m"
        assert m.global_.value == 10

        assert isinstance(m.branch[0], OneDFieldBranch)
        assert m.branch[0].branchid == "Channel1"
        assert m.branch[0].numlocations == 2
        assert m.branch[0].chainage == [0.0, 100.0]
        assert m.branch[0].values == [7, 7.5]

        assert isinstance(m.branch[1], OneDFieldBranch)
        assert m.branch[1].branchid == "Channel4"
        assert m.branch[1].numlocations == 0
        assert m.branch[1].values == [8.0]

    def test_given_text_parses_branch(self):
        field_text = inspect.cleandoc(
            """
            [Branch]
            branchId = Channel1 # overrule for Channel1
            numLocations = 2 # at two locations
            chainage = 0.000 100.000
            values = 7.000 7.500 # 7 at 0m and 7.5 at 100m
            """
        )

        # 2. Parse data.
        parser = Parser(ParserConfig())
        for line in field_text.splitlines():
            parser.feed_line(line)
        document = parser.finalize()

        fb = WrapperTest[OneDFieldBranch].parse_obj({"val": document.sections[0]}).val

        assert fb
        assert isinstance(fb, OneDFieldBranch)
        assert fb.branchid == "Channel1"
        assert fb.numlocations == 2
        assert fb.chainage == [0, 100]
        assert fb.values == [7, 7.5]

    @pytest.mark.parametrize(
        "numlocations,chainage,values",
        [
            (1, [2.3], [45]),
            (None, None, [45]),
            (2, [2.3, 3.4], [45, 67]),
        ],
    )
    def test_create_a_onedfieldbranch_from_scratch(
        self,
        numlocations: Optional[int],
        chainage: Optional[List[float]],
        values: List[float],
    ):
        fb = OneDFieldBranch(
            branchid="B1",
            numlocations=numlocations,
            chainage=chainage,
            values=values,
        )
        assert fb.branchid == "B1"
        assert fb.numlocations == (numlocations or 0)
        assert fb.chainage == chainage
        assert fb.values == values

    def test_create_a_frictbranch_with_incorrect_levels_or_locations(self):
        branchid = "B1"
        with pytest.raises(ValidationError) as error:
            _ = OneDFieldBranch(
                branchid=branchid,
                chainage=[10, 20],  # intentional wrong len(), should be 1
                values=[1.5, 2.5, 3.5],  # intentional wrong len(), should be 1
            )
        expected_message0 = (
            f"Number of values for chainage should be equal to the numlocations value."
        )
        expected_message1 = f"Number of values for values should be equal to the numlocations value (and at least 1)."

        assert expected_message0 in str(error.value)
        assert expected_message1 in str(error.value)
