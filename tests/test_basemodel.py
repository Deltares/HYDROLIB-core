from pathlib import Path
from typing import Sequence, Tuple

import pytest

from hydrolib.core.basemodel import (
    FileLoadContext,
    FileModel,
    FileModelCache,
    FilePathResolver,
    ResolveRelativeMode,
    context_file_loading,
    file_load_context,
)
from hydrolib.core.io.dimr.models import DIMR
from tests.utils import test_input_dir


def test_loading_a_file_twice_returns_different_model_instances() -> None:
    # If the same source file is read multiple times, we expect that
    # multiple (deep) copies are returned, and not references to the
    # same object.

    # For the ease of testing, we use DIMR model, which implements FileModel
    assert issubclass(DIMR, FileModel)

    test_file = (
        test_input_dir
        / "e02"
        / "c11_korte-woerden-1d"
        / "dimr_model"
        / "dimr_config.xml"
    )

    model_a = DIMR(test_file)
    model_b = DIMR(test_file)

    assert model_a is not model_b


class TestContextManagerFileLoadContext:
    def test_context_is_created_and_disposed_properly(self):
        assert context_file_loading.get(None) is None

        with file_load_context() as flc:
            assert isinstance(flc, FileLoadContext)
            assert context_file_loading.get(None) is flc

        assert context_file_loading.get(None) is None

    def test_context_called_multiple_times_provides_same_instance(self):
        with file_load_context() as flc_root:
            with file_load_context() as flc_child:
                assert flc_child is flc_root


class TestFileModelCache:
    def test_cache_without_state_returns_none(self):
        cache = FileModelCache()
        assert cache.retrieve_model(Path("some/path")) is None

    def test_cache_with_state_returns_correct_result(self):
        cache = FileModelCache()

        path = Path.cwd() / "some-dimr.xml"
        model = DIMR()  # empty subclass of the FileModel

        cache.register_model(path, model)

        assert cache.retrieve_model(path) is model


