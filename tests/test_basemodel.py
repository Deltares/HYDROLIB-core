from hydrolib.core.basemodel import FileModel
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
