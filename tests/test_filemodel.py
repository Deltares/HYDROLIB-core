from pathlib import Path
from .utils import test_input_dir, test_output_dir
from hydrolib.core.io.mdu.models import FMModel

import shutil


def test_exporting_a_model_with_default_paths_should_preserve_files_with_duplicate_names():
    input_dir = (
        test_input_dir
        / test_exporting_a_model_with_default_paths_should_preserve_files_with_duplicate_names.__name__
    )
    input_mdu = input_dir / "fm.mdu"
    output_dir = (
        test_output_dir
        / test_exporting_a_model_with_default_paths_should_preserve_files_with_duplicate_names.__name__
    )

    if output_dir.exists():
        shutil.rmtree(output_dir)

    model = FMModel(input_mdu)
    model.save(output_dir)

    # We expect the same number of ini files.
    input_files = list(input_dir.glob("**/*.ini"))
    output_files = list(output_dir.glob("**/*.ini"))
    assert len(output_files) == len(input_files)
