"""Unit tests for the file_manager module."""

import platform
from pathlib import Path
from typing import Dict, Optional, Sequence, Tuple
from unittest.mock import patch

import pytest

from hydrolib.core.base.file_manager import (
    CachedFileModel,
    FileCasingResolver,
    FileLoadContext,
    FileModelCache,
    FilePathResolver,
    ModelLoadSettings,
    PathStyleValidator,
    ResolveRelativeMode,
    context_file_loading,
    file_load_context,
    path_style_validator,
)

from hydrolib.core.base.models import FileModel, ModelSaveSettings
from hydrolib.core.utils import PathStyle
from tests.utils import test_input_dir


# Mock FileModel implementation for testing
class MockFileModel(FileModel):
    """Mock implementation of FileModel for testing."""

    @classmethod
    def _generate_name(cls) -> Optional[Path]:
        """Generate a default name for this FileModel."""
        return Path("mock_file.txt")

    def _save(self, save_settings: ModelSaveSettings) -> None:
        """Mock implementation of save."""
        pass

    def _load(self, filepath: Path) -> Dict:
        """Mock implementation of load."""
        return {}


def runs_from_docker():
    """Check if the tests are running from a Docker container."""
    return platform.system() == "Linux" and Path("/.dockerenv").exists()


class TestResolveRelativeMode:
    """Test class for the ResolveRelativeMode enum."""

    def test_enum_values(self):
        """Test that the enum values are correct."""
        assert ResolveRelativeMode.ToParent == 0
        assert ResolveRelativeMode.ToAnchor == 1


class TestFilePathResolver:
    """Test class for the FilePathResolver class."""

    @pytest.mark.parametrize(
        ("parents", "n_to_pop", "input_path", "expected_result"),
        [
            pytest.param(
                [],
                0,
                Path("somePath.xml"),
                Path.cwd() / "somePath.xml",
                id="without_parents_path_returns_relative_to_the_cwd",
            ),
            pytest.param(
                [],
                0,
                test_input_dir / "somePath.xml",
                test_input_dir / "somePath.xml",
                id="absolute_path_returns_itself",
            ),
            pytest.param(
                [],
                5,
                Path("somePath.xml"),
                Path.cwd() / "somePath.xml",
                id="without_parents_with_pop_last_parents_returns_relative_to_the_cwd",
            ),
            pytest.param(
                [
                    (test_input_dir / "1", ResolveRelativeMode.ToParent),
                ],
                1,
                Path("somePath.xml"),
                Path.cwd() / "somePath.xml",
                id="with_pop_only_parent_path_returns_relative_to_the_cwd",
            ),
            pytest.param(
                [
                    (test_input_dir / "1", ResolveRelativeMode.ToParent),
                    (test_input_dir / "2", ResolveRelativeMode.ToParent),
                    (test_input_dir / "3", ResolveRelativeMode.ToParent),
                ],
                2,
                Path("somePath.xml"),
                test_input_dir / "1" / "somePath.xml",
                id="with_pop_last_parents_path_returns_relative_",
            ),
            pytest.param(
                [(test_input_dir / "otherPath", ResolveRelativeMode.ToParent)],
                0,
                Path("somePath.xml"),
                test_input_dir / "otherPath" / "somePath.xml",
                id="with_parent_path_returns_relative_to_parent",
            ),
            pytest.param(
                [
                    (test_input_dir / "1", ResolveRelativeMode.ToParent),
                    (test_input_dir / "2", ResolveRelativeMode.ToParent),
                ],
                0,
                Path("somePath.xml"),
                test_input_dir / "2" / "somePath.xml",
                id="with_multiple_parent_paths_returns_relative_to_last_parent",
            ),
            pytest.param(
                [
                    (test_input_dir / "1", ResolveRelativeMode.ToAnchor),
                    (test_input_dir / "2", ResolveRelativeMode.ToParent),
                ],
                0,
                Path("somePath.xml"),
                test_input_dir / "1" / "somePath.xml",
                id="with_anchor_parent_path_returns_relative_to_anchor",
            ),
            pytest.param(
                [
                    (test_input_dir / "1", ResolveRelativeMode.ToAnchor),
                    (test_input_dir / "2", ResolveRelativeMode.ToAnchor),
                ],
                0,
                Path("somePath.xml"),
                test_input_dir / "2" / "somePath.xml",
                id="with_multiple_anchor_parent_paths_returns_relative_to_last_anchor",
            ),
            pytest.param(
                [
                    (test_input_dir / "1", ResolveRelativeMode.ToAnchor),
                    (test_input_dir / "2", ResolveRelativeMode.ToParent),
                    (test_input_dir / "3", ResolveRelativeMode.ToParent),
                ],
                0,
                Path("somePath.xml"),
                test_input_dir / "1" / "somePath.xml",
                id="with_anchor_and_parent_paths_returns_relative_to_anchor",
            ),
            pytest.param(
                [
                    (test_input_dir / "1", ResolveRelativeMode.ToAnchor),
                    (test_input_dir / "2", ResolveRelativeMode.ToAnchor),
                    (test_input_dir / "3", ResolveRelativeMode.ToParent),
                ],
                0,
                Path("somePath.xml"),
                test_input_dir / "2" / "somePath.xml",
                id="with_multiple_anchor_and_parent_paths_returns_relative_to_last_anchor",
            ),
            pytest.param(
                [
                    (test_input_dir / "1", ResolveRelativeMode.ToAnchor),
                    (test_input_dir / "2", ResolveRelativeMode.ToAnchor),
                ],
                1,
                Path("somePath.xml"),
                test_input_dir / "1" / "somePath.xml",
                id="with_pop_last_anchor_path_returns_relative_to_previous_anchor",
            ),
        ],
    )
    def test_resolves_to_expected_result(
        self,
        parents: Sequence[Tuple[Path, ResolveRelativeMode]],
        n_to_pop: int,
        input_path: Path,
        expected_result: Path,
    ):
        """Test that the resolver resolves paths correctly."""
        resolver = FilePathResolver()

        for path, mode in parents:
            resolver.push_new_parent(path, mode)

        for _ in range(n_to_pop):
            resolver.pop_last_parent()

        assert resolver.resolve(input_path) == expected_result

    def test_get_current_parent_with_no_parents(self):
        """Test that get_current_parent returns cwd when no parents are set."""
        resolver = FilePathResolver()
        assert resolver.get_current_parent() == Path.cwd()

    def test_get_current_parent_with_parent(self):
        """Test that get_current_parent returns the parent when a parent is set."""
        resolver = FilePathResolver()
        parent_path = test_input_dir / "parent"
        resolver.push_new_parent(parent_path, ResolveRelativeMode.ToParent)
        assert resolver.get_current_parent() == parent_path

    def test_get_current_parent_with_anchor(self):
        """Test that get_current_parent returns the anchor when an anchor is set."""
        resolver = FilePathResolver()
        anchor_path = test_input_dir / "anchor"
        resolver.push_new_parent(anchor_path, ResolveRelativeMode.ToAnchor)
        assert resolver.get_current_parent() == anchor_path

    def test_pop_last_parent_with_no_parents(self):
        """Test that pop_last_parent does nothing when no parents are set."""
        resolver = FilePathResolver()
        resolver.pop_last_parent()  # Should not raise an exception
        assert resolver.get_current_parent() == Path.cwd()


