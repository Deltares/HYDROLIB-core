"""Unit tests for the FileModel cache cleanup fix.

Tests verify that when a FileModel subclass successfully loads a file but fails
Pydantic validation of the loaded data, the partially-initialized instance is
removed from the FileLoadContext cache. This prevents Pydantic's Union fallback
types (e.g., DiskOnlyFileModel) from retrieving a broken cached instance.

See: https://github.com/Deltares/HYDROLIB-core/issues/1032
"""

from pathlib import Path
from typing import Dict, Optional, Union

import pytest
from pydantic import field_validator

from hydrolib.core.base.file_manager import FileLoadContext, FileModelCache
from hydrolib.core.base.models import (
    DiskOnlyFileModel,
    FileModel,
    ModelSaveSettings,
)


class ValidFileModel(FileModel):
    """FileModel subclass that always loads successfully."""

    name: str = "default"

    def _load(self, filepath: Path) -> Dict:
        return {"name": "loaded"}

    def _save(self, save_settings: ModelSaveSettings) -> None:
        pass

    @classmethod
    def _generate_name(cls) -> Optional[Path]:
        return Path("valid.txt")


class FailingFileModel(FileModel):
    """FileModel subclass that loads file data but fails Pydantic validation.

    The _load method returns data that will cause a validation error
    in super().__init__(), simulating the real bug scenario where a file
    parses successfully but its content violates model constraints.
    """

    name: str = "default"

    @field_validator("name", mode="before")
    @classmethod
    def _reject_bad_name(cls, v):
        if v == "INVALID_DATA":
            raise ValueError("name cannot be INVALID_DATA")
        return v

    def _load(self, filepath: Path) -> Dict:
        return {"name": "INVALID_DATA"}

    def _save(self, save_settings: ModelSaveSettings) -> None:
        pass

    @classmethod
    def _generate_name(cls) -> Optional[Path]:
        return Path("failing.txt")


class TestFileModelCacheUnregister:
    """Tests for FileModelCache.unregister_model."""

    def test_unregister_removes_cached_model(self, tmp_path: Path):
        """Test that unregister_model removes a previously registered model.

        Test scenario:
            Register a model, then unregister it. Subsequent retrieval
            should return None.
        """
        cache = FileModelCache()
        path = tmp_path / "test.txt"
        model = ValidFileModel()
        cache.register_model(path, model)

        assert cache.retrieve_model(path) is model, (
            "Model should be retrievable before unregistering"
        )

        cache.unregister_model(path)

        assert cache.retrieve_model(path) is None, (
            "Model should be None after unregistering"
        )

    def test_unregister_nonexistent_path_is_noop(self, tmp_path: Path):
        """Test that unregistering a path not in the cache does not raise.

        Test scenario:
            Call unregister_model on a path that was never registered.
            Should silently do nothing.
        """
        cache = FileModelCache()
        path = tmp_path / "nonexistent.txt"

        cache.unregister_model(path)

        assert cache.retrieve_model(path) is None, (
            "Cache should remain empty after unregistering nonexistent path"
        )

    def test_unregister_leaves_other_entries_intact(self, tmp_path: Path):
        """Test that unregistering one path does not affect other cached models.

        Test scenario:
            Register two models under different paths, unregister one.
            The other should still be retrievable.
        """
        cache = FileModelCache()
        path_a = tmp_path / "a.txt"
        path_b = tmp_path / "b.txt"
        model_a = ValidFileModel()
        model_b = ValidFileModel()
        cache.register_model(path_a, model_a)
        cache.register_model(path_b, model_b)

        cache.unregister_model(path_a)

        assert cache.retrieve_model(path_a) is None, (
            "Unregistered model should be removed"
        )
        assert cache.retrieve_model(path_b) is model_b, (
            "Other cached model should remain"
        )

    def test_cache_is_empty_after_unregistering_only_entry(self, tmp_path: Path):
        """Test that the cache reports empty after its only entry is removed.

        Test scenario:
            Register one model, unregister it, check is_empty().
        """
        cache = FileModelCache()
        path = tmp_path / "only.txt"
        cache.register_model(path, ValidFileModel())

        cache.unregister_model(path)

        assert cache.is_empty(), (
            "Cache should be empty after removing its only entry"
        )