class TestFilePathResolver:
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
                    (test_input_dir / "3", ResolveRelativeMode.ToParent),
                    (test_input_dir / "4", ResolveRelativeMode.ToParent),
                    (test_input_dir / "5", ResolveRelativeMode.ToParent),
                ],
                0,
                Path("somePath.xml"),
                test_input_dir / "5" / "somePath.xml",
                id="with_relative_parent_paths_returns_relative_to_last_parent",
            ),
            pytest.param(
                [
                    (test_input_dir / "1", ResolveRelativeMode.ToParent),
                    (test_input_dir / "2", ResolveRelativeMode.ToParent),
                    (test_input_dir / "3", ResolveRelativeMode.ToParent),
                    (test_input_dir / "4", ResolveRelativeMode.ToParent),
                    (test_input_dir / "5", ResolveRelativeMode.ToAnchor),
                ],
                0,
                Path("somePath.xml"),
                test_input_dir / "5" / "somePath.xml",
                id="with_anchor_last_returns_relative_to_anchor",
            ),
            pytest.param(
                [
                    (test_input_dir / "1", ResolveRelativeMode.ToAnchor),
                    (test_input_dir / "2", ResolveRelativeMode.ToParent),
                    (test_input_dir / "3", ResolveRelativeMode.ToParent),
                    (test_input_dir / "4", ResolveRelativeMode.ToParent),
                    (test_input_dir / "5", ResolveRelativeMode.ToParent),
                ],
                0,
                Path("somePath.xml"),
                test_input_dir / "1" / "somePath.xml",
                id="with_anchor_first_returns_relative_to_anchor",
            ),
            pytest.param(
                [
                    (test_input_dir / "1", ResolveRelativeMode.ToParent),
                    (test_input_dir / "2", ResolveRelativeMode.ToParent),
                    (test_input_dir / "3", ResolveRelativeMode.ToAnchor),
                    (test_input_dir / "4", ResolveRelativeMode.ToParent),
                    (test_input_dir / "5", ResolveRelativeMode.ToParent),
                ],
                0,
                Path("somePath.xml"),
                test_input_dir / "3" / "somePath.xml",
                id="with_anchors_middle_returns_relative_to_last_anchor",
            ),
            pytest.param(
                [
                    (test_input_dir / "1", ResolveRelativeMode.ToAnchor),
                    (test_input_dir / "2", ResolveRelativeMode.ToParent),
                    (test_input_dir / "3", ResolveRelativeMode.ToAnchor),
                    (test_input_dir / "4", ResolveRelativeMode.ToParent),
                    (test_input_dir / "5", ResolveRelativeMode.ToParent),
                ],
                0,
                Path("somePath.xml"),
                test_input_dir / "3" / "somePath.xml",
                id="with_multiple_anchors_returns_relative_to_last_anchor",
            ),
            pytest.param(
                [
                    (test_input_dir / "1", ResolveRelativeMode.ToParent),
                    (test_input_dir / "2", ResolveRelativeMode.ToParent),
                    (test_input_dir / "3", ResolveRelativeMode.ToAnchor),
                    (test_input_dir / "4", ResolveRelativeMode.ToParent),
                    (test_input_dir / "5", ResolveRelativeMode.ToParent),
                ],
                3,
                Path("somePath.xml"),
                test_input_dir / "2" / "somePath.xml",
                id="with_pop_anchor_returns_relative_to_parent_before_anchor",
            ),
            pytest.param(
                [
                    (test_input_dir / "1", ResolveRelativeMode.ToAnchor),
                    (test_input_dir / "2", ResolveRelativeMode.ToParent),
                    (test_input_dir / "3", ResolveRelativeMode.ToAnchor),
                    (test_input_dir / "4", ResolveRelativeMode.ToParent),
                    (test_input_dir / "5", ResolveRelativeMode.ToParent),
                ],
                3,
                Path("somePath.xml"),
                test_input_dir / "1" / "somePath.xml",
                id="with_pop_last_anchor_multiple_anchors_returns_relative_to_previous_anchor",
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
        resolver = FilePathResolver()

        for path, mode in parents:
            resolver.push_new_parent(path, mode)

        for _ in range(n_to_pop):
            resolver.pop_last_parent()

        assert resolver.resolve(input_path) == expected_result


class TestFileLoadContext:
    def test_retrieve_model_with_none_returns_none(self):
        context = FileLoadContext()
        assert context.retrieve_model(None) is None

    @pytest.mark.parametrize(
        "path",
        [
            pytest.param(Path("dimr.xml"), id="relative_path"),
            pytest.param(test_input_dir / "dimr.xml", id="absolute_path"),
        ],
    )
    def test_retrieve_model_with_relative_path_returns_correct_result(
        self,
        path: Path,
    ):
        context = FileLoadContext()
        model = DIMR()

        context.register_model(path, model)
        retrieved_model = context.retrieve_model(path)

        assert retrieved_model is model

    @pytest.mark.parametrize(
        ("register_path", "retrieval_path"),
        [
            pytest.param(Path("dimr.xml"), Path("dimr.xml"), id="relative-relative"),
            pytest.param(
                Path("dimr.xml"), Path.cwd() / Path("dimr.xml"), id="relative-absolute"
            ),
            pytest.param(
                Path.cwd() / Path("dimr.xml"), Path("dimr.xml"), id="absolute-relative"
            ),
            pytest.param(
                Path.cwd() / Path("dimr.xml"),
                Path.cwd() / Path("dimr.xml"),
                id="absolute-absolute",
            ),
        ],
    )
    def test_retrieve_model_is_always_determined_from_the_absolute_path(
        self,
        register_path: Path,
        retrieval_path: Path,
    ):
        context = FileLoadContext()

        model = DIMR()
        context.register_model(register_path, model)
        assert context.retrieve_model(retrieval_path) is model