class TestPathStyleValidator:
    """Test class for the PathStyleValidator class."""

    def test_validate_none_returns_current_os_path_style(self):
        """Test that validate(None) returns the current OS path style."""
        validator = PathStyleValidator()
        path_style = validator.validate(None)

        exp_path_style = (
            PathStyle.WINDOWSLIKE
            if platform.system() == "Windows"
            else PathStyle.UNIXLIKE
        )

        assert path_style == exp_path_style

    def test_validate_windows_returns_windows_path_style(self):
        """Test that validate("windows") returns the Windows path style."""
        validator = PathStyleValidator()
        path_style = validator.validate("windows")

        assert path_style == PathStyle.WINDOWSLIKE

    def test_validate_unix_returns_unix_path_style(self):
        """Test that validate("unix") returns the Unix path style."""
        validator = PathStyleValidator()
        path_style = validator.validate("unix")

        assert path_style == PathStyle.UNIXLIKE

    def test_validate_unknown_raises_error(self):
        """Test that validate("unknown") raises a ValueError."""
        validator = PathStyleValidator()

        with pytest.raises(ValueError) as error:
            validator.validate("unknown")

        expected_message = (
            "Path style 'unknown' not supported. Supported path styles: unix, windows"
        )
        assert expected_message in str(error.value)


class TestModelLoadSettings:
    """Test class for the ModelLoadSettings class."""

    @pytest.mark.parametrize("value", [True, False])
    @pytest.mark.parametrize("path_style", [PathStyle.UNIXLIKE, PathStyle.WINDOWSLIKE])
    def test_properties(self, value: bool, path_style: PathStyle):
        """Test that the properties return the correct values."""
        settings = ModelLoadSettings(
            recurse=value, resolve_casing=value, path_style=path_style
        )
        assert settings.recurse == value
        assert settings.resolve_casing == value
        assert settings.path_style == path_style


