import filecmp
import platform
import shutil
from pathlib import Path
from typing import Sequence, Tuple
from unittest.mock import patch

import pytest

from hydrolib.core.basemodel import (
    DiskOnlyFileModel,
    FileCasingResolver,
    FileLoadContext,
    FileModel,
    FileModelCache,
    FilePathResolver,
    ModelLoadSettings,
    ModelSaveSettings,
    ParsableFileModel,
    PathStyleValidator,
    ResolveRelativeMode,
    SerializerConfig,
    context_file_loading,
    file_load_context,
)
from hydrolib.core.dflowfm.bc.models import ForcingModel
from hydrolib.core.dflowfm.ext.models import ExtModel
from hydrolib.core.dflowfm.mdu.models import FMModel
from hydrolib.core.dimr.models import DIMR
from hydrolib.core.utils import PathStyle
from tests.utils import test_input_dir, test_output_dir

_external_path = test_output_dir / "test_save_and_load_maintains_correct_paths_external"


def runs_from_docker() -> bool:
    """Check to see if we are running from within docker."""
    return Path("/.dockerenv").exists()





class TestFileLoadContextReusingCachedFilesDuringInit:
    def test_loading_file_referenced_multiple_times_only_loads_once(
        self, tmp_path: Path
    ):
        bc_file_name = "bc_file.bc"
        ext_file = self.create_ext_file_with_5_times_bc_file_reused(
            tmp_path, bc_file_name
        )
        self.create_bc_file(tmp_path, bc_file_name)

        with patch.object(ForcingModel, "_load") as bc_mocked_load:
            ExtModel(ext_file)
            assert bc_mocked_load.call_count == 1

    def test_loading_file_referenced_multiple_times_has_loaded_data_as_same_instance(
        self, tmp_path: Path
    ):
        bc_file_name = "bc_file.bc"
        ext_file = self.create_ext_file_with_5_times_bc_file_reused(
            tmp_path, bc_file_name
        )
        self.create_bc_file(tmp_path, bc_file_name)

        model = ExtModel(ext_file)

        assert model.boundary[0].forcingfile is model.boundary[1].forcingfile
        assert model.boundary[1].forcingfile is model.boundary[2].forcingfile
        assert model.boundary[2].forcingfile is model.boundary[3].forcingfile
        assert model.boundary[3].forcingfile is model.boundary[4].forcingfile

    def test_loading_multiple_files_referenced_multiple_times_only_loads_the_respective_files_once(
        self, tmp_path: Path
    ):
        first_bc_file_name = "bc_file.bc"
        second_bc_file_name = "bc_file2.bc"
        ext_file = self.create_ext_file_with_2_times_2_bc_file_reused(
            tmp_path, first_bc_file_name, second_bc_file_name
        )
        self.create_bc_file(tmp_path, first_bc_file_name)
        self.create_bc_file(tmp_path, second_bc_file_name)

        with patch.object(ForcingModel, "_load") as bc_mocked_load:
            ExtModel(ext_file)
            assert bc_mocked_load.call_count == 2

    def create_bc_file(self, tmp_path: Path, name: str):
        bc_file = tmp_path / name
        bc_file_data = """[forcing]
Name                = global
Function            = timeseries
Time-interpolation  = linear
Quantity            = time
Unit                = minutes since 2006-12-25 0:00:00
Quantity            = rainfall_rate
Unit                = mm day-1
   0.000000     0.0000000
 120.000000     0.0000000
 240.000000    10.0000000
 360.000000    31.6000000
 480.000000   100.0000000
 600.000000   120.0000000
 720.000000   100.0000000
 840.000000    70.0000000
 960.000000     0.0000000
 960.000000    54.0000000
1080.000000    70.0000000
1200.000000    35.0000000
1320.000000     0.0000000
1440.000000     0.0000000
3000.000000     0.0000000
"""
        bc_file.write_text(bc_file_data)

    def change_bc_file(self, tmp_path: Path, name: str):
        bc_file = tmp_path / name
        bc_file_data = """[forcing]
Name                = little_change_to_the_file
Function            = timeseries
Time-interpolation  = linear
Quantity            = time
Unit                = minutes since 2006-12-25 0:00:00
Quantity            = rainfall_rate
Unit                = mm day-1
   0.000000     0.0000000
 120.000000     0.0000000
 240.000000    10.0000000
 360.000000    31.6000000
 480.000000   100.0000000
 600.000000   120.0000000
 720.000000   100.0000000
 840.000000    70.0000000
 960.000000     0.0000000
 960.000000    54.0000000
1080.000000    70.0000000
1200.000000    35.0000000
1320.000000     0.0000000
1440.000000     0.0000000
3000.000000     0.0000000
"""
        bc_file.write_text(bc_file_data)

    def create_ext_file_with_5_times_bc_file_reused(
        self, tmp_path: Path, name: str
    ) -> Path:
        ext_file = tmp_path / "ext_file.ext"
        ext_file_data = f"""[boundary]
quantity=dischargebnd
locationfile=boundary_conditions/Lek.pli
forcingfile={name}
[boundary]
quantity=dischargebnd
locationfile=boundary_conditions/Waal.pli
forcingfile={name}
[boundary]
quantity=dischargebnd
locationfile=boundary_conditions/Maas.pli
forcingfile={name}
[boundary]
quantity=salinitybnd
locationfile=boundary_conditions/rmm_zeerand_v3.pli
forcingfile={name}
[boundary]
quantity=temperaturebnd
locationfile=boundary_conditions/rmm_zeerand_v3.pli
forcingfile={name}"""

        ext_file.write_text(ext_file_data)
        return ext_file

    def create_ext_file_with_2_times_2_bc_file_reused(
        self, tmp_path: Path, name: str, name2: str
    ) -> Path:
        ext_file = tmp_path / "ext_file.ext"
        ext_file_data = f"""[boundary]
quantity=dischargebnd
locationfile=boundary_conditions/Lek.pli
forcingfile={name}
[boundary]
quantity=dischargebnd
locationfile=boundary_conditions/Waal.pli
forcingfile={name}
[boundary]
quantity=dischargebnd
locationfile=boundary_conditions/Maas.pli
forcingfile={name2}
[boundary]
quantity=salinitybnd
locationfile=boundary_conditions/rmm_zeerand_v3.pli
forcingfile={name2}"""

        ext_file.write_text(ext_file_data)
        return ext_file


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

    def test_registed_model_when_cache_exists_returns_true(self, tmp_path):
        cache = FileModelCache()
        path = tmp_path / "some-dimr.xml"
        model = DIMR()
        cache.register_model(path, model)

        assert cache._exists(path)

    def test_no_registed_model_when_cache_exists_returns_false(self, tmp_path):
        cache = FileModelCache()
        path = tmp_path / "some-dimr.xml"

        assert not cache._exists(path)

    def test_has_changed_on_unchanged_file_returns_false(self, tmp_path: Path):
        cache = FileModelCache()
        path = tmp_path / "some-dimr.xml"
        path.write_text("Hello World")
        model = DIMR()
        cache.register_model(path, model)

        assert not cache.has_changed(path)

    def test_has_changed_on_changed_file_returns_true(self, tmp_path: Path):
        cache = FileModelCache()
        path = tmp_path / "some-dimr.xml"
        path.write_text("Hello World")
        model = DIMR()
        cache.register_model(path, model)
        path.write_text("Hello World second time")

        assert cache.has_changed(path)

    def test_has_changed_when_no_registed_model_returns_true(self, tmp_path: Path):
        cache = FileModelCache()
        path = tmp_path / "some-dimr.xml"

        assert cache.has_changed(path)


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

    def test_load_settings_property_raises_error_with_uninitialized_settings(self):
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
        context = FileLoadContext()
        context.initialize_load_settings(first_bool, first_bool, first_path_style)
        context.initialize_load_settings(second_bool, second_bool, second_path_style)

        assert context.load_settings is not None
        assert context.load_settings.recurse == first_bool
        assert context.load_settings.resolve_casing == first_bool
        assert context.load_settings.path_style == first_path_style

    def test_is_content_changed_on_unchanged_file_returns_false(self, tmp_path: Path):
        context = FileLoadContext()
        path = tmp_path / "some-dimr.xml"
        path.write_text("Hello World")
        model = DIMR()
        context.register_model(path, model)

        assert not context.is_content_changed(path)

    def test_is_content_changed_on_changed_file_returns_true(self, tmp_path: Path):
        context = FileLoadContext()
        path = tmp_path / "some-dimr.xml"
        path.write_text("Hello World")
        model = DIMR()
        context.register_model(path, model)
        path.write_text("Hello World second time")

        assert context.is_content_changed(path)

    def test_is_content_changed_when_no_registed_model_returns_true(
        self, tmp_path: Path
    ):
        context = FileLoadContext()
        path = tmp_path / "some-dimr.xml"

        assert context.is_content_changed(path)


