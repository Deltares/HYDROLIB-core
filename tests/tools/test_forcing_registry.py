"""Unit tests of `ForcingFileRegistry`, which makes blocks that write one `.bc` share a model."""

import warnings
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm.bc.models import ForcingModel, TimeSeries
from hydrolib.core.dflowfm.ext.models import Boundary, ExtModel
from hydrolib.tools.extforce_convert.forcing_registry import (
    FORCING_BLOCK_LIST_NAMES,
    ForcingFileRegistry,
)


pytestmark = pytest.mark.unit


class _ThreeFieldBlock(BaseModel):
    """Stands in for a source/sink: one model held by three fields."""

    discharge: Any = None
    salinity: Any = None
    temperature: Any = None


def _forcing_model(
    filepath: Path, quantity: str, name: str = "A_0001"
) -> ForcingModel:
    series = TimeSeries(
        name=name,
        timeInterpolation="linear",
        quantityunitpair=[
            {"quantity": "time", "unit": "minutes since 2020-01-01"},
            {"quantity": quantity, "unit": "-"},
        ],
        datablock=[[0, 1], [10, 2]],
    )
    model = ForcingModel(forcing=[series])
    model.filepath = filepath

    return model


def _boundary(tmp_path: Path, quantity: str, forcing_file: Any) -> Boundary:
    return Boundary(
        quantity=quantity,
        locationfile=tmp_path / "A.pli",
        forcingfile=forcing_file,
    )


def _quantities(model: ForcingModel) -> list[str]:
    return [
        pair.quantity
        for forcing in model.forcing
        for pair in forcing.quantityunitpair
        if pair.quantity != "time"
    ]


@pytest.fixture
def ext_model(tmp_path: Path) -> ExtModel:
    (tmp_path / "A.pli").write_text("A\n2 2\n0 0\n1 1\n")
    model = ExtModel()
    model.filepath = tmp_path / "new.ext"

    return model


class TestShare:
    def test_different_paths_are_left_alone(self, tmp_path: Path, ext_model: ExtModel):
        registry = ForcingFileRegistry(ext_model)
        first = _boundary(tmp_path, "q1", _forcing_model(Path("A.bc"), "q1"))
        second = _boundary(tmp_path, "q2", _forcing_model(Path("B.bc"), "q2"))

        registry.share(first)
        registry.share(second)

        assert first.forcingfile is not second.forcingfile
        assert _quantities(first.forcingfile) == ["q1"]
        assert _quantities(second.forcingfile) == ["q2"]

    def test_same_path_shares_one_model_with_every_quantity(
        self, tmp_path: Path, ext_model: ExtModel
    ):
        registry = ForcingFileRegistry(ext_model)
        first = _boundary(tmp_path, "q1", _forcing_model(Path("A.bc"), "q1"))
        second = _boundary(tmp_path, "q2", _forcing_model(Path("A.bc"), "q2"))

        registry.share(first)
        registry.share(second)

        assert second.forcingfile is first.forcingfile
        assert _quantities(first.forcingfile) == ["q1", "q2"]

    def test_forcing_equal_to_an_existing_one_is_not_added_again(
        self, tmp_path: Path, ext_model: ExtModel
    ):
        registry = ForcingFileRegistry(ext_model)
        first = _boundary(tmp_path, "q1", _forcing_model(Path("A.bc"), "q1"))
        same = _boundary(tmp_path, "q1", _forcing_model(Path("A.bc"), "q1"))

        registry.share(first)
        registry.share(same)

        assert same.forcingfile is first.forcingfile
        assert _quantities(first.forcingfile) == ["q1"]

    def test_one_model_held_by_three_fields_is_merged_once(
        self, tmp_path: Path, ext_model: ExtModel
    ):
        registry = ForcingFileRegistry(ext_model)
        first = _boundary(tmp_path, "q1", _forcing_model(Path("A.bc"), "q1"))
        source = _forcing_model(Path("A.bc"), "q2")
        block = _ThreeFieldBlock(discharge=source, salinity=source, temperature=source)

        registry.share(first)
        registry.share(block)

        assert block.discharge is first.forcingfile
        assert block.salinity is first.forcingfile
        assert block.temperature is first.forcingfile
        assert _quantities(first.forcingfile) == ["q1", "q2"]

    def test_block_of_the_existing_ext_model_is_the_target(
        self, tmp_path: Path, ext_model: ExtModel
    ):
        existing = _boundary(tmp_path, "q1", _forcing_model(Path("A.bc"), "q1"))
        ext_model.boundary = [existing]
        registry = ForcingFileRegistry(ext_model)
        new = _boundary(tmp_path, "q2", _forcing_model(Path("A.bc"), "q2"))

        registry.share(new)

        assert new.forcingfile is existing.forcingfile
        assert _quantities(existing.forcingfile) == ["q1", "q2"]