class TestCachedFileModel:
    """Test class for the CachedFileModel class."""

    def test_properties(self):
        """Test that the properties return the correct values."""
        model = MockFileModel()
        checksum = "checksum"
        cached_model = CachedFileModel(model, checksum)
        assert cached_model.model is model
        assert cached_model.checksum == checksum


class TestFileModelCache:
    """Test class for the FileModelCache class."""

    def test_cache_without_state_returns_none(self):
        """Test that retrieve_model returns None when the cache is empty."""
        cache = FileModelCache()
        assert cache.retrieve_model(Path("some/path")) is None

    def test_cache_with_state_returns_correct_result(self):
        """Test that retrieve_model returns the correct model when the cache has state."""
        cache = FileModelCache()

        path = Path.cwd() / "some-mock-file.txt"
        model = MockFileModel()

        cache.register_model(path, model)

        assert cache.retrieve_model(path) is model

    def test_registed_model_when_cache_exists_returns_true(self, tmp_path):
        """Test that _exists returns True when a model is registered."""
        cache = FileModelCache()
        path = tmp_path / "some-mock-file.txt"
        model = MockFileModel()
        cache.register_model(path, model)

        assert cache._exists(path)

    def test_no_registed_model_when_cache_exists_returns_false(self, tmp_path):
        """Test that _exists returns False when no model is registered."""
        cache = FileModelCache()
        path = tmp_path / "some-mock-file.txt"

        assert not cache._exists(path)

    def test_has_changed_on_unchanged_file_returns_false(self, tmp_path: Path):
        """Test that has_changed returns False when a file hasn't changed."""
        cache = FileModelCache()
        path = tmp_path / "some-mock-file.txt"
        path.write_text("Hello World")
        model = MockFileModel()
        cache.register_model(path, model)

        assert not cache.has_changed(path)

    def test_has_changed_on_changed_file_returns_true(self, tmp_path: Path):
        """Test that has_changed returns True when a file has changed."""
        cache = FileModelCache()
        path = tmp_path / "some-mock-file.txt"
        path.write_text("Hello World")
        model = MockFileModel()
        cache.register_model(path, model)
        path.write_text("Hello World second time")

        assert cache.has_changed(path)

    def test_has_changed_when_no_registed_model_returns_true(self, tmp_path: Path):
        """Test that has_changed returns True when no model is registered."""
        cache = FileModelCache()
        path = tmp_path / "some-mock-file.txt"

        assert cache.has_changed(path)

    def test_is_empty_returns_true_when_empty(self):
        """Test that is_empty returns True when the cache is empty."""
        cache = FileModelCache()
        assert cache.is_empty()

    def test_is_empty_returns_false_when_not_empty(self, tmp_path: Path):
        """Test that is_empty returns False when the cache is not empty."""
        cache = FileModelCache()
        path = tmp_path / "some-mock-file.txt"
        model = MockFileModel()
        cache.register_model(path, model)
        assert not cache.is_empty()


class TestFileCasingResolver:
    """Test class for the FileCasingResolver class."""

    @pytest.mark.parametrize(
        "input_file, expected_file",
        [
            pytest.param(
                Path("DFLOWFM_INDIVIDUAL_FILES/FLOWFM_BOUNDARYCONDITIONS1D.BC"),
                Path("dflowfm_individual_files/FlowFM_boundaryconditions1d.bc"),
                id="resolve_casing True: Matching file exists with different casing",
            ),
            pytest.param(
                Path("DFLOWFM_INDIVIDUAL_FILES/beepboop.robot"),
                Path("dflowfm_individual_files/beepboop.robot"),
                id="resolve_casing True: No matching file",
            ),
        ],
    )
    @pytest.mark.skipif(
        runs_from_docker(),
        reason="Paths are case-insensitive while running from a Docker container (Linux) on a Windows machine, so this test will fail locally.",
    )
    def test_resolve_returns_correct_result(
        self, input_file: str, expected_file: str
    ) -> None:
        """Test that resolve returns the correct result."""
        resolver = FileCasingResolver()

        file_path = test_input_dir / input_file

        expected_file_path = test_input_dir / expected_file
        actual_file_path = resolver.resolve(file_path)

        assert actual_file_path == expected_file_path

    @patch("hydrolib.core.base.file_manager.get_operating_system")
    def test_resolve_unsupported_os_raises_error(self, mock_get_os):
        """Test that resolve raises an error for unsupported operating systems."""
        mock_get_os.return_value = "unsupported"
        resolver = FileCasingResolver()
        with pytest.raises(NotImplementedError):
            resolver.resolve(Path("some/path"))


