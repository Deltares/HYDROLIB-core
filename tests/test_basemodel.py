import shutil
from os import path
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
from hydrolib.core.io.mdu.models import FMModel
from tests.utils import test_input_dir, test_output_dir

_external_path = test_output_dir / "test_save_and_load_maintains_correct_paths_external"


class TestFileModel:
    def test_dimr_model_is_a_file_model(self):
        # For the ease of testing, we use DIMR model, which implements FileModel
        # If this test fails the other tests are basically useless.
        assert issubclass(DIMR, FileModel)

    def test_loading_a_file_twice_returns_different_model_instances(self) -> None:
        # If the same source file is read multiple times, we expect that
        # multiple (deep) copies are returned, and not references to the
        # same object.

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

    def _resolve(self, path: Path, relative_parent: Path) -> Path:
        if path.is_absolute():
            return path
        return relative_parent / path

    @pytest.mark.parametrize(
        "paths_relative_to_parent",
        [True, False],
    )
    @pytest.mark.parametrize(
        (
            "netfile",
            "structuresfile",
            "roughness_channel",
            "roughness_main",
            "roughness_sewer",
            "extforcefile",
        ),
        [
            pytest.param(
                Path("FlowFM_net.nc"),
                Path("structures.ini"),
                Path("roughness-Channels.ini"),
                Path("roughness-Main.ini"),
                Path("roughness-Sewers.ini"),
                Path("FM_model_bnd.ext"),
                id="flat-hierarchy",
            ),
            pytest.param(
                Path("./net/FlowFM_net.nc"),
                Path("./struc/structures.ini"),
                Path("./channels/roughness-Channels.ini"),
                Path("./channels/roughness-Main.ini"),
                Path("./channels/roughness-Sewers.ini"),
                Path("./ext/FM_model_bnd.ext"),
                id="relative paths",
            ),
            pytest.param(
                _external_path / "FlowFM_net.nc",
                _external_path / "structures.ini",
                _external_path / "roughness-Channels.ini",
                _external_path / "roughness-Main.ini",
                _external_path / "roughness-Sewers.ini",
                _external_path / "FM_model_bnd.ext",
                id="absolute paths",
            ),
        ],
    )
    @pytest.mark.parametrize(
        "forcingfile",
        [
            Path("FM_model_boundaryconditions1d.bc"),
            Path("./ext/FM_model_boundaryconditions1d.bc"),
            _external_path / "FM_model_boundaryconditions1d.bc",
        ],
    )
    def test_save_and_load_maintains_correct_paths(
        self,
        paths_relative_to_parent: bool,
        netfile: Path,
        structuresfile: Path,
        roughness_channel: Path,
        roughness_main: Path,
        roughness_sewer: Path,
        extforcefile: Path,
        forcingfile: Path,
    ):
        reference_model_path = test_input_dir / "file_load_test" / "fm.mdu"
        reference_model = FMModel(reference_model_path)

        # TODO: temp fix should be fixed with #150
        reference_model.wind.cdbreakpoints = []
        reference_model.wind.windspeedbreakpoints = []

        output_dir = (
            test_output_dir / self.test_save_and_load_maintains_correct_paths.__name__
        )

        if _external_path.exists():
            shutil.rmtree(_external_path)

        if output_dir.exists():
            shutil.rmtree(output_dir)

        model_path = output_dir / "fm.mdu"

        # Configure paths
        reference_model.filepath = model_path
        reference_model.general.pathsrelativetoparent = paths_relative_to_parent

        geometry = reference_model.geometry

        geometry.netfile.filepath = netfile  # type: ignore[arg-type]
        geometry.structurefile[0].filepath = structuresfile  # type: ignore[arg-type]
        geometry.frictfile[0].filepath = roughness_channel  # type: ignore[arg-type]
        geometry.frictfile[1].filepath = roughness_main  # type: ignore[arg-type]
        geometry.frictfile[2].filepath = roughness_sewer  # type: ignore[arg-type]

        extforce = reference_model.external_forcing.extforcefilenew

        extforce.filepath = extforcefile  # type: ignore[arg-type]
        extforce.boundary[0].forcingfile.filepath = forcingfile  # type: ignore[arg-type]
        extforce.boundary[1].forcingfile.filepath = forcingfile  # type: ignore[arg-type]

        reference_model.save(recurse=True)

        read_model = FMModel(model_path)

        assert read_model.filepath == model_path
        assert read_model.general.pathsrelativetoparent == paths_relative_to_parent

        read_geometry = read_model.geometry
        assert read_geometry.netfile.filepath == netfile  # type: ignore[arg-type]
        assert read_geometry.structurefile[0].filepath == structuresfile  # type: ignore[arg-type]
        assert read_geometry.frictfile[0].filepath == roughness_channel  # type: ignore[arg-type]
        assert read_geometry.frictfile[1].filepath == roughness_main  # type: ignore[arg-type]
        assert read_geometry.frictfile[2].filepath == roughness_sewer  # type: ignore[arg-type]

        read_extforce = read_model.external_forcing.extforcefilenew

        assert read_extforce.filepath == extforcefile  # type: ignore[arg-type]
        assert Path(read_extforce.boundary[0].forcingfile.filepath) == forcingfile  # type: ignore[arg-type]
        assert Path(read_extforce.boundary[1].forcingfile.filepath) == forcingfile  # type: ignore[arg-type]

        # We assume that if the file exists it is read correctly.
        # The contents should be verified in the specific models.
        assert self._resolve(model_path, output_dir).is_file()
        assert self._resolve(netfile, output_dir).is_file()
        assert self._resolve(structuresfile, output_dir).is_file()
        assert self._resolve(roughness_channel, output_dir).is_file()
        assert self._resolve(roughness_main, output_dir).is_file()
        assert self._resolve(roughness_sewer, output_dir).is_file()
        assert self._resolve(extforcefile, output_dir).is_file()

        if paths_relative_to_parent:
            parent = self._resolve(extforcefile, output_dir).parent
            assert self._resolve(forcingfile, parent).is_file()
        else:
            assert self._resolve(forcingfile, output_dir).is_file()


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