class TestExistingPlaceholder:
    """The existing new ext holds a `DiskOnlyFileModel` for the `.bc` its blocks reference."""

    def test_existing_file_is_parsed_and_merged_into(
        self, tmp_path: Path, ext_model: ExtModel
    ):
        _forcing_model(tmp_path / "A.bc", "q1").save()
        existing = _boundary(tmp_path, "q1", DiskOnlyFileModel(Path("A.bc")))
        ext_model.boundary = [existing]
        registry = ForcingFileRegistry(ext_model)
        new = _boundary(tmp_path, "q2", _forcing_model(Path("A.bc"), "q2"))

        registry.share(new)

        assert isinstance(existing.forcingfile, ForcingModel)
        assert new.forcingfile is existing.forcingfile
        assert existing.forcingfile.filepath == Path("A.bc")
        assert _quantities(existing.forcingfile) == ["q1", "q2"]

    def test_missing_file_leaves_the_placeholder_and_keeps_the_new_model(
        self, tmp_path: Path, ext_model: ExtModel
    ):
        existing = _boundary(tmp_path, "q1", DiskOnlyFileModel(Path("A.bc")))
        ext_model.boundary = [existing]
        registry = ForcingFileRegistry(ext_model)
        new = _boundary(tmp_path, "q2", _forcing_model(Path("A.bc"), "q2"))

        registry.share(new)

        assert isinstance(existing.forcingfile, DiskOnlyFileModel)
        assert _quantities(new.forcingfile) == ["q2"]

    def test_blocks_converted_after_a_missing_file_still_share_one_model(
        self, tmp_path: Path, ext_model: ExtModel
    ):
        existing = _boundary(tmp_path, "q1", DiskOnlyFileModel(Path("A.bc")))
        ext_model.boundary = [existing]
        registry = ForcingFileRegistry(ext_model)
        first = _boundary(tmp_path, "q2", _forcing_model(Path("A.bc"), "q2"))
        second = _boundary(tmp_path, "q3", _forcing_model(Path("A.bc"), "q3"))

        registry.share(first)
        registry.share(second)

        assert second.forcingfile is first.forcingfile
        assert _quantities(first.forcingfile) == ["q2", "q3"]


    def test_merging_into_an_existing_file_warns_that_it_is_rewritten(
        self, tmp_path: Path, ext_model: ExtModel
    ):
        _forcing_model(tmp_path / "A.bc", "q1").save()
        existing = _boundary(tmp_path, "q1", DiskOnlyFileModel(Path("A.bc")))
        ext_model.boundary = [existing]
        registry = ForcingFileRegistry(ext_model)
        new = _boundary(tmp_path, "q2", _forcing_model(Path("A.bc"), "q2"))

        with pytest.warns(UserWarning, match="is rewritten") as recorded:
            registry.share(new)

        assert str(tmp_path / "A.bc") in str(recorded[0].message)

    def test_no_warning_when_the_file_does_not_exist_yet(
        self, tmp_path: Path, ext_model: ExtModel
    ):
        existing = _boundary(tmp_path, "q1", DiskOnlyFileModel(Path("A.bc")))
        ext_model.boundary = [existing]
        registry = ForcingFileRegistry(ext_model)
        new = _boundary(tmp_path, "q2", _forcing_model(Path("A.bc"), "q2"))

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            registry.share(new)

    def test_unparsable_existing_file_raises_a_clear_error(
        self, tmp_path: Path, ext_model: ExtModel
    ):
        (tmp_path / "A.bc").write_text("[Forcing]\nname = X\nnot a valid bc file\n")
        existing = _boundary(tmp_path, "q1", DiskOnlyFileModel(Path("A.bc")))
        ext_model.boundary = [existing]
        registry = ForcingFileRegistry(ext_model)
        new = _boundary(tmp_path, "q2", _forcing_model(Path("A.bc"), "q2"))

        with pytest.raises(ValueError, match="could not be parsed") as error:
            registry.share(new)

        assert str(tmp_path / "A.bc") in str(error.value)
        assert isinstance(existing.forcingfile, DiskOnlyFileModel)