class TestFileLoadContext:
    """Test class for the FileLoadContext class."""

    def test_retrieve_model_with_none_returns_none(self):
        """Test that retrieve_model returns None when path is None."""
        context = FileLoadContext()
        assert context.retrieve_model(None) is None

    @pytest.mark.parametrize(
        "path",
        [
            pytest.param(Path("mock-file.txt"), id="relative_path"),
            pytest.param(test_input_dir / "mock-file.txt", id="absolute_path"),
        ],
    )
    def test_retrieve_model_with_relative_path_returns_correct_result(
        self,
        path: Path,
    ):
        """Test that retrieve_model returns the correct model."""
        context = FileLoadContext()
        model = MockFileModel()

        context.register_model(path, model)
        retrieved_model = context.retrieve_model(path)

        assert retrieved_model is model

    @pytest.mark.parametrize(
        ("register_path", "retrieval_path"),
        [
            pytest.param(Path("mock-file.txt"), Path("mock-file.txt"), id="relative-relative"),
            pytest.param(
                Path("mock-file.txt"), Path.cwd() / Path("mock-file.txt"), id="relative-absolute"
            ),
            pytest.param(
                Path.cwd() / Path("mock-file.txt"), Path("mock-file.txt"), id="absolute-relative"
            ),
            pytest.param(
                Path.cwd() / Path("mock-file.txt"),
                Path.cwd() / Path("mock-file.txt"),
                id="absolute-absolute",
            ),
        ],
    )
    def test_retrieve_model_is_always_determined_from_the_absolute_path(
        self,
        register_path: Path,
        retrieval_path: Path,
    ):
        """Test that retrieve_model always uses the absolute path."""
        context = FileLoadContext()

        model = MockFileModel()
        context.register_model(register_path, model)
        assert context.retrieve_model(retrieval_path) is model

    def test_load_settings_property_raises_error_with_uninitialized_settings(self):
        """Test that load_settings raises an error when settings are not initialized."""
        context = FileLoadContext()
        with pytest.raises(ValueError) as error:
            context.load_settings

        assert (
            str(error.value)
            == f"The model load settings have not been initialized yet. Make sure to call `{context.initialize_load_settings.__name__}` first."
        )

    @pytest.mark.parametrize("first_bool", [True, False])
    @pytest.mark.parametrize("second_bool", [True, False])
    @pytest.mark.parametrize(
        "first_path_style", [PathStyle.UNIXLIKE, PathStyle.WINDOWSLIKE]
    )
    @pytest.mark.parametrize(
        "second_path_style", [PathStyle.UNIXLIKE, PathStyle.WINDOWSLIKE]
    )
    def test_can_only_set_load_settings_once(
        self,
        first_bool: bool,
        second_bool: bool,
        first_path_style: PathStyle,
        second_path_style: PathStyle,
    ):
        """Test that load settings can only be set once."""
        context = FileLoadContext()
        context.initialize_load_settings(first_bool, first_bool, first_path_style)
        context.initialize_load_settings(second_bool, second_bool, second_path_style)

        assert context.load_settings is not None
        assert context.load_settings.recurse == first_bool
        assert context.load_settings.resolve_casing == first_bool
        assert context.load_settings.path_style == first_path_style

    def test_is_content_changed_on_unchanged_file_returns_false(self, tmp_path: Path):
        """Test that is_content_changed returns False for unchanged files."""
        context = FileLoadContext()
        path = tmp_path / "some-mock-file.txt"
        path.write_text("Hello World")
        model = MockFileModel()
        context.register_model(path, model)

        assert not context.is_content_changed(path)

    def test_is_content_changed_on_changed_file_returns_true(self, tmp_path: Path):
        """Test that is_content_changed returns True for changed files."""
        context = FileLoadContext()
        path = tmp_path / "some-mock-file.txt"
        path.write_text("Hello World")
        model = MockFileModel()
        context.register_model(path, model)
        path.write_text("Hello World second time")

        assert context.is_content_changed(path)

    def test_is_content_changed_when_no_registed_model_returns_true(
        self, tmp_path: Path
    ):
        """Test that is_content_changed returns True when no model is registered."""
        context = FileLoadContext()
        path = tmp_path / "some-mock-file.txt"

        assert context.is_content_changed(path)

    def test_cache_is_empty_returns_true_when_empty(self):
        """Test that cache_is_empty returns True when the cache is empty."""
        context = FileLoadContext()
        assert context.cache_is_empty()

    def test_cache_is_empty_returns_false_when_not_empty(self, tmp_path: Path):
        """Test that cache_is_empty returns False when the cache is not empty."""
        context = FileLoadContext()
        path = tmp_path / "some-mock-file.txt"
        model = MockFileModel()
        context.register_model(path, model)
        assert not context.cache_is_empty()

    def test_get_current_parent(self):
        """Test that get_current_parent returns the correct parent."""
        context = FileLoadContext()
        assert context.get_current_parent() == Path.cwd()

        parent_path = test_input_dir / "parent"
        context.push_new_parent(parent_path, ResolveRelativeMode.ToParent)
        assert context.get_current_parent() == parent_path

    def test_resolve(self):
        """Test that resolve returns the correct path."""
        context = FileLoadContext()
        path = Path("some/path")
        assert context.resolve(path) == Path.cwd() / path

        parent_path = test_input_dir / "parent"
        context.push_new_parent(parent_path, ResolveRelativeMode.ToParent)
        assert context.resolve(path) == parent_path / path

    def test_push_new_parent_and_pop_last_parent(self):
        """Test that push_new_parent and pop_last_parent work correctly."""
        context = FileLoadContext()
        parent1 = test_input_dir / "parent1"
        parent2 = test_input_dir / "parent2"

        context.push_new_parent(parent1, ResolveRelativeMode.ToParent)
        assert context.get_current_parent() == parent1

        context.push_new_parent(parent2, ResolveRelativeMode.ToParent)
        assert context.get_current_parent() == parent2

        context.pop_last_parent()
        assert context.get_current_parent() == parent1

        context.pop_last_parent()
        assert context.get_current_parent() == Path.cwd()

    def test_resolve_casing_with_resolve_casing_true(self, tmp_path: Path):
        """Test that resolve_casing resolves casing when resolve_casing is True."""
        context = FileLoadContext()
        context.initialize_load_settings(True, True, PathStyle.WINDOWSLIKE)

        with patch.object(context._file_casing_resolver, "resolve") as mock_resolve:
            mock_resolve.return_value = tmp_path / "resolved"
            path = tmp_path / "original"
            result = context.resolve_casing(path)
            mock_resolve.assert_called_once_with(path)
            assert result == tmp_path / "resolved"

    def test_resolve_casing_with_resolve_casing_false(self, tmp_path: Path):
        """Test that resolve_casing doesn't resolve casing when resolve_casing is False."""
        context = FileLoadContext()
        context.initialize_load_settings(True, False, PathStyle.WINDOWSLIKE)

        with patch.object(context._file_casing_resolver, "resolve") as mock_resolve:
            path = tmp_path / "original"
            result = context.resolve_casing(path)
            mock_resolve.assert_not_called()
            assert result == path

    def test_convert_path_style_with_absolute_path(self, tmp_path: Path):
        """Test that convert_path_style returns the path as is for absolute paths."""
        context = FileLoadContext()
        context.initialize_load_settings(True, True, PathStyle.WINDOWSLIKE)

        path = tmp_path / "file.txt"
        result = context.convert_path_style(path)
        assert result == path

    def test_convert_path_style_with_relative_path(self):
        """Test that convert_path_style converts the path style for relative paths."""
        context = FileLoadContext()
        context.initialize_load_settings(True, True, PathStyle.WINDOWSLIKE)

        with patch.object(context._file_path_style_converter, "convert_to_os_style") as mock_convert:
            mock_convert.return_value = "converted/path"
            path = Path("original/path")
            result = context.convert_path_style(path)
            mock_convert.assert_called_once_with(path, PathStyle.WINDOWSLIKE)
            assert result == Path("converted/path")


class TestContextManagerFileLoadContext:
    """Test class for the file_load_context context manager."""

    def test_context_is_created_and_disposed_properly(self):
        """Test that the context is created and disposed properly."""
        assert context_file_loading.get(None) is None

        with file_load_context() as flc:
            assert context_file_loading.get(None) is flc

        assert context_file_loading.get(None) is None

    def test_context_called_multiple_times_provides_same_instance(self):
        """Test that calling the context manager multiple times provides the same instance."""
        with file_load_context() as flc_root:
            with file_load_context() as flc_child:
                assert flc_child is flc_root


class TestPathStyleValidatorGlobal:
    """Test class for the path_style_validator global instance."""

    def test_path_style_validator_is_instance_of_path_style_validator(self):
        """Test that path_style_validator is an instance of PathStyleValidator."""
        assert isinstance(path_style_validator, PathStyleValidator)

    def test_path_style_validator_validate_works(self):
        """Test that path_style_validator.validate works."""
        assert path_style_validator.validate("windows") == PathStyle.WINDOWSLIKE