class TestDiskOnlyFileModel:
    _generic_file_model_path = Path("unsupported_file.blob")

    def test_constructor(self):
        # Setup file load context
        parent_path = Path.cwd() / "some" / "parent" / "directory"
        with file_load_context() as context:
            context.push_new_parent(parent_path, ResolveRelativeMode.ToParent)

            # Call
            model = DiskOnlyFileModel(filepath=self._generic_file_model_path)

            # Assert
            assert model._source_file_path == (
                parent_path / self._generic_file_model_path
            )

    def test_save_as_without_file(self):
        # Setup file load context
        parent_path = Path.cwd() / "some" / "parent" / "directory"

        with file_load_context() as context:
            context.push_new_parent(parent_path, ResolveRelativeMode.ToParent)
            model = DiskOnlyFileModel(filepath=self._generic_file_model_path)

            output_path = (
                test_output_dir
                / TestDiskOnlyFileModel.__name__
                / TestDiskOnlyFileModel.test_save_as_absolute.__name__
                / "someFile.blob"
            ).resolve()

            # Call
            model.save(filepath=output_path)

            # Assert
            assert model._source_file_path == output_path
            assert model.filepath == output_path
            assert not output_path.exists()

    def test_save_without_file(self):
        # Setup file load context
        parent_path = Path.cwd() / "some" / "parent" / "directory"

        with file_load_context() as context:
            context.push_new_parent(parent_path, ResolveRelativeMode.ToParent)
            model = DiskOnlyFileModel(filepath=self._generic_file_model_path)

            output_path = (
                test_output_dir
                / TestDiskOnlyFileModel.__name__
                / TestDiskOnlyFileModel.test_save_as_absolute.__name__
                / "someFile.blob"
            ).resolve()

            # Call
            model.filepath = output_path
            model.save()

            # Assert
            assert model._source_file_path == output_path
            assert model.filepath == output_path
            assert not output_path.exists()

    def test_save_as_absolute(self):
        input_parent_path = (
            test_input_dir / "e02" / "c11_korte-woerden-1d" / "dimr_model" / "rr"
        )
        file_name = Path("CROP_OW.PRN")

        with file_load_context() as context:
            context.push_new_parent(input_parent_path, ResolveRelativeMode.ToParent)
            model = DiskOnlyFileModel(filepath=file_name)

        output_path = (
            test_output_dir
            / TestDiskOnlyFileModel.__name__
            / TestDiskOnlyFileModel.test_save_as_absolute.__name__
            / file_name
        ).resolve()

        with file_load_context() as context:
            context.push_new_parent(output_path, ResolveRelativeMode.ToParent)
            model.save(output_path)

        assert output_path.exists()
        assert output_path.is_file()
        assert filecmp.cmp(input_parent_path / file_name, output_path)

    def test_save(self):
        input_parent_path = (
            test_input_dir / "e02" / "c11_korte-woerden-1d" / "dimr_model" / "rr"
        )
        input_file_name = Path("CROP_OW.PRN")

        with file_load_context() as context:
            context.push_new_parent(input_parent_path, ResolveRelativeMode.ToParent)
            model = DiskOnlyFileModel(filepath=input_file_name)

        output_file_name = Path("CROP.PRN")
        output_path = (
            test_output_dir
            / TestDiskOnlyFileModel.__name__
            / TestDiskOnlyFileModel.test_save_as_absolute.__name__
            / output_file_name
        ).resolve()

        with file_load_context() as context:
            context.push_new_parent(output_path, ResolveRelativeMode.ToParent)
            model.filepath = output_path
            model.save()

        assert output_path.exists()
        assert output_path.is_file()
        assert filecmp.cmp(input_parent_path / input_file_name, output_path)


