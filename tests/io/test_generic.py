import filecmp
from pathlib import Path

import pytest

from hydrolib.core.basemodel import ResolveRelativeMode, file_load_context
from hydrolib.core.io.generic.models import GenericFileModel

from ..utils import test_input_dir, test_output_dir


class TestGenericFileModel:
    def test_constructor(self):
        # Setup file load context
        parent_path = Path.cwd() / "some" / "parent" / "directory"
        generic_file_model_path = Path("unsupported_file.blob")

        with file_load_context() as context:
            context.push_new_parent(parent_path, ResolveRelativeMode.ToParent)

            # Call
            model = GenericFileModel(filepath=generic_file_model_path)

            # Assert
            assert model._source_file_path == (parent_path / generic_file_model_path)

    def test_save_as_without_file(self):
        # Setup file load context
        parent_path = Path.cwd() / "some" / "parent" / "directory"
        generic_file_model_path = Path("unsupported_file.blob")

        with file_load_context() as context:
            context.push_new_parent(parent_path, ResolveRelativeMode.ToParent)
            model = GenericFileModel(filepath=generic_file_model_path)

            output_path = (
                test_output_dir
                / TestGenericFileModel.__name__
                / TestGenericFileModel.test_save_as_absolute.__name__
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
        generic_file_model_path = Path("unsupported_file.blob")

        with file_load_context() as context:
            context.push_new_parent(parent_path, ResolveRelativeMode.ToParent)
            model = GenericFileModel(filepath=generic_file_model_path)

            output_path = (
                test_output_dir
                / TestGenericFileModel.__name__
                / TestGenericFileModel.test_save_as_absolute.__name__
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
            model = GenericFileModel(filepath=file_name)

        output_path = (
            test_output_dir
            / TestGenericFileModel.__name__
            / TestGenericFileModel.test_save_as_absolute.__name__
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
            model = GenericFileModel(filepath=input_file_name)

        output_file_name = Path("CROP.PRN")
        output_path = (
            test_output_dir
            / TestGenericFileModel.__name__
            / TestGenericFileModel.test_save_as_absolute.__name__
            / output_file_name
        ).resolve()

        with file_load_context() as context:
            context.push_new_parent(output_path, ResolveRelativeMode.ToParent)
            model.filepath = output_path
            model.save()

        assert output_path.exists()
        assert output_path.is_file()
        assert filecmp.cmp(input_parent_path / input_file_name, output_path)
