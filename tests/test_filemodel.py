from .utils import test_output_dir
from hydrolib.core.io.mdu.models import FMModel

import shutil


def test_an_exported_default_model_should_be_readable():
    output_dir = test_output_dir / "test_an_exported_default_model_should_be_readable"
    if output_dir.exists():
        shutil.rmtree(output_dir)

    model = FMModel()
    model.save(output_dir)
    read_model = FMModel(output_dir / (FMModel._filename() + FMModel._ext()))

    assert read_model is not None
