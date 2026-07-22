from math import nan
from typing import List

import pytest
from pydantic import ValidationError

from hydrolib.core.dflowfm.crosssection.models import CrossDefModel, CrossLocModel
from hydrolib.core.dflowfm.ext.models import ExtModel
from hydrolib.core.dflowfm.friction.models import FrictionModel
from hydrolib.core.dflowfm.ini.models import DataBlockINIBasedModel, INIBasedModel
from hydrolib.core.dflowfm.structure.models import StructureModel, Weir
from tests.utils import error_occurs_only_once


class TestDataBlockINIBasedModel:
    def test_datablock_with_nan_values_should_raise_error(self):
        model = DataBlockINIBasedModel()

        with pytest.raises(ValidationError) as error:
            model.datablock = [[nan, 0], [-1, 2]]

        expected_message = "NaN is not supported in datablocks."
        assert expected_message in str(error.value)

    def test_updating_datablock_with_nan_values_should_raise_error(self):
        model = DataBlockINIBasedModel()

        valid_datablock = [[0, 1], [2, 3]]
        model.datablock = valid_datablock

        invalid_datablock = [[nan, 1], [2, 3]]
        with pytest.raises(ValidationError) as error:
            model.datablock = invalid_datablock

        expected_message = "NaN is not supported in datablocks."
        assert expected_message in str(error.value)

    def test_datablock_with_multiple_nans_should_only_give_error_once(self):
        model = DataBlockINIBasedModel()

        with pytest.raises(ValidationError) as error:
            model.datablock = [[nan, nan], [nan, nan]]

        expected_message = "NaN is not supported in datablocks."
        assert error_occurs_only_once(expected_message, str(error.value))

    def test_as_dataframe(self):
        model = DataBlockINIBasedModel()

        valid_datablock = [[0, 1], [2, 3]]
        model.datablock = valid_datablock
        df = model.as_dataframe()
        assert df.loc[:, 0].to_list() == [1.0, 3.0]


class TestINIBasedModel:
    class INIBasedModelTest(INIBasedModel):
        id: str
        float_value: float
        float_values: List[float]

    _random_string: str = "randomString"
    _random_float: float = 123.456
    _random_list_of_floats: List[float] = [12.34, 56.78]

    @pytest.mark.parametrize("string_value", ["1d0", "1d-2", "1d+2", "1.d+2", "-1.d-2"])
    def test_scientific_notation_for_string_field_is_parsed_as_string(
        self, string_value: str
    ):

        test_model = self.INIBasedModelTest(
            id=string_value,
            float_value=self._random_float,
            float_values=self._random_list_of_floats,
        )

        assert test_model.id == string_value
        assert test_model.float_value == pytest.approx(self._random_float)
        assert test_model.float_values == pytest.approx(self._random_list_of_floats)

    @pytest.mark.parametrize(
        "float_as_string, expected_value",
        [
            ("1d0", 1e0),
            ("1d-2", 1e-2),
            ("1d+2", 1e2),
            ("1.d+2", 1.0e2),
            ("-1.d-2", -1.0e-2),
        ],
    )
    def test_scientific_notation_for_float_field_is_parsed_as_float(
        self, float_as_string: str, expected_value: float
    ):
        test_model = self.INIBasedModelTest(
            id=self._random_string,
            float_value=float_as_string,
            float_values=self._random_list_of_floats,
        )

        assert test_model.id == self._random_string
        assert test_model.float_value == pytest.approx(expected_value)
        assert test_model.float_values == pytest.approx(self._random_list_of_floats)

    @pytest.mark.parametrize(
        "floats_as_strings, expected_values",
        [
            (["1d0", "1d-2"], [1e0, 1e-2]),
            (["1d+2", "1.d+2", "-1.d-2"], [1e2, 1.0e2, -1.0e-2]),
        ],
    )
    def test_scientific_notation_for_list_of_float_field_is_parsed_as_list_of_floats(
        self, floats_as_strings: List[str], expected_values: List[float]
    ):
        test_model = self.INIBasedModelTest(
            id=self._random_string,
            float_value=self._random_float,
            float_values=floats_as_strings,
        )

        assert test_model.id == self._random_string
        assert test_model.float_value == pytest.approx(self._random_float)
        assert test_model.float_values == pytest.approx(expected_values)

    def test_setting_string_attribute_with_scientific_notation_correctly_parses_value(
        self,
    ):
        test_model = self.INIBasedModelTest(
            id=self._random_string,
            float_value=self._random_float,
            float_values=self._random_list_of_floats,
        )

        test_model.id = "1d1"

        assert test_model.id == "1d1"

    def test_setting_float_attribute_with_scientific_notation_correctly_parses_value(
        self,
    ):
        test_model = self.INIBasedModelTest(
            id=self._random_string,
            float_value=self._random_float,
            float_values=self._random_list_of_floats,
        )

        test_model.float_value = "1d1"

        assert test_model.float_value == pytest.approx(1e1)

    def test_setting_list_of_floats_attribute_with_scientific_notation_correctly_parses_values(
        self,
    ):
        test_model = self.INIBasedModelTest(
            id=self._random_string,
            float_value=self._random_float,
            float_values=self._random_list_of_floats,
        )

        test_model.float_values = ["1d1", "2d-1"]

        assert test_model.float_values == pytest.approx([1e1, 2e-1])