class TestFileLoadContextUnregister:
    """Tests for FileLoadContext.unregister_model."""

    def test_unregister_removes_model_via_context(self):
        """Test that FileLoadContext.unregister_model delegates to the cache.

        Test scenario:
            Register a model through the context, then unregister it.
            Retrieval should return None.
        """
        context = FileLoadContext()
        path = Path("context_test.txt")
        model = ValidFileModel()
        context.register_model(path, model)

        assert context.retrieve_model(path) is model, (
            "Model should be retrievable before unregistering"
        )

        context.unregister_model(path)

        assert context.retrieve_model(path) is None, (
            "Model should be None after unregistering via context"
        )

    @pytest.mark.parametrize(
        ("register_path", "unregister_path"),
        [
            pytest.param(
                Path("file.txt"),
                Path("file.txt"),
                id="relative-relative",
            ),
            pytest.param(
                Path("file.txt"),
                Path.cwd() / "file.txt",
                id="relative-absolute",
            ),
            pytest.param(
                Path.cwd() / "file.txt",
                Path("file.txt"),
                id="absolute-relative",
            ),
        ],
    )
    def test_unregister_resolves_paths_consistently(
        self,
        register_path: Path,
        unregister_path: Path,
    ):
        """Test that unregister resolves paths the same way as register.

        Args:
            register_path: Path used to register the model.
            unregister_path: Path used to unregister the model.

        Test scenario:
            Register with one path form, unregister with another. Both
            should resolve to the same absolute path internally.
        """
        context = FileLoadContext()
        model = ValidFileModel()
        context.register_model(register_path, model)

        context.unregister_model(unregister_path)

        assert context.retrieve_model(register_path) is None, (
            f"Model registered at {register_path} should be removed "
            f"when unregistered via {unregister_path}"
        )


class TestFileModelInitCacheCleanup:
    """Tests for FileModel.__init__ cache cleanup on validation failure.

    These tests verify the core bug fix: when super().__init__() fails inside
    FileModel.__init__, the model must be removed from the cache and the
    parent path must be popped, so that subsequent construction attempts
    (e.g., Pydantic Union fallbacks) start with a clean slate.
    """

    def test_successful_init_returns_valid_model(self, tmp_path: Path):
        """Test that a successful FileModel init returns a fully initialized model.

        Test scenario:
            Create a ValidFileModel from a real file. The model should be
            properly initialized with loaded data and have Pydantic internals
            intact (model_fields_set should be accessible).
        """
        file_path = tmp_path / "valid.txt"
        file_path.write_text("content")

        model = ValidFileModel(filepath=file_path)

        assert model.name == "loaded", (
            f"Expected name 'loaded', got '{model.name}'"
        )
        assert hasattr(model, "__pydantic_fields_set__"), (
            "Model should have __pydantic_fields_set__ after successful init"
        )

    def test_failed_init_does_not_leave_zombie_in_cache(self, tmp_path: Path):
        """Test that a failed init cleans up so DiskOnlyFileModel loads fresh.

        Test scenario:
            FailingFileModel fails on a file. Then DiskOnlyFileModel is loaded
            from the same file. Without the fix, DiskOnlyFileModel.__new__
            would return the broken FailingFileModel from cache. With the fix,
            a proper DiskOnlyFileModel is returned.
        """
        file_path = tmp_path / "failing.txt"
        file_path.write_text("content")

        with pytest.raises(Exception):
            FailingFileModel(filepath=file_path)

        fallback = DiskOnlyFileModel(filepath=file_path)

        assert isinstance(fallback, DiskOnlyFileModel), (
            "DiskOnlyFileModel should not return a cached FailingFileModel. "
            f"Got {type(fallback).__name__} instead."
        )

    def test_failed_init_reraises_original_exception(self, tmp_path: Path):
        """Test that the original validation error propagates after cleanup.

        Test scenario:
            FailingFileModel should raise a ValidationError containing
            the validator's error message after cleaning up the cache.
        """
        file_path = tmp_path / "failing.txt"
        file_path.write_text("content")

        with pytest.raises(Exception, match="INVALID_DATA"):
            FailingFileModel(filepath=file_path)

    def test_failed_init_does_not_corrupt_subsequent_loads(
        self, tmp_path: Path
    ):
        """Test that a DiskOnlyFileModel can load after a FileModel fails.

        Test scenario:
            This is the end-to-end reproduction of the original bug.
            FailingFileModel.__init__ fails, then DiskOnlyFileModel is
            constructed with the same filepath. Without the fix,
            DiskOnlyFileModel.__new__ would return the broken cached
            FailingFileModel. With the fix, it creates a fresh instance.
        """
        file_path = tmp_path / "shared.txt"
        file_path.write_text("content")

        with pytest.raises(Exception):
            FailingFileModel(filepath=file_path)

        fallback = DiskOnlyFileModel(filepath=file_path)

        assert isinstance(fallback, DiskOnlyFileModel), (
            f"Expected DiskOnlyFileModel, got {type(fallback).__name__}. "
            "Cache cleanup likely failed — the broken FailingFileModel "
            "instance leaked through."
        )
        assert fallback.filepath == file_path, (
            f"Expected filepath {file_path}, got {fallback.filepath}"
        )

    def test_failed_init_does_not_affect_different_filepath(
        self, tmp_path: Path
    ):
        """Test that a failed init for one path doesn't affect another.

        Test scenario:
            FailingFileModel fails for path A. ValidFileModel should still
            load successfully from a different path B.
        """
        failing_path = tmp_path / "failing.txt"
        failing_path.write_text("content")
        valid_path = tmp_path / "valid.txt"
        valid_path.write_text("content")

        with pytest.raises(Exception):
            FailingFileModel(filepath=failing_path)

        model = ValidFileModel(filepath=valid_path)

        assert isinstance(model, ValidFileModel), (
            f"Expected ValidFileModel, got {type(model).__name__}"
        )
        assert model.name == "loaded", (
            f"Expected name 'loaded', got '{model.name}'"
        )