class TestFieldsThatAreIgnored:
    def test_forcing_model_without_a_path_is_not_shared(
        self, tmp_path: Path, ext_model: ExtModel
    ):
        registry = ForcingFileRegistry(ext_model)
        first = _boundary(tmp_path, "q1", _forcing_model(Path("A.bc"), "q1"))
        first.forcingfile.filepath = None
        second = _boundary(tmp_path, "q2", _forcing_model(Path("A.bc"), "q2"))
        second.forcingfile.filepath = None

        registry.share(first)
        registry.share(second)

        assert first.forcingfile is not second.forcingfile
        assert _quantities(first.forcingfile) == ["q1"]
        assert _quantities(second.forcingfile) == ["q2"]

    def test_unrelated_placeholders_are_not_parsed(
        self, tmp_path: Path, ext_model: ExtModel
    ):
        """A placeholder is only parsed when a new block writes the same path."""
        _forcing_model(tmp_path / "X.bc", "q1").save()
        existing = _boundary(tmp_path, "q1", DiskOnlyFileModel(Path("X.bc")))
        ext_model.boundary = [existing]
        registry = ForcingFileRegistry(ext_model)
        new = _boundary(tmp_path, "q2", _forcing_model(Path("B.bc"), "q2"))

        registry.share(new)

        assert isinstance(existing.forcingfile, DiskOnlyFileModel)
        assert isinstance(existing.locationfile, DiskOnlyFileModel)
        assert _quantities(new.forcingfile) == ["q2"]

    def test_sharing_the_same_block_twice_changes_nothing(
        self, tmp_path: Path, ext_model: ExtModel
    ):
        registry = ForcingFileRegistry(ext_model)
        block = _boundary(tmp_path, "q1", _forcing_model(Path("A.bc"), "q1"))

        registry.share(block)
        registry.share(block)

        assert _quantities(block.forcingfile) == ["q1"]


class TestRegistryIndex:
    def test_first_existing_block_wins_for_a_path(
        self, tmp_path: Path, ext_model: ExtModel
    ):
        first = _boundary(tmp_path, "q1", _forcing_model(Path("A.bc"), "q1"))
        second = _boundary(tmp_path, "q2", _forcing_model(Path("A.bc"), "q2"))
        ext_model.boundary = [first, second]
        registry = ForcingFileRegistry(ext_model)
        new = _boundary(tmp_path, "q3", _forcing_model(Path("A.bc"), "q3"))

        registry.share(new)

        assert new.forcingfile is first.forcingfile
        assert _quantities(first.forcingfile) == ["q1", "q3"]
        assert _quantities(second.forcingfile) == ["q2"]

    def test_block_lists_are_attributes_of_the_ext_model(self, ext_model: ExtModel):
        """Guards against a renamed list in `ExtModel` silently dropping blocks from the index."""
        for list_name in FORCING_BLOCK_LIST_NAMES:
            assert isinstance(getattr(ext_model, list_name), list)