class TestINIBasedModelEquality:
    """Regression tests for Pydantic equality on INI-based file models.

    `IniBasedModel` holds a `FilePathStyleConverter` as a Pydantic private
    attribute. If that helper compares by identity, two freshly built
    instances of any INI-based model fail `==`, which surprises users who
    expect value-based equality (issue #1055).
    """

    @pytest.mark.parametrize(
        "model_cls",
        [
            INIBasedModel,
            StructureModel,
            ExtModel,
            CrossDefModel,
            CrossLocModel,
            FrictionModel,
        ],
    )
    def test_two_empty_models_are_equal(self, model_cls):
        assert model_cls() == model_cls()

    def test_two_populated_structure_models_are_equal(self):
        # Populated case: same INI-based model class with the same nested
        # content must also compare equal, not only fresh empty instances.
        weir_kwargs = dict(
            id="w1",
            branchid="b1",
            chainage=1.0,
            crestlevel=0.0,
            allowedflowdir="positive",
        )
        a = StructureModel(structure=[Weir(**weir_kwargs)])
        b = StructureModel(structure=[Weir(**weir_kwargs)])
        assert a == b

    def test_populated_structure_models_with_different_content_differ(self):
        # Sanity check: two populated models that differ on a public field
        # must compare unequal, so the equality contract is not trivially
        # satisfied by all populated instances.
        base = dict(
            branchid="b1",
            chainage=1.0,
            crestlevel=0.0,
            allowedflowdir="positive",
        )
        a = StructureModel(structure=[Weir(id="w1", **base)])
        b = StructureModel(structure=[Weir(id="w2", **base)])
        assert a != b


class TestINIBasedModelCommentsReset:
    """Tests that comments are always reset to their default values on
    initialization (via _skip_nones_and_set_header validator), regardless
    of what comment values are passed in during construction."""

    class ModelWithComments(INIBasedModel):
        class Comments(INIBasedModel.Comments):
            field_a: str | None = "Default comment for field_a."
            field_b: str | None = "Default comment for field_b."

        comments: Comments = Comments()
        field_a: str = "value_a"
        field_b: str = "value_b"

    def test_comments_with_all_fields_overridden_are_reset_to_defaults(self):
        custom_comments = self.ModelWithComments.Comments(
            field_a="Overridden A", field_b="Overridden B"
        )
        model = self.ModelWithComments(comments=custom_comments)
        assert model.comments == self.ModelWithComments.Comments()

    def test_comments_with_all_fields_set_to_none_are_reset_to_defaults(self):
        empty_comments = self.ModelWithComments.Comments(field_a=None, field_b=None)
        model = self.ModelWithComments(comments=empty_comments)
        assert model.comments == self.ModelWithComments.Comments()

    def test_comments_with_partial_override_are_reset_to_defaults(self):
        partial_comments = self.ModelWithComments.Comments(field_a="Only A changed")
        model = self.ModelWithComments(comments=partial_comments)
        assert model.comments == self.ModelWithComments.Comments()

    def test_comments_with_extra_fields_are_reset_to_defaults(self):
        # Comments allows extra fields (extra="allow"); they must still be discarded.
        comments_with_extra = self.ModelWithComments.Comments(
            field_a="Overridden A", unknown_extra="some extra comment"
        )
        model = self.ModelWithComments(comments=comments_with_extra)
        assert model.comments == self.ModelWithComments.Comments()

    def test_comments_default_values_are_preserved_when_no_comments_provided(self):
        model = self.ModelWithComments()
        assert model.comments == self.ModelWithComments.Comments()