class TestPydanticUnionFallback:
    """Tests verifying correct Union[FileModel, DiskOnlyFileModel] behavior.

    These tests use Pydantic's Union validation directly to ensure the
    cache cleanup allows proper fallback from a failing FileModel type
    to DiskOnlyFileModel.
    """

    def test_union_field_falls_back_to_disk_only_model(self, tmp_path: Path):
        """Test that a Union field falls back to DiskOnlyFileModel on failure.

        Test scenario:
            Define a parent model with a Union[FailingFileModel, DiskOnlyFileModel]
            field. When initialized with a filepath, FailingFileModel should fail
            and DiskOnlyFileModel should succeed as the fallback.
        """
        from pydantic import Field

        from hydrolib.core.base.models import BaseModel

        class ParentModel(BaseModel):
            child: Optional[Union[FailingFileModel, DiskOnlyFileModel]] = Field(
                None
            )

        file_path = tmp_path / "union_test.txt"
        file_path.write_text("content")

        parent = ParentModel(child={"filepath": file_path})

        assert isinstance(parent.child, DiskOnlyFileModel), (
            f"Expected DiskOnlyFileModel fallback, got {type(parent.child).__name__}"
        )

    def test_union_field_uses_primary_type_when_valid(self, tmp_path: Path):
        """Test that a Union field uses the primary type when it validates.

        Test scenario:
            Define a parent model with a Union[ValidFileModel, DiskOnlyFileModel]
            field. When the primary type succeeds, it should be used directly
            without falling back.
        """
        from pydantic import Field

        from hydrolib.core.base.models import BaseModel

        class ParentModel(BaseModel):
            child: Optional[Union[ValidFileModel, DiskOnlyFileModel]] = Field(
                None
            )

        file_path = tmp_path / "valid_union.txt"
        file_path.write_text("content")

        parent = ParentModel(child={"filepath": file_path})

        assert isinstance(parent.child, ValidFileModel), (
            f"Expected ValidFileModel, got {type(parent.child).__name__}"
        )

    def test_union_field_none_default_stays_none(self):
        """Test that a Union field with default None remains None when omitted.

        Test scenario:
            Define a parent model with Optional Union field defaulting to None.
            When no value is provided, the field should stay None.
        """
        from pydantic import Field

        from hydrolib.core.base.models import BaseModel

        class ParentModel(BaseModel):
            child: Optional[Union[FailingFileModel, DiskOnlyFileModel]] = Field(
                None
            )

        parent = ParentModel()

        assert parent.child is None, (
            f"Expected None default, got {type(parent.child).__name__}"
        )