class TestAppendMissingForcings:
    def test_appends_only_the_forcings_the_shared_model_lacks_in_order(self):
        first = _forcing_model(Path("A.bc"), "q1", name="P_0001").forcing[0]
        second = _forcing_model(Path("A.bc"), "q2", name="P_0001").forcing[0]
        third = _forcing_model(Path("A.bc"), "q3", name="P_0001").forcing[0]
        shared_model = ForcingModel(forcing=[first])
        new_model = ForcingModel(forcing=[first, second, third])

        ForcingFileRegistry._append_missing_forcings(shared_model, new_model)

        assert shared_model.forcing == [first, second, third]

    def test_nothing_is_appended_when_the_new_model_has_no_forcings(self):
        first = _forcing_model(Path("A.bc"), "q1").forcing[0]
        shared_model = ForcingModel(forcing=[first])

        ForcingFileRegistry._append_missing_forcings(shared_model, ForcingModel())

        assert shared_model.forcing == [first]

    def test_the_new_model_is_left_unchanged(self):
        first = _forcing_model(Path("A.bc"), "q1").forcing[0]
        second = _forcing_model(Path("A.bc"), "q2").forcing[0]
        shared_model = ForcingModel(forcing=[first])
        new_model = ForcingModel(forcing=[first, second])

        ForcingFileRegistry._append_missing_forcings(shared_model, new_model)

        assert new_model.forcing == [first, second]

    def test_a_forcing_repeated_in_the_new_model_is_appended_once(self):
        first = _forcing_model(Path("A.bc"), "q1").forcing[0]
        repeated = _forcing_model(Path("A.bc"), "q2").forcing[0]
        shared_model = ForcingModel(forcing=[first])
        new_model = ForcingModel(forcing=[repeated, repeated])

        ForcingFileRegistry._append_missing_forcings(shared_model, new_model)

        assert shared_model.forcing == [first, repeated]


class TestGetForcingModelOrDiskOnlyFields:
    def test_returns_the_fields_holding_a_forcing_model_or_a_placeholder(
        self, tmp_path: Path
    ):
        forcing_model = _forcing_model(Path("A.bc"), "q1")
        placeholder = DiskOnlyFileModel(Path("B.bc"))
        block = _ThreeFieldBlock(
            discharge=forcing_model, salinity=placeholder, temperature=1.5
        )

        fields = ForcingFileRegistry._get_forcing_model_or_disk_only_fields(block)

        assert fields == [("discharge", forcing_model), ("salinity", placeholder)]

    def test_skips_models_and_placeholders_without_a_path(self):
        block = _ThreeFieldBlock(
            discharge=ForcingModel(),
            salinity=DiskOnlyFileModel(None),
            temperature=_forcing_model(Path("A.bc"), "q1"),
        )

        fields = ForcingFileRegistry._get_forcing_model_or_disk_only_fields(block)

        assert [field_name for field_name, _ in fields] == ["temperature"]

    def test_skips_values_of_other_types(self):
        block = _ThreeFieldBlock(discharge="text", salinity=None, temperature=3)

        fields = ForcingFileRegistry._get_forcing_model_or_disk_only_fields(block)

        assert fields == []

    def test_returns_the_fields_in_declaration_order(self):
        first = _forcing_model(Path("A.bc"), "q1")
        second = _forcing_model(Path("B.bc"), "q2")
        block = _ThreeFieldBlock(discharge=first, salinity=second, temperature=first)

        fields = ForcingFileRegistry._get_forcing_model_or_disk_only_fields(block)

        assert [field_name for field_name, _ in fields] == [
            "discharge",
            "salinity",
            "temperature",
        ]

