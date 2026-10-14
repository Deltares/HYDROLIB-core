"""Unit tests of `ForcingFileRegistry`, which makes blocks that write one `.bc` share a model."""

from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm.bc.models import ForcingModel, TimeSeries
from hydrolib.core.dflowfm.ext.models import Boundary, ExtModel
from hydrolib.tools.extforce_convert.forcing_registry import (
    ForcingFileRegistry,
    _ForcingFileFieldRef,
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


class TestForcingFileFieldRef:
    def test_value_reads_the_current_field_of_the_block(self, tmp_path: Path):
        block = _ThreeFieldBlock(discharge="first")

        field_ref = _ForcingFileFieldRef(block, "discharge")

        assert field_ref.value == "first"

        block.discharge = "second"

        assert field_ref.value == "second"

    def test_replace_writes_the_field_of_the_block(self, tmp_path: Path):
        block = _ThreeFieldBlock(discharge="first", salinity="other")
        field_ref = _ForcingFileFieldRef(block, "discharge")

        field_ref.replace("second")

        assert block.discharge == "second"
        assert block.salinity == "other"

    def test_refs_to_the_same_field_are_equal(self, tmp_path: Path):
        block = _ThreeFieldBlock()

        assert _ForcingFileFieldRef(block, "discharge") == _ForcingFileFieldRef(
            block, "discharge"
        )
        assert _ForcingFileFieldRef(block, "discharge") != _ForcingFileFieldRef(
            block, "salinity"
        )

