from pathlib import Path
from typing import List, Optional
from unittest.mock import MagicMock, patch

import pytest

from hydrolib.core.base.models import DiskOnlyFileModel, FileModel
from hydrolib.core.base.utils import PathToDictionaryConverter


class TestPathToDictionaryConverter:

    @pytest.mark.parametrize(
        "annotation, expected",
        [
            (FileModel, True),
            (DiskOnlyFileModel, True),
            (int, False),
            (str, False),
            (Optional[FileModel], True),
            (Optional[DiskOnlyFileModel], True),
            (Optional[List[FileModel]], False),
            (dict[str, int], False),
        ]
    )
    def test_is_file_model_type(self, annotation, expected):
        assert PathToDictionaryConverter.is_file_model_type(annotation) == expected

    @pytest.mark.parametrize(
        "annotation, expected",
        [
            (FileModel, False),
            (DiskOnlyFileModel, False),
            (int, False),
            (str, False),
            (Optional[FileModel], False),
            (Optional[DiskOnlyFileModel], False),
            (List[FileModel], True),
            (List[DiskOnlyFileModel], True),
            (Optional[List[FileModel]], True),
            (Optional[List[DiskOnlyFileModel]], True),
            (dict[str, int], False),
        ],
    )
    def test_is_list_file_model_type(self, annotation, expected):
        assert PathToDictionaryConverter.is_list_file_model_type(annotation) == expected

    @pytest.mark.parametrize("path", ["test/path/to/file", Path("another/test/path")])
    def test_make_dict(self, path):
        with patch("hydrolib.core.base.file_manager.file_load_context") as mock_context:
            result = PathToDictionaryConverter.make_dict(path)

        assert result == {"filepath": Path(path)}

    @pytest.mark.parametrize("path", ["test/path/to/file", Path("another/test/path")])
    def test_make_dict_recurse_false(self, path):
        mock_load_settings = MagicMock()
        mock_load_settings.recurse = False
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = MagicMock(_load_settings=mock_load_settings)
        with patch("hydrolib.core.base.file_manager.file_load_context", return_value=mock_context_manager):
            result = PathToDictionaryConverter.make_dict(path)

        assert isinstance(result, DiskOnlyFileModel)
        assert result.filepath == Path(path)

    @pytest.fixture
    def mock_cls(self):
        mock_cls = MagicMock()
        mock_annotation = MagicMock()
        mock_annotation.annotation = Optional[FileModel]
        mock_cls.model_fields = {"ext": mock_annotation}
        return mock_cls

    @pytest.fixture
    def mock_validation_info(self):
        mock_validation_info = MagicMock()
        mock_validation_info.field_name = "ext"
        return mock_validation_info

    def test_convert(self, mock_cls, mock_validation_info):
        with patch("hydrolib.core.base.file_manager.file_load_context") as mock_context:
            result = PathToDictionaryConverter.convert(mock_cls, "test/path/to/file", mock_validation_info)

        assert result == {"filepath": Path("test/path/to/file")}

    def test_convert_recurse_false(self, mock_cls, mock_validation_info):
        mock_load_settings = MagicMock()
        mock_load_settings.recurse = False
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = MagicMock(_load_settings=mock_load_settings)
        with patch("hydrolib.core.base.file_manager.file_load_context", return_value=mock_context_manager):
            result = PathToDictionaryConverter.convert(mock_cls, "test/path/to/file", mock_validation_info)

        assert isinstance(result, DiskOnlyFileModel)
        assert result.filepath == Path("test/path/to/file")