class TestFileCasingResolver:
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
        resolver = FileCasingResolver()

        file_path = test_input_dir / input_file

        expected_file_path = test_input_dir / expected_file
        actual_file_path = resolver.resolve(file_path)

        assert actual_file_path == expected_file_path


class TestModelSaveSettings:
    def test_initialize_new_instance_sets_os_path_style_by_default(self):
        settings = ModelSaveSettings()

        exp_path_style = (
            PathStyle.WINDOWSLIKE
            if platform.system() == "Windows"
            else PathStyle.UNIXLIKE
        )

        assert settings.path_style == exp_path_style

    @pytest.mark.parametrize("path_style", [PathStyle.UNIXLIKE, PathStyle.WINDOWSLIKE])
    def test_properties(self, path_style: PathStyle):
        settings = ModelSaveSettings(path_style=path_style)
        assert settings.path_style == path_style


class TestModelLoadSettings:
    @pytest.mark.parametrize("value", [True, False])
    @pytest.mark.parametrize("path_style", [PathStyle.UNIXLIKE, PathStyle.WINDOWSLIKE])
    def test_recurse_property(self, value: bool, path_style: PathStyle):
        settings = ModelLoadSettings(
            recurse=value, resolve_casing=value, path_style=path_style
        )
        assert settings.recurse == value
        assert settings.resolve_casing == value
        assert settings.path_style == path_style


class TestSerializerConfig:
    def test_default(self):
        config = SerializerConfig()
        assert config.float_format == ""


class TestPathStyleValidator:
    def test_validate_none_returns_current_os_path_style(self):
        validator = PathStyleValidator()
        path_style = validator.validate(None)

        exp_path_style = (
            PathStyle.WINDOWSLIKE
            if platform.system() == "Windows"
            else PathStyle.UNIXLIKE
        )

        assert path_style == exp_path_style

    def test_validate_windows_returns_windows_path_style(self):
        validator = PathStyleValidator()
        path_style = validator.validate("windows")

        assert path_style == PathStyle.WINDOWSLIKE

    def test_validate_unix_returns_unix_path_style(self):
        validator = PathStyleValidator()
        path_style = validator.validate("unix")

        assert path_style == PathStyle.UNIXLIKE

    def test_validate_unknown_raises_error(self):
        validator = PathStyleValidator()

        with pytest.raises(ValueError) as error:
            validator.validate("unknown")

        expected_message = (
            "Path style 'unknown' not supported. Supported path styles: unix, windows"
        )
        assert expected_message in str(error.value)
